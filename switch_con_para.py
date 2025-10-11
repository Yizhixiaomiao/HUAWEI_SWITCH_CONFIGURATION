import paramiko
import time
import os
import re
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


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


class HuaweiSwitchBackup:
    def __init__(self, output_dir='config_backups'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

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

    # def get_device_info(self, chan):
    #     """获取设备基本信息"""
    #     try:
    #         chan.send("display device\n")
    #         time.sleep(1)
    #         chan.send("display current-configuration\n")
    #         time.sleep(1)
    #         device_info = ""
    #         while chan.recv_ready():
    #             device_info += chan.recv(4096).decode('utf-8', 'ignore')
    #
    #         # # 提取设备型号和名称
    #         # model_match = re.search(r'0\s+-\s+(\S+)\s+Present', device_info)
    #         # name_match = re.search(r'sysname\s+(\S+)', device_info)
    #         #
    #         # model = model_match.group(1).strip() if model_match else "Unknown"
    #         # name = name_match.group(1).strip() if name_match else "Unknown"
    #         #
    #         # while chan.recv_ready():
    #         #     chan.recv(1024)
    #         #
    #         # return name, model
    #     except Exception as e:
    #         logger.warning(f"获取设备信息失败: {str(e)}")
    #         return "Unknown", "Unknown"

    # def prepare_session(self, chan):
    #     """准备会话环境"""
    #     try:
    #         # 进入系统视图
    #         chan.send("system-view\n")
    #         time.sleep(0.5)
    #
    #         # 禁用分页
    #         chan.send("screen-length 0 temporary\n")
    #         time.sleep(0.5)
    #
    #         # 清除缓冲区
    #         while chan.recv_ready():
    #             chan.recv(1024)
    #
    #         return True
    #     except Exception as e:
    #         logger.error(f"会话准备失败: {str(e)}")
    #         return False

    def get_configuration(self, chan):
        """获取交换机配置"""
        try:
            while chan.recv_ready():
                chan.recv(1024)
            f = open('Command.txt', 'r')
            cli_list = f.readlines()

            for i in cli_list:
                chan.send(i)
                time.sleep(0.5)

            config = ""
            start_time = time.time()
            max_wait = 120  # 最大等待时间120秒
            last_data_time = time.time()

            while time.time() - start_time < max_wait:
                if chan.recv_ready():
                    chunk = chan.recv(65535).decode('utf-8', 'ignore')
                    config += chunk
                    last_data_time = time.time()
                elif time.time() - last_data_time > 5:  # 5秒无数据
                    break
                else:
                    time.sleep(0.5)

            # 提取设备型号和名称
            model_match = re.search(r'0\s+-\s+(\S+)\s+Present', config)
            name_match = re.search(r'sysname\s+(\S+)', config)

            model = model_match.group(1).strip() if model_match else "Unknown"
            name = name_match.group(1).strip() if name_match else "Unknown"

            # 清理ANSI转义码
            clean_config = re.sub(r'\x1b\[\d+m', '', config)
            return clean_config,name, model
        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            return None

    def save_config(self, config, ip, device_name, model):
        """保存配置到文件"""
        try:
            # 创建文件名
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

    def backup_single_switch(self, ip, username, password):
        """备份单个交换机配置"""
        client = self.connect_to_switch(ip, username, password)
        if not client:
            return False, f"{ip}: 连接失败"

        try:
            chan = client.invoke_shell()
            time.sleep(1)  # 等待shell初始化

            # 获取设备信息
            device_name, model = self.get_configuration(chan=con)

            # 准备会话
            # if not self.prepare_session(chan):
            #     return False, f"{ip}: 会话准备失败"

            # 获取配置
            config = self.get_configuration(chan)
            if not config:
                return False, f"{ip}: 获取配置失败"

            # 保存配置
            filepath = self.save_config(config, ip, device_name, model)
            if not filepath:
                return False, f"{ip}: 保存配置失败"

            return True, f"{ip}: 备份成功 ({device_name})"
        except Exception as e:
            logger.exception(f"备份过程中出错: {str(e)}")
            return False, f"{ip}: 备份失败 - {str(e)}"
        finally:
            try:
                # 安全退出
                chan.send("quit\n")  # 退出系统视图
                time.sleep(0.5)
                chan.send("quit\n")  # 退出登录
                time.sleep(0.5)
                chan.close()
            except:
                pass
            client.close()

    def backup_multiple_switches(self, devices, max_workers=5):
        """批量备份多个交换机配置"""
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for device in devices:
                ip = device['ip']
                username = device.get('username', 'admin')
                password = device['password']
                future = executor.submit(self.backup_single_switch, ip, username, password)
                futures[future] = ip

            for future in as_completed(futures):
                ip = futures[future]
                try:
                    success, message = future.result()
                    results.append((success, message))
                except Exception as e:
                    results.append((False, f"{ip}: 执行失败 - {str(e)}"))

        # 打印结果摘要
        print("\n=== 备份结果摘要 ===")
        success_count = sum(1 for success, _ in results if success)
        failure_count = len(results) - success_count

        for success, message in results:
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{status}: {message}")

        print(f"\n总计: {len(results)} 台设备, 成功: {success_count}, 失败: {failure_count}")
        return results


def main():
    # 设备列表 - 替换为实际设备信息
    # devices = [
    #     {'ip': '10.3.1.31', 'username': 'admin', 'password': 'Yunwei@1688'},
    #     {'ip': '10.3.1.32', 'username': 'admin', 'password': 'Yunwei@1688'},
    #     {'ip': '10.3.1.33', 'username': 'admin', 'password': 'Yunwei@1688'},
    #     {'ip': '10.3.1.34', 'username': 'admin', 'password': 'Yunwei@1688'},
    #     {'ip': '10.3.1.35', 'username': 'admin', 'password': 'Yunwei@1688'},
    #
    #     # 添加更多设备...
    # ]
    # 从文件读取IP地址列表
    ip_list_file = 'ip_list_test.txt'

    # 检查文件是否存在
    if not os.path.exists(ip_list_file):
        print(f"错误: IP列表文件不存在 - {ip_list_file}")
        return

    # 读取IP地址
    devices = []
    with open(ip_list_file, 'r') as f:
        for line in f:
            # 清理行内容
            ip = line.strip()

            # 跳过空行和注释
            if not ip or ip.startswith('#'):
                continue

            # 添加到设备列表
            devices.append({
                'ip': ip,
                'username': 'admin',
                'password': 'Yunwei@1688'
            })

    # 创建备份实例
    backup_tool = HuaweiSwitchBackup(output_dir='D:/HUAWEI_SWITCH/ConfigBackups')

    # 执行备份
    backup_tool.backup_multiple_switches(devices)


if __name__ == "__main__":
    main()