# PyDayBar - 桌面日历进度条 📅

<div align="center">

一个简洁优雅的桌面时间进度条工具,实时可视化您的每日任务安排

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)

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
    "corner_radius": 0             // 圆角半径(0=直角)
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

- **打开配置** - 启动 GUI 配置管理器
- **重载配置** - 重新加载 `config.json` 和 `tasks.json`
- **切换位置** - 在屏幕顶部和底部之间切换
- **退出** - 关闭程序

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

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包主程序
pyinstaller PyDayBar.spec

# 打包配置管理器(可选)
pyinstaller PyDayBar-Config.spec

# 生成的文件在 dist/ 目录中
```

**⚠️ 重要提示:** 确保 `PyDayBar.spec` 文件中包含所有模板文件。详细打包说明请参考 [CLAUDE.md](CLAUDE.md#⚠️-important-packaging-with-template-files)。

## 🛠️ 开发指南

### 项目结构

```
PyDayBar/
├── main.py                       # 主程序入口 (1012 行)
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

更多问题请参考 [jindutiao.md 常见问题部分](jindutiao.md#常见问题与解决方案-faq) 或查看 `pydaybar.log` 日志文件。

## 🎯 路线图

### 当前版本 (v1.0) ✅ 已完成
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

### 计划中 (v1.1)
- [ ] 任务提醒通知
- [ ] 任务统计报告
- [ ] 主题切换(深色/浅色)
- [ ] 国际化支持(英文)
- [ ] 任务完成度跟踪

### 未来计划 (v2.0)
- [ ] 周视图/月视图
- [ ] 任务拖拽编辑
- [ ] 云同步支持
- [ ] 番茄钟集成
- [ ] 任务分类和标签

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
