#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""添加 create_scene_tab() 国际化翻译键"""

import json

# Define new translation keys
new_keys_zh = {
    "scene": {
        "basic_settings_title": "⚙️ 基础设置",
        "scene_selection_title": "🎬 场景选择",
        "advanced_features_title": "🛠️ 高级功能",
        "info_label": "配置场景效果,让进度条更具个性化",
        "current_scene_label": "当前场景:",
        "enable_scene_system": "启用场景系统",
        "show_progress_bar": "依然展示进度条",
        "progress_bar_tooltip": "场景模式下在场景上方叠加显示进度条",
        "refresh_button_tooltip": "重新扫描scenes目录，加载新导出的场景",
        "editor_hint": "场景编辑器可以创建和编辑自定义场景效果",
        "no_scene": "无场景",
        "no_available_scenes": "无可用场景",
        "btn_refresh_scenes": "🔄 刷新场景",
        "btn_open_editor": "🎨 打开场景编辑器",
        "please_select_scene": "请选择一个场景",
        "no_scene_selected": "未选择场景,将显示默认进度条样式",
        "no_description": "无描述",
        "unknown_author": "未知",
        "scene_info_format": "描述: {description}\\n版本: {version}  作者: {author}",
        "cannot_load_info": "无法加载场景信息",
        "manager_not_initialized": "场景管理器未初始化"
    },
    "message": {
        "scene_editor_opened": "场景编辑器已打开",
        "error_open_editor": "打开场景编辑器失败: {e}",
        "scene_editor_closed": "场景编辑器已关闭",
        "scene_list_refreshed": "场景列表已刷新,共 {count} 个场景",
        "error_refresh_scenes": "刷新场景列表失败: {e}",
        "error_open_editor_detail": "打开场景编辑器失败:\\n{e}\\n\\n请检查日志文件获取详细信息",
        "error_refresh_detail": "刷新场景列表时出错:\\n{e}"
    },
    "dialog": {
        "refresh_failed": "刷新失败"
    }
}

new_keys_en = {
    "scene": {
        "basic_settings_title": "⚙️ Basic Settings",
        "scene_selection_title": "🎬 Scene Selection",
        "advanced_features_title": "🛠️ Advanced Features",
        "info_label": "Configure scene effects to personalize your progress bar",
        "current_scene_label": "Current Scene:",
        "enable_scene_system": "Enable Scene System",
        "show_progress_bar": "Still Show Progress Bar",
        "progress_bar_tooltip": "Show progress bar overlay on top of scene in scene mode",
        "refresh_button_tooltip": "Rescan scenes directory and load newly exported scenes",
        "editor_hint": "Scene Editor can create and edit custom scene effects",
        "no_scene": "No Scene",
        "no_available_scenes": "No Available Scenes",
        "btn_refresh_scenes": "🔄 Refresh Scenes",
        "btn_open_editor": "🎨 Open Scene Editor",
        "please_select_scene": "Please select a scene",
        "no_scene_selected": "No scene selected, will display default progress bar style",
        "no_description": "No description",
        "unknown_author": "Unknown",
        "scene_info_format": "Description: {description}\\nVersion: {version}  Author: {author}",
        "cannot_load_info": "Cannot load scene information",
        "manager_not_initialized": "Scene manager not initialized"
    },
    "message": {
        "scene_editor_opened": "Scene editor opened",
        "error_open_editor": "Failed to open scene editor: {e}",
        "scene_editor_closed": "Scene editor closed",
        "scene_list_refreshed": "Scene list refreshed, {count} scene(s) in total",
        "error_refresh_scenes": "Failed to refresh scene list: {e}",
        "error_open_editor_detail": "Failed to open scene editor:\\n{e}\\n\\nPlease check log file for details",
        "error_refresh_detail": "Error refreshing scene list:\\n{e}"
    },
    "dialog": {
        "refresh_failed": "Refresh Failed"
    }
}

def add_keys_to_file(filepath, new_keys):
    """Add new keys to i18n file"""
    # Read existing data
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Add new keys
    keys_added = 0
    for namespace, keys in new_keys.items():
        if namespace not in data:
            data[namespace] = {}

        for key, value in keys.items():
            full_key = f"{namespace}.{key}"
            if key not in data[namespace]:
                data[namespace][key] = value
                keys_added += 1
                print(f"Added: {full_key}")
            else:
                print(f"Skipped (exists): {full_key}")

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return keys_added

# Process both files
print("=== Adding translation keys to zh_CN.json ===")
zh_added = add_keys_to_file('i18n/zh_CN.json', new_keys_zh)

print("\n=== Adding translation keys to en_US.json ===")
en_added = add_keys_to_file('i18n/en_US.json', new_keys_en)

print(f"\n=== Summary ===")
print(f"Chinese keys added: {zh_added}")
print(f"English keys added: {en_added}")
print(f"Total new keys: {zh_added}")
