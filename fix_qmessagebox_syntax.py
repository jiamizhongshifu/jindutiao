#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix QMessageBox.warning syntax errors caused by batch replacement
"""

import re

def fix_qmessagebox_syntax():
    """Fix missing closing parentheses in QMessageBox method calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: QMessageBox.METHOD(self, tr("common.dialog_titles.TYPE"), tr("message")
    # Should be: QMessageBox.METHOD(self, tr("common.dialog_titles.TYPE"), tr("message"))
    # Missing the closing ) for QMessageBox.METHOD

    # Match all QMessageBox methods (warning, information, critical, question)
    # and all dialog title types
    pattern = r'(QMessageBox\.(warning|information|critical|question)\(self, tr\("common\.dialog_titles\.[^"]+"\), tr\("[^"]+"\))'

    # Find all matches to count
    matches = re.findall(pattern, content)
    print(f"Found {len(matches)} QMessageBox method calls to fix")

    # Replace: add closing parenthesis
    def replacer(match):
        return match.group(0) + ')'

    content = re.sub(pattern, replacer, content)

    # Also fix double tr() calls: tr(tr("...")) -> tr("...")
    double_tr_pattern = r'tr\(tr\("([^"]+)"\)\)'
    double_tr_matches = re.findall(double_tr_pattern, content)
    if double_tr_matches:
        print(f"Found {len(double_tr_matches)} double tr() calls to fix")
        content = re.sub(double_tr_pattern, r'tr("\1")', content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    total_fixes = len(matches) + len(double_tr_matches)
    print(f"Fixed {total_fixes} total issues")
    print(f"  - {len(matches)} QMessageBox method calls")
    print(f"  - {len(double_tr_matches)} double tr() calls")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Fixing QMessageBox.warning syntax errors...")
    fix_qmessagebox_syntax()
    print("\nDone!")
