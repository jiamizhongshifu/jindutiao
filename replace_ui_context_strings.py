#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace UI strings in specific contexts only (safer approach)
Only replace strings in explicit UI component calls, not standalone strings
"""

import re

def replace_ui_context_strings():
    """Replace Chinese strings only in known UI contexts"""

    file_path = 'config_gui.py'

    # Read file with explicit encoding
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    modified_count = 0

    # === SAFE CONTEXT-SPECIFIC REPLACEMENTS ===

    # 1. QPushButton with specific Chinese text
    button_replacements = [
        ('取消', 'common.buttons.cancel'),
        ('保存', 'common.buttons.save'),
        ('删除', 'common.buttons.delete'),
        ('确认', 'common.buttons.confirm'),
        ('关闭', 'common.buttons.close'),
        ('刷新', 'common.buttons.refresh'),
        ('选色', 'common.color_picker.title'),
        ('🔍 执行测试', 'common.buttons.test'),
        ('💚 微信支付', 'membership.payment.wechat_pay'),
    ]

    for cn_text, key in button_replacements:
        pattern = re.compile(rf'QPushButton\("{re.escape(cn_text)}"\)')
        matches = len(pattern.findall(content))
        if matches > 0:
            content = pattern.sub(f'QPushButton(tr("{key}"))', content)
            modified_count += matches

    # 2. QMessageBox titles (only replace the title parameter, not the message)
    # Pattern: QMessageBox.xxx(self, "title", -> QMessageBox.xxx(self, tr("key"),
    qmb_title_replacements = [
        ('提示', 'common.dialog_titles.info'),
        ('警告', 'common.dialog_titles.warning'),
        ('错误', 'common.dialog_titles.error'),
        ('成功', 'common.dialog_titles.success'),
        ('确认', 'common.dialog_titles.confirm'),
        ('失败', 'common.dialog_titles.failure'),
        ('创建订单失败', 'membership.payment.create_order_failed'),
    ]

    for cn_text, key in qmb_title_replacements:
        # Match QMessageBox.xxx(self, "title",
        pattern = re.compile(
            rf'(QMessageBox\.(warning|critical|information|question)\(\s*self\s*,\s*)"{re.escape(cn_text)}"(\s*,)'
        )
        matches = len(pattern.findall(content))
        if matches > 0:
            content = pattern.sub(rf'\1tr("{key}")\3', content)
            modified_count += matches

    # 3. setToolTip replacements
    tooltip_replacements = [
        ('编辑', 'common.buttons.edit'),
        ('删除', 'common.buttons.delete'),
    ]

    for cn_text, key in tooltip_replacements:
        pattern = re.compile(rf'setToolTip\("{re.escape(cn_text)}"\)')
        matches = len(pattern.findall(content))
        if matches > 0:
            content = pattern.sub(f'setToolTip(tr("{key}"))', content)
            modified_count += matches

    # 4. Other specific safe patterns
    safe_patterns = [
        # Result.get("error", "xxx")
        (r'\.get\("error",\s*"创建订单失败"\)', '.get("error", tr("membership.payment.create_order_failed"))'),

        # Specific logging/dialog messages in function parameters (not docstrings)
        # Only if preceded by (, [, or =
        (r'(?<=[(\[=,])\s*"支付窗口已打开"', ' tr("membership.payment.payment_window_opened")'),
        (r'(?<=[(\[=,])\s*"创建支付会话失败"', ' tr("membership.payment.create_session_failed")'),
        (r'(?<=[(\[=,])\s*"支付异常"', ' tr("membership.payment.payment_exception")'),
        (r'(?<=[(\[=,])\s*"支付成功"', ' tr("membership.payment.payment_success")'),
    ]

    for pattern, replacement in safe_patterns:
        compiled = re.compile(pattern)
        matches = len(compiled.findall(content))
        if matches > 0:
            content = compiled.sub(replacement, content)
            modified_count += matches

    # Write back
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print(f"\nTotal replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing UI context strings in config_gui.py...")
    replace_ui_context_strings()
    print("\nDone!")
