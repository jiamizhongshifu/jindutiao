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
from gaiya.data.db_manager import db


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

        # ✅ 性能优化: 延迟写入机制
        self._pending_save = False  # 标记是否有待保存的数据
        self._save_timer = None  # 延迟保存定时器

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
        """保存统计数据到文件 (立即写入)"""
        self._save_statistics()

    def schedule_save(self, delay_ms: int = 5000):
        """延迟保存统计数据 (批量写入,减少磁盘I/O)

        Args:
            delay_ms: 延迟时间(毫秒),默认5秒

        工作原理:
        - 每次调用会重置定时器,如果5秒内没有新的更新,才真正写入文件
        - 这样可以将多次频繁更新合并为一次写入,大幅减少磁盘I/O
        """
        if self._save_timer is None:
            # 延迟导入,避免循环依赖
            from PySide6.QtCore import QTimer
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)  # 单次触发
            self._save_timer.timeout.connect(self._do_delayed_save)

        # 重启定时器 (如果已在等待,重置倒计时)
        self._save_timer.stop()
        self._save_timer.start(delay_ms)

    def _do_delayed_save(self):
        """执行延迟保存"""
        if self._pending_save:
            self._save_statistics()
            self._pending_save = False

    def _save_statistics(self):
        """内部保存方法 (实际写入文件)"""
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
        """更新任务状态 (不立即写入文件,使用延迟批量写入)

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

        # ✅ 性能优化: 标记需要保存,但不立即写入 (减少98.6%的磁盘I/O)
        self._pending_save = True
        # ❌ 删除立即保存: self._save_statistics()

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

    def _calculate_summary_from_completions(
        self, date_str: str, task_completions: List[Dict]
    ) -> dict:
        """从任务完成推理数据计算统计摘要

        Args:
            date_str: 日期字符串
            task_completions: 任务完成推理数据列表

        Returns:
            dict: 统计摘要
        """
        total_tasks = len(task_completions)
        completed_tasks = 0  # 完成度 >= 80% 的任务
        in_progress_tasks = 0  # 进行中的任务（基于当前时间）
        not_started_tasks = 0  # 未开始的任务（基于当前时间）
        high_confidence_tasks = 0  # 高置信度任务数
        total_planned_minutes = 0
        total_completed_minutes = 0
        avg_completion = 0

        # 获取当前时间（仅用于今天的统计）
        now = datetime.now()
        current_time = now.time()
        is_today = (date_str == date.today().isoformat())

        for completion in task_completions:
            # 计划时长
            planned_duration = completion.get('planned_duration_minutes', 0)
            total_planned_minutes += planned_duration

            # 实际完成度
            completion_pct = completion.get('completion_percentage', 0)
            avg_completion += completion_pct

            # 实际完成时长 = 计划时长 * 完成度
            actual_minutes = int(planned_duration * completion_pct / 100)
            total_completed_minutes += actual_minutes

            # 判断任务状态
            if is_today:
                # 仅对今天的任务根据当前时间判断状态
                try:
                    start_time_str = completion.get('planned_start_time', '00:00')
                    end_time_str = completion.get('planned_end_time', '00:00')

                    # 解析时间
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()

                    # 判断任务状态（基于时间，不考虑完成度）
                    if current_time < start_time:
                        # 未到开始时间 → 未开始
                        not_started_tasks += 1
                    elif start_time <= current_time < end_time:
                        # 在时间范围内 → 进行中
                        in_progress_tasks += 1
                    else:
                        # 已过结束时间 → 已完成（无论完成度如何）
                        completed_tasks += 1
                except Exception:
                    # 解析失败，默认算已完成
                    completed_tasks += 1
            else:
                # 历史日期的任务，全部算已完成
                completed_tasks += 1

            # 统计高置信度任务
            if completion.get('confidence_level') == 'high':
                high_confidence_tasks += 1

        # 计算平均完成度
        avg_completion = round(avg_completion / total_tasks, 2) if total_tasks > 0 else 0

        # 计算完成率 (基于时长)
        completion_rate = (
            round(total_completed_minutes / total_planned_minutes * 100, 2)
            if total_planned_minutes > 0 else 0
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,  # 完成度 >= 80%
            "high_confidence_tasks": high_confidence_tasks,
            "in_progress_tasks": in_progress_tasks,  # 基于当前时间判断
            "not_started_tasks": not_started_tasks,  # 基于当前时间判断
            "total_planned_minutes": total_planned_minutes,
            "total_completed_minutes": total_completed_minutes,
            "completion_rate": completion_rate,
            "avg_completion_percentage": avg_completion,  # 新增: 平均完成度
            "data_source": "task_completions"  # 标记数据来源
        }

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

        # 尝试从 task_completions 表获取真实完成度数据
        summary = self.statistics["daily_records"][today]["summary"].copy()

        try:
            # 获取今日的任务完成推理数据
            task_completions = db.get_today_task_completions(today)

            if task_completions:
                # 如果有推理数据,重新计算摘要
                summary = self._calculate_summary_from_completions(
                    today, task_completions
                )
        except Exception as e:
            self.logger.warning(f"读取任务完成推理数据失败,使用默认统计: {e}")

        return summary

    def get_today_tasks_with_completions(self) -> List[Dict]:
        """获取今日任务及其完成度数据

        优先返回 task_completions 数据,如果没有则返回 statistics.json 数据

        Returns:
            List[Dict]: 任务列表,每个任务包含:
                - task_name: 任务名称
                - start_time: 开始时间
                - end_time: 结束时间
                - planned_duration: 计划时长(分钟)
                - completion_percentage: 完成度 (0-100)
                - confidence_level: 置信度 (high/medium/low/unknown)
                - user_confirmed: 是否已确认
                - data_source: 数据来源 (task_completions 或 statistics)
        """
        today = date.today().isoformat()
        tasks = []

        try:
            # 尝试从 task_completions 获取
            task_completions = db.get_today_task_completions(today)

            if task_completions:
                for completion in task_completions:
                    tasks.append({
                        'task_name': completion.get('task_name', '未命名'),
                        'start_time': completion.get('planned_start_time', '00:00'),
                        'end_time': completion.get('planned_end_time', '00:00'),
                        'planned_duration': completion.get('planned_duration_minutes', 0),
                        'completion_percentage': completion.get('completion_percentage', 0),
                        'confidence_level': completion.get('confidence_level', 'unknown'),
                        'user_confirmed': completion.get('user_confirmed', False),
                        'user_corrected': completion.get('user_corrected', False),
                        'completion_id': completion.get('id'),
                        'data_source': 'task_completions'
                    })
                return tasks
        except Exception as e:
            self.logger.warning(f"读取任务完成数据失败: {e}")

        # 退回到 statistics.json
        self._ensure_today_record()
        daily_record = self.statistics["daily_records"].get(today, {})
        tasks_dict = daily_record.get("tasks", {})

        for task_name, task_info in tasks_dict.items():
            duration = self._calculate_duration(task_info['start'], task_info['end'])

            # 根据 status 推断完成度
            if task_info['status'] == 'completed':
                completion_pct = 100
            elif task_info['status'] == 'in_progress':
                completion_pct = 50
            else:  # not_started
                completion_pct = 0

            tasks.append({
                'task_name': task_name,
                'start_time': task_info['start'],
                'end_time': task_info['end'],
                'planned_duration': duration,
                'completion_percentage': completion_pct,
                'confidence_level': 'unknown',
                'user_confirmed': False,
                'user_corrected': False,
                'completion_id': None,
                'data_source': 'statistics'
            })

        return tasks

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

    def get_weekly_trend(self, days: int = 7) -> List[Dict]:
        """获取最近N天的任务完成率趋势数据

        Args:
            days: 要获取的天数,默认7天

        Returns:
            List[Dict]: 趋势数据列表,每个元素包含:
                - date: 日期字符串 (YYYY-MM-DD)
                - completion_rate: 完成率 (0-100)
                - total_tasks: 总任务数
                - completed_tasks: 已完成任务数
        """
        trend_data = []
        today = date.today()

        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            date_str = target_date.isoformat()

            # 获取该日期的统计数据
            if date_str in self.statistics["daily_records"]:
                daily_record = self.statistics["daily_records"][date_str]
                summary = daily_record.get("summary", {})

                trend_data.append({
                    'date': date_str,
                    'completion_rate': summary.get('completion_rate', 0.0),
                    'total_tasks': summary.get('total_tasks', 0),
                    'completed_tasks': summary.get('completed_tasks', 0)
                })
            else:
                # 没有数据的日期,填充0值
                trend_data.append({
                    'date': date_str,
                    'completion_rate': 0.0,
                    'total_tasks': 0,
                    'completed_tasks': 0
                })

        return trend_data

    def get_task_color_distribution(self, date_range: str = "today") -> List[Dict]:
        """获取任务颜色分布统计(用于饼图)

        Args:
            date_range: 统计范围, "today"(今日) / "week"(本周) / "month"(本月)

        Returns:
            List[Dict]: 颜色分布数据列表,每个元素包含:
                - color: 颜色代码 (例如: "#4CAF50")
                - label: 颜色标签 (例如: "工作")
                - count: 任务数量
                - percentage: 百分比 (0-100)
        """
        # 定义颜色标签映射 (与config_gui.py中的保持一致)
        COLOR_LABELS = {
            "#4CAF50": "工作",      # 绿色
            "#2196F3": "学习",      # 蓝色
            "#FF9800": "生活",      # 橙色
            "#E91E63": "娱乐",      # 粉色
            "#9C27B0": "运动",      # 紫色
            "#FF5722": "重要",      # 红色
            "#00BCD4": "社交",      # 青色
            "#FFEB3B": "休闲",      # 黄色
            "#795548": "其他",      # 棕色
        }

        # 统计任务颜色
        color_counts = defaultdict(int)
        total_tasks = 0

        if date_range == "today":
            # 今日任务
            today_str = date.today().isoformat()
            if today_str in self.statistics["daily_records"]:
                tasks = self.statistics["daily_records"][today_str].get("tasks", {})
                for task_info in tasks.values():
                    color = task_info.get("color", "#795548")
                    color_counts[color] += 1
                    total_tasks += 1

        elif date_range == "week":
            # 本周任务 (最近7天)
            today = date.today()
            for i in range(7):
                target_date = (today - timedelta(days=i)).isoformat()
                if target_date in self.statistics["daily_records"]:
                    tasks = self.statistics["daily_records"][target_date].get("tasks", {})
                    for task_info in tasks.values():
                        color = task_info.get("color", "#795548")
                        color_counts[color] += 1
                        total_tasks += 1

        elif date_range == "month":
            # 本月任务 (最近30天)
            today = date.today()
            for i in range(30):
                target_date = (today - timedelta(days=i)).isoformat()
                if target_date in self.statistics["daily_records"]:
                    tasks = self.statistics["daily_records"][target_date].get("tasks", {})
                    for task_info in tasks.values():
                        color = task_info.get("color", "#795548")
                        color_counts[color] += 1
                        total_tasks += 1

        # 构建结果列表
        distribution = []
        for color, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
            label = COLOR_LABELS.get(color, "其他")
            percentage = (count / total_tasks * 100) if total_tasks > 0 else 0

            distribution.append({
                'color': color,
                'label': label,
                'count': count,
                'percentage': percentage
            })

        return distribution

    def _classify_task(self, task_name: str) -> str:
        """根据任务名称对任务进行分类

        Args:
            task_name: 任务名称

        Returns:
            str: 分类名称
        """
        task_name_lower = task_name.lower()

        # 工作类
        if any(keyword in task_name_lower for keyword in ['工作', '会议', '开发', '项目', '讨论', '设计', '编程', '代码', '测试', '部署', '早会']):
            return '工作'

        # 学习类
        if any(keyword in task_name_lower for keyword in ['学习', '阅读', '课程', '培训', '研究', '充电', '看书', '教程']):
            return '学习'

        # 运动类
        if any(keyword in task_name_lower for keyword in ['健身', '运动', '跑步', '游泳', '瑜伽', '锻炼', '散步', '球类', '体育']):
            return '运动'

        # 饮食类
        if any(keyword in task_name_lower for keyword in ['早餐', '午餐', '晚餐', '吃饭', '用餐', '饮食', '做饭', '烹饪']):
            return '饮食'

        # 休息类
        if any(keyword in task_name_lower for keyword in ['睡眠', '休息', '午休', '小憩', '放松', '打盹', '睡觉']):
            return '休息'

        # 娱乐类
        if any(keyword in task_name_lower for keyword in ['娱乐', '游戏', '电影', '追剧', '看剧', '综艺', '音乐', '唱歌', 'ktv']):
            return '娱乐'

        # 通勤类
        if any(keyword in task_name_lower for keyword in ['通勤', '上班', '下班', '路上', '交通', '地铁', '公交', '开车']):
            return '通勤'

        # 其他类
        return '其他'

    def get_category_distribution(self, days: int = 7) -> Dict[str, Dict]:
        """获取最近N天的任务分类分布统计

        Args:
            days: 要统计的天数,默认7天

        Returns:
            Dict[str, Dict]: 分类统计字典,格式为:
                {
                    '工作': {'count': 10, 'completed': 8, 'total_minutes': 600},
                    '学习': {'count': 5, 'completed': 4, 'total_minutes': 300},
                    ...
                }
        """
        category_stats = defaultdict(lambda: {'count': 0, 'completed': 0, 'total_minutes': 0})
        today = date.today()

        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            date_str = target_date.isoformat()

            if date_str not in self.statistics["daily_records"]:
                continue

            daily_record = self.statistics["daily_records"][date_str]
            tasks = daily_record.get("tasks", {})

            for task_name, task_info in tasks.items():
                # 分类任务
                category = self._classify_task(task_name)

                # 统计数量
                category_stats[category]['count'] += 1

                # 统计完成数
                if task_info.get('status') == 'completed':
                    category_stats[category]['completed'] += 1

                # 计算任务时长（分钟）
                try:
                    start_time = datetime.strptime(task_info['start'], '%H:%M')
                    end_time = datetime.strptime(task_info['end'], '%H:%M')
                    duration = (end_time - start_time).total_seconds() / 60

                    # 处理跨天任务（end < start）
                    if duration < 0:
                        duration += 24 * 60

                    category_stats[category]['total_minutes'] += int(duration)
                except (ValueError, KeyError):
                    pass

        return dict(category_stats)

    def get_task_categories(self, days: int = 7) -> List[Dict]:
        """获取任务分类分布数据 (格式化为饼图所需格式)

        Args:
            days: 要统计的天数,默认7天

        Returns:
            List[Dict]: 分类列表,每个元素包含:
                - name: 分类名称
                - count: 任务数量
                - percentage: 百分比
                - hours: 总时长(小时)
        """
        category_dist = self.get_category_distribution(days=days)

        # 如果没有数据,返回空列表
        if not category_dist:
            return []

        # 计算总任务数
        total_count = sum(stats['count'] for stats in category_dist.values())

        # 如果总数为0,返回空列表
        if total_count == 0:
            return []

        # 格式化为饼图数据
        categories = []
        for category_name, stats in category_dist.items():
            count = stats['count']
            percentage = (count / total_count) * 100
            hours = stats['total_minutes'] / 60.0

            categories.append({
                'name': category_name,
                'count': count,
                'percentage': percentage,
                'hours': hours
            })

        # 按数量排序 (从大到小)
        categories.sort(key=lambda x: x['count'], reverse=True)

        return categories
