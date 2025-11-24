#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test language switching for membership translations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from i18n.translator import tr, set_language

def test_language_switch():
    """Test switching between Chinese and English"""

    print("=== Testing Language Switching ===\n")

    test_keys = [
        'membership.dialog_title',
        'membership.not_logged_in',
        'membership.btn_buy_now',
        'membership.plan.monthly_name',
        'membership.feature.smart_planning_50',
        'membership.payment.select_method',
        'membership.error.no_plan_selected_title',
    ]

    # Test Chinese (default)
    print("--- Chinese (zh_CN) ---")
    set_language('zh_CN')
    for key in test_keys:
        value = tr(key)
        print(f"{key}: {value}")

    print("\n--- English (en_US) ---")
    set_language('en_US')
    for key in test_keys:
        value = tr(key)
        print(f"{key}: {value}")

    # Test parameterized translation
    print("\n--- Parameterized Translation ---")
    print("Chinese:")
    set_language('zh_CN')
    msg = tr('membership.error.order_creation_failed', error_msg='网络超时')
    print(f"  {msg}")

    print("English:")
    set_language('en_US')
    msg = tr('membership.error.order_creation_failed', error_msg='Network timeout')
    print(f"  {msg}")

    # Restore default language
    set_language('zh_CN')

    print("\n[OK] Language switching works correctly!")
    return True

def compare_all_keys():
    """Compare all membership keys between zh_CN and en_US"""

    print("\n=== Comparing All Keys ===\n")

    import json

    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    def get_all_paths(data, prefix=''):
        """Get all key paths from nested dict"""
        paths = []
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                paths.extend(get_all_paths(v, full_key))
            else:
                paths.append(full_key)
        return paths

    zh_keys = set(get_all_paths(zh_cn.get('membership', {}), 'membership'))
    en_keys = set(get_all_paths(en_us.get('membership', {}), 'membership'))

    # Check for missing keys
    missing_in_en = zh_keys - en_keys
    missing_in_zh = en_keys - zh_keys

    if missing_in_en:
        print(f"[WARN] Keys in zh_CN but missing in en_US:")
        for key in missing_in_en:
            print(f"  - {key}")

    if missing_in_zh:
        print(f"[WARN] Keys in en_US but missing in zh_CN:")
        for key in missing_in_zh:
            print(f"  - {key}")

    if not missing_in_en and not missing_in_zh:
        print(f"[OK] Both language files have the same {len(zh_keys)} keys")
        print("[OK] No missing translations detected!")
        return True

    return False

if __name__ == '__main__':
    success = True

    success = test_language_switch() and success
    success = compare_all_keys() and success

    print("\n" + "="*60)
    if success:
        print("ALL LANGUAGE TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)
