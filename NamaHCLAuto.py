import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import json
import threading
import queue
from config_loader import ConfigLoader
from adb_utils import AdbUtils
from step_run import StepRunner
from exit_condition import ExitConditionChecker
from image_utils import ImageUtils

# ---------------------------- 控制台输出重定向 ----------------------------
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.output_queue = queue.Queue()
        self.running = True

    def write(self, text):
        self.output_queue.put(text)
    
    def flush(self):
        pass
    
    def update_display(self):
        while not self.output_queue.empty():
            text = self.output_queue.get()
            self.text_widget.insert(tk.END, text)
            self.text_widget.see(tk.END)
        if self.running:
            self.text_widget.after(100, self.update_display)

# ---------------------------- 核心自动化逻辑 ----------------------------
class AutomationCore:
    def __init__(self, config_path, adb_path, adb_port):
        self.config = ConfigLoader.load(config_path)
        ConfigLoader.validate(self.config)
        self.adb_utils = AdbUtils(adb_path)
        self.adb_utils.connect_emulator(adb_port)
        ImageUtils.preload_templates(self.config)
        self.running = True

    def check_global_monitor(self):
        monitor_config = self.config.get("global_monitor")
        if not monitor_config:
            return False
        if self.adb_utils.take_screenshot():
            position = ImageUtils.find_image(
                'screen.png', 
                monitor_config["trigger_image"],
                monitor_config.get("threshold", 0.8)
            )
            return position is not None
        return False

    def run(self):
        try:
            step_runner = StepRunner(self.config, self.adb_utils)
            exit_checker = ExitConditionChecker(self.config, self.adb_utils)
            loop_count, max_loops = 0, 0

            if self.config['loop'].get('enabled', False):
                loop_type = self.config['loop'].get('type', 'times')
                max_loops = float('inf') if loop_type == 'infinite' else self.config['loop'].get('times', 1)

            current_main_step = 0
            main_loop_steps = step_runner.steps
            in_sub_loop = False

            while self.running and loop_count < max_loops:
                if in_sub_loop:
                    sub_loop_config = self.config["global_monitor"]["target_loop"]
                    sub_step_runner = StepRunner({"steps": sub_loop_config["steps"]}, self.adb_utils)
                    sub_loop_exit = False

                    for step in sub_loop_config["steps"]:
                        success = sub_step_runner.run_step(step)
                        if not success:
                            sub_loop_exit = True
                            break

                    if not sub_loop_exit and self.adb_utils.take_screenshot():
                        exit_target = sub_loop_config.get("exit_condition", {}).get("target")
                        exit_threshold = sub_loop_config.get("exit_condition", {}).get("threshold", 0.6)
                        if exit_target and ImageUtils.find_image('screen.png', exit_target, exit_threshold):
                            sub_loop_exit = True

                    in_sub_loop = False
                    current_main_step = 0
                    step_runner.steps = main_loop_steps
                    continue

                print(f"\n--- 主循环第 {loop_count+1} 次 ---")
                current_main_step = 0
                while current_main_step < len(step_runner.steps) and self.running:
                    if self.check_global_monitor():
                        print("检测到全局触发图像，进入子循环")
                        in_sub_loop = True
                        break
                    if exit_checker.check_exit_condition():
                        print("满足主循环退出条件，终止程序")
                        return
                    success = step_runner.run_step(step_runner.steps[current_main_step])
                    if not success:
                        return
                    current_main_step += 1
                loop_count += 1

            print(f"\n总共完成 {loop_count} 次主循环")

        except Exception as e:
            print(f"自动化执行失败: {str(e)}")

