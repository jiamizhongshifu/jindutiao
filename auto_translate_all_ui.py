#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automatic translation system for all UI strings"""

import json
import re
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_existing_i18n():
    """Load existing translations"""
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_data = json.load(f)
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    return zh_data, en_data

def find_matching_key(text, zh_data):
    """Find if text already has a translation key"""
    def search_dict(d, prefix=''):
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result = search_dict(value, full_key)
                if result:
                    return result
            elif isinstance(value, str) and value == text:
                return full_key
        return None

    return search_dict(zh_data)

def translate_to_english(chinese_text):
    """Simple translation rules for common UI elements"""
    translations = {
        # Buttons
        "确定": "OK",
        "取消": "Cancel",
        "保存": "Save",
        "删除": "Delete",
        "编辑": "Edit",
        "添加": "Add",
        "禁用": "Disable",
        "启用": "Enable",
        "关闭": "Close",
        "应用": "Apply",
        "刷新": "Refresh",

        # Common labels
        "警告": "Warning",
        "错误": "Error",
        "成功": "Success",
        "提示": "Hint",
        "信息": "Information",
        "冲突": "Conflict",
        "输入错误": "Input Error",

        # Template related
        "保存为模板": "Save as Template",
        "选择模板": "Select Template",
        "模板名称": "Template Name",
        "添加模板应用规则": "Add Template Rule",
        "编辑模板应用规则": "Edit Template Rule",

        # Time/Date related
        "按星期重复": "Repeat by Week",
        "每月重复": "Repeat Monthly",
        "特定日期": "Specific Dates",
        "添加日期": "Add Date",
        "选择具体日期": "Select Specific Date",

        # Common phrases
        "请输入": "Please enter",
        "例如": "For example",
        "选择": "Select",
    }

    # Try exact match first
    if chinese_text in translations:
        return translations[chinese_text]

    # Try partial matches for compound phrases
    for zh, en in translations.items():
        if zh in chinese_text:
            # Simple replacement for now
            result = chinese_text.replace(zh, en)
            if result != chinese_text:
                return result

    # Generic translation
    return f"[TODO: {chinese_text}]"

def generate_key_name(text, category):
    """Generate a suitable key name"""
    # Remove special characters
    clean = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', text)
    clean = clean.strip()[:30]  # Limit length

    # Use pinyin-like representation (simplified)
    # For now, just use numbered keys
    import hashlib
    hash_suffix = hashlib.md5(clean.encode()).hexdigest()[:6]

    return f"{category}.ui_{hash_suffix}"

def main():
    print("=" * 80)
    print("自动翻译系统 - 批量处理所有UI字符串")
    print("=" * 80)
    print()

    # Load existing translations
    zh_data, en_data = load_existing_i18n()
    print("✓ 已加载现有翻译")

    # Load UI strings to translate
    with open('all_ui_chinese_strings.json', 'r', encoding='utf-8') as f:
        ui_data = json.load(f)

    items = ui_data['items']
    print(f"✓ 需要处理 {len(items)} 个UI字符串")
    print()

    # Process each string
    matched = []
    need_translation = []

    for item in items:
        text = item['text']

        # Check if already has a key
        existing_key = find_matching_key(text, zh_data)

        if existing_key:
            matched.append({
                'item': item,
                'key': existing_key,
                'status': 'matched'
            })
        else:
            need_translation.append(item)

    print(f"匹配结果:")
    print(f"  - 已有翻译键: {len(matched)}")
    print(f"  - 需要新建: {len(need_translation)}")
    print()

    # Generate new translations
    new_translations = {}

    for item in need_translation:
        text = item['text']

        # Determine category
        if any(w in text for w in ['警告', '错误', '成功', '冲突']):
            category = 'config.labels'
        elif any(w in text for w in ['模板', 'template']):
            category = 'config.template_ui'
        elif len(text) < 10 and ('button' in item['code'].lower() or 'btn' in item['code'].lower()):
            category = 'config.buttons'
        else:
            category = 'config.ui'

        key = generate_key_name(text, category)
        en_text = translate_to_english(text)

        new_translations[key] = {
            'zh_CN': text,
            'en_US': en_text,
            'line': item['line'],
            'code': item['code'][:100]
        }

    print(f"生成了 {len(new_translations)} 个新翻译")
    print()

    # Save for review
    output = {
        'summary': {
            'total': len(items),
            'matched': len(matched),
            'new': len(new_translations)
        },
        'matched_keys': matched,
        'new_translations': new_translations
    }

    with open('auto_translation_plan.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("✓ 翻译计划已保存到: auto_translation_plan.json")
    print()
    print("=" * 80)
    print("下一步:")
    print("  1. 审查新生成的翻译（特别是[TODO]标记的）")
    print("  2. 运行应用脚本批量添加到i18n文件")
    print("  3. 运行替换脚本更新代码")
    print("=" * 80)

if __name__ == '__main__':
    main()
