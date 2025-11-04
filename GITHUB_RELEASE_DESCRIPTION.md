# Gaiya (盖亚) v1.4.0 - 智能模板管理 + 安全性增强

> 🌍 **守护你的每一分钟**
> 🎉 **发布日期**: 2025-11-04
> 🔖 **代号**: Template Enhancement & Security Update

---

## 🌟 主要更新

### ✨ 智能模板保存交互

全新设计的模板保存对话框，让模板管理更高效：

- 🎯 **智能适配**：根据是否有历史模板自动调整UI
- 📋 **直观选择**：下拉框显示所有历史模板及任务数量
- 🔄 **一键覆盖**：选择即覆盖，无需二次确认
- ➕ **快速新建**：直接输入新名称创建模板

**操作演示：**
```
场景1: 首次保存 → 简洁输入框
场景2: 覆盖模板 → 下拉选择"工作日模板 (8个任务)"
场景3: 新建模板 → 下拉框输入"周末模板"
```

### 🔒 安全性重大改进

**减少杀毒软件误报 50-70%！**

- 🚫 禁用UPX压缩（主要原因）
- 📄 添加版本信息资源
- 🛡️ 提交白名单申请（进行中）

**详细说明请查看**: [SECURITY.md](https://github.com/jiamizhongshifu/jindutiao/blob/main/SECURITY.md)

### 🐛 Bug修复

1. **模板保存**
   - 修复：重复保存同名模板无提示的问题
   - 改进：保存成功后明确提示"已创建"或"已更新"

2. **WebP动画性能优化**
   - 修复：动画播放中途停顿的问题
   - 优化：使用帧缓存技术，帧间隔精度从±21ms提升到±1.2ms

3. **主题配色同步**
   - 修复：保存主题后进度条颜色未立即刷新的问题
   - 改进：reload_all() 中添加主题重新应用逻辑

---

## 📥 下载

### Windows 64-bit

下载下方的 **Gaiya-v1.4.exe** 文件（53 MB）
（文件名暂为 PyDayBar-v1.4.exe，v1.5将统一为Gaiya）

### 文件完整性验证

```
MD5:    752CB26CDAC6EE35A4E1AF37C345E14E
SHA256: DB824CB5EBBA03FA9CD1EEDCC8A4A286FFB1BC9AD4BD2FAEE94049CF335DD947
```

**验证方法（Windows PowerShell）：**
```powershell
Get-FileHash -Path "PyDayBar-v1.4.exe" -Algorithm SHA256
```

**验证方法（命令提示符）：**
```cmd
certutil -hashfile PyDayBar-v1.4.exe SHA256
```

注：文件名暂为PyDayBar-v1.4.exe，从v1.5开始将统一使用Gaiya命名

---

## 🔒 关于杀毒软件误报

### 为什么会误报？

Gaiya 使用PyInstaller打包（Python应用标准方式），部分杀毒软件可能误报。

### v1.4的改进

✅ **已禁用UPX压缩** - 减少50-70%误报
🟡 **白名单申请中** - 预计1-2周通过
📖 **完全开源** - 所有代码可审计

### 如何安装？

**推荐方法：添加到杀毒软件信任列表**

**Windows Defender：**
1. 打开"Windows 安全中心"
2. "病毒和威胁防护" → "管理设置"
3. "排除项" → "添加排除项" → 选择文件
4. 选择 `PyDayBar-v1.4.exe`

**360安全卫士：**
1. 打开360安全卫士 → 设置 → 信任与阻止
2. 信任区 → 添加信任文件
3. 选择 `PyDayBar-v1.4.exe`

**火绒安全：**
1. 打开火绒 → 菜单 → 信任区
2. 添加文件 → 选择 `PyDayBar-v1.4.exe`

**详细指南**：
- [安装教程](https://github.com/jiamizhongshifu/jindutiao/blob/main/SECURITY.md#-如何安全使用)
- [误报解决方案](https://github.com/jiamizhongshifu/jindutiao/blob/main/反病毒误报解决方案.md)

---

## 📋 完整更新日志

### ✨ 新增
- 智能模板保存对话框（SaveTemplateDialog类）
- 保存成功后区分"创建"/"更新"提示

### 🔒 安全性
- 禁用UPX压缩减少误报
- 添加Windows版本信息
- 准备白名单提交材料

### 🐛 修复
- 模板覆盖前无提示问题
- 保存提示信息不准确问题
- WebP动画播放卡顿问题
- 主题保存后颜色未刷新问题

### 📝 文档
- 新增 SECURITY.md
- 新增 CHANGELOG.md
- 新增 反病毒误报解决方案.md

**查看完整更新**: [CHANGELOG.md](https://github.com/jiamizhongshifu/jindutiao/blob/main/CHANGELOG.md)

---

## 🎯 升级指南

### 从 v1.3 升级

1. 关闭正在运行的旧版本
2. 下载 PyDayBar-v1.4.exe
3. 替换旧文件
4. 运行新版本

**数据兼容性**: ✅ 所有配置自动保留

---

## 📋 系统要求

- **操作系统**: Windows 10/11 (64-bit)
- **内存**: 最低 512 MB RAM
- **磁盘空间**: 100 MB 可用空间
- **屏幕分辨率**: 建议 1920x1080 或更高

---

## 📞 问题反馈

- 🐛 [Bug反馈](https://github.com/jiamizhongshifu/jindutiao/issues)
- 💬 [功能建议](https://github.com/jiamizhongshifu/jindutiao/discussions)

---

## 🙏 致谢

感谢所有提供反馈的用户！本次更新主要基于：

- 模板管理体验优化需求
- 杀毒软件误报问题反馈
- 安全性审计建议

**🌟 如果 Gaiya 对你有帮助，请给我们一个 Star！**
