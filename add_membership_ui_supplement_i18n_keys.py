#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add membership UI supplement i18n keys to translation files
Handles price units, labels, marketing copy, and partner introduction dialog
"""

import json

def add_membership_ui_supplement_keys():
    """Add membership UI supplement translation keys"""

    # Membership UI supplement keys - Chinese
    membership_ui_supplement_zh = {
        "membership": {
            # Price units
            "price_units": {
                "per_month": "/月",
                "per_year": "/年"
            },
            # Labels and badges
            "labels": {
                "limited_quota": "限量1000名",
                "onetime_payment": "一次付费",
                "lifetime_access": "终身可用",
                "member_tips_title": "💡 会员提示",
                "comparison_title": "💎 会员方案详细对比"
            },
            # Buttons
            "buttons": {
                "become_partner": "我愿意成为会员合伙人"
            }
        }
    }

    # Membership UI supplement keys - English
    membership_ui_supplement_en = {
        "membership": {
            # Price units
            "price_units": {
                "per_month": "/mo",
                "per_year": "/yr"
            },
            # Labels and badges
            "labels": {
                "limited_quota": "Limited to 1000",
                "onetime_payment": "One-time Payment",
                "lifetime_access": "Lifetime Access",
                "member_tips_title": "💡 Member Tips",
                "comparison_title": "💎 Membership Comparison"
            },
            # Buttons
            "buttons": {
                "become_partner": "I Want to Become a Partner"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Merge with existing membership keys
    if 'membership' not in zh_cn:
        zh_cn['membership'] = {}
    if 'membership' not in en_us:
        en_us['membership'] = {}

    zh_cn['membership'].update(membership_ui_supplement_zh['membership'])
    en_us['membership'].update(membership_ui_supplement_en['membership'])

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Membership UI supplement translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total = count_keys(membership_ui_supplement_zh['membership'])
    print(f"Total new keys: {total}")
    print("  - Price units: 2 keys")
    print("  - Labels: 5 keys")
    print("  - Buttons: 1 key")

if __name__ == '__main__':
    add_membership_ui_supplement_keys()
