#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate i18n key suggestions for untranslated strings"""

import json
import re
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def suggest_i18n_key(text, line_num, code):
    """Suggest an appropriate i18n key based on context"""

    # Remove special characters for key generation
    text_clean = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', text)

    # Check context from code
    if 'setToolTip' in code:
        category = 'tooltips'
    elif 'QMessageBox' in code or 'Dialog' in code:
        category = 'dialogs'
    elif 'logging.error' in code or '失败' in text or '错误' in text:
        category = 'errors'
    elif 'logging.info' in code:
        category = 'logs'
    elif '"""' in code and text == code.strip().strip('"""'):
        category = 'docstrings'
    elif '会员' in text or '套餐' in text or '支付' in text:
        category = 'membership'
    elif '模板' in text:
        category = 'templates'
    elif '时间表' in text or '时间轴' in text:
        category = 'schedule'
    elif '主题' in text:
        category = 'theme'
    elif '场景' in text:
        category = 'scene'
    elif '通知' in text:
        category = 'notification'
    else:
        category = 'general'

    # Generate key name (simplified pinyin-like conversion)
    # For demonstration, just use a numbered approach
    key_name = f"item_{line_num}"

    return category, key_name

def main():
    # Load audit data
    with open('config_i18n_audit_data.json', 'r', encoding='utf-8') as f:
        audit_data = json.load(f)

    untranslated = audit_data['untranslated_details']

    # Group by category
    categorized = {
        'tooltips': [],
        'dialogs': [],
        'membership': [],
        'templates': [],
        'schedule': [],
        'theme': [],
        'scene': [],
        'notification': [],
        'errors': [],
        'logs': [],
        'docstrings': [],
        'general': []
    }

    for item in untranslated:
        category, key_name = suggest_i18n_key(
            item['text'],
            item['line'],
            item['code']
        )
        categorized[category].append(item)

    # Generate translation templates
    translations_zh = {}
    translations_en = {}

    # Priority 1: User-facing UI
    priority_categories = ['tooltips', 'dialogs', 'membership']

    print("=" * 80)
    print("高优先级翻译清单（用户界面文本）")
    print("=" * 80)
    print()

    priority_items = []
    for cat in priority_categories:
        if categorized[cat]:
            print(f"\n## {cat.upper()} ({len(categorized[cat])} 项)\n")
            for i, item in enumerate(categorized[cat], 1):
                key = f"config.{cat}.{i}"
                print(f"{i}. 行 {item['line']}: {item['text'][:60]}...")
                print(f"   建议键: {key}")
                print()

                translations_zh[key] = item['text']
                translations_en[key] = f"[TODO: Translate] {item['text']}"
                priority_items.append(item)

    # Priority 2: Other UI elements
    print("\n" + "=" * 80)
    print("中优先级翻译清单（其他UI元素）")
    print("=" * 80)
    print()

    medium_categories = ['templates', 'schedule', 'theme', 'scene', 'notification']
    medium_items = []

    for cat in medium_categories:
        if categorized[cat]:
            print(f"\n## {cat.upper()} ({len(categorized[cat])} 项)\n")
            for i, item in enumerate(categorized[cat], 1):
                if len(item['text']) < 50:  # Only short UI texts
                    key = f"config.{cat}.{i}"
                    print(f"{i}. 行 {item['line']}: {item['text']}")
                    print(f"   建议键: {key}")
                    print()

                    translations_zh[key] = item['text']
                    translations_en[key] = f"[TODO] {item['text']}"
                    medium_items.append(item)

    # Summary
    print("\n" + "=" * 80)
    print("统计总结")
    print("=" * 80)
    print(f"\n高优先级项目: {len(priority_items)}")
    print(f"中优先级项目: {len(medium_items)}")
    print(f"Docstrings（建议改英文）: {len(categorized['docstrings'])}")
    print(f"日志消息（可保留中文）: {len(categorized['logs'])}")
    print()

    # Save suggested translations
    output = {
        'summary': {
            'high_priority': len(priority_items),
            'medium_priority': len(medium_items),
            'docstrings': len(categorized['docstrings']),
            'logs': len(categorized['logs'])
        },
        'zh_CN_additions': translations_zh,
        'en_US_additions': translations_en,
        'categorized_counts': {k: len(v) for k, v in categorized.items()}
    }

    with open('i18n_translation_suggestions.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] 翻译建议已保存到: i18n_translation_suggestions.json")

    # Generate a TODO checklist
    with open('i18n_translation_todo.md', 'w', encoding='utf-8') as f:
        f.write("# 配置界面国际化待办清单\n\n")
        f.write("## ✅ 高优先级（必须完成）\n\n")

        for i, item in enumerate(priority_items, 1):
            f.write(f"- [ ] 行 {item['line']}: `{item['text'][:50]}...`\n")

        f.write("\n## 🔄 中优先级（建议完成）\n\n")

        for i, item in enumerate(medium_items, 1):
            f.write(f"- [ ] 行 {item['line']}: `{item['text'][:50]}...`\n")

        f.write("\n## 📝 Docstrings（改为英文）\n\n")
        f.write(f"- [ ] 将 {len(categorized['docstrings'])} 个文档字符串改为英文\n")

    print(f"[OK] 待办清单已保存到: i18n_translation_todo.md")

if __name__ == '__main__':
    main()
