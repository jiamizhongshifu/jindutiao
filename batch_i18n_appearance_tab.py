#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理外观Tab的国际化
安全地替换所有硬编码中文字符串为tr()调用
"""
import json
import re
from pathlib import Path

def add_i18n_keys():
    """添加外观Tab相关的i18n键到翻译文件"""

    # 外观Tab的所有字符串(按出现顺序)
    appearance_keys = {
        # 基本设置区域
        "appearance.basic_settings": "🔧 基本设置",
        "appearance.bar_height": "进度条高度",
        "appearance.position": "进度条位置",
        "appearance.position_top": "顶部",
        "appearance.position_bottom": "底部",
        "appearance.custom": "自定义",
        "appearance.pixels": "像素",
        "appearance.screen": "显示器",
        "appearance.autostart": "开机自动启动",
        "appearance.update_interval": "从本地刷新时间间隔",
        "appearance.milliseconds": "毫秒",

        # 语言设置
        "appearance.language": "语言",
        "appearance.language_zh_cn": "简体中文",
        "appearance.language_en_us": "English",

        # 颜色设置
        "appearance.color_settings": "🎨 颜色设置",
        "appearance.background_color": "背景颜色",
        "appearance.background_opacity": "背景透明度",
        "appearance.marker_color": "时间标记颜色",
        "appearance.marker_width": "标记宽度",

        # 标记设置
        "appearance.marker_type": "标记类型",
        "appearance.marker_type_line": "线条",
        "appearance.marker_type_image": "图片",
        "appearance.marker_type_gif": "动画",
        "appearance.marker_type_note": "(line=线条, image=图片, gif=动画)",
        "appearance.marker_image": "标记图片",
        "appearance.browse": "📁 浏览",
        "appearance.marker_size": "标记图片大小",
        "appearance.marker_x_offset": "标记X轴偏移",
        "appearance.marker_x_offset_note": "(正值向右,负值向左)",
        "appearance.marker_y_offset": "标记Y轴偏移",
        "appearance.marker_y_offset_note": "(正值向上,负值向下)",
        "appearance.marker_speed": "动画速度",
        "appearance.marker_speed_note": "(100%=原速, 200%=2倍速)",

        # 视觉效果
        "appearance.visual_effects": "✨ 视觉效果",
        "appearance.corner_radius": "圆角半径",
        "appearance.enable_shadow": "启用阴影效果",
    }

    # 对应的英文翻译
    appearance_keys_en = {
        "appearance.basic_settings": "🔧 Basic Settings",
        "appearance.bar_height": "Progress Bar Height",
        "appearance.position": "Progress Bar Position",
        "appearance.position_top": "Top",
        "appearance.position_bottom": "Bottom",
        "appearance.custom": "Custom",
        "appearance.pixels": "pixels",
        "appearance.screen": "Screen",
        "appearance.autostart": "Launch at Startup",
        "appearance.update_interval": "Local Refresh Interval",
        "appearance.milliseconds": "milliseconds",

        "appearance.language": "Language",
        "appearance.language_zh_cn": "简体中文",
        "appearance.language_en_us": "English",

        "appearance.color_settings": "🎨 Color Settings",
        "appearance.background_color": "Background Color",
        "appearance.background_opacity": "Background Opacity",
        "appearance.marker_color": "Time Marker Color",
        "appearance.marker_width": "Marker Width",

        "appearance.marker_type": "Marker Type",
        "appearance.marker_type_line": "Line",
        "appearance.marker_type_image": "Image",
        "appearance.marker_type_gif": "Animation",
        "appearance.marker_type_note": "(line, image, or animation)",
        "appearance.marker_image": "Marker Image",
        "appearance.browse": "📁 Browse",
        "appearance.marker_size": "Marker Image Size",
        "appearance.marker_x_offset": "Marker X Offset",
        "appearance.marker_x_offset_note": "(positive=right, negative=left)",
        "appearance.marker_y_offset": "Marker Y Offset",
        "appearance.marker_y_offset_note": "(positive=up, negative=down)",
        "appearance.marker_speed": "Animation Speed",
        "appearance.marker_speed_note": "(100%=normal, 200%=2x speed)",

        "appearance.visual_effects": "✨ Visual Effects",
        "appearance.corner_radius": "Corner Radius",
        "appearance.enable_shadow": "Enable Shadow Effect",
    }

    # 读取现有翻译文件
    zh_file = Path('i18n/zh_CN.json')
    en_file = Path('i18n/en_US.json')

    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    # 添加新键(如果不存在)
    zh_data.update(appearance_keys)
    en_data.update(appearance_keys_en)

    # 保存回文件
    with open(zh_file, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)
    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Added {len(appearance_keys)} appearance keys to translation files")
    return appearance_keys

def apply_replacements():
    """安全地应用i18n替换到config_gui.py"""

    # 定义替换规则(原文 -> i18n键)
    replacements = [
        # 区域标题
        ('"🔧 基本设置"', 'tr("appearance.basic_settings")'),
        ('"🎨 颜色设置"', 'tr("appearance.color_settings")'),
        ('"✨ 视觉效果"', 'tr("appearance.visual_effects")'),

        # 标签文本(注意要避免替换已经在tr()中的)
        ('"进度条高度:"', 'tr("appearance.bar_height") + ":"'),
        ('"进度条位置:"', 'tr("appearance.position") + ":"'),
        ('"显示器:"', 'tr("appearance.screen") + ":"'),
        ('"从本地刷新时间间隔:"', 'tr("appearance.update_interval") + ":"'),
        ('"语言:"', 'tr("appearance.language") + ":"'),
        ('"背景颜色:"', 'tr("appearance.background_color") + ":"'),
        ('"背景透明度:"', 'tr("appearance.background_opacity") + ":"'),
        ('"时间标记颜色:"', 'tr("appearance.marker_color") + ":"'),
        ('"标记宽度:"', 'tr("appearance.marker_width") + ":"'),
        ('"标记类型:"', 'tr("appearance.marker_type") + ":"'),
        ('"标记图片:"', 'tr("appearance.marker_image") + ":"'),
        ('"标记图片大小:"', 'tr("appearance.marker_size") + ":"'),
        ('"标记X轴偏移:"', 'tr("appearance.marker_x_offset") + ":"'),
        ('"标记Y轴偏移:"', 'tr("appearance.marker_y_offset") + ":"'),
        ('"动画速度:"', 'tr("appearance.marker_speed") + ":"'),
        ('"圆角半径:"', 'tr("appearance.corner_radius") + ":"'),

        # 下拉选项
        ('"顶部"', 'tr("appearance.position_top")'),
        ('"底部"', 'tr("appearance.position_bottom")'),

        # 复选框
        ('"开机自动启动"', 'tr("appearance.autostart")'),
        ('"启用阴影效果"', 'tr("appearance.enable_shadow")'),

        # 按钮
        ('"📁 浏览"', 'tr("appearance.browse")'),

        # 后缀文本
        ('" 像素"', '" " + tr("appearance.pixels")'),
        ('" 毫秒"', '" " + tr("appearance.milliseconds")'),

        # 注释文本
        ('"(line=线条, image=图片, gif=动画)"', 'tr("appearance.marker_type_note")'),
        ('"(正值向右,负值向左)"', 'tr("appearance.marker_x_offset_note")'),
        ('"(正值向上,负值向下)"', 'tr("appearance.marker_y_offset_note")'),
        ('"(100%=原速, 200%=2倍速)"', 'tr("appearance.marker_speed_note")'),
    ]

    # 读取config_gui.py
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 应用替换
    changes_made = 0
    for old, new in replacements:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            changes_made += count
            print(f"  ✓ Replaced '{old}' → '{new}' ({count}x)")

    # 写回文件
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ Total replacements made: {changes_made}")
    return changes_made

if __name__ == '__main__':
    print("=== Batch i18n for Appearance Tab ===\n")

    # 步骤1: 添加翻译键
    print("Step 1: Adding translation keys...")
    add_i18n_keys()

    # 步骤2: 应用替换
    print("\nStep 2: Applying replacements...")
    apply_replacements()

    print("\n✨ Done! Please test the application.")
