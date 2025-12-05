import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import os
import paramiko
import time
import re
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('huawei_config_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HuaweiConfigBackup')


class HuaweiSwitchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("华为交换机配置同步工具")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TFrame", background="#f0f0f0")

        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建输入区域框架
        self.input_frame = ttk.LabelFrame(self.main_frame, text="配置输入", padding="10")
        self.input_frame.pack(fill=tk.X, pady=(0, 10))

        # 创建结果区域框架
        self.result_frame = ttk.LabelFrame(self.main_frame, text="操作结果", padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧IP列表区域
        self.ip_frame = ttk.LabelFrame(self.input_frame, text="IP列表", padding="5")
        self.ip_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # 右侧配置区域
        self.config_frame = ttk.LabelFrame(self.input_frame, text="交换机配置", padding="5")
        self.config_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # 配置输入框架的网格权重
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.columnconfigure(1, weight=1)
        self.input_frame.rowconfigure(0, weight=1)

        # IP列表文本框
        self.ip_text = scrolledtext.ScrolledText(self.ip_frame, wrap=tk.WORD, height=10)
        self.ip_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # IP列表按钮
        self.ip_buttons = ttk.Frame(self.ip_frame)
        self.ip_buttons.pack(fill=tk.X, padx=5, pady=5)

        self.btn_load_ip = ttk.Button(self.ip_buttons, text="加载IP列表", command=self.load_ip_list)
        self.btn_load_ip.pack(side=tk.LEFT, padx=2)

        self.btn_save_ip = ttk.Button(self.ip_buttons, text="保存IP列表", command=self.save_ip_list)
        self.btn_save_ip.pack(side=tk.LEFT, padx=2)

        self.btn_clear_ip = ttk.Button(self.ip_buttons, text="清空", command=lambda: self.ip_text.delete(1.0, tk.END))
        self.btn_clear_ip.pack(side=tk.RIGHT, padx=2)

        # 配置区域控件
        # 品牌选择
        ttk.Label(self.config_frame, text="品牌:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.brand_var = tk.StringVar(value="华为")
        self.brand_combo = ttk.Combobox(self.config_frame, textvariable=self.brand_var, values=["华为", "其他"],
                                        width=20)
        self.brand_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # 用户名
        ttk.Label(self.config_frame, text="用户名:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = ttk.Entry(self.config_frame, textvariable=self.username_var, width=20)
        self.username_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # 密码
        ttk.Label(self.config_frame, text="密码:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.password_var = tk.StringVar(value="Yunwei@1688")
        self.password_entry = ttk.Entry(self.config_frame, textvariable=self.password_var, show="*", width=20)
        self.password_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # 端口
        ttk.Label(self.config_frame, text="端口:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_var = tk.StringVar(value="22")
        self.port_entry = ttk.Entry(self.config_frame, textvariable=self.port_var, width=20)
        self.port_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # 备份目录
        ttk.Label(self.config_frame, text="备份目录:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.backup_dir_var = tk.StringVar(value="D:/HUAWEI_SWITCH/ConfigBackups")
        self.backup_dir_entry = ttk.Entry(self.config_frame, textvariable=self.backup_dir_var, width=20)
        self.backup_dir_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        self.btn_browse_dir = ttk.Button(self.config_frame, text="浏览...", command=self.browse_backup_dir)
        self.btn_browse_dir.grid(row=4, column=2, padx=5, pady=5)

        # 并发数
        ttk.Label(self.config_frame, text="并发数:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_workers_var = tk.StringVar(value="5")
        self.max_workers_entry = ttk.Entry(self.config_frame, textvariable=self.max_workers_var, width=20)
        self.max_workers_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

        # 命令文件路径
        ttk.Label(self.config_frame, text="命令文件:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.command_file_var = tk.StringVar(value="command.txt")
        self.command_file_entry = ttk.Entry(self.config_frame, textvariable=self.command_file_var, width=20)
        self.command_file_entry.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)

        self.btn_browse_cmd = ttk.Button(self.config_frame, text="浏览...", command=self.browse_command_file)
        self.btn_browse_cmd.grid(row=6, column=2, padx=5, pady=5)

        # 自定义查询关键字
        ttk.Label(self.config_frame, text="查询关键字:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(self.config_frame, textvariable=self.keyword_var, width=20)
        self.keyword_entry.grid(row=7, column=1, sticky=tk.W, padx=5, pady=5)

        # 关键字列名
        ttk.Label(self.config_frame, text="列名:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
        self.column_name_var = tk.StringVar()
        self.column_name_entry = ttk.Entry(self.config_frame, textvariable=self.column_name_var, width=20)
        self.column_name_entry.grid(row=8, column=1, sticky=tk.W, padx=5, pady=5)

        # 底部按钮
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=tk.X, pady=10)

        self.btn_start = ttk.Button(self.btn_frame, text="开始同步配置", command=self.start_sync)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_generate_csv = ttk.Button(self.btn_frame, text="生成配置表格", command=self.generate_config_table)
        self.btn_generate_csv.pack(side=tk.LEFT, padx=5)

        # 结果显示区域
        self.result_text = scrolledtext.ScrolledText(self.result_frame, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.result_text.config(state=tk.DISABLED)

        # 备份工具实例
        self.backup_tool = None

        # 自定义关键字变量
        self.custom_keyword = ""
        self.custom_column_name = ""

    def log(self, message):
        """在结果区域显示日志信息"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
        logger.info(message)

    def load_ip_list(self):
        """加载IP列表文件"""
        file_path = filedialog.askopenfilename(
            title="选择IP列表文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self.ip_text.delete(1.0, tk.END)
                self.ip_text.insert(tk.END, content)
                self.log(f"已加载IP列表文件: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"加载IP列表失败: {str(e)}")
                self.log(f"加载IP列表失败: {str(e)}")

    def save_ip_list(self):
        """保存IP列表到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存IP列表文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                content = self.ip_text.get(1.0, tk.END).strip()
                with open(file_path, 'w') as f:
                    f.write(content)
                self.log(f"已保存IP列表到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存IP列表失败: {str(e)}")
                self.log(f"保存IP列表失败: {str(e)}")

    def browse_backup_dir(self):
        """浏览备份目录"""
        dir_path = filedialog.askdirectory(title="选择备份目录")
        if dir_path:
            self.backup_dir_var.set(dir_path)

    def browse_command_file(self):
        """浏览命令文件"""
        file_path = filedialog.askopenfilename(
            title="选择命令文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.command_file_var.set(file_path)

    def get_ip_list(self):
        """从文本框获取IP列表"""
        content = self.ip_text.get(1.0, tk.END).strip()
        if not content:
            return []
        ips = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        return ips

    def start_sync(self):
        """开始同步配置"""
        ips = self.get_ip_list()
        if not ips:
            messagebox.showwarning("警告", "请输入或加载IP列表")
            return

        # 获取配置信息
        username = self.username_var.get()
        password = self.password_var.get()
        port = self.port_var.get()
        backup_dir = self.backup_dir_var.get()
        command_file = self.command_file_var.get()

        try:
            port = int(port)
            max_workers = int(self.max_workers_var.get())
        except ValueError:
            messagebox.showerror("错误", "端口和并发数必须是数字")
            return

        # 验证命令文件是否存在
        if not os.path.exists(command_file):
            messagebox.showerror("错误", f"命令文件不存在: {command_file}")
            return

        # 清空结果区域
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)

        # 创建备份工具实例
        self.backup_tool = HuaweiSwitchBackup(output_dir=backup_dir, command_file=command_file)

        # 准备设备列表
        devices = [
            {
                'ip': ip,
                'username': username,
                'password': password,
                'port': port
            } for ip in ips
        ]

        # 在新线程中执行备份，避免界面冻结
        self.btn_start.config(state=tk.DISABLED)
        threading.Thread(
            target=self.run_backup,
            args=(devices, max_workers),
            daemon=True
        ).start()

    def run_backup(self, devices, max_workers):
        """执行备份操作"""
        self.log(f"开始同步 {len(devices)} 台交换机的配置...")
        self.log(f"备份目录: {self.backup_dir_var.get()}")

        results = self.backup_tool.backup_multiple_switches(devices, max_workers)

        # 显示结果摘要
        success_count = sum(1 for s, _ in results if s)
        failure_count = len(results) - success_count

        self.log("\n=== 同步结果摘要 ===")
        self.log(f"总计: {len(results)} 台设备")
        self.log(f"成功: {success_count} 台")
        self.log(f"失败: {failure_count} 台")

        # 重新启用按钮
        self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))

    def generate_config_table(self):
        """生成配置表格"""
        backup_dir = self.backup_dir_var.get()
        if not os.path.exists(backup_dir):
            messagebox.showerror("错误", f"备份目录不存在: {backup_dir}")
            return

        # 获取自定义关键字
        self.custom_keyword = self.keyword_var.get().strip()
        self.custom_column_name = self.column_name_var.get().strip()

        if self.custom_keyword and not self.custom_column_name:
            messagebox.showwarning("警告", "请输入关键字对应的列名")
            return

        # 询问保存路径
        output_file = filedialog.asksaveasfilename(
            title="保存配置表格",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if not output_file:
            return

        # 处理目录并生成CSV
        self.log("开始生成配置表格...")
        self.btn_generate_csv.config(state=tk.DISABLED)

        threading.Thread(
            target=self.process_configs,
            args=(backup_dir, output_file),
            daemon=True
        ).start()

    def process_configs(self, directory, output_file):
        """处理配置文件并生成CSV"""
        results = self.process_directory(directory)
        self.save_to_csv(results, output_file)
        self.log(f"配置表格已保存到: {output_file}")
        self.root.after(0, lambda: self.btn_generate_csv.config(state=tk.NORMAL))

    def parse_filename(self, filename):
        """解析文件名，提取系统名称、交换机型号、IP地址和提取时间"""
        base_name = os.path.splitext(filename)[0]
        parts = base_name.split('__', 3)

        if len(parts) < 4:
            return None

        system_name = parts[0]
        switch_model = parts[1]
        ip_address = parts[2]
        timestamp = parts[3]

        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_address):
            return None

        try:
            if '_' in timestamp:
                date_part, time_part = timestamp.split('_')
            else:
                date_part = timestamp[:8]
                time_part = timestamp[8:]
            extract_time = datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M%S")
            formatted_time = extract_time.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_time = timestamp

        return {
            "系统名称": system_name,
            "交换机型号": switch_model,
            "IP地址": ip_address,
            "提取时间": formatted_time
        }

    def check_8021x_config(self, file_path):
        """检查配置文件中是否包含domain sangfor_802.1x"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if re.search(r'domain\s+sangfor_802\.1x', content):
                return 'domain sangfor_802.1x'
            else:
                return '未刷入'
        except Exception as e:
            self.log(f"读取文件 {file_path} 失败: {e}")
            return '未刷入'

    def search_custom_config(self, file_path, keyword):
        """在配置文件中搜索用户自定义关键字"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if keyword in line:
                        return line.strip()
            return "未查询到"
        except Exception as e:
            self.log(f"读取文件 {file_path} 失败: {e}")
            return "未查询到"

    def get_cfg_files(self, directory):
        return [f for f in os.listdir(directory)
                if f.endswith('.cfg') and os.path.isfile(os.path.join(directory, f))]

    def process_directory(self, directory):
        """处理目录中的所有cfg文件"""
        results = []
        cfg_files = self.get_cfg_files(directory)

        if not cfg_files:
            self.log(f"在目录 {directory} 中未找到任何.cfg文件")
            return results

        self.log(f"找到 {len(cfg_files)} 个.cfg文件，正在解析...")
        for filename in cfg_files:
            parsed = self.parse_filename(filename)
            if parsed:
                file_path = os.path.join(directory, filename)

                # 802.1x 检查
                parsed["是否刷入802.1x"] = self.check_8021x_config(file_path)

                # 自定义关键字搜索
                if self.custom_keyword and self.custom_column_name:
                    parsed[self.custom_column_name] = self.search_custom_config(file_path, self.custom_keyword)

                results.append(parsed)
                self.log(f"已解析: {filename}")
            else:
                self.log(f"无法解析: {filename}")

        return results

    def save_to_csv(self, results, output_file):
        """将结果保存为CSV文件"""
        if not results:
            self.log("没有有效数据可保存")
            return

        fieldnames = ['系统名称', '交换机型号', 'IP地址', '提取时间', '是否刷入802.1x']

        # 加入用户自定义列
        if self.custom_column_name:
            fieldnames.append(self.custom_column_name)

        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow(result)

        self.log(f"结果已保存到 {output_file} (共 {len(results)} 条记录)")


class HuaweiSwitchBackup:
    def __init__(self, output_dir='config_backups', command_file='command.txt'):
        self.output_dir = output_dir
        self.command_file = command_file
        os.makedirs(self.output_dir, exist_ok=True)

        # 读取命令列表
        self.cli_list = self._load_commands()

    def _load_commands(self):
        """加载命令列表"""
        try:
            with open(self.command_file, 'r') as f:
                return [line.rstrip() for line in f.readlines() if line.strip()]
        except Exception as e:
            logger.error(f"加载命令文件失败: {str(e)}")
            return ["dis device", "dis cu", "dis int b", "dis lldp n", "dis version"]

    def connect_to_switch(self, ip, username, password, port=22, timeout=15):
        """建立SSH连接"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            logger.info(f"正在连接 {ip}...")
            client.connect(
                hostname=ip,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                banner_timeout=25,
                auth_timeout=20,
                look_for_keys=False,
                allow_agent=False
            )
            return client
        except Exception as e:
            logger.error(f"连接 {ip} 失败: {str(e)}")
            return None

    def get_configuration(self, chan):
        """获取交换机配置"""
        try:
            # 关闭分页
            chan.send("screen-length 0 temporary\n")
            time.sleep(0.3)
            # 清空缓冲区
            while chan.recv_ready():
                chan.recv(1024)

            # 执行命令
            for cmd in self.cli_list:
                chan.send(cmd + "\n")
                time.sleep(0.5)

            config = ""
            start_time = time.time()
            max_wait = 120
            last_data_time = time.time()

            # 读取输出
            while time.time() - start_time < max_wait:
                if chan.recv_ready():
                    data = chan.recv(65535).decode('utf-8', 'ignore')
                    config += data
                    last_data_time = time.time()
                elif time.time() - last_data_time > 5:
                    break
                else:
                    time.sleep(0.5)

            # 提取设备信息
            model_match = re.search(r'0\s+-\s+(\S+)\s+Present', config)
            name_match = re.search(r'sysname\s+(\S+)', config)

            model = model_match.group(1).strip() if model_match else "Unknown"
            name = name_match.group(1).strip() if name_match else "Unknown"

            # 清理ANSI转义码
            clean_config = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', config)

            return clean_config, name, model

        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            return None

    def save_config(self, config, ip, device_name, model):
        """保存配置到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r'[^\w\-]', '_', device_name)

            filename = f"{safe_name}__{model}__{ip}__{timestamp}.cfg"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(config)

            logger.info(f"配置已保存到: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return None

    def backup_single_switch(self, ip, username, password, port=22):
        """备份单个交换机配置"""
        client = self.connect_to_switch(ip, username, password, port)
        if not client:
            return False, f"{ip}: 连接失败"

        chan = None
        try:
            chan = client.invoke_shell()
            time.sleep(1)

            result = self.get_configuration(chan)
            if not result:
                return False, f"{ip}: 获取配置失败"

            config, device_name, model = result

            filepath = self.save_config(config, ip, device_name, model)
            if not filepath:
                return False, f"{ip}: 保存配置失败"

            return True, f"{ip}: 备份成功 ({device_name})"

        except Exception as e:
            logger.exception(f"备份过程中出错: {str(e)}")
            return False, f"{ip}: 备份失败 - {str(e)}"

        finally:
            try:
                if chan:
                    chan.send("quit\n")
                    time.sleep(0.4)
                    chan.send("quit\n")
                    time.sleep(0.4)
                    chan.close()
            except:
                pass
            client.close()

    def backup_multiple_switches(self, devices, max_workers=5):
        """批量备份多个交换机配置"""
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    self.backup_single_switch,
                    d['ip'],
                    d['username'],
                    d['password'],
                    d['port']
                ): d['ip'] for d in devices
            }

            for future in as_completed(future_map):
                ip = future_map[future]
                try:
                    success, message = future.result()
                    results.append((success, message))
                    logger.info(message)
                    # 在GUI中显示结果
                    app.log(f"{'✅ 成功' if success else '❌ 失败'}: {message}")
                except Exception as e:
                    error_msg = f"{ip}: 执行失败 - {str(e)}"
                    results.append((False, error_msg))
                    logger.error(error_msg)
                    app.log(f"❌ 失败: {error_msg}")

        return results


if __name__ == "__main__":
    root = tk.Tk()
    app = HuaweiSwitchGUI(root)
    root.mainloop()