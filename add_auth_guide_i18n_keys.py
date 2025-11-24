#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add authentication guide and remaining UI translation keys
"""

import json

def add_auth_guide_keys():
    """Add translation keys for auth guide and other remaining UI strings"""

    # Translation keys - Chinese
    auth_guide_zh = {
        "auth": {
            "features": {
                "this_feature": "此功能",
                "template_auto_apply": "模板自动应用",
                "ai_smart_planning": "AI智能规划"
            },
            "guide": {
                "benefits_intro": "登录后您将享有：",
                "free_user_quota": "• 免费用户：3次/天 AI智能规划",
                "pro_member_quota": "• Pro会员：20次/天 AI智能规划",
                "more_features": "• 更多高级功能和服务",
                "go_to_login": "是否前往个人中心登录？"
            }
        },
        "autostart": {
            "messages": {
                "setup_failed": "开机自启动设置失败\n\n可能需要管理员权限或系统限制"
            }
        },
        "about": {
            "dialog_title": "GaiYa每日进度条",
            "letter_title": "致 GaiYa 会员合伙人的一封信",
            "letter_subtitle": "邀请您共同成长，共享价值"
        }
    }

    # Translation keys - English
    auth_guide_en = {
        "auth": {
            "features": {
                "this_feature": "This Feature",
                "template_auto_apply": "Template Auto-Apply",
                "ai_smart_planning": "AI Smart Planning"
            },
            "guide": {
                "benefits_intro": "Benefits after login:",
                "free_user_quota": "• Free users: 3 AI plans/day",
                "pro_member_quota": "• Pro members: 20 AI plans/day",
                "more_features": "• More advanced features and services",
                "go_to_login": "Go to personal center to login?"
            }
        },
        "autostart": {
            "messages": {
                "setup_failed": "Failed to set auto-start\n\nMay require administrator privileges or system restrictions"
            }
        },
        "about": {
            "dialog_title": "GaiYa Daily Progress Bar",
            "letter_title": "A Letter to GaiYa Lifetime Partners",
            "letter_subtitle": "Inviting you to grow together and share value"
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Merge auth keys
    if 'auth' not in zh_cn:
        zh_cn['auth'] = {}
    if 'features' not in zh_cn['auth']:
        zh_cn['auth']['features'] = {}
    if 'guide' not in zh_cn['auth']:
        zh_cn['auth']['guide'] = {}

    zh_cn['auth']['features'].update(auth_guide_zh['auth']['features'])
    zh_cn['auth']['guide'] = auth_guide_zh['auth']['guide']

    if 'auth' not in en_us:
        en_us['auth'] = {}
    if 'features' not in en_us['auth']:
        en_us['auth']['features'] = {}
    if 'guide' not in en_us['auth']:
        en_us['auth']['guide'] = {}

    en_us['auth']['features'].update(auth_guide_en['auth']['features'])
    en_us['auth']['guide'] = auth_guide_en['auth']['guide']

    # Merge autostart keys
    if 'autostart' not in zh_cn:
        zh_cn['autostart'] = {}
    if 'messages' not in zh_cn['autostart']:
        zh_cn['autostart']['messages'] = {}

    zh_cn['autostart']['messages'] = auth_guide_zh['autostart']['messages']

    if 'autostart' not in en_us:
        en_us['autostart'] = {}
    if 'messages' not in en_us['autostart']:
        en_us['autostart']['messages'] = {}

    en_us['autostart']['messages'] = auth_guide_en['autostart']['messages']

    # Merge about keys
    zh_cn['about'] = auth_guide_zh['about']
    en_us['about'] = auth_guide_en['about']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Auth guide and remaining UI translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_auth_features = count_keys(auth_guide_zh['auth']['features'])
    total_auth_guide = count_keys(auth_guide_zh['auth']['guide'])
    total_autostart = count_keys(auth_guide_zh['autostart'])
    total_about = count_keys(auth_guide_zh['about'])
    total = total_auth_features + total_auth_guide + total_autostart + total_about

    print(f"Total new keys: {total}")
    print(f"  - Auth features: {total_auth_features} keys")
    print(f"  - Auth guide: {total_auth_guide} keys")
    print(f"  - Autostart: {total_autostart} keys")
    print(f"  - About: {total_about} keys")

if __name__ == '__main__':
    add_auth_guide_keys()
