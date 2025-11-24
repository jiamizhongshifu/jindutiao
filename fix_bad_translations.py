#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复en_US.json中的机器翻译错误
"""

import json
from pathlib import Path

# 需要修复的翻译映射 (i18n_key: 正确的英文翻译)
TRANSLATION_FIXES = {
    # === 错误的机器翻译 ===
    "config.config_1": "Failed to load configuration and tasks: {e}",
    "message.text_2521": "Failed to update UI controls: {e}",
    "general.text_7793": "ScheduleManager not initialized, retrying in 500ms",
    "message.text_7435": "Failed to toggle rule status: {e}",
    "message.text_6143": "Failed to delete rule: {e}",
    "message.text_4939": "Failed to test date match: {e}",
    "ai.text_4639": "Failed to initialize AI components: {e}",
    "message.text_2933": "Health check failed: {str(e)}",

    # === 完全未翻译的 ===
    "general.display": "Display Index:",
    "general.text_7375": "Update Interval:",
    "general.text_2184": "When checked, GaiYa daily progress bar will start automatically on Windows boot",
    "general.text_3030": "Auto-start:",
    "general.marker": "Marker Image:",
    "general.size": "Marker Image Size:",
    "general.marker_1": "Marker Image X Offset:",
    "general.marker_2": "Marker Image Y Offset:",
    "general.animation": "Animation Playback Speed:",

    # === 半中半英混杂 ===
    "config.color_3": "Text Color",
    "general.text_9791": "Enable Scene System",
    "general.display_1": "Overlay progress bar above scene in scene mode",
    "general.text_6942": "No Scene",
    "general.text_1681": "No Available Scenes",
    "general.text_7449": "Rescan scenes directory and load newly exported scenes",
    "dialog.display": "No scene selected, default progress bar style will be displayed",
    "general.text_7472": "No Description",
    "general.text_8358": "Unable to load scene info",
    "general.text_7526": "Scene manager not initialized",
    "general.text_3263": "Scene editor is already open",
    "general.text_1159": "Scene editor has been closed",
    "general.text_6289": "Scene list refreshed, total {len(scene_list)} scene(s)",

    # === 其他需要改进的 ===
    "message.text_7732": "Failed to add schedule rule: {e}",
    "message.text_8752": "Failed to edit schedule rule: {e}",
    "message.text_4623": "Invalid date",
    "message.text_9345": "No template matched for this date",
    "message.text_3265": "Test date matching failed: {e}",
    "message.text_1862": "Failed to load schedule rules: {e}",
    "message.text_2564": "Loaded {len(schedules)} schedule rules",

    # UI相关
    "ui.notification_task_start_before": "Notify Before Task Starts:",
    "ui.notification_task_end_before": "Notify Before Task Ends:",
    "ui.notification_dnd_time": "Do Not Disturb Period:",
    "ui.scene_show_progress": "Still show progress bar",
    "ui.scene_current": "Current Scene:",
    "ui.scene_author": "Author:",
    "ui.scene_description": "Description:",
    "ui.scene_edit": "Edit Scene",
    "ui.scene_refresh": "Refresh",

    # 通用文本
    "general.minute": "minute(s)",
    "general.minutes": "minutes",
    "general.test_date": "Test Date",
    "general.test_result": "Test Result",
    "general.template_not_exist": "Template does not exist",
    "general.unknown": "Unknown",
    "general.none": "None",
    "general.optional": "Optional",
    "general.required": "Required",
}

def fix_translations_in_file(file_path, fixes):
    """修复翻译文件中的错误翻译"""
    # 读取现有翻译
    with open(file_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    fixed_count = 0
    not_found = []

    # 递归查找并修复
    def find_and_fix(obj, key_path, target_key, new_value):
        nonlocal fixed_count
        parts = target_key.split('.')
        current = obj

        try:
            # 导航到目标位置
            for part in parts[:-1]:
                if part in current:
                    current = current[part]
                else:
                    return False

            # 修复最后一个key
            final_key = parts[-1]
            if final_key in current:
                old_value = current[final_key]
                current[final_key] = new_value
                fixed_count += 1
                print(f"  Fixed: {target_key}")
                print(f"    Old: {old_value}")
                print(f"    New: {new_value}")
                return True
            else:
                return False
        except:
            return False

    # 应用所有修复
    for key, new_value in fixes.items():
        if not find_and_fix(translations, '', key, new_value):
            not_found.append(key)

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    return fixed_count, not_found

def main():
    en_path = Path('i18n/en_US.json')

    print("Fixing bad translations in en_US.json...")
    print(f"Total fixes to apply: {len(TRANSLATION_FIXES)}\n")

    fixed_count, not_found = fix_translations_in_file(en_path, TRANSLATION_FIXES)

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} translations")

    if not_found:
        print(f"\nWarning: {len(not_found)} keys not found:")
        for key in not_found[:10]:
            print(f"  - {key}")
        if len(not_found) > 10:
            print(f"  ... and {len(not_found)-10} more")

    print(f"\nUpdated: {en_path}")

if __name__ == '__main__':
    main()
