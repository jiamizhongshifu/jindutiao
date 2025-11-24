#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自动应用 create_notification_tab() 国际化修改"""

import re

# Read the file
with open('config_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Track changes
changes_made = 0
skipped = []
log_messages = []

# Define replacements (line_number, old_string, new_string, description)
replacements = [
    # Labels
    (2756, 'info_label = QLabel("配置任务提醒通知,让您不会错过任何重要时刻")',
     'info_label = QLabel(tr("notification.info_label"))',
     "Info label"),

    # Group titles
    (2761, 'basic_group = QGroupBox("⚙️ 基础设置")',
     'basic_group = QGroupBox(tr("notification.basic_settings_title"))',
     "Basic settings group title"),

    (2783, 'timing_group = QGroupBox("⏰ 提醒时机")',
     'timing_group = QGroupBox(tr("notification.reminder_timing_title"))',
     "Reminder timing group title"),

    (2789, 'before_start_group = QGroupBox("🔔 任务开始前提醒")',
     'before_start_group = QGroupBox(tr("notification.before_start_title"))',
     "Before start group title"),

    (2841, 'before_end_group = QGroupBox("🔕 任务结束前提醒")',
     'before_end_group = QGroupBox(tr("notification.before_end_title"))',
     "Before end group title"),

    (2895, 'dnd_group = QGroupBox("🌙 免打扰时段")',
     'dnd_group = QGroupBox(tr("notification.do_not_disturb_title"))',
     "DND group title"),

    # Checkboxes
    (2766, 'self.notify_enabled_check = QCheckBox("启用任务提醒通知")',
     'self.notify_enabled_check = QCheckBox(tr("notification.enable_notifications"))',
     "Enable notifications checkbox"),

    (2774, 'self.notify_sound_check = QCheckBox("播放提示音")',
     'self.notify_sound_check = QCheckBox(tr("notification.enable_sound"))',
     "Enable sound checkbox"),

    (2902, 'self.dnd_enabled_check = QCheckBox("启用免打扰时段")',
     'self.dnd_enabled_check = QCheckBox(tr("notification.enable_dnd"))',
     "Enable DND checkbox"),

    # Hint labels
    (2807, 'before_start_hint = QLabel("选择在任务开始前多久提醒(可多选):")',
     'before_start_hint = QLabel(tr("notification.before_start_hint"))',
     "Before start hint label"),

    (2859, 'before_end_hint = QLabel("选择在任务结束前多久提醒(可多选):")',
     'before_end_hint = QLabel(tr("notification.before_end_hint"))',
     "Before end hint label"),

    (2916, 'after_hint = QLabel("(在此时间后不发送通知)")',
     'after_hint = QLabel(tr("notification.after_time_hint"))',
     "After time hint label"),

    (2920, 'start_label = QLabel("开始时间:")',
     'start_label = QLabel(tr("notification.start_time_label"))',
     "Start time label"),

    (2931, 'before_hint = QLabel("(在此时间前不发送通知)")',
     'before_hint = QLabel(tr("notification.before_time_hint"))',
     "Before time hint label"),

    (2935, 'end_label = QLabel("结束时间:")',
     'end_label = QLabel(tr("notification.end_time_label"))',
     "End time label"),

    (2937, 'example_label = QLabel("示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰")',
     'example_label = QLabel(tr("notification.dnd_example"))',
     "DND example label"),

    # Note: Lines with "任务开始时提醒" and "任务结束时提醒" and "提前 {minutes} 分钟" need special handling
]

# Apply replacements
for line_num, old_str, new_str, desc in replacements:
    idx = line_num - 1
    if idx < len(lines):
        original_line = lines[idx]
        if old_str in original_line:
            lines[idx] = original_line.replace(old_str, new_str)
            changes_made += 1
            log_messages.append(f"✓ Line {line_num}: {desc}")
        else:
            skipped.append((line_num, desc, "String not found in line"))
            log_messages.append(f"✗ Line {line_num}: {desc} - SKIPPED (string not found)")
    else:
        skipped.append((line_num, desc, "Line number out of range"))
        log_messages.append(f"✗ Line {line_num}: {desc} - SKIPPED (out of range)")

# Write back
with open('config_gui.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))

# Write log
with open('notification_i18n_apply_log.txt', 'w', encoding='utf-8') as f:
    f.write('=== Notification Tab Internationalization Application Log ===\n\n')
    f.write(f'Total replacements attempted: {len(replacements)}\n')
    f.write(f'Successful: {changes_made}\n')
    f.write(f'Skipped: {len(skipped)}\n\n')

    f.write('=== Detailed Log ===\n')
    for msg in log_messages:
        f.write(msg + '\n')

    if skipped:
        f.write('\n=== Skipped Items (Manual Fix Required) ===\n')
        for line_num, desc, reason in skipped:
            f.write(f'Line {line_num}: {desc} - {reason}\n')

    f.write('\n=== Manual Fixes Required ===\n')
    f.write('Line 2805: Replace "任务开始时提醒" with tr("notification.notify_at_start")\n')
    f.write('Line 2813: Replace "任务开始时提醒" with tr("notification.notify_at_start")\n')
    f.write('Line 2814: Replace "任务开始时提醒" with tr("notification.notify_at_start")\n')
    f.write('Line 2828: Replace f"提前 {minutes} 分钟" with tr("notification.minutes_before", minutes=minutes)\n')
    f.write('Line 2857: Replace "任务结束时提醒" with tr("notification.notify_at_end")\n')
    f.write('Line 2865: Replace "任务结束时提醒" with tr("notification.notify_at_end")\n')
    f.write('Line 2866: Replace "任务结束时提醒" with tr("notification.notify_at_end")\n')
    f.write('Line 2879: Replace f"提前 {minutes} 分钟" with tr("notification.minutes_before", minutes=minutes)\n')

print(f'Changes made: {changes_made}/{len(replacements)}')
print(f'Skipped: {len(skipped)}')
print(f'Log written to notification_i18n_apply_log.txt')
print(f'\nManual fixes required: 8 items')
print('Please check notification_i18n_apply_log.txt for details')
