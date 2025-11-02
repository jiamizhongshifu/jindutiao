# PyDayBar - 桌面日历进度条 📅

<div align="center">

一个简洁优雅的桌面时间进度条工具,实时可视化您的每日任务安排

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://pypi.org/project/PySide6/)
[![Version](https://img.shields.io/badge/version-1.4.3-brightgreen.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)

**当前版本: v1.4.3** | 最后更新: 2025-11-02 | Vercel云服务 ✅

</div>

---

## ✨ 核心特性

### 🎯 基础功能
- **透明置顶** - 始终显示在所有窗口之上,不干扰日常操作
- **悬停提示** - 鼠标悬停显示任务详情,支持交互式操作
- **实时更新** - 动态显示当前时间进度,精确到秒
- **高度自定义** - 支持自定义颜色、位置、高度、圆角等外观
- **热重载** - 修改配置文件即时生效,无需重启
- **轻量级** - 内存占用极低,CPU使用率几乎为0

### 📊 任务管理
- **任务可视化** - 用彩色色块直观显示全天的任务安排,紧凑模式无缝衔接
- **预设主题配色** - 多种内置主题(商务、创意、自然等),一键切换
- **自定义任务颜色** - 支持单独设置每个任务的背景色和文字颜色
- **预设模板** - 8种内置作息模板(工作日、学生、自由职业等),快速加载

### 🖼️ 视觉效果
- **多样时间标记** - 支持线条、静态图片、动画GIF三种时间标记样式
- **多显示器支持** - 可选择在任意显示器上显示
- **优化图层渲染** - 悬停提示文字始终显示在时间标记上方,确保清晰可见

### 🎛️ 配置管理
- **图形化配置界面** - 功能完善的GUI配置管理器(已集成在主程序中)
- **可视化时间轴编辑器** - 拖拽调整任务时间,实时预览
- **开机自启动管理** - 一键设置开机自启动

### 🍅 番茄钟 & 通知
- **番茄钟集成** - 内置番茄钟计时器,支持拖拽定位和可视化配置
- **智能通知** - 任务提醒和番茄钟通知,支持免打扰时段
- **任务统计报告** - 自动跟踪任务完成情况,提供多维度统计分析和数据导出

### 🤖 AI智能功能 (云服务)
- **AI智能规划** - 使用自然语言快速生成任务时间表
- **Vercel云服务** - 基于Vercel Serverless Functions的云端AI服务
- **配额管理** - 每日免费配额限制,数据持久化存储(Supabase)
- **无需本地配置** - 云端运行,无需手动启动本地服务

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
- 红色垂直线/图片/GIF标记当前时间位置,随时间移动
- 鼠标悬停在任务上时显示任务详情和时间范围

## 🚀 快速开始

### 前置要求

- **Python 3.8 或更高版本**
- **操作系统:** Windows 10/11(推荐), Linux, macOS

### 安装步骤

1. **克隆/下载项目**
   ```bash
   git clone https://github.com/jiamizhongshifu/jindutiao.git
   cd jindutiao
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

5. **打开配置界面**
   - 右键点击系统托盘图标
   - 选择"⚙️ 配置"

### 首次运行

程序首次启动时会自动创建以下文件:

- `config.json` - 应用配置文件
- `tasks.json` - 任务数据文件
- `themes.json` - 主题数据文件

## ⚙️ 配置说明

### 使用图形化配置界面(推荐)

配置管理器已集成在主程序中，通过系统托盘菜单"⚙️ 配置"即可启动。

**配置界面功能:**

#### 1. 外观配置
- 进度条高度、位置(顶部/底部)
- 背景颜色和透明度
- 圆角半径、阴影效果
- 显示器选择
- 时间标记样式(线条/图片/GIF)

#### 2. 任务管理
- **预设主题配色** - 选择内置主题,时间轴实时预览
- **可视化时间轴编辑器** - 图形化编辑任务时间
- **自定义任务颜色** - 单独设置每个任务的背景色和文字颜色
- **加载预设模板** - 快速加载常用作息模板

#### 3. 番茄钟设置
- 工作/休息时长设置
- 提醒音效选择
- 番茄钟位置调整

#### 4. 通知设置
- 任务开始/结束提醒
- 提醒提前时间
- 免打扰时段设置
- 声音开关

#### 5. 开机自启动
- 一键开启/关闭开机自启动
- 自动注册到系统启动项

### 手动编辑配置文件

您也可以直接编辑 `config.json` 和 `tasks.json` 文件。修改后保存,程序会自动重新加载。

**config.json 示例:**

```json
{
  "bar_height": 20,
  "position": "bottom",
  "background_color": "#505050",
  "background_opacity": 180,
  "marker_color": "#FF0000",
  "theme": {
    "mode": "preset",
    "current_theme_id": "business",
    "auto_apply_task_colors": false
  }
}
```

**tasks.json 示例:**

```json
[
  {
    "start": "09:00",
    "end": "12:00",
    "task": "上午工作",
    "color": "#4CAF50",
    "text_color": "#FFFFFF"
  },
  {
    "start": "12:00",
    "end": "13:00",
    "task": "午休",
    "color": "#FFC107"
  }
]
```

## 🤖 AI智能功能

### AI任务规划

使用自然语言快速生成任务时间表,基于Vercel云服务。

**使用方法:**

1. 打开配置界面 → 任务管理
2. 在"AI智能生成任务"区域输入描述:
   ```
   我是程序员,朝九晚六工作,中午休息1小时
   ```
3. 点击"生成"按钮
4. AI会自动生成完整的任务时间表
5. 点击"保存所有设置"应用

**云服务特点:**

- ✅ **自动运行** - 基于Vercel Serverless Functions,无需本地启动服务
- ✅ **配额管理** - 每日免费配额限制(免费用户: 3次/天)
- ✅ **数据持久化** - 使用Supabase数据库,配额数据实时同步
- ✅ **无需配置** - 完全云端运行,开箱即用

**配额规则(免费用户):**

- 每日任务规划: 3次/天
- 每周报告: 1次/周
- AI聊天: 10次/天
- 主题推荐: 5次/天
- 主题生成: 3次/天

**查看配额状态:**

打开配置界面,任务管理tab中会显示"✓ 今日剩余: X 次规划"

## 🎨 主题系统

### 预设主题

应用内置多种精心设计的主题配色:

- **商务专业** (business) - 深蓝、天蓝、青色,专业稳重
- **活力橙** (vibrant) - 橙色、黄色、绿色,充满活力
- **自然清新** (nature) - 绿色系,清新自然
- **创意彩虹** (creative) - 多彩渐变,富有创意
- **深夜** (dark) - 深色系,护眼舒适
- **柔和粉** (pastel) - 粉色系,温柔可爱

**使用方法:**

1. 打开配置界面 → 任务管理
2. 在"预设主题配色"下拉菜单中选择主题
3. 时间轴编辑器会实时预览颜色变化
4. 点击"保存所有设置"应用主题到进度条

**特性:**

- ✅ 实时预览 - 选择主题时,时间轴编辑器立即显示预览
- ✅ 保存应用 - 点击保存后,进度条颜色立即更新
- ✅ 持久化 - 重启应用后主题仍然生效

### 自定义任务颜色

除了使用预设主题,您还可以单独设置每个任务的颜色:

1. 在任务表格中,每个任务都有"背景颜色"和"文字颜色"列
2. 点击"选色"按钮选择颜色,或直接输入颜色代码
3. 颜色预览框会实时显示选择的颜色
4. 保存后生效

## 📦 打包发布

### 使用PyInstaller打包

项目提供了打包配置文件 `PyDayBar.spec`:

```bash
# 清理旧文件
rm -rf build dist

# 打包
pyinstaller PyDayBar.spec

# 生成的exe位于
dist/PyDayBar-v1.4.exe
```

**打包特点:**

- **文件大小**: 约55 MB
- **启动速度**: 1-2秒
- **配置管理器**: 已集成在主程序中
- **AI功能**: 使用Vercel云服务,无需打包本地服务

**重要提醒**:
修改Python源代码后,必须重新打包才能在exe中生效。详见 [PyInstaller开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md)。

## 📁 项目结构

```
PyDayBar/
├── main.py                      # 主程序入口
├── config_gui.py                # 配置管理器(已集成)
├── ai_client.py                 # AI客户端(调用Vercel API)
├── theme_manager.py             # 主题管理器
├── timeline_editor.py           # 时间轴编辑器
├── notification_manager.py      # 通知管理器
├── statistics_manager.py        # 统计管理器
├── autostart_manager.py         # 开机自启动管理器
├── PyDayBar.spec                # PyInstaller打包配置
├── requirements.txt             # Python依赖
├── config.json                  # 配置文件(自动生成)
├── tasks.json                   # 任务数据(自动生成)
├── themes.json                  # 主题数据(自动生成)
├── api/                         # Vercel云服务(部署在Vercel)
│   ├── quota_manager.py         # 配额管理器
│   ├── quota-status.py          # 配额查询API
│   ├── plan-tasks.py            # AI任务生成API
│   ├── health.py                # 健康检查API
│   └── requirements.txt         # Vercel依赖
└── docs/                        # 文档目录
    ├── PYINSTALLER_DEVELOPMENT_METHODOLOGY.md
    ├── TASK_COLOR_RESET_FIX.md
    ├── QUOTA_SYSTEM_README.md
    └── ...
```

## 🎯 键盘快捷键

主程序:
- **右键** - 打开系统托盘菜单
- **左键** - (预留功能)

配置管理器:
- **Ctrl+S** - 保存所有设置
- **Esc** - 关闭窗口

## ❓ 常见问题

### Q1: 进度条不显示?

**检查清单:**
1. 确认程序正在运行(系统托盘应该有图标)
2. 检查是否被其他窗口遮挡(尝试切换到顶部/底部)
3. 查看 `pydaybar.log` 日志文件

### Q2: 修改配置后没有生效?

**解决方案:**
- 如果修改的是 `config.json` 或 `tasks.json`,应该会自动重新加载
- 如果没有生效,尝试重启应用
- 如果修改的是源代码,需要重新打包exe

### Q3: 主题保存后进度条颜色没有变化?

**原因:** 这个问题在v1.4.3中已修复。

**v1.4.3更新:**
- 保存主题时自动应用主题颜色到任务数据
- reload_all()方法中添加主题重新应用逻辑
- 确保保存后进度条立即刷新

### Q4: AI智能规划显示"无法连接云服务"?

**可能原因:**
1. 网络连接问题
2. Vercel服务暂时不可用
3. API配额已用完

**解决方案:**
- 检查网络连接
- 查看配额状态(配置界面中显示)
- 等待配额重置(每日0点重置)
- 查看日志文件 `pydaybar.log` 了解详细错误

### Q5: 如何设置开机自启动?

**方法一: 使用配置界面(推荐)**
1. 打开配置界面 → 外观配置
2. 勾选"开机自启动"
3. 点击保存

**方法二: 手动设置**

Windows:
- 按 `Win+R`,输入 `shell:startup`
- 将 PyDayBar 的快捷方式复制到打开的文件夹

Linux:
- 创建 `~/.config/autostart/pydaybar.desktop`
- 添加应用启动命令

macOS:
- 系统偏好设置 → 用户与群组 → 登录项
- 添加 PyDayBar 应用

### Q6: 配额什么时候重置?

**重置规则:**
- 每日配额: 每天 0:00 (UTC+8) 重置
- 每周配额: 每周一 0:00 (UTC+8) 重置

**查看配额:**
打开配置界面,任务管理tab会实时显示剩余配额。

## 🔗 相关文档

### 开发文档
- [PyInstaller开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md) - 打包应用的开发调试最佳实践
- [UI状态同步问题诊断法](CLAUDE.md#ui-state-synchronization-troubleshooting) - GUI状态同步问题的系统化诊断方法
- [任务配色重置Bug修复记录](TASK_COLOR_RESET_FIX.md) - 完整的问题诊断和修复过程

### 云服务文档
- [Vercel部署指南](api/README.md) - Vercel Serverless Functions部署说明
- [配额系统说明](QUOTA_SYSTEM_README.md) - 配额管理系统使用指南
- [Vercel部署问题排查](VERCEL_404_TROUBLESHOOTING.md) - 常见部署问题及解决方案

### 方法论文档
- [CLAUDE.md](CLAUDE.md) - AI助手配置和方法论库

## 🔄 更新日志

### v1.4.3 (2025-11-02) - UI状态同步优化 ✅

**🎨 主题系统增强**
- 修复主题保存后进度条未立即刷新的问题
- 保存时自动应用主题颜色到任务数据
- reload_all()中添加主题重新应用逻辑
- 实现"选择→预览→保存→立即生效"的完整流程

**🛠️ 配置管理优化**
- 移除"应用配色到所有任务"按钮(简化操作)
- 修复通知设置tab重复加载问题
- 主题切换时仅预览,不自动应用到进度条

**📚 方法论沉淀**
- 添加"UI状态同步问题诊断法"到CLAUDE.md
- 5步诊断法: 数据流图→预览/持久化→断裂点→修复策略→验证
- 包含完整案例研究和最佳实践
- 提供快速诊断卡和常见原因统计

**🔧 代码修改**
- `config_gui.py:2188-2219` - 保存时应用主题颜色
- `config_gui.py:2245` - 使用主题颜色而非输入框颜色
- `main.py:1826-1831` - reload_all()中重新加载主题

**🧹 项目清理**
- 删除旧的配置程序 `PyDayBar-Config-v1.4.exe`
- 删除本地后端配置文件 `.env`
- 删除旧的spec文件 `PyDayBar-Config*.spec`
- 只保留必要文件

### v1.4.2 (2025-11-01) - Vercel云服务部署 ✅

**☁️ 完全切换到云服务**
- 成功部署Vercel Serverless Functions
- 基于Supabase的真实配额管理系统
- 移除所有本地后端相关代码

**🔐 安全性增强**
- API密钥存储在Vercel环境变量中
- 客户端无法获取密钥
- 云端配额验证和扣除

**🌐 API端点**
- `/api/health` - 健康检查
- `/api/quota-status` - 配额查询
- `/api/plan-tasks` - AI任务生成

**📊 配额规则**
- 每日任务规划: 3次/天
- 每周报告: 1次/周
- AI聊天: 10次/天
- 主题推荐: 5次/天
- 主题生成: 3次/天

### v1.4.1 (2025-11-01) - 配置管理器整合 🎯

**🔧 核心架构调整**
- 配置管理器完全整合到主程序中
- 通过系统托盘菜单"配置"访问
- 无需单独的配置程序exe

**🎨 UI增强**
- 预设主题选择功能
- 任务颜色自定义(背景色+文字颜色)
- 时间轴实时预览

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📧 联系方式

如有问题或建议,请通过以下方式联系:

- GitHub Issues: [项目Issue页面](https://github.com/jiamizhongshifu/jindutiao/issues)
- Email: (待添加)

---

<div align="center">

Made with ❤️ by PyDayBar Team

⭐ 如果觉得这个项目不错,请给我们一个Star! ⭐

</div>
