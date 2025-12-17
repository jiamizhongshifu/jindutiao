"""
Achievement System - Gamification and user motivation

Tracks user achievements and unlocks badges:
- Milestone-based achievements
- Streak-based achievements
- Performance-based achievements
- Achievement unlocking notifications
- Progress tracking and category filtering

Author: GaiYa Team
Date: 2025-12-09
Version: 2.0 (Enhanced with progress tracking and new categories)
"""

import json
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, date
from pathlib import Path


# Achievement Category Definitions
ACHIEVEMENT_CATEGORIES = {
    "consistency": {
        "name": "坚持之道",
        "icon": "flame",
        "color": "#FF6B35",
        "description": "记录你的持续使用天数"
    },
    "productivity": {
        "name": "效率大师",
        "icon": "lightning",
        "color": "#FFD700",
        "description": "完成任务相关成就"
    },
    "focus": {
        "name": "专注达人",
        "icon": "target",
        "color": "#4ECDC4",
        "description": "专注时间相关成就"
    },
    "explorer": {
        "name": "功能探索",
        "icon": "compass",
        "color": "#9B59B6",
        "description": "探索和使用各种功能"
    },
    "special": {
        "name": "特殊成就",
        "icon": "sparkles",
        "color": "#E91E63",
        "description": "限定时段或特殊条件解锁"
    }
}

# Rarity color mappings
RARITY_COLORS = {
    "common": {"border": "#BDBDBD", "bg": "#F5F5F5", "text": "#757575"},
    "rare": {"border": "#2196F3", "bg": "#E3F2FD", "text": "#1565C0"},
    "epic": {"border": "#9C27B0", "bg": "#F3E5F5", "text": "#7B1FA2"},
    "legendary": {"border": "#FFD700", "bg": "#FFF8E1", "text": "#FF6F00"}
}

# Title system based on total points
TITLE_LEVELS = {
    0: "时间新手",
    50: "时间学徒",
    100: "时间管理者",
    200: "时间大师",
    500: "时间领主",
    1000: "时间之神"
}


