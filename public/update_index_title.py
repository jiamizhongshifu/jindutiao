import re

# Read index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update title tag
old_title = '<title>GaiYa每日进度条 - 让每一天都清晰可见</title>'
new_title = '<title data-i18n-page-title="page_title.index">GaiYa每日进度条 - 让每一天都清晰可见</title>'

if old_title in content:
    content = content.replace(old_title, new_title)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Successfully updated index.html title tag')
else:
    print('ERROR: Title tag not found or already updated')
