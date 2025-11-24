#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add common UI i18n keys to translation files
"""

import json

def add_common_ui_keys():
    """Add common UI translation keys"""

    # Common UI keys - Chinese
    common_ui_keys_zh = {
        "common": {
            # Dialog titles
            "dialog_titles": {
                "info": "提示",
                "warning": "警告",
                "error": "错误",
                "success": "成功",
                "confirm": "确认",
                "failure": "失败"
            },
            # Common buttons
            "buttons": {
                "save": "保存",
                "cancel": "取消",
                "delete": "删除",
                "confirm": "确认",
                "close": "关闭",
                "ok": "确定",
                "yes": "是",
                "no": "否",
                "apply": "应用",
                "reset": "重置",
                "refresh": "刷新",
                "load": "加载",
                "execute": "执行",
                "test": "测试"
            },
            # Common messages
            "messages": {
                "save_success": "保存成功",
                "save_failed": "保存失败",
                "load_success": "加载成功",
                "load_failed": "加载失败",
                "delete_success": "删除成功",
                "delete_failed": "删除失败",
                "operation_success": "操作成功",
                "operation_failed": "操作失败",
                "confirm_delete": "确认删除",
                "confirm_delete_msg": "确定要删除 {name} 吗？",
                "confirm_clear": "确认清空",
                "confirm_clear_msg": "确定要清空所有任务吗？",
                "no_data": "暂无数据",
                "loading": "加载中...",
                "processing": "处理中...",
                "please_select": "请先选择",
                "cannot_save": "无法保存"
            },
            # Form labels
            "labels": {
                "name": "名称",
                "description": "描述",
                "type": "类型",
                "status": "状态",
                "date": "日期",
                "time": "时间",
                "color": "颜色",
                "file": "文件"
            },
            # Colors
            "color_picker": {
                "title": "选色",
                "select": "选择颜色"
            }
        },
        "templates": {
            "load_template": "加载模板",
            "save_template": "保存模板",
            "delete_template": "删除模板",
            "select_template": "选择模板",
            "custom_templates": "自定义模板",
            "no_custom_templates": "(暂无自定义模板)",
            "no_templates": "没有自定义模板",
            "template_not_found": "模板不存在",
            "confirm_load": "确认加载模板",
            "confirm_load_msg": "确定要加载模板 {name} 吗？当前任务将被替换。",
            "confirm_delete_msg": "确定要删除模板 {name} 吗？",
            "delete_success_msg": "模板 {name} 已删除",
            "please_create_first": "请先创建自定义模板",
            "template_metadata": "模板元数据",
            "tasks_count": "{count}个任务"
        },
        "tasks": {
            "new_task": "新任务",
            "delete_task": "删除任务",
            "clear_all_tasks": "清空所有任务",
            "confirm_clear_tasks": "确定要清空所有任务吗？"
        }
    }

    # Common UI keys - English
    common_ui_keys_en = {
        "common": {
            # Dialog titles
            "dialog_titles": {
                "info": "Information",
                "warning": "Warning",
                "error": "Error",
                "success": "Success",
                "confirm": "Confirm",
                "failure": "Failure"
            },
            # Common buttons
            "buttons": {
                "save": "Save",
                "cancel": "Cancel",
                "delete": "Delete",
                "confirm": "Confirm",
                "close": "Close",
                "ok": "OK",
                "yes": "Yes",
                "no": "No",
                "apply": "Apply",
                "reset": "Reset",
                "refresh": "Refresh",
                "load": "Load",
                "execute": "Execute",
                "test": "Test"
            },
            # Common messages
            "messages": {
                "save_success": "Saved successfully",
                "save_failed": "Save failed",
                "load_success": "Loaded successfully",
                "load_failed": "Load failed",
                "delete_success": "Deleted successfully",
                "delete_failed": "Delete failed",
                "operation_success": "Operation successful",
                "operation_failed": "Operation failed",
                "confirm_delete": "Confirm Delete",
                "confirm_delete_msg": "Are you sure you want to delete {name}?",
                "confirm_clear": "Confirm Clear",
                "confirm_clear_msg": "Are you sure you want to clear all tasks?",
                "no_data": "No data available",
                "loading": "Loading...",
                "processing": "Processing...",
                "please_select": "Please select first",
                "cannot_save": "Cannot save"
            },
            # Form labels
            "labels": {
                "name": "Name",
                "description": "Description",
                "type": "Type",
                "status": "Status",
                "date": "Date",
                "time": "Time",
                "color": "Color",
                "file": "File"
            },
            # Colors
            "color_picker": {
                "title": "Pick Color",
                "select": "Select Color"
            }
        },
        "templates": {
            "load_template": "Load Template",
            "save_template": "Save Template",
            "delete_template": "Delete Template",
            "select_template": "Select Template",
            "custom_templates": "Custom Templates",
            "no_custom_templates": "(No custom templates)",
            "no_templates": "No custom templates",
            "template_not_found": "Template not found",
            "confirm_load": "Confirm Load Template",
            "confirm_load_msg": "Are you sure you want to load template {name}? Current tasks will be replaced.",
            "confirm_delete_msg": "Are you sure you want to delete template {name}?",
            "delete_success_msg": "Template {name} deleted",
            "please_create_first": "Please create a custom template first",
            "template_metadata": "Template Metadata",
            "tasks_count": "{count} tasks"
        },
        "tasks": {
            "new_task": "New Task",
            "delete_task": "Delete Task",
            "clear_all_tasks": "Clear All Tasks",
            "confirm_clear_tasks": "Are you sure you want to clear all tasks?"
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add common UI keys
    zh_cn['common'] = common_ui_keys_zh['common']
    zh_cn['templates'] = common_ui_keys_zh['templates']
    zh_cn['tasks'] = common_ui_keys_zh['tasks']

    en_us['common'] = common_ui_keys_en['common']
    en_us['templates'] = common_ui_keys_en['templates']
    en_us['tasks'] = common_ui_keys_en['tasks']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Common UI translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_common = count_keys(common_ui_keys_zh['common'])
    total_templates = count_keys(common_ui_keys_zh['templates'])
    total_tasks = count_keys(common_ui_keys_zh['tasks'])
    total = total_common + total_templates + total_tasks

    print(f"  - Common UI: {total_common} keys")
    print(f"  - Templates: {total_templates} keys")
    print(f"  - Tasks: {total_tasks} keys")
    print(f"Total new keys: {total}")

if __name__ == '__main__':
    add_common_ui_keys()
