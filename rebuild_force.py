# -*- coding: utf-8 -*-
"""
强制重新打包脚本 - 处理文件被锁定的情况
"""
import os
import time
import subprocess
import sys

print("="*60)
print("强制重新打包 GaiYa")
print("="*60)
print()

exe_path = r"c:\Users\Sats\Downloads\jindutiao\dist\GaiYa-v1.6.exe"

# 1. 尝试多次删除exe
print("1. 尝试删除旧exe文件...")
for i in range(3):
    try:
        if os.path.exists(exe_path):
            os.remove(exe_path)
            print(f"   ✓ exe已删除")
            break
    except PermissionError:
        print(f"   尝试 {i+1}/3: 文件被占用,等待2秒...")
        time.sleep(2)
else:
    # 如果删除失败,重命名它
    try:
        backup_path = exe_path + ".old_" + str(int(time.time()))
        os.rename(exe_path, backup_path)
        print(f"   ✓ 已重命名为: {backup_path}")
    except Exception as e:
        print(f"   ✗ 无法删除或重命名: {e}")
        print("   继续尝试打包...")

print()

# 2. 运行PyInstaller
print("2. 开始打包...")
print()

try:
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "Gaiya.spec", "--noconfirm"],
        cwd=r"c:\Users\Sats\Downloads\jindutiao",
        capture_output=True,
        text=True,
        timeout=180
    )

    print(result.stdout)

    if result.returncode != 0:
        print("打包失败!")
        print(result.stderr)
        sys.exit(1)

except subprocess.TimeoutExpired:
    print("✗ 打包超时 (180秒)")
    sys.exit(1)

# 3. 验证结果
print()
print("3. 验证打包结果...")

if os.path.exists(exe_path):
    size = os.path.getsize(exe_path)
    mtime = time.ctime(os.path.getmtime(exe_path))
    print(f"   ✓ exe文件已生成")
    print(f"   文件大小: {size:,} 字节")
    print(f"   修改时间: {mtime}")
else:
    print(f"   ✗ exe文件不存在: {exe_path}")
    sys.exit(1)

print()
print("="*60)
print("✓ 打包完成!")
print("="*60)
