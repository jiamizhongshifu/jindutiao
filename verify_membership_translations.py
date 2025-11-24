#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify all membership translation keys are used in membership_ui.py
"""

import re
import json

def verify_all_keys_used():
    """Verify all translation keys defined are actually used in the code"""

    print("=== Verifying Translation Key Usage ===\n")

    # Load translation file
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    membership_keys = zh_cn.get('membership', {})

    # Read membership_ui.py
    with open('gaiya/ui/membership_ui.py', 'r', encoding='utf-8') as f:
        code_content = f.read()

    # Collect all translation keys (flatten the nested structure)
    def collect_keys(data, prefix=''):
        keys = []
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.extend(collect_keys(v, full_key))
            else:
                keys.append(full_key)
        return keys

    all_keys = collect_keys(membership_keys, 'membership')

    print(f"Total translation keys defined: {len(all_keys)}\n")

    # Check each key
    unused_keys = []
    used_keys = []

    for key in all_keys:
        # Search for tr("key") or tr('key')
        pattern = rf'tr\(["\']({re.escape(key)})["\']'
        if re.search(pattern, code_content):
            used_keys.append(key)
            print(f"[OK] {key}")
        else:
            unused_keys.append(key)
            print(f"[WARN] {key} - NOT FOUND IN CODE")

    print(f"\n=== Summary ===")
    print(f"Used keys: {len(used_keys)}/{len(all_keys)}")
    print(f"Unused keys: {len(unused_keys)}/{len(all_keys)}")

    if unused_keys:
        print(f"\nUnused keys:")
        for key in unused_keys:
            print(f"  - {key}")
        return False

    print("\n[OK] All translation keys are used in the code!")
    return True

def verify_no_chinese_strings():
    """Verify no Chinese strings remain in the code (except comments and logs)"""

    print("\n=== Checking for Remaining Chinese Strings ===\n")

    with open('gaiya/ui/membership_ui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    found_chinese = []

    for line_num, line in enumerate(lines, 1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Skip debug/diagnostic logs
        if '[DIAG' in line or 'file=sys.stderr' in line:
            continue

        # Skip test code (main block)
        if line_num >= 1255:  # Test code starts around line 1255
            continue

        # Check for Chinese characters in string literals
        string_matches = re.findall(r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']', line)
        if string_matches:
            for match in string_matches:
                found_chinese.append((line_num, match, line.strip()))

    if found_chinese:
        print(f"[WARN] Found {len(found_chinese)} Chinese string(s) that may need translation:\n")
        for line_num, text, code in found_chinese:
            print(f"  Line {line_num}: {text}")
            print(f"    Code: {code}\n")
        return False
    else:
        print("[OK] No untranslated Chinese strings found (except logs and test code)")
        return True

def check_tr_function_import():
    """Check if tr function is properly imported"""

    print("\n=== Checking tr() Import ===\n")

    with open('gaiya/ui/membership_ui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from i18n.translator import tr' in content:
        print("[OK] tr() function is properly imported")
        return True
    else:
        print("[FAIL] tr() function import not found")
        return False

if __name__ == '__main__':
    import sys

    success = True

    success = check_tr_function_import() and success
    success = verify_all_keys_used() and success
    success = verify_no_chinese_strings() and success

    print("\n" + "="*60)
    if success:
        print("VERIFICATION COMPLETE - ALL CHECKS PASSED!")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED - PLEASE REVIEW WARNINGS")
        sys.exit(1)
