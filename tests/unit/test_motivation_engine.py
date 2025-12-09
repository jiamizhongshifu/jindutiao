"""
Motivation Engine 单元测试
测试激励循环引擎核心功能
"""
import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
from gaiya.core.motivation_engine import MotivationEngine
from gaiya.core.goal_manager import Goal
from gaiya.core.achievement_manager import Achievement


@pytest.fixture
def mock_logger():
    """创建Mock Logger"""
    return Mock()


@pytest.fixture
def mock_goal_manager():
    """创建Mock GoalManager"""
    manager = Mock()
    manager.get_active_goals = Mock(return_value=[])
    manager.update_goal_progress = Mock(return_value=False)
    return manager


@pytest.fixture
def mock_achievement_manager():
    """创建Mock AchievementManager"""
    manager = Mock()
    manager.check_and_unlock = Mock(return_value=[])
    return manager


@pytest.fixture
def mock_stats_manager():
    """创建Mock StatisticsManager"""
    manager = Mock()
    manager.statistics = {
        "daily_records": {}
    }
    return manager


@pytest.fixture
def motivation_engine(mock_goal_manager, mock_achievement_manager, mock_stats_manager, mock_logger):
    """创建MotivationEngine实例"""
    return MotivationEngine(
        goal_manager=mock_goal_manager,
        achievement_manager=mock_achievement_manager,
        stats_manager=mock_stats_manager,
        logger=mock_logger
    )


class TestMotivationEngineInit:
    """测试MotivationEngine初始化"""

    def test_initialization(self, motivation_engine):
        """测试初始化"""
        assert motivation_engine.goal_manager is not None
        assert motivation_engine.achievement_manager is not None
        assert motivation_engine.stats_manager is not None
        assert motivation_engine.on_goal_completed is None
        assert motivation_engine.on_achievement_unlocked is None


class TestGoalProgressUpdate:
    """测试目标进度更新"""

    def test_update_goals_no_active_goals(self, motivation_engine, mock_goal_manager):
        """测试没有活跃目标"""
        mock_goal_manager.get_active_goals.return_value = []

        completed_goals = motivation_engine.update_goals_from_stats()

        assert len(completed_goals) == 0

    def test_update_goals_with_active_goals(self, motivation_engine, mock_goal_manager, mock_stats_manager):
        """测试更新活跃目标"""
        # 创建测试目标
        goal = Mock()
        goal.goal_id = "test-goal-1"
        goal.goal_type = "daily_tasks"
        goal.target_value = 5.0

        mock_goal_manager.get_active_goals.return_value = [goal]
        mock_goal_manager.update_goal_progress.return_value = False

        # 设置统计数据
        today = date.today().isoformat()
        mock_stats_manager.statistics = {
            "daily_records": {
                today: {
                    "summary": {
                        "completed_tasks": 3
                    }
                }
            }
        }

        completed_goals = motivation_engine.update_goals_from_stats()

        # 验证调用
        mock_goal_manager.update_goal_progress.assert_called_once_with("test-goal-1", 3.0)
        assert len(completed_goals) == 0

    def test_update_goals_goal_just_completed(self, motivation_engine, mock_goal_manager, mock_stats_manager):
        """测试目标刚完成"""
        goal = Mock()
        goal.goal_id = "test-goal-1"
        goal.goal_type = "daily_tasks"

        mock_goal_manager.get_active_goals.return_value = [goal]
        mock_goal_manager.update_goal_progress.return_value = True  # 刚完成

        # 设置统计数据
        today = date.today().isoformat()
        mock_stats_manager.statistics = {
            "daily_records": {
                today: {
                    "summary": {
                        "completed_tasks": 5
                    }
                }
            }
        }

        completed_goals = motivation_engine.update_goals_from_stats()

        assert len(completed_goals) == 1
        assert completed_goals[0] == goal

    def test_goal_completed_callback(self, motivation_engine, mock_goal_manager, mock_stats_manager):
        """测试目标完成回调"""
        goal = Mock()
        goal.goal_id = "test-goal-1"
        goal.goal_type = "daily_tasks"

        mock_goal_manager.get_active_goals.return_value = [goal]
        mock_goal_manager.update_goal_progress.return_value = True

        # 设置回调
        callback_mock = Mock()
        motivation_engine.on_goal_completed = callback_mock

        # 设置统计数据
        today = date.today().isoformat()
        mock_stats_manager.statistics = {
            "daily_records": {
                today: {
                    "summary": {
                        "completed_tasks": 5
                    }
                }
            }
        }

        motivation_engine.update_goals_from_stats()

        # 验证回调被调用
        callback_mock.assert_called_once_with(goal)


