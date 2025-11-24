#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add authentication/login i18n keys to translation files
"""

import json

def add_auth_keys():
    """Add authentication translation keys"""

    # Auth keys - Chinese
    auth_keys_zh = {
        "auth": {
            # Login/Logout
            "login_success": "登录成功",
            "logout_success": "退出成功",
            "account_updated": "您的账户信息已更新。",
            "user": "用户",

            # Dialog titles
            "confirm_logout": "确认退出",
            "login_required": "需要登录",

            # Messages
            "confirm_logout_msg": "确定要退出当前账号吗？\n\n退出后将以游客身份继续使用，免费用户功能将受到限制。",
            "login_required_msg": "💡 {feature}需要登录后才能使用。\n\n登录后您将享有：\n{benefits}",
            "feature_name": "此功能"
        },
        "scene": {
            # Scene editor related
            "ui": {
                "open_editor": "打开场景编辑器",
                "refresh_scenes": "刷新场景选择下拉框"
            }
        }
    }

    # Auth keys - English
    auth_keys_en = {
        "auth": {
            # Login/Logout
            "login_success": "Login Successful",
            "logout_success": "Logout Successful",
            "account_updated": "Your account information has been updated.",
            "user": "User",

            # Dialog titles
            "confirm_logout": "Confirm Logout",
            "login_required": "Login Required",

            # Messages
            "confirm_logout_msg": "Are you sure you want to logout?\n\nAfter logout, you will continue as a guest with limited features.",
            "login_required_msg": "💡 {feature} requires login to use.\n\nAfter login, you will have access to:\n{benefits}",
            "feature_name": "This feature"
        },
        "scene": {
            # Scene editor related
            "ui": {
                "open_editor": "Open Scene Editor",
                "refresh_scenes": "Refresh Scene Selection"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add auth keys
    zh_cn['auth'] = auth_keys_zh['auth']
    zh_cn['scene'] = auth_keys_zh['scene']

    en_us['auth'] = auth_keys_en['auth']
    en_us['scene'] = auth_keys_en['scene']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Authentication translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_auth = count_keys(auth_keys_zh['auth'])
    total_scene = count_keys(auth_keys_zh['scene'])
    total = total_auth + total_scene

    print(f"  - Auth: {total_auth} keys")
    print(f"  - Scene: {total_scene} keys")
    print(f"Total new keys: {total}")

if __name__ == '__main__':
    add_auth_keys()
