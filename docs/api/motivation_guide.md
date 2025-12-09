# 激励系统完整使用指南

## 概述

GaiYa激励系统是一个自动化的用户激励循环引擎,通过**目标管理 (GoalManager)** + **成就系统 (AchievementManager)** + **激励引擎 (MotivationEngine)** 三大模块协同工作,自动追踪用户进度并触发激励反馈。

**核心特性**:
- ✅ 自动化: 无需手动更新,根据统计数据自动计算
- 🎯 多维度: 支持任务数、专注时长、完成率等多种目标
- 🏆 成就系统: 11个预定义成就,4种稀有度
- 🔄 实时反馈: 目标完成和成就解锁即时通知

---

## 快速开始

### 1. 初始化激励系统

```python
from pathlib import Path
import logging
from gaiya.core.goal_manager import GoalManager
from gaiya.core.achievement_manager import AchievementManager
from gaiya.core.motivation_engine import MotivationEngine
from statistics_manager import StatisticsManager  # 你的统计管理器

# 设置数据目录
data_dir = Path("./data")
logger = logging.getLogger("gaiya")

# 初始化三大模块
goal_manager = GoalManager(data_dir, logger)
achievement_manager = AchievementManager(data_dir, logger)
stats_manager = StatisticsManager(data_dir, logger)

# 创建激励引擎
motivation_engine = MotivationEngine(
    goal_manager=goal_manager,
    achievement_manager=achievement_manager,
    stats_manager=stats_manager,
    logger=logger
)

print("✅ 激励系统初始化完成!")
```

### 2. 设置回调函数 (可选但推荐)

```python
def on_goal_completed(goal):
    """目标完成回调"""
    print(f"🎉 目标完成: {goal.get_info()['name']}")
    # 显示UI通知、播放音效等

def on_achievement_unlocked(achievement):
    """成就解锁回调"""
    print(f"🏆 解锁成就: {achievement.emoji} {achievement.name}")
    print(f"   {achievement.description}")
    # 显示成就弹窗、播放特效等

# 注册回调
motivation_engine.on_goal_completed = on_goal_completed
motivation_engine.on_achievement_unlocked = on_achievement_unlocked
```

### 3. 创建用户目标

```python
# 创建每日任务目标: 每天完成5个任务
daily_goal = goal_manager.create_goal(
    goal_type='daily_tasks',
    target_value=5.0
)

# 创建每周专注目标: 每周专注20小时
weekly_goal = goal_manager.create_goal(
    goal_type='weekly_focus_hours',
    target_value=20.0
)

print(f"✅ 创建了 {len(goal_manager.get_active_goals())} 个目标")
```

### 4. 定期自动更新

```python
# 在合适的时机调用 (如任务完成后、定时器触发)
result = motivation_engine.update_all()

print(f"目标完成: {len(result['completed_goals'])} 个")
print(f"成就解锁: {len(result['unlocked_achievements'])} 个")
```

---

## 使用场景

### 场景1: 用户完成任务时

```python
def on_task_completed(task):
    """任务完成时调用"""
    # 1. 更新统计数据 (你的statistics_manager)
    stats_manager.record_task_completion(task)

    # 2. 自动更新激励系统
    result = motivation_engine.update_all()

    # 3. 处理激励反馈
    if result['completed_goals']:
        # 显示目标完成庆祝动画
        pass

    if result['unlocked_achievements']:
        # 显示成就解锁通知
        pass
```

### 场景2: 每日刷新时

```python
import schedule

def daily_refresh():
    """每日0点执行"""
    # 更新所有目标进度
    completed_goals = motivation_engine.update_goals_from_stats()

    # 检查连续打卡成就
    unlocked = motivation_engine.check_achievements()

    if completed_goals or unlocked:
        # 发送每日激励总结通知
        pass

# 注册定时任务
schedule.every().day.at("00:00").do(daily_refresh)
```

### 场景3: 用户查看进度时

```python
def show_progress_dashboard():
    """显示进度仪表盘"""
    # 1. 目标进度
    active_goals = goal_manager.get_active_goals()
    for goal in active_goals:
        info = goal.get_info()
        print(f"{info['emoji']} {info['name']}: {info['progress_percentage']:.1f}%")

    # 2. 成就进度
    stats = achievement_manager.get_statistics()
    print(f"\n成就进度: {stats['unlocked_count']}/{stats['total_achievements']}")

    # 3. 待解锁成就
    locked = achievement_manager.get_locked_achievements()
    print(f"\n最近可解锁:")
    for achievement in locked[:3]:
        print(f"  {achievement.emoji} {achievement.name}")
```

---

## 进阶技巧

### 1. 目标生命周期管理

