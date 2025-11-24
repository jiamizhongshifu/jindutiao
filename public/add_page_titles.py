import json

# Update zh_CN.json
with open('locales/zh_CN.json', 'r', encoding='utf-8') as f:
    zh = json.load(f)

# Update en_US.json
with open('locales/en_US.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Add page_title section to zh_CN
if 'page_title' not in zh:
    zh['page_title'] = {}

zh['page_title']['checkout'] = '结账 - GaiYa每日进度条'
zh['page_title']['index'] = 'GaiYa每日进度条 - 让每一天都清晰可见'
zh['page_title']['download'] = '下载 - GaiYa每日进度条'
zh['page_title']['pricing'] = '定价 - GaiYa每日进度条'
zh['page_title']['help'] = '帮助中心 - GaiYa每日进度条'
zh['page_title']['about'] = '关于 - GaiYa每日进度条'

# Add page_title section to en_US
if 'page_title' not in en:
    en['page_title'] = {}

en['page_title']['checkout'] = 'Checkout - GaiYa Time Progress Bar'
en['page_title']['index'] = 'GaiYa Time Progress Bar - Visualize Every Minute of Your Day'
en['page_title']['download'] = 'Download - GaiYa Time Progress Bar'
en['page_title']['pricing'] = 'Pricing - GaiYa Time Progress Bar'
en['page_title']['help'] = 'Help Center - GaiYa Time Progress Bar'
en['page_title']['about'] = 'About - GaiYa Time Progress Bar'

# Save files
with open('locales/zh_CN.json', 'w', encoding='utf-8') as f:
    json.dump(zh, f, ensure_ascii=False, indent=2)

with open('locales/en_US.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

print('Added page titles to translation files')
print('zh_CN: 6 page titles')
print('en_US: 6 page titles')
