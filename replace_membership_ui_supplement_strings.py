#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace membership UI supplement strings with tr() calls
"""

import re

def replace_membership_ui_supplement_strings():
    """Replace membership UI supplement strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements - only UI contexts
    replacements = [
        # Price units
        (r'QLabel\("/月"\)', 'QLabel(tr("membership.price_units.per_month"))'),
        (r'QLabel\("/年"\)', 'QLabel(tr("membership.price_units.per_year"))'),

        # Labels and badges
        (r'QLabel\("限量1000名"\)', 'QLabel(tr("membership.labels.limited_quota"))'),
        (r'QLabel\("一次付费"\)', 'QLabel(tr("membership.labels.onetime_payment"))'),
        (r'QLabel\("终身可用"\)', 'QLabel(tr("membership.labels.lifetime_access"))'),
        (r'QLabel\("💡 会员提示"\)', 'QLabel(tr("membership.labels.member_tips_title"))'),
        (r'QLabel\("💎 会员方案详细对比"\)', 'QLabel(tr("membership.labels.comparison_title"))'),

        # Buttons
        (r'QPushButton\("我愿意成为会员合伙人"\)', 'QPushButton(tr("membership.buttons.become_partner"))'),
    ]

    # Apply basic replacements
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
    print("Replacing membership UI supplement strings...")
    replace_membership_ui_supplement_strings()
    print("Done!")