```python
# 创建限时目标 (如: 12月挑战)
goal = goal_manager.create_goal(
    goal_type='weekly_focus_hours',
    target_value=100.0,
    start_date='2025-12-01',
    end_date='2025-12-31'
)

# 检查目标是否过期
from datetime import date
if goal.end_date and date.today().isoformat() > goal.end_date:
    if goal.is_completed():
        print("✅ 挑战成功!")
    else:
        goal_manager.abandon_goal(goal.goal_id)
        print("⏰ 挑战失败,已放弃")
```

### 2. 自定义成就触发逻辑

```python
# 在MotivationEngine基础上扩展
class ExtendedMotivationEngine(MotivationEngine):
    def check_custom_achievements(self):
        """检查自定义成就"""
        # 例如: 检查用户是否达到特定里程碑
        if self._is_early_bird():
            # 触发"早起的鸟儿"成就
            pass

    def _is_early_bird(self):
        """检测用户是否在6点前完成任务"""
        # 自定义逻辑
        return False
```

### 3. 成就稀有度UI展示

```python
RARITY_COLORS = {
    'common': '#9E9E9E',    # 灰色
    'rare': '#2196F3',      # 蓝色
    'epic': '#9C27B0',      # 紫色
    'legendary': '#FF9800'  # 橙色
}

RARITY_NAMES = {
    'common': '普通',
    'rare': '稀有',
    'epic': '史诗',
    'legendary': '传说'
}

def render_achievement(achievement):
    """渲染成就卡片"""
    color = RARITY_COLORS[achievement.rarity]
    rarity_name = RARITY_NAMES[achievement.rarity]

    # 使用对应颜色渲染UI
    pass
```

---

## 数据流图

```
┌─────────────────┐
│ StatisticsManager│  (你的统计系统)
└────────┬────────┘
         │ 提供统计数据
         ↓
┌─────────────────┐
│ MotivationEngine │  ← 核心引擎
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌──────┐  ┌──────────┐
│ Goal │  │Achievement│
│Manager│  │ Manager  │
└───┬──┘  └────┬─────┘
    │          │
    ↓          ↓
 goals.json  achievements.json
```

**工作流程**:
1. `MotivationEngine.update_all()` 被调用
2. 从 `StatisticsManager` 读取最新统计数据
3. 更新 `GoalManager` 中的目标进度
4. 检测 `AchievementManager` 的成就解锁条件
5. 触发回调通知UI
6. 自动保存到JSON文件

---

## 性能优化建议

### 1. 批量更新而非实时更新

```python
# ❌ 不推荐: 每次任务完成都更新
def on_task_completed(task):
    motivation_engine.update_all()  # 频繁I/O

# ✅ 推荐: 批量更新或定时更新
def on_task_batch_completed(tasks):
    motivation_engine.update_all()  # 减少更新频率
```

### 2. 缓存目标信息

```python
class CachedMotivationEngine:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._goal_info_cache = {}

    def get_goal_info(self, goal_id):
        if goal_id not in self._goal_info_cache:
            goal = self.goal_manager.get_goal(goal_id)
            self._goal_info_cache[goal_id] = goal.get_info()
        return self._goal_info_cache[goal_id]
```

### 3. 异步处理成就检查

```python
import asyncio

async def update_motivation_async():
    """异步更新激励系统"""
    result = await asyncio.to_thread(motivation_engine.update_all)
    # 处理结果
```

---

## 常见问题

### Q1: 如何重置所有目标和成就?

```python
# 删除数据文件
import os
os.remove("data/goals.json")
os.remove("data/achievements.json")

# 重新初始化
goal_manager = GoalManager(data_dir, logger)
achievement_manager = AchievementManager(data_dir, logger)
```

### Q2: 目标完成后如何再次使用?

目标完成后状态变为 `completed`,无法再次更新。需要创建新目标:

```python
# 获取旧目标信息
old_goal = goal_manager.get_goal(goal_id)

# 创建相同类型的新目标
new_goal = goal_manager.create_goal(
    goal_type=old_goal.goal_type,
    target_value=old_goal.target_value
)
```

### Q3: 如何手动触发成就解锁?

```python
# 直接调用 check_and_unlock
newly_unlocked = achievement_manager.check_and_unlock(
    requirement_type='total_tasks_completed',
    current_value=100.0
)
```

### Q4: 连续打卡中断后如何处理?

连续打卡成就检测中断后会重新计算:
- 已解锁的成就不会失去
- 未解锁的成就从0开始重新计算

---

## API参考

详细API文档:
- [GoalManager API](./goal_manager.md)
- [AchievementManager API](./achievement_manager.md)
- [MotivationEngine API](./motivation_engine.md)
- [AppRecommender API](./app_recommender.md)

---

## 示例项目

完整集成示例见: [tests/test_integration.py](../../test_integration.py)

---

**版本**: v1.0
**最后更新**: 2025-12-09
**作者**: GaiYa Team
