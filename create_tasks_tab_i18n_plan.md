# create_tasks_tab() 国际化方案

## 字符串映射计划 (43个字符串)

### 1. 分组标题 (7个)

| 行号 | 原文 | 翻译键 | 英文翻译 |
|------|------|--------|----------|
| 1932 | 🤖 AI智能规划 | tasks.ai_planning_title | 🤖 AI Smart Planning |
| 2026 | 🎨 预设主题配色 | tasks.preset_themes_title | 🎨 Preset Theme Colors |
| 2060 | 📋 预设模板 | tasks.preset_templates_title | 📋 Preset Templates |
| 2090 | 💾 我的模板 | tasks.my_templates_title | 💾 My Templates |
| 2129 | 🎨 可视化时间轴编辑器 | tasks.visual_timeline_editor_title | 🎨 Visual Timeline Editor |
| 2199 | 📅 模板自动应用管理 | tasks.template_auto_apply_title | 📅 Template Auto-Apply Management |
| 2238 | 🔍 测试日期 | tasks.test_date_title | 🔍 Test Date |

### 2. 提示/帮助文本 (5个)

| 行号 | 原文 | 翻译键 | 英文翻译 |
|------|------|--------|----------|
| 1937 | 💡 用自然语言描述您的计划,AI将自动生成任务时间表 | tasks.ai_planning_hint | 💡 Describe your plan in natural language, AI will automatically generate a task schedule |
| 2021 | 双击表格单元格可以编辑任务内容 | tasks.double_click_to_edit_hint | Double-click table cells to edit task content |
| 2133 | 💡 提示：拖动色块边缘可调整任务时长 | tasks.drag_to_adjust_hint | 💡 Tip: Drag the edges of color blocks to adjust task duration |
| 2204 | 💡 为每个模板设置自动应用的日期规则，到了指定时间会自动加载对应模板 | tasks.auto_apply_hint | 💡 Set date rules for each template to automatically apply at specified times |
| 2239 | 测试指定日期会匹配到哪个模板 | tasks.test_date_hint | Test which template will match a specified date |

### 3. 标签文本 (7个)

| 行号 | 原文 | 翻译键 | 英文翻译 |
|------|------|--------|----------|
| 1943 | 描述您的计划: | tasks.describe_plan_label | Describe your plan: |
| 2030 | 选择主题: | tasks.select_theme_label | Select theme: |
| 2045 | 配色预览: | tasks.color_preview_label | Color preview: |
| 2064 | 快速加载: | tasks.quick_load_label | Quick load: |
| 2094 | 选择模板: | tasks.select_template_label | Select template: |
| 1983 | 配额状态: 加载中... | tasks.quota_status_loading | Quota status: Loading... |
| 2079 | 模板加载中... | tasks.template_loading | Template loading... |

### 4. 占位符文本 (1个)

| 行号 | 原文 | 翻译键 | 英文翻译 |
|------|------|--------|----------|
| 1949 | 例如: 明天9点开会1小时,然后写代码到下午5点,中午12点休息1小时,晚上6点健身... | tasks.plan_placeholder | For example: Meeting at 9am for 1 hour tomorrow, then coding until 5pm, lunch break at noon for 1 hour, gym at 6pm... |

### 5. 按钮文本 (9个)

| 行号 | 原文 | 翻译键 | 英文翻译 |
|------|------|--------|----------|
| 1960 | ✨ 智能生成任务 | tasks.btn_generate_tasks | ✨ Generate Tasks |
| 1988 | 🔄 刷新配额 | tasks.btn_refresh_quota | 🔄 Refresh Quota |
| 2104 | 📂 加载 | tasks.btn_load | 📂 Load |
| 2112 | 🗑️ 删除 | tasks.btn_delete | 🗑️ Delete |
| 2170 | ➕ 添加任务 | tasks.btn_add_task | ➕ Add Task |
| 2175 | 💾 保存为模板 | tasks.btn_save_as_template | 💾 Save as Template |
| 2180 | 📂 加载自定义模板 | tasks.btn_load_custom_template | 📂 Load Custom Template |
| 2185 | 🗑️ 清空所有任务 | tasks.btn_clear_all_tasks | 🗑️ Clear All Tasks |
| 2232 | ➕ 添加规则 | tasks.btn_add_rule | ➕ Add Rule |

