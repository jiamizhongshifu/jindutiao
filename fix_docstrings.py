#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix malformed docstrings from batch replacement
"""

import re

def fix_docstrings():
    """Fix docstrings that were incorrectly transformed"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Map of tr() keys to proper English docstrings
    docstring_map = {
        'membership.payment.check_payment_status': 'Check payment status',
        'membership.payment.stop_polling': 'Stop payment status polling',
        'tasks.delete_task': 'Delete task',
        'tasks.clear_all_tasks': 'Clear all tasks',
        'settings.color.select_color': 'Select color',
        'settings.color.select_time_marker_image': 'Select time marker image',
        'updates.messages.auto_download_and_install': 'Auto download and install updates',
    }

    changes_made = 0

    # Fix each malformed docstring
    for key, english_doc in docstring_map.items():
        pattern = f'""tr\\("{key}"\\)""'
        replacement = f'"""{english_doc}"""'
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            changes_made += matches
            print(f"Fixed {matches} occurrences of '{key}'")

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nTotal changes: {changes_made}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Fixing malformed docstrings...")
    fix_docstrings()
    print("\nDone!")