class TestGoalValueCalculation:
    """测试目标值计算"""

    def test_calculate_daily_tasks(self, motivation_engine, mock_stats_manager):
        """测试计算每日任务"""
        today = date.today().isoformat()
        mock_stats_manager.statistics = {
            "daily_records": {
                today: {
                    "summary": {
                        "completed_tasks": 7
                    }
                }
            }
        }

        value = motivation_engine._get_today_completed_tasks()
        assert value == 7.0

    def test_calculate_daily_tasks_no_data(self, motivation_engine, mock_stats_manager):
        """测试计算每日任务(无数据)"""
        mock_stats_manager.statistics = {"daily_records": {}}

        value = motivation_engine._get_today_completed_tasks()
        assert value == 0.0

    def test_calculate_weekly_focus_hours(self, motivation_engine, mock_stats_manager):
        """测试计算每周专注时长"""
        # 构造本周数据
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        daily_records = {}
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            daily_records[day.isoformat()] = {
                "summary": {
                    "total_completed_minutes": 120  # 每天2小时
                }
            }

        mock_stats_manager.statistics = {"daily_records": daily_records}

        hours = motivation_engine._get_weekly_focus_hours()
        assert hours == 14.0  # 7天 * 2小时

    def test_calculate_weekly_completion_rate(self, motivation_engine, mock_stats_manager):
        """测试计算每周完成率"""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        daily_records = {}
        # 只有前5天有数据
        for i in range(5):
            day = start_of_week + timedelta(days=i)
            daily_records[day.isoformat()] = {
                "summary": {
                    "completion_rate": 80.0
                }
            }

        mock_stats_manager.statistics = {"daily_records": daily_records}

        rate = motivation_engine._get_weekly_completion_rate()
        assert rate == 80.0  # 平均值


class TestAchievementChecking:
    """测试成就检查"""

    def test_check_achievements_none_unlocked(self, motivation_engine, mock_achievement_manager):
        """测试检查成就(无解锁)"""
        mock_achievement_manager.check_and_unlock.return_value = []

        newly_unlocked = motivation_engine.check_achievements()

        assert len(newly_unlocked) == 0
        # 验证所有成就类型都被检查了
        assert mock_achievement_manager.check_and_unlock.call_count == 5

    def test_check_achievements_some_unlocked(self, motivation_engine, mock_achievement_manager, mock_stats_manager):
        """测试检查成就(有解锁)"""
        # 模拟解锁一个成就
        achievement = Mock()
        achievement.name = "测试成就"
        achievement.achievement_id = "test-achievement"

        mock_achievement_manager.check_and_unlock.side_effect = [
            [achievement],  # continuous_days 解锁1个
            [],  # total_tasks_completed
            [],  # total_focus_hours
            [],  # daily_completion_rate
            []   # weekly_completion_rate
        ]

        # 设置统计数据
        today = date.today()
        mock_stats_manager.statistics = {
            "daily_records": {
                today.isoformat(): {
                    "summary": {
                        "completed_tasks": 5
                    }
                },
                (today - timedelta(days=1)).isoformat(): {
                    "summary": {
                        "completed_tasks": 3
                    }
                },
                (today - timedelta(days=2)).isoformat(): {
                    "summary": {
                        "completed_tasks": 2
                    }
                }
            }
        }

        newly_unlocked = motivation_engine.check_achievements()

        assert len(newly_unlocked) == 1
        assert newly_unlocked[0] == achievement

    def test_achievement_unlocked_callback(self, motivation_engine, mock_achievement_manager):
        """测试成就解锁回调"""
        achievement = Mock()
        achievement.name = "测试成就"

        # check_achievements 会调用5次 check_and_unlock,只有第一次返回成就
        mock_achievement_manager.check_and_unlock.side_effect = [
            [achievement],  # 第一次返回成就
            [], [], [], []  # 其他4次返回空
        ]

        # 设置回调
        callback_mock = Mock()
        motivation_engine.on_achievement_unlocked = callback_mock

        motivation_engine.check_achievements()

        # 验证回调被调用一次
        callback_mock.assert_called_once_with(achievement)


