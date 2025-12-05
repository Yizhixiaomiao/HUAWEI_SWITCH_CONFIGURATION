import os
import re
from datetime import datetime
import csv


# 全局变量（不改变你已有结构，只新增）
custom_keyword = ""
custom_column_name = ""


def parse_filename(filename):
    """解析文件名，提取系统名称、交换机型号、IP地址和提取时间"""
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split('__', 3)

    if len(parts) < 4:
        return None

    system_name = parts[1]
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


def check_8021x_config(file_path):
    """检查配置文件中是否包含domain sangfor_802.1x"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if re.search(r'domain\s+sangfor_802\.1x', content):
            return 'domain sangfor_802.1x'
        else:
            return '未刷入'
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")
        return '未刷入'


# ★ 新增功能：搜索自定义关键字
def search_custom_config(file_path, keyword):
    """在配置文件中搜索用户自定义关键字"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if keyword in line:
                    return line.strip()
        return "未查询到"
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")
        return "未查询到"


def get_cfg_files(directory):
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
            file_path = os.path.join(directory, filename)

            # 802.1x 检查保持不变
            parsed["是否刷入802.1x"] = check_8021x_config(file_path)

            # ★ 新增：自定义关键字搜索
            if custom_keyword and custom_column_name:
                parsed[custom_column_name] = search_custom_config(file_path, custom_keyword)

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

    fieldnames = ['系统名称', '交换机型号', 'IP地址', '提取时间', '是否刷入802.1x']

    # ★ 自动加入用户自定义列
    if custom_column_name:
        fieldnames.append(custom_column_name)

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(result)

    print(f"\n结果已保存到 {output_file} (共 {len(results)} 条记录)")


if __name__ == "__main__":

    # ★ 用户交互：自定义配置关键字与 CSV 列名
    print("如需查询配置内容，请输入关键字；直接回车可跳过此功能。")
    custom_keyword = input("请输入要查询的配置关键字（例如 authentication-mode）：").strip()

    if custom_keyword:
        custom_column_name = input("请输入该字段在 CSV 中显示的列名（例如 认证模式）：").strip()
        print(f"将新增 CSV 列名：{custom_column_name}，搜索关键字：{custom_keyword}\n")
    else:
        custom_column_name = ""

    # 设置工作目录
    directory = 'D:\\HUAWEI_SWITCH\\ConfigBackups'
    output_file = 'switch_info.csv'

    print(f"开始处理目录: {os.path.abspath(directory)}")

    results = process_directory(directory)

    save_to_csv(results, output_file)
import os
import re
from datetime import datetime
import csv


# 全局变量（不改变你已有结构，只新增）
custom_keyword = ""
custom_column_name = ""


def parse_filename(filename):
    """解析文件名，提取系统名称、交换机型号、IP地址和提取时间"""
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split('__', 3)

    if len(parts) < 4:
        return None

    system_name = parts[1]
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


def check_8021x_config(file_path):
    """检查配置文件中是否包含domain sangfor_802.1x"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if re.search(r'domain\s+sangfor_802\.1x', content):
            return 'domain sangfor_802.1x'
        else:
            return '未刷入'
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")
        return '未刷入'


# ★ 新增功能：搜索自定义关键字
def search_custom_config(file_path, keyword):
    """在配置文件中搜索用户自定义关键字"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if keyword in line:
                    return line.strip()
        return "未查询到"
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")
        return "未查询到"


def get_cfg_files(directory):
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
            file_path = os.path.join(directory, filename)

            # 802.1x 检查保持不变
            parsed["是否刷入802.1x"] = check_8021x_config(file_path)

            # ★ 新增：自定义关键字搜索
            if custom_keyword and custom_column_name:
                parsed[custom_column_name] = search_custom_config(file_path, custom_keyword)

            results.append(parsed)
            print(f"✓ 已解析: {filename}")
        else:
            print(f"✗ 无法解析: {filename}")

    return results

