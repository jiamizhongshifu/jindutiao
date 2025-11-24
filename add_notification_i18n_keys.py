#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""添加 create_notification_tab() 国际化翻译键"""

import json

# Define new translation keys
new_keys_zh = {
    "notification": {
        "basic_settings_title": "⚙️ 基础设置",
        "reminder_timing_title": "⏰ 提醒时机",
        "before_start_title": "🔔 任务开始前提醒",
        "before_end_title": "🔕 任务结束前提醒",
        "do_not_disturb_title": "🌙 免打扰时段",
        "info_label": "配置任务提醒通知,让您不会错过任何重要时刻",
        "before_start_hint": "选择在任务开始前多久提醒(可多选):",
        "before_end_hint": "选择在任务结束前多久提醒(可多选):",
        "after_time_hint": "(在此时间后不发送通知)",
        "start_time_label": "开始时间:",
        "before_time_hint": "(在此时间前不发送通知)",
        "end_time_label": "结束时间:",
        "dnd_example": "示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰",
        "enable_notifications": "启用任务提醒通知",
        "enable_sound": "播放提示音",
        "notify_at_start": "任务开始时提醒",
        "notify_at_end": "任务结束时提醒",
        "enable_dnd": "启用免打扰时段",
        "minutes_before": "提前 {minutes} 分钟"
    }
}

new_keys_en = {
    "notification": {
        "basic_settings_title": "⚙️ Basic Settings",
        "reminder_timing_title": "⏰ Reminder Timing",
        "before_start_title": "🔔 Before Task Start",
        "before_end_title": "🔕 Before Task End",
        "do_not_disturb_title": "🌙 Do Not Disturb",
        "info_label": "Configure task reminder notifications so you won't miss any important moments",
        "before_start_hint": "Select how long before task start to remind (multiple selection):",
        "before_end_hint": "Select how long before task end to remind (multiple selection):",
        "after_time_hint": "(No notifications will be sent after this time)",
        "start_time_label": "Start Time:",
        "before_time_hint": "(No notifications will be sent before this time)",
        "end_time_label": "End Time:",
        "dnd_example": "Example: 22:00 - 08:00 means no disturb from 10 PM to 8 AM",
        "enable_notifications": "Enable Task Reminder Notifications",
        "enable_sound": "Play Notification Sound",
        "notify_at_start": "Notify at Task Start",
        "notify_at_end": "Notify at Task End",
        "enable_dnd": "Enable Do Not Disturb Period",
        "minutes_before": "{minutes} minutes before"
    }
}

def add_keys_to_file(filepath, new_keys):
    """Add new keys to i18n file"""
    # Read existing data
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Add new keys
    keys_added = 0
    for namespace, keys in new_keys.items():
        if namespace not in data:
            data[namespace] = {}

        for key, value in keys.items():
            full_key = f"{namespace}.{key}"
            if key not in data[namespace]:
                data[namespace][key] = value
                keys_added += 1
                print(f"Added: {full_key}")
            else:
                print(f"Skipped (exists): {full_key}")

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return keys_added

# Process both files
print("=== Adding translation keys to zh_CN.json ===")
zh_added = add_keys_to_file('i18n/zh_CN.json', new_keys_zh)

print("\n=== Adding translation keys to en_US.json ===")
en_added = add_keys_to_file('i18n/en_US.json', new_keys_en)

print(f"\n=== Summary ===")
print(f"Chinese keys added: {zh_added}")
print(f"English keys added: {en_added}")
print(f"Total new keys: {zh_added}")
