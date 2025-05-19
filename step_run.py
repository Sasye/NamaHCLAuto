import time
import os
from image_utils import ImageUtils

class StepRunner:
    def __init__(self, config, adb_utils, check_interval=2):
        self.config = config
        self.adb_utils = adb_utils
        self.check_interval = check_interval
        self.steps = config.get("steps", [])

    def check_and_run_helpers(self):
        helpers = self.config.get("helper_steps", {})
        for name, helper in helpers.items():
            trigger_image = helper.get("trigger_image")
            threshold = helper.get("threshold", 0.8)
            if not trigger_image:
                continue

            position = ImageUtils.find_image('screen.png', trigger_image, threshold)
            if position:
                print(f"检测到辅助触发图 [{trigger_image}]，点击触发图像位置 {position}，执行辅助步骤 [{name}]")
                self.adb_utils.tap_screen(*position)
                time.sleep(helper.get("step", {}).get("post_delay", 1))

    def run_step(self, step_config):
        print(f"正在执行步骤: {step_config.get('description', '')}")
        start_time = time.time()
        any_mode = step_config.get('any', False)
        loop_until_target = step_config.get('loop_until_target', None)

        while True:
            if not self.adb_utils.take_screenshot():
                time.sleep(self.check_interval)
                continue

            self.check_and_run_helpers()

            if loop_until_target:
                if ImageUtils.find_image('screen.png', loop_until_target, 0.8):
                    print(f"检测到退出标志图片 [{loop_until_target}]，进入下一步骤")
                    return True

            found_targets = []

            for target in step_config['targets']:
                position = ImageUtils.find_image(
                    'screen.png',
                    target['path'],
                    target.get('threshold', 0.8)
                )
                if position:
                    x_offset, y_offset = target.get('offset', (0, 0))
                    actual_pos = (
                        position[0] + x_offset,
                        position[1] + y_offset
                    )
                    found_targets.append({
                        "pos": actual_pos,
                        "name": os.path.basename(target['path']),
                        "priority": target.get('priority', 0)
                    })
                    if any_mode:
                        break

            if found_targets:
                if any_mode:
                    target_to_click = found_targets[0]
                else:
                    found_targets.sort(key=lambda x: x['priority'], reverse=True)
                    target_to_click = found_targets[0]

                print(f"找到目标 [{target_to_click['name']}]，点击坐标 {target_to_click['pos']}，优先级 {target_to_click['priority']}")
                self.adb_utils.tap_screen(*target_to_click['pos'])
                time.sleep(step_config.get('post_delay', 1))
                if not loop_until_target:
                    return True
                else:
                    continue
            else:
                print("未找到目标，继续等待...")

            if time.time() - start_time > step_config.get('timeout', 60):
                print("步骤超时")
                return False

            time.sleep(self.check_interval)
