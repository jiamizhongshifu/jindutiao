#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add schedule/timetable i18n keys to translation files
"""

import json

def add_schedule_keys():
    """Add schedule translation keys"""

    # Schedule keys - Chinese
    schedule_keys_zh = {
        "schedule": {
            # Rule types
            "rule_types": {
                "weekly": "按星期重复",
                "monthly": "每月重复",
                "specific_date": "特定日期"
            },
            # Weekdays
            "weekdays": {
                "monday": "周一",
                "tuesday": "周二",
                "wednesday": "周三",
                "thursday": "周四",
                "friday": "周五",
                "saturday": "周六",
                "sunday": "周日"
            },
            # UI labels
            "ui": {
                "template_auto_apply": "模板自动应用",
                "rule_type": "规则类型",
                "add_date": "+ 添加日期",
                "edit": "编辑",
                "enabled": "✅ 启用",
                "disabled": "❌ 禁用",
                "enable": "启用",
                "disable": "禁用"
            },
            # Dialog titles
            "dialogs": {
                "add_rule": "添加模板应用规则",
                "edit_rule": "编辑模板应用规则",
                "delete_rule": "删除时间表规则"
            },
            # Messages
            "messages": {
                "manager_not_initialized": "时间表管理器未初始化",
                "rule_added": "时间表规则已添加",
                "rule_updated": "时间表规则已更新",
                "rule_update_failed": "更新规则失败，请检查",
                "invalid_rule_index": "无效的规则索引",
                "select_at_least_one_weekday": "请至少选择一个星期",
                "enter_monthly_dates": "请输入每月的日期",
                "date_must_be_1_to_31": "日期必须在1-31之间",
                "date_format_error": "日期格式错误，请使用逗号分隔的数字",
                "add_at_least_one_date": "请至少添加一个日期",
                "select_rule_type": "请选择规则类型",
                "rule_deleted": "规则已删除",
                "conflict": "冲突"
            }
        },
        "ui": {
            "language": {
                "zh_cn": "简体中文",
                "en_us": "English"
            }
        }
    }

    # Schedule keys - English
    schedule_keys_en = {
        "schedule": {
            # Rule types
            "rule_types": {
                "weekly": "Weekly Repeat",
                "monthly": "Monthly Repeat",
                "specific_date": "Specific Date"
            },
            # Weekdays
            "weekdays": {
                "monday": "Mon",
                "tuesday": "Tue",
                "wednesday": "Wed",
                "thursday": "Thu",
                "friday": "Fri",
                "saturday": "Sat",
                "sunday": "Sun"
            },
            # UI labels
            "ui": {
                "template_auto_apply": "Template Auto-Apply",
                "rule_type": "Rule Type",
                "add_date": "+ Add Date",
                "edit": "Edit",
                "enabled": "✅ Enabled",
                "disabled": "❌ Disabled",
                "enable": "Enable",
                "disable": "Disable"
            },
            # Dialog titles
            "dialogs": {
                "add_rule": "Add Template Apply Rule",
                "edit_rule": "Edit Template Apply Rule",
                "delete_rule": "Delete Schedule Rule"
            },
            # Messages
            "messages": {
                "manager_not_initialized": "Schedule manager not initialized",
                "rule_added": "Schedule rule added",
                "rule_updated": "Schedule rule updated",
                "rule_update_failed": "Failed to update rule, please check",
                "invalid_rule_index": "Invalid rule index",
                "select_at_least_one_weekday": "Please select at least one weekday",
                "enter_monthly_dates": "Please enter monthly dates",
                "date_must_be_1_to_31": "Date must be between 1-31",
                "date_format_error": "Date format error, please use comma-separated numbers",
                "add_at_least_one_date": "Please add at least one date",
                "select_rule_type": "Please select rule type",
                "rule_deleted": "Rule deleted",
                "conflict": "Conflict"
            }
        },
        "ui": {
            "language": {
                "zh_cn": "简体中文",
                "en_us": "English"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add schedule keys
    zh_cn['schedule'] = schedule_keys_zh['schedule']
    zh_cn['ui'] = schedule_keys_zh['ui']

    en_us['schedule'] = schedule_keys_en['schedule']
    en_us['ui'] = schedule_keys_en['ui']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Schedule translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_schedule = count_keys(schedule_keys_zh['schedule'])
    total_ui = count_keys(schedule_keys_zh['ui'])
    total = total_schedule + total_ui

    print(f"  - Schedule: {total_schedule} keys")
    print(f"  - UI: {total_ui} keys")
    print(f"Total new keys: {total}")

if __name__ == '__main__':
    add_schedule_keys()
