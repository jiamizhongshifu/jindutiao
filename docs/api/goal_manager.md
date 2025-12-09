# GoalManager API 文档

## 概述

GoalManager (目标管理器) 负责用户目标的创建、追踪、更新和持久化。支持三种目标类型:
- 每日任务目标 (`daily_tasks`)
- 每周专注时长目标 (`weekly_focus_hours`)
- 每周完成率目标 (`weekly_completion_rate`)

**文件路径**: `gaiya/core/goal_manager.py`

---

## 类: Goal

单个目标对象,表示用户设定的一个目标。

### 构造函数

```python
Goal(
    goal_id: str,
    goal_type: str,
    target_value: float,
    start_date: str,
    end_date: Optional[str] = None,
    status: str = 'active'
)
```

**参数**:
- `goal_id` (str): 唯一目标ID (UUID格式)
- `goal_type` (str): 目标类型
  - `'daily_tasks'`: 每日任务目标
  - `'weekly_focus_hours'`: 每周专注时长
  - `'weekly_completion_rate'`: 每周完成率
- `target_value` (float): 目标值 (如: 5个任务, 20小时, 80%)
- `start_date` (str): 开始日期 (YYYY-MM-DD格式)
- `end_date` (Optional[str]): 结束日期 (可选,用于限时目标)
- `status` (str): 目标状态 (`'active'` | `'completed'` | `'abandoned'`)

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `goal_id` | str | 目标唯一ID |
| `goal_type` | str | 目标类型 |
| `target_value` | float | 目标值 |
| `current_value` | float | 当前进度值 |
| `start_date` | str | 开始日期 |
| `end_date` | Optional[str] | 结束日期 |
| `status` | str | 目标状态 |
| `created_at` | str | 创建时间 (ISO格式) |
| `completed_at` | Optional[str] | 完成时间 |

### 方法

#### `get_progress_percentage() -> float`

获取目标进度百分比 (0-100)。

**返回**: 进度百分比,自动限制在100%以内

**示例**:
```python
goal = Goal(...)
goal.current_value = 3
goal.target_value = 5
print(goal.get_progress_percentage())  # 输出: 60.0
```

#### `is_completed() -> bool`

判断目标是否已完成。

**返回**: 当前值 >= 目标值时返回 True

**示例**:
```python
if goal.is_completed():
    print("目标已完成!")
```

#### `get_info() -> Dict`

获取目标完整信息 (包含元数据和进度)。

**返回**: 包含以下字段的字典:
- `goal_id`: 目标ID
- `name`: 目标名称 (中文)
- `emoji`: 目标图标
- `description`: 目标描述
- `unit`: 单位
- `target_value`: 目标值
- `current_value`: 当前值
- `progress_percentage`: 进度百分比
- `status`: 状态
- `is_completed`: 是否完成
- `start_date`: 开始日期
- `end_date`: 结束日期

#### `to_dict() -> Dict`

将目标对象序列化为字典 (用于持久化)。

#### `from_dict(data: Dict) -> Goal` (类方法)

从字典反序列化为Goal对象。

---

## 类: GoalManager

目标管理器,负责目标的CRUD操作和进度追踪。

### 构造函数

```python
GoalManager(data_dir: Path, logger: Optional[logging.Logger] = None)
```

**参数**:
- `data_dir` (Path): 数据存储目录 (存放 `goals.json`)
- `logger` (Optional[Logger]): 日志记录器 (可选)

**示例**:
```python
from pathlib import Path
import logging

data_dir = Path("./data")
logger = logging.getLogger("gaiya")
goal_manager = GoalManager(data_dir, logger)
```

### 方法

#### `create_goal(goal_type, target_value, start_date=None, end_date=None) -> Goal`

创建新目标。

**参数**:
- `goal_type` (str): 目标类型 (`'daily_tasks'` | `'weekly_focus_hours'` | `'weekly_completion_rate'`)
- `target_value` (float): 目标值
- `start_date` (Optional[str]): 开始日期 (默认: 今天)
- `end_date` (Optional[str]): 结束日期 (可选)

**返回**: 创建的Goal对象

**抛出**: `ValueError` - 当目标类型无效时

**示例**:
```python
# 创建每日任务目标: 每天完成5个任务
goal = goal_manager.create_goal(
    goal_type='daily_tasks',
    target_value=5.0
)

# 创建限时目标: 12月完成100小时专注
goal = goal_manager.create_goal(
    goal_type='weekly_focus_hours',
    target_value=100.0,
    start_date='2025-12-01',
    end_date='2025-12-31'
)
```

#### `get_active_goals() -> List[Goal]`

获取所有活跃目标 (status='active')。

