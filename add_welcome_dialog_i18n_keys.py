#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 welcome_dialog.py 的翻译键到 i18n 文件
"""

import json

def add_welcome_dialog_keys():
    """添加welcome_dialog的翻译键"""

    # 定义所有翻译键（中文和英文）
    welcome_keys_zh = {
        "welcome_dialog": {
            "window": {
                "title": "欢迎使用 GaiYa"
            },
            "title": {
                "main": "让每一天都清晰可见 ⏱️",
                "subtitle": "GaiYa 时间进度条助手"
            },
            "features": {
                "task_progress": "🎯 一眼掌握全天任务进度",
                "smart_reminder": "⏰ 智能提醒永不错过重要时刻",
                "rich_themes": "🎨 丰富主题个性化你的界面",
                "ai_planning": "🤖 AI智能规划优化时间管理"
            },
            "info": {
                "message": "接下来将通过简单的2步配置，帮助你快速开始使用。"
            },
            "checkbox": {
                "confirm": "我已了解，开始配置"
            },
            "buttons": {
                "skip": "暂时跳过",
                "start": "开始配置"
            }
        }
    }

    welcome_keys_en = {
        "welcome_dialog": {
            "window": {
                "title": "Welcome to GaiYa"
            },
            "title": {
                "main": "Make Every Day Crystal Clear ⏱️",
                "subtitle": "GaiYa Time Progress Bar Assistant"
            },
            "features": {
                "task_progress": "🎯 Master your daily task progress at a glance",
                "smart_reminder": "⏰ Smart reminders never miss important moments",
                "rich_themes": "🎨 Rich themes personalize your interface",
                "ai_planning": "🤖 AI smart planning optimizes time management"
            },
            "info": {
                "message": "The following 2 simple steps will help you get started quickly."
            },
            "checkbox": {
                "confirm": "I understand, start configuration"
            },
            "buttons": {
                "skip": "Skip for Now",
                "start": "Start Configuration"
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加welcome_dialog命名空间
    zh_cn['welcome_dialog'] = welcome_keys_zh['welcome_dialog']
    en_us['welcome_dialog'] = welcome_keys_en['welcome_dialog']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计welcome_dialog命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    key_count = count_keys(welcome_keys_zh['welcome_dialog'])
    print(f"新增 welcome_dialog 命名空间翻译键: {key_count} 个")

if __name__ == '__main__':
    add_welcome_dialog_keys()
