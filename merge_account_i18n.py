#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将account center的i18n翻译合并到主翻译文件中
"""

import json
from pathlib import Path
from collections import OrderedDict

def load_json(file_path):
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """保存JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def convert_flat_to_nested(flat_dict):
    """将扁平的key转换为嵌套结构"""
    nested = {}
    for key, value in flat_dict.items():
        parts = key.split('.')
        current = nested
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return nested

def merge_nested_dicts(base, updates):
    """递归合并嵌套字典"""
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            merge_nested_dicts(base[key], value)
        else:
            base[key] = value
    return base

def main():
    print("Merging account center i18n translations...")

    # 加载生成的翻译
    account_zh = load_json('account_center_i18n_zh.json')
    account_en = load_json('account_center_i18n_en.json')

    print(f"Loaded {len(account_zh)} Chinese translations")
    print(f"Loaded {len(account_en)} English translations")

    # 转换为嵌套结构
    account_zh_nested = convert_flat_to_nested(account_zh)
    account_en_nested = convert_flat_to_nested(account_en)

    # 加载现有的主翻译文件
    zh_main_path = Path('i18n/zh_CN.json')
    en_main_path = Path('i18n/en_US.json')

    if zh_main_path.exists():
        zh_main = load_json(zh_main_path)
        print(f"Loaded existing zh_CN.json with {count_keys(zh_main)} keys")
    else:
        zh_main = {}
        print("zh_CN.json not found, creating new file")

    if en_main_path.exists():
        en_main = load_json(en_main_path)
        print(f"Loaded existing en_US.json with {count_keys(en_main)} keys")
    else:
        en_main = {}
        print("en_US.json not found, creating new file")

    # 合并
    zh_main = merge_nested_dicts(zh_main, account_zh_nested)
    en_main = merge_nested_dicts(en_main, account_en_nested)

    print(f"\nAfter merge:")
    print(f"  zh_CN.json: {count_keys(zh_main)} keys")
    print(f"  en_US.json: {count_keys(en_main)} keys")

    # 保存
    save_json(zh_main, zh_main_path)
    save_json(en_main, en_main_path)

    print(f"\nSuccessfully merged to:")
    print(f"  {zh_main_path}")
    print(f"  {en_main_path}")

def count_keys(d, count=0):
    """递归计算字典中的key总数"""
    for value in d.values():
        if isinstance(value, dict):
            count = count_keys(value, count)
        else:
            count += 1
    return count

if __name__ == '__main__':
    main()
