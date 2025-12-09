"""
Achievement System - Gamification and user motivation

Tracks user achievements and unlocks badges:
- Milestone-based achievements
- Streak-based achievements
- Performance-based achievements
- Achievement unlocking notifications

Author: GaiYa Team
Date: 2025-12-09
Version: 1.0
"""

import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, date
from pathlib import Path


class Achievement:
    """
    Single Achievement Definition

    Represents an achievement that can be unlocked
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
        rarity: str = 'common'
    ):
        """
        Initialize Achievement

        Args:
            achievement_id: Unique achievement ID
            name: Achievement name
            description: Achievement description
            emoji: Achievement emoji icon
            category: Achievement category (streak/milestone/performance)
            requirement_type: Type of requirement (e.g., 'continuous_days', 'total_tasks')
            requirement_value: Value needed to unlock
            rarity: Achievement rarity (common/rare/epic/legendary)
        """
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.emoji = emoji
        self.category = category
        self.requirement_type = requirement_type
        self.requirement_value = requirement_value
        self.rarity = rarity
        self.unlocked = False
        self.unlocked_at = None

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
            'unlocked': self.unlocked,
            'unlocked_at': self.unlocked_at
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
            rarity=data.get('rarity', 'common')
        )
        achievement.unlocked = data.get('unlocked', False)
        achievement.unlocked_at = data.get('unlocked_at')
        return achievement


class AchievementManager:
    """
    Achievement Management System

    Manages achievement definitions, unlocking, and persistence
    """

    # Predefined achievements
    ACHIEVEMENTS = [
        # Streak achievements (连续打卡)
        {
            'achievement_id': 'streak_3_days',
            'name': '初露锋芒',
            'description': '连续使用GaiYa 3天',
            'emoji': '🔥',
            'category': 'streak',
            'requirement_type': 'continuous_days',
            'requirement_value': 3,
            'rarity': 'common'
        },
        {
            'achievement_id': 'streak_7_days',
            'name': '坚持不懈',
            'description': '连续使用GaiYa 7天',
            'emoji': '💪',
            'category': 'streak',
            'requirement_type': 'continuous_days',
            'requirement_value': 7,
            'rarity': 'rare'
        },
        {
            'achievement_id': 'streak_30_days',
            'name': '习惯养成大师',
            'description': '连续使用GaiYa 30天',
            'emoji': '👑',
            'category': 'streak',
            'requirement_type': 'continuous_days',
            'requirement_value': 30,
            'rarity': 'epic'
        },

        # Task completion milestones (任务完成里程碑)
        {
            'achievement_id': 'tasks_10',
            'name': '新手上路',
            'description': '累计完成10个任务',
            'emoji': '📝',
            'category': 'milestone',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 10,
            'rarity': 'common'
        },
        {
            'achievement_id': 'tasks_100',
            'name': '任务达人',
            'description': '累计完成100个任务',
            'emoji': '⭐',
            'category': 'milestone',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 100,
            'rarity': 'rare'
        },
        {
            'achievement_id': 'tasks_500',
            'name': '生产力机器',
            'description': '累计完成500个任务',
            'emoji': '🚀',
            'category': 'milestone',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 500,
            'rarity': 'epic'
        },

        # Focus time milestones (专注时长里程碑)
        {
            'achievement_id': 'focus_10_hours',
            'name': '专注新手',
            'description': '累计专注10小时',
            'emoji': '⏰',
            'category': 'milestone',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 10,
            'rarity': 'common'
        },
        {
            'achievement_id': 'focus_100_hours',
            'name': '深度工作者',
            'description': '累计专注100小时',
            'emoji': '🎯',
            'category': 'milestone',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 100,
            'rarity': 'rare'
        },
        {
            'achievement_id': 'focus_500_hours',
            'name': '时间管理大师',
            'description': '累计专注500小时',
            'emoji': '🏆',
            'category': 'milestone',
            'requirement_type': 'total_focus_hours',
            'requirement_value': 500,
            'rarity': 'legendary'
        },

        # Performance achievements (表现成就)
        {
            'achievement_id': 'perfect_day',
            'name': '完美一天',
            'description': '单日任务完成率达到100%',
            'emoji': '💯',
            'category': 'performance',
            'requirement_type': 'daily_completion_rate',
            'requirement_value': 100,
            'rarity': 'rare'
        },
        {
            'achievement_id': 'perfect_week',
            'name': '完美一周',
            'description': '一周内所有任务全部完成',
            'emoji': '🌟',
            'category': 'performance',
            'requirement_type': 'weekly_completion_rate',
            'requirement_value': 100,
            'rarity': 'epic'
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
                rarity=achievement_data.get('rarity', 'common')
            )
            self.achievements[achievement.achievement_id] = achievement

    def _load_achievements(self):
        """Load unlocked achievements from JSON file"""
        try:
            if self.achievements_file.exists():
                with open(self.achievements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                unlocked_achievements = data.get('unlocked', [])
                for unlocked_data in unlocked_achievements:
                    achievement_id = unlocked_data['achievement_id']
                    if achievement_id in self.achievements:
                        self.achievements[achievement_id].unlocked = True
                        self.achievements[achievement_id].unlocked_at = unlocked_data.get('unlocked_at')

                self.logger.info(f"Loaded {len(unlocked_achievements)} unlocked achievements")

        except Exception as e:
            self.logger.error(f"Failed to load achievements: {e}")

    def _save_achievements(self):
        """Save unlocked achievements to JSON file"""
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

            data = {
                'unlocked': unlocked,
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
        current_value: float
    ) -> List[Achievement]:
        """
        Check if any achievements should be unlocked

        Args:
            requirement_type: Type of requirement to check
            current_value: Current value of the requirement

        Returns:
            List of newly unlocked achievements
        """
        newly_unlocked = []

        for achievement in self.achievements.values():
            # Skip if already unlocked
            if achievement.unlocked:
                continue

            # Check if requirement matches and value is sufficient
            if (achievement.requirement_type == requirement_type and
                    current_value >= achievement.requirement_value):

                achievement.unlocked = True
                achievement.unlocked_at = datetime.now().isoformat()
                newly_unlocked.append(achievement)

                self.logger.info(
                    f"Achievement unlocked: {achievement.name} ({achievement.achievement_id})"
                )

        if newly_unlocked:
            self._save_achievements()

        return newly_unlocked

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

    def get_statistics(self) -> Dict:
        """Get achievement statistics"""
        all_achievements = self.get_all_achievements()
        unlocked = self.get_unlocked_achievements()

        rarity_counts = {
            'common': 0,
            'rare': 0,
            'epic': 0,
            'legendary': 0
        }

        for achievement in unlocked:
            rarity_counts[achievement.rarity] = rarity_counts.get(achievement.rarity, 0) + 1

        return {
            'total_achievements': len(all_achievements),
            'unlocked_count': len(unlocked),
            'unlock_percentage': len(unlocked) / len(all_achievements) * 100 if all_achievements else 0,
            'rarity_counts': rarity_counts
        }
