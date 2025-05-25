import subprocess
import os

class AdbUtils:
    def __init__(self, adb_path, device_id=None):
        self.adb_path = os.path.normpath(adb_path)
        self.device_id = device_id

    def connect_emulator(self, ip=None, port=None):
        if ip is None:
            ip = "127.0.0.1"
        if port is None:
            port = 16384
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(['-s', self.device_id])
        cmd.extend(['connect', f"{ip}:{port}"])
        subprocess.call(cmd)

    def take_screenshot(self, filename='screen.png'):
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['exec-out', 'screencap', '-p'])

            proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
            )
            screenshot_data, _ = proc.communicate()

            with open(filename, 'wb') as f:
                f.write(screenshot_data)

            return True
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return False

    def tap_screen(self, x, y):
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(['-s', self.device_id])
        cmd.extend(['shell', 'input', 'tap', str(x), str(y)])
        
        # 添加 creationflags 参数
        subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NO_WINDOW,  # Windows隐藏窗口
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"已点击坐标 ({x}, {y})")