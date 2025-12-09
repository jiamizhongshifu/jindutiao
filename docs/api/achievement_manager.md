# AchievementManager API 文档

## 概述

AchievementManager (成就管理器) 负责成就系统的管理,包括成就定义、解锁检测和持久化。内置11个预定义成就,支持4种稀有度等级。

**文件路径**: `gaiya/core/achievement_manager.py`

---

## 类: Achievement

单个成就对象,表示一个可解锁的成就。

### 构造函数

```python
Achievement(
    achievement_id: str,
    name: str,
    description: str,
    emoji: str,
    category: str,
    requirement_type: str,
    requirement_value: float,
    rarity: str = 'common'
)
```

**参数**:
- `achievement_id` (str): 唯一成就ID
- `name` (str): 成就名称 (如: "初露锋芒")
- `description` (str): 成就描述 (如: "连续使用GaiYa 3天")
- `emoji` (str): 成就图标 (如: "🔥")
- `category` (str): 成就类别 (`'streak'` | `'milestone'` | `'performance'`)
- `requirement_type` (str): 需求类型 (详见下文)
- `requirement_value` (float): 解锁所需值
- `rarity` (str): 稀有度 (`'common'` | `'rare'` | `'epic'` | `'legendary'`)

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `achievement_id` | str | 成就唯一ID |
| `name` | str | 成就名称 |
| `description` | str | 成就描述 |
| `emoji` | str | 成就图标 |
| `category` | str | 成就类别 |
| `requirement_type` | str | 需求类型 |
| `requirement_value` | float | 解锁所需值 |
| `rarity` | str | 稀有度 |
| `unlocked` | bool | 是否已解锁 |
| `unlocked_at` | Optional[str] | 解锁时间 (ISO格式) |

### 方法

#### `to_dict() -> Dict`

将成就对象序列化为字典。

#### `from_dict(data: Dict) -> Achievement` (类方法)

从字典反序列化为Achievement对象。

---

## 类: AchievementManager

成就管理器,负责成就的解锁检测和持久化。

### 构造函数

```python
AchievementManager(data_dir: Path, logger: Optional[logging.Logger] = None)
```

**参数**:
- `data_dir` (Path): 数据存储目录 (存放 `achievements.json`)
- `logger` (Optional[Logger]): 日志记录器 (可选)

**示例**:
```python
from pathlib import Path
import logging

data_dir = Path("./data")
logger = logging.getLogger("gaiya")
achievement_manager = AchievementManager(data_dir, logger)
```

### 方法

#### `check_and_unlock(requirement_type: str, current_value: float) -> List[Achievement]`

检查并解锁符合条件的成就。

**参数**:
- `requirement_type` (str): 需求类型 (详见"需求类型"章节)
- `current_value` (float): 当前值

**返回**: 新解锁的成就列表

**示例**:
```python
# 检查连续打卡成就
newly_unlocked = achievement_manager.check_and_unlock(
    requirement_type='continuous_days',
    current_value=7.0
)

for achievement in newly_unlocked:
    print(f"🏆 解锁成就: {achievement.name}")
    # 输出: 🏆 解锁成就: 初露锋芒
    # 输出: 🏆 解锁成就: 坚持不懈
```

#### `get_all_achievements() -> List[Achievement]`

获取所有成就 (包括已解锁和未解锁)。

**返回**: 成就列表 (11个预定义成就)

#### `get_unlocked_achievements() -> List[Achievement]`

获取所有已解锁的成就。

**返回**: 已解锁成就列表

**示例**:
```python
unlocked = achievement_manager.get_unlocked_achievements()
print(f"已解锁 {len(unlocked)} 个成就")
```

#### `get_locked_achievements() -> List[Achievement]`

获取所有未解锁的成就。

**返回**: 未解锁成就列表

#### `get_statistics() -> Dict`

获取成就统计信息。

**返回**: 包含以下字段的字典:
- `total_achievements`: 总成就数 (11)
- `unlocked_count`: 已解锁成就数
- `unlock_percentage`: 解锁百分比
- `rarity_counts`: 各稀有度解锁数量
  - `common`: 普通成就解锁数
  - `rare`: 稀有成就解锁数
  - `epic`: 史诗成就解锁数
  - `legendary`: 传说成就解锁数

