# GaiYa每日进度条 🌍

<div align="center">

**守护你的每一分钟** ⏱️

用进度条让时间流逝清晰可见的桌面工具

[![最新版本](https://img.shields.io/github/v/release/jiamizhongshifu/jindutiao?label=%E6%9C%80%E6%96%B0%E7%89%88%E6%9C%AC)](https://github.com/jiamizhongshifu/jindutiao/releases/latest)
[![下载量](https://img.shields.io/github/downloads/jiamizhongshifu/jindutiao/total?label=%E4%B8%8B%E8%BD%BD%E9%87%8F)](https://github.com/jiamizhongshifu/jindutiao/releases)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**📥 [下载 Windows 版本](https://github.com/jiamizhongshifu/jindutiao/releases/latest)**

当前版本: **v1.5.0** | 最后更新: 2025-11-04

</div>

---

## ✨ 核心特性

| 功能分类 | 特性说明 |
|---------|---------|
| **🎯 桌面进度条** | 透明置顶、实时更新、悬停提示、点击穿透 |
| **📊 任务管理** | 可视化色块、12种预设模板、自定义颜色、智能时间表 |
| **🎨 主题系统** | 6种预设主题、AI主题生成、实时预览 |
| **🤖 AI功能** | 自然语言生成任务、智能配色推荐（云服务） |
| **🍅 番茄钟** | 集成番茄钟、智能通知、免打扰模式 |
| **📈 数据统计** | 任务完成跟踪、多维度分析、数据导出 |
| **⚙️ 配置管理** | 图形化界面、时间轴编辑、开机自启动 |

---

## 🚀 快速开始

### 方式一：下载可执行文件（推荐）

1. **下载最新版本**: [Gaiya-v1.5.exe](https://github.com/jiamizhongshifu/jindutiao/releases/latest)
2. **运行程序**: 双击 exe 文件
3. **打开配置**: 右键系统托盘图标 → "⚙️ 配置"

### 方式二：从源码运行

```bash
# 1. 克隆项目
git clone https://github.com/jiamizhongshifu/jindutiao.git
cd jindutiao

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

---

## 🔒 关于安全

**GaiYa 是完全开源的软件，所有代码公开可审计。**

部分杀毒软件可能因 PyInstaller 打包方式误报，这是 Python 应用的常见问题。

**解决方案**：
- ✅ **已优化**: v1.4.0+ 禁用 UPX 压缩，大幅减少误报
- 🛡️ **添加信任**: [查看详细步骤](SECURITY.md)
- 🔨 **从源码构建**: 自己构建最安全

---

## ⚙️ 核心配置

通过系统托盘菜单 "⚙️ 配置" 打开配置界面：

### 1. 外观设置
- 进度条高度、位置（顶部/底部）、透明度
- 背景颜色、圆角、阴影效果
- 多显示器支持
- 时间标记样式（线条/图片/GIF）

### 2. 任务管理
- **预设主题**: 6种内置配色（商务、活力、自然等）
- **任务编辑**: 可视化时间轴，拖拽调整
- **模板库**: 12种作息模板（工作日、学生、自由职业等）
- **时间表**: 自动应用规则（按日期/星期/月份）

### 3. AI 功能
- **智能生成**: 自然语言描述 → 完整任务表
- **配额管理**: 免费用户每日 20 次
- **云服务**: 基于 Vercel，无需本地配置

### 4. 其他
- 番茄钟设置、通知规则、免打扰时段
- 任务统计与报告
- 开机自启动

**详细配置说明**: 编辑 `config.json` 和 `tasks.json` 后自动生效

---

## 🤖 AI 智能功能

### 使用方法

1. 打开配置界面 → **任务管理**
2. 在 AI 生成区域输入描述：
   ```
   我是程序员，朝九晚六工作，中午休息1小时
   ```
3. 点击 **"生成"** → 自动生成完整任务表
4. 点击 **"保存"** 应用

### 云服务特点

| 特点 | 说明 |
|------|------|
| ✅ **自动运行** | 基于 Vercel，无需本地启动 |
| ✅ **配额管理** | 免费用户：20 次/天 |
| ✅ **数据持久化** | 配额实时同步（Supabase） |
| ✅ **无需配置** | 开箱即用 |

---

## 📦 打包发布

```bash
# 清理旧文件
rm -rf build dist

# 打包（使用 Gaiya.spec）
pyinstaller Gaiya.spec

# 生成文件
dist/Gaiya-v1.5.exe  # 约 57 MB
```

**重要**: 修改源代码后必须重新打包才能在 exe 中生效。详见 [PyInstaller 开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md)

---

## 📚 文档导航

### 🛠️ 开发文档
- [PyInstaller 开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md) - 打包应用开发调试最佳实践
- [UI 样式修改问题诊断](docs/UI_STYLE_MODIFICATION_TROUBLESHOOTING.md) - 修改代码但 UI 未生效的排查方法
- [AI 助手配置](CLAUDE.md) - AI 协作开发指南与方法论

### ☁️ 云服务
- [Vercel 部署指南](api/README.md) - Serverless Functions 部署说明
- [配额系统说明](QUOTA_SYSTEM_README.md) - 配额管理使用指南
- [部署问题排查](VERCEL_404_TROUBLESHOOTING.md) - 常见问题解决

### 📋 其他
- [更新日志](CHANGELOG.md) - 完整版本历史
- [安全说明](SECURITY.md) - 隐私保护与杀毒软件误报
- [开发路线图](ROADMAP_v1.5.md) - 功能规划

---

## 🔄 最新更新

### v1.5.0 (2025-11-04) - 品牌升级与会员系统

**🌍 品牌升级**
- ✅ 产品名称：PyDayBar → GaiYa（盖亚）
- ✅ 品牌口号：守护你的每一分钟
- ✅ 全面文档品牌化

**🔐 认证与会员系统**
- ✅ 手机号登录/注册
- ✅ 三种会员套餐（月付/年付/终身）
- ✅ 会员功能解锁（AI 配额、高级统计）

**💳 支付集成**
- ✅ 支持微信支付
- ✅ ZPAY 支付网关集成
- ✅ 订单状态轮询与通知

**🎨 UI 优化**
- ✅ 会员卡片样式升级
- ✅ Material Design 主题集成

**详细说明**: [查看完整更新日志](CHANGELOG.md)

---

## ❓ 常见问题

<details>
<summary><strong>Q: 进度条不显示？</strong></summary>

检查清单：
1. 确认程序正在运行（系统托盘有图标）
2. 切换位置（顶部/底部）
3. 查看日志文件 `gaiya.log`
</details>

<details>
<summary><strong>Q: 修改配置没有生效？</strong></summary>

- 编辑 `config.json` 或 `tasks.json` 后会自动重载
- 如果修改源代码，需要重新打包 exe
</details>

<details>
<summary><strong>Q: AI 功能显示"无法连接"？</strong></summary>

可能原因：
- 网络问题
- 配额已用完（每日 20 次）
- Vercel 服务暂时不可用

解决：查看配额状态，等待重置（每日 0:00）
</details>

<details>
<summary><strong>Q: 如何设置开机自启动？</strong></summary>

**方法一（推荐）**: 配置界面 → 外观设置 → 勾选"开机自启动"

**方法二（手动）**:
- Windows: `Win+R` → `shell:startup` → 复制快捷方式
- Linux: 创建 `~/.config/autostart/gaiya.desktop`
- macOS: 系统偏好设置 → 用户与群组 → 登录项
</details>

---

## 🤝 参与贡献

我们欢迎任何形式的贡献！

- 🐛 **报告 Bug**: [提交 Issue](https://github.com/jiamizhongshifu/jindutiao/issues)
- 💡 **功能建议**: [讨论区](https://github.com/jiamizhongshifu/jindutiao/discussions)
- 🔧 **代码贡献**: 提交 Pull Request 前请先创建 Issue 讨论
- 📖 **文档改进**: 欢迎优化文档表述

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议

---

<div align="center">

Made with ❤️ by GaiYa 团队

⭐ **如果这个项目对你有帮助，请给我们一个 Star！** ⭐

[官网](https://gaiya.app) · [文档](https://docs.gaiya.app) · [反馈](https://github.com/jiamizhongshifu/jindutiao/issues)

</div>
