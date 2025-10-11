import os
import re
from datetime import datetime
import csv


def parse_filename(filename):
    """解析文件名，提取系统名称、交换机型号、IP地址和提取时间"""
    # 移除文件扩展名
    base_name = os.path.splitext(filename)[0]

    # 使用双下划线分割文件名（最多分割4次）
    parts = base_name.split('__', 3)

    # 检查是否有足够的字段
    if len(parts) < 4:
        return None

    # 提取各字段
    system_name = parts[0]
    switch_model = parts[1]
    ip_address = parts[2]
    timestamp = parts[3]

    # 验证IP地址格式
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_address):
        return None

    # 解析时间戳
    try:
        # 处理时间戳中的下划线（日期和时间之间）
        if '_' in timestamp:
            date_part, time_part = timestamp.split('_')
        else:
            date_part = timestamp[:8]
            time_part = timestamp[8:]

        # 格式化时间
        extract_time = datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M%S")
        formatted_time = extract_time.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        formatted_time = timestamp  # 如果无法解析，保留原始时间戳

    return {
        "系统名称": system_name,
        "交换机型号": switch_model,
        "IP地址": ip_address,
        "提取时间": formatted_time
    }


def get_cfg_files(directory):
    """获取目录中所有.cfg文件"""
    return [f for f in os.listdir(directory)
            if f.endswith('.cfg') and os.path.isfile(os.path.join(directory, f))]


def process_directory(directory):
    """处理目录中的所有cfg文件"""
    results = []
    cfg_files = get_cfg_files(directory)

    if not cfg_files:
        print(f"在目录 {directory} 中未找到任何.cfg文件")
        return results

    print(f"找到 {len(cfg_files)} 个.cfg文件:")
    for filename in cfg_files:
        parsed = parse_filename(filename)
        if parsed:
            results.append(parsed)
            print(f"✓ 已解析: {filename}")
        else:
            print(f"✗ 无法解析: {filename}")

    return results


def save_to_csv(results, output_file):
    """将结果保存为CSV文件"""
    if not results:
        print("没有有效数据可保存")
        return

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['系统名称', '交换机型号', 'IP地址', '提取时间']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"\n结果已保存到 {output_file} (共 {len(results)} 条记录)")


if __name__ == "__main__":
    # 设置工作目录
    directory = 'D:\ConfigBackups'  # 当前目录
    output_file = 'switch_info.csv'

    print(f"开始处理目录: {os.path.abspath(directory)}")

    # 处理目录中的所有cfg文件
    results = process_directory(directory)

    # 保存结果到CSV
    save_to_csv(results, output_file)

    # 在Windows中自动打开CSV文件
    # if os.name == 'nt' and os.path.exists(output_file):
    #     try:
    #         os.startfile(output_file)
    #     except Exception as e:
    #         print(f"无法自动打开文件: {e}")