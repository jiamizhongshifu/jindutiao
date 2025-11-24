import os
import re

html_files = [
    'download.html',
    'pricing.html',
    'help.html',
    'about.html',
    'payment-success.html',
    'payment-cancel.html',
    'email-verified.html'
]

print('=== Checking Navigation Bars ===\n')

for filename in html_files:
    if not os.path.exists(filename):
        print(f'{filename}: FILE NOT FOUND')
        continue

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for language switcher
    has_lang_switcher = 'language-switcher' in content or 'data-lang-switch' in content

    # Check for navbar
    has_navbar = '<nav class="navbar">' in content

    # Check for GitHub link
    has_github = 'github.com/jiamizhongshifu/jindutiao' in content

    status = 'OK' if has_lang_switcher else 'MISSING'
    print(f'[{status}] {filename}:')
    print(f'   Navbar: {"Yes" if has_navbar else "No"}')
    print(f'   Lang Switcher: {"Yes" if has_lang_switcher else "No"}')
    print(f'   GitHub Link: {"Yes" if has_github else "No"}')
    print()
