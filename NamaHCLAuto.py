import os
from config_loader import ConfigLoader
from adb_utils import AdbUtils
from step_run import StepRunner
from exit_condition import ExitConditionChecker

def main():
    try:
        config_path = "config.json"
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

        while loop_count < max_loops:
            print(f"\n--- 开始第 {loop_count+1} 次循环 ---")
            current_step = 0

            while current_step < len(step_runner.steps):
                if exit_checker.check_exit_condition():
                    print("满足退出条件，终止循环")
                    return

                success = step_runner.run_step(step_runner.steps[current_step])
                if not success:
                    print("步骤执行失败，终止循环")
                    return
                current_step += 1

            loop_count += 1
            if loop_type == 'infinite' and exit_checker.check_exit_condition():
                break

        print(f"\n总共完成 {loop_count} 次循环")

    except KeyboardInterrupt:
        print("\n用户中断操作")

    except Exception as e:
        print(f"启动失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
