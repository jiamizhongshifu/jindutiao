#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 statistics_gui.py 的翻译键到 i18n 文件
"""

import json

def add_statistics_keys():
    """添加statistics_gui的翻译键"""

    # 定义所有翻译键（中文和英文）
    statistics_keys_zh = {
        "statistics": {
            # 窗口和按钮
            "window_title_full": "📊 任务统计报告 - GaiYa每日进度条",
            "window_title": "📊 任务统计报告",
            "btn_refresh": "🔄 刷新",
            "btn_export_csv": "📥 导出CSV",

            "tab": {
                # 标签页标题
                "today": "📅 今日统计",
                "weekly": "📊 本周统计",
                "monthly": "📈 本月统计",
                "category_history": "📋 任务分类统计(历史累计)",
                "category": "📋 任务分类"
            },

            "card": {
                # 统计卡片
                "today_completion": "今日完成率",
                "weekly_completion": "本周完成率",
                "monthly_completion": "本月完成率",
                "total_tasks": "总任务数",
                "completed": "已完成",
                "in_progress": "进行中",
                "not_started": "未开始",
                "completed_duration": "完成时长"
            },

            "table": {
                # 表格列标题
                "today_task_details": "今日任务详情",
                "task_name": "任务名称",
                "start_time": "开始时间",
                "end_time": "结束时间",
                "duration_minutes": "时长(分钟)",
                "status": "状态",
                "daily_completion": "每日完成情况",
                "daily_stats": "每日统计",
                "date": "日期",
                "weekday": "星期",
                "task_count": "任务数",
                "completed_count": "完成数",
                "planned_hours": "计划时长(h)",
                "completion_rate": "完成率(%)",
                "completion_times": "完成次数",
                "total_hours": "总时长(小时)",
                "color": "颜色"
            },

            "status": {
                # 状态文本
                "completed": "✅ 已完成",
                "in_progress": "⏳ 进行中",
                "not_started": "⏰ 未开始"
            },

            "message": {
                # 消息提示
                "loading_start": "开始加载统计数据...",
                "loading_complete": "统计数据加载完成",
                "export_dialog_title": "导出统计数据",
                "csv_file_filter": "CSV文件 (*.csv)",
                "export_success_title": "导出成功",
                "export_success_message": "统计数据已导出到:\n{file_path}"
            },

            "error": {
                # 错误消息
                "error_title": "错误",
                "loading_failed_log": "加载统计数据失败: {e}",
                "loading_failed_message": "加载统计数据失败:\n{error}",
                "export_failed_title": "导出失败",
                "export_failed_simple": "导出统计数据失败,请查看日志了解详情",
                "export_failed_log": "导出统计数据失败: {e}",
                "export_failed_message": "导出失败:\n{error}"
            }
        }
    }

    statistics_keys_en = {
        "statistics": {
            # Window and buttons
            "window_title_full": "📊 Task Statistics Report - GaiYa Daily Progress Bar",
            "window_title": "📊 Task Statistics Report",
            "btn_refresh": "🔄 Refresh",
            "btn_export_csv": "📥 Export CSV",

            "tab": {
                # Tab titles
                "today": "📅 Today's Statistics",
                "weekly": "📊 Weekly Statistics",
                "monthly": "📈 Monthly Statistics",
                "category_history": "📋 Task Category Statistics (Historical)",
                "category": "📋 Task Category"
            },

            "card": {
                # Statistics cards
                "today_completion": "Today's Completion Rate",
                "weekly_completion": "Weekly Completion Rate",
                "monthly_completion": "Monthly Completion Rate",
                "total_tasks": "Total Tasks",
                "completed": "Completed",
                "in_progress": "In Progress",
                "not_started": "Not Started",
                "completed_duration": "Completed Duration"
            },

            "table": {
                # Table column headers
                "today_task_details": "Today's Task Details",
                "task_name": "Task Name",
                "start_time": "Start Time",
                "end_time": "End Time",
                "duration_minutes": "Duration (minutes)",
                "status": "Status",
                "daily_completion": "Daily Completion",
                "daily_stats": "Daily Statistics",
                "date": "Date",
                "weekday": "Weekday",
                "task_count": "Task Count",
                "completed_count": "Completed Count",
                "planned_hours": "Planned Hours (h)",
                "completion_rate": "Completion Rate (%)",
                "completion_times": "Completion Times",
                "total_hours": "Total Hours",
                "color": "Color"
            },

            "status": {
                # Status text
                "completed": "✅ Completed",
                "in_progress": "⏳ In Progress",
                "not_started": "⏰ Not Started"
            },

            "message": {
                # Messages
                "loading_start": "Loading statistics data...",
                "loading_complete": "Statistics data loaded successfully",
                "export_dialog_title": "Export Statistics Data",
                "csv_file_filter": "CSV Files (*.csv)",
                "export_success_title": "Export Successful",
                "export_success_message": "Statistics data exported to:\n{file_path}"
            },

            "error": {
                # Error messages
                "error_title": "Error",
                "loading_failed_log": "Failed to load statistics data: {e}",
                "loading_failed_message": "Failed to load statistics data:\n{error}",
                "export_failed_title": "Export Failed",
                "export_failed_simple": "Failed to export statistics data. Please check the logs for details.",
                "export_failed_log": "Failed to export statistics data: {e}",
                "export_failed_message": "Export failed:\n{error}"
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加statistics命名空间
    zh_cn['statistics'] = statistics_keys_zh['statistics']
    en_us['statistics'] = statistics_keys_en['statistics']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计statistics命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    statistics_key_count = count_keys(statistics_keys_zh['statistics'])
    print(f"新增 statistics 命名空间翻译键: {statistics_key_count} 个")

if __name__ == '__main__':
    add_statistics_keys()
