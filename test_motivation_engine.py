"""Test script for Motivation Engine"""

import sys
import io
import logging
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from statistics_manager import StatisticsManager
from gaiya.core.goal_manager import GoalManager
from gaiya.core.achievement_manager import AchievementManager
from gaiya.core.motivation_engine import MotivationEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_motivation")

def main():
    print("\n" + "="*60)
    print("🧪 测试激励循环引擎")
    print("="*60 + "\n")

    # Initialize managers
    app_dir = Path(".")
    data_dir = app_dir / 'gaiya' / 'data'

    stats_manager = StatisticsManager(app_dir, logger)
    goal_manager = GoalManager(data_dir, logger)
    achievement_manager = AchievementManager(data_dir, logger)

    # Initialize motivation engine
    motivation_engine = MotivationEngine(
        goal_manager=goal_manager,
        achievement_manager=achievement_manager,
        stats_manager=stats_manager,
        logger=logger
    )

    print("📊 当前统计数据:")
    print(f"  今日完成任务: {motivation_engine._get_today_completed_tasks()}")
    print(f"  本周专注时长: {motivation_engine._get_weekly_focus_hours():.1f} 小时")
    print(f"  本周完成率: {motivation_engine._get_weekly_completion_rate():.1f}%")
    print(f"  连续使用天数: {motivation_engine._get_continuous_usage_days()}")
    print(f"  累计完成任务: {motivation_engine._get_total_completed_tasks()}")
    print(f"  累计专注时长: {motivation_engine._get_total_focus_hours():.1f} 小时")
    print()

    # Test creating a goal
    print("🎯 创建测试目标...")
    goal = goal_manager.create_goal(
        goal_type='daily_tasks',
        target_value=5
    )
    print(f"  ✅ 创建目标: 每日完成 5 个任务")
    print(f"  目标ID: {goal.goal_id}")
    print()

    # Test updating goals
    print("🔄 测试目标进度自动更新...")
    completed_goals = motivation_engine.update_goals_from_stats()
    print(f"  完成的目标数: {len(completed_goals)}")

    # Show goal progress
    active_goals = goal_manager.get_active_goals()
    print(f"\n  活跃目标数: {len(active_goals)}")
    for g in active_goals:
        info = g.get_info()
        print(f"    - {info['emoji']} {info['name']}: {info['progress_percentage']:.1f}% ({g.current_value}/{g.target_value})")
    print()

    # Test checking achievements
    print("🏆 测试成就解锁检测...")
    unlocked = motivation_engine.check_achievements()
    print(f"  新解锁成就数: {len(unlocked)}")

    # Show achievement stats
    all_achievements = achievement_manager.get_all_achievements()
    unlocked_achievements = achievement_manager.get_unlocked_achievements()
    locked_achievements = achievement_manager.get_locked_achievements()

    print(f"\n  总成就数: {len(all_achievements)}")
    print(f"  已解锁: {len(unlocked_achievements)}")
    print(f"  未解锁: {len(locked_achievements)}")

    if unlocked_achievements:
        print("\n  已解锁成就:")
        for ach in unlocked_achievements[:5]:  # 只显示前5个
            print(f"    {ach.emoji} {ach.name} [{ach.rarity}]")
    print()

    # Test full update
    print("🚀 测试完整激励系统更新...")
    result = motivation_engine.update_all()
    print(f"  完成目标数: {len(result['completed_goals'])}")
    print(f"  解锁成就数: {len(result['unlocked_achievements'])}")
    print()

    print("✅ 测试完成!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