class Achievement:
    """
    Single Achievement Definition

    Represents an achievement that can be unlocked with progress tracking
    """

    def __init__(
        self,
        achievement_id: str,
        name: str,
        description: str,
        emoji: str,
        category: str,
        requirement_type: str,
        requirement_value: float,
        rarity: str = 'common',
        points: int = 10,
        progress_unit: str = ''
    ):
        """
        Initialize Achievement

        Args:
            achievement_id: Unique achievement ID
            name: Achievement name
            description: Achievement description
            emoji: Achievement emoji icon
            category: Achievement category (consistency/productivity/focus/explorer/special)
            requirement_type: Type of requirement (e.g., 'continuous_days', 'total_tasks')
            requirement_value: Value needed to unlock (target)
            rarity: Achievement rarity (common/rare/epic/legendary)
            points: Points awarded when unlocked
            progress_unit: Unit for progress display (e.g., '天', '个', '小时')
        """
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.emoji = emoji
        self.category = category
        self.requirement_type = requirement_type
        self.requirement_value = requirement_value
        self.rarity = rarity
        self.points = points
        self.progress_unit = progress_unit
        self.unlocked = False
        self.unlocked_at = None
        # Progress tracking
        self.progress = 0.0
        self.target = requirement_value

    def get_progress_percentage(self) -> float:
        """Get progress as percentage (0-100)"""
        if self.target == 0:
            return 0.0
        return min(100.0, (self.progress / self.target) * 100)

    def get_progress_text(self) -> str:
        """Get formatted progress text"""
        if self.unlocked:
            return "已解锁"
        # Format based on requirement type
        if self.progress_unit:
            return f"{int(self.progress)}/{int(self.target)}{self.progress_unit}"
        return f"{int(self.progress)}/{int(self.target)}"

    def update_progress(self, current_value: float) -> bool:
        """
        Update progress and check if unlocked

        Args:
            current_value: Current value for this requirement type

        Returns:
            True if newly unlocked, False otherwise
        """
        self.progress = min(current_value, self.target)
        if not self.unlocked and current_value >= self.target:
            self.unlocked = True
            self.unlocked_at = datetime.now().isoformat()
            return True
        return False

    def get_category_info(self) -> Dict:
        """Get category information"""
        return ACHIEVEMENT_CATEGORIES.get(self.category, {
            "name": self.category,
            "icon": "star",
            "color": "#9E9E9E",
            "description": ""
        })

    def get_rarity_colors(self) -> Dict:
        """Get rarity color scheme"""
        return RARITY_COLORS.get(self.rarity, RARITY_COLORS["common"])

    def to_dict(self) -> Dict:
        """Convert achievement to dictionary"""
        return {
            'achievement_id': self.achievement_id,
            'name': self.name,
            'description': self.description,
            'emoji': self.emoji,
            'category': self.category,
            'requirement_type': self.requirement_type,
            'requirement_value': self.requirement_value,
            'rarity': self.rarity,
            'points': self.points,
            'progress_unit': self.progress_unit,
            'unlocked': self.unlocked,
            'unlocked_at': self.unlocked_at,
            'progress': self.progress,
            'target': self.target
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Achievement':
        """Create achievement from dictionary"""
        achievement = cls(
            achievement_id=data['achievement_id'],
            name=data['name'],
            description=data['description'],
            emoji=data['emoji'],
            category=data['category'],
            requirement_type=data['requirement_type'],
            requirement_value=data['requirement_value'],
            rarity=data.get('rarity', 'common'),
            points=data.get('points', 10),
            progress_unit=data.get('progress_unit', '')
        )
        achievement.unlocked = data.get('unlocked', False)
        achievement.unlocked_at = data.get('unlocked_at')
        achievement.progress = data.get('progress', 0.0)
        achievement.target = data.get('target', achievement.requirement_value)
        return achievement


class AchievementManager:
    """
    Achievement Management System

    Manages achievement definitions, unlocking, and persistence
    """

    # Predefined achievements - Enhanced with new categories and progress tracking
    ACHIEVEMENTS = [
        # ============ 坚持之道 (Consistency) ============
        {
            'achievement_id': 'streak_3_days',
            'name': '初露锋芒',
            'description': '连续使用GaiYa 3天',
            'emoji': '🔥',
            'category': 'consistency',
            'requirement_type': 'continuous_days',
            'requirement_value': 3,
            'rarity': 'common',
            'points': 10,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'streak_7_days',
            'name': '七日之约',
            'description': '连续使用GaiYa 7天',
            'emoji': '💪',
            'category': 'consistency',
            'requirement_type': 'continuous_days',
            'requirement_value': 7,
            'rarity': 'rare',
            'points': 20,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'streak_30_days',
            'name': '习惯养成',
            'description': '连续使用GaiYa 30天',
            'emoji': '👑',
            'category': 'consistency',
            'requirement_type': 'continuous_days',
            'requirement_value': 30,
            'rarity': 'epic',
            'points': 50,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'streak_100_days',
            'name': '百日之约',
            'description': '连续使用GaiYa 100天',
            'emoji': '🏅',
            'category': 'consistency',
            'requirement_type': 'continuous_days',
            'requirement_value': 100,
            'rarity': 'epic',
            'points': 100,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'streak_365_days',
            'name': '年度陪伴',
            'description': '连续使用GaiYa 365天',
            'emoji': '🌟',
            'category': 'consistency',
            'requirement_type': 'continuous_days',
            'requirement_value': 365,
            'rarity': 'legendary',
            'points': 200,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'early_bird',
            'name': '早起鸟儿',
            'description': '连续7天在9点前开始工作',
            'emoji': '🌅',
            'category': 'consistency',
            'requirement_type': 'early_start_streak',
            'requirement_value': 7,
            'rarity': 'rare',
            'points': 25,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'night_owl',
            'name': '夜猫子',
            'description': '连续7天22点后仍在工作',
            'emoji': '🦉',
            'category': 'consistency',
            'requirement_type': 'late_work_streak',
            'requirement_value': 7,
            'rarity': 'rare',
            'points': 25,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'weekend_warrior',
            'name': '周末战士',
            'description': '连续2个周末都在使用GaiYa',
            'emoji': '⚔️',
            'category': 'consistency',
            'requirement_type': 'weekend_usage_streak',
            'requirement_value': 2,
            'rarity': 'common',
            'points': 10,
            'progress_unit': '周'
        },

        # ============ 效率大师 (Productivity) ============
        {
            'achievement_id': 'tasks_10',
            'name': '新手上路',
            'description': '累计完成10个任务',
            'emoji': '📝',
            'category': 'productivity',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 10,
            'rarity': 'common',
            'points': 10,
            'progress_unit': '个'
        },
        {
            'achievement_id': 'tasks_50',
            'name': '任务新星',
            'description': '累计完成50个任务',
            'emoji': '✨',
            'category': 'productivity',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 50,
            'rarity': 'common',
            'points': 15,
            'progress_unit': '个'
        },
        {
            'achievement_id': 'tasks_100',
            'name': '百任务达人',
            'description': '累计完成100个任务',
            'emoji': '⭐',
            'category': 'productivity',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 100,
            'rarity': 'rare',
            'points': 30,
            'progress_unit': '个'
        },
        {
            'achievement_id': 'tasks_500',
            'name': '任务狂人',
            'description': '累计完成500个任务',
            'emoji': '🚀',
            'category': 'productivity',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 500,
            'rarity': 'epic',
            'points': 80,
            'progress_unit': '个'
        },
        {
            'achievement_id': 'tasks_1000',
            'name': '生产力机器',
            'description': '累计完成1000个任务',
            'emoji': '🤖',
            'category': 'productivity',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 1000,
            'rarity': 'legendary',
            'points': 150,
            'progress_unit': '个'
        },
        {
            'achievement_id': 'perfect_day',
            'name': '完美一天',
            'description': '单日任务完成率达到100%',
            'emoji': '💯',
            'category': 'productivity',
            'requirement_type': 'daily_completion_rate',
            'requirement_value': 100,
            'rarity': 'common',
            'points': 10,
            'progress_unit': '%'
        },
        {
            'achievement_id': 'perfect_week',
            'name': '完美一周',
            'description': '连续7天任务完成率100%',
            'emoji': '🌈',
            'category': 'productivity',
            'requirement_type': 'perfect_day_streak',
            'requirement_value': 7,
            'rarity': 'epic',
            'points': 80,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'speed_demon',
            'name': '效率恶魔',
            'description': '单日完成10个以上任务',
            'emoji': '⚡',
            'category': 'productivity',
            'requirement_type': 'daily_tasks_completed',
            'requirement_value': 10,
            'rarity': 'rare',
            'points': 30,
            'progress_unit': '个'
        },

        # ============ 专注达人 (Focus) ============
        {
            'achievement_id': 'focus_10_hours',
            'name': '专注新星',
            'description': '累计专注10小时',
            'emoji': '⏰',
            'category': 'focus',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 10,
            'rarity': 'common',
            'points': 10,
            'progress_unit': '小时'
        },
        {
            'achievement_id': 'focus_50_hours',
            'name': '专注能手',
            'description': '累计专注50小时',
            'emoji': '🎯',
            'category': 'focus',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 50,
            'rarity': 'rare',
            'points': 25,
            'progress_unit': '小时'
        },
        {
            'achievement_id': 'focus_100_hours',
            'name': '专注达人',
            'description': '累计专注100小时',
            'emoji': '🔥',
            'category': 'focus',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 100,
            'rarity': 'rare',
            'points': 40,
            'progress_unit': '小时'
        },
        {
            'achievement_id': 'focus_500_hours',
            'name': '专注大师',
            'description': '累计专注500小时',
            'emoji': '🏆',
            'category': 'focus',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 500,
            'rarity': 'epic',
            'points': 100,
            'progress_unit': '小时'
        },
        {
            'achievement_id': 'focus_1000_hours',
            'name': '时间管理大师',
            'description': '累计专注1000小时',
            'emoji': '👑',
            'category': 'focus',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 1000,
            'rarity': 'legendary',
            'points': 200,
            'progress_unit': '小时'
        },
        {
            'achievement_id': 'deep_work',
            'name': '深度工作',
            'description': '单次专注超过2小时',
            'emoji': '🧘',
            'category': 'focus',
            'requirement_type': 'single_focus_session',
            'requirement_value': 120,
            'rarity': 'rare',
            'points': 25,
            'progress_unit': '分钟'
        },
        {
            'achievement_id': 'code_warrior',
            'name': '代码战士',
            'description': '在代码编辑器中专注满50小时',
            'emoji': '💻',
            'category': 'focus',
            'requirement_type': 'app_focus_hours',
            'requirement_value': 50,
            'rarity': 'rare',
            'points': 35,
            'progress_unit': '小时'
        },

        # ============ 功能探索 (Explorer) ============
        {
            'achievement_id': 'first_task',
            'name': '迈出第一步',
            'description': '完成第一个任务',
            'emoji': '🎉',
            'category': 'explorer',
            'requirement_type': 'first_task_completed',
            'requirement_value': 1,
            'rarity': 'common',
            'points': 5,
            'progress_unit': ''
        },
        {
            'achievement_id': 'scene_creator',
            'name': '场景设计师',
            'description': '创建第一个自定义场景',
            'emoji': '🎨',
            'category': 'explorer',
            'requirement_type': 'first_scene_created',
            'requirement_value': 1,
            'rarity': 'common',
            'points': 10,
            'progress_unit': ''
        },
        {
            'achievement_id': 'ai_user',
            'name': 'AI助手',
            'description': '首次使用AI生成任务',
            'emoji': '🤖',
            'category': 'explorer',
            'requirement_type': 'first_ai_task',
            'requirement_value': 1,
            'rarity': 'common',
            'points': 10,
            'progress_unit': ''
        },
        {
            'achievement_id': 'stats_viewer',
            'name': '数据分析师',
            'description': '查看统计报告10次',
            'emoji': '📊',
            'category': 'explorer',
            'requirement_type': 'stats_view_count',
            'requirement_value': 10,
            'rarity': 'common',
            'points': 10,
            'progress_unit': '次'
        },
        {
            'achievement_id': 'power_user',
            'name': '高级用户',
            'description': '解锁所有探索类成就',
            'emoji': '🌟',
            'category': 'explorer',
            'requirement_type': 'explorer_achievements_unlocked',
            'requirement_value': 4,
            'rarity': 'rare',
            'points': 40,
            'progress_unit': '个'
        },

        # ============ 特殊成就 (Special) ============
        {
            'achievement_id': 'new_year',
            'name': '新年新气象',
            'description': '在新年第一天使用GaiYa',
            'emoji': '🎊',
            'category': 'special',
            'requirement_type': 'new_year_usage',
            'requirement_value': 1,
            'rarity': 'epic',
            'points': 50,
            'progress_unit': ''
        },
        {
            'achievement_id': 'anniversary',
            'name': '周年纪念',
            'description': '使用GaiYa满一周年',
            'emoji': '🎂',
            'category': 'special',
            'requirement_type': 'usage_anniversary',
            'requirement_value': 365,
            'rarity': 'legendary',
            'points': 150,
            'progress_unit': '天'
        },
        {
            'achievement_id': 'midnight_worker',
            'name': '午夜奋斗者',
            'description': '在凌晨0点-2点期间完成任务',
            'emoji': '🌙',
            'category': 'special',
            'requirement_type': 'midnight_task_completed',
            'requirement_value': 1,
            'rarity': 'rare',
            'points': 20,
            'progress_unit': ''
        },
        {
            'achievement_id': 'holiday_hero',
            'name': '假日英雄',
            'description': '在法定节假日完成任务',
            'emoji': '🦸',
            'category': 'special',
            'requirement_type': 'holiday_task_completed',
            'requirement_value': 1,
            'rarity': 'rare',
            'points': 25,
            'progress_unit': ''
        }
    ]

    def __init__(self, data_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize Achievement Manager

        Args:
            data_dir: Directory to store achievements.json
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.data_dir = data_dir
        self.achievements_file = data_dir / 'achievements.json'

        self.achievements: Dict[str, Achievement] = {}
        self._initialize_achievements()
        self._load_achievements()

    def _initialize_achievements(self):
        """Initialize predefined achievements"""
        for achievement_data in self.ACHIEVEMENTS:
            achievement = Achievement(
                achievement_id=achievement_data['achievement_id'],
                name=achievement_data['name'],
                description=achievement_data['description'],
                emoji=achievement_data['emoji'],
                category=achievement_data['category'],
                requirement_type=achievement_data['requirement_type'],
                requirement_value=achievement_data['requirement_value'],
                rarity=achievement_data.get('rarity', 'common'),
                points=achievement_data.get('points', 10),
                progress_unit=achievement_data.get('progress_unit', '')
            )
            self.achievements[achievement.achievement_id] = achievement

    def _load_achievements(self):
        """Load unlocked achievements and progress from JSON file"""
        try:
            if self.achievements_file.exists():
                with open(self.achievements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Load unlocked status
                unlocked_achievements = data.get('unlocked', [])
                for unlocked_data in unlocked_achievements:
                    achievement_id = unlocked_data['achievement_id']
                    if achievement_id in self.achievements:
                        self.achievements[achievement_id].unlocked = True
                        self.achievements[achievement_id].unlocked_at = unlocked_data.get('unlocked_at')

                # Load progress data
                progress_data = data.get('progress', {})
                for achievement_id, progress in progress_data.items():
                    if achievement_id in self.achievements:
                        self.achievements[achievement_id].progress = progress

                self.logger.info(f"Loaded {len(unlocked_achievements)} unlocked achievements")

        except Exception as e:
            self.logger.error(f"Failed to load achievements: {e}")

    def _save_achievements(self):
        """Save unlocked achievements and progress to JSON file"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)

            unlocked = [
                {
                    'achievement_id': achievement.achievement_id,
                    'unlocked_at': achievement.unlocked_at
                }
                for achievement in self.achievements.values()
                if achievement.unlocked
            ]

            # Save progress for all achievements
            progress = {
                achievement.achievement_id: achievement.progress
                for achievement in self.achievements.values()
            }

            data = {
                'unlocked': unlocked,
                'progress': progress,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.achievements_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(unlocked)} unlocked achievements")

        except Exception as e:
            self.logger.error(f"Failed to save achievements: {e}")

    def check_and_unlock(
        self,
        requirement_type: str,
        current_value: float,
        update_progress: bool = True
    ) -> List[Achievement]:
        """
        Check if any achievements should be unlocked and update progress

        Args:
            requirement_type: Type of requirement to check
            current_value: Current value of the requirement
            update_progress: Whether to update progress for matching achievements

        Returns:
            List of newly unlocked achievements
        """
        newly_unlocked = []

        for achievement in self.achievements.values():
            # Update progress for matching requirement type
            if achievement.requirement_type == requirement_type:
                if update_progress:
                    achievement.progress = min(current_value, achievement.target)

                # Skip if already unlocked
                if achievement.unlocked:
                    continue

                # Check if value is sufficient to unlock
                if current_value >= achievement.requirement_value:
                    achievement.unlocked = True
                    achievement.unlocked_at = datetime.now().isoformat()
                    achievement.progress = achievement.target
                    newly_unlocked.append(achievement)

                    self.logger.info(
                        f"Achievement unlocked: {achievement.name} ({achievement.achievement_id})"
                    )

        if newly_unlocked or update_progress:
            self._save_achievements()

        return newly_unlocked

    def update_progress(self, requirement_type: str, current_value: float) -> None:
        """
        Update progress for achievements without triggering unlock check

        Args:
            requirement_type: Type of requirement to update
            current_value: Current progress value
        """
        for achievement in self.achievements.values():
            if achievement.requirement_type == requirement_type and not achievement.unlocked:
                achievement.progress = min(current_value, achievement.target)
        self._save_achievements()

    def get_all_achievements(self) -> List[Achievement]:
        """Get all achievements"""
        return list(self.achievements.values())

    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get all unlocked achievements"""
        return [
            achievement for achievement in self.achievements.values()
            if achievement.unlocked
        ]

    def get_locked_achievements(self) -> List[Achievement]:
        """Get all locked achievements"""
        return [
            achievement for achievement in self.achievements.values()
            if not achievement.unlocked
        ]

    def get_achievements_by_category(self, category: str) -> List[Achievement]:
        """Get achievements filtered by category"""
        return [
            achievement for achievement in self.achievements.values()
            if achievement.category == category
        ]

    def get_categories(self) -> Dict[str, Dict]:
        """Get all achievement categories with their info"""
        return ACHIEVEMENT_CATEGORIES.copy()

    def get_total_points(self) -> int:
        """Get total points from unlocked achievements"""
        return sum(
            achievement.points
            for achievement in self.achievements.values()
            if achievement.unlocked
        )

    def get_user_title(self) -> str:
        """Get user title based on total points"""
        total_points = self.get_total_points()
        title = "时间新手"
        for threshold, level_title in sorted(TITLE_LEVELS.items()):
            if total_points >= threshold:
                title = level_title
        return title

    def get_statistics(self) -> Dict:
        """Get comprehensive achievement statistics"""
        all_achievements = self.get_all_achievements()
        unlocked = self.get_unlocked_achievements()

        # Rarity counts
        rarity_counts = {
            'common': 0,
            'rare': 0,
            'epic': 0,
            'legendary': 0
        }
        for achievement in unlocked:
            rarity_counts[achievement.rarity] = rarity_counts.get(achievement.rarity, 0) + 1

        # Category counts
        category_stats = {}
        for category_id in ACHIEVEMENT_CATEGORIES:
            category_achievements = self.get_achievements_by_category(category_id)
            category_unlocked = [a for a in category_achievements if a.unlocked]
            category_stats[category_id] = {
                'total': len(category_achievements),
                'unlocked': len(category_unlocked),
                'percentage': len(category_unlocked) / len(category_achievements) * 100 if category_achievements else 0
            }

        return {
            'total_achievements': len(all_achievements),
            'unlocked_count': len(unlocked),
            'unlock_percentage': len(unlocked) / len(all_achievements) * 100 if all_achievements else 0,
            'rarity_counts': rarity_counts,
            'category_stats': category_stats,
            'total_points': self.get_total_points(),
            'user_title': self.get_user_title()
        }
