#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将config_gui.py个人中心部分的硬编码中文替换为i18n调用
"""

import re
import json
from pathlib import Path

def load_replacement_map():
    """加载替换映射"""
    with open('account_center_replacement_map.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def apply_replacements_to_file(file_path, replacement_map, start_line, end_line):
    """在指定行范围内应用替换"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    replacements_made = []

    # 对指定范围的行进行处理
    for i in range(start_line - 1, min(end_line, len(lines))):
        original_line = lines[i]
        modified_line = original_line

        # 按照最长匹配优先的原则排序
        sorted_texts = sorted(replacement_map.keys(), key=len, reverse=True)

        for zh_text in sorted_texts:
            i18n_key = replacement_map[zh_text]

            # 尝试多种匹配模式
            patterns = [
                # 双引号字符串
                (f'"{re.escape(zh_text)}"', f'tr("{i18n_key}")'),
                # 单引号字符串
                (f"'{re.escape(zh_text)}'", f'tr("{i18n_key}")'),
            ]

            for pattern, replacement in patterns:
                if re.search(pattern, modified_line):
                    new_line = re.sub(pattern, replacement, modified_line)
                    if new_line != modified_line:
                        replacements_made.append({
                            'line': i + 1,
                            'original': original_line.strip(),
                            'modified': new_line.strip(),
                            'zh_text': zh_text,
                            'i18n_key': i18n_key
                        })
                        modified_line = new_line
                        break  # 每行只替换一次匹配

        lines[i] = modified_line

    return lines, replacements_made

def main():
    print("Applying i18n replacements to config_gui.py account center section...")

    file_path = Path('config_gui.py')
    replacement_map = load_replacement_map()

    print(f"Loaded {len(replacement_map)} replacement mappings")

    # 个人中心范围：3016-6835行
    start_line = 3016
    end_line = 6835

    modified_lines, replacements = apply_replacements_to_file(
        file_path, replacement_map, start_line, end_line
    )

    if replacements:
        # 保存修改后的文件
        backup_path = Path('config_gui.py.backup_account_i18n')
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(file_path, 'r', encoding='utf-8') as original:
                f.write(original.read())

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)

        print(f"\nMade {len(replacements)} replacements")
        print(f"Backup saved to: {backup_path}")
        print(f"Modified file saved to: {file_path}")

        # 保存详细替换日志
        log_path = Path('account_i18n_replacement_log.txt')
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("Account Center i18n Replacement Log\n")
            f.write("=" * 80 + "\n\n")
            for r in replacements[:50]:  # 只显示前50个
                f.write(f"Line {r['line']}:\n")
                f.write(f"  Chinese: {r['zh_text']}\n")
                f.write(f"  i18n Key: {r['i18n_key']}\n")
                f.write(f"  Before: {r['original'][:100]}\n")
                f.write(f"  After:  {r['modified'][:100]}\n")
                f.write("\n")
            if len(replacements) > 50:
                f.write(f"... and {len(replacements) - 50} more replacements\n")

        print(f"Replacement log saved to: {log_path}")

        # 保存JSON格式的替换记录
        json_log_path = Path('account_i18n_replacement_log.json')
        with open(json_log_path, 'w', encoding='utf-8') as f:
            json.dump(replacements, f, ensure_ascii=False, indent=2)

        print(f"JSON log saved to: {json_log_path}")
    else:
        print("\nNo replacements were made.")

if __name__ == '__main__':
    main()
