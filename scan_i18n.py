#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描硬编码的中文字符串"""
import re
from pathlib import Path

# 扫描模式: 字符串中包含中文
pattern = re.compile(r'["\']([^"\']*[\u4e00-\u9fa5]+[^"\']*)["\']')

files = list(Path('gaiya').rglob('*.py')) + [Path('config_gui.py')]

ui_strings = []
for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                # 跳过注释和文档字符串
                if line.strip().startswith('#') or '"""' in line or "'''" in line:
                    continue
                # 跳过logger调用
                if 'logger.' in line or 'logging.' in line:
                    continue
                # 查找中文字符串
                matches = pattern.findall(line)
                for match in matches:
                    if any('\u4e00' <= c <= '\u9fa5' for c in match):
                        ui_strings.append(f'{file}:{i}: {match[:60]}')
    except Exception as e:
        print(f'Error processing {file}: {e}')

# 输出前100个
for s in ui_strings[:100]:
    print(s)

print(f'\n总计发现 {len(ui_strings)} 个硬编码中文字符串')
