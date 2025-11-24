#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace schedule-related strings with tr() calls
"""

import re

def replace_schedule_strings():
    """Replace schedule strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements - more careful this time
    # Only replace strings that are clearly standalone, not in comments or docstrings
    replacements = [
        # Weekdays - only in QCheckBox or similar UI contexts
        (r'QCheckBox\("周一"\)', 'QCheckBox(tr("schedule.weekdays.monday"))'),
        (r'QCheckBox\("周二"\)', 'QCheckBox(tr("schedule.weekdays.tuesday"))'),
        (r'QCheckBox\("周三"\)', 'QCheckBox(tr("schedule.weekdays.wednesday"))'),
        (r'QCheckBox\("周四"\)', 'QCheckBox(tr("schedule.weekdays.thursday"))'),
        (r'QCheckBox\("周五"\)', 'QCheckBox(tr("schedule.weekdays.friday"))'),
        (r'QCheckBox\("周六"\)', 'QCheckBox(tr("schedule.weekdays.saturday"))'),
        (r'QCheckBox\("周日"\)', 'QCheckBox(tr("schedule.weekdays.sunday"))'),

        # Rule types - only in QRadioButton contexts
        (r'QRadioButton\("按星期重复"\)', 'QRadioButton(tr("schedule.rule_types.weekly"))'),
        (r'QRadioButton\("每月重复"\)', 'QRadioButton(tr("schedule.rule_types.monthly"))'),
        (r'QRadioButton\("特定日期"\)', 'QRadioButton(tr("schedule.rule_types.specific_date"))'),

        # UI labels - buttons and labels
        (r'QPushButton\("\+ 添加日期"\)', 'QPushButton(tr("schedule.ui.add_date"))'),
        (r'QPushButton\("编辑"\)', 'QPushButton(tr("schedule.ui.edit"))'),

        # Enable/Disable status strings
        (r'"✅ 启用"', 'tr("schedule.ui.enabled")'),
        (r'"❌ 禁用"', 'tr("schedule.ui.disabled")'),
        (r'"启用"(?!】)', 'tr("schedule.ui.enable")'),  # Not followed by】
        (r'"禁用"(?!】)', 'tr("schedule.ui.disable")'),  # Not followed by】

        # Dialog and section titles
        (r'QLabel\("规则类型"\)', 'QLabel(tr("schedule.ui.rule_type"))'),
        (r'QGroupBox\("模板自动应用"\)', 'QGroupBox(tr("schedule.ui.template_auto_apply"))'),

        # Dialog window titles
        (r'setWindowTitle\("添加模板应用规则"\)', 'setWindowTitle(tr("schedule.dialogs.add_rule"))'),
        (r'setWindowTitle\("编辑模板应用规则"\)', 'setWindowTitle(tr("schedule.dialogs.edit_rule"))'),
        (r'setWindowTitle\("删除时间表规则"\)', 'setWindowTitle(tr("schedule.dialogs.delete_rule"))'),

        # Messages - standalone strings in QMessageBox or similar
        (r'"时间表管理器未初始化"', 'tr("schedule.messages.manager_not_initialized")'),
        (r'"时间表规则已添加"', 'tr("schedule.messages.rule_added")'),
        (r'"时间表规则已更新"', 'tr("schedule.messages.rule_updated")'),
        (r'"更新规则失败，请检查"', 'tr("schedule.messages.rule_update_failed")'),
        (r'"无效的规则索引"', 'tr("schedule.messages.invalid_rule_index")'),
        (r'"请至少选择一个星期"', 'tr("schedule.messages.select_at_least_one_weekday")'),
        (r'"请输入每月的日期"', 'tr("schedule.messages.enter_monthly_dates")'),
        (r'"日期必须在1-31之间"', 'tr("schedule.messages.date_must_be_1_to_31")'),
        (r'"日期格式错误，请使用逗号分隔的数字"', 'tr("schedule.messages.date_format_error")'),
        (r'"请至少添加一个日期"', 'tr("schedule.messages.add_at_least_one_date")'),
        (r'"请选择规则类型"', 'tr("schedule.messages.select_rule_type")'),
        (r'"规则已删除"', 'tr("schedule.messages.rule_deleted")'),
        (r'"冲突"', 'tr("schedule.messages.conflict")'),

        # Language strings
        (r'"简体中文"', 'tr("ui.language.zh_cn")'),
    ]

    # Apply replacements
    modified_count = 0
    for old, new in replacements:
        matches = len(re.findall(old, content))
        if matches > 0:
            content = re.sub(old, new, content)
            modified_count += matches

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nTotal replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing schedule strings in config_gui.py...")
    replace_schedule_strings()
    print("\nDone!")
