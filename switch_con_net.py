import csv
from netmiko import ConnectHandler, exceptions
from datetime import datetime
import getpass


def configure_switches(device_file, command_file, output_dir="./output/"):
    """
    批量配置华为交换机并保存结果

    参数:
        device_file (str): 设备信息CSV文件路径
        command_file (str): 命令文件路径
        output_dir (str): 输出目录路径
    """
    # 读取配置命令
    try:
        with open(command_file, encoding='utf-8') as f:
            commands = [cmd.strip() for cmd in f.readlines() if cmd.strip()]
    except FileNotFoundError:
        print(f"错误: 命令文件 {command_file} 未找到")
        return
    except Exception as e:
        print(f"读取命令文件时出错: {str(e)}")
        return

    # 读取交换机信息
    devices = []
    try:
        with open(device_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                devices.append(row)
    except FileNotFoundError:
        print(f"错误: 设备文件 {device_file} 未找到")
        return
    except Exception as e:
        print(f"读取设备文件时出错: {str(e)}")
        return

    # 创建输出目录
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历设备并配置
    for device in devices:
        host = device.get('ip', 'unknown')
        log_filename = f"{output_dir}{host}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        try:
            print(f"正在连接设备 {host}...")

            # 建立连接
            connection = ConnectHandler(
                device_type='huawei',
                host=device['ip'],
                username=device['username'],
                password=device['password'],
                port=int(device.get('port', 22))
            )

            # 禁用分页
            connection.send_command('screen-length 0 temporary')

            # 执行命令并收集输出
            full_output = f"设备配置执行记录\n设备IP: {host}\n执行时间: {datetime.now()}\n\n"

            for cmd in commands:
                output = connection.send_command(cmd)
                full_output += f"命令: {cmd}\n输出:\n{output}\n{'=' * 50}\n"

            # 保存输出到文件
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(full_output)

            print(f"配置完成，结果已保存到 {log_filename}")

            # 关闭连接
            connection.disconnect()

        except exceptions.NetmikoAuthenticationException:
            error_msg = f"设备 {host} 认证失败（用户名/密码错误）"
            print(error_msg)
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(error_msg)
        except exceptions.NetmikoTimeoutException:
            error_msg = f"设备 {host} 连接超时"
            print(error_msg)
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(error_msg)
        except KeyError as e:
            error_msg = f"设备文件缺少必要字段: {str(e)}"
            print(error_msg)
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(error_msg)
        except Exception as e:
            error_msg = f"设备 {host} 发生未知错误: {str(e)}"
            print(error_msg)
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(error_msg)


if __name__ == "__main__":
    # 输入文件设置
    device_file ="./ip_list.csv"  # CSV设备文件
    command_file ="./command.txt"  # 命令文本文件
    output_dir = "./results/"  # 输出目录

    # 执行配置
    configure_switches(device_file, command_file, output_dir)