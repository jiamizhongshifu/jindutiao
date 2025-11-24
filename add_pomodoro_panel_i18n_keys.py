#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 pomodoro_panel.py 的翻译键到 i18n 文件
"""

import json

def add_pomodoro_keys():
    """添加pomodoro_panel的翻译键"""

    # 定义所有翻译键（中文和英文）
    pomodoro_keys_zh = {
        "pomodoro": {
            "settings": {
                # 设置对话框
                "dialog_title": "番茄钟设置",
                "work_duration": "工作时长:",
                "short_break": "短休息时长:",
                "long_break": "长休息时长:",
                "long_break_interval": "长休息间隔:",
                "saved": "番茄钟设置已保存",
                "updated": "番茄钟配置已更新"
            },

            "button": {
                # 按钮文本
                "save": "保存",
                "cancel": "取消"
            },

            "log": {
                # 日志消息
                "panel_created": "番茄钟面板创建成功",
                "panel_positioned": "番茄钟面板定位: x={panel_x}, y={panel_y}",
                "started_work": "番茄钟开始:工作模式",
                "started_short_break": "番茄钟开始:短休息",
                "started_long_break": "番茄钟开始:长休息",
                "resumed": "番茄钟继续",
                "paused": "番茄钟暂停",
                "stopped": "番茄钟停止",
                "settings_opened": "番茄钟设置窗口已打开",
                "completed": "番茄钟完成:第{count}个",
                "config_update_failed": "更新番茄钟配置失败: {e}"
            },

            "notification": {
                # 通知消息
                "completed_title": "🍅 番茄钟完成!",
                "completed_message": "恭喜完成第{count}个番茄钟!\\n休息一下吧~",
                "short_break_text": "短休息",
                "long_break_text": "长休息",
                "break_ended_title": "⏰ 休息时间结束",
                "break_ended_message": "{rest_type}结束啦!准备好开始下一个番茄钟了吗?\\n点击番茄钟面板的开始按钮继续~"
            },

            "error": {
                # 错误消息
                "error_title": "错误",
                "save_failed_log": "保存番茄钟设置失败: {e}",
                "save_failed_message": "保存设置失败:\\n{error}",
                "open_settings_failed_log": "打开番茄钟设置窗口失败: {e}",
                "open_settings_failed_message": "打开设置失败: {error}"
            },

            "unit": {
                # 单位/后缀
                "minutes": "分钟",
                "pomodoro_count": "个番茄钟",
                "panel_title": "番茄钟",
                "or": "或"
            }
        }
    }

    pomodoro_keys_en = {
        "pomodoro": {
            "settings": {
                # Settings dialog
                "dialog_title": "Pomodoro Settings",
                "work_duration": "Work Duration:",
                "short_break": "Short Break:",
                "long_break": "Long Break:",
                "long_break_interval": "Long Break Interval:",
                "saved": "Pomodoro settings saved",
                "updated": "Pomodoro configuration updated"
            },

            "button": {
                # Button text
                "save": "Save",
                "cancel": "Cancel"
            },

            "log": {
                # Log messages
                "panel_created": "Pomodoro panel created successfully",
                "panel_positioned": "Pomodoro panel positioned: x={panel_x}, y={panel_y}",
                "started_work": "Pomodoro started: Work mode",
                "started_short_break": "Pomodoro started: Short break",
                "started_long_break": "Pomodoro started: Long break",
                "resumed": "Pomodoro resumed",
                "paused": "Pomodoro paused",
                "stopped": "Pomodoro stopped",
                "settings_opened": "Pomodoro settings window opened",
                "completed": "Pomodoro completed: #{count}",
                "config_update_failed": "Failed to update pomodoro config: {e}"
            },

            "notification": {
                # Notification messages
                "completed_title": "🍅 Pomodoro Completed!",
                "completed_message": "Congratulations on completing pomodoro #{count}!\\nTake a break~",
                "short_break_text": "Short break",
                "long_break_text": "Long break",
                "break_ended_title": "⏰ Break Time Ended",
                "break_ended_message": "{rest_type} is over! Ready to start the next pomodoro?\\nClick the start button on the pomodoro panel to continue~"
            },

            "error": {
                # Error messages
                "error_title": "Error",
                "save_failed_log": "Failed to save pomodoro settings: {e}",
                "save_failed_message": "Failed to save settings:\\n{error}",
                "open_settings_failed_log": "Failed to open pomodoro settings window: {e}",
                "open_settings_failed_message": "Failed to open settings: {error}"
            },

            "unit": {
                # Units/Suffixes
                "minutes": "minutes",
                "pomodoro_count": "pomodoros",
                "panel_title": "Pomodoro",
                "or": "or"
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加pomodoro命名空间
    zh_cn['pomodoro'] = pomodoro_keys_zh['pomodoro']
    en_us['pomodoro'] = pomodoro_keys_en['pomodoro']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计pomodoro命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    pomodoro_key_count = count_keys(pomodoro_keys_zh['pomodoro'])
    print(f"新增 pomodoro 命名空间翻译键: {pomodoro_key_count} 个")

if __name__ == '__main__':
    add_pomodoro_keys()
