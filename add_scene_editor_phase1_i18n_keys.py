#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 scene_editor.py 阶段1（命令和事件系统）的翻译键到 i18n 文件
"""

import json

def add_scene_editor_phase1_keys():
    """添加scene_editor阶段1的翻译键"""

    # 定义所有翻译键（中文和英文）
    scene_editor_keys_zh = {
        "scene_editor": {
            "commands": {
                "add_item": "添加元素",
                "move_item": "移动元素",
                "move_multiple": "移动 {count} 个元素",
                "scale_item": "缩放元素"
            },
            "events": {
                "dialog": {
                    "title": "配置事件",
                    "trigger_group": "触发器",
                    "action_group": "动作",
                    "params_group": "参数"
                },
                "triggers": {
                    "label": "触发类型:",
                    "on_hover": "on_hover - 鼠标悬停",
                    "on_click": "on_click - 鼠标点击",
                    "on_time_reach": "on_time_reach - 时间到达",
                    "on_progress_range": "on_progress_range - 进度范围",
                    "on_task_start": "on_task_start - 任务开始",
                    "on_task_end": "on_task_end - 任务结束"
                },
                "actions": {
                    "label": "动作类型:",
                    "show_tooltip": "show_tooltip - 显示提示",
                    "show_dialog": "show_dialog - 显示对话框",
                    "open_url": "open_url - 打开链接"
                },
                "params": {
                    "text_content": "文本内容:",
                    "url_address": "URL地址:",
                    "url_placeholder": "https://example.com",
                    "time": "时间:",
                    "time_placeholder": "例如: 09:00 或 50%",
                    "start_percent": "起始百分比:",
                    "start_percent_placeholder": "例如: 0 (表示0%)",
                    "end_percent": "结束百分比:",
                    "end_percent_placeholder": "例如: 50 (表示50%)",
                    "task_index": "任务索引:",
                    "task_index_placeholder": "例如: 0 (表示第一个任务)"
                }
            }
        }
    }

    scene_editor_keys_en = {
        "scene_editor": {
            "commands": {
                "add_item": "Add Item",
                "move_item": "Move Item",
                "move_multiple": "Move {count} Items",
                "scale_item": "Scale Item"
            },
            "events": {
                "dialog": {
                    "title": "Configure Event",
                    "trigger_group": "Trigger",
                    "action_group": "Action",
                    "params_group": "Parameters"
                },
                "triggers": {
                    "label": "Trigger Type:",
                    "on_hover": "on_hover - Mouse Hover",
                    "on_click": "on_click - Mouse Click",
                    "on_time_reach": "on_time_reach - Time Reached",
                    "on_progress_range": "on_progress_range - Progress Range",
                    "on_task_start": "on_task_start - Task Start",
                    "on_task_end": "on_task_end - Task End"
                },
                "actions": {
                    "label": "Action Type:",
                    "show_tooltip": "show_tooltip - Show Tooltip",
                    "show_dialog": "show_dialog - Show Dialog",
                    "open_url": "open_url - Open URL"
                },
                "params": {
                    "text_content": "Text Content:",
                    "url_address": "URL Address:",
                    "url_placeholder": "https://example.com",
                    "time": "Time:",
                    "time_placeholder": "e.g.: 09:00 or 50%",
                    "start_percent": "Start Percentage:",
                    "start_percent_placeholder": "e.g.: 0 (means 0%)",
                    "end_percent": "End Percentage:",
                    "end_percent_placeholder": "e.g.: 50 (means 50%)",
                    "task_index": "Task Index:",
                    "task_index_placeholder": "e.g.: 0 (first task)"
                }
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加scene_editor命名空间
    zh_cn['scene_editor'] = scene_editor_keys_zh['scene_editor']
    en_us['scene_editor'] = scene_editor_keys_en['scene_editor']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("阶段1翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计scene_editor命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    key_count = count_keys(scene_editor_keys_zh['scene_editor'])
    print(f"新增 scene_editor 命名空间翻译键: {key_count} 个（阶段1）")

if __name__ == '__main__':
    add_scene_editor_phase1_keys()
