#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add missed translation keys to i18n JSON files
"""

import json
from pathlib import Path

def deep_merge(target, source):
    """Deep merge source dict into target dict"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value

def add_missed_keys():
    """Add missed translation keys"""

    # New keys in Chinese
    missed_zh = {
        "templates": {
            "messages": {
                "manager_not_initialized": "模板管理器未初始化"
            },
            "auto_apply": {
                "add_rule_failed": "添加规则失败:\n{error}",
                "edit_rule_failed": "编辑规则失败:\n{error}",
                "delete_failed": "删除失败:\n{error}",
                "operation_failed": "操作失败:\n{error}",
                "test_failed": "测试失败:\n{error}"
            }
        }
    }

    # New keys in English
    missed_en = {
        "templates": {
            "messages": {
                "manager_not_initialized": "Template manager not initialized"
            },
            "auto_apply": {
                "add_rule_failed": "Failed to add rule:\n{error}",
                "edit_rule_failed": "Failed to edit rule:\n{error}",
                "delete_failed": "Failed to delete:\n{error}",
                "operation_failed": "Operation failed:\n{error}",
                "test_failed": "Test failed:\n{error}"
            }
        }
    }

    # Load and merge zh_CN
    zh_file = Path('i18n/zh_CN.json')
    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    deep_merge(zh_data, missed_zh)

    with open(zh_file, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated {zh_file}")

    # Load and merge en_US
    en_file = Path('i18n/en_US.json')
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    deep_merge(en_data, missed_en)

    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated {en_file}")
    print("\nAdded missed translation keys:")
    print("  - Template manager error (1 key)")
    print("  - Template auto-apply errors (5 keys)")
    print("\nTotal: 6 new keys")

if __name__ == '__main__':
    add_missed_keys()
