#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive scan of all UI Chinese strings in config_gui.py"""

import re
import json
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def is_user_facing_context(line):
    """Check if the line contains user-facing UI elements"""
    ui_indicators = [
        'QLabel(',
        'QPushButton(',
        'QCheckBox(',
        'QRadioButton(',
        'setWindowTitle(',
        'setText(',
        'setToolTip(',
        'setPlaceholderText(',
        'addItem(',
        'QMessageBox.',
        'QTabWidget',
        'setTabText(',
        '.format(',
    ]

    return any(indicator in line for indicator in ui_indicators)

def should_skip(line):
    """Check if line should be skipped"""
    skip_patterns = [
        'logging.',
        '"""',
        "'''",
        '#',
        'self.i18n.t(',
        'i18n.t(',
    ]

    line_stripped = line.strip()

    # Skip if already using i18n
    if any(pattern in line for pattern in skip_patterns[:2]):
        return True

    # Skip if it's already translated
    if 'self.i18n.t(' in line or 'i18n.t(' in line:
        return True

    return False

def main():
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("=" * 80)
    print("全面扫描 config_gui.py 中的用户界面中文字符串")
    print("=" * 80)
    print()

    chinese_pattern = r'["\']([^"\']*[\u4e00-\u9fa5][^"\']*)["\']'

    ui_strings = []
    other_strings = []

    for line_num, line in enumerate(lines, 1):
        if should_skip(line):
            continue

        matches = re.findall(chinese_pattern, line)
        for match in matches:
            if len(match.strip()) == 0:
                continue

            item = {
                'line': line_num,
                'text': match.strip(),
                'code': line.strip()
            }

            if is_user_facing_context(line):
                ui_strings.append(item)
            else:
                other_strings.append(item)

    print(f"用户界面中文字符串: {len(ui_strings)}")
    print(f"其他中文字符串: {len(other_strings)}")
    print()

    # Group by line number to avoid duplicates
    unique_ui = {}
    for item in ui_strings:
        if item['line'] not in unique_ui:
            unique_ui[item['line']] = item

    print("=" * 80)
    print(f"需要翻译的用户界面文本 (前50项)")
    print("=" * 80)
    print()

    sorted_items = sorted(unique_ui.values(), key=lambda x: x['line'])

    for i, item in enumerate(sorted_items[:50], 1):
        print(f"{i}. 行 {item['line']}: {item['text'][:60]}")
        if i % 10 == 0:
            print()

    if len(sorted_items) > 50:
        print(f"... 还有 {len(sorted_items) - 50} 项")

    print()
    print("=" * 80)
    print("统计")
    print("=" * 80)
    print(f"总计需要翻译: {len(unique_ui)} 项")
    print()

    # Save to file
    output = {
        'total_ui_strings': len(unique_ui),
        'items': sorted_items
    }

    with open('all_ui_chinese_strings.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("✓ 完整清单已保存到: all_ui_chinese_strings.json")
    print()
    print("建议:")
    print(f"  1. 审查这 {len(unique_ui)} 项是否都需要翻译")
    print(f"  2. 排除按钮/标签已经通过其他方式翻译的")
    print(f"  3. 创建批量翻译脚本处理剩余项目")

if __name__ == '__main__':
    main()
