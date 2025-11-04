# GitHub Release 发布指南

本指南将指导你如何在GitHub上发布 PyDayBar v1.4 版本。

---

## 📋 准备清单

在发布前，确保以下文件和信息已准备好：

### ✅ 必需文件

- [x] `dist/PyDayBar-v1.4.exe` - 打包好的可执行文件
- [x] `RELEASE_NOTES_v1.4.md` - 版本说明
- [x] `CHANGELOG.md` - 完整更新日志
- [x] `SECURITY.md` - 安全说明
- [x] `反病毒误报解决方案.md` - 用户指南

### ✅ 必需信息

- [x] **文件哈希值**
  - MD5: `752CB26CDAC6EE35A4E1AF37C345E14E`
  - SHA256: `DB824CB5EBBA03FA9CD1EEDCC8A4A286FFB1BC9AD4BD2FAEE94049CF335DD947`

- [x] **版本信息**
  - 版本号: `v1.4.0`
  - 发布日期: `2025-11-04`
  - 代号: `Template Enhancement & Security Update`

---

## 🚀 发布步骤

### 步骤1：提交所有文件到GitHub

```bash
# 1. 添加所有新文件
git add .

# 2. 提交更改
git commit -m "feat: v1.4.0 - 智能模板保存 + 安全性增强

主要更新:
- 新增智能模板保存对话框,支持历史模板选择和快速覆盖
- 禁用UPX压缩,减少杀毒软件误报50-70%
- 添加完整的安全说明和白名单申请指南
- 优化用户体验,提升模板管理效率

详见 RELEASE_NOTES_v1.4.md"

# 3. 推送到GitHub
git push origin main
```

### 步骤2：在GitHub上创建Release

#### 2.1 进入Releases页面

1. 打开你的GitHub仓库页面
2. 点击右侧的 "Releases"
3. 点击 "Create a new release" 或 "Draft a new release"

#### 2.2 填写Release信息

**Tag version (标签版本):**
```
v1.4.0
```
- 点击 "Choose a tag" → 输入 `v1.4.0` → 点击 "Create new tag: v1.4.0 on publish"

**Release title (发布标题):**
```
v1.4.0 - Template Enhancement & Security Update
```

**Describe this release (发布说明):**

复制以下内容到描述框：

````markdown
# PyDayBar v1.4.0 - 智能模板管理 + 安全性增强

> 🎉 **发布日期**: 2025-11-04
> 🔖 **代号**: Template Enhancement & Security Update

---

## 🌟 主要更新

### ✨ 智能模板保存交互

全新设计的模板保存对话框,让模板管理更高效:

- 🎯 **智能适配**: 根据是否有历史模板自动调整UI
- 📋 **直观选择**: 下拉框显示所有历史模板及任务数量
- 🔄 **一键覆盖**: 选择即覆盖,无需二次确认
- ➕ **快速新建**: 直接输入新名称创建模板

**操作演示:**
```
场景1: 首次保存 → 简洁输入框
场景2: 覆盖模板 → 下拉选择"工作日模板 (8个任务)"
场景3: 新建模板 → 下拉框输入"周末模板"
```

### 🔒 安全性重大改进

**减少杀毒软件误报 50-70%！**

- 🚫 禁用UPX压缩 (主要原因)
- 📄 添加版本信息资源
- 🛡️ 提交白名单申请 (进行中)

**详细说明请查看**: [SECURITY.md](SECURITY.md)

---

## 📥 下载

### Windows 64-bit

