#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提取 create_about_tab() 方法中的中文字符串"""

import re

# Read the file
with open('config_gui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# create_about_tab starts at 6792 (from grep result)
start_line = 6792
end_line = None

# Find method end
for i in range(start_line, len(lines)):
    line = lines[i]
    # Check if this is a new method definition (at the same indentation level)
    if i > start_line and re.match(r'    def \w+', line):
        end_line = i
        break

if end_line is None:
    end_line = len(lines)

# Extract Chinese strings
chinese_strings = []
for i in range(start_line - 1, min(end_line, len(lines))):
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
            if match and len(match.strip()) > 0:
                chinese_strings.append((line_num, match))

# Write to file
with open('create_about_tab_strings.txt', 'w', encoding='utf-8') as f:
    f.write('=== 关于页面方法中文字符串提取 ===\n')
    f.write(f'范围: 第{start_line}-{end_line if end_line else "EOF"}行\n')
    f.write(f'共找到 {len(chinese_strings)} 个中文字符串\n\n')

    for line_num, string in chinese_strings:
        f.write(f'Line {line_num}: {string}\n')

print(f'\nFound {len(chinese_strings)} Chinese strings in lines {start_line}-{end_line if end_line else "EOF"}')
print('Results saved to create_about_tab_strings.txt')
