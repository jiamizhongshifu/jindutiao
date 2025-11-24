#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit config_gui.py for hardcoded Chinese strings"""

import re
import json
import sys
from pathlib import Path
from collections import defaultdict

# Set UTF-8 output for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_chinese_strings_detailed(filepath):
    """Extract all Chinese strings with line numbers"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    results = []
    pattern = r'["\']([^"\']*[\u4e00-\u9fa5][^"\']*)["\']'

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        matches = re.finditer(pattern, line)
        for match in matches:
            text = match.group(1).strip()
            if text and any('\u4e00' <= c <= '\u9fa5' for c in text):
                # Check if it's using i18n
                if 'i18n.t(' not in line and 'self.i18n.t(' not in line:
                    results.append({
                        'line': line_num,
                        'text': text,
                        'code': line.strip()
                    })

    return results

def load_i18n_values(i18n_dir):
    """Load all translated values from i18n files"""
    all_values = set()
    i18n_path = Path(i18n_dir)

    for json_file in i18n_path.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def extract_values(d):
                """Recursively extract all values from nested dict"""
                for key, value in d.items():
                    if isinstance(value, dict):
                        extract_values(value)
                    elif isinstance(value, str):
                        all_values.add(value)

            extract_values(data)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    return all_values

def categorize_strings(strings):
    """Categorize strings by type"""
    categories = {
        'ui_labels': [],
        'messages': [],
        'errors': [],
        'tooltips': [],
        'dialogs': [],
        'others': []
    }

    keywords = {
        'errors': ['失败', '错误', '异常', '无法'],
        'messages': ['成功', '完成', '已', '正在'],
        'tooltips': ['提示', '说明', '帮助'],
        'dialogs': ['确认', '取消', '对话框', '弹窗']
    }

    for item in strings:
        text = item['text']
        categorized = False

        for category, kws in keywords.items():
            if any(kw in text for kw in kws):
                categories[category].append(item)
                categorized = True
                break

        if not categorized:
            if len(text) < 10:
                categories['ui_labels'].append(item)
            else:
                categories['others'].append(item)

    return categories

def main():
    print("=" * 80)
    print("配置界面翻译审计报告")
    print("=" * 80)
    print()

    # Extract Chinese strings from config_gui.py
    chinese_strings = extract_chinese_strings_detailed('config_gui.py')
    print(f"[1] 在 config_gui.py 中找到 {len(chinese_strings)} 个硬编码中文字符串")

    # Load i18n values
    i18n_values = load_i18n_values('i18n')
    print(f"[2] 从 i18n 文件加载了 {len(i18n_values)} 个翻译值")
    print()

    # Filter untranslated
    untranslated = []
    for item in chinese_strings:
        if item['text'] not in i18n_values:
            untranslated.append(item)

    print(f"[3] 未翻译字符串总数: {len(untranslated)}")
    print()

    # Categorize
    categories = categorize_strings(untranslated)

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("配置界面国际化审计报告")
    report.append("=" * 80)
    report.append(f"\n扫描文件: config_gui.py")
    report.append(f"扫描时间: {Path('config_gui.py').stat().st_mtime}")
    report.append(f"\n总计硬编码中文字符串: {len(chinese_strings)}")
    report.append(f"已翻译: {len(chinese_strings) - len(untranslated)}")
    report.append(f"未翻译: {len(untranslated)}")
    report.append(f"翻译完成率: {((len(chinese_strings) - len(untranslated)) / len(chinese_strings) * 100):.1f}%")
    report.append("\n" + "=" * 80)

    # Category breakdown
    report.append("\n## 分类统计\n")
    for cat_name, items in categories.items():
        if items:
            report.append(f"- {cat_name}: {len(items)} 项")

    # Detailed listing by category
    for cat_name, items in categories.items():
        if not items:
            continue

        report.append(f"\n\n## {cat_name.upper()} ({len(items)} 项)\n")
        report.append("-" * 80)

        for i, item in enumerate(items, 1):
            report.append(f"\n{i}. 第 {item['line']} 行:")
            report.append(f"   文本: {item['text']}")
            report.append(f"   代码: {item['code'][:100]}...")

    # Top 50 most common untranslated strings
    report.append("\n\n" + "=" * 80)
    report.append("## 最常见的未翻译字符串 (前50个)\n")
    report.append("-" * 80)

    string_counts = defaultdict(list)
    for item in untranslated:
        string_counts[item['text']].append(item['line'])

    sorted_strings = sorted(string_counts.items(), key=lambda x: len(x[1]), reverse=True)

    for i, (text, lines) in enumerate(sorted_strings[:50], 1):
        report.append(f"\n{i:2d}. \"{text}\"")
        report.append(f"    出现次数: {len(lines)}")
        report.append(f"    行号: {', '.join(map(str, lines[:10]))}" +
                     (f" ... 共{len(lines)}处" if len(lines) > 10 else ""))

    # Save report
    report_text = '\n'.join(report)

    with open('config_i18n_audit_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)

    # Also save JSON for programmatic use
    audit_data = {
        'total_strings': len(chinese_strings),
        'translated': len(chinese_strings) - len(untranslated),
        'untranslated': len(untranslated),
        'completion_rate': (len(chinese_strings) - len(untranslated)) / len(chinese_strings) * 100,
        'categories': {k: len(v) for k, v in categories.items()},
        'untranslated_details': untranslated[:100]  # First 100 for size
    }

    with open('config_i18n_audit_data.json', 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, ensure_ascii=False, indent=2)

    print("\n报告已保存:")
    print("  - config_i18n_audit_report.txt (详细报告)")
    print("  - config_i18n_audit_data.json (结构化数据)")
    print()
    print("=" * 80)
    print(f"翻译完成率: {audit_data['completion_rate']:.1f}%")
    print("=" * 80)

if __name__ == '__main__':
    main()