# ---------------------------- GUI界面 ----------------------------
class AutomationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NamaHCLAuto v0.0.1")
        self.running = False
        self.automation_core = None
        self.worker_thread = None

        # 初始化配置变量
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config_path = tk.StringVar()
        self.adb_path = tk.StringVar()
        self.adb_port = tk.IntVar(value=16384)

        # 构建UI组件
        self.setup_ui()
        
        # 配置输出重定向
        self.console_redirector = ConsoleRedirector(self.console_text)
        sys.stdout = self.console_redirector
        sys.stderr = self.console_redirector
        self.console_redirector.update_display()

        # 自动加载默认配置
        self.load_default_config()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        config_frame = ttk.LabelFrame(main_frame, text="配置设置", padding=10)
        config_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Label(config_frame, text="配置文件:").grid(row=0, column=0, sticky="w")
        config_entry = ttk.Entry(config_frame, textvariable=self.config_path, width=40)
        config_entry.grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="浏览", command=self.select_config).grid(row=0, column=2)

        ttk.Label(config_frame, text="ADB路径:").grid(row=1, column=0, sticky="w", pady=5)
        entry_adb = ttk.Entry(config_frame, textvariable=self.adb_path, width=40)
        entry_adb.grid(row=1, column=1, padx=5)
        ttk.Button(config_frame, text="选择ADB", command=self.select_adb).grid(row=1, column=2)

        ttk.Label(config_frame, text="ADB端口:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(config_frame, textvariable=self.adb_port, width=10).grid(row=2, column=1, sticky="w")

        control_frame = ttk.Frame(main_frame, padding=10)
        control_frame.grid(row=1, column=0, sticky="ew", pady=10)
        self.start_btn = ttk.Button(control_frame, text="启动", command=self.toggle_script)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(control_frame, text="状态: 空闲")
        self.status_label.pack(side=tk.LEFT, padx=10)

        console_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        console_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.console_text = scrolledtext.ScrolledText(
            console_frame, 
            wrap=tk.WORD,
            font=('Consolas', 10),
            height=15
        )
        self.console_text.pack(expand=True, fill="both")

    def load_default_config(self):
        default_path = os.path.join(self.script_dir, "config.json")
        if os.path.isfile(default_path):
            self.config_path.set(os.path.normpath(default_path))
            self.load_config_values(default_path)

    def load_config_values(self, config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.adb_path.set(os.path.normpath(config.get('adb_path', '')))
            self.adb_port.set(config.get('adb_port', 16384))
        except Exception as e:
            self.show_error(f"配置文件加载失败: {str(e)}")

    def select_config(self):
        path = filedialog.askopenfilename(
            title="选择配置文件",
            initialdir=self.script_dir,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if path:
            self.config_path.set(os.path.normpath(path))
            self.load_config_values(path)

    def select_adb(self):
        path = filedialog.askopenfilename(
            title="选择ADB程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if path:
            self.adb_path.set(os.path.normpath(path))

    def toggle_script(self):
        if not self.running:
            if self.validate_config():
                try:
                    self.update_config()
                    self.start_script()
                except Exception as e:
                    self.show_error(f"启动失败: {str(e)}")
        else:
            self.stop_script()

    def validate_config(self):
        errors = []
        if not os.path.exists(self.config_path.get()):
            errors.append("配置文件不存在")
        if not os.path.exists(self.adb_path.get()):
            errors.append("ADB路径无效")
        if errors:
            self.show_error("\n".join(errors))
            return False
        return True

    def update_config(self):
        try:
            with open(self.config_path.get(), 'r+', encoding='utf-8') as f:
                config = json.load(f)
                config['adb_path'] = self.adb_path.get()
                config['adb_port'] = self.adb_port.get()
                f.seek(0)
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.truncate()
        except Exception as e:
            raise RuntimeError(f"更新配置失败: {str(e)}")

    def start_script(self):
        self.worker_thread = threading.Thread(
            target=self.run_automation, 
            daemon=True
        )
        self.running = True
        self.start_btn.config(text="停止")
        self.status_label.config(text="状态: 运行中")
        self.worker_thread.start()

    def run_automation(self):
        self.automation_core = AutomationCore(
            config_path=self.config_path.get(),
            adb_path=self.adb_path.get(),
            adb_port=self.adb_port.get()
        )
        self.automation_core.run()
        self.running = False
        self.start_btn.config(text="启动")
        self.status_label.config(text="状态: 空闲")

    def stop_script(self):
        if self.automation_core:
            self.automation_core.running = False
        self.running = False
        print("正在停止自动化任务...")

    def show_error(self, message):
        messagebox.showerror("错误", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationUI(root)
    root.mainloop()