def save_to_csv(results, output_file):
    """将结果增量保存为CSV文件（不会覆盖旧列），使用复合键保证行唯一性和对齐"""
    if not results:
        print("没有有效数据可保存")
        return

    # 新数据的字段（基础字段 + 可能的新自定义列）
    new_fieldnames = ['系统名称', '交换机型号', 'IP地址', '提取时间', '是否刷入802.1x']
    if custom_column_name:
        new_fieldnames.append(custom_column_name)

    # 生成一个辅助函数来返回行的复合唯一键（IP|系统名称|提取时间）
    def make_key(row_dict):
        return f"{row_dict.get('IP地址','').strip()}|{row_dict.get('系统名称','').strip()}|{row_dict.get('提取时间','').strip()}"

    # 如果 CSV 不存在 -> 直接写入新文件（初始化）
    if not os.path.exists(output_file):
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=new_fieldnames)
            writer.writeheader()
            for result in results:
                # 确保写入行包含所有必须字段
                row = {fn: result.get(fn, "未查询到") for fn in new_fieldnames}
                writer.writerow(row)
        print(f"\n已创建新 CSV 文件: {output_file} (共 {len(results)} 条记录)")
        return

    # CSV 已存在 -> 读取旧内容并合并
    print("检测到 CSV 已存在，执行增量合并……")

    old_rows = []
    old_fieldnames = []

    with open(output_file, 'r', encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        old_fieldnames = reader.fieldnames or []
        for row in reader:
            old_rows.append(row)

    # 合并字段名（保持旧字段顺序，新增字段追加）
    merged_fieldnames = list(old_fieldnames)
    for fn in new_fieldnames:
        if fn not in merged_fieldnames:
            merged_fieldnames.append(fn)

    # 建立以复合键为索引的字典，保持旧行顺序
    merged_data = {}
    merged_keys_in_order = []

    for row in old_rows:
        key = make_key(row)
        # 标准化行：保留原来的键值（字符串）
        merged_data[key] = dict(row)  # shallow copy
        merged_keys_in_order.append(key)

    # 将新结果合并进去（更新已有行或新增行）
    for result in results:
        key = make_key(result)
        if key in merged_data:
            # 仅用新 result 中实际存在的字段覆盖/更新旧行（避免把旧字段设为未查询到）
            for k, v in result.items():
                merged_data[key][k] = v
        else:
            # 新行：创建并确保包含旧列中可能存在的字段（先填未查询到）
            new_row = {fn: "未查询到" for fn in merged_fieldnames}
            # 覆盖为 result 中的实际值
            for k, v in result.items():
                new_row[k] = v
            merged_data[key] = new_row
            merged_keys_in_order.append(key)

    # 补全所有行缺失字段为 "未查询到"
    for key in merged_keys_in_order:
        row = merged_data[key]
        for fn in merged_fieldnames:
            if fn not in row or row[fn] is None or str(row[fn]).strip() == "":
                row[fn] = "未查询到"

    # 写回 CSV（覆盖文件，但保留并合并了所有旧数据）
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=merged_fieldnames)
        writer.writeheader()
        for key in merged_keys_in_order:
            writer.writerow(merged_data[key])

    print(f"\nCSV 已增量更新完成：{output_file}（共 {len(merged_keys_in_order)} 条记录；列数：{len(merged_fieldnames)}）")



if __name__ == "__main__":

    # ★ 用户交互：自定义配置关键字与 CSV 列名
    print("如需查询配置内容，请输入关键字；直接回车可跳过此功能。")
    custom_keyword = input("请输入要查询的配置关键字（例如 authentication-mode）：").strip()

    if custom_keyword:
        custom_column_name = input("请输入该字段在 CSV 中显示的列名（例如 认证模式）：").strip()
        print(f"将新增 CSV 列名：{custom_column_name}，搜索关键字：{custom_keyword}\n")
    else:
        custom_column_name = ""

    # 设置工作目录
    directory = 'D:\\HUAWEI_SWITCH\\ConfigBackups'
    output_file = 'switch_info.csv'

    print(f"开始处理目录: {os.path.abspath(directory)}")

    results = process_directory(directory)

    save_to_csv(results, output_file)