class TestContinuousUsageDays:
    """测试连续使用天数计算"""

    def test_calculate_continuous_days_single_day(self, motivation_engine, mock_stats_manager):
        """测试单天连续"""
        today = date.today()
        mock_stats_manager.statistics = {
            "daily_records": {
                today.isoformat(): {
                    "summary": {
                        "completed_tasks": 3
                    }
                }
            }
        }

        days = motivation_engine._get_continuous_usage_days()
        assert days == 1.0

    def test_calculate_continuous_days_multiple_days(self, motivation_engine, mock_stats_manager):
        """测试多天连续"""
        today = date.today()
        daily_records = {}

        # 连续5天
        for i in range(5):
            day = today - timedelta(days=i)
            daily_records[day.isoformat()] = {
                "summary": {
                    "completed_tasks": 2
                }
            }

        mock_stats_manager.statistics = {"daily_records": daily_records}

        days = motivation_engine._get_continuous_usage_days()
        assert days == 5.0

    def test_calculate_continuous_days_with_gap(self, motivation_engine, mock_stats_manager):
        """测试有间隔的连续天数"""
        today = date.today()
        daily_records = {
            today.isoformat(): {
                "summary": {
                    "completed_tasks": 3
                }
            },
            (today - timedelta(days=1)).isoformat(): {
                "summary": {
                    "completed_tasks": 2
                }
            },
            # 第2天没有记录 - 中断
            (today - timedelta(days=3)).isoformat(): {
                "summary": {
                    "completed_tasks": 5
                }
            }
        }

        mock_stats_manager.statistics = {"daily_records": daily_records}

        days = motivation_engine._get_continuous_usage_days()
        assert days == 2.0  # 只计算到中断前

    def test_calculate_continuous_days_zero_tasks(self, motivation_engine, mock_stats_manager):
        """测试0任务中断连续"""
        today = date.today()
        daily_records = {
            today.isoformat(): {
                "summary": {
                    "completed_tasks": 3
                }
            },
            (today - timedelta(days=1)).isoformat(): {
                "summary": {
                    "completed_tasks": 0  # 0任务,中断连续
                }
            }
        }

        mock_stats_manager.statistics = {"daily_records": daily_records}

        days = motivation_engine._get_continuous_usage_days()
        assert days == 1.0


class TestTotalStatistics:
    """测试累计统计"""

    def test_get_total_completed_tasks(self, motivation_engine, mock_stats_manager):
        """测试获取累计完成任务数"""
        mock_stats_manager.statistics = {
            "daily_records": {
                "2025-12-01": {"summary": {"completed_tasks": 5}},
                "2025-12-02": {"summary": {"completed_tasks": 3}},
                "2025-12-03": {"summary": {"completed_tasks": 7}}
            }
        }

        total = motivation_engine._get_total_completed_tasks()
        assert total == 15.0

    def test_get_total_focus_hours(self, motivation_engine, mock_stats_manager):
        """测试获取累计专注时长"""
        mock_stats_manager.statistics = {
            "daily_records": {
                "2025-12-01": {"summary": {"total_completed_minutes": 120}},
                "2025-12-02": {"summary": {"total_completed_minutes": 180}},
                "2025-12-03": {"summary": {"total_completed_minutes": 60}}
            }
        }

        hours = motivation_engine._get_total_focus_hours()
        assert hours == 6.0  # 360分钟 = 6小时

    def test_get_today_completion_rate(self, motivation_engine, mock_stats_manager):
        """测试获取今日完成率"""
        today = date.today().isoformat()
        mock_stats_manager.statistics = {
            "daily_records": {
                today: {
                    "summary": {
                        "completion_rate": 85.5
                    }
                }
            }
        }

        rate = motivation_engine._get_today_completion_rate()
        assert rate == 85.5


class TestUpdateAll:
    """测试完整更新"""

    def test_update_all_no_changes(self, motivation_engine, mock_goal_manager, mock_achievement_manager):
        """测试完整更新(无变化)"""
        mock_goal_manager.get_active_goals.return_value = []
        mock_achievement_manager.check_and_unlock.return_value = []

        result = motivation_engine.update_all()

        assert len(result["completed_goals"]) == 0
        assert len(result["unlocked_achievements"]) == 0

    def test_update_all_with_changes(self, motivation_engine, mock_goal_manager, mock_achievement_manager, mock_stats_manager):
        """测试完整更新(有变化)"""
        # Mock目标完成
        goal = Mock()
        goal.goal_id = "test-goal"
        goal.goal_type = "daily_tasks"

        mock_goal_manager.get_active_goals.return_value = [goal]
        mock_goal_manager.update_goal_progress.return_value = True

        # Mock成就解锁
        achievement = Mock()
        achievement.name = "测试成就"

        mock_achievement_manager.check_and_unlock.side_effect = [
            [achievement],  # 第一次调用返回成就
            [], [], [], []  # 后续调用返回空
        ]

        # 设置统计数据
        today = date.today().isoformat()
        mock_stats_manager.statistics = {
            "daily_records": {
                today: {
                    "summary": {
                        "completed_tasks": 5,
                        "total_completed_minutes": 120
                    }
                }
            }
        }

        result = motivation_engine.update_all()

        assert len(result["completed_goals"]) == 1
        assert len(result["unlocked_achievements"]) == 1

    def test_update_all_logs_results(self, motivation_engine, mock_logger, mock_goal_manager, mock_achievement_manager):
        """测试完整更新记录日志"""
        mock_goal_manager.get_active_goals.return_value = []
        mock_achievement_manager.check_and_unlock.return_value = []

        motivation_engine.update_all()

        # 验证日志记录
        assert mock_logger.info.called


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
