# statistics_gui.py 国际化方案

## 文件信息
- **文件**: statistics_gui.py
- **行数**: 666行
- **中文字符串**: 63个
- **去重后**: 51个唯一翻译键

## 字符串统计

### 总体统计
- **原始字符串**: 63个
- **去重后**: 51个唯一翻译键
- **重复字符串**: 12个（如"已完成"、"任务名称"等）

### 分类详情

#### 1. 窗口和按钮 (statistics命名空间)
- 窗口标题
- 操作按钮（刷新、导出）

#### 2. 标签页标题 (statistics.tab子空间)
- 今日统计
- 本周统计
- 本月统计
- 任务分类

#### 3. 统计卡片 (statistics.card子空间)
- 卡片标题（总任务数、已完成等）
- 完成率标题

#### 4. 表格列标题 (statistics.table子空间)
- 任务详情表格列
- 每日统计表格列

#### 5. 状态文本 (statistics.status子空间)
- 任务状态（已完成、进行中、未开始）
- 时长单位

#### 6. 消息提示 (statistics.message子空间)
- 加载提示
- 导出成功/失败消息

#### 7. 错误消息 (statistics.error子空间)
- 加载失败
- 导出失败

## 翻译键规划

### statistics - 窗口和按钮 (3个)

| 原文 | 翻译键 | 使用次数 |
|------|--------|---------|
| 📊 任务统计报告 - GaiYa每日进度条 | statistics.window_title_full | 1 |
| 📊 任务统计报告 | statistics.window_title | 1 |
| 🔄 刷新 | statistics.btn_refresh | 1 |
| 📥 导出CSV | statistics.btn_export_csv | 1 |

### statistics.tab - 标签页标题 (4个)

| 原文 | 翻译键 |
|------|--------|
| 📅 今日统计 | statistics.tab.today |
| 📊 本周统计 | statistics.tab.weekly |
| 📈 本月统计 | statistics.tab.monthly |
| 📋 任务分类统计(历史累计) | statistics.tab.category_history |
| 📋 任务分类 | statistics.tab.category |

### statistics.card - 统计卡片 (8个)

| 原文 | 翻译键 |
|------|--------|
| 今日完成率 | statistics.card.today_completion |
| 本周完成率 | statistics.card.weekly_completion |
| 本月完成率 | statistics.card.monthly_completion |
| 总任务数 | statistics.card.total_tasks |
| 已完成 | statistics.card.completed |
| 进行中 | statistics.card.in_progress |
| 未开始 | statistics.card.not_started |
| 完成时长 | statistics.card.completed_duration |

### statistics.table - 表格列标题 (11个)

| 原文 | 翻译键 |
|------|--------|
| 今日任务详情 | statistics.table.today_task_details |
| 任务名称 | statistics.table.task_name |
| 开始时间 | statistics.table.start_time |
| 结束时间 | statistics.table.end_time |
| 时长(分钟) | statistics.table.duration_minutes |
| 状态 | statistics.table.status |
| 每日完成情况 | statistics.table.daily_completion |
| 每日统计 | statistics.table.daily_stats |
| 日期 | statistics.table.date |
| 星期 | statistics.table.weekday |
| 任务数 | statistics.table.task_count |
| 完成数 | statistics.table.completed_count |
| 计划时长(h) | statistics.table.planned_hours |
| 完成率(%) | statistics.table.completion_rate |
| 完成次数 | statistics.table.completion_times |
| 总时长(小时) | statistics.table.total_hours |
| 颜色 | statistics.table.color |

### statistics.status - 状态文本 (3个)

| 原文 | 翻译键 |
|------|--------|
| ✅ 已完成 | statistics.status.completed |
| ⏳ 进行中 | statistics.status.in_progress |
| ⏰ 未开始 | statistics.status.not_started |

### statistics.message - 消息提示 (5个)

| 原文 | 翻译键 |
|------|--------|
| 开始加载统计数据... | statistics.message.loading_start |
| 统计数据加载完成 | statistics.message.loading_complete |
| 导出统计数据 | statistics.message.export_dialog_title |
| CSV文件 (*.csv) | statistics.message.csv_file_filter |
| 导出成功 | statistics.message.export_success_title |
| 统计数据已导出到:\n{file_path} | statistics.message.export_success_message |

### statistics.error - 错误消息 (5个)

| 原文 | 翻译键 |
|------|--------|
| 错误 | statistics.error.error_title |
| 加载统计数据失败: {e} | statistics.error.loading_failed_log |
| 加载统计数据失败:\n{str(e)} | statistics.error.loading_failed_message |
| 导出失败 | statistics.error.export_failed_title |
| 导出统计数据失败,请查看日志了解详情 | statistics.error.export_failed_simple |
| 导出统计数据失败: {e} | statistics.error.export_failed_log |
| 导出失败:\n{str(e)} | statistics.error.export_failed_message |

### 日志消息（不翻译）
- Line 661: "已应用主题到统计窗口: {theme.get(" - 调试日志

## 翻译键总结

### 命名空间统计
| 命名空间 | 翻译键数 | 主要用途 |
|---------|---------|---------|
| statistics | 4 | 窗口和按钮 |
| statistics.tab | 5 | 标签页标题 |
| statistics.card | 8 | 统计卡片 |
| statistics.table | 17 | 表格列标题 |
| statistics.status | 3 | 状态文本 |
| statistics.message | 6 | 消息提示 |
| statistics.error | 7 | 错误消息 |
| **总计** | **50** | - |

## 参数化翻译

需要参数的翻译键：
1. `statistics.message.export_success_message`: `{file_path}`
2. `statistics.error.loading_failed_log`: `{e}`
3. `statistics.error.loading_failed_message`: `{str(e)}`
4. `statistics.error.export_failed_log`: `{e}`
5. `statistics.error.export_failed_message`: `{str(e)}`

## 实施建议

### 分阶段实施

#### 第一阶段：基本UI (9个)
- statistics命名空间的所有键
- statistics.tab命名空间的所有键
- 预计工作量：20分钟

#### 第二阶段：统计卡片和表格 (25个)
- statistics.card命名空间
- statistics.table命名空间
- 预计工作量：30分钟

#### 第三阶段：状态和消息 (16个)
- statistics.status命名空间
- statistics.message命名空间
- statistics.error命名空间
- 预计工作量：25分钟

### 总预计工作量
- **翻译键添加**: 10分钟
- **代码自动替换**: 20分钟
- **手动修复**: 20分钟
- **验证和测试**: 10分钟
- **总计**: 1小时

## 复杂度评估

### 自动化难度
- **简单替换**: 约45个（单行字符串）
- **中等难度**: 约5个（带参数的字符串）
- **手动处理**: 约3个（复杂的多行消息）

### 预计自动化成功率
约90%（基于前面的经验）

## 特殊注意事项

### 1. Emoji图标
许多字符串包含emoji（📊、📅、🔄等），需要保留在翻译中

### 2. 单位标注
- "时长(分钟)" - 包含单位
- "完成率(%)" - 包含单位
- "计划时长(h)" - 包含单位
需要在翻译中保持清晰

### 3. 重复字符串
- "已完成" 出现3次（不同上下文）
- "任务名称" 出现2次
- "任务数"、"完成数" 各出现2次
- 可以复用同一个翻译键

### 4. 日志消息
Line 661的调试日志保持中文或改为英文均可

## 修改文件清单

- `statistics_gui.py`: 约50处修改
- `i18n/zh_CN.json`: 添加50个键
- `i18n/en_US.json`: 添加50个键
