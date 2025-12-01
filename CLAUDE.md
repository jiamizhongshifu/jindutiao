# CLAUDE AI ASSISTANT CONFIG

> ⚠️ **核心行为逻辑依赖外部脚本**: `$HOME/.claude/feedback_common.md`
> 📖 **产品信息与功能文档**: 参考 [README.md](README.md)

---

## 📌 项目概览

**Purpose**: GaiYa每日进度条 - 用进度条让时间流逝清晰可见的桌面工具

**Stack**:

- 桌面端: Python 3.11+, PySide6, PyInstaller
- 后端: Vercel Serverless Functions, Supabase
- AI: Claude 3.5 Sonnet (任务生成)

**Architecture**:

```text
gaiya/
├── main.py              # 主窗口 & 进度条核心
├── config_gui.py        # 配置界面 & 任务管理
├── ai_client.py         # AI 云服务客户端
├── gaiya/               # 核心模块(ui/core/utils/scene)
├── api/                 # Vercel Serverless Functions
├── templates/           # 任务模板
└── tests/               # 测试用例(94个, 100%通过率)
```

---

## ⚙️ 核心命令

**开发验证** (源代码修改后验证):

```bash
# 开发模式 - 修改立即生效
python main.py

# Type Check (严格修改TS文件后运行,本项目为Python无此步骤)
# Test (修改逻辑后运行相关测试)
pytest tests/

# Lint (提交前自动修复样式问题)
# 本项目暂无配置,遵循PEP 8规范
```

**打包发布** (必须重新打包才能在exe中生效):

```bash
# ⚠️ PyInstaller打包核心规则:
# 修改代码 → 清理build/dist → 重新打包 → 测试exe

# 快速增量构建 (日常开发,速度提升50-87%)
build-fast.bat

# 完全重建 (修改spec/添加依赖/缓存异常时)
build-clean.bat

# 手动打包
rm -rf build dist && pyinstaller Gaiya.spec
```

**Vercel部署** (推送自动触发):

```bash
git push origin main
# 查看部署状态: https://vercel.com/jindutiao
```

---

## 📚 文档索引 (渐进式披露)

**仅在相关任务时阅读对应文档**:

### 开发调试

- **打包问题**: 读 [PYINSTALLER_DEVELOPMENT_METHODOLOGY.md](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md)
  (增量打包失败、exe未更新、Qt样式问题)

- **UI样式问题**: 读 [docs/UI_STYLE_MODIFICATION_TROUBLESHOOTING.md](docs/UI_STYLE_MODIFICATION_TROUBLESHOOTING.md)
  (修改代码但UI未生效)

- **快速参考**: 读 [QUICKREF.md](QUICKREF.md)
  (核心文件职责、关键类位置、常用命令)

### 安全与质量

- **安全审计**: 读 [SECURITY_FIX_PROGRESS.md](SECURITY_FIX_PROGRESS.md)
  (11/12项安全修复记录、测试覆盖)

- **HTTP工具**: 读 [api/HTTP_UTILS_MIGRATION_GUIDE.md](api/HTTP_UTILS_MIGRATION_GUIDE.md)
  (代码重构最佳实践)

### 云服务

- **Vercel部署**: 读 [api/README.md](api/README.md)
  (Serverless Functions部署说明)

- **配额系统**: 读 [QUOTA_SYSTEM_README.md](QUOTA_SYSTEM_README.md)
  (AI配额管理使用指南)

### 功能实现说明

- **行为识别**: 读 [行为识别问题修复说明.md](行为识别问题修复说明.md)
  (应用分类配置、数据采集、统计展示)

- **自我追踪过滤**: 读 [GaiYa自我追踪过滤功能说明.md](GaiYa自我追踪过滤功能说明.md)
  (忽略GaiYa自身进程、双重过滤机制)

- **专注统计**: 读 [红温专注统计简化说明.md](红温专注统计简化说明.md)
  (时间回放界面优化、专注数据展示)

### 工作流与方法论

- **调试方法论**: 读 [.claude/debugging_methods.md](.claude/debugging_methods.md)
  (PyInstaller打包故障诊断、Qt组件样式、Vercel部署问题)

- **工作流定义**: 读 [.claude/workflows.md](.claude/workflows.md)
  (WF_DEBUG/WF_REVIEW/WF_COMPLEX等标准化流程)

- **编码协议**: 读 [.claude/coding_standards.md](.claude/coding_standards.md)
  (全局编码规范、ULTRATHINK协议、决策框架)

---

## 🎯 编码标准

**遵循现有linting规则**:

- PEP 8 Python代码风格
- 提交信息遵循 Conventional Commits
- 中文沟通 + 英文代码注释 + 英文搜索关键词

**核心原则** (详细规范见 `.claude/coding_standards.md`):

1. **渐进式开发**: 小步提交,每次都能编译通过和测试通过
2. **从现有代码学习**: 先研究和规划,再开始实现
3. **务实而非教条**: 选择简单明了的解决方案
4. **明确意图而非聪明代码**: 代码要让人一眼看懂

**PyInstaller开发黄金法则**:

```text
修改代码 → 清理build/dist → 重新打包 → 测试exe
```

详见: [PYINSTALLER_DEVELOPMENT_METHODOLOGY.md](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md)

---

## 🚀 快速决策树

**何时使用 Task(Explore) vs 直接处理?**

```text
需要读取 >5个文件?
├─ 是 → Task(subagent_type="Explore")
└─ 否 → 继续

开放式搜索(不确定目标在哪)?
├─ 是 → Task(Explore)
└─ 否 → 直接使用 Glob/Grep/Read

复杂多步骤任务?
├─ 是 → 参考 .claude/workflows.md 选择工作流
└─ 否 → 直接处理
```

**工作流路由逻辑** (详见 `.claude/workflows.md`):

- `/solve_complex [任务]` → WF_COMPLEX (复杂需求分解)
- 关键词"调试/bug/错误" → WF_DEBUG (错误分析)
- 关键词"审查/review" → WF_REVIEW (代码分析)

---

**最后更新**: 2025-12-01
**配置版本**: v4.0 (精简版)
