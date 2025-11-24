#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取 auth_ui.py 中的所有中文字符串
"""

import re

def extract_chinese_strings():
    """提取中文字符串并记录行号"""

    with open('gaiya/ui/auth_ui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 匹配包含中文的字符串
    pattern = r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']'

    results = []
    for line_num, line in enumerate(lines, 1):
        # 跳过注释和文档字符串
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        matches = re.findall(pattern, line)
        for match in matches:
            # 过滤掉太长的字符串（可能是文档）和多行字符串
            if len(match) < 200 and '\n' not in match:
                results.append({
                    'line': line_num,
                    'text': match,
                    'code': line.strip()
                })

    # 写入结果到文件
    with open('auth_ui_strings.txt', 'w', encoding='utf-8') as f:
        f.write(f"=== auth_ui.py 中文字符串提取 ===\n")
        f.write(f"共找到 {len(results)} 个中文字符串\n\n")

        for item in results:
            f.write(f"Line {item['line']}: {item['text']}\n")
            # f.write(f"  Code: {item['code']}\n\n")

    print(f"提取完成！共找到 {len(results)} 个中文字符串")
    print(f"结果已保存到 auth_ui_strings.txt")

    return results

if __name__ == '__main__':
    results = extract_chinese_strings()
