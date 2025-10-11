from netmiko import ConnectHandler

# 定义华为交换机连接参数
huawei_switch = {
    'device_type': 'huawei',  # Netmiko设备类型
    'ip': '10.3.1.147' ,  # 交换机的管理IP
    'username': 'admin',      # SSH用户名
    'password': 'Yunwei@1688', # SSH密码
    'port': 22,               # SSH端口，默认是22
}

try:
    # 建立连接
    with ConnectHandler(**huawei_switch) as net_connect:
        # 发送命令，例如查看版本信息
        output = net_connect.send_command('display version')
        print("交换机版本信息：")
        print(output)
except Exception as e:
    print(f"连接或执行命令失败: {e}")