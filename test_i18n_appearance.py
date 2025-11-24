#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试i18n外观Tab翻译是否正常加载
"""
import sys
from pathlib import Path

# 测试i18n加载
print("=== i18n Appearance Translation Test ===\n")

try:
    from i18n import tr, set_language, get_language, get_available_languages

    print(f"✓ i18n module imported successfully")
    print(f"Current language: {get_language()}")
    print(f"Available languages: {get_available_languages()}")

    # 测试切换到英文
    print("\n--- Testing English translations ---")
    set_language("en_US")
    print(f"Language set to: {get_language()}")

    # 测试外观Tab的关键翻译
    test_keys = [
        "appearance.basic_settings",
        "appearance.background_color",
        "appearance.autostart",
        "appearance.visual_effects",
        "appearance.color_settings",
    ]

    print("\nTranslation results:")
    for key in test_keys:
        value = tr(key)
        status = "✓" if value != key else "✗"
        print(f"  {status} {key}: {value}")

    # 测试中文翻译
    print("\n--- Testing Chinese translations ---")
    set_language("zh_CN")
    print(f"Language set to: {get_language()}")

    print("\nTranslation results:")
    for key in test_keys:
        value = tr(key)
        status = "✓" if value != key else "✗"
        print(f"  {status} {key}: {value}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 测试打包后的路径
print("\n--- Path Information ---")
print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
if getattr(sys, 'frozen', False):
    print(f"sys._MEIPASS: {sys._MEIPASS}")
    i18n_path = Path(sys._MEIPASS) / 'i18n'
else:
    i18n_path = Path(__file__).parent / 'i18n'
print(f"i18n directory: {i18n_path}")
print(f"i18n exists: {i18n_path.exists()}")
if i18n_path.exists():
    json_files = list(i18n_path.glob("*.json"))
    print(f"JSON files found: {[f.name for f in json_files]}")
