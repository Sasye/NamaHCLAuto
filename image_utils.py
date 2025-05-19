import cv2
import os

class ImageUtils:
    @staticmethod
    def find_image(screen_path, template_path, threshold=0.8):
        screen = cv2.imread(screen_path, cv2.IMREAD_GRAYSCALE)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        print(f"尝试加载图像: {template_path}")

        if screen is None or template is None:
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
