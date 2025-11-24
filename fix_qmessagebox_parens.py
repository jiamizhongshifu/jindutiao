#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix missing closing parentheses in QMessageBox calls
"""

import re

def fix_qmessagebox_parens():
    """Add missing closing parentheses to QMessageBox calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: QMessageBox.XXX(self, tr(...), tr(...)  <- missing final )
    # We need to add ) before the newline
    pattern = r'(QMessageBox\.(warning|critical|information|question)\([^)]+\), tr\([^)]+\))\n'
    replacement = r'\1)\n'

    matches = len(re.findall(pattern, content))
    content = re.sub(pattern, replacement, content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Fixed {matches} missing closing parentheses")

if __name__ == '__main__':
    fix_qmessagebox_parens()