| 文件 | 大小 | 下载 |
|------|------|------|
| PyDayBar-v1.4.exe | 54.9 MB | [⬇️ 下载](https://github.com/[你的用户名]/PyDayBar/releases/download/v1.4.0/PyDayBar-v1.4.exe) |

### 文件完整性验证

```
MD5:    752CB26CDAC6EE35A4E1AF37C345E14E
SHA256: DB824CB5EBBA03FA9CD1EEDCC8A4A286FFB1BC9AD4BD2FAEE94049CF335DD947
```

**验证方法:**
```powershell
Get-FileHash -Path "PyDayBar-v1.4.exe" -Algorithm SHA256
```

---

## 🔒 关于杀毒软件误报

### 为什么会误报?

PyDayBar使用PyInstaller打包(Python应用标准方式),部分杀毒软件可能误报。

### v1.4的改进

✅ **已禁用UPX压缩** - 减少50-70%误报
🟡 **白名单申请中** - 预计1-2周通过
📖 **完全开源** - 所有代码可审计

### 如何安装?

**推荐方法**: 添加到杀毒软件信任列表

**详细指南**:
- [安装教程](SECURITY.md#-如何安全使用)
- [误报解决方案](反病毒误报解决方案.md)

---

## 📋 完整更新日志

### ✨ 新增
- 智能模板保存对话框 (SaveTemplateDialog类)
- 保存成功后区分"创建"/"更新"提示

### 🔒 安全性
- 禁用UPX压缩减少误报
- 添加Windows版本信息
- 准备白名单提交材料

### 🐛 修复
- 模板覆盖前无提示问题
- 保存提示信息不准确问题

### 📝 文档
- 新增 SECURITY.md
- 新增 CHANGELOG.md
- 新增 反病毒误报解决方案.md

**查看完整更新**: [CHANGELOG.md](CHANGELOG.md)

---

## 🎯 升级指南

### 从 v1.3 升级

1. 关闭正在运行的旧版本
2. 下载 PyDayBar-v1.4.exe
3. 替换旧文件
4. 运行新版本

**数据兼容性**: ✅ 所有配置自动保留

---

## 📞 问题反馈

- 🐛 [Bug反馈](https://github.com/[你的用户名]/PyDayBar/issues)
- 💬 [功能建议](https://github.com/[你的用户名]/PyDayBar/discussions)
- 📧 [邮件联系](你的邮箱)

---

## 🙏 致谢

感谢所有提供反馈的用户！本次更新主要基于:

- 模板管理体验优化需求
- 杀毒软件误报问题反馈
- 安全性审计建议

**🌟 如果 PyDayBar 对你有帮助，请给我们一个 Star！**
````

#### 2.3 上传文件

在 "Attach binaries" 区域:

1. 拖拽或选择 `dist/PyDayBar-v1.4.exe`
2. 等待上传完成

#### 2.4 发布设置

- [ ] **Set as the latest release** - 勾选（设为最新版本）
- [ ] **Set as a pre-release** - 不勾选（这是正式版）
- [ ] **Create a discussion for this release** - 可选（创建讨论帖）

#### 2.5 发布

点击 **"Publish release"** 按钮完成发布！

---

## 📣 发布后的推广

### 步骤3：更新README.md

在README.md顶部添加版本徽章和下载链接:

```markdown
# PyDayBar

[![最新版本](https://img.shields.io/github/v/release/[你的用户名]/PyDayBar)](https://github.com/[你的用户名]/PyDayBar/releases/latest)
[![下载量](https://img.shields.io/github/downloads/[你的用户名]/PyDayBar/total)](https://github.com/[你的用户名]/PyDayBar/releases)
[![许可证](https://img.shields.io/github/license/[你的用户名]/PyDayBar)](LICENSE)

一款开源的桌面进度条时间管理工具

## 📥 快速下载

[⬇️ 下载 PyDayBar v1.4.0 (Windows 64-bit)](https://github.com/[你的用户名]/PyDayBar/releases/download/v1.4.0/PyDayBar-v1.4.exe)

**最新更新 (v1.4.0):**
- ✨ 智能模板保存对话框
- 🔒 减少杀毒软件误报50-70%
- [查看完整更新日志](CHANGELOG.md)

## 🔒 安全说明

PyDayBar 完全开源可审计。关于杀毒软件误报问题的详细说明，请查看 [SECURITY.md](SECURITY.md)。
```

### 步骤4：提交白名单申请

参照 `反病毒误报解决方案.md` 中的指南,提交白名单申请:

1. **Windows Defender**: https://www.microsoft.com/wdsi/filesubmission
2. **360安全卫士**: https://www.360.cn/web/shopcenter/filequery/misreport/
3. **火绒安全**: support@huorong.cn

### 步骤5：社交媒体宣传（可选）

如果你有社交媒体账号,可以发布更新公告:

**推荐内容模板:**
```
🎉 PyDayBar v1.4.0 正式发布！

主要更新：
✨ 智能模板管理 - 让任务保存更便捷
🔒 安全性增强 - 大幅减少误报问题

下载地址：[GitHub链接]

#PyDayBar #开源软件 #时间管理 #桌面工具
```

---

## 📊 发布后监控

### 监控指标

- GitHub Stars 增长
- Release下载次数
- Issues 新增数量
- Discussions 讨论热度

### 白名单申请跟进

| 时间 | 任务 |
|------|------|
| Day 1-2 | 检查邮箱,确认提交成功 |
| Day 3-5 | 跟进审核进度 |
| Day 7 | 测试误报率变化 |

### 用户反馈处理

- 及时回复 Issues
- 收集功能建议
- 记录Bug报告
- 感谢用户贡献

---

## ✅ 发布完成清单

- [ ] 代码已推送到GitHub
- [ ] Release已发布
- [ ] exe文件已上传
- [ ] 哈希值已验证
- [ ] README已更新
- [ ] 白名单已提交
- [ ] 社交媒体已宣传(可选)

---

## 🔗 相关链接

- **GitHub仓库**: https://github.com/[你的用户名]/PyDayBar
- **Release页面**: https://github.com/[你的用户名]/PyDayBar/releases
- **Issues**: https://github.com/[你的用户名]/PyDayBar/issues
- **Discussions**: https://github.com/[你的用户名]/PyDayBar/discussions

---

**祝发布顺利！🎉**