**返回**: 活跃目标列表

**示例**:
```python
active_goals = goal_manager.get_active_goals()
for goal in active_goals:
    print(f"{goal.get_info()['name']}: {goal.get_progress_percentage():.1f}%")
```

#### `get_goal(goal_id: str) -> Optional[Goal]`

通过ID获取目标。

**参数**:
- `goal_id` (str): 目标ID

**返回**: Goal对象,如果不存在返回 None

#### `update_goal_progress(goal_id: str, current_value: float) -> bool`

更新目标进度。

**参数**:
- `goal_id` (str): 目标ID
- `current_value` (float): 当前进度值

**返回**: 如果目标刚好完成返回 True,否则返回 False

**示例**:
```python
# 更新今日完成任务数为3
just_completed = goal_manager.update_goal_progress(goal_id, 3.0)

if just_completed:
    print("🎉 目标刚刚完成!")
```

#### `delete_goal(goal_id: str)`

删除目标 (永久删除)。

**参数**:
- `goal_id` (str): 目标ID

#### `abandon_goal(goal_id: str)`

放弃目标 (标记为abandoned,不删除)。

**参数**:
- `goal_id` (str): 目标ID

#### `get_statistics() -> Dict`

获取目标统计信息。

**返回**: 包含以下字段的字典:
- `total_goals`: 总目标数
- `active_goals`: 活跃目标数
- `completed_goals`: 已完成目标数
- `completion_rate`: 完成率 (%)

**示例**:
```python
stats = goal_manager.get_statistics()
print(f"完成率: {stats['completion_rate']:.1f}%")
```

---

## 支持的目标类型

### 1. 每日任务目标 (`daily_tasks`)

**说明**: 每天完成指定数量的任务

**单位**: 个任务

**典型目标值**: 3-10

**示例**:
```python
goal = goal_manager.create_goal('daily_tasks', 5)
# 目标: 每天完成5个任务
```

### 2. 每周专注时长 (`weekly_focus_hours`)

**说明**: 每周累计专注时长达到目标

**单位**: 小时

**典型目标值**: 10-40

**示例**:
```python
goal = goal_manager.create_goal('weekly_focus_hours', 20)
# 目标: 每周专注20小时
```

### 3. 每周完成率 (`weekly_completion_rate`)

**说明**: 每周任务平均完成率达到目标

**单位**: 百分比 (%)

**典型目标值**: 60-100

**示例**:
```python
goal = goal_manager.create_goal('weekly_completion_rate', 80)
# 目标: 每周完成率达到80%
```

---

## 数据持久化

目标数据保存在 `{data_dir}/goals.json`:

```json
{
  "goals": [
    {
      "goal_id": "550e8400-e29b-41d4-a716-446655440000",
      "goal_type": "daily_tasks",
      "target_value": 5.0,
      "current_value": 3.0,
      "start_date": "2025-12-09",
      "end_date": null,
      "status": "active",
      "created_at": "2025-12-09T10:00:00",
      "completed_at": null
    }
  ],
  "last_updated": "2025-12-09T15:30:00"
}
```

---

## 完整使用示例

```python
from pathlib import Path
import logging
from gaiya.core.goal_manager import GoalManager

# 初始化
data_dir = Path("./data")
logger = logging.getLogger("gaiya")
goal_manager = GoalManager(data_dir, logger)

# 创建目标
goal = goal_manager.create_goal(
    goal_type='daily_tasks',
    target_value=5.0
)

print(f"创建目标: {goal.goal_id}")

# 获取活跃目标
active_goals = goal_manager.get_active_goals()
print(f"当前有 {len(active_goals)} 个活跃目标")

# 更新进度
just_completed = goal_manager.update_goal_progress(goal.goal_id, 3.0)
print(f"进度: {goal.get_progress_percentage():.1f}%")

# 完成目标
just_completed = goal_manager.update_goal_progress(goal.goal_id, 5.0)
if just_completed:
    print("🎉 目标完成!")

# 查看统计
stats = goal_manager.get_statistics()
print(f"总完成率: {stats['completion_rate']:.1f}%")
```

---

## 注意事项

1. **线程安全**: GoalManager 不是线程安全的,多线程环境需要外部加锁
2. **自动保存**: 所有修改操作 (create/update/delete) 会立即保存到文件
3. **目标类型**: 只支持预定义的三种目标类型,传入其他值会抛出 ValueError
4. **进度验证**: current_value 可以超过 target_value,但进度百分比最大显示100%
5. **状态转换**: 目标完成后状态自动变为 'completed',无法再次更新进度

---

**版本**: v1.0
**最后更新**: 2025-12-09
**作者**: GaiYa Team
