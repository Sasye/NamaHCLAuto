import os
import sys
from config_loader import ConfigLoader
from adb_utils import AdbUtils
from step_run import StepRunner
from exit_condition import ExitConditionChecker
from image_utils import ImageUtils

def check_global_monitor(config, adb_utils):
    """检查全局监听条件"""
    monitor_config = config.get("global_monitor")
    if not monitor_config:
        return False

    # 强制截图并匹配
    if adb_utils.take_screenshot():
        trigger_image = monitor_config["trigger_image"]
        threshold = monitor_config.get("threshold", 0.8)
        position = ImageUtils.find_image('screen.png', trigger_image, threshold)
        return position is not None
    else:
        print("截图失败，无法检测全局触发图像")
        return False

def main():
    try:
        config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
        config = ConfigLoader.load(config_path)
        ConfigLoader.validate(config)

        adb_port = config.get('adb_port', 16384)
        adb_utils = AdbUtils(config['adb_path'], device_id=config.get('device_id'))
        step_runner = StepRunner(config, adb_utils, check_interval=config.get('check_interval', 2))
        exit_checker = ExitConditionChecker(config, adb_utils, enable_exit_condition=False)

        loop_count = 0
        max_loops = 0
        loop_type = config['loop'].get('type', 'times')

        if config['loop'].get('enabled', False):
            if loop_type == 'infinite':
                max_loops = float('inf')
            elif loop_type == 'times':
                max_loops = config['loop'].get('times', 1)

        current_main_step = 0  # 主循环当前步骤索引（持久保存）
        main_loop_steps = step_runner.steps  # 保存主循环的步骤配置
        in_sub_loop = False    # 是否处于子循环中

        while loop_count < max_loops:
            if in_sub_loop:
                # 执行子循环逻辑
                sub_loop_config = config["global_monitor"]["target_loop"]
                sub_step_runner = StepRunner({"steps": sub_loop_config["steps"]}, adb_utils)
                sub_loop_exit = False

                # 1. 执行所有子循环步骤（不中途检测退出条件）
                for step in sub_loop_config["steps"]:
                    success = sub_step_runner.run_step(step)
                    if not success:
                        print("子循环步骤执行失败，强制退出")
                        sub_loop_exit = True
                        break
                
                # 2. 所有步骤完成后，强制刷新截图并检测退出条件
                if not sub_loop_exit:
                    adb_utils.take_screenshot('screen.png')  # 强制刷新截图
                    exit_condition = sub_loop_config.get("exit_condition", {})
                    exit_target = exit_condition.get("target")
                    exit_threshold = exit_condition.get("threshold", 0.6)
                    if exit_target and ImageUtils.find_image('screen.png', exit_target, exit_threshold):
                        print("满足子循环退出条件，返回主循环")
                        sub_loop_exit = True

                # 恢复主循环状态
                in_sub_loop = False
                current_main_step = 0  # 新增：重置步骤索引
                step_runner.steps = main_loop_steps
                continue  # 回到主循环，继续执行 current_main_step 的步骤

            # 主循环逻辑
            print(f"\n--- 主循环第 {loop_count+1} 次 ---")
            current_main_step = 0
            while current_main_step < len(step_runner.steps):
                # 全局监听检测
                if check_global_monitor(config, adb_utils):
                    print("检测到全局触发图像，进入子循环")
                    in_sub_loop = True
                    break  # 跳出主循环步骤执行，进入子循环

                # 主循环退出条件检查
                if exit_checker.check_exit_condition():
                    print("满足主循环退出条件，终止程序")
                    return

                # 执行当前步骤
                success = step_runner.run_step(step_runner.steps[current_main_step])
                if not success:
                    print("步骤执行失败，终止程序")
                    return
                current_main_step += 1  # 步骤执行成功后递增

            loop_count += 1

        print(f"\n总共完成 {loop_count} 次主循环")

    except KeyboardInterrupt:
        print("\n用户中断操作")

    except Exception as e:
        print(f"启动失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
