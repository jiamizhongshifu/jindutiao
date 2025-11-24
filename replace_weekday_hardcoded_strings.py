#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace hardcoded weekday strings in schedule dialog with tr() calls
"""

import re

def replace_weekday_strings():
    """Replace hardcoded weekday strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace the hardcoded weekday lists
    # Pattern 1: Line 543-544 (add schedule dialog)
    old_pattern_1 = r'for i, name in \[\(1, "周一"\), \(2, "周二"\), \(3, "周三"\), \(4, "周四"\),\s*\(5, "周五"\), \(6, "周六"\), \(7, "周日"\)\]:'

    new_pattern_1 = '''for i, name in [
                (1, tr("schedule.weekdays.monday")),
                (2, tr("schedule.weekdays.tuesday")),
                (3, tr("schedule.weekdays.wednesday")),
                (4, tr("schedule.weekdays.thursday")),
                (5, tr("schedule.weekdays.friday")),
                (6, tr("schedule.weekdays.saturday")),
                (7, tr("schedule.weekdays.sunday"))
            ]:'''

    # Replace first occurrence (add dialog)
    match1 = re.search(old_pattern_1, content)
    if match1:
        content = content.replace(match1.group(0), new_pattern_1)
        print("Replaced weekday strings in add schedule dialog (Line ~543)")
    else:
        print("WARNING: Could not find first weekday pattern (add dialog)")

    # Pattern 2: Line 807-808 (edit schedule dialog)
    # Find second occurrence
    old_pattern_2 = r'for i, name in \[\(1, "周一"\), \(2, "周二"\), \(3, "周三"\), \(4, "周四"\),\s*\(5, "周五"\), \(6, "周六"\), \(7, "周日"\)\]:'

    match2 = re.search(old_pattern_2, content)
    if match2:
        content = content.replace(match2.group(0), new_pattern_1)
        print("Replaced weekday strings in edit schedule dialog (Line ~807)")
    else:
        print("INFO: Second weekday pattern already replaced or not found")

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nFile updated: {file_path}")
    print("Replaced hardcoded weekday strings with tr() calls")

if __name__ == '__main__':
    print("Replacing hardcoded weekday strings in config_gui.py...")
    replace_weekday_strings()
    print("\nDone!")
