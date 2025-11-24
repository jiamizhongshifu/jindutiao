#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add task management and AI generation i18n keys to translation files
"""

import json

def add_task_management_keys():
    """Add task management translation keys"""

    # Task management keys - Chinese
    task_management_keys_zh = {
        "task_management": {
            # UI Labels
            "ui": {
                "new_task": "新任务",
                "delete_button": "🗑️ 删除",
                "pick_color": "选色",
                "save_all_settings": "保存所有设置",
                "load_tasks": "加载任务",
                "load_config": "加载配置"
            },
            # Messages
            "messages": {
                "time_overlap_warning": "时间重叠警告",
                "time_error": "时间错误",
                "config_and_tasks_loaded": "配置和任务加载完成",
                "load_config_and_tasks_failed": "加载配置和任务失败: {error}",
                "check_time_overlap": "检查任务时间是否重叠",
                "update_color_preview": "更新颜色预览",
                "update_task_color_preview": "更新任务配色预览",
                "refresh_timeline_from_table": "从表格刷新时间轴",
                "autostart_disabled": "(未启用)",
                "autostart_enabled_msg": "自启动设置{status}",
                "enabled": "启用",
                "disabled": "禁用"
            }
        },
        "ai_generation": {
            # UI
            "ui": {
                "smart_generate_tasks": "✨ 智能生成任务",
                "ai_planning": "AI智能规划"
            },
            # Messages
            "messages": {
                "input_empty": "输入为空",
                "please_wait": "请稍候",
                "ai_service_initializing": "AI服务正在初始化",
                "generation_failed": "生成失败",
                "confirm_replace": "确认替换",
                "confirm_replace_msg": "AI已生成 {count} 个任务\n\n是否替换当前表格中的所有任务?",
                "generation_success": "生成成功",
                "error_occurred": "发生错误",
                "ai_generation_failed": "AI生成失败"
            }
        },
        "updates": {
            # UI
            "ui": {
                "auto_update": "自动更新",
                "downloading_update": "正在下载更新...",
                "download_complete": "下载完成"
            },
            # Messages
            "messages": {
                "no_update_notes": "无更新说明",
                "update_failed": "更新失败",
                "download_failed": "下载失败",
                "cancelled": "已取消",
                "download_complete_msg": "新版本已下载完成，是否立即安装并重启应用？\n\n下载位置：{path}",
                "auto_download_and_install": "自动下载并安装更新"
            }
        },
        "settings": {
            # Color
            "color": {
                "select_color": "选择颜色",
                "select_time_marker_image": "选择时间标记图片"
            },
            # Preset
            "preset": {
                "set_preset_height": "设置预设高度",
                "set_preset_marker_size": "设置预设标记大小",
                "any": "任意",
                "no_matching_template": "(无匹配模板)"
            }
        }
    }

    # Task management keys - English
    task_management_keys_en = {
        "task_management": {
            # UI Labels
            "ui": {
                "new_task": "New Task",
                "delete_button": "🗑️ Delete",
                "pick_color": "Pick Color",
                "save_all_settings": "Save All Settings",
                "load_tasks": "Load Tasks",
                "load_config": "Load Config"
            },
            # Messages
            "messages": {
                "time_overlap_warning": "Time Overlap Warning",
                "time_error": "Time Error",
                "config_and_tasks_loaded": "Config and tasks loaded",
                "load_config_and_tasks_failed": "Failed to load config and tasks: {error}",
                "check_time_overlap": "Check task time overlap",
                "update_color_preview": "Update color preview",
                "update_task_color_preview": "Update task color preview",
                "refresh_timeline_from_table": "Refresh timeline from table",
                "autostart_disabled": "(Not enabled)",
                "autostart_enabled_msg": "Autostart {status}",
                "enabled": "enabled",
                "disabled": "disabled"
            }
        },
        "ai_generation": {
            # UI
            "ui": {
                "smart_generate_tasks": "✨ Smart Generate Tasks",
                "ai_planning": "AI Planning"
            },
            # Messages
            "messages": {
                "input_empty": "Input is empty",
                "please_wait": "Please wait",
                "ai_service_initializing": "AI service is initializing",
                "generation_failed": "Generation failed",
                "confirm_replace": "Confirm Replace",
                "confirm_replace_msg": "AI has generated {count} tasks\n\nReplace all current tasks in the table?",
                "generation_success": "Generation successful",
                "error_occurred": "An error occurred",
                "ai_generation_failed": "AI generation failed"
            }
        },
        "updates": {
            # UI
            "ui": {
                "auto_update": "Auto Update",
                "downloading_update": "Downloading update...",
                "download_complete": "Download Complete"
            },
            # Messages
            "messages": {
                "no_update_notes": "No update notes",
                "update_failed": "Update failed",
                "download_failed": "Download failed",
                "cancelled": "Cancelled",
                "download_complete_msg": "New version downloaded. Install and restart now?\n\nDownload location: {path}",
                "auto_download_and_install": "Auto download and install updates"
            }
        },
        "settings": {
            # Color
            "color": {
                "select_color": "Select Color",
                "select_time_marker_image": "Select Time Marker Image"
            },
            # Preset
            "preset": {
                "set_preset_height": "Set Preset Height",
                "set_preset_marker_size": "Set Preset Marker Size",
                "any": "Any",
                "no_matching_template": "(No matching template)"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add task management keys
    zh_cn['task_management'] = task_management_keys_zh['task_management']
    zh_cn['ai_generation'] = task_management_keys_zh['ai_generation']
    zh_cn['updates'] = task_management_keys_zh['updates']
    zh_cn['settings'] = task_management_keys_zh['settings']

    en_us['task_management'] = task_management_keys_en['task_management']
    en_us['ai_generation'] = task_management_keys_en['ai_generation']
    en_us['updates'] = task_management_keys_en['updates']
    en_us['settings'] = task_management_keys_en['settings']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Task management translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_task = count_keys(task_management_keys_zh['task_management'])
    total_ai = count_keys(task_management_keys_zh['ai_generation'])
    total_updates = count_keys(task_management_keys_zh['updates'])
    total_settings = count_keys(task_management_keys_zh['settings'])
    total = total_task + total_ai + total_updates + total_settings

    print(f"  - Task Management: {total_task} keys")
    print(f"  - AI Generation: {total_ai} keys")
    print(f"  - Updates: {total_updates} keys")
    print(f"  - Settings: {total_settings} keys")
    print(f"Total new keys: {total}")

if __name__ == '__main__':
    add_task_management_keys()
