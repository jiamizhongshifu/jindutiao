#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加缺失的AI配额相关翻译key
"""

import json
from pathlib import Path

# 缺失的翻译
missing_translations = {
    "account": {
        "feature": {
            "ai_quota_20_per_day": {
                "zh": "20次/天 AI智能规划",
                "en": "20 AI planning tasks/day"
            },
            "ai_quota_50_per_day": {
                "zh": "50次/天 AI智能规划",
                "en": "50 AI planning tasks/day"
            }
        }
    }
}

def merge_translations(file_path, new_translations):
    """合并翻译到现有文件"""
    # 读取现有翻译
    with open(file_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    # 深度合并
    def deep_merge(base, updates):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    deep_merge(existing, new_translations)

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def main():
    zh_path = Path('i18n/zh_CN.json')
    en_path = Path('i18n/en_US.json')

    print("Adding missing AI quota translation keys...")

    # 提取中英文翻译
    zh_new = {}
    en_new = {}

    def extract_lang(obj, lang, prefix=''):
        result = {}
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                if lang in value:
                    # 叶子节点
                    result[key] = value[lang]
                else:
                    # 继续递归
                    result[key] = extract_lang(value, lang)
            else:
                result[key] = value
        return result

    zh_new = extract_lang(missing_translations, 'zh')
    en_new = extract_lang(missing_translations, 'en')

    # 合并
    merge_translations(zh_path, zh_new)
    merge_translations(en_path, en_new)

    print(f"Added 2 new translation keys")
    print(f"Updated: {zh_path}")
    print(f"Updated: {en_path}")

if __name__ == '__main__':
    main()
