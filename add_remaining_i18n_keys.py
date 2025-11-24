#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add remaining translation keys to i18n JSON files
"""

import json
from pathlib import Path

def deep_merge(target, source):
    """Deep merge source dict into target dict"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value

def add_remaining_keys():
    """Add remaining translation keys"""

    # New keys in Chinese
    remaining_zh = {
        "templates": {
            "dialog": {
                "save_as_template": "保存为模板",
                "select_or_create": "选择要覆盖的模板或输入新的模板名称:",
                "enter_name": "请输入模板名称:",
                "hint_title": "💡 提示:\n",
                "hint_overwrite": "• 选择历史模板将直接覆盖该模板\n",
                "hint_create": "• 输入新名称将创建新的模板",
                "placeholder_select": "选择历史模板或输入新名称",
                "placeholder_example": "例如: 工作日模板"
            },
            "messages": {
                "name_empty": "模板名称不能为空!"
            },
            "template_with_count": "{name} ({count}个任务)",
            "auto_apply": {
                "select_template": "选择模板:",
                "rule_type": "规则类型",
                "monthly_days": "每月的哪些天？（用逗号分隔，例如: 1,15,28）",
                "select_dates": "选择具体日期:",
                "test_match": "测试日期匹配",
                "test_instruction": "选择一个日期，查看该日期会匹配到哪个模板：",
                "test_date": "测试日期: {date}",
                "will_load": "✅ 该日期会自动加载模板: {template}",
                "conflict_count": "⚠️ 警告：该日期有 {count} 个模板规则冲突！",
                "conflicting_templates": "冲突的模板：",
                "conflict_suggestion": "建议：删除或禁用其中某些规则，避免冲突",
                "no_match": "❌ 该日期没有匹配到任何模板规则",
                "use_default": "将使用默认24小时模板",
                "conflict_warning": "该规则与现有规则冲突，请检查",
                "confirm_delete_rule": "确定要删除这条规则吗?"
            }
        },
        "tabs": {
            "appearance": "🎨 外观配置",
            "tasks": "📋 任务管理",
            "scenes": "🎬 场景设置",
            "notifications": "🔔 通知设置",
            "profile": "👤 个人中心",
            "about": "📖 关于"
        },
        "ai": {
            "status": {
                "initializing": "⏳ AI服务正在初始化...",
                "starting": "⚠️ AI服务正在启动...",
                "init_failed": "❌ AI服务初始化失败"
            }
        }
    }

    # New keys in English
    remaining_en = {
        "templates": {
            "dialog": {
                "save_as_template": "Save as Template",
                "select_or_create": "Select a template to overwrite or enter a new template name:",
                "enter_name": "Please enter template name:",
                "hint_title": "💡 Hint:\n",
                "hint_overwrite": "• Selecting a history template will overwrite it directly\n",
                "hint_create": "• Entering a new name will create a new template",
                "placeholder_select": "Select history template or enter new name",
                "placeholder_example": "e.g., Workday Template"
            },
            "messages": {
                "name_empty": "Template name cannot be empty!"
            },
            "template_with_count": "{name} ({count} tasks)",
            "auto_apply": {
                "select_template": "Select Template:",
                "rule_type": "Rule Type",
                "monthly_days": "Which days of the month? (comma-separated, e.g., 1,15,28)",
                "select_dates": "Select specific dates:",
                "test_match": "Test Date Match",
                "test_instruction": "Select a date to see which template it will match:",
                "test_date": "Test Date: {date}",
                "will_load": "✅ This date will auto-load template: {template}",
                "conflict_count": "⚠️ Warning: This date has {count} template rule conflicts!",
                "conflicting_templates": "Conflicting templates:",
                "conflict_suggestion": "Suggestion: Delete or disable some rules to avoid conflicts",
                "no_match": "❌ This date doesn't match any template rule",
                "use_default": "Will use default 24-hour template",
                "conflict_warning": "This rule conflicts with existing rules, please check",
                "confirm_delete_rule": "Are you sure you want to delete this rule?"
            }
        },
        "tabs": {
            "appearance": "🎨 Appearance",
            "tasks": "📋 Tasks",
            "scenes": "🎬 Scenes",
            "notifications": "🔔 Notifications",
            "profile": "👤 Profile",
            "about": "📖 About"
        },
        "ai": {
            "status": {
                "initializing": "⏳ AI service is initializing...",
                "starting": "⚠️ AI service is starting...",
                "init_failed": "❌ AI service initialization failed"
            }
        }
    }

    # Load and merge zh_CN
    zh_file = Path('i18n/zh_CN.json')
    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    deep_merge(zh_data, remaining_zh)

    with open(zh_file, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated {zh_file}")

    # Load and merge en_US
    en_file = Path('i18n/en_US.json')
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    deep_merge(en_data, remaining_en)

    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated {en_file}")
    print("\nAdded translation keys for:")
    print("  - Template dialog (9 keys)")
    print("  - Template auto-apply (13 keys)")
    print("  - Tab labels (6 keys)")
    print("  - AI status (3 keys)")
    print("\nTotal: ~31 new keys")

if __name__ == '__main__':
    add_remaining_keys()
