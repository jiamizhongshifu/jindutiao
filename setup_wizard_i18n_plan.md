# setup_wizard.py 国际化规划文档

## 📅 创建时间
2025-11-23

## 📊 字符串统计
- **原始字符串数**: 42个
- **唯一字符串数**: 41个
- **用户可见字符串**: 26个
- **文档字符串（不翻译）**: 16个
- **规划翻译键**: 26个

## 🗂️ 命名空间设计

### 命名空间结构
```
wizard
├── window           # 窗口基本信息 (1个)
├── template_page    # 模板选择页面 (9个)
├── complete_page    # 完成页面 (7个)
├── suggestions      # 下一步建议列表 (3个)
└── tips             # 快速上手提示列表 (4个)
```

### 模板信息特别处理
模板名称和描述采用独立的命名空间：
```
wizard.templates
├── work_weekday.name         # 工作日模板名称
├── work_weekday.description  # 工作日模板描述
├── student.name              # 学生模板名称
├── student.description       # 学生模板描述
├── freelancer.name           # 自由职业模板名称
└── freelancer.description    # 自由职业模板描述
```

## 📋 详细翻译键列表

### 1. wizard.window - 窗口基本信息 (1个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| title | 快速配置 | Quick Setup | 34 |

### 2. wizard.template_page - 模板选择页面 (9个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| title | 选择任务模板 | Select Task Template | 90 |
| subtitle | 为你推荐3个热门模板，选择最适合的一个即可快速开始 | We recommend 3 popular templates, choose the one that suits you best to get started quickly | 91 |
| ai_option_label | 或者，让AI根据你的需求智能生成任务： | Or, let AI intelligently generate tasks based on your needs: | 158 |
| ai_button | 🤖 AI智能生成任务 | 🤖 AI Smart Task Generation | 165 |
| ai_note | 💡 点击后将关闭向导，打开配置界面使用AI生成 | 💡 Click to close the wizard and open the configuration interface to use AI generation | 184 |

### 3. wizard.templates - 模板信息 (6个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| work_weekday.name | 📊 工作日模板 | 📊 Workday Template | 101, 296 |
| work_weekday.description | 适合上班族。包含：通勤、会议、工作、午休、晚餐、学习等典型工作日任务。 | Suitable for office workers. Includes: commute, meetings, work, lunch break, dinner, study and other typical workday tasks. | 107 |
| student.name | 🎓 学生模板 | 🎓 Student Template | 113, 297 |
| student.description | 适合学生党。包含：早读、上课、自习、运动、社团活动等校园生活任务。 | Suitable for students. Includes: morning reading, classes, self-study, sports, club activities and other campus life tasks. | 117 |
| freelancer.name | 💼 自由职业模板 | 💼 Freelancer Template | 123, 298 |
| freelancer.description | 适合自由工作者。包含：客户沟通、项目开发、创作时间、休息等灵活时间安排。 | Suitable for freelancers. Includes: client communication, project development, creative time, rest and other flexible time arrangements. | 127 |

### 4. wizard.complete_page - 完成页面 (7个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| title | 配置完成！🎉 | Configuration Complete! 🎉 | 212 |
| subtitle | 你已成功完成基础配置，现在可以开始使用 GaiYa 了 | You have successfully completed the basic configuration, now you can start using GaiYa | 213 |
| summary_title | ✅ 已完成的配置： | ✅ Completed Configuration: | 220 |
| selected_template | 已选择任务模板: {template_name} | Selected Task Template: {template_name} | 302 |
| position_label | 进度条位置: 屏幕底部（固定） | Progress Bar Position: Bottom of Screen (Fixed) | 235 |
| suggestions_title | 下一步建议: | Next Steps: | 245 |
| tips_title | 💡 快速上手提示： | 💡 Quick Start Tips: | 269 |

