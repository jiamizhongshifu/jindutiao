"""
Goal Manager 单元测试
测试目标管理核心功能
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import Mock
from gaiya.core.goal_manager import GoalManager, Goal


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_logger():
    """创建Mock Logger"""
    return Mock()


@pytest.fixture
def goal_manager(temp_data_dir, mock_logger):
    """创建GoalManager实例"""
    return GoalManager(temp_data_dir, mock_logger)


class TestGoalInit:
    """测试Goal对象初始化"""

    def test_goal_creation(self):
        """测试创建Goal对象"""
        goal = Goal(
            goal_id="test-id",
            goal_type="daily_tasks",
            target_value=5.0,
            start_date="2025-12-09",
            status="active"
        )

        assert goal.goal_id == "test-id"
        assert goal.goal_type == "daily_tasks"
        assert goal.target_value == 5.0
        assert goal.current_value == 0.0
        assert goal.status == "active"

    def test_goal_to_dict(self):
        """测试Goal转换为字典"""
        goal = Goal(
            goal_id="test-id",
            goal_type="daily_tasks",
            target_value=5.0,
            start_date="2025-12-09"
        )

        goal_dict = goal.to_dict()

        assert goal_dict["goal_id"] == "test-id"
        assert goal_dict["goal_type"] == "daily_tasks"
        assert goal_dict["target_value"] == 5.0
        assert goal_dict["current_value"] == 0.0
        assert goal_dict["status"] == "active"

    def test_goal_from_dict(self):
        """测试从字典创建Goal"""
        data = {
            "goal_id": "test-id",
            "goal_type": "daily_tasks",
            "target_value": 5.0,
            "current_value": 3.0,
            "start_date": "2025-12-09",
            "status": "active"
        }

        goal = Goal.from_dict(data)

        assert goal.goal_id == "test-id"
        assert goal.current_value == 3.0
        assert goal.status == "active"

    def test_goal_progress_percentage(self):
        """测试进度百分比计算"""
        goal = Goal(
            goal_id="test-id",
            goal_type="daily_tasks",
            target_value=10.0,
            start_date="2025-12-09"
        )

        # 0% 进度
        assert goal.get_progress_percentage() == 0.0

        # 50% 进度
        goal.current_value = 5.0
        assert goal.get_progress_percentage() == 50.0

        # 100% 进度
        goal.current_value = 10.0
        assert goal.get_progress_percentage() == 100.0

        # 超过100%应显示100%
        goal.current_value = 15.0
        assert goal.get_progress_percentage() == 100.0

    def test_goal_is_completed(self):
        """测试目标完成判断"""
        goal = Goal(
            goal_id="test-id",
            goal_type="daily_tasks",
            target_value=5.0,
            start_date="2025-12-09"
        )

        # 未完成
        goal.current_value = 3.0
        assert goal.is_completed() is False

        # 刚好完成
        goal.current_value = 5.0
        assert goal.is_completed() is True

        # 超额完成
        goal.current_value = 7.0
        assert goal.is_completed() is True

    def test_goal_get_info(self):
        """测试获取目标信息"""
        goal = Goal(
            goal_id="test-id",
            goal_type="daily_tasks",
            target_value=5.0,
            start_date="2025-12-09"
        )
        goal.current_value = 3.0

        info = goal.get_info()

        assert info["goal_id"] == "test-id"
        assert info["name"] == "每日任务目标"
        assert info["emoji"] == "📋"
        assert info["target_value"] == 5.0
        assert info["current_value"] == 3.0
        assert info["progress_percentage"] == 60.0
        assert info["is_completed"] is False


class TestGoalManagerInit:
    """测试GoalManager初始化"""

    def test_init_empty_directory(self, goal_manager):
        """测试空目录初始化"""
        assert len(goal_manager.goals) == 0
        assert goal_manager.goals_file.parent.exists()

    def test_init_with_existing_goals(self, temp_data_dir, mock_logger):
        """测试加载已有目标"""
        # 创建测试数据
        goals_file = temp_data_dir / "goals.json"
        test_data = {
            "goals": [
                {
                    "goal_id": "test-1",
                    "goal_type": "daily_tasks",
                    "target_value": 5.0,
                    "current_value": 3.0,
                    "start_date": "2025-12-09",
                    "status": "active"
                }
            ]
        }

        with open(goals_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # 加载
        manager = GoalManager(temp_data_dir, mock_logger)

        assert len(manager.goals) == 1
        assert "test-1" in manager.goals


class TestGoalCreation:
    """测试目标创建"""

    def test_create_daily_tasks_goal(self, goal_manager):
        """测试创建每日任务目标"""
        goal = goal_manager.create_goal(
            goal_type="daily_tasks",
            target_value=5.0
        )

        assert goal.goal_type == "daily_tasks"
        assert goal.target_value == 5.0
        assert goal.status == "active"
        assert goal.goal_id in goal_manager.goals

    def test_create_weekly_focus_hours_goal(self, goal_manager):
        """测试创建每周专注时长目标"""
        goal = goal_manager.create_goal(
            goal_type="weekly_focus_hours",
            target_value=20.0
        )

        assert goal.goal_type == "weekly_focus_hours"
        assert goal.target_value == 20.0

    def test_create_goal_with_custom_dates(self, goal_manager):
        """测试创建带自定义日期的目标"""
        start_date = "2025-12-01"
        end_date = "2025-12-31"

        goal = goal_manager.create_goal(
            goal_type="daily_tasks",
            target_value=5.0,
            start_date=start_date,
            end_date=end_date
        )

        assert goal.start_date == start_date
        assert goal.end_date == end_date

    def test_create_invalid_goal_type(self, goal_manager):
        """测试创建无效类型的目标"""
        with pytest.raises(ValueError):
            goal_manager.create_goal(
                goal_type="invalid_type",
                target_value=5.0
            )

    def test_goal_persistence_after_creation(self, goal_manager):
        """测试目标创建后持久化"""
        goal = goal_manager.create_goal(
            goal_type="daily_tasks",
            target_value=5.0
        )

        # 检查文件是否存在
        assert goal_manager.goals_file.exists()

        # 读取文件验证
        with open(goal_manager.goals_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["goals"]) == 1
        assert data["goals"][0]["goal_id"] == goal.goal_id


class TestGoalRetrieval:
    """测试目标检索"""

    def test_get_active_goals(self, goal_manager):
        """测试获取活跃目标"""
        # 创建多个目标
        goal1 = goal_manager.create_goal("daily_tasks", 5.0)
        goal2 = goal_manager.create_goal("weekly_focus_hours", 20.0)

        # 完成一个目标
        goal1.status = "completed"

        active_goals = goal_manager.get_active_goals()

        assert len(active_goals) == 1
        assert active_goals[0].goal_id == goal2.goal_id

    def test_get_goal_by_id(self, goal_manager):
        """测试通过ID获取目标"""
        goal = goal_manager.create_goal("daily_tasks", 5.0)

        retrieved_goal = goal_manager.get_goal(goal.goal_id)

        assert retrieved_goal is not None
        assert retrieved_goal.goal_id == goal.goal_id

    def test_get_nonexistent_goal(self, goal_manager):
        """测试获取不存在的目标"""
        result = goal_manager.get_goal("nonexistent-id")
        assert result is None


class TestGoalProgressUpdate:
    """测试目标进度更新"""

    def test_update_goal_progress(self, goal_manager):
        """测试更新目标进度"""
        goal = goal_manager.create_goal("daily_tasks", 5.0)

        # 更新进度
        just_completed = goal_manager.update_goal_progress(goal.goal_id, 3.0)

        assert goal.current_value == 3.0
        assert just_completed is False  # 未完成

    def test_update_goal_to_completion(self, goal_manager):
        """测试目标完成"""
        goal = goal_manager.create_goal("daily_tasks", 5.0)

        # 更新到完成
        just_completed = goal_manager.update_goal_progress(goal.goal_id, 5.0)

        assert goal.current_value == 5.0
        assert goal.status == "completed"
        assert goal.completed_at is not None
        assert just_completed is True

    def test_update_completed_goal_no_change(self, goal_manager):
        """测试更新已完成目标不再触发完成事件"""
        goal = goal_manager.create_goal("daily_tasks", 5.0)

        # 第一次完成
        goal_manager.update_goal_progress(goal.goal_id, 5.0)

        # 第二次更新
        just_completed = goal_manager.update_goal_progress(goal.goal_id, 6.0)

        assert just_completed is False  # 不是刚完成

    def test_update_nonexistent_goal(self, goal_manager):
        """测试更新不存在的目标"""
        result = goal_manager.update_goal_progress("nonexistent-id", 5.0)
        assert result is False


class TestGoalDeletion:
    """测试目标删除"""

    def test_delete_goal(self, goal_manager):
        """测试删除目标"""
        goal = goal_manager.create_goal("daily_tasks", 5.0)
        goal_id = goal.goal_id

        goal_manager.delete_goal(goal_id)

        assert goal_id not in goal_manager.goals

    def test_delete_nonexistent_goal(self, goal_manager):
        """测试删除不存在的目标不报错"""
        goal_manager.delete_goal("nonexistent-id")  # 应该不抛异常

    def test_abandon_goal(self, goal_manager):
        """测试放弃目标"""
        goal = goal_manager.create_goal("daily_tasks", 5.0)

        goal_manager.abandon_goal(goal.goal_id)

        assert goal.status == "abandoned"


class TestGoalStatistics:
    """测试目标统计"""

    def test_empty_statistics(self, goal_manager):
        """测试空统计"""
        stats = goal_manager.get_statistics()

        assert stats["total_goals"] == 0
        assert stats["active_goals"] == 0
        assert stats["completed_goals"] == 0
        assert stats["completion_rate"] == 0

    def test_statistics_with_goals(self, goal_manager):
        """测试有目标的统计"""
        # 创建3个目标
        goal1 = goal_manager.create_goal("daily_tasks", 5.0)
        goal2 = goal_manager.create_goal("weekly_focus_hours", 20.0)
        goal3 = goal_manager.create_goal("weekly_completion_rate", 80.0)

        # 完成1个
        goal_manager.update_goal_progress(goal1.goal_id, 5.0)

        stats = goal_manager.get_statistics()

        assert stats["total_goals"] == 3
        assert stats["active_goals"] == 2
        assert stats["completed_goals"] == 1
        assert stats["completion_rate"] == pytest.approx(33.33, rel=1e-2)


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
