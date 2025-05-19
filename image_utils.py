import cv2
import os

class ImageUtils:
    _template_cache = {}  # 静态字典缓存模板图像

    @staticmethod
    def preload_templates(config):
        """预加载所有配置中的模板图像"""
        # 收集所有需要预加载的图像路径
        all_images = set()
        
        # 主步骤中的目标图像
        for step in config.get("steps", []):
            for target in step.get("targets", []):
                all_images.add(target['path'])
        
        # 辅助步骤中的触发图像
        for helper in config.get("helper_steps", {}).values():
            if 'trigger_image' in helper:
                all_images.add(helper['trigger_image'])
        
        # 全局监听和子循环图像
        if 'global_monitor' in config:
            all_images.add(config['global_monitor']['trigger_image'])
            for step in config['global_monitor']['target_loop']['steps']:
                for target in step.get('targets', []):
                    all_images.add(target['path'])
        
        # 加载到缓存
        for path in all_images:
            if path not in ImageUtils._template_cache:
                template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    ImageUtils._template_cache[path] = template
                else:
                    print(f"警告: 无法加载模板图像 {path}")

    @staticmethod
    def find_image(screen_path, template_path, threshold=0.8):
        screen = cv2.imread(screen_path, cv2.IMREAD_GRAYSCALE)
        if screen is None:
            return None
        
        # 从缓存获取模板图像
        template = ImageUtils._template_cache.get(template_path)
        if template is None:
            print(f"错误: 模板图像 {template_path} 未预加载")
            return None
        
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        print(f"匹配值: {max_val:.3f} (阈值: {threshold})")
        
        if max_val < threshold:
            return None
        
        h, w = template.shape
        x = max_loc[0] + w // 2
        y = max_loc[1] + h // 2
        return (x, y)