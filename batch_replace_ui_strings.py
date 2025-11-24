#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch replace hardcoded Chinese strings with i18n calls"""

import json
import re
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def escape_for_regex(text):
    """Escape special regex characters"""
    return re.escape(text)

def main():
    print("=" * 80)
    print("批量替换硬编码中文为 i18n 调用")
    print("=" * 80)
    print()

    # Load translation plan
    with open('auto_translation_plan.json', 'r', encoding='utf-8') as f:
        plan = json.load(f)

    matched_keys = plan['matched_keys']

    print(f"计划替换 {len(matched_keys)} 处硬编码")
    print()

    # Read config_gui.py
    config_path = Path('config_gui.py')
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"文件总行数: {len(lines)}")
    print()

    # Create backup
    backup_path = config_path.with_suffix('.py.backup_batch_auto')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"✓ 备份已创建: {backup_path}")
    print()

    # Group by line number to handle multiple replacements on same line
    line_replacements = {}
    for match in matched_keys:
        line_num = match['item']['line']
        if line_num not in line_replacements:
            line_replacements[line_num] = []

        line_replacements[line_num].append({
            'text': match['item']['text'],
            'key': match['key'],
            'code': match['item']['code']
        })

    print(f"需要修改 {len(line_replacements)} 行")
    print()
    print("=" * 80)
    print("开始替换...")
    print("=" * 80)
    print()

    replaced_count = 0
    failed_count = 0
    batch_size = 20

    for batch_start in range(0, len(line_replacements), batch_size):
        batch_lines = list(line_replacements.keys())[batch_start:batch_start + batch_size]

        print(f"\n批次 {batch_start//batch_size + 1} (行 {batch_lines[0]} - {batch_lines[-1]})")

        for line_num in batch_lines:
            replacements = line_replacements[line_num]
            idx = line_num - 1

            if idx >= len(lines):
                print(f"  ❌ 行 {line_num}: 超出范围")
                failed_count += len(replacements)
                continue

            original_line = lines[idx]
            modified_line = original_line

            for repl in replacements:
                text = repl['text']
                key = repl['key']

                # Try different quote styles
                patterns = [
                    f'"{text}"',
                    f"'{text}'",
                    f'"{text}"',  # Smart quotes
                ]

                replaced_this = False
                for pattern in patterns:
                    if pattern in modified_line:
                        # Build i18n call
                        i18n_call = f'self.i18n.t("{key}")'
                        modified_line = modified_line.replace(pattern, i18n_call)
                        replaced_this = True
                        break

                if replaced_this:
                    replaced_count += 1
                else:
                    # Try to find the Chinese text even without exact quotes
                    if text in modified_line and 'self.i18n.t(' not in modified_line:
                        print(f"  ⚠️  行 {line_num}: 找到文本但无法精确替换: {text[:30]}")
                        failed_count += 1
                    # Silently skip if already replaced by earlier batch

            if modified_line != original_line:
                lines[idx] = modified_line

        print(f"  完成 {len(batch_lines)} 行")

    print()
    print("=" * 80)
    print(f"替换完成")
    print("=" * 80)
    print()
    print(f"✓ 成功替换: {replaced_count}")
    print(f"⚠️  需要手动处理: {failed_count}")
    print()

    # Write updated file
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"✓ 文件已更新: {config_path}")
    print()
    print("=" * 80)
    print("重要提示:")
    print("=" * 80)
    print("1. 由于替换数量巨大，请务必测试应用")
    print("2. 如有问题，可从备份恢复:")
    print(f"   cp {backup_path} config_gui.py")
    print("3. 建议先测试关键功能，确认翻译正常显示")
    print("=" * 80)

if __name__ == '__main__':
    main()
