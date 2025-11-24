#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace missed UI strings that weren't caught by the first script
"""

import re

def replace_missed_strings():
    """Replace UI strings that were missed in the first pass"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    modified_count = 0

    # === 1. QGroupBox strings ===
    groupbox_replacements = [
        (r'QGroupBox\("规则类型"\)', 'QGroupBox(tr("templates.auto_apply.rule_type"))'),
    ]

    for pattern, replacement in groupbox_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches
            print(f"  Replaced {matches}x QGroupBox pattern")

    # === 2. Simple message strings (in QMessageBox) ===
    # Pattern: QMessageBox.warning(..., tr("title"), "未翻译的消息")
    simple_msg_patterns = [
        (r'(QMessageBox\.warning\([^,]+,\s*tr\([^)]+\),\s*)"模板管理器未初始化"',
         r'\1tr("templates.messages.manager_not_initialized")'),
    ]

    for pattern, replacement in simple_msg_patterns:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches
            print(f"  Replaced {matches}x simple message pattern")

    # === 3. QLabel with specific complex text ===
    qlabel_patterns = [
        (r'QLabel\("每月的哪些天\?（用逗号分隔，例如: 1,15,28）"\)',
         'QLabel(tr("templates.auto_apply.monthly_days"))'),
    ]

    for pattern, replacement in qlabel_patterns:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches
            print(f"  Replaced {matches}x QLabel pattern")

    # === 4. Error messages with variables (f-strings) ===
    # These need to preserve the variable placeholder
    fstring_error_patterns = [
        # "添加规则失败:\n{str(e)}"
        (r'"添加规则失败:\\n{str\(e\)}"',
         'tr("templates.auto_apply.add_rule_failed", error=str(e))'),
        # "编辑规则失败:\n{str(e)}"
        (r'"编辑规则失败:\\n{str\(e\)}"',
         'tr("templates.auto_apply.edit_rule_failed", error=str(e))'),
        # "删除失败:\n{str(e)}"
        (r'"删除失败:\\n{str\(e\)}"',
         'tr("templates.auto_apply.delete_failed", error=str(e))'),
        # "操作失败:\n{str(e)}"
        (r'"操作失败:\\n{str\(e\)}"',
         'tr("templates.auto_apply.operation_failed", error=str(e))'),
        # "测试失败:\n{str(e)}"
        (r'"测试失败:\\n{str\(e\)}"',
         'tr("templates.auto_apply.test_failed", error=str(e))'),
    ]

    for pattern, replacement in fstring_error_patterns:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches
            print(f"  Replaced {matches}x f-string error pattern")

    # === 5. QMessageBox.question dialogs ===
    question_patterns = [
        (r'(QMessageBox\.question\([^,]+,\s*)"确认删除"(\s*,\s*)"确定要删除这条规则吗\?"',
         r'\1tr("common.dialog_titles.confirm")\2tr("templates.auto_apply.confirm_delete_rule")'),
    ]

    for pattern, replacement in question_patterns:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches
            print(f"  Replaced {matches}x QMessageBox.question pattern")

    # Write back
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print(f"\nTotal additional replacements: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing missed UI strings...")
    replace_missed_strings()
    print("\nDone!")
