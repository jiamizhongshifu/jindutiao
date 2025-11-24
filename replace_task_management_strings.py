#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace task management related strings with tr() calls
"""

import re

def replace_task_management_strings():
    """Replace task management strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements - only UI contexts
    replacements = [
        # Task management UI - buttons and labels
        (r'QPushButton\("🗑️ 删除"\)', 'QPushButton(tr("task_management.ui.delete_button"))'),
        (r'QPushButton\("选色"\)', 'QPushButton(tr("task_management.ui.pick_color"))'),
        (r'QPushButton\("保存所有设置"\)', 'QPushButton(tr("task_management.ui.save_all_settings"))'),

        # AI Generation UI
        (r'QPushButton\("✨ 智能生成任务"\)', 'QPushButton(tr("ai_generation.ui.smart_generate_tasks"))'),
        (r'setWindowTitle\("AI智能规划"\)', 'setWindowTitle(tr("ai_generation.ui.ai_planning"))'),

        # AI Generation messages - DISABLED (standalone strings may be docstrings)
        # (r'"输入为空"', 'tr("ai_generation.messages.input_empty")'),
        # (r'"请稍候"(?!】)', 'tr("ai_generation.messages.please_wait")'),
        # (r'"AI服务正在初始化"', 'tr("ai_generation.messages.ai_service_initializing")'),
        # (r'"生成失败"(?!】)', 'tr("ai_generation.messages.generation_failed")'),
        # (r'"生成成功"(?!】)', 'tr("ai_generation.messages.generation_success")'),
        # (r'"发生错误"(?!】)', 'tr("ai_generation.messages.error_occurred")'),
        # (r'"AI生成失败"', 'tr("ai_generation.messages.ai_generation_failed")'),

        # Updates UI
        (r'setWindowTitle\("自动更新"\)', 'setWindowTitle(tr("updates.ui.auto_update"))'),
        (r'"正在下载更新\.\.\."', 'tr("updates.ui.downloading_update")'),

        # Updates messages - DISABLED (standalone strings may be docstrings)
        # (r'"无更新说明"', 'tr("updates.messages.no_update_notes")'),
        # (r'"更新失败"', 'tr("updates.messages.update_failed")'),
        # (r'"下载失败"', 'tr("updates.messages.download_failed")'),
        # (r'"已取消"', 'tr("updates.messages.cancelled")'),
        # (r'"自动下载并安装更新"', 'tr("updates.messages.auto_download_and_install")'),

        # Settings - Color
        # Only replace in specific UI contexts, not standalone (which is docstring)
        (r'QPushButton\("选择颜色"\)', 'QPushButton(tr("settings.color.select_color"))'),
        (r'QColorDialog\.getColor\(([^,]+),\s*([^,]+),\s*"选择颜色"\)', r'QColorDialog.getColor(\1, \2, tr("settings.color.select_color"))'),
        # Removed: "选择时间标记图片" - it's a docstring
        # (r'"选择时间标记图片"', 'tr("settings.color.select_time_marker_image")'),

        # Settings - Preset - DISABLED (may be docstrings)
        # (r'"任意"(?![\u4e00-\u9fff])', 'tr("settings.preset.any")'),
        # (r'"\(无匹配模板\)"', 'tr("settings.preset.no_matching_template")'),

        # Task messages - DISABLED (may be docstrings)
        # (r'"时间重叠警告"', 'tr("task_management.messages.time_overlap_warning")'),
        # (r'"时间错误"', 'tr("task_management.messages.time_error")'),
        # (r'"\(未启用\)"', 'tr("task_management.messages.autostart_disabled")'),
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

    print(f"\nTotal replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing task management strings in config_gui.py...")
    replace_task_management_strings()
    print("\nDone!")
