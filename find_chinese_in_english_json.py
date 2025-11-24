#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find Chinese characters in English translation file"""
import json
import re

def contains_chinese(text):
    """Check if text contains Chinese characters"""
    if not isinstance(text, str):
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def find_chinese_in_dict(data, prefix=''):
    """Recursively find all keys with Chinese values"""
    results = []

    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            results.extend(find_chinese_in_dict(value, full_key))
        elif contains_chinese(str(value)):
            results.append({
                'key': full_key,
                'value': value
            })

    return results

# Load English translation file
with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
    en_data = json.load(f)

# Find all keys with Chinese
chinese_keys = find_chinese_in_dict(en_data)

print(f"Found {len(chinese_keys)} keys with Chinese characters in en_US.json:\n")

for item in chinese_keys:
    print(f"Key: {item['key']}")
    print(f"Value: {item['value']}")
    print()

# Save to file for review
with open('chinese_in_english_translations.txt', 'w', encoding='utf-8') as f:
    f.write(f"Found {len(chinese_keys)} keys with Chinese characters:\n\n")
    for item in chinese_keys:
        f.write(f"Key: {item['key']}\n")
        f.write(f"Value: {item['value']}\n")
        f.write("\n")

print(f"Results saved to: chinese_in_english_translations.txt")
