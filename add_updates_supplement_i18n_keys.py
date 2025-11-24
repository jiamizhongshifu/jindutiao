#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add updates system supplement i18n keys to translation files
"""

import json

def add_updates_supplement_keys():
    """Add updates system supplement translation keys"""

    # Updates supplement keys - Chinese
    updates_supplement_zh = {
        "updates": {
            "buttons": {
                "update_now": "立即更新",
                "go_to_download": "前往下载",
                "check_update": "检查更新"
            },
            "messages": {
                "latest_version": "已是最新版本",
                "latest_version_msg": "当前版本 v{version} 已是最新版本！",
                "checking": "检查中...",
                "new_version_found": "发现新版本",
                "no_releases": "暂无发布版本",
                "update_check_failed": "检查更新失败",
                "cannot_auto_update": "无法自动更新",
                "preparing_update": "准备更新",
                "install_failed": "安装失败",
                "update_cancelled": "更新已取消"
            }
        },
        "membership": {
            "tiers": {
                "pro_monthly": "Pro 月度",
                "pro_yearly": "Pro 年度",
                "lifetime_partner": "会员合伙人"
            }
        },
        "wechat": {
            "add_founder": "添加创始人微信",
            "qrcode_load_failed": "无法加载二维码图片"
        }
    }

    # Updates supplement keys - English
    updates_supplement_en = {
        "updates": {
            "buttons": {
                "update_now": "Update Now",
                "go_to_download": "Go to Download",
                "check_update": "Check Update"
            },
            "messages": {
                "latest_version": "Latest Version",
                "latest_version_msg": "Current version v{version} is up to date!",
                "checking": "Checking...",
                "new_version_found": "New Version Found",
                "no_releases": "No releases available",
                "update_check_failed": "Update check failed",
                "cannot_auto_update": "Cannot auto-update",
                "preparing_update": "Preparing update",
                "install_failed": "Install failed",
                "update_cancelled": "Update cancelled"
            }
        },
        "membership": {
            "tiers": {
                "pro_monthly": "Pro Monthly",
                "pro_yearly": "Pro Yearly",
                "lifetime_partner": "Lifetime Partner"
            }
        },
        "wechat": {
            "add_founder": "Add Founder on WeChat",
            "qrcode_load_failed": "Cannot load QR code image"
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Merge with existing keys
    if 'updates' not in zh_cn:
        zh_cn['updates'] = {}
    if 'membership' not in zh_cn:
        zh_cn['membership'] = {}
    if 'wechat' not in zh_cn:
        zh_cn['wechat'] = {}

    zh_cn['updates'].update(updates_supplement_zh['updates'])
    zh_cn['membership'].update(updates_supplement_zh['membership'])
    zh_cn['wechat'] = updates_supplement_zh['wechat']

    if 'updates' not in en_us:
        en_us['updates'] = {}
    if 'membership' not in en_us:
        en_us['membership'] = {}
    if 'wechat' not in en_us:
        en_us['wechat'] = {}

    en_us['updates'].update(updates_supplement_en['updates'])
    en_us['membership'].update(updates_supplement_en['membership'])
    en_us['wechat'] = updates_supplement_en['wechat']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Updates supplement translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_updates = count_keys(updates_supplement_zh['updates'])
    total_membership = count_keys(updates_supplement_zh['membership'])
    total_wechat = count_keys(updates_supplement_zh['wechat'])
    total = total_updates + total_membership + total_wechat

    print(f"Total new keys: {total}")
    print(f"  - Updates: {total_updates} keys")
    print(f"  - Membership tiers: {total_membership} keys")
    print(f"  - WeChat: {total_wechat} keys")

if __name__ == '__main__':
    add_updates_supplement_keys()
