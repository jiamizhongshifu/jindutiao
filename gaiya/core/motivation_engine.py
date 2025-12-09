"""
Motivation Engine - 激励循环引擎

自动化激励系统的核心引擎:
1. 监听统计数据变化
2. 自动更新目标进度
3. 自动检测成就解锁
4. 触发通知和庆祝动画

Author: GaiYa Team
Date: 2025-12-09
Version: 1.0
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import date, datetime, timedelta
from pathlib import Path

from gaiya.core.goal_manager import GoalManager, Goal
from gaiya.core.achievement_manager import AchievementManager, Achievement


class MotivationEngine:
    """
    激励循环引擎

    负责协调目标管理和成就系统,实现自动化激励循环:
    - 根据统计数据自动更新目标进度
    - 检测成就解锁条件
    - 触发UI通知和动画
    """

    def __init__(
        self,
        goal_manager: GoalManager,
        achievement_manager: AchievementManager,
        stats_manager,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化激励引擎

        Args:
            goal_manager: 目标管理器
            achievement_manager: 成就管理器
            stats_manager: 统计管理器
            logger: 日志记录器
        """
        self.goal_manager = goal_manager
        self.achievement_manager = achievement_manager
        self.stats_manager = stats_manager
        self.logger = logger or logging.getLogger(__name__)

        # 回调函数: 当有目标完成时触发
        self.on_goal_completed: Optional[Callable[[Goal], None]] = None

        # 回调函数: 当有成就解锁时触发
        self.on_achievement_unlocked: Optional[Callable[[Achievement], None]] = None

        self.logger.info("Motivation Engine initialized")

    def update_goals_from_stats(self) -> List[Goal]:
        """
        根据统计数据更新所有活跃目标的进度

        Returns:
            List[Goal]: 刚刚完成的目标列表
        """
        newly_completed_goals = []

        # 获取所有活跃目标
        active_goals = self.goal_manager.get_active_goals()

        if not active_goals:
            return newly_completed_goals

        self.logger.info(f"Updating {len(active_goals)} active goals...")

        for goal in active_goals:
            # 根据目标类型计算当前值
            current_value = self._calculate_goal_current_value(goal)

            # 更新目标进度
            just_completed = self.goal_manager.update_goal_progress(
                goal.goal_id,
                current_value
            )

            if just_completed:
                newly_completed_goals.append(goal)
                self.logger.info(f"🎉 Goal completed: {goal.goal_type}")

                # 触发回调
                if self.on_goal_completed:
                    self.on_goal_completed(goal)

        return newly_completed_goals

    def _calculate_goal_current_value(self, goal: Goal) -> float:
        """
        根据目标类型计算当前进度值

        Args:
            goal: 目标对象

        Returns:
            float: 当前进度值
        """
        goal_type = goal.goal_type

        if goal_type == 'daily_tasks':
            # 每日任务目标: 今日完成的任务数
            return self._get_today_completed_tasks()

        elif goal_type == 'weekly_focus_hours':
            # 每周专注时长: 本周累计专注小时数
            return self._get_weekly_focus_hours()

        elif goal_type == 'weekly_completion_rate':
            # 每周完成率: 本周平均任务完成率
            return self._get_weekly_completion_rate()

        else:
            self.logger.warning(f"Unknown goal type: {goal_type}")
            return 0.0

    def _get_today_completed_tasks(self) -> float:
        """获取今日完成的任务数"""
        today = date.today().isoformat()
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        if today not in daily_records:
            return 0.0

        summary = daily_records[today].get("summary", {})
        return float(summary.get("completed_tasks", 0))

    def _get_weekly_focus_hours(self) -> float:
        """获取本周累计专注时长(小时)"""
        # 计算本周日期范围
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # 周一

        total_minutes = 0.0
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        # 遍历本周的每一天
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            day_str = day.isoformat()

            if day_str in daily_records:
                summary = daily_records[day_str].get("summary", {})
                total_minutes += summary.get("total_completed_minutes", 0)

        # 转换为小时
        return total_minutes / 60.0

    def _get_weekly_completion_rate(self) -> float:
        """获取本周平均任务完成率(%)"""
        # 计算本周日期范围
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        total_rate = 0.0
        days_with_data = 0
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        # 遍历本周的每一天
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            day_str = day.isoformat()

            if day_str in daily_records:
                summary = daily_records[day_str].get("summary", {})
                rate = summary.get("completion_rate", 0)
                if rate > 0:  # 只统计有数据的天数
                    total_rate += rate
                    days_with_data += 1

        # 计算平均值
        if days_with_data == 0:
            return 0.0

        return total_rate / days_with_data

    def check_achievements(self) -> List[Achievement]:
        """
        检查所有成就解锁条件

        Returns:
            List[Achievement]: 新解锁的成就列表
        """
        newly_unlocked = []

        self.logger.info("Checking achievement unlock conditions...")

        # 1. 检查连续打卡成就
        continuous_days = self._get_continuous_usage_days()
        unlocked = self.achievement_manager.check_and_unlock(
            'continuous_days',
            continuous_days
        )
        newly_unlocked.extend(unlocked)

        # 2. 检查累计任务完成成就
        total_tasks = self._get_total_completed_tasks()
        unlocked = self.achievement_manager.check_and_unlock(
            'total_tasks_completed',
            total_tasks
        )
        newly_unlocked.extend(unlocked)

        # 3. 检查累计专注时长成就
        total_focus_hours = self._get_total_focus_hours()
        unlocked = self.achievement_manager.check_and_unlock(
            'total_focus_hours',
            total_focus_hours
        )
        newly_unlocked.extend(unlocked)

        # 4. 检查每日完成率成就
        daily_rate = self._get_today_completion_rate()
        unlocked = self.achievement_manager.check_and_unlock(
            'daily_completion_rate',
            daily_rate
        )
        newly_unlocked.extend(unlocked)

        # 5. 检查每周完成率成就
        weekly_rate = self._get_weekly_completion_rate()
        unlocked = self.achievement_manager.check_and_unlock(
            'weekly_completion_rate',
            weekly_rate
        )
        newly_unlocked.extend(unlocked)

        # 触发回调
        for achievement in newly_unlocked:
            self.logger.info(f"🏆 Achievement unlocked: {achievement.name}")
            if self.on_achievement_unlocked:
                self.on_achievement_unlocked(achievement)

        return newly_unlocked

    def _get_continuous_usage_days(self) -> float:
        """计算连续使用天数"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        if not daily_records:
            return 0.0

        # 从今天开始往前计算连续天数
        today = date.today()
        continuous_days = 0

        while True:
            day_str = today.isoformat()

            # 检查这一天是否有记录且有完成任务
            if day_str in daily_records:
                summary = daily_records[day_str].get("summary", {})
                completed = summary.get("completed_tasks", 0)

                if completed > 0:
                    continuous_days += 1
                    today = today - timedelta(days=1)
                else:
                    break  # 中断连续
            else:
                break  # 没有记录,中断连续

        return float(continuous_days)

    def _get_total_completed_tasks(self) -> float:
        """获取累计完成的任务总数"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        total = 0
        for day_data in daily_records.values():
            summary = day_data.get("summary", {})
            total += summary.get("completed_tasks", 0)

        return float(total)

    def _get_total_focus_hours(self) -> float:
        """获取累计专注时长(小时)"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        total_minutes = 0
        for day_data in daily_records.values():
            summary = day_data.get("summary", {})
            total_minutes += summary.get("total_completed_minutes", 0)

        return total_minutes / 60.0

    def _get_today_completion_rate(self) -> float:
        """获取今日任务完成率(%)"""
        today = date.today().isoformat()
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        if today not in daily_records:
            return 0.0

        summary = daily_records[today].get("summary", {})
        return summary.get("completion_rate", 0.0)

    def update_all(self) -> Dict[str, List]:
        """
        执行完整的激励系统更新

        检查目标进度和成就解锁,返回所有变化

        Returns:
            Dict: {
                'completed_goals': List[Goal],
                'unlocked_achievements': List[Achievement]
            }
        """
        self.logger.info("Running full motivation system update...")

        # 更新目标进度
        completed_goals = self.update_goals_from_stats()

        # 检查成就解锁
        unlocked_achievements = self.check_achievements()

        result = {
            'completed_goals': completed_goals,
            'unlocked_achievements': unlocked_achievements
        }

        self.logger.info(
            f"Update complete: {len(completed_goals)} goals completed, "
            f"{len(unlocked_achievements)} achievements unlocked"
        )

        return result
