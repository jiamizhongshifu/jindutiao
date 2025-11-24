import re

# Standard navbar actions section
STANDARD_NAVBAR_ACTIONS = '''            <div class="navbar-actions">
                <!-- Language Switcher -->
                <div class="language-switcher">
                    <button class="lang-btn" data-lang-switch="zh_CN" onclick="switchLanguage('zh_CN')">中</button>
                    <button class="lang-btn" data-lang-switch="en_US" onclick="switchLanguage('en_US')">EN</button>
                </div>
                <a href="https://github.com/jiamizhongshifu/jindutiao" target="_blank" class="btn btn-secondary btn-small">GitHub</a>
                <a href="index.html#download" class="btn btn-primary btn-small" data-i18n="hero.download_btn">立即下载</a>
            </div>'''

# Files to update
files_to_update = [
    ('help.html', 'help page'),
    ('about.html', 'about page')
]

for filename, description in files_to_update:
    print(f'\nProcessing {description} ({filename})...')

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and replace navbar-actions section
        # Pattern to match navbar-actions div and its contents
        pattern = r'<div class="navbar-actions">.*?</div>\s*</div>\s*</nav>'

        # Check if already has the standard navbar
        if 'github.com/jiamizhongshifu/jindutiao' in content:
            print(f'  Already has GitHub link - skipping')
            continue

        # Replace with standard navbar actions
        replacement = STANDARD_NAVBAR_ACTIONS + '\n        </div>\n    </nav>'

        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # Save the updated file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f'  Updated successfully')

    except Exception as e:
        print(f'  Error: {str(e)}')

print('\nDone!')
