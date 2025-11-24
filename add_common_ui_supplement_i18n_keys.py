#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add missing common UI supplement translation keys
"""

import json

def add_common_ui_supplement_keys():
    """Add edit button translation key to common namespace"""

    # Common UI supplement keys - Chinese
    common_ui_supplement_zh = {
        "common": {
            "buttons": {
                "edit": "编辑"
            }
        }
    }

    # Common UI supplement keys - English
    common_ui_supplement_en = {
        "common": {
            "buttons": {
                "edit": "Edit"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Merge with existing keys
    if 'common' not in zh_cn:
        zh_cn['common'] = {}
    if 'buttons' not in zh_cn['common']:
        zh_cn['common']['buttons'] = {}

    zh_cn['common']['buttons']['edit'] = common_ui_supplement_zh['common']['buttons']['edit']

    if 'common' not in en_us:
        en_us['common'] = {}
    if 'buttons' not in en_us['common']:
        en_us['common']['buttons'] = {}

    en_us['common']['buttons']['edit'] = common_ui_supplement_en['common']['buttons']['edit']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Common UI supplement translation keys added!")
    print("Added 1 new key: common.buttons.edit")

if __name__ == '__main__':
    add_common_ui_supplement_keys()
