import subprocess
import os

class AdbUtils:
    def __init__(self, adb_path, device_id=None):
        self.adb_path = os.path.normpath(adb_path)
        self.device_id = device_id

    def connect_emulator(self, port=None):
        if port is None:
            port = 16384
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(['-s', self.device_id])
        cmd.extend(['connect', f"127.0.0.1:{port}"])
        subprocess.call(cmd)

    def take_screenshot(self, filename='screen.png'):
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['exec-out', 'screencap', '-p'])

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
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
        subprocess.call(cmd)
        print(f"已点击坐标 ({x}, {y})")
