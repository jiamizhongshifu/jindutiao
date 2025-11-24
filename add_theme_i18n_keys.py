#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add theme manager i18n keys to translation files
"""

import json

def add_theme_keys():
    """Add theme translation keys"""

    # Theme keys - Chinese
    theme_keys_zh = {
        "themes": {
            "business": {
                "name": "商务专业",
                "description": "深色背景，蓝色系工作，适合商务场景"
            },
            "fresh": {
                "name": "清新自然",
                "description": "浅色背景，自然色系，清新舒适"
            },
            "warm": {
                "name": "温暖橙色",
                "description": "暖色调，温馨舒适，适合日常使用"
            },
            "minimal": {
                "name": "极简黑白",
                "description": "极简风格，黑白灰配色，专注高效"
            },
            "tech": {
                "name": "科技蓝",
                "description": "深色背景，蓝色系，科技感十足"
            },
            "ocean": {
                "name": "海洋蓝",
                "description": "浅蓝色调，清新宁静，适合专注工作"
            },
            "forest": {
                "name": "森林绿",
                "description": "绿色系，自然清新，适合学习和工作"
            },
            "sunset": {
                "name": "日落橙",
                "description": "橙色系，温暖活力，适合创意工作"
            },
            "lavender": {
                "name": "薰衣草紫",
                "description": "紫色系，优雅舒适，适合思考和学习"
            },
            "dark": {
                "name": "深色模式",
                "description": "深色背景，Material Design深色主题，护眼舒适"
            },
            "light": {
                "name": "浅色模式",
                "description": "浅色背景，Material Design浅色主题，明亮清晰"
            }
        }
    }

    # Theme keys - English
    theme_keys_en = {
        "themes": {
            "business": {
                "name": "Business Professional",
                "description": "Dark background, blue work tones, suitable for business scenarios"
            },
            "fresh": {
                "name": "Fresh Natural",
                "description": "Light background, natural colors, fresh and comfortable"
            },
            "warm": {
                "name": "Warm Orange",
                "description": "Warm tones, cozy and comfortable, suitable for daily use"
            },
            "minimal": {
                "name": "Minimal B&W",
                "description": "Minimalist style, black-white-gray palette, focused and efficient"
            },
            "tech": {
                "name": "Tech Blue",
                "description": "Dark background, blue tones, full of technology feel"
            },
            "ocean": {
                "name": "Ocean Blue",
                "description": "Light blue tones, fresh and calm, suitable for focused work"
            },
            "forest": {
                "name": "Forest Green",
                "description": "Green tones, natural and fresh, suitable for study and work"
            },
            "sunset": {
                "name": "Sunset Orange",
                "description": "Orange tones, warm and energetic, suitable for creative work"
            },
            "lavender": {
                "name": "Lavender Purple",
                "description": "Purple tones, elegant and comfortable, suitable for thinking and learning"
            },
            "dark": {
                "name": "Dark Mode",
                "description": "Dark background, Material Design dark theme, eye-friendly"
            },
            "light": {
                "name": "Light Mode",
                "description": "Light background, Material Design light theme, bright and clear"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add theme keys
    zh_cn['themes'] = theme_keys_zh['themes']
    en_us['themes'] = theme_keys_en['themes']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Theme translation keys added!")
    print(f"Added {len(theme_keys_zh['themes'])} themes")
    print(f"Total keys per theme: 2 (name + description)")
    print(f"Total new keys: {len(theme_keys_zh['themes']) * 2}")

if __name__ == '__main__':
    add_theme_keys()
