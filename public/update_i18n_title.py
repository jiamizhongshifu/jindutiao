import re

# Read i18n.js
with open('js/i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position to insert the page title update code
# We want to insert it after the HTML content update section and before the language switcher section

search_pattern = r'(        // Update HTML content \(use with caution\).*?\n        \}\);\n\n)(        // Update language switcher active state)'

replacement = r'''\1        // Update page title
        const titleEl = document.querySelector('title[data-i18n-page-title]');
        if (titleEl) {
            const key = titleEl.getAttribute('data-i18n-page-title');
            const translated = this.t(key);
            if (translated !== key) {
                document.title = translated;
            }
        }

\2'''

new_content = re.sub(search_pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open('js/i18n.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Successfully added page title update functionality to i18n.js')
else:
    print('WARNING: Pattern not found, file not modified')
