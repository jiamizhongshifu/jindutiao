#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add scene_editor.py Phase 2 (UI Panels) i18n keys to translation files
"""

import json

def add_scene_editor_phase2_keys():
    """Add scene_editor phase 2 translation keys"""

    # Phase 2 keys - Chinese
    phase2_keys_zh = {
        "asset_library": {
            "title": "素材库",
            "road_group": "道路层",
            "road_upload": "+ 上传道路图片",
            "road_load": "设为道路",
            "scene_group": "场景层",
            "scene_upload": "+ 上传场景图片",
            "scene_load": "加载到画布",
            "select_road_dialog": "选择道路图片",
            "select_scene_dialog": "选择场景图片",
            "file_filter_png": "PNG图片 (*.png)",
            "warning_title": "提示",
            "warning_select_road": "请先选择一个道路图片",
            "warning_select_scene": "请先选择一个场景图片"
        },
        "property_panel": {
            "title": "属性面板",
            "basic_group": "基本信息",
            "scene_name_placeholder": "例如: 像素森林",
            "scene_name_label": "场景名称:",
            "canvas_height_label": "画布高度:",
            "road_group": "道路层",
            "no_road_selected": "未选择道路图片",
            "file_none": "文件: 无",
            "file_label": "文件: {filename}",
            "x_offset_label": "X偏移:",
            "y_offset_label": "Y偏移:",
            "scale_label": "缩放:",
            "z_index_label": "层级:",
            "select_road_btn": "选择道路图片",
            "clear_road_btn": "清除道路",
            "element_group": "选中元素",
            "no_selection": "未选中",
            "id_label": "ID:",
            "x_position_label": "X位置:",
            "y_position_label": "Y位置:",
            "events_config": "事件配置",
            "add_event_btn": "添加事件",
            "edit_btn": "编辑",
            "delete_btn": "删除",
            "image_load_failed": "图片加载失败",
            "event_display": {
                "triggers": {
                    "on_hover": "悬停",
                    "on_click": "点击",
                    "on_time_reach": "时间到达",
                    "on_progress_range": "进度范围",
                    "on_task_start": "任务开始",
                    "on_task_end": "任务结束"
                },
                "actions": {
                    "show_tooltip": "显示提示",
                    "show_dialog": "显示对话框",
                    "open_url": "打开链接"
                }
            }
        },
        "layer_panel": {
            "title": "图层管理",
            "refresh_tooltip": "刷新图层列表",
            "help_text": "💡 提示: 拖拽调整图层顺序 (上方优先显示)",
            "road_layer_name": "🛣 道路层",
            "toggle_visibility": "切换可见性",
            "toggle_lock": "切换锁定状态"
        }
    }

    # Phase 2 keys - English
    phase2_keys_en = {
        "asset_library": {
            "title": "Asset Library",
            "road_group": "Road Layer",
            "road_upload": "+ Upload Road Image",
            "road_load": "Set as Road",
            "scene_group": "Scene Layer",
            "scene_upload": "+ Upload Scene Image",
            "scene_load": "Add to Canvas",
            "select_road_dialog": "Select Road Image",
            "select_scene_dialog": "Select Scene Image",
            "file_filter_png": "PNG Images (*.png)",
            "warning_title": "Notice",
            "warning_select_road": "Please select a road image first",
            "warning_select_scene": "Please select a scene image first"
        },
        "property_panel": {
            "title": "Property Panel",
            "basic_group": "Basic Info",
            "scene_name_placeholder": "e.g.: Pixel Forest",
            "scene_name_label": "Scene Name:",
            "canvas_height_label": "Canvas Height:",
            "road_group": "Road Layer",
            "no_road_selected": "No road image selected",
            "file_none": "File: None",
            "file_label": "File: {filename}",
            "x_offset_label": "X Offset:",
            "y_offset_label": "Y Offset:",
            "scale_label": "Scale:",
            "z_index_label": "Z-Index:",
            "select_road_btn": "Select Road Image",
            "clear_road_btn": "Clear Road",
            "element_group": "Selected Element",
            "no_selection": "Not Selected",
            "id_label": "ID:",
            "x_position_label": "X Position:",
            "y_position_label": "Y Position:",
            "events_config": "Event Config",
            "add_event_btn": "Add Event",
            "edit_btn": "Edit",
            "delete_btn": "Delete",
            "image_load_failed": "Image load failed",
            "event_display": {
                "triggers": {
                    "on_hover": "Hover",
                    "on_click": "Click",
                    "on_time_reach": "Time Reached",
                    "on_progress_range": "Progress Range",
                    "on_task_start": "Task Start",
                    "on_task_end": "Task End"
                },
                "actions": {
                    "show_tooltip": "Show Tooltip",
                    "show_dialog": "Show Dialog",
                    "open_url": "Open URL"
                }
            }
        },
        "layer_panel": {
            "title": "Layer Manager",
            "refresh_tooltip": "Refresh Layer List",
            "help_text": "💡 Tip: Drag to reorder layers (top = higher priority)",
            "road_layer_name": "🛣 Road Layer",
            "toggle_visibility": "Toggle Visibility",
            "toggle_lock": "Toggle Lock"
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add phase 2 keys to scene_editor namespace
    if 'scene_editor' not in zh_cn:
        zh_cn['scene_editor'] = {}
    if 'scene_editor' not in en_us:
        en_us['scene_editor'] = {}

    # Merge phase 2 keys
    zh_cn['scene_editor']['asset_library'] = phase2_keys_zh['asset_library']
    zh_cn['scene_editor']['property_panel'] = phase2_keys_zh['property_panel']
    zh_cn['scene_editor']['layer_panel'] = phase2_keys_zh['layer_panel']

    en_us['scene_editor']['asset_library'] = phase2_keys_en['asset_library']
    en_us['scene_editor']['property_panel'] = phase2_keys_en['property_panel']
    en_us['scene_editor']['layer_panel'] = phase2_keys_en['layer_panel']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Phase 2 translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_keys = sum(count_keys(v) for v in phase2_keys_zh.values())
    print(f"New phase 2 translation keys: {total_keys}")

    # Detailed breakdown
    for panel, keys in phase2_keys_zh.items():
        panel_count = count_keys(keys)
        print(f"  - {panel}: {panel_count} keys")

if __name__ == '__main__':
    add_scene_editor_phase2_keys()
