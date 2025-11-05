# Gaiya 快速参考手册

> 🎯 **目标**：为AI助手和开发者提供快速定位代码的索引，补充CLAUDE.md中的详细方法论。

---

## 📁 核心文件职责

### 主程序文件
- **main.py** (1997行)
  - 主窗口：`TimeProgressBar`类 (第44行)
  - 进度条绘制：`paintEvent()` 方法
  - 动画系统：时间标记GIF/WebP播放
  - 番茄钟面板集成
  - 托盘菜单和系统交互

- **config_gui.py** (4070行)
  - 配置界面：`ConfigManager`类 (第169行)
  - 任务表格编辑：`QTableWidget`操作
  - 主题预览：`TimelineEditor`集成
  - AI任务生成：`AIWorker`线程 (第36行)
  - 模板管理：保存/加载/导入/导出

- **ai_client.py** (260行)
  - AI通信：`GaiyaAIClient`类 (第13行)
  - Vercel云服务API调用
  - 配额查询和任务生成
  - 错误处理和重试逻辑

### 核心模块（gaiya/）
- **gaiya/core/theme_manager.py**
  - 主题管理：`ThemeManager`类
  - 预设主题加载
  - Qt-Material样式应用

- **gaiya/core/notification_manager.py**
  - 通知管理：`NotificationManager`类
  - Windows系统通知集成

- **gaiya/core/pomodoro_state.py**
  - 番茄钟状态：`PomodoroState`类
  - 工作/休息周期管理

### 工具模块（gaiya/utils/）
- **path_utils.py** - 路径处理工具
- **time_utils.py** - 时间计算工具
- **data_loader.py** - 配置和任务数据加载

---

## 🔑 关键类和方法

### TimeProgressBar（主窗口）
```python
main.py:44 - class TimeProgressBar(QWidget)
  ├─ __init__() - 初始化配置、任务、主题
  ├─ paintEvent() - 绘制进度条和动画
  ├─ calculate_time_range() - 计算任务时间范围
  ├─ reload_all() - 重新加载配置和任务
  └─ apply_theme() - 应用主题样式
```

### ConfigManager（配置界面）
```python
config_gui.py:169 - class ConfigManager(QMainWindow)
  ├─ load_tasks_to_table() - 加载任务到表格
  ├─ save_all() - 保存配置和任务
  ├─ generate_tasks_with_ai() - AI生成任务
  ├─ on_preset_theme_changed_with_preview() - 主题预览
  └─ save_tasks_as_template() - 保存任务模板
```

### GaiyaAIClient（AI通信）
```python
ai_client.py:13 - class GaiyaAIClient
  ├─ plan_tasks() - AI任务生成
  ├─ check_quota_status() - 查询配额
  └─ _check_service_health() - 健康检查
```

### ThemeManager（主题管理）
```python
gaiya/core/theme_manager.py:16 - class ThemeManager
  ├─ load_themes() - 加载预设主题
  ├─ apply_theme() - 应用主题到组件
  └─ theme_changed (Signal) - 主题变更信号
```

---

## 🛠️ 常用操作命令

### 开发与测试
```bash
# 开发模式（源代码运行，修改立即生效）
python main.py

# 打包为单文件exe（更新版本号后执行）
pyinstaller Gaiya.spec

# 打包配置工具（独立exe）
pyinstaller Gaiya-Config.spec

# 查看应用日志
type gaiya.log

# 过滤错误日志
type gaiya.log | findstr "ERROR"

# 查看AI相关日志
type gaiya.log | findstr /C:"AI" /C:"任务生成" /C:"智能" /C:"配额"
```

### 版本发布流程
```bash
# 1. 更新版本号（Gaiya.spec, version_info.txt）
# 2. 清理旧文件
rm -rf build dist

# 3. 打包主程序和配置工具
pyinstaller Gaiya.spec
pyinstaller Gaiya-Config.spec

# 4. 测试打包后的exe
./dist/Gaiya-v1.5.exe

# 5. 提交代码
git add .
git commit -m "release: v1.5.0"
git tag v1.5.0

# 6. GitHub Release（使用./dist/中的exe文件）
```

### Vercel API部署
```bash
# 推送代码自动触发部署
git push origin main

# 查看部署状态（Vercel Dashboard）
https://vercel.com/jindutiao

# 测试API端点
curl https://jindutiao.vercel.app/api/health
curl "https://jindutiao.vercel.app/api/quota-status?user_tier=free"
```

---

## 📦 数据文件说明

### 配置文件（用户数据目录）
- **config.json** - 用户配置
  - 窗口位置和尺寸
  - 主题ID（当前选择的主题）
  - AI设置（用户层级、端点）
  - 番茄钟设置

- **tasks.json** - 任务数据
  - 任务列表（名称、开始时间、结束时间、颜色）
  - 由ConfigManager保存
  - **重要**：包含实际的任务颜色值

