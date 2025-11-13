# Gaiya (盖亚) 更新日志

**守护你的每一分钟** ⏱️

所有值得注意的项目更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [v1.6.0] - 2025-11-13

### ✨ 新功能 / New Features

- **自动更新系统**
  - 实现应用内自动检查更新功能
  - 支持一键下载并安装最新版本
  - 优化用户升级体验，无需手动下载

### 🐛 Bug修复 / Bug Fixes

- **WebEngine可选导入**
  - 将WebEngine改为可选导入，解决个人中心标签页加载失败问题
  - 提升应用稳定性和兼容性

- **进度条视觉优化**
  - 修复主题切换时进度条出现白色/黑色描边的问题
  - 移除垂直边距，优化QPainter绘制逻辑
  - 修复浮点数舍入导致的任务块间隙问题
  - 所有主题下进度条显示更加一致和流畅

- **模块引用清理**
  - 移除不存在的theme_ai_helper模块引用
  - 代码结构更加清晰

### ⚡ 性能优化 / Performance

- **异步网络请求**
  - 实施异步网络请求架构，解决UI阻塞问题
  - 配置界面健康检查改为异步执行
  - 提升应用响应速度和用户体验

### 🎨 UI/UX优化 / UI/UX Improvements

- **统一提示样式**
  - 统一全局QToolTip样式，提升视觉一致性
  - 悬停提示采用半透明黑色背景+白色文字
  - 圆角边框，优雅的视觉效果