**示例**:
```python
stats = achievement_manager.get_statistics()
print(f"解锁进度: {stats['unlock_percentage']:.1f}%")
print(f"传说成就: {stats['rarity_counts']['legendary']}/1")
```

---

## 预定义成就列表

### 连续打卡成就 (Streak)

| ID | 名称 | 描述 | 需求 | 稀有度 |
|----|------|------|------|--------|
| `streak_3_days` | 初露锋芒 🔥 | 连续使用GaiYa 3天 | 3天 | common |
| `streak_7_days` | 坚持不懈 💪 | 连续使用GaiYa 7天 | 7天 | rare |
| `streak_30_days` | 习惯养成大师 👑 | 连续使用GaiYa 30天 | 30天 | epic |

### 任务完成里程碑 (Milestone - Tasks)

| ID | 名称 | 描述 | 需求 | 稀有度 |
|----|------|------|------|--------|
| `tasks_10` | 新手上路 📝 | 累计完成10个任务 | 10个 | common |
| `tasks_100` | 任务达人 ⭐ | 累计完成100个任务 | 100个 | rare |
| `tasks_500` | 生产力机器 🚀 | 累计完成500个任务 | 500个 | epic |

### 专注时长里程碑 (Milestone - Focus)

| ID | 名称 | 描述 | 需求 | 稀有度 |
|----|------|------|------|--------|
| `focus_10_hours` | 专注新手 ⏰ | 累计专注10小时 | 10小时 | common |
| `focus_100_hours` | 深度工作者 🎯 | 累计专注100小时 | 100小时 | rare |
| `focus_500_hours` | 时间管理大师 🏆 | 累计专注500小时 | 500小时 | legendary |

### 表现成就 (Performance)

| ID | 名称 | 描述 | 需求 | 稀有度 |
|----|------|------|------|--------|
| `perfect_day` | 完美一天 💯 | 单日任务完成率达到100% | 100% | rare |
| `perfect_week` | 完美一周 🌟 | 一周内所有任务全部完成 | 100% | epic |

---

## 需求类型 (Requirement Types)

成就解锁需要满足特定条件,通过 `requirement_type` 区分:

### 1. `continuous_days` - 连续使用天数

**说明**: 从今天往前计算连续有完成任务的天数

**使用场景**: 连续打卡成就

**示例**:
```python
# 检查用户是否达到3天连续打卡
achievement_manager.check_and_unlock('continuous_days', 3.0)
```

### 2. `total_tasks_completed` - 累计完成任务数

**说明**: 所有时间累计完成的任务总数

**使用场景**: 任务完成里程碑

**示例**:
```python
# 检查用户是否累计完成100个任务
achievement_manager.check_and_unlock('total_tasks_completed', 100.0)
```

### 3. `total_focus_hours` - 累计专注时长 (小时)

**说明**: 所有时间累计的专注时长 (单位: 小时)

**使用场景**: 专注时长里程碑

**示例**:
```python
# 检查用户是否累计专注100小时
achievement_manager.check_and_unlock('total_focus_hours', 100.0)
```

### 4. `daily_completion_rate` - 每日完成率 (%)

**说明**: 当日任务完成率

**使用场景**: 单日完美表现

**示例**:
```python
# 检查今日是否达到100%完成率
achievement_manager.check_and_unlock('daily_completion_rate', 100.0)
```

### 5. `weekly_completion_rate` - 每周完成率 (%)

**说明**: 本周平均任务完成率

**使用场景**: 周度完美表现

**示例**:
```python
# 检查本周是否达到100%完成率
achievement_manager.check_and_unlock('weekly_completion_rate', 100.0)
```

---

## 成就分类

### Streak (连续打卡)

奖励用户持续使用应用的行为,培养习惯。

**特点**:
- 需要连续每天都有完成任务
- 中断后重新计算
- 解锁难度递增

### Milestone (里程碑)

