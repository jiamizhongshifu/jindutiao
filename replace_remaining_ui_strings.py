#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace remaining UI strings in config_gui.py
Focus on dialogs, labels, and user-facing messages
"""

import re

def replace_remaining_ui_strings():
    """Replace remaining UI strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    modified_count = 0

    # === 1. SaveTemplateDialog ===
    template_dialog_replacements = [
        # Window title
        (r'setWindowTitle\("保存为模板"\)', 'setWindowTitle(tr("templates.dialog.save_as_template"))'),

        # Labels
        (r'QLabel\("选择要覆盖的模板或输入新的模板名称:"\)', 'QLabel(tr("templates.dialog.select_or_create"))'),
        (r'QLabel\("请输入模板名称:"\)', 'QLabel(tr("templates.dialog.enter_name"))'),
        (r'QLabel\("💡 提示:\\n"\)', 'QLabel(tr("templates.dialog.hint_title"))'),
        (r'"• 选择历史模板将直接覆盖该模板\\n"', 'tr("templates.dialog.hint_overwrite")'),
        (r'"• 输入新名称将创建新的模板"', 'tr("templates.dialog.hint_create")'),

        # Placeholders
        (r'setPlaceholderText\("选择历史模板或输入新名称"\)', 'setPlaceholderText(tr("templates.dialog.placeholder_select"))'),
        (r'setPlaceholderText\("例如: 工作日模板"\)', 'setPlaceholderText(tr("templates.dialog.placeholder_example"))'),

        # Messages
        (r'QMessageBox\.warning\([^,]+,\s*"输入错误",\s*"模板名称不能为空!"\)',
         'QMessageBox.warning(self, tr("common.dialog_titles.error"), tr("templates.messages.name_empty"))'),
    ]

    for pattern, replacement in template_dialog_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 2. Template Auto-Apply Rules ===
    auto_apply_replacements = [
        # Labels
        (r'QLabel\("选择模板:"\)', 'QLabel(tr("templates.auto_apply.select_template"))'),
        (r'QLabel\("规则类型"\)', 'QLabel(tr("templates.auto_apply.rule_type"))'),
        (r'QLabel\("每月的哪些天\?\（用逗号分隔，例如: 1,15,28\)"\)',
         'QLabel(tr("templates.auto_apply.monthly_days"))'),
        (r'QLabel\("选择具体日期:"\)', 'QLabel(tr("templates.auto_apply.select_dates"))'),

        # Window titles
        (r'setWindowTitle\("测试日期匹配"\)', 'setWindowTitle(tr("templates.auto_apply.test_match"))'),

        # Messages
        (r'"选择一个日期，查看该日期会匹配到哪个模板："',
         'tr("templates.auto_apply.test_instruction")'),
        (r'"该规则与现有规则冲突，请检查"',
         'tr("templates.auto_apply.conflict_warning")'),
        (r'"冲突的模板："', 'tr("templates.auto_apply.conflicting_templates")'),
        (r'"建议：删除或禁用其中某些规则，避免冲突"',
         'tr("templates.auto_apply.conflict_suggestion")'),
        (r'"将使用默认24小时模板"', 'tr("templates.auto_apply.use_default")'),
    ]

    for pattern, replacement in auto_apply_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 3. Tab Labels with Emojis ===
    tab_replacements = [
        (r'addTab\([^,]+,\s*"🎨 外观配置"\)', 'addTab(appearance_tab, tr("tabs.appearance"))'),
        (r'addTab\([^,]+,\s*"📋 任务管理"\)', 'addTab(task_tab, tr("tabs.tasks"))'),
        (r'addTab\([^,]+,\s*"🎬 场景设置"\)', 'addTab(scene_tab, tr("tabs.scenes"))'),
        (r'addTab\([^,]+,\s*"🔔 通知设置"\)', 'addTab(notification_tab, tr("tabs.notifications"))'),
        (r'addTab\([^,]+,\s*"👤 个人中心"\)', 'addTab(profile_tab, tr("tabs.profile"))'),
        (r'addTab\([^,]+,\s*"📖 关于"\)', 'addTab(about_tab, tr("tabs.about"))'),
    ]

    for pattern, replacement in tab_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 4. AI Service Status Messages ===
    ai_status_replacements = [
        (r'"⏳ AI服务正在初始化\.\.\."', 'tr("ai.status.initializing")'),
        (r'"⚠️ AI服务正在启动\.\.\."', 'tr("ai.status.starting")'),
        (r'"❌ AI服务初始化失败"', 'tr("ai.status.init_failed")'),
    ]

    for pattern, replacement in ai_status_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 5. Confirm Delete Dialog ===
    confirm_delete_pattern = r'QMessageBox\.question\([^,]+,\s*"确认删除",\s*"确定要删除这条规则吗\?"\)'
    confirm_delete_replacement = 'QMessageBox.question(self, tr("common.dialog_titles.confirm"), tr("templates.auto_apply.confirm_delete_rule"))'
    matches = len(re.findall(confirm_delete_pattern, content))
    if matches > 0:
        content = re.sub(confirm_delete_pattern, confirm_delete_replacement, content)
        modified_count += matches

    # === 6. f-string Messages (parameterized) ===
    # These need special handling to preserve parameters
    fstring_patterns = [
        (r'f"{template_name} \({task_count}个任务\)"',
         'tr("templates.template_with_count", name=template_name, count=task_count)'),
        (r'f"测试日期: {selected_date\.strftime\(\'%Y-%m-%d %A\'\)}"',
         'tr("templates.auto_apply.test_date", date=selected_date.strftime(\'%Y-%m-%d %A\'))'),
        (r'f"✅ 该日期会自动加载模板: {template_name}"',
         'tr("templates.auto_apply.will_load", template=template_name)'),
        (r'f"⚠️ 警告：该日期有 {len\(all_matched\)} 个模板规则冲突！"',
         'tr("templates.auto_apply.conflict_count", count=len(all_matched))'),
        (r'f"❌ 该日期没有匹配到任何模板规则"',
         'tr("templates.auto_apply.no_match")'),
    ]

    for pattern, replacement in fstring_patterns:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # Write back
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print(f"\nTotal replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing remaining UI strings in config_gui.py...")
    replace_remaining_ui_strings()
    print("\nDone!")
