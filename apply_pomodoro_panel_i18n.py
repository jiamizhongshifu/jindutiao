#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply i18n replacements to gaiya/ui/pomodoro_panel.py using regex patterns
Based on successful previous approaches
"""

import re

def apply_replacements():
    """Apply all i18n replacements"""

    file_path = 'gaiya/ui/pomodoro_panel.py'

    # Read original file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Regex-based replacements (pattern, replacement, description)
    replacements = [
        # Settings dialog (single quotes)
        (r"'番茄钟设置'", r'tr("pomodoro.settings.dialog_title")', 'dialog title'),
        (r"'工作时长:'", r'tr("pomodoro.settings.work_duration")', 'work duration'),
        (r"'短休息时长:'", r'tr("pomodoro.settings.short_break")', 'short break'),
        (r"'长休息时长:'", r'tr("pomodoro.settings.long_break")', 'long break'),
        (r"'长休息间隔:'", r'tr("pomodoro.settings.long_break_interval")', 'long break interval'),

        # Buttons (single quotes)
        (r"'保存'", r'tr("pomodoro.button.save")', 'save button'),
        (r"'取消'", r'tr("pomodoro.button.cancel")', 'cancel button'),

        # Units (single quotes)
        (r"' 分钟'", r'tr("pomodoro.unit.minutes")', 'minutes suffix'),
        (r"' 个番茄钟'", r'tr("pomodoro.unit.pomodoro_count")', 'pomodoro count suffix'),
        (r"'番茄钟'", r'tr("pomodoro.unit.panel_title")', 'panel title'),
        (r"' 或 '", r'tr("pomodoro.unit.or")', 'or'),

        # Log messages
        (r'"番茄钟面板创建成功"', r'tr("pomodoro.log.panel_created")', 'panel created'),
        (r'f"番茄钟面板定位: x=\\{panel_x\\}, y=\\{panel_y\\}"',
         r'tr("pomodoro.log.panel_positioned", panel_x=panel_x, panel_y=panel_y)', 'panel positioned'),
        (r'"番茄钟开始:工作模式"', r'tr("pomodoro.log.started_work")', 'started work'),
        (r'"番茄钟开始:短休息"', r'tr("pomodoro.log.started_short_break")', 'started short break'),
        (r'"番茄钟开始:长休息"', r'tr("pomodoro.log.started_long_break")', 'started long break'),
        (r'"番茄钟继续"', r'tr("pomodoro.log.resumed")', 'resumed'),
        (r'"番茄钟暂停"', r'tr("pomodoro.log.paused")', 'paused'),
        (r'"番茄钟停止"', r'tr("pomodoro.log.stopped")', 'stopped'),
        (r'"番茄钟设置窗口已打开"', r'tr("pomodoro.log.settings_opened")', 'settings opened'),
        (r'f"番茄钟完成:第\\{self\\.pomodoro_count\\}个"',
         r'tr("pomodoro.log.completed", count=self.pomodoro_count)', 'completed'),
        (r'f"更新番茄钟配置失败: \\{e\\}"',
         r'tr("pomodoro.log.config_update_failed", e=e)', 'config update failed'),

        # Notifications
        (r'"🍅 番茄钟完成!"', r'tr("pomodoro.notification.completed_title")', 'completed notification title'),
        (r'f"恭喜完成第\\{self\\.pomodoro_count\\}个番茄钟!\\\\n休息一下吧~"',
         r'tr("pomodoro.notification.completed_message", count=self.pomodoro_count)', 'completed message'),
        (r'"短休息"', r'tr("pomodoro.notification.short_break_text")', 'short break text'),
        (r'"长休息"', r'tr("pomodoro.notification.long_break_text")', 'long break text'),
        (r'"⏰ 休息时间结束"', r'tr("pomodoro.notification.break_ended_title")', 'break ended title'),
        (r'f"\\{rest_type\\}结束啦!准备好开始下一个番茄钟了吗\\?\\\\n点击番茄钟面板的开始按钮继续~"',
         r'tr("pomodoro.notification.break_ended_message", rest_type=rest_type)', 'break ended message'),

        # Errors
        (r'"错误"', r'tr("pomodoro.error.error_title")', 'error title'),
        (r'f"保存番茄钟设置失败: \\{e\\}"',
         r'tr("pomodoro.error.save_failed_log", e=e)', 'save failed log'),
        (r'f"保存设置失败:\\\\n\\{str\\(e\\)\\}"',
         r'tr("pomodoro.error.save_failed_message", error=str(e))', 'save failed message'),
        (r'f"打开番茄钟设置窗口失败: \\{e\\}"',
         r'tr("pomodoro.error.open_settings_failed_log", e=e)', 'open settings failed log'),
        (r'f"打开设置失败: \\{str\\(e\\)\\}"',
         r'tr("pomodoro.error.open_settings_failed_message", error=str(e))', 'open settings failed message'),
    ]

    # Apply each replacement
    total_replaced = 0
    for pattern, replacement, description in replacements:
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            total_replaced += count
            print(f"[OK] Replaced: {description} ({count} occurrence(s))")
        else:
            print(f"[SKIP] Not found: {description}")

    # Check if content changed
    if content == original_content:
        print("\n[WARNING] No changes made to file!")
        return

    # Write modified content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n[SUCCESS] Total replacements: {total_replaced}")
    print(f"Modified file: {file_path}")

if __name__ == '__main__':
    apply_replacements()