### 5. wizard.suggestions - 下一步建议 (3个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| customize_tasks | • 打开配置界面自定义任务时间和颜色 | • Open the configuration interface to customize task time and colors | 255 |
| set_reminders | • 设置任务提醒时间 | • Set task reminder time | 256 |
| choose_theme | • 选择喜欢的主题配色 | • Choose your favorite theme color | 257 |

### 6. wizard.tips - 快速上手提示 (4个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| right_click_config | • 右键点击进度条可以打开配置界面 | • Right-click the progress bar to open the configuration interface | 274 |
| tray_menu | • 系统托盘图标右键菜单提供快捷操作 | • Right-click menu on the system tray icon provides quick actions | 275 |
| double_click_toggle | • 支持快捷键：双击隐藏/显示进度条 | • Shortcut support: Double-click to hide/show progress bar | 276 |
| free_quota | • 免费用户每天有3次AI任务规划配额 | • Free users have 3 AI task planning quotas per day | 277 |

## 🔧 实施策略

### 1. 添加翻译键
- 创建 `add_setup_wizard_i18n_keys.py`
- 添加26个翻译键到 i18n/zh_CN.json 和 i18n/en_US.json
- 组织为5个命名空间（window, template_page, templates, complete_page, suggestions, tips）

### 2. 代码修改策略
- **优先自动化**: 简单字符串替换（单行标签、按钮）
- **手动处理**:
  - 模板字典（Lines 295-299）需要重构
  - 列表推导式（suggestions, tips）需要改造
  - 参数化字符串（Line 302）

### 3. 特殊处理

#### A. 模板选择重构
将硬编码的模板字典改为使用翻译键：
```python
# 旧代码
template_names = {
    "work_weekday": "工作日模板 📊",
    "student": "学生模板 🎓",
    "freelancer": "自由职业模板 💼"
}

# 新代码
template_names = {
    "work_weekday": tr("wizard.templates.work_weekday.name"),
    "student": tr("wizard.templates.student.name"),
    "freelancer": tr("wizard.templates.freelancer.name")
}
```

#### B. 列表数据结构化
将建议和提示从硬编码列表改为翻译键：
```python
# 旧代码
suggestions = [
    "• 打开配置界面自定义任务时间和颜色",
    "• 设置任务提醒时间",
    "• 选择喜欢的主题配色"
]

# 新代码
suggestions = [
    tr("wizard.suggestions.customize_tasks"),
    tr("wizard.suggestions.set_reminders"),
    tr("wizard.suggestions.choose_theme")
]
```

### 4. 验证
- 运行 `python -m py_compile gaiya/ui/onboarding/setup_wizard.py`
- 确保所有翻译键正确引用
- 确保emoji图标正确保留

## 📈 预期工作量
- **翻译键添加**: 10分钟
- **自动替换**: 5分钟（简单字符串）
- **手动重构**: 20分钟（模板字典、列表）
- **验证测试**: 3分钟
- **文档编写**: 7分钟
- **总计**: 约45分钟

## 🎯 质量目标
- 自动化成功率: 40%+ (简单字符串替换)
- 代码语法: 100%通过
- 翻译完整性: 100%覆盖
- Emoji保留: 100%
- 代码可读性: 提升（将硬编码改为结构化数据）

## 📝 特殊注意事项

### 模板名称复用
- "工作日模板 📊" 在 Line 101 和 Line 296 出现
- "学生模板 🎓" 在 Line 113 和 Line 297 出现
- "自由职业模板 💼" 在 Line 123 和 Line 298 出现
- 统一使用 wizard.templates.*.name 翻译键

### Emoji图标保留
所有emoji图标都在翻译字符串中保留：
- 📊 工作日模板
- 🎓 学生模板
- 💼 自由职业模板
- 🤖 AI智能生成任务
- 💡 提示标签（2处）
- ✅ 已完成的配置
- 🎉 配置完成

### 列表条目格式
建议和提示列表都使用 "•" 符号作为前缀，需要在翻译中保留

---

**文档创建时间**: 2025-11-23
**预期完成时间**: 2025-11-23