- **themes.json** - 用户自定义主题
  - 用户创建的自定义主题
  - 不包含预设主题（预设主题在代码中定义）

### 模板文件（项目目录）
- **tasks_template_*.json** - 预设任务模板
  - `tasks_template_workday.json` - 工作日模板
  - `tasks_template_student.json` - 学生模板
  - `tasks_template_24h.json` - 24小时模板
  - ...等

- **templates_config.json** - 用户保存的模板
  - 用户通过ConfigManager保存的自定义模板

---

## 🐛 调试要点

### PyInstaller打包注意事项
⚠️ **修改Python源代码后，必须重新打包才能在exe中生效！**

```bash
# 验证是否需要重新打包
dir dist\*.exe  # 查看exe修改时间
# 如果exe修改时间早于源代码修改时间，必须重新打包

# 强制清理重建（推荐）
rm -rf build dist && pyinstaller Gaiya.spec
```

📖 **详细指南**：参考 `PYINSTALLER_DEVELOPMENT_METHODOLOGY.md`

### 常见问题排查

**1. 配置保存后UI未刷新**
- 检查数据流：用户输入 → 表格 → tasks.json → reload → UI
- 确认`reload_all()`调用了`apply_theme()`
- 📖 详见：`CLAUDE.md` - UI State Synchronization Troubleshooting

**2. Vercel API返回404**
- 检查路径一致性：客户端路径 = `/api/xxx`
- 检查vercel.json路由配置
- 📖 详见：`CLAUDE.md` - Vercel Deployment Troubleshooting

**3. 动画播放卡顿**
- 检查是否预缓存所有帧
- 验证帧延迟设置（WebP可能为0ms）
- 📖 详见：`CLAUDE.md` - Performance Perception vs Reality Analysis

**4. 主题颜色不生效**
- 确认`config.json`中的`theme_id`
- 确认`tasks.json`中的`color`字段
- 检查`apply_theme()`调用时机
- 📖 详见：`SESSION_SUMMARY_2025-11-02.md`

---

## 📚 扩展文档索引

### 方法论文档（CLAUDE.md）
- 🔍 **Progressive Differential Analysis** - 部分功能正常、部分失败的诊断
- 🚀 **Vercel Deployment Troubleshooting** - Vercel部署404问题
- 📦 **PyInstaller Development Methodology** - 打包应用开发流程
- 🎨 **UI State Synchronization** - UI状态同步问题
- ⚡ **Performance Perception Analysis** - 动画性能优化

### 功能文档
- `AI_FEATURE_GUIDE.md` - AI功能使用指南
- `QUOTA_SYSTEM_README.md` - 配额系统说明
- `任务模板使用说明.md` - 任务模板详细文档
- `使用指南.md` - 用户使用手册

### 发布文档
- `RELEASE_v1.5.md` - v1.5版本发布说明
- `ROADMAP_v1.5.md` - v1.5路线图
- `CHANGELOG.md` - 完整变更日志

### 安全文档
- `SECURITY.md` - 安全策略
- `API_SECURITY_ANALYSIS.md` - API安全分析
- `反病毒误报解决方案.md` - AV误报处理

---

## 🎯 快速决策树

### 何时直接修改 vs 何时用Task探索？

```
是否需要读取 >5个文件？
├─ 是 → 使用 Task(subagent_type="Explore")
└─ 否 → 继续

是否是开放式搜索（不确定目标在哪）？
├─ 是 → 使用 Task
└─ 否 → 继续

是否需要频繁与用户交互确认？
├─ 是 → 主窗口直接处理
└─ 否 → 继续

是否是独立的、一次性的分析？
├─ 是 → 使用 Task
└─ 否 → 主窗口直接处理（效率最高）
```

### Task调用模板
```python
Task(
    subagent_type="Explore",
    model="haiku",  # 简单搜索用haiku节省成本
    prompt=f"""
    在Gaiya项目中搜索{目标}。

    背景：{为什么需要搜索，1-2句话}

    请返回：
    1. 相关文件列表（按重要性排序）
    2. 关键代码位置（文件:行号格式）
    3. 初步分析（潜在问题或改进建议）

    要求：结论简洁，便于主窗口决策。
    """
)
```

---

## 📝 版本历史

| 版本 | 日期 | 主要特性 |
|------|------|---------|
| v1.5.0 | 2025-11-04 | 品牌升级为Gaiya，Qt-Material主题集成 |
| v1.4.1 | 2025-11-01 | 修复配色重置bug，优化动画性能 |
| v1.4.0 | 2025-11-01 | AI功能增强，Vercel云服务 |
| v1.3.0 | 2025-10-29 | 任务模板系统 |

---

**最后更新**: 2025-11-05
**维护者**: Claude Code AI Assistant
**项目主页**: https://github.com/Sats365/jindutiao
