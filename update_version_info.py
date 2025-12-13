#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本信息同步脚本
自动从 version.py 读取版本号并更新 version_info.txt

用法:
    python update_version_info.py
"""

import sys
import os
from pathlib import Path

# Windows 命令行编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def update_version_info():
    """从 version.py 读取版本号并更新 version_info.txt"""

    # 导入版本信息
    try:
        from version import (
            VERSION_MAJOR,
            VERSION_MINOR,
            VERSION_PATCH,
            __version__,
            __app_name__,
            get_exe_name
        )
    except ImportError as e:
        print(f"❌ 错误: 无法导入 version.py: {e}")
        sys.exit(1)

    # 版本号元组 (用于 filevers 和 prodvers)
    version_tuple = f"({VERSION_MAJOR}, {VERSION_MINOR}, {VERSION_PATCH}, 0)"

    # 版本字符串 (用于 FileVersion 和 ProductVersion)
    version_string = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}.0"

    # EXE 文件名
    exe_name = f"{get_exe_name()}.exe"

    # 读取模板文件
    version_info_path = Path("version_info.txt")
    if not version_info_path.exists():
        print(f"❌ 错误: 找不到 version_info.txt 文件")
        sys.exit(1)

    print(f"📖 读取文件: {version_info_path}")
    content = version_info_path.read_text(encoding='utf-8')

    # 替换版本号
    print(f"🔄 更新版本号: {__version__} ({version_string})")

    # 1. 替换 filevers 和 prodvers
    import re

    # 替换 filevers=(x, x, x, x) 格式
    content = re.sub(
        r'filevers=\([0-9]+,\s*[0-9]+,\s*[0-9]+,\s*[0-9]+\)',
        f'filevers={version_tuple}',
        content
    )

    content = re.sub(
        r'prodvers=\([0-9]+,\s*[0-9]+,\s*[0-9]+,\s*[0-9]+\)',
        f'prodvers={version_tuple}',
        content
    )

    # 2. 替换 StringStruct 中的版本字符串
    # FileVersion
    content = re.sub(
        r"StringStruct\(u'FileVersion',\s*u'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'\)",
        f"StringStruct(u'FileVersion', u'{version_string}')",
        content
    )

    # ProductVersion
    content = re.sub(
        r"StringStruct\(u'ProductVersion',\s*u'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'\)",
        f"StringStruct(u'ProductVersion', u'{version_string}')",
        content
    )

    # 3. 替换 OriginalFilename (EXE文件名)
    content = re.sub(
        r"StringStruct\(u'OriginalFilename',\s*u'[^']+'\)",
        f"StringStruct(u'OriginalFilename', u'{exe_name}')",
        content
    )

    # 4. 替换 InternalName 和 ProductName (保持为 GaiYa 而非 PyDayBar)
    content = re.sub(
        r"StringStruct\(u'InternalName',\s*u'[^']+'\)",
        f"StringStruct(u'InternalName', u'{__app_name__}')",
        content
    )

    content = re.sub(
        r"StringStruct\(u'ProductName',\s*u'[^']+'\)",
        f"StringStruct(u'ProductName', u'{__app_name__}')",
        content
    )

    # 写回文件
    version_info_path.write_text(content, encoding='utf-8')

    print(f"✅ 成功更新 version_info.txt:")
    print(f"   - filevers/prodvers: {version_tuple}")
    print(f"   - FileVersion/ProductVersion: {version_string}")
    print(f"   - OriginalFilename: {exe_name}")
    print(f"   - InternalName/ProductName: {__app_name__}")


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 版本信息同步脚本")
    print("=" * 60)

    update_version_info()

    print("=" * 60)
    print("✅ 同步完成!")
    print("=" * 60)
