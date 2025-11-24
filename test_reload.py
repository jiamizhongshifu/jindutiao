#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from i18n import tr, set_language, reload_translations
import json

# 检查文件有多少键
with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'JSON file has {len(data)} keys')

# 重新加载翻译
print('Reloading translations...')
reload_translations()

# 切换到英文
set_language('en_US')

# 测试翻译
test_keys = [
    'appearance.basic_settings',
    'appearance.background_color',
    'appearance.autostart',
]

for key in test_keys:
    value = tr(key)
    print(f'{key}: {value}')
