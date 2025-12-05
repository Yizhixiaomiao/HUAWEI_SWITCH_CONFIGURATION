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

    def get_configuration(self, chan):
        """获取交换机配置"""
        try:
            chan.send("screen-length 0 temporary\n")
            time.sleep(0.3)
            # 清空缓冲区
            while chan.recv_ready():
                chan.recv(1024)

            with open('Command.txt', 'r') as f:
                cli_list = f.readlines()

            # 执行 CLI
            for cmd in cli_list:
                chan.send(cmd.rstrip() + "\n")
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

    def backup_single_switch(self, ip, username, password):
        """备份单个交换机配置"""
        client = self.connect_to_switch(ip, username, password)
        if not client:
            return False, f"{ip}: 连接失败"

        chan = None
        try:
            chan = client.invoke_shell()
            time.sleep(1)

            # ---------------------------
            # ✔ 修复：一次获取全部信息
            # ---------------------------
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
                executor.submit(self.backup_single_switch, d['ip'], d['username'], d['password']): d['ip']
                for d in devices
            }

            for future in as_completed(future_map):
                ip = future_map[future]
                try:
                    success, message = future.result()
                    results.append((success, message))
                except Exception as e:
                    results.append((False, f"{ip}: 执行失败 - {str(e)}"))

        print("\n=== 备份结果摘要 ===")
        success_count = sum(1 for s, _ in results if s)
        failure_count = len(results) - success_count

        for success, message in results:
            print(f"{'✅ 成功' if success else '❌ 失败'}: {message}")

        print(f"\n总计: {len(results)} 台设备, 成功: {success_count}, 失败: {failure_count}")
        return results


def main():
    ip_list_file = 'ip_list.txt'
    if not os.path.exists(ip_list_file):
        print(f"错误: IP列表文件不存在 - {ip_list_file}")
        return

    devices = []
    with open(ip_list_file, 'r') as f:
        for line in f:
            ip = line.strip()
            if not ip or ip.startswith('#'):
                continue

            devices.append({
                'ip': ip,
                'username': 'admin',
                'password': 'Yunwei@1688'
            })

    backup_tool = HuaweiSwitchBackup(output_dir='D:/HUAWEI_SWITCH/ConfigBackups')
    backup_tool.backup_multiple_switches(devices)


if __name__ == "__main__":
    main()
