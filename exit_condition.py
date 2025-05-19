from image_utils import ImageUtils

class ExitConditionChecker:
    def __init__(self, config, adb_utils, enable_exit_condition=True):
        self.config = config
        self.adb_utils = adb_utils
        self.enable_exit_condition = enable_exit_condition

    def check_exit_condition(self):
        if not self.enable_exit_condition:
            return False
        
        if not self.config['loop'].get('exit_condition'):
            return False
            
        if self.adb_utils.take_screenshot():
            target = self.config['loop']['exit_condition']['target']
            threshold = self.config['loop']['exit_condition'].get('threshold', 0.8)
            return ImageUtils.find_image('screen.png', target, threshold) is not None
        return False
