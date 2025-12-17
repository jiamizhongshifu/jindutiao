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

        # 5. 检查完美日连续成就
        perfect_day_streak = self._get_perfect_day_streak()
        unlocked = self.achievement_manager.check_and_unlock(
            'perfect_day_streak',
            perfect_day_streak
        )
        newly_unlocked.extend(unlocked)

        # 6. 检查单日任务完成数成就
        daily_tasks = self._get_today_completed_tasks()
        unlocked = self.achievement_manager.check_and_unlock(
            'daily_tasks_completed',
            daily_tasks
        )
        newly_unlocked.extend(unlocked)

        # 7. 检查早起鸟儿成就
        early_bird_streak = self._get_early_start_streak()
        unlocked = self.achievement_manager.check_and_unlock(
            'early_start_streak',
            early_bird_streak
        )
        newly_unlocked.extend(unlocked)

        # 8. 检查夜猫子成就
        night_owl_streak = self._get_late_work_streak()
        unlocked = self.achievement_manager.check_and_unlock(
            'late_work_streak',
            night_owl_streak
        )
        newly_unlocked.extend(unlocked)

        # 9. 检查周末战士成就
        weekend_streak = self._get_weekend_usage_streak()
        unlocked = self.achievement_manager.check_and_unlock(
            'weekend_usage_streak',
            weekend_streak
        )
        newly_unlocked.extend(unlocked)

        # 10. 检查新年成就
        if self._check_new_year_usage():
            unlocked = self.achievement_manager.check_and_unlock(
                'new_year_usage',
                1
            )
            newly_unlocked.extend(unlocked)

        # 11. 检查午夜奋斗者成就
        if self._check_midnight_task():
            unlocked = self.achievement_manager.check_and_unlock(
                'midnight_task_completed',
                1
            )
            newly_unlocked.extend(unlocked)

        # 12. 检查周年纪念成就
        total_usage_days = self._get_total_usage_days()
        unlocked = self.achievement_manager.check_and_unlock(
            'usage_anniversary',
            total_usage_days
        )
        newly_unlocked.extend(unlocked)

        # 触发回调
        for achievement in newly_unlocked:
            self.logger.info(f"Achievement unlocked: {achievement.name}")
            if self.on_achievement_unlocked:
                self.on_achievement_unlocked(achievement)

        return newly_unlocked

    def _get_perfect_day_streak(self) -> float:
        """获取连续完美日天数(100%完成率)"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        if not daily_records:
            return 0.0

        today = date.today()
        streak = 0

        while True:
            day_str = today.isoformat()

            if day_str in daily_records:
                summary = daily_records[day_str].get("summary", {})
                completion_rate = summary.get("completion_rate", 0)
                total_tasks = summary.get("total_tasks", 0)

                # 需要有任务且100%完成
                if total_tasks > 0 and completion_rate >= 100:
                    streak += 1
                    today = today - timedelta(days=1)
                else:
                    break
            else:
                break

        return float(streak)

    def _get_early_start_streak(self) -> float:
        """获取连续早起工作天数(9点前有活动)"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        if not daily_records:
            return 0.0

        today = date.today()
        streak = 0

        while True:
            day_str = today.isoformat()

            if day_str in daily_records:
                # 检查是否有9点前的活动
                first_activity_time = daily_records[day_str].get("first_activity_time")
                if first_activity_time:
                    try:
                        activity_hour = int(first_activity_time.split(":")[0])
                        if activity_hour < 9:
                            streak += 1
                            today = today - timedelta(days=1)
                            continue
                    except (ValueError, IndexError):
                        pass
                break
            else:
                break

        return float(streak)

    def _get_late_work_streak(self) -> float:
        """获取连续夜间工作天数(22点后有活动)"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        if not daily_records:
            return 0.0

        today = date.today()
        streak = 0

        while True:
            day_str = today.isoformat()

            if day_str in daily_records:
                # 检查是否有22点后的活动
                last_activity_time = daily_records[day_str].get("last_activity_time")
                if last_activity_time:
                    try:
                        activity_hour = int(last_activity_time.split(":")[0])
                        if activity_hour >= 22:
                            streak += 1
                            today = today - timedelta(days=1)
                            continue
                    except (ValueError, IndexError):
                        pass
                break
            else:
                break

        return float(streak)

    def _get_weekend_usage_streak(self) -> float:
        """获取连续周末使用周数"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})

        if not daily_records:
            return 0.0

        today = date.today()
        streak = 0

        # 找到上一个完整周末
        days_since_sunday = (today.weekday() + 1) % 7
        last_sunday = today - timedelta(days=days_since_sunday)

        while True:
            saturday = last_sunday - timedelta(days=1)
            sunday = last_sunday

            sat_str = saturday.isoformat()
            sun_str = sunday.isoformat()

            # 检查周六或周日是否有使用
            sat_used = sat_str in daily_records and daily_records[sat_str].get("summary", {}).get("completed_tasks", 0) > 0
            sun_used = sun_str in daily_records and daily_records[sun_str].get("summary", {}).get("completed_tasks", 0) > 0

            if sat_used or sun_used:
                streak += 1
                last_sunday = last_sunday - timedelta(days=7)
            else:
                break

        return float(streak)

    def _check_new_year_usage(self) -> bool:
        """检查是否在新年第一天使用"""
        today = date.today()
        if today.month == 1 and today.day == 1:
            daily_records = self.stats_manager.statistics.get("daily_records", {})
            today_str = today.isoformat()
            if today_str in daily_records:
                return True
        return False

    def _check_midnight_task(self) -> bool:
        """检查是否在凌晨0-2点完成过任务"""
        # 这需要更详细的时间戳记录,暂时返回False
        # 未来可以通过检查任务完成时间实现
        return False

    def _get_total_usage_days(self) -> float:
        """获取累计使用天数"""
        daily_records = self.stats_manager.statistics.get("daily_records", {})
        return float(len(daily_records))

    def trigger_first_task_achievement(self) -> List[Achievement]:
        """触发首个任务完成成就"""
        return self.achievement_manager.check_and_unlock('first_task_completed', 1)

    def trigger_first_scene_achievement(self) -> List[Achievement]:
        """触发首个场景创建成就"""
        return self.achievement_manager.check_and_unlock('first_scene_created', 1)

    def trigger_first_ai_task_achievement(self) -> List[Achievement]:
        """触发首次AI任务成就"""
        return self.achievement_manager.check_and_unlock('first_ai_task', 1)

    def increment_stats_view_count(self) -> List[Achievement]:
        """增加统计查看次数并检查成就"""
        # 从成就管理器获取当前进度
        achievement = self.achievement_manager.achievements.get('stats_viewer')
        if achievement and not achievement.unlocked:
            current_count = achievement.progress + 1
            return self.achievement_manager.check_and_unlock('stats_view_count', current_count)
        return []

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
