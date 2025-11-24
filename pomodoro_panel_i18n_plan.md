# pomodoro_panel.py 国际化规划文档

## 📅 创建时间
2025-11-23

## 📊 字符串统计
- **原始字符串数**: 42个
- **唯一字符串数**: 38个
- **规划翻译键**: 35个

## 🗂️ 命名空间设计

### 命名空间结构
```
pomodoro
├── settings          # 设置对话框 (7个)
├── button            # 按钮文本 (2个)
├── log               # 日志消息 (11个)
├── notification      # 通知消息 (6个)
├── error             # 错误消息 (5个)
└── unit              # 单位/后缀 (4个)
```

## 📋 详细翻译键列表

### 1. pomodoro.settings - 设置对话框 (7个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| dialog_title | 番茄钟设置 | Pomodoro Settings | 28 |
| work_duration | 工作时长: | Work Duration: | 45 |
| short_break | 短休息时长: | Short Break: | 52 |
| long_break | 长休息时长: | Long Break: | 59 |
| long_break_interval | 长休息间隔: | Long Break Interval: | 66 |
| saved | 番茄钟设置已保存 | Pomodoro settings saved | 108 |
| updated | 番茄钟配置已更新 | Pomodoro configuration updated | 310, 313 |

### 2. pomodoro.button - 按钮文本 (2个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| save | 保存 | Save | 74 |
| cancel | 取消 | Cancel | 79 |

### 3. pomodoro.log - 日志消息 (11个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| panel_created | 番茄钟面板创建成功 | Pomodoro panel created successfully | 178 |
| panel_positioned | 番茄钟面板定位: x={panel_x}, y={panel_y} | Pomodoro panel positioned: x={panel_x}, y={panel_y} | 216 |
| started_work | 番茄钟开始:工作模式 | Pomodoro started: Work mode | 224 |
| started_short_break | 番茄钟开始:短休息 | Pomodoro started: Short break | 232 |
| started_long_break | 番茄钟开始:长休息 | Pomodoro started: Long break | 240 |
| resumed | 番茄钟继续 | Pomodoro resumed | 257 |
| paused | 番茄钟暂停 | Pomodoro paused | 262 |
| stopped | 番茄钟停止 | Pomodoro stopped | 271 |
| settings_opened | 番茄钟设置窗口已打开 | Pomodoro settings window opened | 288 |
| completed | 番茄钟完成:第{count}个 | Pomodoro completed: #{count} | 338 |
| config_update_failed | 更新番茄钟配置失败: {e} | Failed to update pomodoro config: {e} | 319 |

### 4. pomodoro.notification - 通知消息 (6个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| completed_title | 🍅 番茄钟完成! | 🍅 Pomodoro Completed! | 342 |
| completed_message | 恭喜完成第{count}个番茄钟!\n休息一下吧~ | Congratulations on completing pomodoro #{count}!\nTake a break~ | 343 |
| short_break_text | 短休息 | Short break | 356 |
| long_break_text | 长休息 | Long break | 356 |
| break_ended_title | ⏰ 休息时间结束 | ⏰ Break Time Ended | 361 |
| break_ended_message | {rest_type}结束啦!准备好开始下一个番茄钟了吗?\n点击番茄钟面板的开始按钮继续~ | {rest_type} is over! Ready to start the next pomodoro?\nClick the start button on the pomodoro panel to continue~ | 362 |

### 5. pomodoro.error - 错误消息 (5个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| error_title | 错误 | Error | 120, 293 |
| save_failed_log | 保存番茄钟设置失败: {e} | Failed to save pomodoro settings: {e} | 117 |
| save_failed_message | 保存设置失败:\n{error} | Failed to save settings:\n{error} | 121 |
| open_settings_failed_log | 打开番茄钟设置窗口失败: {e} | Failed to open pomodoro settings window: {e} | 291 |
| open_settings_failed_message | 打开设置失败: {error} | Failed to open settings: {error} | 294 |

### 6. pomodoro.unit - 单位/后缀 (4个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| minutes | 分钟 | minutes | 44, 51, 58 |
| pomodoro_count | 个番茄钟 | pomodoros | 65 |
| panel_title | 番茄钟 | Pomodoro | 183 |
| or | 或 | or | 149 |

### 保留的原始字符串
以下字符串是日志消息参数，不需要单独翻译：
- Line 175: "主题管理器初始化失败: {e}" (日志消息)
- Line 312: "设置已保存" (重复，已包含在 settings.saved 中)
- Line 357: "{rest_type}完成" (动态生成的标题)

## 🔧 实施策略

### 1. 添加翻译键
- 创建 `add_pomodoro_panel_i18n_keys.py`
- 添加35个翻译键到 i18n/zh_CN.json 和 i18n/en_US.json

### 2. 自动替换
- 创建 `apply_pomodoro_panel_i18n.py`
- 使用正则表达式模式批量替换
- 处理参数化字符串（count, error, e, panel_x, panel_y, rest_type）

### 3. 手动修复
- 检查多行字符串拼接
- 验证参数化翻译是否正确

### 4. 验证
- 运行 `python -m py_compile gaiya/ui/pomodoro_panel.py`
- 确保所有翻译键正确引用

## 📈 预期工作量
- **翻译键添加**: 15分钟
- **自动替换**: 20分钟
- **手动修复**: 15分钟
- **验证测试**: 10分钟
- **文档编写**: 20分钟
- **总计**: 约1小时20分钟

## 🎯 质量目标
- 自动化成功率: 80%+
- 代码语法: 100%通过
- 翻译完整性: 100%覆盖
- emoji保留: 100% (🍅, ⏰)

---

**文档创建时间**: 2025-11-23
**预期完成时间**: 2025-11-23
