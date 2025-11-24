# create_notification_tab() 国际化方案

## 方法范围

- **主方法**: `create_notification_tab()` (lines 2750-2947, 198 lines)
- **相关方法**: 无（所有逻辑在主方法内）
- **总计**: 约198行代码

## 字符串统计

- **原始提取**: 25个中文字符串
- **文档字符串**: 1个（跳过）
- **用户可见字符串**: 24个
- **去重后**: 约18个唯一翻译键

## 翻译键规划

### 1. 分组标题 (Group Titles) - 5个

| 行号 | 原文 | 翻译键 | 变量名 |
|------|------|--------|--------|
| 2761 | ⚙️ 基础设置 | notification.basic_settings_title | basic_group |
| 2783 | ⏰ 提醒时机 | notification.reminder_timing_title | timing_group |
| 2789 | 🔔 任务开始前提醒 | notification.before_start_title | before_start_group |
| 2841 | 🔕 任务结束前提醒 | notification.before_end_title | before_end_group |
| 2895 | 🌙 免打扰时段 | notification.do_not_disturb_title | dnd_group |

### 2. 标签文本 (Labels) - 8个

| 行号 | 原文 | 翻译键 | 使用位置 |
|------|------|--------|--------|
| 2756 | 配置任务提醒通知,让您不会错过任何重要时刻 | notification.info_label | info_label |
| 2807 | 选择在任务开始前多久提醒(可多选): | notification.before_start_hint | before_start_hint |
| 2859 | 选择在任务结束前多久提醒(可多选): | notification.before_end_hint | before_end_hint |
| 2916 | (在此时间后不发送通知) | notification.after_time_hint | after_hint |
| 2920 | 开始时间: | notification.start_time_label | start_label |
| 2931 | (在此时间前不发送通知) | notification.before_time_hint | before_hint |
| 2935 | 结束时间: | notification.end_time_label | end_label |
| 2937 | 示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰 | notification.dnd_example | example_label |

### 3. 复选框文本 (Checkboxes) - 4个

| 行号 | 原文 | 翻译键 | 变量名 |
|------|------|--------|--------|
| 2766 | 启用任务提醒通知 | notification.enable_notifications | notify_enabled_check |
| 2774 | 播放提示音 | notification.enable_sound | notify_sound_check |
| 2805, 2813, 2814 | 任务开始时提醒 | notification.notify_at_start | 3处使用 |
| 2857, 2865, 2866 | 任务结束时提醒 | notification.notify_at_end | 3处使用 |
| 2902 | 启用免打扰时段 | notification.enable_dnd | dnd_enabled_check |

### 4. 动态文本 (Dynamic Text) - 1个

| 行号 | 原文 | 翻译键 | 使用位置 |
|------|------|--------|--------|
| 2828, 2879 | 提前 {minutes} 分钟 | notification.minutes_before | QCheckBox.setText (2处) |

## 翻译键总结

### notification命名空间 (18个)
- notification.basic_settings_title
- notification.reminder_timing_title
- notification.before_start_title
- notification.before_end_title
- notification.do_not_disturb_title
- notification.info_label
- notification.before_start_hint
- notification.before_end_hint
- notification.after_time_hint
- notification.start_time_label
- notification.before_time_hint
- notification.end_time_label
- notification.dnd_example
- notification.enable_notifications
- notification.enable_sound
- notification.notify_at_start
- notification.notify_at_end
- notification.enable_dnd
- notification.minutes_before

**总计**: 18个新翻译键

## 参数替换说明

以下翻译键包含参数替换：

1. **notification.minutes_before**: `{minutes}`
   - Line 2828: 用于任务开始前的分钟数
   - Line 2879: 用于任务结束前的分钟数

## 实施步骤

1. **添加翻译键**: 将18个翻译键添加到 `i18n/zh_CN.json` 和 `i18n/en_US.json`
2. **创建自动替换脚本**: 处理简单的字符串替换
3. **手动修复**: 处理复杂的情况（如参数替换、重复使用的翻译键）
4. **验证语法**: 确保所有修改后的代码仍然有效
5. **测试**: 切换语言测试所有通知设置功能

## 注意事项

1. **"⚙️ 基础设置"**: 可能与scene命名空间的同名键冲突，使用notification命名空间区分
2. **重复字符串**:
   - "任务开始时提醒" 出现3次（lines 2805, 2813, 2814）
   - "任务结束时提醒" 出现3次（lines 2857, 2865, 2866）
   - "提前 {minutes} 分钟" 出现2次（lines 2828, 2879）
3. **动态生成的复选框**: Lines 2828 和 2879 的复选框是在循环中动态生成的，需要特别处理

## 修改文件清单

- `config_gui.py`: 约24处修改（不含docstring）
- `i18n/zh_CN.json`: 添加18个键
- `i18n/en_US.json`: 添加18个键

## 代码结构分析

### 基础设置组 (Lines 2761-2781)
- 2个复选框

### 提醒时机组 (Lines 2783-2893)
包含两个子组：
1. **任务开始前提醒** (Lines 2789-2839):
   - 1个主复选框（任务开始时提醒）
   - 1个提示标签
   - 动态生成的分钟选项复选框（从notification_config）

2. **任务结束前提醒** (Lines 2841-2891):
   - 1个主复选框（任务结束时提醒）
   - 1个提示标签
   - 动态生成的分钟选项复选框（从notification_config）

### 免打扰时段组 (Lines 2895-2943)
- 1个启用复选框
- 2个时间选择器（开始时间、结束时间）
- 相关提示标签

## 技术挑战预估

### 中等难度
1. **动态生成的复选框**: Lines 2828, 2879 的文本是在for循环中设置的
2. **多处重复**: 需要确保所有重复的字符串使用相同的翻译键

### 简单
1. 大部分是静态文本的简单替换
2. 结构清晰，没有复杂的多行字符串

## 预期工作量
- 分析和规划: 15分钟 ✅ (已完成)
- 添加翻译键: 5分钟
- 自动化脚本: 10分钟
- 手动修复: 10分钟
- 验证和总结: 10分钟
- **总计**: 约50分钟
