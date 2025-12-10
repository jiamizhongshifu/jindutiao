# GaiYa每日进度条 🌍

<div align="center">

![GaiYa Logo](gaiya-logo2.png)

**让每一天都清晰可见** ⏱️

用进度条让时间流逝清晰可见的桌面工具

[![最新版本](https://img.shields.io/github/v/release/jiamizhongshifu/jindutiao?label=%E6%9C%80%E6%96%B0%E7%89%88%E6%9C%AC&color=brightgreen)](https://github.com/jiamizhongshifu/jindutiao/releases/latest)
[![下载量](https://img.shields.io/github/downloads/jiamizhongshifu/jindutiao/total?label=%E4%B8%8B%E8%BD%BD%E9%87%8F&color=blue)](https://github.com/jiamizhongshifu/jindutiao/releases)
[![Stars](https://img.shields.io/github/stars/jiamizhongshifu/jindutiao?style=social)](https://github.com/jiamizhongshifu/jindutiao/stargazers)
[![Forks](https://img.shields.io/github/forks/jiamizhongshifu/jindutiao?style=social)](https://github.com/jiamizhongshifu/jindutiao/network/members)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.4+-green.svg)](https://pypi.org/project/PySide6/)
[![Issues](https://img.shields.io/github/issues/jiamizhongshifu/jindutiao?label=Issues)](https://github.com/jiamizhongshifu/jindutiao/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**🌐 [访问官网](https://www.gaiyatime.com)** | **📥 [下载应用](https://github.com/jiamizhongshifu/jindutiao/releases/latest)** | **📖 [查看文档](#-文档导航)** | **🤝 [参与贡献](CONTRIBUTING.md)**

当前版本: **v1.6.11** | 最后更新: 2025-12-08 | 🔒 **企业级安全认证** | 🌍 **全球支付支持**

</div>

---

## 📸 功能预览

<div align="center">

<!-- 请在此处更新最新版本的主界面截图，以展示实时进度条功能 -->
*主界面：实时进度条*

<!-- 请在此处更新最新版本的配置界面截图，以展示丰富的自定义选项 -->
*配置界面：丰富的自定义选项*

<!-- 请在此处更新最新版本的AI生成功能截图，以展示自然语言生成任务计划 -->
*AI功能：自然语言生成任务计划*

</div>

> 💡 **提示**: 首次使用建议查看 [快速开始](#-快速开始) 章节

---

## ✨ 核心特性

| 功能分类 | 特性说明 |
|---------|---------|
| **🎯 桌面进度条** | 透明置顶、实时更新、悬停提示、点击穿透 |
| **📊 任务管理** | 可视化色块、12种预设模板、自定义颜色、智能时间表 |
| **💬 弹幕系统** | **630+条丰富内容**、5种动态变量、智能防重复、随机化生成、上下文感知、60fps流畅动画、**450+行为感知弹幕** |
| **🔍 行为识别** | **实时活动追踪**、智能行为分析、5种行为趋势检测、应用分类管理、弹幕智能触发、概率控制、三级冷却机制 |
| **🎨 主题系统** | 6种预设主题、AI主题生成、实时预览 |
| **🖼️ 场景系统** | 可视化编辑器（已集成到主应用）、拖拽式设计、场景导入导出、道路层配置 |
| **🤖 AI功能** | 自然语言生成任务（免费版3次/天）、智能配色推荐 |
| **🍅 番茄钟** | 集成番茄钟、智能通知、免打扰模式 |
| **📈 数据统计** | 任务完成跟踪、多维度分析、数据导出（会员功能） |
| **⚙️ 配置管理** | 图形化界面、时间轴编辑、开机自启动 |
| **💎 会员系统** | 月付(¥29)/年付(¥199)/会员合伙人(¥599限量1000名)，支持国内支付（微信）和国际支付（Stripe），解锁AI配额、去水印、专属社群 |

---

## 🌟 为什么选择 GaiYa

### 开源透明

- ✅ **完全开源**: 所有代码公开审计，无隐藏行为
- ✅ **MIT 协议**: 自由使用、修改和分发
- ✅ **活跃维护**: 持续更新，快速响应 Issues
- ✅ **社区驱动**: 欢迎贡献，共同成长

### 技术优势

- 🎯 **现代技术栈**: Python 3.11+ + PySide6 + Vercel
- 🤖 **AI 赋能**: Claude 3.5 Sonnet 智能生成任务
- ☁️ **云原生**: Serverless 架构，开箱即用
- 🔒 **企业级安全**: 通过全面安全审计（11/12项已修复，91.7%完成率）
  - ✅ SSL证书验证 - 防止MITM攻击
  - ✅ API速率限制 - 防止滥用和DDoS
  - ✅ Token加密存储 - 使用系统级密钥链（Windows DPAPI/macOS Keychain）
  - ✅ 输入验证增强 - RFC 5322邮箱验证、UUID/Decimal严格校验
  - ✅ 日志安全规范 - 敏感信息自动脱敏
  - ✅ CORS白名单保护 - 所有21个API端点已配置
  - ✅ 支付安全 - 时间戳验证、签名校验
  - 📊 完整测试覆盖 - 94个单元测试（100%通过率）

### 用户友好

- 🎨 **精美设计**: Material Design 风格
- 📱 **轻量高效**: 单文件绿色版，约82MB（含场景编辑器）
- ⚙️ **高度可定制**: 6种主题 + AI配色 + 完全自定义
- 🆓 **Freemium 模式**: 核心功能免费，高级功能解锁

---

## 🚀 快速开始

### 系统要求

| 项目 | 要求 |
|-----|------|
| 操作系统 | Windows 10/11 (64位) |
| 内存 | ≥ 4GB RAM |
| 磁盘空间 | ≥ 100MB |
| 网络 | 使用AI功能需要联网 |

### 方式一：下载可执行文件（推荐新手）

1. **下载最新版本**
   - 访问 [Releases 页面](https://github.com/jiamizhongshifu/jindutiao/releases/latest)
   - 下载 `GaiYa-v1.6.3.exe` (约82MB，含场景编辑器)

2. **首次运行**
   ```
   双击 GaiYa-v1.6.3.exe → 系统托盘出现图标
   ```

3. **打开配置**
   ```
   右键系统托盘图标 → "⚙️ 配置"
   ```

4. **开机自启动**（可选）
   ```
   配置界面 → 外观设置 → 勾选"开机自启动"
   ```

> ⚠️ **杀毒软件提示**: 部分杀毒软件可能误报，请添加信任。详见 [安全说明](#-关于安全)

### 方式二：从源码运行（推荐开发者）

```bash
# 1. 克隆项目
git clone https://github.com/jiamizhongshifu/jindutiao.git
cd jindutiao

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行主程序
python main.py
```

**开发环境推荐**:
- Python 3.11+
- IDE: VS Code / PyCharm
- 调试工具: PySide6 DevTools

---

## 🛠️ 技术栈

### 核心技术

| 技术 | 用途 | 版本 |
|-----|------|------|
| **Python** | 主要编程语言 | 3.11+ |
| **PySide6** | GUI框架 | 6.4+ |
| **PyInstaller** | 应用打包 | 6.16+ |
| **Requests** | HTTP客户端 | 2.31+ |

### 后端服务

| 服务 | 用途 |
|-----|------|
| **Vercel** | Serverless Functions托管 |
| **Supabase** | 用户认证与数据库 |
| **ZPAY** | 国内支付网关（微信支付） |
| **Stripe** | 国际支付网关（支持Visa/Mastercard等） |

### AI 服务

| 模型 | 用途 |
|-----|------|
| **Claude 3.5 Sonnet** | 任务生成 |
| **Claude Haiku** | 配色建议 |

---

## 📐 架构设计

```
GaiYa/
├── main.py                  # 主程序入口
├── config_gui.py            # 配置界面
├── gaiya/                   # 核心模块（规划中）
│   ├── ui/                  # UI组件
│   ├── core/                # 核心逻辑
│   └── utils/               # 工具函数
├── api/                     # Vercel Serverless Functions
│   ├── health.py            # 健康检查
│   ├── quota-status.py      # 配额查询
│   ├── plan-tasks.py        # AI任务生成
│   └── ...
├── templates/               # 任务模板
└── tests/                   # 测试用例
```

**核心组件**:
- `ProgressBar`: 主进度条窗口
- `ConfigGui`: 配置管理界面
- `ThemeManager`: 主题管理器
- `AuthClient`: 认证客户端
- `AIClient`: AI服务客户端

---

## 🔒 关于安全

**GaiYa 是完全开源的软件，所有代码公开可审计。**

### 为什么会被杀毒软件误报？

部分杀毒软件可能因 PyInstaller 打包方式误报，这是 Python 应用的常见问题。

**解决方案**：
- ✅ **已优化**: v1.4.0+ 禁用 UPX 压缩，大幅减少误报
- 🛡️ **添加信任**:
  - Windows Defender: [查看详细步骤](SECURITY.md#windows-defender-添加信任)
  - 360安全卫士: [查看详细步骤](SECURITY.md#360-安全卫士)
  - 火绒安全: [查看详细步骤](SECURITY.md#火绒安全)
- 🔨 **从源码构建**: 自己构建最安全（见下方构建说明）

### 隐私保护

- ✅ **开源透明**: 所有代码公开，无隐藏行为
- ✅ **最小权限**: 仅使用必要的系统权限
- ✅ **数据本地**: 配置文件存储在本地
- ✅ **可选联网**: 仅AI功能需要联网，可完全离线使用

详见: [安全说明文档](SECURITY.md)

---

## ⚙️ 核心配置

通过系统托盘菜单 "⚙️ 配置" 打开配置界面，或使用环境变量进行高级配置：

### 1. 外观设置
- 进度条高度 (2-50px，支持极细模式)、位置（顶部/底部）、透明度 (0-255)
- 背景颜色、阴影效果（已集成至弹幕设置）
- 多显示器支持
- 时间标记样式（线条/图片/GIF动画）
- 开机自启动

### 2. 任务管理
- **预设主题**: 6种内置配色（商务、活力、自然等）
- **任务编辑**: 可视化时间轴，拖拽调整
- **模板库**: 12种作息模板（工作日、学生、自由职业等）
- **时间表**: 自动应用规则（按日期/星期/月份）
- **AI生成**: 自然语言描述 → 完整任务表

### 3. AI 功能
- **智能生成**: 支持自然语言描述
  ```
  示例：我是程序员，朝九晚六工作，中午休息1小时
  ```
- **配额管理**:
  - 免费用户: 3次/天
  - 会员: 无限次
- **云服务**: 基于 Vercel，无需本地配置

### 4. 其他
- **番茄钟**: 自定义时长、通知提醒
- **统计报告**: 任务完成率、时间分布（会员功能）
- **免打扰模式**: 自定义时段关闭通知

### 5. 环境变量配置（高级）

支持通过环境变量覆盖默认配置，适用于开发、测试和生产环境：

**应用基础**:
- `APP_NAME` - 应用名称（默认：GaiYa）
- `ENVIRONMENT` - 运行环境（development/production，默认：production）
- `LOG_LEVEL` - 日志级别（DEBUG/INFO/WARNING/ERROR，默认：INFO）

**服务URL**:
- `FRONTEND_URL` - 前端URL（默认：https://jindutiao.vercel.app）
- `TUZI_BASE_URL` - 兔子AI API（默认：https://api.tu-zi.com/v1）
- `ZPAY_API_URL` - Zpay支付网关（默认：https://zpayz.cn）

**CORS配置**:
- `CORS_ALLOWED_ORIGINS` - 允许的源列表（逗号分隔）
  ```bash
  # 示例
  CORS_ALLOWED_ORIGINS="https://app1.com,https://app2.com"
  ```
  **注意**: 开发环境（`ENVIRONMENT=development`）会自动添加 localhost 域名

**订阅价格**（用于动态调整定价）:
- `PLAN_PRICE_PRO_MONTHLY` - 月度会员价格（默认：29.0）
- `PLAN_PRICE_PRO_YEARLY` - 年度会员价格（默认：199.0）
- PLAN_PRICE_LIFETIME - 会员合伙人价格（默认：599.0）

**数据库**:
- `SUPABASE_URL` - Supabase项目URL（必需）
- `SUPABASE_KEY` - Supabase匿名密钥（必需）
- `SUPABASE_SERVICE_KEY` - 服务角色密钥（可选）

**安全**:
- `DISABLE_SSL_VERIFY` - 禁用SSL验证（仅开发/测试，默认：false）
- `LOG_VERBOSE` - 详细日志模式（默认：false）

**配置文件**:
- `config.json`: 外观与系统设置
- `tasks.json`: 任务与时间表
- `themes.json`: 主题配色

编辑配置文件后会自动重载，无需重启。

**配置验证**: 启动时自动检查必需的环境变量（SUPABASE_URL、SUPABASE_KEY），缺失时会输出警告。

---

## 🤖 AI 智能功能

### 使用方法

1. **打开AI生成面板**
   ```
   配置界面 → 任务管理 → AI生成区域
   ```

2. **输入描述**（支持自然语言）
   ```
   我是程序员，朝九晚六工作，中午休息1小时
   上午主要写代码，下午开会和代码审查
   ```

3. **生成任务表**
   ```
   点击"生成" → AI自动规划完整任务表
   ```

4. **预览与调整**
   ```
   在时间轴编辑器中微调细节
   ```

5. **保存应用**
   ```
   点击"保存" → 进度条立即更新
   ```

### 云服务特点

| 特点 | 说明 |
|------|------|
| ✅ **自动运行** | 基于 Vercel Serverless，无需本地启动服务 |
| ✅ **配额管理** | 免费用户：3次/天，会员：无限次 |
| ✅ **数据持久化** | 配额实时同步（Supabase） |
| ✅ **无需配置** | 开箱即用，零配置 |
| ✅ **高可用** | Vercel全球CDN加速 |

### 常见AI生成示例

<details>
<summary><strong>示例1: 程序员工作日</strong></summary>

**输入**:
```
程序员，朝九晚六，中午休息1小时
上午写代码，下午开会和代码审查
```

**生成结果**:
- 09:00-12:00: 深度编码
- 12:00-13:00: 午餐休息
- 13:00-15:00: 会议/沟通
- 15:00-18:00: 代码审查
</details>

<details>
<summary><strong>示例2: 学生学习计划</strong></summary>

**输入**:
```
高中生，早上8点开始学习
上午两节课，下午两节课，晚上自习
```

**生成结果**:
- 08:00-10:00: 语文数学
- 10:00-12:00: 英语物理
- 14:00-16:00: 化学生物
- 19:00-22:00: 自习复习
</details>

---

## 📦 构建与发布

### 本地构建

**推荐方式：使用构建脚本（Windows）**

项目提供了两个优化的构建脚本，大幅提升打包效率：

#### 1️⃣ 快速增量构建（日常开发推荐）
```bash
# 双击运行或命令行执行
build-fast.bat
```

**优势**：
- ⚡ 利用 PyInstaller 缓存，速度提升 **50-87%**
- 📊 修改 UI 代码：10-20秒（原耗时 60-90秒）
- 🔧 修改业务逻辑：20-30秒
- 📝 修改注释/文档：8-15秒

**适用场景**：
- ✅ 日常开发迭代
- ✅ UI 样式调整
- ✅ 业务逻辑修改

#### 2️⃣ 完全重建（异常时使用）
```bash
# 双击运行或命令行执行
build-clean.bat
```

**特点**：
- 🔧 删除所有缓存（build/ 和 dist/ 目录）
- 🔄 完全重新分析和打包所有依赖
- ⏱️ 耗时 60-90秒

**适用场景**：
- ⚠️ 修改了 `Gaiya.spec` 配置文件
- ⚠️ 添加/删除了 hiddenimports
- ⚠️ 更新了 PySide6 或其他依赖库
- ⚠️ `build-fast.bat` 打包失败时
- ⚠️ 出现缓存损坏等异常

> 📖 **详细文档**：[BUILD_SCRIPTS_README.md](BUILD_SCRIPTS_README.md)

#### 手动构建（备选方式）
```bash
# 1. 清理旧文件
rm -rf build dist

# 2. 打包（使用 Gaiya.spec）
pyinstaller Gaiya.spec

# 3. 测试生成的exe
./dist/GaiYa-v1.6.3.exe

# 输出文件
dist/GaiYa-v1.6.3.exe  # 约 82 MB，单文件绿色版（含场景编辑器）
```

### 打包配置

**关键配置** (Gaiya.spec):
```python
# 禁用UPX压缩（减少杀毒误报）
upx=False

# 隐藏控制台窗口
console=False

# 应用图标
icon='gaiya-logo2.ico'

# 数据文件（任务模板、图片等）
datas=[
    ('tasks_template_*.json', '.'),
    ('templates_config.json', '.'),
    ('kun.webp', '.'),
    # ...更多数据文件
]
```

**重要**:
- 修改源代码后必须重新打包才能在 exe 中生效
- 详见: [PyInstaller开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md)

### CI/CD（规划中）

```yaml
# 未来计划：GitHub Actions 自动构建
- Windows 自动打包
- 自动发布 Release
- 自动上传构建产物
```

---

## 📚 文档导航

### 🛠️ 开发文档
- [快速参考手册](QUICKREF.md) - 项目结构、核心类、常用命令
- [PyInstaller开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md) - 打包应用开发调试最佳实践
- [UI样式修改问题诊断](docs/UI_STYLE_MODIFICATION_TROUBLESHOOTING.md) - 修改代码但UI未生效的排查方法
- [AI助手配置](CLAUDE.md) - AI协作开发指南与方法论（内部使用）

### 🔒 安全与测试
- [安全修复进度报告](SECURITY_FIX_PROGRESS.md) - 完整的安全审计与修复记录（11/12项已完成）
- [测试覆盖报告](tests/) - 单元测试与集成测试（94个测试用例，100%通过率）
- [HTTP工具迁移指南](api/HTTP_UTILS_MIGRATION_GUIDE.md) - 代码重构最佳实践
- [速率限制集成指南](api/RATE_LIMIT_INTEGRATION_GUIDE.md) - API速率限制使用文档

### ☁️ 云服务部署
- [Vercel部署指南](api/README.md) - Serverless Functions 部署说明
- [配额系统说明](QUOTA_SYSTEM_README.md) - 配额管理使用指南
- [部署问题排查](VERCEL_404_TROUBLESHOOTING.md) - 常见问题解决

### 📝 项目管理
- [更新日志](CHANGELOG.md) - 完整版本历史
- [安全说明](SECURITY.md) - 隐私保护与杀毒软件误报
- [开发路线图](ROADMAP_v1.5.md) - 功能规划
- [贡献指南](CONTRIBUTING.md) - 如何参与项目贡献

---

## 🔄 最新更新

### v1.6.13 (2025-12-10) - 统计报告界面优化 📊

#### 🎨 UI修复与优化

- ✅ **表格序号字体修复** - 解决序号列使用特殊字体显示异常的问题
  - 分离水平表头(列标题)和垂直表头(行号)样式
  - 统一使用系统标准字体: "Microsoft YaHei", "Segoe UI", Arial, sans-serif
  - 修复 `apply_theme()` 方法覆盖表格创建时样式的问题
  - 影响范围: 本周统计、本月统计、任务分类三个标签页

- ✅ **成就展示优化** - 未解锁成就现在完整展示给用户
  - 移除 "???" 和 "解锁后可见" 的隐藏逻辑
  - 未解锁成就显示完整名称和描述信息
  - 使用灰色文本视觉区分已解锁/未解锁状态
  - 添加调试日志记录成就统计信息
  - 空状态显示: "🎉 恭喜!你已解锁所有成就!"

#### 🔧 技术实现

- 📁 **修复文件**: [statistics_gui.py](statistics_gui.py)
  - 行 1076-1091, 1247-1262, 1302-1318: 表格创建时样式设置
  - 行 1600-1615: `apply_theme()` 方法样式统一
  - 行 2720-2746: 成就展示逻辑优化
  - 行 2854-2856, 2878-2881: 成就卡片文本显示

- 🎯 **关键修复**:
  ```python
  # 表头样式分离
  QHeaderView::section {
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
  }
  QHeaderView:horizontal::section {  # 列标题
      border-bottom: 2px solid ...;
  }
  QHeaderView:vertical::section {  # 行号
      border-right: 1px solid ...;
      text-align: center;
  }

  # 成就始终显示
  name_label = QLabel(achievement.name)  # 不再隐藏
  desc_label = QLabel(achievement.description)  # 完整描述
  ```

#### 💡 用户体验提升

- 📊 **表格可读性**: 序号使用标准字体,不再出现特殊字符显示异常
- 🏆 **成就激励**: 用户可清楚看到所有未解锁成就的解锁条件
- 🎯 **目标明确**: 知道还有哪些成就可以挑战,提升使用动力

---

### v1.6.12 (2025-12-08) - 行为识别 × 弹幕系统 🔍💬

#### 🧠 智能行为识别系统

- ✅ **实时活动追踪** - 后台采集用户应用使用情况(5秒间隔可调)
  - 应用名称、窗口标题、URL识别
  - 使用时长统计
  - 数据本地存储,可设置保留期限(7-365天)

- ✅ **行为智能分析** - 5种行为趋势自动检测
  - `focus_steady`: 专注稳定(连续使用生产力应用)
  - `moyu_start`: 摸鱼开始(切换到娱乐应用)
  - `moyu_steady`: 摸鱼稳定(持续使用娱乐应用)
  - `mode_switch`: 模式切换(生产↔消费模式转换)
  - `task_switch`: 任务切换(频繁切换应用)

- ✅ **应用智能分类** - 自动识别应用类型
  - 生产力(PRODUCTIVE): IDE、Office、设计工具
  - 摸鱼(LEISURE): 视频、社交、游戏
  - 中性(NEUTRAL): 浏览器、聊天、系统工具
  - 可自定义应用分类规则

#### 💬 行为感知弹幕系统

- ✅ **450+行为弹幕模板库** - 根据行为触发个性化弹幕
  - 专注稳定: 50条鼓励性弹幕
  - 摸鱼开始: 50条调侃性弹幕
  - 摸鱼稳定: 50条吐槽性弹幕
  - 模式切换: 50条观察性弹幕
  - 任务切换: 50条建议性弹幕
  - 6种语调: 吐槽、调侃、鼓励、观察、吃瓜、建议

- ✅ **事件驱动架构** - 智能触发机制
  - 优先级队列(HIGH/MEDIUM/LOW)
  - 概率触发(30-50%可调)
  - 时间抖动(±5秒随机化)
  - 三级冷却机制:
    - 全局冷却: 30秒(所有弹幕)
    - 分类冷却: 60秒(同类行为)
    - 语调冷却: 120秒(同种语调)

- ✅ **上下文感知模板** - 弹幕内容与行为深度关联
  - `{app}`: 当前应用名称
  - `{domain}`: 网站域名
  - `{duration_min}`: 活动持续时间
  - 示例: "已经在B站摸了15分钟了,要不要回去工作?"

#### 🎛️ 配置界面集成

- ✅ **新增"🔍 行为识别"Tab** - 统一管理所有设置
  - 左侧面板:
    - ⚙️ 基本设置: 启用追踪、采样间隔、数据保留
    - 💬 弹幕行为识别: 启用弹幕、采集间隔、触发概率、冷却时间
    - 💡 使用说明: 帮助文本
  - 右侧面板:
    - 📱 应用分类管理: 打开分类设置、统计显示
    - 统计信息: PRODUCTIVE/LEISURE/NEUTRAL数量

- ✅ **应用分类设置窗口** - 完整的分类管理界面
  - 应用列表: 所有已追踪应用
  - 分类下拉框: 4种分类选择
  - 忽略开关: 排除特定应用
  - 刷新/添加/导入功能

#### 🔧 技术实现

- 📁 **核心模块**:
  - `gaiya/core/activity_collector.py`: 活动数据采集
  - `gaiya/core/behavior_analyzer.py`: 行为趋势分析
  - `gaiya/core/danmaku_event_engine.py`: 事件驱动引擎
  - `gaiya/core/cooldown_manager.py`: 冷却管理器
  - `gaiya/core/behavior_danmaku_manager.py`: 行为弹幕管理器

- 📊 **数据文件**:
  - `gaiya/data/behavior_danmaku.json`: 450+行为弹幕模板
  - `gaiya/data/app_categories.json`: 应用分类规则库

- ⚙️ **配置项** (config.json):
  ```json
  "activity_tracking": {
    "enabled": false,
    "polling_interval": 5,
    "data_retention_days": 90
  },
  "behavior_recognition": {
    "enabled": false,
    "collection_interval": 5,
    "trigger_probability": 0.4,
    "global_cooldown": 30,
    "category_cooldown": 60,
    "tone_cooldown": 120
  }
  ```

#### 💡 使用效果

- 📈 **弹幕多样性**: 从630条 → 1080+条(630通用 + 450行为)
- 🎯 **个性化提升**: 弹幕与用户实际行为强关联
- 🎭 **趣味性增强**: 智能检测摸鱼行为,幽默提醒
- 🔒 **隐私保护**: 所有数据本地存储,不上传云端
- 📊 **统计分析**: 了解自己的应用使用习惯

---

### v1.6.11 (2025-12-08) - 弹幕系统全面升级 💬✨

#### 🎯 弹幕内容大扩充

- ✅ **内容库扩充5倍** - 从~150条扩充至~630条丰富内容
  - work工作: 10 → 50条
  - study学习: 10 → 50条
  - rest休息: 10 → 50条
  - exercise运动: 10 → 50条
  - meeting会议: 10 → 50条
  - meal用餐: 10 → 50条
  - commute通勤: 4 → 20条
  - commute_morning早高峰: 10 → 40条
  - commute_evening晚高峰: 10 → 40条
  - entertainment娱乐: 10 → 50条
  - sleep睡眠: 10 → 50条
  - default默认: 15 → 50条
  - motivational励志: 15 → 50条

#### 🎭 模板化弹幕系统

- ✅ **动态变量支持** - 弹幕内容与用户任务紧密关联
  - `{task_name}`: 当前任务名称
  - `{elapsed}`: 已用时间(分钟)
  - `{remaining}`: 剩余时间(分钟)
  - `{progress}`: 完成百分比(0-100)
  - `{time_period}`: 时间段(早晨/上午/下午/晚上/深夜)
- ✅ **上下文感知** - 根据任务进度和时间段生成个性化提示
  - 示例: "「工作」已完成65%,还剩35分钟,继续加油!"
  - 示例: "上午时光,专注工作效率最高"

#### 🔄 防重复机制

- ✅ **智能历史追踪** - 记录最近20条弹幕,避免短时间重复
- ✅ **自动清理策略** - 当可选内容不足时智能清理旧历史
- ✅ **多样性保证** - 630条内容库+防重复机制,弹幕不再单调

#### 🎲 随机性优化

- ✅ **时间随机化** - 生成间隔基准频率±30%浮动
  - 例: 30秒频率 → 21-39秒随机出现
- ✅ **Y轴随机偏移** - ±15px位置变化,避免轨迹固定
- ⚠️ **保持稳定** - 速度和字体大小不变,确保阅读体验

#### 🔧 技术实现

- 📁 内容库: [gaiya/data/danmaku_presets.json](gaiya/data/danmaku_presets.json)
- 🔨 核心逻辑: [gaiya/core/danmaku_manager.py](gaiya/core/danmaku_manager.py)
  - `should_spawn_danmaku()`: 随机时间生成
  - `spawn_danmaku()`: Y轴随机偏移 + 模板替换
  - `_select_non_repeat_content()`: 防重复选择
  - `_apply_template()`: 变量替换(5种动态变量)
  - `_update_current_task_info()`: 任务信息实时缓存

#### 💡 升级效果

- 📈 **多样性提升**: 内容数量增加4.2倍(150→630)
- 🎯 **相关性提升**: 弹幕与用户任务深度关联
- 🎭 **趣味性提升**: 动态变量+随机性,每次都有惊喜
- 🔄 **重复率降低**: 从经常重复 → 几乎不重复

---

### v1.6.10 (2025-12-09) - UI优化与配置整合 🎨

#### 🎨 弹幕设置优化

- ✅ **视觉效果整合** - 将阴影效果设置整合至弹幕设置分组,统一管理
- ✅ **UI布局优化** - 输入框宽度统一调整为80px,界面更加紧凑美观
- ✅ **参数调整增强** - 弹幕透明度、移动速度等参数支持实时调整

#### ⚙️ 配置简化

- ✅ **圆角设置移除** - 进度条圆角固定为0,无需用户手动配置
- ✅ **配置界面精简** - 移除不必要的配置项,降低用户选择负担
- ✅ **配置保存优化** - 确保所有弹幕参数正确保存和加载

#### 🔧 技术改进

- ✅ QFormLayout 正确使用两列布局模式
- ✅ 输入控件宽度标准化至80px
- ✅ 配置保存/加载逻辑验证和优化

---

### v1.6.9 (2025-12-08) - 支付流程完整修复 💳

**💰 支付自动识别功能完整修复**
- ✅ **绕过 Vercel 缓存** - 直接调用 manual_upgrade API 验证支付状态
- ✅ **真实支付验证** - manual_upgrade API 添加 Z-Pay 真实支付验证,防止未支付激活
- ✅ **Webhook 回调机制** - 实现支付成功自动激活,替代轮询方式
- ✅ **数据库架构修复** - 添加 users.tier 和 subscription_expires_at 字段
- ✅ **RPC 函数绕过缓存** - 创建 upgrade_user_subscription 函数解决 PostgREST schema cache 问题

**🐛 关键 Bug 修复**
- ✅ 修复会员状态查询字段名不一致(tier vs user_tier)导致的降级 bug
- ✅ 修复 manual_upgrade 调用不存在的 _refresh_user_info 方法
- ✅ 修复 users 表 is_active 字段不存在导致的 HTTP 500
- ✅ 修复配置界面频繁卡顿闪退问题

**🎨 UI 优化**
- ✅ 优化会员中心界面,支持会员等级逐级显示
- ✅ 价格已恢复正常: Pro月度 ¥29, Pro年度 ¥199, 终身会员 ¥599

**🔧 技术改进**
- ✅ 双重支付验证机制(webhook缓存 + Z-Pay API查询)
- ✅ RPC函数绕过PostgREST缓存问题
- ✅ 完整的错误日志和调试信息
- ✅ 支付成功自动激活,无需手动刷新

---

### v1.6.7 (2025-11-30) - 会员系统优化 👥

**🎨 UI/UX 增强**
- ✅ 优化会员中心界面,支持会员等级逐级显示
- ✅ 改进会员卡片布局和视觉效果
- ✅ 提升用户体验和交互流畅度

**🐛 Bug 修复**
- ✅ 修复配置界面频繁卡顿闪退问题
- ✅ 优化界面渲染性能
- ✅ 减少不必要的重绘操作

---

### v1.6.6 (2025-11-28) - 价格恢复 💰

**💰 定价调整**
- ✅ 恢复个人中心套餐正常价格
  - Pro月度: ¥29/月
  - Pro年度: ¥199/年
  - 终身会员: ¥599(限量1000名)
- ✅ 前后端价格同步更新
- ✅ 价格验证逻辑优化

---

### v1.6.5 (2025-11-26) - 品牌图标统一升级 🎨

**🎨 图标设计升级**
- ✅ **官网导航栏** - 更新为新版盾牌图标 (64x64)
- ✅ **官网关于模块** - Logo 尺寸优化至 180x180,视觉效果更佳
- ✅ **桌面应用图标** - 统一使用新版设计,保持品牌一致性
- ✅ **产品名称显示** - 配置界面"关于"标签页显示完整产品名称
  - 中文版: "GaiYa每日进度条"
  - 英文版: "GaiYa Daily Progress Bar"

**⚡ 性能优化**
- ✅ **API调用频率** - quota-status API 调用间隔从 5 秒优化到 5 分钟
- ✅ **预期收益** - 减少 98% 的 API 请求量 (从 162次/6小时 降至 ~3次/6小时)

**📁 图片文件优化**
- ✅ **GaiYa1120.png** - 文件大小从 1.2MB 优化到 536KB
- ✅ **logo-large.png** - 文件大小从 2.5MB 优化到 1.2MB
- ✅ **加载速度提升** - 官网图片加载更快,改善用户体验

---

### v1.6.4 (2025-11-20) - 官网上线 & Favicon 🌐

**🌐 官网正式上线**
- ✅ **域名**: [www.gaiyatime.com](https://www.gaiyatime.com)
- ✅ **技术栈**: 静态网站 + Vercel Serverless Functions
- ✅ **响应式设计**: 完美支持桌面和移动端
- ✅ **页面结构**:
  - 首页 - 产品介绍与核心功能展示
  - 下载页 - 最新版本下载与安装指南
  - 定价页 - 会员套餐详情与对比
  - 帮助中心 - FAQ与常见问题解答
  - 关于我们 - 团队故事与开源理念

**🎨 品牌视觉优化**
- ✅ **Favicon**: 添加GaiYa Logo图标，浏览器标签页显示品牌标识
- ✅ **统一设计**: Material Design风格，绿色主题（#4CAF50）
- ✅ **专业排版**: 清晰的视觉层级与信息架构

**☁️ 部署架构**
- ✅ **Vercel托管**: 静态网站 + API Serverless Functions
- ✅ **自定义域名**: www.gaiyatime.com
- ✅ **自动SSL证书**: HTTPS加密传输
- ✅ **全球CDN加速**: 快速访问体验

---

### v1.6.3 (2025-11-20) - Stripe国际支付集成 🌍💳

**💳 国际支付支持**
- ✅ **Stripe支付集成** - 支持Visa、Mastercard、American Express等国际信用卡
- ✅ **双支付通道** - 国内用户使用微信支付，海外用户使用Stripe
- ✅ **多币种显示** - 国内支付显示人民币（¥29/¥199/¥599），国际支付显示美元（$4.99/$39.99/$169.99）
- ✅ **支付方式选择** - 点击升级按钮时弹出支付方式对话框，用户可选择微信支付或Stripe

**🎯 支付流程优化**
- ✅ **智能分流** - 根据用户选择自动路由到对应支付网关
- ✅ **浏览器支付** - Stripe使用托管Checkout页面，无需PCI合规
- ✅ **Webhook自动处理** - 支付成功后自动创建订阅、升级用户等级、更新配额
- ✅ **完整错误处理** - 用户验证、API错误、异常捕获，详细日志记录

**🔧 技术实现**
- ✅ **后端API** - `/api/stripe-create-checkout` 创建Checkout Session
- ✅ **Webhook处理** - `/api/stripe-webhook` 接收支付完成事件
- ✅ **客户端集成** - `AuthClient.create_stripe_checkout_session()` 方法
- ✅ **UI组件** - 支付方式选择对话框，支持两种支付选项
- ✅ **数据统一** - payments和subscriptions表支持payment_provider字段区分支付来源

**📝 文档更新**
- ✅ Stripe集成方案文档（STRIPE_INTEGRATION_PLAN.md）
- ✅ 支付流程说明与测试指南
- ✅ 价格对照表（CNY vs USD）

**🌍 全球化支持**
- ✅ 为海外用户提供便捷的支付方式
- ✅ 支持全球主流信用卡品牌
- ✅ 自动货币转换与显示
- ✅ 符合国际支付标准与安全规范

---

### v1.6.2 (2025-11-19) - 场景编辑器整合优化 🎨

**🏗️ 架构优化**
- ✅ **场景编辑器完全整合** - 移除独立SceneEditor.exe，完全集成到主应用
- ✅ **开发流程优化** - 统一使用 `python main.py` 测试，`pyinstaller Gaiya.spec` 打包
- ✅ **文件清理** - 删除SceneEditor.spec和独立构建文件，简化项目结构

**🎯 场景编辑器增强**
- ✅ **道路层选择同步** - 点击画布中的道路图片，素材库自动高亮对应项目
- ✅ **双向选择联动** - 画布 ↔ 素材库实时同步，提升编辑体验
- ✅ **图层面板稳定性** - 修复点击图层时的崩溃问题

**🔧 技术改进**
- ✅ **模块化集成** - scene_editor作为Python模块直接导入，而非子进程调用
- ✅ **统一资源管理** - 场景编辑器与主窗口共享scenes/目录
- ✅ **代码简化** - 移除冗余的打包配置和启动脚本

**📐 文件变更**
- 🗑️ 删除: SceneEditor.spec（不再需要独立打包）
- 🗑️ 删除: dist/SceneEditor.exe（已整合到主程序）
- ✏️ 修改: scene_editor.py:3045-3064（道路层选择同步）
- ✏️ 修改: config_gui.py:2612-2642（场景编辑器窗口管理）

---

### v1.6.1 (2025-11-17) - 企业级安全升级 🔒

**🛡️ 安全审计与修复（11/12项完成，91.7%）**
- ✅ **SSL证书验证** - 修复全局禁用SSL验证问题，使用certifi CA证书包，防止MITM攻击
- ✅ **API速率限制** - 实现基于Supabase的速率限制系统，9个关键端点已集成
- ✅ **Token加密存储** - 使用keyring系统级密钥链（Windows DPAPI/macOS Keychain/Linux Secret Service）
- ✅ **输入验证增强** - RFC 5322邮箱验证、UUID/Decimal严格校验，35个测试用例
- ✅ **日志安全规范** - 统一日志工具，敏感信息自动脱敏（邮箱/Token/密码）
- ✅ **CORS白名单保护** - 所有21个API端点已配置，防止跨域攻击
- ✅ **支付安全增强** - 时间戳验证、签名校验，防止回调重放攻击
- ✅ **代码重复提取** - HTTP工具函数统一化，减少1000+行重复代码
- ✅ **配置管理统一** - 创建config.py模块，支持环境变量覆盖，消除硬编码

**📊 测试覆盖**
- 94个单元测试（100%通过率）
- 测试模块：http_utils(18)、config(25)、logger(10)、validators(35)、keyring(6)

**📚 文档完善**
- 安全修复进度报告（SECURITY_FIX_PROGRESS.md）
- HTTP工具迁移指南（HTTP_UTILS_MIGRATION_GUIDE.md）
- 速率限制集成指南（RATE_LIMIT_INTEGRATION_GUIDE.md）

**🔧 配置管理增强**
- 支持环境变量动态配置（CORS/价格/服务URL等）
- 开发环境自动添加localhost CORS
- 启动时自动验证必需配置（Supabase URL/Key）

**详细说明**: [查看安全修复进度报告](SECURITY_FIX_PROGRESS.md)

---

### v1.6.0 (2025-11-16) - 场景系统重磅上线

**🎨 场景系统(Scene System)**
- ✅ 可视化场景编辑器 - 拖拽式设计，所见即所得
- ✅ **一体化集成** - 场景编辑器已集成到主应用，无需独立exe文件
- ✅ **快速访问** - 配置界面 → 🎬场景设置 → 🎨打开场景编辑器
- ✅ 画布预览 - 实时查看场景效果
- ✅ 元素管理 - 支持添加、移动、缩放、删除场景元素
- ✅ 道路层配置 - 独立的道路层设置(平铺模式、偏移、缩放)
- ✅ 场景导入 - 从 scenes/ 目录导入已有场景进行编辑
- ✅ 场景导出 - 导出场景配置及资源文件到指定目录
- ✅ 场景刷新 - 主窗口支持刷新场景列表,立即显示新场景
- ✅ 场景进度条叠加 - 场景模式中可选择"依然展示进度条",实现场景与进度条的完美融合
- ✅ **自动场景加载** - 编辑器启动时自动加载默认"森林步道"场景
- ✅ **素材库预览** - 28个PNG素材自动加载到左侧素材库

**📁 导入/导出增强**
- ✅ 智能备份机制 - 重导出当前加载场景时自动备份资源文件
- ✅ 道路层备份 - 临时备份道路层图片,防止循环引用导致的数据丢失
- ✅ 场景元素备份 - 批量备份所有场景元素,确保数据完整性
- ✅ 自动清理 - 成功或失败后自动清理临时备份文件
- ✅ 目录一致性 - 编辑器与主窗口统一使用 scenes/ 目录

**🎯 UI/UX 增强**
- ✅ 进度条高度范围扩展 - 支持 2px-50px 超细模式，新增"极细(6px)"预设选项
- ✅ 更灵活的自定义控制 - 将自定义范围从 6-100px 调整为 2-50px，更符合实际使用场景

**🐛 Bug 修复**
- ✅ 场景Y位置调整 - 场景向下偏移21px,填满任务栏与场景之间的空白
- ✅ 重导出数据丢失 - 修复导出当前加载场景时所有场景元素(26+项)丢失的问题
- ✅ 刷新按钮崩溃 - 移除阻塞式消息框,改用异步刷新机制
- ✅ 道路层丢失 - 修复导出时道路层配置和图片丢失的问题
- ✅ 水印位置偏移 - 修复调整进度条高度后水印位置发生偏移的问题，改为固定在窗口底部

**🏗️ 架构优化**
- ✅ 新增 gaiya/scene 模块 - 场景系统独立模块化
  - SceneLoader - 场景配置加载器
  - SceneConfig/RoadLayer/SceneItem - 场景数据模型
  - ResourceCache - 图片资源缓存管理
- ✅ 场景编辑器(scene_editor.py) - 完整的可视化编辑工具
- ✅ 临时文件管理 - 使用 tempfile.NamedTemporaryFile 确保资源安全

**📝 文档更新**
- ✅ 场景系统路线图(SCENE_SYSTEM_ROADMAP.md)
- ✅ 场景编辑器更新报告(SCENE_EDITOR_UPDATE_*.md)
- ✅ Bug修复报告(BUG_FIX_REPORT_*.md)
- ✅ 测试计划与报告(SCENE_EDITOR_V2_TEST_*.md)

---

### v1.5.2 (2025-11-10) - 会员合伙人计划升级

**🎯 限量发售策略**
- ✅ 会员合伙人套餐限量1000名（¥599，终身使用）
- ✅ 深金色限量标签，强调稀缺性与高级定位
- ✅ 一次购买成为合伙人，共享项目长期价值

**💰 当前定价**
- ✅ 月度会员：¥29/月（20次/天AI配额）
- ✅ 年度会员：¥199/年（相当于16.6元/月，年省149元）
- ✅ 会员合伙人：¥599（限量1000名，终身权益）

**🤝 会员合伙人九大权益**
- ✅ 无限AI任务生成配额
- ✅ 去除进度条水印
- ✅ 完整数据统计报告
- ✅ 专属会员合伙人社群
- ✅ 33%引荐返现奖励
- ✅ 优先体验新功能
- ✅ 专属1v1咨询服务
- ✅ 共同成长分享价值
- ✅ 终身免费更新

**🎁 免费版增强**
- ✅ 每日3次AI任务规划配额
- ✅ 进度条水印："激活高级版,解锁更多服务"
- ✅ 完整核心功能体验
- ✅ 品牌曝光与口碑传播（参考StageTimer策略）

**📈 增长策略**
- ✅ 采用StageTimer启发的Freemium模式
- ✅ 免费版作为产品体验与品牌传播窗口
- ✅ 年付优惠鼓励长期订阅
- ✅ 聚焦真实用户需求（时间可视化 + AI辅助）

---

### v1.5.0 (2025-11-04) - 品牌升级与会员系统

**🌍 品牌升级**
- ✅ 产品名称：PyDayBar → GaiYa（盖亚）
- ✅ 品牌口号：守护你的每一分钟
- ✅ 全面文档品牌化

**🔐 认证与会员系统**
- ✅ 手机号登录/注册
- ✅ 三种会员套餐（月付/年付/会员合伙人）
- ✅ 会员功能解锁（AI配额、统计报告）

**💳 支付集成**
- ✅ 支持微信支付（ZPAY网关）
- ✅ 支持Stripe国际支付（v1.6.3新增）
- ✅ 双支付通道（国内/国际）
- ✅ 订单状态轮询与通知

**🎨 UI优化**
- ✅ 会员卡片样式升级
- ✅ Material Design主题集成
- ✅ 外观配置UI布局优化

**详细说明**: [查看完整更新日志](CHANGELOG.md)

---

## ❓ 常见问题

<details>
<summary><strong>Q1: 进度条不显示？</strong></summary>

**检查清单**：
1. ✅ 确认程序正在运行（系统托盘有图标）
2. ✅ 尝试切换位置（顶部 ↔ 底部）
3. ✅ 检查透明度设置（不要设置为0）
4. ✅ 查看日志文件 `gaiya.log`

**常见原因**:
- 任务未配置（所有时间段颜色相同）
- 进度条高度设置过小（<5px）
- 被其他窗口覆盖

**解决方法**:
```
配置界面 → 任务管理 → 选择预设模板
或使用AI生成任务表
```
</details>

<details>
<summary><strong>Q2: 修改配置没有生效？</strong></summary>

**情况1: 修改JSON文件**
- ✅ 配置文件会自动重载
- ✅ 无需重启程序

**情况2: 修改源代码**
- ⚠️ 必须重新打包 exe 才能生效
- 步骤: `rm -rf build dist → pyinstaller Gaiya.spec`
- 详见: [PyInstaller开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md)
</details>

<details>
<summary><strong>Q3: AI功能显示"无法连接"？</strong></summary>

**可能原因**:
1. 🌐 网络问题
2. 📊 配额已用完（免费版: 3次/天）
3. ☁️ Vercel服务暂时不可用
4. 🔐 未登录账号

**解决方法**:
- 检查配额状态: 配置界面 → AI生成区域 → 查看剩余次数
- 免费版每日0:00重置配额
- 升级会员获得无限AI配额
- 检查网络连接
</details>

<details>
<summary><strong>Q4: 如何设置开机自启动？</strong></summary>

**方法一（推荐）**:
```
配置界面 → 外观设置 → 勾选"开机自启动"
```

**方法二（手动）**:
- **Windows**:
  1. `Win+R` 输入 `shell:startup`
  2. 复制 `GaiYa-v1.6.3.exe` 的快捷方式到启动文件夹

**验证**: 重启电脑，检查系统托盘是否自动出现图标
</details>

<details>
<summary><strong>Q5: 如何卸载/完全删除？</strong></summary>

**步骤**:
1. 关闭程序（右键托盘图标 → 退出）
2. 删除 exe 文件
3. 删除配置文件（可选）:
   - Windows: `%LOCALAPPDATA%\GaiYa\`
   - 或查看当前目录的 `config.json`、`tasks.json`

**注意**:
- 卸载前可备份配置文件以便将来恢复
- 会员数据存储在云端，可随时重新登录恢复
</details>

<details>
<summary><strong>Q6: 支持Mac/Linux吗？</strong></summary>

**当前状态**:
- ✅ Windows 10/11 (完全支持)
- ⚠️ Linux (理论支持，未充分测试)
- ⚠️ macOS (理论支持，未充分测试)

**Linux/macOS使用方法**:
```bash
git clone https://github.com/jiamizhongshifu/jindutiao.git
cd jindutiao
pip install -r requirements.txt
python main.py
```

**已知问题**:
- 系统托盘图标可能显示异常
- 开机自启动需手动配置
- 部分UI样式可能需要调整

**后续计划**: v1.6+ 将优化跨平台支持
</details>

<details>
<summary><strong>Q7: 可以自定义任务颜色吗？</strong></summary>

**方法1: 使用预设主题**
```
配置界面 → 任务管理 → 主题 → 选择预设（6种）
```

**方法2: 完全自定义**
```
配置界面 → 任务管理 → 任务列表 → 点击颜色方块 → 选择器
```

**方法3: AI推荐**
```
配置界面 → AI生成 → 描述风格偏好 → AI自动配色
```

**方法4: 编辑JSON**
```json
// tasks.json
{
  "tasks": [
    {"name": "工作", "start": "09:00", "end": "12:00", "color": "#FF5733"}
  ]
}
```
</details>

<details>
<summary><strong>Q8: 支持哪些支付方式？</strong></summary>

**国内用户**:
- ✅ **微信支付** - 使用ZPAY支付网关
💰 价格: 月付¥29、年付¥199、会员合伙人¥599

**海外用户**:
- ✅ **Stripe国际支付** - 支持Visa、Mastercard、American Express等
- 💰 **价格**: 月付$4.99、年付$39.99、会员合伙人$169.99

**支付流程**:
1. 点击"升级会员"或"成为合伙人"按钮
2. 选择支付方式（微信支付 / 国际支付）
3. 浏览器自动打开支付页面
4. 完成支付后自动激活会员权益

**安全保障**:
- 🔒 Stripe通过PCI DSS Level 1认证（最高级别）
- 🔒 不存储任何信用卡信息
- 🔒 使用Stripe托管Checkout页面
- 🔒 Webhook签名验证防止伪造支付
</details>

更多问题请查看 [Issues](https://github.com/jiamizhongshifu/jindutiao/issues) 或加入微信群讨论。

---

## 🗺️ 开发路线图

### ✅ 已完成（v1.0 - v1.5）

- [x] 桌面进度条核心功能
- [x] 任务可视化管理
- [x] 主题系统
- [x] AI任务生成
- [x] 会员系统
- [x] 支付集成（微信支付 + Stripe国际支付）
- [x] 数据统计（会员功能）
- [x] 场景系统（可视化编辑器）

### 🚧 进行中（v1.6）

- [ ] 跨平台支持优化
- [ ] 多语言支持（英文）
- [ ] 性能优化
- [ ] UI/UX改进

### 📋 计划中（v2.0）

- [ ] 移动端同步
- [ ] 团队协作功能
- [ ] 数据导出/导入
- [ ] 插件系统
- [ ] Notion/Todoist集成

详见: [完整路线图](ROADMAP_v1.5.md)

---

## 🤝 参与贡献

我们欢迎任何形式的贡献！无论是报告bug、提出功能建议，还是提交代码，我们都非常感激。

### 贡献方式

- 🐛 **报告 Bug**: [提交 Issue](https://github.com/jiamizhongshifu/jindutiao/issues)
- 💡 **功能建议**: [讨论区](https://github.com/jiamizhongshifu/jindutiao/discussions)
- 🔧 **代码贡献**: 提交 Pull Request（请先阅读 [贡献指南](CONTRIBUTING.md)）
- 📖 **文档改进**: 欢迎优化文档表述、修正错误
- 🌍 **翻译**: 帮助翻译文档或UI文本

### 开发环境设置

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/YOUR_USERNAME/jindutiao.git
cd jindutiao

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建功能分支
git checkout -b feature/your-feature-name

# 4. 进行开发并测试
python main.py

# 5. 提交更改
git commit -m "feat: 添加xxx功能"
git push origin feature/your-feature-name

# 6. 创建 Pull Request
```

### 代码规范

- ✅ 遵循 PEP 8 Python代码风格
- ✅ 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)
- ✅ 添加必要的注释和文档字符串
- ✅ 确保代码通过测试
- ✅ 更新相关文档

详细说明请阅读: [贡献指南](CONTRIBUTING.md)

---

## 👥 贡献者

感谢所有为 GaiYa 做出贡献的开发者！

<!-- 自动生成贡献者列表 -->
<a href="https://github.com/jiamizhongshifu/jindutiao/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=jiamizhongshifu/jindutiao" />
</a>

*你的贡献将让 GaiYa 变得更好！*

---

## 💬 社区与支持

### 获取帮助

- 🌐 **官网**: [www.gaiyatime.com](https://www.gaiyatime.com)
- 📖 **文档**: [在线文档](https://github.com/jiamizhongshifu/jindutiao#-文档导航)
- 💬 **讨论区**: [GitHub Discussions](https://github.com/jiamizhongshifu/jindutiao/discussions)
- 🐛 **Bug反馈**: [GitHub Issues](https://github.com/jiamizhongshifu/jindutiao/issues)
- 👥 **微信群**: 见配置界面"关于"页面二维码

### 联系我们

- **官网**: [www.gaiyatime.com](https://www.gaiyatime.com)
- **邮箱**: support@gaiya.app
- **GitHub**: https://github.com/jiamizhongshifu/jindutiao

---

## 📜 行为准则

本项目遵循 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。

**核心原则**:
- 🤝 尊重所有贡献者
- 💬 提供建设性反馈
- 🎯 专注于问题本身，而非个人
- 👋 欢迎新手，耐心解答问题
- 🌈 包容不同观点和经验

详见: [CONTRIBUTING.md - 行为准则](CONTRIBUTING.md#-行为准则)

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议

```
MIT License

Copyright (c) 2025 GaiYa 团队

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

**这意味着**:
- ✅ 可以自由使用、复制、修改、合并、发布、分发、再许可
- ✅ 可以用于商业目的
- ✅ 必须保留原始许可证和版权声明
- ⚠️ 软件按"原样"提供，不提供任何明示或暗示的保证

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=jiamizhongshifu/jindutiao&type=Date)](https://star-history.com/#jiamizhongshifu/jindutiao&Date)

---

## 🙏 致谢

### 开源项目

感谢以下开源项目：

- [PySide6](https://pypi.org/project/PySide6/) - Qt for Python
- [PyInstaller](https://www.pyinstaller.org/) - Python应用打包
- [Requests](https://requests.readthedocs.io/) - HTTP库

### 服务提供商

- [Vercel](https://vercel.com/) - Serverless部署平台
- [Supabase](https://supabase.com/) - 开源后端服务
- [Anthropic](https://www.anthropic.com/) - Claude AI API
- [Stripe](https://stripe.com/) - 国际支付网关

### 灵感来源

- [StageTimer](https://stagetimer.io/) - Freemium模式启发
- [RescueTime](https://www.rescuetime.com/) - 时间追踪理念

---

## 💖 支持我们

如果 GaiYa 对您有帮助，请考虑通过以下方式支持我们：

### 免费支持

- ⭐ **Star 本项目**: 点击右上角的 Star 按钮
- 🔀 **Fork 并贡献**: 提交代码改进或新功能
- 📢 **分享推荐**: 告诉更多需要的朋友
- 🐛 **反馈 Bug**: 帮助我们发现和修复问题
- 📖 **完善文档**: 改进文档表述或添加示例

### 成为会员合伙人

- 💎 **限量1000名 ¥599**: 一次购买，终身使用
- ✨ **九大专属权益**: 无限AI配额、专属社群、33%返现等
- 🤝 **共享价值**: 与我们一起成长，见证项目发展
- 🌟 **官网查看详情**: [www.gaiyatime.com/pricing](https://www.gaiyatime.com/pricing.html)

---

<div align="center">

Made with ❤️ by GaiYa 团队

⭐ **如果这个项目对你有帮助，请给我们一个 Star！** ⭐

[官网](https://www.gaiyatime.com) · [下载](https://www.gaiyatime.com/download.html) · [定价](https://www.gaiyatime.com/pricing.html) · [文档](#-文档导航) · [反馈](https://github.com/jiamizhongshifu/jindutiao/issues) · [贡献](CONTRIBUTING.md)

</div>
# Force redeploy
