#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find all Chinese strings in config_gui.py for i18n analysis
"""

import re
from pathlib import Path

def find_chinese_strings(file_path):
    """Find all Chinese strings in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Pattern to match Chinese characters in strings
    # Matches both single and double quoted strings containing Chinese
    pattern = re.compile(r'["\']([^"\']*[\u4e00-\u9fff]+[^"\']*)["\']')

    results = []
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        matches = pattern.findall(line)
        for match in matches:
            # Skip if it's already wrapped in tr()
            if f'tr("{match}")' in line or f"tr('{match}')" in line:
                continue

            results.append({
                'line': line_num,
                'text': match,
                'context': line.strip()[:100]
            })

    return results

if __name__ == '__main__':
    file_path = Path('config_gui.py')
    output_file = Path('chinese_strings_found.txt')

    if not file_path.exists():
        print(f"Error: {file_path} not found")
        exit(1)

    print(f"Searching for Chinese strings in {file_path}...")
    print(f"Results will be written to {output_file}")

    results = find_chinese_strings(file_path)

    # Group by category
    theme_names = []
    ui_labels = []
    messages = []
    other = []

    for result in results:
        text = result['text']
        if any(keyword in text for keyword in ['专业', '自然', '橙色', '黑白', '蓝', '绿', '日落', '薰衣草', '深色']):
            theme_names.append(result)
        elif any(keyword in text for keyword in ['剩余', '次规划', '配额']):
            messages.append(result)
        elif len(text) <= 10 and ':' not in text:
            ui_labels.append(result)
        else:
            other.append(result)

    # Write results to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Chinese Strings Analysis for {file_path}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Found: {len(results)} Chinese strings\n\n")

        if theme_names:
            f.write(f"[Theme Names] ({len(theme_names)}):\n")
            for r in theme_names:
                f.write(f"  Line {r['line']:5d}: {r['text']}\n")

        if ui_labels:
            f.write(f"\n[UI Labels] ({len(ui_labels)}):\n")
            for r in ui_labels:
                f.write(f"  Line {r['line']:5d}: {r['text']}\n")

        if messages:
            f.write(f"\n[Messages] ({len(messages)}):\n")
            for r in messages:
                f.write(f"  Line {r['line']:5d}: {r['text']}\n")

        if other:
            f.write(f"\n[Other] ({len(other)}):\n")
            for r in other[:50]:  # Show first 50
                f.write(f"  Line {r['line']:5d}: {r['text']}\n")
            if len(other) > 50:
                f.write(f"  ... and {len(other) - 50} more\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Total: {len(results)} untranslated Chinese strings found\n")

    print(f"Analysis complete! Found {len(results)} Chinese strings")
    print(f"Results written to: {output_file}")
