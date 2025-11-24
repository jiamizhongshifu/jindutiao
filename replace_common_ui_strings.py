#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch replace common UI strings in config_gui.py with tr() calls
"""

import re

def replace_common_ui_strings():
    """Replace common UI strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        # Buttons
        (r'QPushButton\("取消"\)', 'QPushButton(tr("common.buttons.cancel"))'),
        (r'QPushButton\("保存"\)', 'QPushButton(tr("common.buttons.save"))'),
        (r'QPushButton\("删除"\)', 'QPushButton(tr("common.buttons.delete"))'),
        (r'QPushButton\("确认"\)', 'QPushButton(tr("common.buttons.confirm"))'),
        (r'QPushButton\("关闭"\)', 'QPushButton(tr("common.buttons.close"))'),
        (r'QPushButton\("刷新"\)', 'QPushButton(tr("common.buttons.refresh"))'),
        (r'QPushButton\("🔍 执行测试"\)', 'QPushButton(tr("common.buttons.test"))'),

        # Dialog titles (in QMessageBox calls)
        (r'"提示",\s*"', 'tr("common.dialog_titles.info"), tr("'),
        (r'"警告",\s*"', 'tr("common.dialog_titles.warning"), tr("'),
        (r'"错误",\s*"', 'tr("common.dialog_titles.error"), tr("'),
        (r'"成功",\s*"', 'tr("common.dialog_titles.success"), tr("'),
        (r'"确认",\s*"', 'tr("common.dialog_titles.confirm"), tr("'),
        (r'"失败",\s*"', 'tr("common.dialog_titles.failure"), tr("'),

        # Common messages
        (r'"保存成功"', 'tr("common.messages.save_success")'),
        (r'"保存失败"', 'tr("common.messages.save_failed")'),
        (r'"加载成功"', 'tr("common.messages.load_success")'),
        (r'"删除成功"', 'tr("common.messages.delete_success")'),
        (r'"删除失败"', 'tr("common.messages.delete_failed")'),
        (r'"确认删除"', 'tr("common.messages.confirm_delete")'),
        (r'"确认清空"', 'tr("common.messages.confirm_clear")'),
        (r'"无法保存"', 'tr("common.messages.cannot_save")'),

        # Color picker
        (r'QPushButton\("选色"\)', 'QPushButton(tr("common.color_picker.title"))'),

        # Templates
        (r'"加载模板"', 'tr("templates.load_template")'),
        (r'"删除模板"', 'tr("templates.delete_template")'),
        (r'"选择模板"', 'tr("templates.select_template")'),
        (r'"\(暂无自定义模板\)"', 'tr("templates.no_custom_templates")'),
        (r'"没有自定义模板"', 'tr("templates.no_templates")'),
        (r'"模板不存在"', 'tr("templates.template_not_found")'),
        (r'"确认加载模板"', 'tr("templates.confirm_load")'),
        (r'"请先创建自定义模板"', 'tr("templates.please_create_first")'),

        # Tasks
        (r'"新任务"', 'tr("tasks.new_task")'),
        (r'"删除任务"', 'tr("tasks.delete_task")'),
        (r'"清空所有任务"', 'tr("tasks.clear_all_tasks")'),

        # Payment-related (expand membership namespace)
        (r'"选择支付方式"', 'tr("membership.payment.select_method")'),
        (r'"请选择支付方式："', 'tr("membership.payment.select_prompt")'),
        (r'"💚 微信支付"', 'tr("membership.payment.wechat_pay")'),
        (r'"确认支付"', 'tr("membership.payment.confirm_payment")'),
        (r'"等待支付"', 'tr("membership.payment.waiting_payment")'),
        (r'"创建订单失败"', 'tr("membership.payment.create_order_failed")'),
        (r'"渠道"', 'tr("membership.payment.channel")'),
        (r'"可能的原因：\\n"', 'tr("membership.payment.possible_reasons")'),
        (r'"建议操作：\\n"', 'tr("membership.payment.suggested_actions")'),
        (r'"调试信息：\\n"', 'tr("membership.payment.debug_info")'),
        (r'"支付窗口已打开"', 'tr("membership.payment.payment_window_opened")'),
        (r'"创建支付会话失败"', 'tr("membership.payment.create_session_failed")'),
        (r'"支付异常"', 'tr("membership.payment.payment_exception")'),
        (r'"检查支付状态"', 'tr("membership.payment.check_payment_status")'),
        (r'"支付成功"', 'tr("membership.payment.payment_success")'),
        (r'"停止支付状态轮询"', 'tr("membership.payment.stop_polling")'),
    ]

    # Apply replacements
    modified_count = 0
    for old, new in replacements:
        matches = len(re.findall(old, content))
        if matches > 0:
            content = re.sub(old, new, content)
            modified_count += matches
            # Skip printing pattern to avoid encoding issues
            pass

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nTotal replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing common UI strings in config_gui.py...")
    replace_common_ui_strings()
    print("\nDone!")
