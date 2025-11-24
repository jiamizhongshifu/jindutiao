#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取 quota_exhausted_dialog.py 中的所有中文字符串

用于国际化工作的准备阶段
"""

import re

def extract_chinese_strings(file_path):
    """从文件中提取所有包含中文的字符串"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # 匹配引号中的字符串
    pattern = r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']'

    chinese_strings = []
    for line_num, line in enumerate(lines, 1):
        matches = re.finditer(pattern, line)
        for match in matches:
            string_content = match.group(1)
            chinese_strings.append({
                'line': line_num,
                'string': string_content,
                'context': line.strip()
            })

    return chinese_strings

def main():
    file_path = 'gaiya/ui/onboarding/quota_exhausted_dialog.py'
    strings = extract_chinese_strings(file_path)

    # 将结果写入文件
    output_file = 'quota_dialog_strings_raw.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"从 {file_path} 中提取到 {len(strings)} 个中文字符串：\n\n")

        # 按行号排序
        strings.sort(key=lambda x: x['line'])

        # 写入所有字符串
        for item in strings:
            f.write(f"Line {item['line']:3d}: {item['string']}\n")
            f.write(f"          上下文: {item['context'][:80]}...\n")
            f.write("\n")

        # 统计唯一字符串
        unique_strings = set(item['string'] for item in strings)
        f.write(f"\n唯一字符串数量: {len(unique_strings)}\n")
        f.write("\n唯一字符串列表:\n")
        for s in sorted(unique_strings):
            f.write(f"  - {s}\n")

    print(f"提取完成！共{len(strings)}个字符串，{len(unique_strings)}个唯一字符串")
    print(f"结果已保存到: {output_file}")

if __name__ == '__main__':
    main()
