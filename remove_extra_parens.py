#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove extra closing parentheses from QMessageBox calls
"""

import re

def remove_extra_parens():
    """Remove duplicate closing parentheses"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: Find lines with 3 closing parens that should only have 2
    # QMessageBox.METHOD(self, tr(...), tr(...))) -> QMessageBox.METHOD(self, tr(...), tr(...))
    pattern = r'(QMessageBox\.(warning|information|critical|question)\(self, tr\("common\.dialog_titles\.[^"]+"\), tr\("[^"]+"\)\))\)'

    # Find all matches to count
    matches = re.findall(pattern, content)
    print(f"Found {len(matches)} lines with extra closing parentheses")

    # Replace: remove the extra closing paren
    content = re.sub(pattern, r'\1', content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Removed {len(matches)} extra closing parentheses")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Removing extra closing parentheses...")
    remove_extra_parens()
    print("\nDone!")
