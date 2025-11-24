#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 welcome_dialog.py 提取所有中文字符串
"""

import re

def extract_strings():
    """提取字符串"""

    file_path = 'gaiya/ui/onboarding/welcome_dialog.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取所有中文字符串（单引号和双引号）
    pattern = r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']'
    matches = re.findall(pattern, content)

    # 去重并保持顺序
    strings = []
    seen = set()
    for s in matches:
        if s not in seen and s.strip():
            strings.append(s)
            seen.add(s)

    # 输出到文件
    output_file = 'welcome_dialog_strings_raw.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"从 {file_path} 中提取到 {len(strings)} 个中文字符串：\n\n")

        for i, s in enumerate(strings, 1):
            # 查找字符串在文件中的行号
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if s in line:
                    f.write(f"{i}. (Line {line_num}) {s}\n")
                    break

    # 输出到控制台（避免 emoji 编码问题）
    result_msg = f"提取完成! 共找到 {len(strings)} 个唯一的中文字符串\n结果已保存到: {output_file}"
    with open('extraction_result.txt', 'w', encoding='utf-8') as rf:
        rf.write(result_msg)
    print(result_msg)

if __name__ == '__main__':
    extract_strings()
