#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add missing translations found in config UI screenshots"""

import json
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def add_nested_key(data, key_path, value):
    """Add a nested key to a dictionary, checking for conflicts"""
    parts = key_path.split('.')
    current = data

    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            # Conflict: existing value is not a dict
            print(f"  ⚠️  Conflict at {'.'.join(parts[:i+1])}: existing value is not a dict")
            return False
        current = current[part]

    # Set final value
    final_key = parts[-1]
    if final_key in current and isinstance(current[final_key], dict):
        print(f"  ⚠️  Conflict at {key_path}: existing value is a dict")
        return False

    current[final_key] = value
    return True

# Additional translations needed
TRANSLATIONS = {
    # Tab titles
    'config.tabs.appearance': {'zh': '外观配置', 'en': 'Appearance'},
    'config.tabs.tasks': {'zh': '任务管理', 'en': 'Task Management'},
    'config.tabs.scene': {'zh': '场景设置', 'en': 'Scene Settings'},
    'config.tabs.notifications': {'zh': '通知设置', 'en': 'Notifications'},
    'config.tabs.about': {'zh': '关于', 'en': 'About'},

    # Basic Settings labels
    'config.labels.show_index': {'zh': '显示带索引', 'en': 'Show Index'},
    'config.labels.update_interval': {'zh': '更新间隔', 'en': 'Update Interval'},
    'config.labels.autostart': {'zh': '自启动', 'en': 'Launch at Startup'},
    'config.labels.marker_width': {'zh': '时间标记宽度', 'en': 'Time Marker Width'},
    'config.labels.marker_type': {'zh': '时间标记类型', 'en': 'Marker Type'},
    'config.labels.marker_x_offset': {'zh': '标记图片 X 偏移', 'en': 'Marker Image X Offset'},
    'config.labels.marker_y_offset': {'zh': '标记图片 Y 偏移', 'en': 'Marker Image Y Offset'},
    'config.labels.animation_speed': {'zh': '动画播放速度', 'en': 'Animation Speed'},

    # Task Management
    'config.ai.title': {'zh': 'AI智能规划', 'en': 'AI Smart Planning'},
    'config.theme.title': {'zh': '预设主题颜色', 'en': 'Preset Theme Colors'},
    'config.templates.preset_label': {'zh': '预设模板', 'en': 'Preset Templates'},
    'config.templates.custom_label': {'zh': '我的模板', 'en': 'My Templates'},
    'config.editor.title': {'zh': '可视化时间编辑器', 'en': 'Visual Time Editor'},

    # Table headers
    'config.table.start_time': {'zh': '开始时间', 'en': 'Start Time'},
    'config.table.end_time': {'zh': '结束时间', 'en': 'End Time'},
    'config.table.task_name': {'zh': '任务名称', 'en': 'Task Name'},
    'config.table.bg_color': {'zh': '背景颜色', 'en': 'Background'},
    'config.table.text_color': {'zh': '文字颜色', 'en': 'Text Color'},
    'config.table.actions': {'zh': '操作', 'en': 'Actions'},

    # Scene Settings
    'config.scene.basic_settings': {'zh': '基础设置', 'en': 'Basic Settings'},
    'config.scene.current_scene': {'zh': '当前Scene', 'en': 'Current Scene'},
    'config.scene.advanced': {'zh': '高级功能', 'en': 'Advanced'},
    'config.scene.editor_button': {'zh': 'OpenScene编辑器', 'en': 'Open Scene Editor'},
    'config.scene.editor_desc': {'zh': 'Scene编辑器可以创建和编辑自定义Scene效果', 'en': 'Scene editor allows you to create and edit custom scene effects'},

    # Notifications
    'config.notifications.basic_settings': {'zh': '基础设置', 'en': 'Basic Settings'},
    'config.notifications.timing': {'zh': '提醒时机', 'en': 'Reminder Timing'},
    'config.notifications.before_start': {'zh': '任务开始前提醒', 'en': 'Task Start Reminders'},
    'config.notifications.before_end': {'zh': '任务结束前提醒', 'en': 'Task End Reminders'},
    'config.notifications.minutes_before': {'zh': '提前 (minutes) 分钟', 'en': 'Minutes Before'},
    'config.notifications.dnd_title': {'zh': '免打扰时段', 'en': 'Do Not Disturb'},
    'config.notifications.enable_dnd': {'zh': '启用Do Not Disturb时段', 'en': 'Enable Do Not Disturb Period'},
    'config.notifications.dnd_start': {'zh': '开始时间', 'en': 'Start Time'},
    'config.notifications.dnd_end': {'zh': '结束时间', 'en': 'End Time'},
    'config.notifications.play_sound': {'zh': '播放Info音', 'en': 'Play Info Sound'},

    # Membership
    'membership.validity_30': {'zh': '有效期30天', 'en': 'Valid for 30 days'},
    'membership.validity_365': {'zh': '有效期365天', 'en': 'Valid for 365 days'},
    'membership.lifetime': {'zh': '永久有效', 'en': 'Lifetime Access'},
    'membership.no_auto_renew': {'zh': '到期后不会自动扣费', 'en': 'No automatic renewal after expiration'},
    'membership.one_time': {'zh': '一次购买,终身可用', 'en': 'One-time purchase, lifetime access'},
    'membership.partner': {'zh': '会员合伙人', 'en': 'Partner Member'},
    'membership.save_percent': {'zh': '节省 {percent}%', 'en': 'Save {percent}%'},

    # About
    'about.slogan': {'zh': '让每一天都清晰可见', 'en': 'Make every day clearly visible'},
    'about.version': {'zh': '版本 v{version}', 'en': 'Version v{version}'},
    'about.check_update': {'zh': '检查Update', 'en': 'Check for Updates'},
    'about.copyright': {'zh': '© {year} GaiYa 团队', 'en': '© {year} GaiYa Team'},

    # Buttons - fix the incorrect "Save所有Settings"
    'button.save_all_settings': {'zh': '保存所有设置', 'en': 'Save Settings'},
}

def main():
    print("=" * 80)
    print("添加配置界面缺失的翻译")
    print("=" * 80)
    print()

    # Load existing i18n files
    zh_path = Path('i18n/zh_CN.json')
    en_path = Path('i18n/en_US.json')

    with open(zh_path, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    with open(en_path, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    print(f"已加载现有翻译文件")
    print()

    # Add translations
    added_count = 0
    skipped_count = 0

    for key, trans in TRANSLATIONS.items():
        # Add to zh_CN
        zh_success = add_nested_key(zh_data, key, trans['zh'])

        # Add to en_US
        en_success = add_nested_key(en_data, key, trans['en'])

        if zh_success and en_success:
            added_count += 1
            print(f"✓ {key}")
        else:
            skipped_count += 1

    print()
    print(f"总计: 新增 {added_count} 项, 跳过 {skipped_count} 项")
    print()

    # Save updated files
    with open(zh_path, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    print("✓ i18n 文件已更新")
    print()
    print("=" * 80)
    print("翻译分类统计:")
    print("=" * 80)
    print(f"  标签页标题: 5")
    print(f"  基础设置标签: 8")
    print(f"  任务管理: 5")
    print(f"  表格表头: 6")
    print(f"  场景设置: 5")
    print(f"  通知设置: 10")
    print(f"  会员信息: 7")
    print(f"  关于页面: 4")
    print(f"  按钮: 1")
    print()
    print(f"总计: {len(TRANSLATIONS)} 个新翻译键")
    print("=" * 80)

if __name__ == '__main__':
    main()
