# PyDayBar - 桌面日历进度条 📅

<div align="center">

一个简洁优雅的桌面时间进度条工具,实时可视化您的每日任务安排

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://pypi.org/project/PySide6/)
[![Version](https://img.shields.io/badge/version-1.2.0-brightgreen.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)

**当前版本: v1.2.0** | 最后更新: 2025-10-30

</div>

---

## ✨ 特性

- 🎯 **透明置顶** - 始终显示在所有窗口之上,不干扰日常操作
- 🖱️ **悬停提示** - 鼠标悬停显示任务详情,支持交互式操作
- ⏱️ **实时更新** - 动态显示当前时间进度,精确到秒
- 🎨 **高度自定义** - 支持自定义颜色、位置、高度、圆角等外观
- 🔄 **热重载** - 修改配置文件即时生效,无需重启
- 💾 **轻量级** - 内存占用极低,CPU使用率几乎为0
- 📊 **任务可视化** - 用彩色色块直观显示全天的任务安排,紧凑模式无缝衔接
- 🌙 **多显示器支持** - 可选择在任意显示器上显示
- 🎛️ **可视化配置** - 功能完善的 GUI 配置管理器,无需手动编辑 JSON
- 📑 **预设模板** - 8 种内置作息模板(工作日、学生、自由职业等),一键加载
- 🖼️ **多样时间标记** - 支持线条、静态图片、动画 GIF 三种时间标记样式
- 🍅 **番茄钟集成** - 内置番茄钟计时器,支持拖拽定位和可视化配置
- 🔔 **智能通知** - 任务提醒和番茄钟通知,支持免打扰时段
- 📈 **任务统计报告** - 自动跟踪任务完成情况,提供多维度统计分析和数据导出

## 📸 效果预览

```
屏幕顶部/底部:
┌────────────────────────────────────────────────────────────────┐
│ [灰色背景] [绿色-上午工作] [黄色-午休] [蓝色-下午工作] [红线-当前时间] │
└────────────────────────────────────────────────────────────────┘
```

**示意图说明:**
- 半透明灰色背景横跨整个屏幕宽度
- 彩色色块代表 `tasks.json` 中定义的任务(紧凑模式,无缝衔接)
- 红色垂直线/图片/GIF 标记当前时间位置,随时间移动
- 鼠标悬停在任务上时显示任务详情和时间范围

## 🚀 快速开始

### 前置要求

- **Python 3.8 或更高版本**
- **操作系统:** Windows 10/11(推荐), Linux, macOS

### 安装步骤

1. **克隆/下载项目**
   ```bash
   git clone https://github.com/yourusername/PyDayBar.git
   cd PyDayBar
   ```

2. **创建虚拟环境(推荐)**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行程序**
   ```bash
   python main.py
   ```

5. **打开配置管理器(可选)**
   ```bash
   python config_gui.py
   ```
   或右键系统托盘图标选择"打开配置"

### 首次运行

程序首次启动时会自动创建以下文件:

- `config.json` - 配置文件
- `tasks.json` - 任务数据文件

您可以使用 GUI 配置管理器或直接编辑这些文件来自定义进度条。

## 📝 配置说明

### 使用 GUI 配置管理器(推荐)

运行 `python config_gui.py` 或通过系统托盘菜单"打开配置"启动可视化配置管理器。

**GUI 配置管理器功能:**
- 📊 **可视化任务编辑** - 使用时间选择器和颜色选择器编辑任务
- 🎨 **外观配置** - 调整进度条高度、位置、颜色、透明度等
- 🖼️ **时间标记设置** - 选择线条/图片/GIF 标记,调整大小和偏移
- 📑 **预设模板** - 一键加载 8 种内置模板:
  - 24小时完整作息
  - 工作日作息
  - 学生作息
  - 自由职业
  - 夜班作息
  - 内容创作者
  - 健身达人
  - 创业者
- 💾 **自定义模板** - 保存和加载自定义任务配置
- ✅ **实时验证** - 自动检测时间冲突和格式错误

### 手动编辑配置文件

#### config.json - 外观配置

```json
{
    "bar_height": 20,              // 进度条高度(像素)
    "position": "bottom",          // 位置:"top" 或 "bottom"
    "background_color": "#505050", // 背景颜色(十六进制)
    "background_opacity": 180,     // 背景透明度(0-255)
    "marker_color": "#FF0000",     // 时间标记颜色(仅线条模式)
    "marker_width": 2,             // 时间标记宽度(像素,仅线条模式)
    "marker_type": "line",         // 标记类型:"line"、"image" 或 "gif"
    "marker_image_path": "",       // 图片/GIF 路径(image/gif 模式)
    "marker_size": 50,             // 图片/GIF 大小(像素)
    "marker_y_offset": 0,          // 标记垂直偏移(像素,正数向上)
    "screen_index": 0,             // 显示器索引(0=主显示器)
    "update_interval": 1000,       // 更新间隔(毫秒)
    "enable_shadow": true,         // 是否启用阴影效果
    "corner_radius": 0,            // 圆角半径(0=直角)
    "notification": {              // 通知配置
        "enabled": true,           // 通知总开关
        "before_start_minutes": [5], // 任务开始前N分钟提醒
        "on_start": true,          // 任务开始时提醒
        "before_end_minutes": [],  // 任务结束前N分钟提醒
        "on_end": false,           // 任务结束时提醒
        "sound_enabled": true,     // 声音开关
        "sound_file": "",          // 自定义提示音路径
        "quiet_hours": {           // 免打扰时段
            "enabled": false,
            "start": "22:00",
            "end": "08:00"
        }
    },
    "pomodoro": {                  // 番茄钟配置
        "work_duration": 1500,     // 工作时长(秒,默认25分钟)
        "short_break": 300,        // 短休息时长(秒,默认5分钟)
        "long_break": 900,         // 长休息时长(秒,默认15分钟)
        "long_break_interval": 4   // 长休息间隔(默认每4个番茄钟)
    }
}
```

#### tasks.json - 任务配置

```json
[
    {
        "start": "09:00",          // 开始时间(24小时制)
        "end": "12:00",            // 结束时间(支持 "24:00")
        "task": "上午工作",         // 任务名称
        "color": "#4CAF50"         // 显示颜色(十六进制)
    },
    {
        "start": "13:00",
        "end": "14:00",
        "task": "午休",
        "color": "#FFC107"
    },
    {
        "start": "14:00",
        "end": "18:00",
        "task": "下午工作",
        "color": "#2196F3"
    }
]
```

**颜色推荐:**
- 工作: `#4CAF50` (绿色), `#2196F3` (蓝色)
- 休息: `#FFC107` (黄色), `#FF9800` (橙色)
- 重要: `#F44336` (红色), `#E91E63` (粉色)
- 学习: `#9C27B0` (紫色), `#673AB7` (深紫)

## 🎮 使用方法

### 系统托盘菜单

右键点击系统托盘图标(任务栏右下角)可以:

- **⚙️ 打开配置** - 启动 GUI 配置管理器
- **🍅 启动番茄钟** - 打开番茄钟面板开始工作
- **🔔 通知功能** - 发送测试通知和查看通知历史
- **🔄 重载配置** - 重新加载 `config.json` 和 `tasks.json`
- **↕️ 切换位置** - 在屏幕顶部和底部之间切换
- **❌ 退出** - 关闭程序

### 悬停提示

将鼠标悬停在进度条的任务色块上,会显示该任务的详细信息:
- 任务名称
- 开始时间
- 结束时间

### 热重载

您可以直接编辑 `tasks.json` 或 `config.json`,程序会自动检测文件变化并更新显示,**无需重启**。

### 时间标记样式

**线条模式** (默认):
- 设置 `"marker_type": "line"`
- 可自定义颜色和宽度
- 性能最佳,推荐日常使用

**图片模式**:
- 设置 `"marker_type": "image"`
- 指定 `"marker_image_path"` 为 PNG/JPG 文件路径
- 调整 `"marker_size"` 控制图片大小

**GIF 动画模式**:
- 设置 `"marker_type": "gif"`
- 指定 `"marker_image_path"` 为 GIF 文件路径
- 支持透明背景和循环播放

### 番茄钟功能 🍅

**启动番茄钟:**
1. 右键点击系统托盘图标
2. 选择"🍅 启动番茄钟"
3. 番茄钟面板将显示在进度条上方

**番茄钟面板功能:**
- **▶/⏸ 按钮** - 开始/暂停番茄钟
- **⚙ 设置按钮** - 打开配置对话框,可调整:
  - 工作时长(1-120分钟,默认25分钟)
  - 短休息时长(1-60分钟,默认5分钟)
  - 长休息时长(1-120分钟,默认15分钟)
  - 长休息间隔(1-10个番茄钟,默认4个)
- **✕ 关闭按钮** - 停止并关闭番茄钟
- **拖拽支持** - 点击面板空白区域可拖动到屏幕任意位置

### 任务统计报告 📊

**打开统计报告:**
1. 右键点击系统托盘图标
2. 选择"📊 统计报告"
3. 统计窗口将显示详细的任务分析

**统计功能特性:**

**📅 今日统计标签页:**
- 今日任务摘要卡片(总任务数、已完成、进行中、未开始)
- 圆形进度条显示今日完成率
- 任务详情表格(显示每个任务的时间和状态)

**📊 本周统计标签页:**
- 本周汇总数据(任务数、完成数、总时长)
- 本周完成率圆形进度条
- 每日趋势表格(星期、任务数、完成率等)

**📈 本月统计标签页:**
- 本月累计统计
- 月度完成率可视化
- 每日统计明细

**📋 任务分类标签页:**
- 按任务名称分类的历史统计
- 显示每个任务的完成次数和总时长
- 颜色标记便于识别

**数据管理:**
- **🔄 刷新按钮** - 实时更新统计数据
- **📥 导出CSV** - 将统计数据导出为CSV文件用于进一步分析
- **自动跟踪** - 任务状态每分钟自动更新(在每分钟的第0秒)
- **数据持久化** - 统计数据保存在`statistics.json`,程序重启不丢失
- **数据清理** - 自动保留最近90天的数据,旧数据可手动清理

**统计数据包含:**
- 每日任务完成记录
- 任务时长和完成时间
- 任务完成率计算
- 按任务名称分类的历史累计
- 支持日期范围查询

**工作流程:**
1. 点击开始按钮,开始25分钟工作
2. 工作完成后自动进入5分钟短休息
3. 完成4个番茄钟后自动进入15分钟长休息
4. 休息结束后手动点击开始按钮继续下一个番茄钟

**通知提醒:**
- 工作完成时显示通知
- 休息结束时提醒开始新的番茄钟
- 面板颜色随状态变化(工作=红色,休息=绿色,暂停=灰色)

### 通知管理 🔔

**配置任务提醒:**
在 `config.json` 的 `notification` 部分配置:
- `enabled` - 开启/关闭通知功能
- `before_start_minutes` - 任务开始前N分钟提醒(支持多个时间点)
- `on_start` - 任务开始时提醒
- `before_end_minutes` - 任务结束前N分钟提醒
- `on_end` - 任务结束时提醒

**免打扰时段:**
设置 `quiet_hours.enabled: true` 并配置起止时间,在此时段内不会发送通知。

**测试通知:**
右键托盘图标 → 通知功能 → 发送测试通知

### 开机自启动

**Windows:**
1. 按 `Win + R`,输入 `shell:startup`,回车
2. 将 `PyDayBar.exe`(或 `main.py` 的快捷方式)复制到打开的文件夹中

**Linux(systemd):**
创建 `~/.config/systemd/user/pydaybar.service`:
```ini
[Unit]
Description=PyDayBar Desktop Time Bar

[Service]
ExecStart=/path/to/venv/bin/python /path/to/main.py
Restart=on-failure

[Install]
WantedBy=default.target
```

然后启用:
```bash
systemctl --user enable pydaybar.service
systemctl --user start pydaybar.service
```

## 📦 打包为可执行文件

使用 PyInstaller 打包成独立的 `.exe` 文件(无需 Python 环境):

### 打包步骤

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 清理旧文件(可选)
# Windows PowerShell:
Remove-Item -Recurse -Force build, dist

# 3. 打包主程序
pyinstaller PyDayBar.spec

# 4. 生成的文件在 dist/ 目录中
```

### 打包配置说明

`PyDayBar.spec` 文件已配置包含以下内容:

**数据文件 (datas):**
- 8个任务模板文件 (`tasks_template_*.json`)

**隐藏导入 (hiddenimports):**
- `statistics_manager` - 统计数据管理器
- `statistics_gui` - 统计报告GUI
- `PySide6.QtCore`, `PySide6.QtGui`, `PySide6.QtWidgets` - Qt子模块

### 打包结果

- **文件大小**: 约 46.5 MB
- **生成位置**: `dist\PyDayBar.exe`
- **运行方式**: 双击exe即可运行,无需Python环境

### 首次运行自动生成文件

exe首次运行时会在同目录自动创建:
- `config.json` - 配置文件
- `tasks.json` - 任务文件(从模板加载)
- `statistics.json` - 统计数据文件
- `pydaybar.log` - 运行日志

### 打包配置管理器(可选)

```bash
pyinstaller PyDayBar-Config.spec
```

配置管理器也可以通过主程序的托盘菜单打开,不需要单独打包。

**⚠️ 重要提示:**

1. **必须使用 `.spec` 文件打包**,不要直接运行 `pyinstaller main.py`,否则模板文件和新模块不会被包含
2. 每次添加新的模板文件或Python模块后,需要更新 `PyDayBar.spec` 中的 `datas` 或 `hiddenimports` 列表
3. 详细打包说明请参考 [CLAUDE.md](CLAUDE.md#⚠️-important-packaging-with-template-files)

## 🛠️ 开发指南

### 项目结构

```
PyDayBar/
├── main.py                       # 主程序入口 (1900+ 行)
│                                 # 包含: 番茄钟、通知管理、进度条、统计追踪
├── statistics_manager.py         # 统计数据管理器
├── statistics_gui.py              # 统计报告GUI窗口
├── config_gui.py                 # GUI 配置管理器 (1123 行)
├── config.json                   # 运行时配置文件
├── tasks.json                    # 当前任务安排
├── requirements.txt              # Python 依赖
├── PyDayBar.spec                 # PyInstaller 打包配置
├── PyDayBar-Config.spec          # 配置管理器打包配置
├── README.md                     # 本文件
├── CLAUDE.md                     # Claude Code 项目指导
├── jindutiao.md                  # 详细开发文档
├── tasks_template_*.json         # 8 个预设模板
├── statistics.json               # 统计数据文件
└── pydaybar.log                  # 运行日志
```

### 核心技术

- **GUI 框架:** PySide6 (Qt for Python)
- **窗口属性:**
  - `Qt.FramelessWindowHint` - 无边框
  - `Qt.WindowStaysOnTopHint` - 始终置顶
  - `Qt.WindowDoesNotAcceptFocus` - 不抢占焦点
  - `WA_TranslucentBackground` - 透明背景
  - **注意:** 移除了 `WindowTransparentForInput` 以支持悬停提示
- **文件监视:** `QFileSystemWatcher` 实现热重载
- **系统集成:** `QSystemTrayIcon` 托盘图标
- **时间计算:** 紧凑模式时间映射算法

### 开发文档

- **快速入门:** 本 README.md
- **详细开发计划:** [jindutiao.md](jindutiao.md) - 包含 6 个阶段的完整实现步骤
- **AI 辅助开发:** [CLAUDE.md](CLAUDE.md) - Claude Code 的项目指导文件

### 代码规范

- 遵循 **PEP 8** 代码风格
- 使用类型提示(Type Hints)
- 添加文档字符串(Docstrings)
- 为关键函数编写单元测试

### 贡献指南

欢迎提交 Issue 和 Pull Request!

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 🐛 常见问题

### Q1: 进度条不显示?

**解决方案:**
- 检查是否有其他全屏程序覆盖
- 尝试切换到屏幕顶部:修改 `config.json` 中的 `"position": "top"`
- 检查 `bar_height` 是否设置过小
- 查看 `pydaybar.log` 日志文件排查错误

### Q2: 悬停提示不工作?

**原因:** 窗口可能被其他全屏应用覆盖,或鼠标没有正确悬停在任务色块上。

**解决方案:**
- 确保鼠标悬停在有颜色的任务区域
- 退出全屏应用后尝试
- 检查是否启用了鼠标跟踪(默认已启用)

### Q3: CPU 占用过高?

**解决方案:**
- 增加 `update_interval` 的值(例如改为 `60000` 表示每分钟更新一次)
- 使用线条标记代替 GIF 动画
- 禁用阴影效果: `"enable_shadow": false`
- 参考 [CLAUDE.md 性能优化部分](CLAUDE.md#performance-optimization)

### Q4: 配置修改后不生效?

**解决方案:**
- 检查 JSON 格式是否正确(使用 [JSONLint](https://jsonlint.com/) 验证)
- 手动通过托盘菜单选择"重载配置"
- 查看 `pydaybar.log` 是否有错误信息
- 确保文件保存成功(某些编辑器可能会创建临时文件)

### Q5: Windows Defender 报毒?

**原因:** PyInstaller 打包的程序可能被误报。

**解决方案:**
- 从源码运行: `python main.py`
- 添加到 Windows Defender 白名单
- 使用代码签名证书(专业用户)

### Q6: 打包后模板无法加载?

**原因:** 模板文件未包含在 PyInstaller 打包中。

**解决方案:**
- 确保 `PyDayBar.spec` 文件的 `datas=[]` 列表中包含所有模板文件
- 重新运行 `pyinstaller PyDayBar.spec`
- 详细说明请参考 [CLAUDE.md 打包说明](CLAUDE.md#⚠️-important-packaging-with-template-files)

### Q7: 统计报告窗口打不开?

**原因:** 可能是统计模块未正确打包或权限问题。

**解决方案:**
- 检查 `statistics.json` 是否可以正常创建
- 查看 `pydaybar.log` 日志文件中的错误信息
- 确保 `PyDayBar.spec` 的 `hiddenimports` 包含 `statistics_manager` 和 `statistics_gui`
- 以管理员权限运行程序

### Q8: 统计数据不更新?

**原因:** 任务状态跟踪每分钟更新一次。

**解决方案:**
- 等待至少1分钟后查看统计数据
- 点击统计窗口的"🔄 刷新"按钮手动刷新
- 确保任务时间设置正确(当前时间在任务时间范围内)
- 检查系统时间是否准确

更多问题请参考 [jindutiao.md 常见问题部分](jindutiao.md#常见问题与解决方案-faq) 或查看 `pydaybar.log` 日志文件。

## 🎯 路线图

### 当前版本 (v1.1) ✅ 已完成
- [x] 基础进度条显示
- [x] 任务可视化(紧凑模式)
- [x] 配置文件支持
- [x] 热重载
- [x] 系统托盘集成
- [x] GUI 配置管理器
- [x] 8 种预设模板
- [x] 悬停提示
- [x] 三种时间标记样式(线条/图片/GIF)
- [x] 多显示器支持
- [x] 圆角和阴影效果
- [x] 自定义模板保存/加载
- [x] 时间冲突检测
- [x] 完整日志系统
- [x] PyInstaller 打包支持
- [x] **番茄钟集成** - 可拖拽面板,可视化配置
- [x] **任务提醒通知** - 支持多种提醒时间点和免打扰时段
- [x] **番茄钟通知** - 工作/休息完成提醒

### 当前版本 (v1.2) ✅ 新增功能
- [x] **任务统计报告** - 完整的统计分析系统
  - 今日/本周/本月统计摘要
  - 任务完成率可视化(圆形进度条)
  - 任务分类统计和历史记录
  - CSV导出功能
  - 自动任务状态跟踪

### 计划中 (v1.3)
- [ ] 主题切换(深色/浅色)
- [ ] 国际化支持(英文)
- [ ] 番茄钟统计和历史记录
- [ ] 数据可视化图表增强

### 未来计划 (v2.0)
- [ ] 周视图/月视图
- [ ] 任务拖拽编辑
- [ ] 云同步支持
- [ ] 任务分类和标签
- [ ] 更丰富的数据可视化图表

## 📝 更新日志

### v1.2.0 (2025-10-30)
**新增功能:**
- ✨ 任务统计报告系统
  - 今日/本周/本月多维度统计
  - 圆形进度条可视化
  - 任务分类历史记录
  - CSV数据导出功能
  - 自动任务状态跟踪

**改进:**
- 🔧 优化打包配置,支持统计模块
- 📝 完善文档和使用说明
- 🐛 修复已知问题

### v1.1.0 (2025-10-28)
**新增功能:**
- 🍅 番茄钟集成
- 🔔 智能通知系统
- 📑 8种预设模板

### v1.0.0 (2025-10-25)
**首次发布:**
- 🎯 基础进度条功能
- 🎨 可视化配置管理器
- 🖼️ 多样时间标记
- 🔄 热重载支持

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- **PySide6** - 提供优秀的 Python Qt 绑定
- **Qt Framework** - 强大的跨平台 GUI 框架
- **所有贡献者** - 感谢每一位为项目做出贡献的开发者

## 📧 联系方式

- **项目主页:** [https://github.com/yourusername/PyDayBar](https://github.com/yourusername/PyDayBar)
- **问题反馈:** [GitHub Issues](https://github.com/yourusername/PyDayBar/issues)
- **电子邮件:** your.email@example.com

---

<div align="center">

**如果这个项目对您有帮助,请给一个 ⭐ Star!**

Made with ❤️ by [Your Name]

</div>
