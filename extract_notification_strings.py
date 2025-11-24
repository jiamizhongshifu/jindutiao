#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提取 create_notification_tab() 方法中的中文字符串"""

import re

# Read the file
with open('config_gui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Define the range - notification tab method (lines 2750-2947)
start_line = 2750
end_line = 2947

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

# Write to file
with open('create_notification_tab_strings.txt', 'w', encoding='utf-8') as f:
    f.write('=== 通知设置方法中文字符串提取 ===\n')
    f.write(f'范围: 第{start_line}-{end_line}行\n')
    f.write(f'共找到 {len(chinese_strings)} 个中文字符串\n\n')

    for line_num, string in chinese_strings:
        f.write(f'Line {line_num}: {string}\n')

print(f'\nFound {len(chinese_strings)} Chinese strings. Results saved to create_notification_tab_strings.txt')
