#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace authentication-related strings with tr() calls
"""

import re

def replace_auth_strings():
    """Replace auth strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements - careful with context
    replacements = [
        # Login/Logout messages - standalone strings
        (r'"登录成功"(?!】)', 'tr("auth.login_success")'),
        (r'"退出成功"(?!】)', 'tr("auth.logout_success")'),
        (r'"您的账户信息已更新。"', 'tr("auth.account_updated")'),
        (r'"用户"(?![\u4e00-\u9fff])', 'tr("auth.user")'),  # Not followed by another Chinese character

        # Dialog titles in setWindowTitle or QMessageBox
        (r'"确认退出"(?!】)', 'tr("auth.confirm_logout")'),
        (r'"需要登录"(?!】)', 'tr("auth.login_required")'),

        # The feature name standalone
        (r'"此功能"(?=需要)', 'tr("auth.feature_name")'),
    ]

    # Apply replacements
    modified_count = 0
    for old, new in replacements:
        matches = len(re.findall(old, content))
        if matches > 0:
            content = re.sub(old, new, content)
            modified_count += matches

    # Handle the multi-line logout confirmation message
    # This one needs special handling due to \n
    logout_msg_pattern = r'"确定要退出当前账号吗？\\n\\n退出后将以游客身份继续使用，免费用户功能将受到限制。"'
    if re.search(logout_msg_pattern, content):
        content = re.sub(logout_msg_pattern, 'tr("auth.confirm_logout_msg")', content)
        modified_count += 1

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nTotal replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing authentication strings in config_gui.py...")
    replace_auth_strings()
    print("\nDone!")
