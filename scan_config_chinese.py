#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan config_gui.py for hardcoded Chinese strings"""

import re
import json
from pathlib import Path

def extract_chinese_strings(filepath):
    """Extract all Chinese strings from a Python file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match strings containing Chinese characters
    # This matches both single and double quoted strings
    pattern = r'["\']([^"\']*[\u4e00-\u9fa5][^"\']*)["\']'
    matches = re.findall(pattern, content)

    # Filter and clean
    chinese_strings = []
    for match in matches:
        # Skip if it's just whitespace or too short
        if len(match.strip()) > 0 and any('\u4e00' <= c <= '\u9fa5' for c in match):
            chinese_strings.append(match.strip())

    return list(set(chinese_strings))

def load_i18n_keys(i18n_dir):
    """Load all keys from i18n files"""
    all_keys = set()
    i18n_path = Path(i18n_dir)

    for json_file in i18n_path.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def extract_keys(d, prefix=''):
                """Recursively extract all keys from nested dict"""
                for key, value in d.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    all_keys.add(full_key)
                    if isinstance(value, dict):
                        extract_keys(value, full_key)
                    elif isinstance(value, str):
                        # Also store the value for comparison
                        all_keys.add(value)

            extract_keys(data)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    return all_keys

def main():
    # Extract Chinese strings from config_gui.py
    chinese_strings = extract_chinese_strings('config_gui.py')
    print(f"[OK] Found {len(chinese_strings)} unique Chinese strings in config_gui.py\n")

    # Load i18n keys
    i18n_keys = load_i18n_keys('i18n')
    print(f"[OK] Loaded {len(i18n_keys)} keys from i18n files\n")

    # Find untranslated strings
    untranslated = []
    for s in chinese_strings:
        # Check if this string exists in i18n files (as a value)
        if s not in i18n_keys:
            untranslated.append(s)

    # Sort by length for better readability
    untranslated.sort(key=lambda x: len(x))

    print("=" * 80)
    print(f"UNTRANSLATED CHINESE STRINGS: {len(untranslated)}")
    print("=" * 80)

    if untranslated:
        for i, s in enumerate(untranslated, 1):
            print(f"{i:3d}. {s}")
    else:
        print("[OK] All Chinese strings appear to be translated!")

    # Save to file for further analysis
    with open('untranslated_config_strings.txt', 'w', encoding='utf-8') as f:
        f.write(f"Total untranslated: {len(untranslated)}\n")
        f.write("=" * 80 + "\n\n")
        for i, s in enumerate(untranslated, 1):
            f.write(f"{i}. {s}\n")

    print(f"\n[OK] Results saved to untranslated_config_strings.txt")

if __name__ == '__main__':
    main()
