#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add AI quota i18n keys to translation files
"""

import json

def add_ai_quota_keys():
    """Add AI quota translation keys"""

    # AI quota keys - Chinese
    ai_quota_keys_zh = {
        "ai_quota": {
            "daily_remaining": "✓ 今日剩余: {remaining} 次规划",
            "quota_exhausted": "⚠️ 今日配额已用完",
            "service_unavailable": "⚠️ 无法连接云服务（请点击刷新重试）"
        }
    }

    # AI quota keys - English
    ai_quota_keys_en = {
        "ai_quota": {
            "daily_remaining": "✓ Remaining today: {remaining} plans",
            "quota_exhausted": "⚠️ Daily quota exhausted",
            "service_unavailable": "⚠️ Cannot connect to cloud service (click refresh to retry)"
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add AI quota keys
    zh_cn['ai_quota'] = ai_quota_keys_zh['ai_quota']
    en_us['ai_quota'] = ai_quota_keys_en['ai_quota']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("AI quota translation keys added!")
    print(f"Added {len(ai_quota_keys_zh['ai_quota'])} keys")

if __name__ == '__main__':
    add_ai_quota_keys()
