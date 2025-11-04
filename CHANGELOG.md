# 更新日志 / Changelog

所有值得注意的项目更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
