#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace standalone common UI strings with tr() calls
These are individual instances not caught by previous batch replacements
"""

import re

def replace_common_ui_standalone_strings():
    """Replace standalone common UI strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements
    replacements = [
        # Tooltips
        (r'setToolTip\("编辑"\)', 'setToolTip(tr("common.buttons.edit"))'),
        (r'setToolTip\("删除"\)', 'setToolTip(tr("common.buttons.delete"))'),

        # Error dialog titles (QMessageBox.critical/warning)
        (r'QMessageBox\.critical\(self, "错误",', 'QMessageBox.critical(self, tr("common.dialog_titles.error"),'),
        (r'QMessageBox\.warning\(self, "错误",', 'QMessageBox.warning(self, tr("common.dialog_titles.error"),'),

        # QProgressDialog cancel button
        (r'QProgressDialog\(tr\("updates\.ui\.downloading_update"\), "取消",',
         'QProgressDialog(tr("updates.ui.downloading_update"), tr("common.buttons.cancel"),'),
    ]

    # Apply replacements
    modified_count = 0
    for old, new in replacements:
        matches = len(re.findall(old, content))
        if matches > 0:
            content = re.sub(old, new, content)
            modified_count += matches

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Total replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing standalone common UI strings...")
    replace_common_ui_standalone_strings()
    print("Done!")