- **时间轴提示优化**
  - 时间轴提示文字颜色从金色(#FFD700)调整为灰色(#666666)
  - 降低视觉干扰，更符合UI设计规范

- **控制台窗口隐藏**
  - 禁用控制台窗口，提升用户体验
  - 专业化应用外观

### 📚 文档完善 / Documentation

- **调试方法论增强**
  - 新增6大系统性调试方法论：
    - 渐进式差异分析法（Progressive Differential Analysis）
    - Vercel部署问题诊断法
    - PyInstaller打包应用开发方法论
    - UI状态同步问题诊断法
    - 性能感知与真实性能分析法
    - UI样式修改无效问题诊断法
  - 完善实战案例和最佳实践

- **构建文档**
  - 添加构建脚本文档
  - 更新README构建章节
  - 优化打包流程说明

- **Vercel部署文档**
  - 完善Vercel相关故障排查文档
  - 添加404问题、空日志、构建警告等解决方案

### 🔧 技术改进 / Technical Improvements

- **代码质量**
  - 优化QPainter绘制逻辑，避免描边问题
  - 改进浮点数坐标计算，消除视觉间隙
  - 统一API路径前缀（/api/），提升路由一致性

- **项目维护**
  - 添加运行时生成文件到.gitignore
  - 更新统计数据（statistics.json）

---

## [v1.5.2] - 2025-11-10

### 🎯 限量发售策略 / Limited Release Strategy

- **会员合伙人计划升级**
  - 价格调整：¥399 → ¥1200
  - 限量发售：1000名会员合伙人
  - 深金色限量标签（#B8860B DarkGoldenrod）
  - 强调稀缺性与高级定位

### 💰 定价策略调整 / Pricing Updates

- **当前定价体系**
  - 月度会员：¥29/月（20次/天AI配额）
  - 年度会员：¥199/年（相当于16.6元/月，年省149元）
  - 会员合伙人：¥1200（限量1000名，终身权益）

### 🎨 UI 增强 / UI Enhancements

- **限量标签实现**
  - 会员合伙人卡片添加"限量1000名"标签
  - 深金色背景突出稀缺性
  - 标题与标签居中对齐布局优化

### 🌐 开源准备 / Open Source Preparation

- **完善开源文档**
  - 创建 CODE_OF_CONDUCT.md（贡献者公约行为准则）
  - 添加 GitHub Issue 模板（Bug报告、功能请求）
  - 添加 Pull Request 模板
  - 创建 FUNDING.yml 赞助配置
  - 增强 README.md（更多徽章、开源优势说明）
  - 优化 .gitignore（确保 Gaiya.spec 被包含）

### 📚 文档更新 / Documentation

- **README.md 优化**
  - 版本号更新：v1.5.1 → v1.5.2
  - 添加"为什么选择 GaiYa"部分（开源透明、技术优势、用户友好）
  - 添加"支持我们"部分（免费支持 + 成为会员合伙人）
  - 增强徽章显示（Stars、Forks、Issues、PRs Welcome）
  - 更新会员系统价格说明

### 🔧 技术改进 / Technical Improvements

- **代码同步**
  - 前端：config_gui.py 价格更新
  - 后端：api/zpay_manager.py 价格同步
  - 后端：api/subscription_manager.py 价格同步
  - 后端：api/validators.py 价格验证同步

---

## [v1.5.0] - 2025-11-04

### 🌍 品牌升级 / Branding

- **品牌正式升级**
  - 产品英文名：PyDayBar → Gaiya
  - 产品中文名：盖亚
  - 品牌口号：守护你的每一分钟
  - 文件命名：PyDayBar-v1.4.exe → Gaiya-v1.5.exe
  - Spec文件：PyDayBar.spec → Gaiya.spec

### 📝 文档更新 / Documentation

- **全面文档品牌化**
  - README.md - 添加品牌故事和Slogan
  - CHANGELOG.md - 更新日志头部品牌化
  - SECURITY.md - 安全文档品牌更新
  - RELEASE_NOTES_v1.4.md - 发布说明品牌更新
  - GITHUB_RELEASE_DESCRIPTION.md - Release描述品牌化
  - 反病毒误报解决方案.md - 白名单申请模板更新

### 🎨 品牌故事 / Brand Story

**表层含义（专业版）**：
- Gaiya源自希腊神话大地女神Gaia
- 象征承载时间的大地
- 守护用户的每一分钟

**深层含义（梗文化）**：
- 灵感来自游戏主播卢本伟的"哎呀"惨叫
- 联想《盖亚·奥特曼》的变身呐喊
- 从"哎呀"到时间管理高手的变身

### 🔄 兼容性 / Compatibility

- ✅ 完全兼容v1.4配置和数据
- ✅ 所有功能保持不变
- ✅ 仅品牌和文件命名更新

---

## [v1.4.0] - 2025-11-04

### ✨ 新增 / Added

- **智能模板保存对话框**
  - 根据是否有历史模板自动调整UI界面
  - 无历史模板：显示普通输入框
  - 有历史模板：显示可编辑下拉框，列出所有历史模板及任务数
  - 支持一键覆盖历史模板，无需二次确认
  - 支持在下拉框中直接输入新名称创建新模板
  - 文件：`config_gui.py:49-160` (SaveTemplateDialog类)

- **保存成功提示优化**
  - 区分"模板已创建"和"模板已更新"两种情况
  - 显示任务数量信息
  - 文件：`config_gui.py:2641-2650`

### 🔒 安全性 / Security

- **禁用UPX压缩**
  - 减少杀毒软件误报率50-70%
  - 文件大小无明显增加（54.9 MB）
  - 性能不受影响
  - 文件：`PyDayBar.spec:69`

- **添加Windows版本信息资源**
  - 创建 `version_info.txt` 文件
  - 包含公司名、产品名、版本号、版权信息等
  - 增加软件正规性（待后续版本启用）

- **准备白名单提交材料**
  - 创建完整的误报解决方案文档
  - 向Windows Defender、360、火绒提交申请
  - 文件：`反病毒误报解决方案.md`

### 🐛 修复 / Fixed

- **模板保存确认机制**
  - 修复：同名模板覆盖前无明确提示
  - 改进：选择历史模板自动覆盖，新名称自动创建

- **模板保存提示信息**
  - 修复：所有保存都显示"已添加到列表"
  - 改进：新建显示"已创建"，覆盖显示"已更新"

### 🎨 改进 / Changed

- **SaveTemplateDialog类设计**
  - 使用QDialog替代QInputDialog
  - 动态适配UI组件（QComboBox vs QLineEdit）
  - 添加友好的使用提示

- **save_as_template方法重构**
  - 简化代码逻辑
  - 移除冗余的覆盖确认对话框
  - 优化用户体验流程

### 📝 文档 / Documentation

- 新增 `反病毒误报解决方案.md`
  - 完整的误报问题分析
  - 白名单提交指南（含英文和中文模板）
  - 用户安装指南（3种方法）
  - 一周实施计划

- 新增 `RELEASE_NOTES_v1.4.md`
  - 详细的版本说明
  - 文件哈希值
  - 升级指南

- 新增 `CHANGELOG.md`
  - 标准化的更新日志格式

---

## [v1.3.0] - 2025-11-02

### ✨ 新增

- **WebP动画性能优化**
  - 实现帧预缓存机制
  - 手动缩放所有帧确保尺寸一致
  - 帧间隔精度从±21ms提升到±1.2ms
  - 运行时帧切换耗时降低到<1ms
  - 文件：`main.py:1461-1477, 2009-2019, 2354-2357`

- **高精度定时器**
  - 使用Qt.TimerType.PreciseTimer
  - 提升动画流畅度

### 🐛 修复

- **WebP动画播放问题**
  - 修复：动画"中途停一下"的卡顿问题
  - 根因：QMovie.setScaledSize不影响已缓存的第0帧
  - 方案：手动缩放所有帧而非依赖框架

- **finished信号异常触发**
  - 修复：帧延迟为0时jumpToFrame触发finished信号
  - 方案：WebP格式不连接finished信号，完全手动控制

### 📝 文档

- 新增 `性能优化方法论.md`
  - 完整记录7次迭代优化过程
  - 渐进式深挖调试方法
  - 性能对比数据

---

## [v1.2.0] - 2025-11-01

### ✨ 新增

- **主题保存后自动刷新**
  - 修复：保存主题后进度条颜色未立即更新
  - 改进：reload_all()中添加主题重新应用逻辑
  - 文件：`main.py:1826-1831`

- **任务配色重置修复**
  - 修复：AI生成任务后配色被重置的问题
  - 改进：添加auto_apply_task_colors检查
  - 文件：`main.py:2243-2258`

### 🐛 修复

- **主题配色同步**
  - 问题：预览正常但保存后配色消失
  - 根因：保存时从表格读取旧颜色，未应用主题颜色
  - 方案：保存时应用主题颜色到任务数据
  - 文件：`config_gui.py:2188-2219, 2245`

### 📝 文档

- 新增 `UI状态同步问题诊断法.md`
  - 完整的UI同步问题诊断流程
  - 数据流分析方法
  - 最佳实践和反模式

---

## [v1.1.0] - 2025-10-30

### ✨ 新增

- **Vercel云服务集成**
  - 迁移AI功能到Vercel Serverless Functions
  - 实现配额查询API（/api/quota-status）
  - 实现任务生成API（/api/plan-tasks）
  - 文件：`vercel_api/health.py, quota-status.py, plan-tasks.py`

### 🐛 修复

- **AI服务连接问题**
  - 问题：健康检查路径不匹配导致404
  - 根因：客户端使用/health，Vercel路由要求/api/*
  - 方案：统一所有API使用/api/前缀
  - 文件：`ai_client.py:212`, `config_gui.py:303, 2916-2937`

### 📝 文档

- 新增 `渐进式差异分析法.md`
  - 系统性诊断"部分功能正常、部分失败"问题
  - Vercel部署问题诊断流程
  - 7次迭代修复记录

---

## [v1.0.0] - 2025-10-25

### ✨ 新增

- **核心功能**
  - 桌面进度条显示
  - 时间线可视化编辑器
  - 自定义任务管理
  - 主题配色系统
  - AI智能任务规划

- **模板系统**
  - 12个预设任务模板
  - 自定义模板保存
  - 模板导入导出

- **开机自启动**
  - Windows注册表集成
  - 自启动管理器

### 🎨 界面

- 现代化Material Design风格
- 托盘图标集成
- 双击隐藏/显示
- 右键菜单

### 📝 文档

- README.md
- 使用说明
- 任务模板说明

---

## 图例 / Legend

- ✨ 新增 / Added - 新功能
- 🔒 安全性 / Security - 安全相关更新
- 🐛 修复 / Fixed - Bug修复
- 🎨 改进 / Changed - 现有功能的更改
- ⚠️ 废弃 / Deprecated - 即将移除的功能
- 🗑️ 移除 / Removed - 已移除的功能
- 📝 文档 / Documentation - 文档更新
- 🚀 性能 / Performance - 性能优化

---

## 链接 / Links

- [未发布的更改](https://github.com/[你的用户名]/PyDayBar/compare/v1.4.0...HEAD)
- [v1.4.0](https://github.com/[你的用户名]/PyDayBar/compare/v1.3.0...v1.4.0)
- [v1.3.0](https://github.com/[你的用户名]/PyDayBar/compare/v1.2.0...v1.3.0)
- [v1.2.0](https://github.com/[你的用户名]/PyDayBar/compare/v1.1.0...v1.2.0)
- [v1.1.0](https://github.com/[你的用户名]/PyDayBar/compare/v1.0.0...v1.1.0)
- [v1.0.0](https://github.com/[你的用户名]/PyDayBar/releases/tag/v1.0.0)
