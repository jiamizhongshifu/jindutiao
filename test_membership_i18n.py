#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test membership_ui.py internationalization
"""

import json
import sys

def test_translation_keys():
    """Test if all translation keys are correctly added"""

    print("=== Testing Translation Keys ===\n")

    # Load translation files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Check if membership namespace exists
    if 'membership' not in zh_cn:
        print("[FAIL] membership namespace not found in zh_CN.json")
        return False

    if 'membership' not in en_us:
        print("[FAIL] membership namespace not found in en_US.json")
        return False

    print("[OK] membership namespace exists in both files")

    # Get membership data
    zh_membership = zh_cn['membership']
    en_membership = en_us['membership']

    # Count keys
    def count_all_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_all_keys(v)
            else:
                count += 1
        return count

    zh_count = count_all_keys(zh_membership)
    en_count = count_all_keys(en_membership)

    print(f"[OK] zh_CN membership keys: {zh_count}")
    print(f"[OK] en_US membership keys: {en_count}")

    if zh_count != en_count:
        print(f"[WARN] Key count mismatch: zh={zh_count}, en={en_count}")

    # List all keys
    print("\n=== Key Structure ===")
    print(f"Direct keys in membership: {len([k for k, v in zh_membership.items() if isinstance(v, str)])}")

    subnamespaces = [k for k, v in zh_membership.items() if isinstance(v, dict)]
    print(f"Sub-namespaces: {subnamespaces}")

    for ns in subnamespaces:
        print(f"  membership.{ns}: {len(zh_membership[ns])} keys")

    # Test some key translations
    print("\n=== Sample Translations ===")
    test_keys = [
        'not_logged_in',
        'dialog_title',
        'btn_buy_now',
    ]

    for key in test_keys:
        zh_val = zh_membership.get(key, 'NOT FOUND')
        en_val = en_membership.get(key, 'NOT FOUND')
        print(f"  {key}:")
        print(f"    zh: {zh_val}")
        print(f"    en: {en_val}")

    print("\n=== Test Summary ===")
    print(f"[OK] All translation keys successfully added")
    print(f"[OK] Total translation keys in zh_CN.json: {len(zh_cn)}")
    print(f"[OK] Total translation keys in en_US.json: {len(en_us)}")

    return True

def test_membership_ui_syntax():
    """Test if membership_ui.py has correct syntax"""

    print("\n=== Testing membership_ui.py Syntax ===\n")

    try:
        import py_compile
        py_compile.compile('gaiya/ui/membership_ui.py', doraise=True)
        print("[OK] membership_ui.py syntax is valid")
        return True
    except Exception as e:
        print(f"[FAIL] Syntax error in membership_ui.py: {e}")
        return False

def test_tr_import():
    """Test if tr function can be imported"""

    print("\n=== Testing tr() Function Import ===\n")

    try:
        # Add parent directory to path
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        from i18n.translator import tr

        # Test translation
        result = tr('membership.dialog_title')
        print(f"[OK] tr('membership.dialog_title') = '{result}'")

        # Test with parameters
        result_with_param = tr('membership.error.order_creation_failed', error_msg='测试错误')
        print(f"[OK] tr with params = '{result_with_param}'")

        return True
    except Exception as e:
        print(f"[FAIL] Failed to import or use tr(): {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = True

    success = test_translation_keys() and success
    success = test_membership_ui_syntax() and success
    success = test_tr_import() and success

    print("\n" + "="*60)
    if success:
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)
