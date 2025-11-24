#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix all errors from batch replacements
"""

import re

def fix_all_errors():
    """Fix all syntax errors from replacements"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix 1: Remove double tr() calls
    content = re.sub(r'tr\(tr\(', r'tr(', content)

    # Fix 2: Add missing closing parentheses for QMessageBox calls
    # Pattern: QMessageBox.XXX(self, tr(...), tr(...)  <- missing )
    #          return
    pattern = r'(QMessageBox\.(warning|critical|information)\([^)]+\), tr\([^)]+\))\n(\s+return)'
    replacement = r'\1)\n\3'
    content = re.sub(pattern, replacement, content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Fixed all errors!")

if __name__ == '__main__':
    fix_all_errors()
