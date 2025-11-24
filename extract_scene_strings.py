#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提取 create_scene_tab() 相关方法中的中文字符串"""

import re

# Read the file
with open('config_gui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Define the range - scene tab methods (lines 2449-2748)
start_line = 2449
end_line = 2748

# Extract Chinese strings
chinese_strings = []
for i in range(start_line - 1, end_line):
    line = lines[i]
    line_num = i + 1

    # Find all quoted strings containing Chinese characters
    patterns = [
        r'"([^"]*[\u4e00-\u9fff]+[^"]*)"',  # Double quotes
        r"'([^']*[\u4e00-\u9fff]+[^']*)'"   # Single quotes
    ]

    for pattern in patterns:
        matches = re.findall(pattern, line)
        for match in matches:
            # Skip if it's just a comment or logging format
            if match and len(match.strip()) > 0:
                chinese_strings.append((line_num, match))

# Write to file first (avoid console encoding issues)
with open('create_scene_tab_strings.txt', 'w', encoding='utf-8') as f:
    f.write('=== 场景设置相关方法中文字符串提取 ===\n')
    f.write(f'范围: 第{start_line}-{end_line}行\n')
    f.write(f'共找到 {len(chinese_strings)} 个中文字符串\n\n')

    for line_num, string in chinese_strings:
        f.write(f'Line {line_num}: {string}\n')

print(f'\nFound {len(chinese_strings)} Chinese strings. Results saved to create_scene_tab_strings.txt')