### 6. 按钮提示文本 (tooltip) (2个)

| 行号 | 原文 | 翻译键 | 英文翻译 |
|------|------|--------|----------|
| 2105 | 加载选中的自定义模板 | tasks.load_template_tooltip | Load selected custom template |
| 2113 | 删除选中的自定义模板 | tasks.delete_template_tooltip | Delete selected custom template |

### 7. 状态消息 (1个)

| 行号 | 原文 | 翻译键 | 英文翻译 |
|------|------|--------|----------|
| 2015 | ⏳ 正在连接云服务（可能需要10-15秒）... | tasks.connecting_cloud_service | ⏳ Connecting to cloud service (may take 10-15 seconds)... |

### 8. 表格列标题 (11个，分两组)

#### 时间轴编辑器表格 (第2155行)

| 原文 | 翻译键 | 英文翻译 |
|------|--------|----------|
| 开始时间 | tasks.column_start_time | Start Time |
| 结束时间 | tasks.column_end_time | End Time |
| 任务名称 | tasks.column_task_name | Task Name |
| 背景颜色 | tasks.column_bg_color | Background Color |
| 文字颜色 | tasks.column_text_color | Text Color |
| 操作 | tasks.column_actions | Actions |

#### 模板自动应用表格 (第2213行)

| 原文 | 翻译键 | 英文翻译 |
|------|--------|----------|
| 模板名称 | tasks.column_template_name | Template Name |
| 应用时间 | tasks.column_apply_time | Apply Time |
| 状态 | tasks.column_status | Status |
| 操作 | tasks.column_actions | Actions (重复使用) |

---

## 统计

- **总字符串数**: 43个
- **唯一字符串**: 42个（"操作"重复1次）
- **需要新建的翻译键**: 42个
- **命名空间**: tasks

## 分类汇总

| 类别 | 数量 |
|------|------|
| 分组标题 | 7 |
| 提示/帮助文本 | 5 |
| 标签文本 | 7 |
| 占位符文本 | 1 |
| 按钮文本 | 9 |
| 按钮提示文本 | 2 |
| 状态消息 | 1 |
| 表格列标题 | 10（去重后） |
| **总计** | **42** |

## 注意事项

1. **emoji图标**: 所有emoji保留在翻译文本中
2. **表格列标题**: 第2155行有6个列标题在一行中，需要特别处理
3. **状态消息**: 包含时间估算，需要确保翻译准确
4. **占位符文本**: 很长的示例文本，需要完整翻译

## 实施步骤

1. ✅ 分析并规划翻译键
2. ⏭️ 创建42个新翻译键并添加到 i18n 文件
3. ⏭️ 修改 config_gui.py 的 create_tasks_tab() 方法
4. ⏭️ 验证并测试中英文切换

## 特殊处理

### 表格列标题 (第2155行)
原代码可能类似：
```python
headers = ["开始时间", "结束时间", "任务名称", "背景颜色", "文字颜色", "操作"]
```

需要改为：
```python
headers = [
    tr("tasks.column_start_time"),
    tr("tasks.column_end_time"),
    tr("tasks.column_task_name"),
    tr("tasks.column_bg_color"),
    tr("tasks.column_text_color"),
    tr("tasks.column_actions")
]
```

### 表格列标题 (第2213行)
类似处理：
```python
headers = [
    tr("tasks.column_template_name"),
    tr("tasks.column_apply_time"),
    tr("tasks.column_status"),
    tr("tasks.column_actions")
]
```
