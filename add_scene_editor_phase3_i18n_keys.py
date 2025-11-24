#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add scene_editor.py Phase 3 (Main Window + Canvas) i18n keys to translation files
"""

import json

def add_scene_editor_phase3_keys():
    """Add scene_editor phase 3 translation keys"""

    # Phase 3 keys - Chinese
    phase3_keys_zh = {
        "main_window": {
            "title": "GaiYa 场景编辑器 v2.0.0",
            "zoom": {
                "label": "缩放:",
                "zoom_out_tooltip": "缩小 (Ctrl+滚轮向下)",
                "zoom_in_tooltip": "放大 (Ctrl+滚轮向上)",
                "fit_btn": "适应窗口",
                "fit_tooltip": "缩放到适合窗口大小并居中",
                "hint": "💡 Ctrl+滚轮缩放 | 空格键拖动视图"
            },
            "progress": {
                "play": "▶ 播放",
                "pause": "⏸ 暂停",
                "reset": "⏮ 重置",
                "label": "进度:",
                "speed_label": "速度:"
            },
            "tabs": {
                "properties": "⚙ 属性编辑",
                "layers": "📚 图层管理"
            },
            "minimap": {
                "title": "🗺️ 小地图"
            },
            "status": {
                "show_grid": "显示网格",
                "snap_grid": "吸附网格",
                "alignment_guides": "对齐辅助线",
                "safe_area_mask": "安全区域蒙版",
                "canvas_width": "画布宽度:",
                "width_1200": "1200px",
                "width_1600": "1600px",
                "width_1800": "1800px (推荐)",
                "width_2400": "2400px"
            },
            "buttons": {
                "import": "📂 导入场景",
                "import_tooltip": "从config.json导入场景进行编辑",
                "export": "💾 导出场景配置",
                "export_tooltip": "导出当前场景为config.json文件"
            },
            "toolbar": {
                "title": "主工具栏",
                "undo": "撤销",
                "redo": "重做",
                "copy": "复制 (Ctrl+C)",
                "paste": "粘贴 (Ctrl+V)",
                "delete": "删除 (Del)",
                "select_all": "全选 (Ctrl+A)"
            }
        },
        "dialogs": {
            "export": {
                "error_no_name_title": "导出失败",
                "error_no_name_msg": "请先设置场景名称！",
                "error_invalid_name_title": "导出失败",
                "error_invalid_name_msg": "场景名称格式不正确！请使用字母、数字、下划线或横线。",
                "exists_title": "场景已存在",
                "exists_msg": "场景 '{scene_name}' 已存在，是否覆盖？\n\n路径: {path}",
                "delete_error_title": "删除失败",
                "delete_error_msg": "无法删除旧场景:\n{error}",
                "create_dir_error_title": "创建目录失败",
                "create_dir_error_msg": "无法创建场景目录:\n{error}",
                "warning_title": "警告",
                "road_missing_msg": "道路层源文件不存在:\n{path}\n\n将跳过道路层导出。",
                "road_copy_error_msg": "道路层复制失败，将继续导出其他内容:\n{error}",
                "save_error_title": "保存失败",
                "save_error_msg": "无法保存配置文件:\n{error}",
                "success_title": "导出成功",
                "success_msg": "场景已成功导出到:\n{path}\n\n包含:\n- config.json\n- {count} 个图片文件\n\n⚠️ 重要提示:\n新导出的场景需要【重启主程序】后才能在场景列表中显示。\n或者在主程序的场景设置中点击【刷新场景】按钮。",
                "open_folder_prompt": "\n\n是否打开文件夹？",
                "open_error_title": "打开失败",
                "open_error_msg": "无法打开文件夹:\n{error}"
            },
            "import": {
                "title": "导入场景配置",
                "filter": "JSON文件 (*.json)",
                "default_name": "未命名场景",
                "template_suffix": "（模板）",
                "success_title": "导入成功",
                "success_msg": "场景配置已导入:\n{name}\n\n包含 {count} 个场景元素",
                "error_title": "导入失败",
                "error_msg": "导入场景配置时出错:\n{error}"
            }
        }
    }

    # Phase 3 keys - English
    phase3_keys_en = {
        "main_window": {
            "title": "GaiYa Scene Editor v2.0.0",
            "zoom": {
                "label": "Zoom:",
                "zoom_out_tooltip": "Zoom Out (Ctrl+Scroll Down)",
                "zoom_in_tooltip": "Zoom In (Ctrl+Scroll Up)",
                "fit_btn": "Fit Window",
                "fit_tooltip": "Zoom to fit window and center",
                "hint": "💡 Ctrl+Scroll to zoom | Space to pan"
            },
            "progress": {
                "play": "▶ Play",
                "pause": "⏸ Pause",
                "reset": "⏮ Reset",
                "label": "Progress:",
                "speed_label": "Speed:"
            },
            "tabs": {
                "properties": "⚙ Properties",
                "layers": "📚 Layers"
            },
            "minimap": {
                "title": "🗺️ Minimap"
            },
            "status": {
                "show_grid": "Show Grid",
                "snap_grid": "Snap to Grid",
                "alignment_guides": "Alignment Guides",
                "safe_area_mask": "Safe Area Mask",
                "canvas_width": "Canvas Width:",
                "width_1200": "1200px",
                "width_1600": "1600px",
                "width_1800": "1800px (Recommended)",
                "width_2400": "2400px"
            },
            "buttons": {
                "import": "📂 Import Scene",
                "import_tooltip": "Import scene from config.json for editing",
                "export": "💾 Export Scene Config",
                "export_tooltip": "Export current scene as config.json file"
            },
            "toolbar": {
                "title": "Main Toolbar",
                "undo": "Undo",
                "redo": "Redo",
                "copy": "Copy (Ctrl+C)",
                "paste": "Paste (Ctrl+V)",
                "delete": "Delete (Del)",
                "select_all": "Select All (Ctrl+A)"
            }
        },
        "dialogs": {
            "export": {
                "error_no_name_title": "Export Failed",
                "error_no_name_msg": "Please set the scene name first!",
                "error_invalid_name_title": "Export Failed",
                "error_invalid_name_msg": "Invalid scene name format! Please use letters, numbers, underscores or hyphens.",
                "exists_title": "Scene Exists",
                "exists_msg": "Scene '{scene_name}' already exists. Overwrite?\n\nPath: {path}",
                "delete_error_title": "Delete Failed",
                "delete_error_msg": "Cannot delete old scene:\n{error}",
                "create_dir_error_title": "Create Directory Failed",
                "create_dir_error_msg": "Cannot create scene directory:\n{error}",
                "warning_title": "Warning",
                "road_missing_msg": "Road layer source file not found:\n{path}\n\nRoad layer export will be skipped.",
                "road_copy_error_msg": "Road layer copy failed, continuing with other content:\n{error}",
                "save_error_title": "Save Failed",
                "save_error_msg": "Cannot save config file:\n{error}",
                "success_title": "Export Successful",
                "success_msg": "Scene exported successfully to:\n{path}\n\nIncludes:\n- config.json\n- {count} image files\n\n⚠️ Important:\nNewly exported scenes require【Restart main program】to appear in scene list.\nOr click【Refresh Scenes】button in main program settings.",
                "open_folder_prompt": "\n\nOpen folder?",
                "open_error_title": "Open Failed",
                "open_error_msg": "Cannot open folder:\n{error}"
            },
            "import": {
                "title": "Import Scene Config",
                "filter": "JSON Files (*.json)",
                "default_name": "Unnamed Scene",
                "template_suffix": " (Template)",
                "success_title": "Import Successful",
                "success_msg": "Scene config imported:\n{name}\n\nContains {count} scene elements",
                "error_title": "Import Failed",
                "error_msg": "Error importing scene config:\n{error}"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Merge phase 3 keys into scene_editor namespace
    zh_cn['scene_editor']['main_window'] = phase3_keys_zh['main_window']
    zh_cn['scene_editor']['dialogs'] = phase3_keys_zh['dialogs']

    en_us['scene_editor']['main_window'] = phase3_keys_en['main_window']
    en_us['scene_editor']['dialogs'] = phase3_keys_en['dialogs']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Phase 3 translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_keys = sum(count_keys(v) for v in phase3_keys_zh.values())
    print(f"New phase 3 translation keys: {total_keys}")

    # Detailed breakdown
    print("  Breakdown:")
    print(f"    - main_window: {count_keys(phase3_keys_zh['main_window'])} keys")
    print(f"    - dialogs: {count_keys(phase3_keys_zh['dialogs'])} keys")

if __name__ == '__main__':
    add_scene_editor_phase3_keys()
