#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add medium priority translations to i18n files"""

import json
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Medium priority translations (6 new user-facing items)
MEDIUM_PRIORITY_TRANSLATIONS = {
    # Error messages (3 items)
    "config.errors.template_save_failed": {
        "zh_CN": "无法保存模板:\n{error}",
        "en_US": "Unable to save template:\n{error}"
    },
    "config.errors.template_format_error": {
        "zh_CN": "模板文件格式错误:\n{error}",
        "en_US": "Template file format error:\n{error}"
    },
    "config.errors.template_load_failed": {
        "zh_CN": "加载模板失败:\n{error}",
        "en_US": "Failed to load template:\n{error}"
    },

    # Success messages (2 items)
    "config.messages.template_updated": {
        "zh_CN": "模板已更新:\n{template_filename}\n\n包含 {task_count} 个任务。",
        "en_US": "Template updated:\n{template_filename}\n\nContains {task_count} tasks."
    },
    "config.messages.template_created": {
        "zh_CN": "模板已创建:\n{template_filename}\n\n已添加到【我的模板】列表中,包含 {task_count} 个任务。",
        "en_US": "Template created:\n{template_filename}\n\nAdded to [My Templates] list with {task_count} tasks."
    },

    # Confirmation prompt (1 item)
    "config.prompts.confirm_load_template": {
        "zh_CN": "即将加载自定义模板: {template_name}\n\n包含 {task_count} 个任务\n\n当前表格中的任务将被替换,是否继续?",
        "en_US": "About to load custom template: {template_name}\n\nContains {task_count} tasks\n\nCurrent tasks will be replaced. Continue?"
    },

    # Test result message (optional)
    "config.schedule.test_date_display": {
        "zh_CN": "测试日期: {test_date}",
        "en_US": "Test date: {test_date}"
    }
}

def add_nested_key(data, key_path, value):
    """Add a nested key to a dictionary"""
    parts = key_path.split('.')
    current = data

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value

def main():
    print("=" * 80)
    print("添加中优先级翻译到 i18n 文件")
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
    updated_count = 0

    for key, translations in MEDIUM_PRIORITY_TRANSLATIONS.items():
        # Check if key exists
        parts = key.split('.')

        zh_exists = True
        current = zh_data
        for part in parts:
            if part not in current:
                zh_exists = False
                break
            current = current.get(part, {})

        # Add to zh_CN
        add_nested_key(zh_data, key, translations['zh_CN'])

        # Add to en_US
        add_nested_key(en_data, key, translations['en_US'])

        if zh_exists:
            updated_count += 1
            print(f"⚠️  更新: {key}")
        else:
            added_count += 1
            print(f"✓ 添加: {key}")
            print(f"   中文: {translations['zh_CN'][:50]}...")
            print(f"   英文: {translations['en_US'][:50]}...")
            print()

    print()
    print(f"总计: 新增 {added_count} 项, 更新 {updated_count} 项")
    print()

    # Save updated files
    with open(zh_path, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    print("✓ i18n 文件已更新")
    print()

    # Generate replacement mapping
    replacement_map = []

    for key, translations in MEDIUM_PRIORITY_TRANSLATIONS.items():
        replacement_map.append({
            'key': key,
            'zh_CN': translations['zh_CN'],
            'en_US': translations['en_US'],
            'replacement_pattern': f'self.i18n.t("{key}")'
        })

    with open('medium_priority_replacement_map.json', 'w', encoding='utf-8') as f:
        json.dump(replacement_map, f, ensure_ascii=False, indent=2)

    print("✓ 替换映射已生成: medium_priority_replacement_map.json")
    print()
    print("=" * 80)
    print("下一步: 应用这些翻译到代码中")
    print("=" * 80)

if __name__ == '__main__':
    main()
