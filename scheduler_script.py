import os
import subprocess

if __name__ == "__main__":
    # 按顺序执行两个脚本
    subprocess.run(["python", "switch_con_para.py"])
    subprocess.run(["python", "switch_info.py"])