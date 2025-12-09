"""
Goal Management System - User goal tracking and motivation

Manages user-defined goals and tracks progress:
- Daily task completion goals
- Weekly focus time goals
- Weekly completion rate goals
- Goal progress tracking
- Goal completion detection

Author: GaiYa Team
Date: 2025-12-09
Version: 1.0
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from pathlib import Path
import uuid


class Goal:
    """
    Single Goal Object

    Represents a user-defined goal with progress tracking
    """

    GOAL_TYPES = {
        'daily_tasks': {
            'name': '每日任务目标',
            'unit': '个任务',
            'description': '每天完成指定数量的任务',
            'default_target': 5,
            'emoji': '📋'
        },
        'weekly_focus_hours': {
            'name': '每周专注时长',
            'unit': '小时',
            'description': '每周累计专注时长达到目标',
            'default_target': 20,
            'emoji': '⏱️'
        },
        'weekly_completion_rate': {
            'name': '每周完成率',
            'unit': '%',
            'description': '每周任务平均完成率达到目标',
            'default_target': 80,
            'emoji': '🎯'
        }
    }

    def __init__(
        self,
        goal_id: str,
        goal_type: str,
        target_value: float,
        start_date: str,
        end_date: Optional[str] = None,
        status: str = 'active'
    ):
        """
        Initialize Goal

        Args:
            goal_id: Unique goal ID
            goal_type: Type of goal (daily_tasks/weekly_focus_hours/weekly_completion_rate)
            target_value: Target value to achieve
            start_date: Goal start date (YYYY-MM-DD)
            end_date: Goal end date (optional, for time-limited goals)
            status: Goal status (active/completed/abandoned)
        """
        self.goal_id = goal_id
        self.goal_type = goal_type
        self.target_value = target_value
        self.current_value = 0.0
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.completed_at = None

    def to_dict(self) -> Dict:
        """Convert goal to dictionary"""
        return {
            'goal_id': self.goal_id,
            'goal_type': self.goal_type,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Goal':
        """Create goal from dictionary"""
        goal = cls(
            goal_id=data['goal_id'],
            goal_type=data['goal_type'],
            target_value=data['target_value'],
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            status=data.get('status', 'active')
        )
        goal.current_value = data.get('current_value', 0.0)
        goal.created_at = data.get('created_at', datetime.now().isoformat())
        goal.completed_at = data.get('completed_at')
        return goal

    def get_progress_percentage(self) -> float:
        """Get progress percentage (0-100)"""
        if self.target_value == 0:
            return 0.0

        progress = (self.current_value / self.target_value) * 100
        return min(progress, 100.0)

    def is_completed(self) -> bool:
        """Check if goal is completed"""
        return self.current_value >= self.target_value

    def get_info(self) -> Dict:
        """Get goal information with metadata"""
        goal_meta = self.GOAL_TYPES.get(self.goal_type, {})

        return {
            'goal_id': self.goal_id,
            'name': goal_meta.get('name', 'Unknown Goal'),
            'emoji': goal_meta.get('emoji', '🎯'),
            'description': goal_meta.get('description', ''),
            'unit': goal_meta.get('unit', ''),
            'target_value': self.target_value,
            'current_value': self.current_value,
            'progress_percentage': self.get_progress_percentage(),
            'status': self.status,
            'is_completed': self.is_completed(),
            'start_date': self.start_date,
            'end_date': self.end_date
        }


class GoalManager:
    """
    Goal Management System

    Handles goal creation, tracking, and persistence:
    - Create and manage user goals
    - Update goal progress based on statistics
    - Detect goal completion
    - Persist goals to JSON file
    """

    def __init__(self, data_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize Goal Manager

        Args:
            data_dir: Directory to store goals.json
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.data_dir = data_dir
        self.goals_file = data_dir / 'goals.json'

        self.goals: Dict[str, Goal] = {}
        self._load_goals()

    def _load_goals(self):
        """Load goals from JSON file"""
        try:
            if self.goals_file.exists():
                with open(self.goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for goal_data in data.get('goals', []):
                    goal = Goal.from_dict(goal_data)
                    self.goals[goal.goal_id] = goal

                self.logger.info(f"Loaded {len(self.goals)} goals from {self.goals_file}")
            else:
                self.logger.info("No existing goals file found, starting fresh")

        except Exception as e:
            self.logger.error(f"Failed to load goals: {e}")
            self.goals = {}

    def _save_goals(self):
        """Save goals to JSON file"""
        try:
            # Ensure data directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)

            data = {
                'goals': [goal.to_dict() for goal in self.goals.values()],
                'last_updated': datetime.now().isoformat()
            }

            with open(self.goals_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(self.goals)} goals to {self.goals_file}")

        except Exception as e:
            self.logger.error(f"Failed to save goals: {e}")

    def create_goal(
        self,
        goal_type: str,
        target_value: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Goal:
        """
        Create a new goal

        Args:
            goal_type: Type of goal
            target_value: Target value to achieve
            start_date: Start date (default: today)
            end_date: End date (optional)

        Returns:
            Created Goal object
        """
        if goal_type not in Goal.GOAL_TYPES:
            raise ValueError(f"Invalid goal type: {goal_type}")

        goal_id = str(uuid.uuid4())
        start_date = start_date or date.today().isoformat()

        goal = Goal(
            goal_id=goal_id,
            goal_type=goal_type,
            target_value=target_value,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )

        self.goals[goal_id] = goal
        self._save_goals()

        self.logger.info(f"Created goal: {goal_type} (target: {target_value})")
        return goal

    def get_active_goals(self) -> List[Goal]:
        """Get all active goals"""
        return [
            goal for goal in self.goals.values()
            if goal.status == 'active'
        ]

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get goal by ID"""
        return self.goals.get(goal_id)

    def update_goal_progress(self, goal_id: str, current_value: float) -> bool:
        """
        Update goal progress

        Args:
            goal_id: Goal ID
            current_value: Current progress value

        Returns:
            True if goal was just completed, False otherwise
        """
        goal = self.goals.get(goal_id)
        if not goal or goal.status != 'active':
            return False

        was_completed = goal.is_completed()
        goal.current_value = current_value

        # Check if goal just got completed
        just_completed = not was_completed and goal.is_completed()

        if just_completed:
            goal.status = 'completed'
            goal.completed_at = datetime.now().isoformat()
            self.logger.info(f"Goal completed: {goal.goal_type} ({goal.goal_id})")

        self._save_goals()
        return just_completed

    def delete_goal(self, goal_id: str):
        """Delete a goal"""
        if goal_id in self.goals:
            del self.goals[goal_id]
            self._save_goals()
            self.logger.info(f"Deleted goal: {goal_id}")

    def abandon_goal(self, goal_id: str):
        """Mark a goal as abandoned"""
        goal = self.goals.get(goal_id)
        if goal:
            goal.status = 'abandoned'
            self._save_goals()
            self.logger.info(f"Abandoned goal: {goal_id}")

    def get_statistics(self) -> Dict:
        """Get goal statistics"""
        all_goals = list(self.goals.values())
        active_goals = [g for g in all_goals if g.status == 'active']
        completed_goals = [g for g in all_goals if g.status == 'completed']

        return {
            'total_goals': len(all_goals),
            'active_goals': len(active_goals),
            'completed_goals': len(completed_goals),
            'completion_rate': len(completed_goals) / len(all_goals) * 100 if all_goals else 0
        }
