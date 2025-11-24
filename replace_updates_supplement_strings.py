#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace updates system supplement strings with tr() calls
"""

import re

def replace_updates_supplement_strings():
    """Replace updates supplement strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements
    replacements = [
        # Update buttons - context-specific to avoid docstring replacement
        (r'QPushButton\("立即更新"\)', 'QPushButton(tr("updates.buttons.update_now"))'),
        (r'QPushButton\("前往下载"\)', 'QPushButton(tr("updates.buttons.go_to_download"))'),
        (r'QPushButton\("检查更新"\)', 'QPushButton(tr("updates.buttons.check_update"))'),
        # Also replace setText("检查更新")
        (r'\.setText\("检查更新"\)', '.setText(tr("updates.buttons.check_update"))'),

        # Update messages
        (r'"已是最新版本"', 'tr("updates.messages.latest_version")'),
        (r'"检查中\.\.\."', 'tr("updates.messages.checking")'),
        (r'"发现新版本"', 'tr("updates.messages.new_version_found")'),
        (r'"暂无发布版本"', 'tr("updates.messages.no_releases")'),
        (r'"检查更新失败"', 'tr("updates.messages.update_check_failed")'),
        (r'"无法自动更新"', 'tr("updates.messages.cannot_auto_update")'),
        (r'"准备更新"', 'tr("updates.messages.preparing_update")'),
        (r'"安装失败"', 'tr("updates.messages.install_failed")'),
        (r'"更新已取消"', 'tr("updates.messages.update_cancelled")'),

        # Membership tiers (in dictionary)
        (r'"Pro 月度"', 'tr("membership.tiers.pro_monthly")'),
        (r'"Pro 年度"', 'tr("membership.tiers.pro_yearly")'),
        (r'"会员合伙人"', 'tr("membership.tiers.lifetime_partner")'),

        # WeChat
        (r'setWindowTitle\("添加创始人微信"\)', 'setWindowTitle(tr("wechat.add_founder"))'),
        (r'"无法加载二维码图片"', 'tr("wechat.qrcode_load_failed")'),
    ]

    # Apply replacements
    modified_count = 0
    for old, new in replacements:
        matches = len(re.findall(old, content))
        if matches > 0:
            content = re.sub(old, new, content)
            modified_count += matches

    # Special handling for parameterized message
    # "当前版本 v{current_version} 已是最新版本！"
    param_pattern = r'f"当前版本 v\{current_version\} 已是最新版本！"'
    param_replacement = 'tr("updates.messages.latest_version_msg", version=current_version)'
    if re.search(param_pattern, content):
        content = re.sub(param_pattern, param_replacement, content)
        modified_count += 1

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Total replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing updates supplement strings...")
    replace_updates_supplement_strings()
    print("Done!")