奖励用户的累计成就,展现长期努力。

**特点**:
- 累计统计,永不清零
- 解锁后不会失去
- 分为任务数和专注时长两类

### Performance (表现)

奖励用户的卓越表现,鼓励追求完美。

**特点**:
- 要求高完成率
- 可重复触发
- 稀有度较高

---

## 稀有度系统

成就按稀有度分为4个等级:

| 稀有度 | 英文 | 说明 | 颜色建议 | 数量 |
|--------|------|------|----------|------|
| 普通 | common | 容易获得,入门级成就 | 灰色/白色 | 3个 |
| 稀有 | rare | 需要一定努力 | 蓝色 | 4个 |
| 史诗 | epic | 需要长期坚持 | 紫色 | 3个 |
| 传说 | legendary | 极难获得,顶级成就 | 橙色/金色 | 1个 |

---

## 数据持久化

成就解锁数据保存在 `{data_dir}/achievements.json`:

```json
{
  "unlocked": [
    {
      "achievement_id": "streak_3_days",
      "unlocked_at": "2025-12-09T10:00:00"
    },
    {
      "achievement_id": "tasks_10",
      "unlocked_at": "2025-12-08T15:30:00"
    }
  ],
  "last_updated": "2025-12-09T15:30:00"
}
```

**注意**: 只保存解锁信息,成就定义在代码中 (`ACHIEVEMENTS`常量)。

---

## 完整使用示例

```python
from pathlib import Path
import logging
from gaiya.core.achievement_manager import AchievementManager

# 初始化
data_dir = Path("./data")
logger = logging.getLogger("gaiya")
achievement_manager = AchievementManager(data_dir, logger)

# 查看所有成就
all_achievements = achievement_manager.get_all_achievements()
print(f"共有 {len(all_achievements)} 个成就")

# 检查连续打卡成就
newly_unlocked = achievement_manager.check_and_unlock(
    requirement_type='continuous_days',
    current_value=7.0
)

if newly_unlocked:
    for achievement in newly_unlocked:
        print(f"🎉 解锁成就: {achievement.emoji} {achievement.name}")
        print(f"   {achievement.description}")

# 查看解锁进度
stats = achievement_manager.get_statistics()
print(f"\n解锁进度: {stats['unlocked_count']}/{stats['total_achievements']}")
print(f"完成度: {stats['unlock_percentage']:.1f}%")

# 查看各稀有度解锁情况
print("\n稀有度统计:")
for rarity, count in stats['rarity_counts'].items():
    print(f"  {rarity}: {count}")

# 查看未解锁的成就 (作为目标展示)
locked = achievement_manager.get_locked_achievements()
print(f"\n待解锁成就: {len(locked)} 个")
for achievement in locked[:3]:  # 显示前3个
    print(f"  {achievement.emoji} {achievement.name}")
    print(f"    需求: {achievement.requirement_value} {achievement.description}")
```

---

## 扩展成就

可以通过修改 `ACHIEVEMENTS` 常量添加自定义成就:

```python
class AchievementManager:
    ACHIEVEMENTS = [
        # 添加自定义成就
        {
            'achievement_id': 'custom_achievement',
            'name': '自定义成就',
            'description': '达到特定条件',
            'emoji': '✨',
            'category': 'milestone',
            'requirement_type': 'total_tasks_completed',
            'requirement_value': 50,
            'rarity': 'rare'
        },
        # ... 其他成就
    ]
```

**注意**: 修改后需要重启应用,且历史解锁数据仍然保留。

---

## 注意事项

1. **幂等性**: 同一个成就只会解锁一次,重复检查不会重复解锁
2. **批量解锁**: 单次检查可能解锁多个成就 (如连续7天同时解锁3天和7天成就)
3. **自动保存**: 解锁成就时自动保存到文件
4. **只增不减**: 成就一旦解锁无法撤销 (除非手动修改JSON文件)
5. **时间戳**: 解锁时间使用UTC时区的ISO 8601格式

---

**版本**: v1.0
**最后更新**: 2025-12-09
**作者**: GaiYa Team
