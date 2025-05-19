import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import json
import sys
import threading
import queue

class ConsoleRedirector:
    """实时输出重定向类"""
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

class AutomationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NamaHCLAuto v0.0.1")
        self.running = False
        self.script_process = None
        self.output_thread = None

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
        """构建用户界面"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # 配置文件区域
        config_frame = ttk.LabelFrame(main_frame, text="配置设置", padding=10)
        config_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Label(config_frame, text="配置文件:").grid(row=0, column=0, sticky="w")
        config_entry = ttk.Entry(config_frame, textvariable=self.config_path, width=40)
        config_entry.grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="浏览", command=self.select_config).grid(row=0, column=2)

        # ADB设置区域
        ttk.Label(config_frame, text="ADB路径:").grid(row=1, column=0, sticky="w", pady=5)
        entry_adb = ttk.Entry(config_frame, textvariable=self.adb_path, width=40)
        entry_adb.grid(row=1, column=1, padx=5)
        ttk.Button(config_frame, text="选择ADB", command=self.select_adb).grid(row=1, column=2)

        ttk.Label(config_frame, text="ADB端口:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(config_frame, textvariable=self.adb_port, width=10).grid(row=2, column=1, sticky="w")

        # 控制按钮区域
        control_frame = ttk.Frame(main_frame, padding=10)
        control_frame.grid(row=1, column=0, sticky="ew", pady=10)
        self.start_btn = ttk.Button(control_frame, text="启动", command=self.toggle_script)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(control_frame, text="状态: 空闲")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 控制台输出区域
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
        """加载默认配置文件"""
        default_path = os.path.join(self.script_dir, "config.json")
        if os.path.isfile(default_path):
            self.config_path.set(self.normalize_path(default_path))
            self.load_config_values(default_path)

    def load_config_values(self, config_path):
        """从配置文件加载设置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.adb_path.set(self.normalize_path(config.get('adb_path', '')))
            self.adb_port.set(config.get('adb_port', 16384))
        except Exception as e:
            self.show_error(f"配置文件加载失败: {str(e)}")

    def normalize_path(self, path):
        """标准化路径格式"""
        return os.path.normpath(path)

    def select_config(self):
        """选择配置文件"""
        path = filedialog.askopenfilename(
            title="选择配置文件",
            initialdir=self.script_dir,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if path:
            self.config_path.set(self.normalize_path(path))
            self.load_config_values(path)

    def select_adb(self):
        """选择ADB程序"""
        path = filedialog.askopenfilename(
            title="选择ADB程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if path:
            self.adb_path.set(self.normalize_path(path))

    def toggle_script(self):
        """切换脚本运行状态"""
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
        """验证配置有效性"""
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
        """更新配置文件"""
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
        """启动脚本进程"""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"  # 禁用输出缓冲
        env["PYTHONIOENCODING"] = "utf-8"

        self.script_process = subprocess.Popen(
            [sys.executable, "-u", "NamaHCLAuto.py", self.config_path.get()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            env=env
        )

        self.running = True
        self.start_btn.config(text="停止")
        self.status_label.config(text="状态: 运行中")

        # 启动输出读取线程
        self.output_thread = threading.Thread(target=self.read_output, daemon=True)
        self.output_thread.start()

    def read_output(self):
        """读取子进程输出"""
        while self.script_process.poll() is None:
            try:
                line = self.script_process.stdout.readline()
                if line:
                    sys.stdout.write(line)  # 通过重定向器输出
            except Exception as e:
                sys.stderr.write(f"输出读取错误: {str(e)}\n")
                break

        # 读取剩余输出
        remaining_output, _ = self.script_process.communicate()
        if remaining_output:
            sys.stdout.write(remaining_output)

    def stop_script(self):
        """停止脚本进程"""
        if self.script_process:
            self.script_process.terminate()
        self.running = False
        self.start_btn.config(text="启动")
        self.status_label.config(text="状态: 已停止")

    def show_error(self, message):
        """显示错误消息"""
        messagebox.showerror("错误", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationUI(root)
    root.mainloop()