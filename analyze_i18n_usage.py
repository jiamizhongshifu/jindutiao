"""
Analyze i18n usage in the desktop application
"""
import os
import re

# Count tr() usage in main application files
tr_usage_count = 0
hardcoded_chinese = []

main_files = ['main.py', 'config_gui.py', 'timeline_editor.py', 'statistics_gui.py']

for filename in main_files:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

            # Count tr() calls
            tr_calls = len(re.findall(r'\btr\(', content))
            tr_usage_count += tr_calls

            # Check for hardcoded Chinese (strings containing Chinese characters)
            # Exclude comments
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#'):
                    continue

                # Find strings with Chinese characters
                # Look for quoted strings containing Chinese
                matches = re.finditer(r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']', line)
                for match in matches:
                    chinese_str = match.group(1)
                    # Skip if it's part of a tr() call
                    if 'tr(' not in line or line.index('tr(') > match.start():
                        hardcoded_chinese.append({
                            'file': filename,
                            'line': i,
                            'text': line.strip()[:100],
                            'chinese': chinese_str[:50]
                        })

print(f'=== i18n Usage Analysis ===\n')
print(f'Total tr() calls in main files: {tr_usage_count}')
print(f'Files checked: {", ".join(main_files)}')
print(f'Hardcoded Chinese strings found: {len(hardcoded_chinese)}\n')

if hardcoded_chinese:
    print('=== Sample Hardcoded Chinese (first 15) ===\n')
    for item in hardcoded_chinese[:15]:
        print(f'{item["file"]}:{item["line"]}')
        print(f'  Chinese: {item["chinese"]}')
        print(f'  Context: {item["text"]}')
        print()
else:
    print('[EXCELLENT] No hardcoded Chinese strings found!\n')

print('=== Recommendation ===')
if hardcoded_chinese:
    print('Replace hardcoded Chinese strings with tr() calls for proper internationalization.')
else:
    print('Application appears to be properly internationalized!')
