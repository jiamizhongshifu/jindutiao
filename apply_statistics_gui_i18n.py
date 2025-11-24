#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply i18n replacements to statistics_gui.py using regex patterns
Based on successful membership_ui approach
"""

import re

def apply_replacements():
    """Apply all i18n replacements"""

    file_path = 'statistics_gui.py'

    # Read original file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Regex-based replacements (pattern, replacement, description)
    replacements = [
        # Window and buttons
        (r'"📊 任务统计报告 - GaiYa每日进度条"', r'tr("statistics.window_title_full")', 'window title full'),
        (r'"📊 任务统计报告"', r'tr("statistics.window_title")', 'window title'),
        (r'"🔄 刷新"', r'tr("statistics.btn_refresh")', 'refresh button'),
        (r'"📥 导出CSV"', r'tr("statistics.btn_export_csv")', 'export CSV button'),

        # Tab titles
        (r'"📅 今日统计"', r'tr("statistics.tab.today")', 'today tab'),
        (r'"📊 本周统计"', r'tr("statistics.tab.weekly")', 'weekly tab'),
        (r'"📈 本月统计"', r'tr("statistics.tab.monthly")', 'monthly tab'),
        (r'"📋 任务分类统计\(历史累计\)"', r'tr("statistics.tab.category_history")', 'category history tab'),
        (r'"📋 任务分类"', r'tr("statistics.tab.category")', 'category tab'),

        # Card titles
        (r'"今日完成率"', r'tr("statistics.card.today_completion")', 'today completion rate'),
        (r'"本周完成率"', r'tr("statistics.card.weekly_completion")', 'weekly completion rate'),
        (r'"本月完成率"', r'tr("statistics.card.monthly_completion")', 'monthly completion rate'),
        (r'"总任务数"', r'tr("statistics.card.total_tasks")', 'total tasks'),
        (r'"已完成"', r'tr("statistics.card.completed")', 'completed'),
        (r'"进行中"', r'tr("statistics.card.in_progress")', 'in progress'),
        (r'"未开始"', r'tr("statistics.card.not_started")', 'not started'),
        (r'"完成时长"', r'tr("statistics.card.completed_duration")', 'completed duration'),

        # Table headers
        (r'"今日任务详情"', r'tr("statistics.table.today_task_details")', 'today task details'),
        (r'"任务名称"', r'tr("statistics.table.task_name")', 'task name'),
        (r'"开始时间"', r'tr("statistics.table.start_time")', 'start time'),
        (r'"结束时间"', r'tr("statistics.table.end_time")', 'end time'),
        (r'"时长\(分钟\)"', r'tr("statistics.table.duration_minutes")', 'duration minutes'),
        (r'"状态"', r'tr("statistics.table.status")', 'status'),
        (r'"每日完成情况"', r'tr("statistics.table.daily_completion")', 'daily completion'),
        (r'"每日统计"', r'tr("statistics.table.daily_stats")', 'daily stats'),
        (r'"日期"', r'tr("statistics.table.date")', 'date'),
        (r'"星期"', r'tr("statistics.table.weekday")', 'weekday'),
        (r'"任务数"', r'tr("statistics.table.task_count")', 'task count'),
        (r'"完成数"', r'tr("statistics.table.completed_count")', 'completed count'),
        (r'"计划时长\(h\)"', r'tr("statistics.table.planned_hours")', 'planned hours'),
        (r'"完成率\(%\)"', r'tr("statistics.table.completion_rate")', 'completion rate'),
        (r'"完成次数"', r'tr("statistics.table.completion_times")', 'completion times'),
        (r'"总时长\(小时\)"', r'tr("statistics.table.total_hours")', 'total hours'),
        (r'"颜色"', r'tr("statistics.table.color")', 'color'),

        # Status
        (r'"✅ 已完成"', r'tr("statistics.status.completed")', 'status completed'),
        (r'"⏳ 进行中"', r'tr("statistics.status.in_progress")', 'status in progress'),
        (r'"⏰ 未开始"', r'tr("statistics.status.not_started")', 'status not started'),

        # Messages
        (r'"开始加载统计数据\.\.\."', r'tr("statistics.message.loading_start")', 'loading start'),
        (r'"统计数据加载完成"', r'tr("statistics.message.loading_complete")', 'loading complete'),
        (r'"导出统计数据"', r'tr("statistics.message.export_dialog_title")', 'export dialog title'),
        (r'"CSV文件 \(\*\.csv\)"', r'tr("statistics.message.csv_file_filter")', 'csv file filter'),
        (r'"导出成功"', r'tr("statistics.message.export_success_title")', 'export success title'),
        (r'f"统计数据已导出到:\\n\{file_path\}"',
         r'tr("statistics.message.export_success_message", file_path=file_path)', 'export success message'),

        # Errors
        (r'"错误"', r'tr("statistics.error.error_title")', 'error title'),
        (r'f"加载统计数据失败: \{e\}"',
         r'tr("statistics.error.loading_failed_log", e=e)', 'loading failed log'),
        (r'f"加载统计数据失败:\\n\{str\(e\)\}"',
         r'tr("statistics.error.loading_failed_message", error=str(e))', 'loading failed message'),
        (r'"导出失败"', r'tr("statistics.error.export_failed_title")', 'export failed title'),
        (r'"导出统计数据失败,请查看日志了解详情"',
         r'tr("statistics.error.export_failed_simple")', 'export failed simple'),
        (r'f"导出统计数据失败: \{e\}"',
         r'tr("statistics.error.export_failed_log", e=e)', 'export failed log'),
        (r'f"导出失败:\\n\{str\(e\)\}"',
         r'tr("statistics.error.export_failed_message", error=str(e))', 'export failed message'),
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
