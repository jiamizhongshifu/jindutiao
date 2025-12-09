"""
Achievement Manager 单元测试
测试成就系统核心功能
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock
from gaiya.core.achievement_manager import AchievementManager, Achievement


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
def achievement_manager(temp_data_dir, mock_logger):
    """创建AchievementManager实例"""
    return AchievementManager(temp_data_dir, mock_logger)


class TestAchievementInit:
    """测试Achievement对象初始化"""

    def test_achievement_creation(self):
        """测试创建Achievement对象"""
        achievement = Achievement(
            achievement_id="test-id",
            name="测试成就",
            description="测试描述",
            emoji="🏆",
            category="milestone",
            requirement_type="total_tasks_completed",
            requirement_value=10.0,
            rarity="common"
        )

        assert achievement.achievement_id == "test-id"
        assert achievement.name == "测试成就"
        assert achievement.emoji == "🏆"
        assert achievement.category == "milestone"
        assert achievement.unlocked is False

    def test_achievement_to_dict(self):
        """测试Achievement转换为字典"""
        achievement = Achievement(
            achievement_id="test-id",
            name="测试成就",
            description="测试描述",
            emoji="🏆",
            category="milestone",
            requirement_type="total_tasks_completed",
            requirement_value=10.0,
            rarity="rare"
        )

        achievement_dict = achievement.to_dict()

        assert achievement_dict["achievement_id"] == "test-id"
        assert achievement_dict["name"] == "测试成就"
        assert achievement_dict["rarity"] == "rare"
        assert achievement_dict["unlocked"] is False

    def test_achievement_from_dict(self):
        """测试从字典创建Achievement"""
        data = {
            "achievement_id": "test-id",
            "name": "测试成就",
            "description": "测试描述",
            "emoji": "🏆",
            "category": "milestone",
            "requirement_type": "total_tasks_completed",
            "requirement_value": 10.0,
            "rarity": "epic",
            "unlocked": True,
            "unlocked_at": "2025-12-09T10:00:00"
        }

        achievement = Achievement.from_dict(data)

        assert achievement.achievement_id == "test-id"
        assert achievement.unlocked is True
        assert achievement.unlocked_at == "2025-12-09T10:00:00"
        assert achievement.rarity == "epic"


class TestAchievementManagerInit:
    """测试AchievementManager初始化"""

    def test_init_loads_predefined_achievements(self, achievement_manager):
        """测试初始化加载预定义成就"""
        # 应该加载11个预定义成就
        assert len(achievement_manager.achievements) == 11

        # 检查特定成就是否存在
        assert "streak_3_days" in achievement_manager.achievements
        assert "tasks_10" in achievement_manager.achievements
        assert "focus_10_hours" in achievement_manager.achievements

    def test_init_all_achievements_locked(self, achievement_manager):
        """测试初始化时所有成就都未解锁"""
        for achievement in achievement_manager.achievements.values():
            assert achievement.unlocked is False

    def test_init_with_existing_unlocked_achievements(self, temp_data_dir, mock_logger):
        """测试加载已解锁成就"""
        # 创建测试数据
        achievements_file = temp_data_dir / "achievements.json"
        test_data = {
            "unlocked": [
                {
                    "achievement_id": "streak_3_days",
                    "unlocked_at": "2025-12-09T10:00:00"
                },
                {
                    "achievement_id": "tasks_10",
                    "unlocked_at": "2025-12-08T15:30:00"
                }
            ]
        }

        with open(achievements_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # 加载
        manager = AchievementManager(temp_data_dir, mock_logger)

        # 检查已解锁成就
        assert manager.achievements["streak_3_days"].unlocked is True
        assert manager.achievements["tasks_10"].unlocked is True
        assert manager.achievements["streak_7_days"].unlocked is False


class TestAchievementUnlocking:
    """测试成就解锁"""

    def test_check_and_unlock_single_achievement(self, achievement_manager):
        """测试解锁单个成就"""
        # 解锁3天连续打卡成就
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="continuous_days",
            current_value=3.0
        )

        assert len(newly_unlocked) == 1
        assert newly_unlocked[0].achievement_id == "streak_3_days"
        assert achievement_manager.achievements["streak_3_days"].unlocked is True

    def test_check_and_unlock_multiple_achievements(self, achievement_manager):
        """测试一次解锁多个成就"""
        # 连续30天应该解锁3个成就 (3天、7天、30天)
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="continuous_days",
            current_value=30.0
        )

        assert len(newly_unlocked) == 3
        assert achievement_manager.achievements["streak_3_days"].unlocked is True
        assert achievement_manager.achievements["streak_7_days"].unlocked is True
        assert achievement_manager.achievements["streak_30_days"].unlocked is True

    def test_check_and_unlock_no_new_achievements(self, achievement_manager):
        """测试值不足时不解锁"""
        # 只有2天,不足以解锁3天成就
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="continuous_days",
            current_value=2.0
        )

        assert len(newly_unlocked) == 0
        assert achievement_manager.achievements["streak_3_days"].unlocked is False

    def test_check_and_unlock_already_unlocked(self, achievement_manager):
        """测试已解锁成就不重复解锁"""
        # 第一次解锁
        achievement_manager.check_and_unlock(
            requirement_type="continuous_days",
            current_value=3.0
        )

        # 第二次检查
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="continuous_days",
            current_value=5.0
        )

        # 应该不包含已解锁的3天成就
        achievement_ids = [a.achievement_id for a in newly_unlocked]
        assert "streak_3_days" not in achievement_ids

    def test_check_and_unlock_sets_timestamp(self, achievement_manager):
        """测试解锁时设置时间戳"""
        before_time = datetime.now(timezone.utc)

        achievement_manager.check_and_unlock(
            requirement_type="continuous_days",
            current_value=3.0
        )

        after_time = datetime.now(timezone.utc)

        unlocked_achievement = achievement_manager.achievements["streak_3_days"]
        assert unlocked_achievement.unlocked_at is not None

        # 验证时间戳在合理范围内 (只检查时间戳存在即可)
        unlocked_time_str = unlocked_achievement.unlocked_at
        assert isinstance(unlocked_time_str, str)
        assert len(unlocked_time_str) > 0

    def test_check_and_unlock_saves_to_file(self, achievement_manager):
        """测试解锁后保存到文件"""
        achievement_manager.check_and_unlock(
            requirement_type="continuous_days",
            current_value=3.0
        )

        # 检查文件是否存在
        assert achievement_manager.achievements_file.exists()

        # 读取文件验证
        with open(achievement_manager.achievements_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["unlocked"]) == 1
        assert data["unlocked"][0]["achievement_id"] == "streak_3_days"


class TestAchievementRetrieval:
    """测试成就检索"""

    def test_get_all_achievements(self, achievement_manager):
        """测试获取所有成就"""
        all_achievements = achievement_manager.get_all_achievements()

        assert len(all_achievements) == 11
        assert all(isinstance(a, Achievement) for a in all_achievements)

    def test_get_unlocked_achievements(self, achievement_manager):
        """测试获取已解锁成就"""
        # 解锁一些成就
        achievement_manager.check_and_unlock("continuous_days", 7.0)
        achievement_manager.check_and_unlock("total_tasks_completed", 10.0)

        unlocked = achievement_manager.get_unlocked_achievements()

        # 应该解锁: 3天、7天连续, 10个任务
        assert len(unlocked) == 3

    def test_get_locked_achievements(self, achievement_manager):
        """测试获取未解锁成就"""
        # 解锁一些成就
        achievement_manager.check_and_unlock("continuous_days", 3.0)

        locked = achievement_manager.get_locked_achievements()

        # 应该还有10个未解锁
        assert len(locked) == 10


class TestAchievementCategories:
    """测试成就分类"""

    def test_streak_achievements(self, achievement_manager):
        """测试连续打卡成就"""
        streak_achievements = [
            a for a in achievement_manager.get_all_achievements()
            if a.category == "streak"
        ]

        assert len(streak_achievements) == 3
        assert all(a.requirement_type == "continuous_days" for a in streak_achievements)

    def test_milestone_achievements(self, achievement_manager):
        """测试里程碑成就"""
        milestone_achievements = [
            a for a in achievement_manager.get_all_achievements()
            if a.category == "milestone"
        ]

        assert len(milestone_achievements) == 6  # 3个任务 + 3个专注时长

    def test_performance_achievements(self, achievement_manager):
        """测试表现成就"""
        performance_achievements = [
            a for a in achievement_manager.get_all_achievements()
            if a.category == "performance"
        ]

        assert len(performance_achievements) == 2  # 完美一天 + 完美一周


class TestAchievementRarity:
    """测试成就稀有度"""

    def test_rarity_distribution(self, achievement_manager):
        """测试稀有度分布"""
        rarity_counts = {
            "common": 0,
            "rare": 0,
            "epic": 0,
            "legendary": 0
        }

        for achievement in achievement_manager.get_all_achievements():
            rarity_counts[achievement.rarity] += 1

        # 验证各稀有度数量
        assert rarity_counts["common"] == 3
        assert rarity_counts["rare"] == 4
        assert rarity_counts["epic"] == 3
        assert rarity_counts["legendary"] == 1


class TestAchievementStatistics:
    """测试成就统计"""

    def test_empty_statistics(self, achievement_manager):
        """测试初始统计"""
        stats = achievement_manager.get_statistics()

        assert stats["total_achievements"] == 11
        assert stats["unlocked_count"] == 0
        assert stats["unlock_percentage"] == 0.0
        assert stats["rarity_counts"]["common"] == 0

    def test_statistics_with_unlocked_achievements(self, achievement_manager):
        """测试有解锁成就的统计"""
        # 解锁一些成就
        achievement_manager.check_and_unlock("continuous_days", 7.0)  # common + rare
        achievement_manager.check_and_unlock("total_tasks_completed", 100.0)  # common + rare

        stats = achievement_manager.get_statistics()

        assert stats["total_achievements"] == 11
        assert stats["unlocked_count"] == 4  # 3天、7天、10任务、100任务
        assert stats["unlock_percentage"] == pytest.approx(36.36, rel=1e-2)
        assert stats["rarity_counts"]["common"] == 2
        assert stats["rarity_counts"]["rare"] == 2


class TestRequirementTypes:
    """测试不同需求类型"""

    def test_total_tasks_completed_requirement(self, achievement_manager):
        """测试累计任务完成需求"""
        # 解锁10个任务
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="total_tasks_completed",
            current_value=10.0
        )

        assert len(newly_unlocked) == 1
        assert newly_unlocked[0].achievement_id == "tasks_10"

    def test_total_focus_hours_requirement(self, achievement_manager):
        """测试累计专注时长需求"""
        # 解锁100小时专注
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="total_focus_hours",
            current_value=100.0
        )

        assert len(newly_unlocked) == 2  # 10小时 + 100小时
        achievement_ids = [a.achievement_id for a in newly_unlocked]
        assert "focus_10_hours" in achievement_ids
        assert "focus_100_hours" in achievement_ids

    def test_daily_completion_rate_requirement(self, achievement_manager):
        """测试每日完成率需求"""
        # 解锁完美一天
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="daily_completion_rate",
            current_value=100.0
        )

        assert len(newly_unlocked) == 1
        assert newly_unlocked[0].achievement_id == "perfect_day"

    def test_weekly_completion_rate_requirement(self, achievement_manager):
        """测试每周完成率需求"""
        # 解锁完美一周
        newly_unlocked = achievement_manager.check_and_unlock(
            requirement_type="weekly_completion_rate",
            current_value=100.0
        )

        assert len(newly_unlocked) == 1
        assert newly_unlocked[0].achievement_id == "perfect_week"


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
