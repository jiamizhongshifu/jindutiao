"""
任务统计管理器
负责跟踪和统计任务完成情况
"""

import json
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class StatisticsManager:
    """任务统计管理器"""

    def __init__(self, app_dir: Path, logger: logging.Logger):
        """初始化统计管理器

        Args:
            app_dir: 应用程序目录
            logger: 日志记录器
        """
        self.app_dir = app_dir
        self.logger = logger
        self.stats_file = app_dir / 'statistics.json'

        # 统计数据结构
        self.statistics = self.load_statistics()

        # 当前日期
        self.current_date = date.today().isoformat()

        # 确保今天的记录存在
        self._ensure_today_record()

        # 自动清理90天前的旧记录（防止statistics.json无限增长）
        self.cleanup_old_records(days_to_keep=90)

    def load_statistics(self) -> dict:
        """加载统计数据文件

        Returns:
            dict: 统计数据字典
        """
        if not self.stats_file.exists():
            self.logger.info("statistics.json 不存在,创建新文件")
            return {
                "daily_records": {},  # 日期 -> 当日统计
                "task_history": {},   # 任务名 -> 历史记录列表
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            }

        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            self.logger.info("统计数据加载成功")
            return stats
        except json.JSONDecodeError as e:
            self.logger.error(f"统计数据JSON解析错误: {e}")
            return self._create_default_statistics()
        except Exception as e:
            self.logger.error(f"加载统计数据失败: {e}", exc_info=True)
            return self._create_default_statistics()

    def _create_default_statistics(self) -> dict:
        """创建默认统计数据结构"""
        return {
            "daily_records": {},
            "task_history": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        }

    def _ensure_today_record(self):
        """确保今天的记录存在"""
        if self.current_date not in self.statistics["daily_records"]:
            self.statistics["daily_records"][self.current_date] = {
                "date": self.current_date,
                "tasks": {},  # 任务名 -> {start, end, color, status, completed_at}
                "summary": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "not_started_tasks": 0,
                    "total_planned_minutes": 0,
                    "total_completed_minutes": 0,
                    "completion_rate": 0.0
                }
            }
            self._save_statistics()

    def save_statistics(self):
        """保存统计数据到文件"""
        self._save_statistics()

    def _save_statistics(self):
        """内部保存方法"""
        try:
            # 更新最后修改时间
            self.statistics["metadata"]["last_updated"] = datetime.now().isoformat()

            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.statistics, f, indent=4, ensure_ascii=False)
            self.logger.info("统计数据保存成功")
        except Exception as e:
            self.logger.error(f"保存统计数据失败: {e}", exc_info=True)

    def update_task_status(self, task_name: str, task_start: str, task_end: str,
                          task_color: str, status: str):
        """更新任务状态

        Args:
            task_name: 任务名称
            task_start: 开始时间 "HH:MM"
            task_end: 结束时间 "HH:MM"
            task_color: 任务颜色
            status: 状态 "completed", "in_progress", "not_started"
        """
        today = date.today().isoformat()

        # 确保今天的记录存在
        if today != self.current_date:
            self.current_date = today
            self._ensure_today_record()

        daily_record = self.statistics["daily_records"][today]

        # 更新任务记录
        if task_name not in daily_record["tasks"]:
            daily_record["tasks"][task_name] = {
                "start": task_start,
                "end": task_end,
                "color": task_color,
                "status": status,
                "completed_at": None
            }
        else:
            daily_record["tasks"][task_name]["status"] = status

        # 如果任务完成,记录完成时间
        if status == "completed" and daily_record["tasks"][task_name]["completed_at"] is None:
            daily_record["tasks"][task_name]["completed_at"] = datetime.now().isoformat()
            self.logger.info(f"任务已完成: {task_name}")

            # 更新任务历史记录
            self._update_task_history(task_name, task_start, task_end, task_color)

        # 重新计算摘要
        self._recalculate_summary(today)

        # 保存
        self._save_statistics()

    def _update_task_history(self, task_name: str, task_start: str,
                            task_end: str, task_color: str):
        """更新任务历史记录

        Args:
            task_name: 任务名称
            task_start: 开始时间
            task_end: 结束时间
            task_color: 任务颜色
        """
        if task_name not in self.statistics["task_history"]:
            self.statistics["task_history"][task_name] = []

        # 计算任务时长(分钟)
        duration = self._calculate_duration(task_start, task_end)

        # 添加历史记录
        self.statistics["task_history"][task_name].append({
            "date": date.today().isoformat(),
            "start": task_start,
            "end": task_end,
            "color": task_color,
            "duration_minutes": duration,
            "completed_at": datetime.now().isoformat()
        })

    def _calculate_duration(self, start_time: str, end_time: str) -> int:
        """计算时间段的分钟数

        Args:
            start_time: 开始时间 "HH:MM"
            end_time: 结束时间 "HH:MM"

        Returns:
            int: 分钟数
        """
        try:
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')

            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])

            # 处理 24:00 的情况
            if end_time == "24:00":
                end_minutes = 24 * 60
            else:
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

            duration = end_minutes - start_minutes
            return max(0, duration)
        except Exception as e:
            self.logger.error(f"计算时长失败: {e}")
            return 0

    def _recalculate_summary(self, date_str: str):
        """重新计算指定日期的统计摘要

        Args:
            date_str: 日期字符串 "YYYY-MM-DD"
        """
        if date_str not in self.statistics["daily_records"]:
            return

        daily_record = self.statistics["daily_records"][date_str]
        tasks = daily_record["tasks"]

        # 初始化计数器
        total_tasks = len(tasks)
        completed_tasks = 0
        in_progress_tasks = 0
        not_started_tasks = 0
        total_planned_minutes = 0
        total_completed_minutes = 0

        # 统计任务
        for task_name, task_info in tasks.items():
            status = task_info["status"]
            duration = self._calculate_duration(task_info["start"], task_info["end"])
            total_planned_minutes += duration

            if status == "completed":
                completed_tasks += 1
                total_completed_minutes += duration
            elif status == "in_progress":
                in_progress_tasks += 1
            elif status == "not_started":
                not_started_tasks += 1

        # 计算完成率
        completion_rate = (total_completed_minutes / total_planned_minutes * 100) if total_planned_minutes > 0 else 0.0

        # 更新摘要
        daily_record["summary"] = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "not_started_tasks": not_started_tasks,
            "total_planned_minutes": total_planned_minutes,
            "total_completed_minutes": total_completed_minutes,
            "completion_rate": round(completion_rate, 2)
        }

    def get_today_summary(self) -> dict:
        """获取今日统计摘要

        Returns:
            dict: 今日摘要数据
        """
        today = date.today().isoformat()
        self._ensure_today_record()
        return self.statistics["daily_records"][today]["summary"]

    def get_weekly_summary(self) -> dict:
        """获取本周统计摘要

        Returns:
            dict: 本周汇总数据
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # 本周一

        weekly_data = {
            "week_start": week_start.isoformat(),
            "week_end": today.isoformat(),
            "total_tasks": 0,
            "completed_tasks": 0,
            "total_planned_minutes": 0,
            "total_completed_minutes": 0,
            "daily_breakdown": []
        }

        # 遍历本周每一天
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_str = day.isoformat()

            if day_str in self.statistics["daily_records"]:
                daily_summary = self.statistics["daily_records"][day_str]["summary"]
                weekly_data["total_tasks"] += daily_summary["total_tasks"]
                weekly_data["completed_tasks"] += daily_summary["completed_tasks"]
                weekly_data["total_planned_minutes"] += daily_summary["total_planned_minutes"]
                weekly_data["total_completed_minutes"] += daily_summary["total_completed_minutes"]

                weekly_data["daily_breakdown"].append({
                    "date": day_str,
                    "weekday": day.strftime("%A"),
                    "summary": daily_summary
                })

        # 计算本周完成率
        if weekly_data["total_planned_minutes"] > 0:
            weekly_data["completion_rate"] = round(
                weekly_data["total_completed_minutes"] / weekly_data["total_planned_minutes"] * 100,
                2
            )
        else:
            weekly_data["completion_rate"] = 0.0

        return weekly_data

    def get_monthly_summary(self) -> dict:
        """获取本月统计摘要

        Returns:
            dict: 本月汇总数据
        """
        today = date.today()
        month_start = today.replace(day=1)

        monthly_data = {
            "month": today.strftime("%Y-%m"),
            "month_start": month_start.isoformat(),
            "month_end": today.isoformat(),
            "total_tasks": 0,
            "completed_tasks": 0,
            "total_planned_minutes": 0,
            "total_completed_minutes": 0,
            "daily_breakdown": []
        }

        # 遍历本月每一天
        current_day = month_start
        while current_day <= today:
            day_str = current_day.isoformat()

            if day_str in self.statistics["daily_records"]:
                daily_summary = self.statistics["daily_records"][day_str]["summary"]
                monthly_data["total_tasks"] += daily_summary["total_tasks"]
                monthly_data["completed_tasks"] += daily_summary["completed_tasks"]
                monthly_data["total_planned_minutes"] += daily_summary["total_planned_minutes"]
                monthly_data["total_completed_minutes"] += daily_summary["total_completed_minutes"]

                monthly_data["daily_breakdown"].append({
                    "date": day_str,
                    "summary": daily_summary
                })

            current_day += timedelta(days=1)

        # 计算本月完成率
        if monthly_data["total_planned_minutes"] > 0:
            monthly_data["completion_rate"] = round(
                monthly_data["total_completed_minutes"] / monthly_data["total_planned_minutes"] * 100,
                2
            )
        else:
            monthly_data["completion_rate"] = 0.0

        return monthly_data

    def get_task_statistics(self) -> dict:
        """获取任务分类统计

        Returns:
            dict: 任务分类统计数据
        """
        task_stats = {}

        for task_name, history in self.statistics["task_history"].items():
            total_completions = len(history)
            total_minutes = sum(record["duration_minutes"] for record in history)

            # 获取最后一次完成的颜色
            last_color = history[-1]["color"] if history else "#808080"

            task_stats[task_name] = {
                "total_completions": total_completions,
                "total_minutes": total_minutes,
                "total_hours": round(total_minutes / 60, 2),
                "color": last_color,
                "history": history
            }

        return task_stats

    def get_date_range_summary(self, start_date: str, end_date: str) -> dict:
        """获取指定日期范围的统计摘要

        Args:
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            dict: 日期范围汇总数据
        """
        range_data = {
            "start_date": start_date,
            "end_date": end_date,
            "total_tasks": 0,
            "completed_tasks": 0,
            "total_planned_minutes": 0,
            "total_completed_minutes": 0,
            "daily_breakdown": []
        }

        try:
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()

            current_day = start
            while current_day <= end:
                day_str = current_day.isoformat()

                if day_str in self.statistics["daily_records"]:
                    daily_summary = self.statistics["daily_records"][day_str]["summary"]
                    range_data["total_tasks"] += daily_summary["total_tasks"]
                    range_data["completed_tasks"] += daily_summary["completed_tasks"]
                    range_data["total_planned_minutes"] += daily_summary["total_planned_minutes"]
                    range_data["total_completed_minutes"] += daily_summary["total_completed_minutes"]

                    range_data["daily_breakdown"].append({
                        "date": day_str,
                        "summary": daily_summary
                    })

                current_day += timedelta(days=1)

            # 计算完成率
            if range_data["total_planned_minutes"] > 0:
                range_data["completion_rate"] = round(
                    range_data["total_completed_minutes"] / range_data["total_planned_minutes"] * 100,
                    2
                )
            else:
                range_data["completion_rate"] = 0.0

        except Exception as e:
            self.logger.error(f"计算日期范围统计失败: {e}", exc_info=True)

        return range_data

    def cleanup_old_records(self, days_to_keep: int = 90):
        """清理旧的统计记录

        Args:
            days_to_keep: 保留最近多少天的记录(默认90天)
        """
        cutoff_date = (date.today() - timedelta(days=days_to_keep)).isoformat()

        # 清理每日记录
        dates_to_remove = [
            date_str for date_str in self.statistics["daily_records"].keys()
            if date_str < cutoff_date
        ]

        for date_str in dates_to_remove:
            del self.statistics["daily_records"][date_str]

        # 清理任务历史
        for task_name in self.statistics["task_history"].keys():
            self.statistics["task_history"][task_name] = [
                record for record in self.statistics["task_history"][task_name]
                if record["date"] >= cutoff_date
            ]

        # 移除空的任务历史
        empty_tasks = [
            task_name for task_name, history in self.statistics["task_history"].items()
            if not history
        ]
        for task_name in empty_tasks:
            del self.statistics["task_history"][task_name]

        if dates_to_remove or empty_tasks:
            self.logger.info(f"清理了 {len(dates_to_remove)} 天的旧记录和 {len(empty_tasks)} 个空任务")
            self._save_statistics()

    def export_to_csv(self, output_file: Path):
        """导出统计数据为CSV文件

        Args:
            output_file: 输出文件路径
        """
        try:
            import csv

            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # 写入标题
                writer.writerow([
                    '日期', '任务名称', '开始时间', '结束时间',
                    '时长(分钟)', '状态', '完成时间'
                ])

                # 写入数据
                for date_str in sorted(self.statistics["daily_records"].keys()):
                    daily_record = self.statistics["daily_records"][date_str]
                    for task_name, task_info in daily_record["tasks"].items():
                        duration = self._calculate_duration(task_info["start"], task_info["end"])
                        writer.writerow([
                            date_str,
                            task_name,
                            task_info["start"],
                            task_info["end"],
                            duration,
                            task_info["status"],
                            task_info.get("completed_at", "")
                        ])

            self.logger.info(f"统计数据已导出到: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"导出CSV失败: {e}", exc_info=True)
            return False
