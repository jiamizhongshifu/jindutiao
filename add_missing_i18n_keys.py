#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加缺失的i18n翻译key
"""

import json

def add_missing_keys():
    # 读取现有翻译
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh = json.load(f)
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en = json.load(f)

    # 添加缺失的key
    missing_translations = {
        'account.tab_title': {
            'zh': '👤 个人中心',
            'en': '👤 Account Center'
        },
        'account.membership.pro': {
            'zh': 'Pro会员',
            'en': 'Pro Member'
        },
        'account.feature.statistics_reports': {
            'zh': '统计报告分析',
            'en': 'Statistics Report Analysis'
        },
        'account.feature.pomodoro_timer': {
            'zh': '番茄时钟',
            'en': 'Pomodoro Timer'
        },
        'account.feature.vip_group': {
            'zh': '加入VIP会员群',
            'en': 'Join VIP Member Group'
        },
        'account.feature.referral_cashback': {
            'zh': '33%引荐返现比例',
            'en': '33% Referral Cashback'
        },
        'account.feature.priority_updates': {
            'zh': '优先体验所有新功能',
            'en': 'Priority Access to All New Features'
        },
        'account.feature.one_on_one_consulting': {
            'zh': '专属1v1咨询服务',
            'en': 'Exclusive 1-on-1 Consulting Service'
        },
    }

    # 添加到翻译文件
    for key, translations in missing_translations.items():
        parts = key.split('.')

        # 添加到zh_CN
        current = zh
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = translations['zh']

        # 添加到en_US
        current = en
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = translations['en']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh, f, ensure_ascii=False, indent=2)
    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en, f, ensure_ascii=False, indent=2)

    print(f"Added {len(missing_translations)} missing translation keys")
    for key in missing_translations:
        print(f"  + {key}")

if __name__ == '__main__':
    add_missing_keys()
