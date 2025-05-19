import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import json
import sys

class AutomationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化控制面板")
        self.running = False
        self.script_process = None

        # 获取脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        # 初始化配置变量
        self.config_path = tk.StringVar()
        self.adb_path = tk.StringVar()
        self.adb_port = tk.IntVar(value=16384)  # 默认值

        # 自动加载默认配置
        self.load_default_config()
        
        self.setup_ui()

    def load_default_config(self):
        """加载默认配置文件"""
        default_path = os.path.join(self.script_dir, "config.json")
        if os.path.isfile(default_path):
            self.config_path.set(self.normalize_path(default_path))
            self.load_config_values(default_path)

    def load_config_values(self, config_path):
        """从配置文件加载ADB设置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 读取ADB设置（带默认值）
            adb_path = config.get('adb_path', '模拟器的adb.exe')
            self.adb_path.set(self.normalize_path(adb_path))
            
            adb_port = config.get('adb_port', 16384)
            self.adb_port.set(adb_port)
            
        except json.JSONDecodeError:
            messagebox.showerror("配置错误", "配置文件格式错误，请检查JSON语法")
        except Exception as e:
            messagebox.showerror("配置错误", f"读取配置失败：\n{str(e)}")

    def normalize_path(self, path):
        """统一转换为系统标准路径格式"""
        return os.path.normpath(path)

    def setup_ui(self):
        """构建用户界面"""
        # 配置文件选择区域
        ttk.Label(self.root, text="配置文件:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        config_entry = ttk.Entry(self.root, textvariable=self.config_path, width=40)
        config_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="浏览", command=self.select_config).grid(row=0, column=2, padx=5, pady=5)

        # ADB路径设置
        ttk.Label(self.root, text="ADB路径:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        entry_adb = ttk.Entry(self.root, textvariable=self.adb_path, width=40)
        entry_adb.grid(row=1, column=1, padx=5, pady=5)
        entry_adb.bind("<FocusOut>", lambda e: self.adb_path.set(self.normalize_path(self.adb_path.get())))
        ttk.Button(self.root, text="选择ADB", command=self.select_adb).grid(row=1, column=2, padx=5, pady=5)

        # ADB端口设置
        ttk.Label(self.root, text="ADB端口:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.root, textvariable=self.adb_port, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # 控制按钮
        self.start_btn = ttk.Button(self.root, text="启动", command=self.toggle_script)
        self.start_btn.grid(row=3, column=1, padx=5, pady=10)

        # 状态显示
        self.status_label = ttk.Label(self.root, text="状态: 空闲")
        self.status_label.grid(row=4, column=0, columnspan=3, pady=5)

    def select_config(self):
        """选择配置文件并自动加载设置"""
        path = filedialog.askopenfilename(
            title="选择配置文件",
            initialdir=self.script_dir,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if path:
            normalized_path = self.normalize_path(path)
            self.config_path.set(normalized_path)
            self.load_config_values(normalized_path)  # 加载新配置

    def select_adb(self):
        """选择ADB程序"""
        path = filedialog.askopenfilename(
            title="选择ADB程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if path:
            self.adb_path.set(self.normalize_path(path))

    def toggle_script(self):
        """启停控制"""
        if not self.running:
            # 验证配置文件有效性
            config_file = self.config_path.get()
            if not config_file or not os.path.exists(config_file):
                messagebox.showerror("错误", "请先选择有效的配置文件！")
                return
            
            # 更新当前配置到文件
            try:
                self.update_config()
            except Exception as e:
                messagebox.showerror("配置错误", f"保存配置失败：\n{str(e)}")
                return
            
            # 启动脚本
            try:
                self.script_process = subprocess.Popen(
                    ["python", "NamaHCLAuto.py", config_file]
                )
                self.running = True
                self.start_btn.config(text="停止")
                self.status_label.config(text="状态: 运行中")
            except Exception as e:
                messagebox.showerror("启动失败", f"无法启动脚本：\n{str(e)}")
                self.running = False
        else:
            if self.script_process:
                self.script_process.terminate()
                self.script_process = None
            self.running = False
            self.start_btn.config(text="启动")
            self.status_label.config(text="状态: 已停止")

    def update_config(self):
        """更新配置文件"""
        with open(self.config_path.get(), 'r+', encoding='utf-8') as f:
            config = json.load(f)
            
            # 更新ADB设置
            config['adb_path'] = self.normalize_path(self.adb_path.get())
            config['adb_port'] = self.adb_port.get()
            
            # 回写文件
            f.seek(0)
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.truncate()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationUI(root)
    root.mainloop()