"""
测试进度条高度配置是否正确加载
"""
import json
from pathlib import Path
from gaiya.utils import path_utils

# 获取应用目录
app_dir = path_utils.get_app_dir()
config_file = app_dir / 'config.json'

print(f"应用目录: {app_dir}")
print(f"配置文件: {config_file}")
print(f"配置文件存在: {config_file.exists()}")

if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    bar_height = config.get('bar_height', '未找到')
    print(f"\n当前配置的进度条高度: {bar_height}px")

    if bar_height == 10:
        print("✅ 配置正确：进度条高度为 10px（细）")
    elif bar_height == 20:
        print("⚠️  配置为默认值：进度条高度为 20px（标准）")
    elif bar_height == 30:
        print("⚠️  配置为：进度条高度为 30px（粗）")
    else:
        print(f"ℹ️  自定义高度：{bar_height}px")
else:
    print("\n❌ 配置文件不存在！")
    print("   请先运行 GaiYa 应用生成默认配置")
