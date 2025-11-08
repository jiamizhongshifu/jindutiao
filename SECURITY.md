# 安全说明 / Security

## 🔒 关于杀毒软件误报

### 这是病毒吗？

**不是！** Gaiya (盖亚) 是完全开源的桌面应用程序，所有源代码公开透明可审计。

### 为什么会被杀毒软件报毒？

Gaiya 使用 **PyInstaller** 打包，这是 Python 应用的标准打包方式。部分杀毒软件可能因以下原因误报：

1. **打包方式特征**
   - PyInstaller 将 Python 解释器和代码打包成单个可执行文件
   - 自解压运行机制与某些恶意软件相似
   - 杀毒软件的启发式检测可能误判

2. **系统操作权限**
   - 读写本地配置文件（JSON格式，位于 `%APPDATA%\PyDayBar\`）
   - 访问 Windows 注册表实现开机自启（需用户授权）
   - 创建系统托盘图标

3. **软件知名度**
   - 新软件缺乏用户量和信誉积累
   - 未经微软 SmartScreen 验证
   - 无代码签名证书

---

## ✅ 我们的安全措施

### 1. 开源透明

- **GitHub仓库**: [https://github.com/jiamizhongshifu/jindutiao](https://github.com/jiamizhongshifu/jindutiao)
- **完整源代码**: 所有功能的实现代码完全公开
- **可审计性**: 任何人都可以审查代码逻辑
- **社区监督**: 接受开源社区的安全审查

### 2. 减少误报技术

**v1.4.0 新增：**
- ✅ **禁用UPX压缩**：降低50-70%误报率
- ✅ **添加版本信息**：增加软件正规性
- 🔜 **白名单申请**：已向主流杀毒软件提交申请

### 3. 白名单申请进度

| 杀毒软件 | 提交时间 | 状态 | 预计完成 |
|---------|---------|------|---------|
| Windows Defender | 2025-11-04 | 🟡 审核中 | 1-3天 |
| 360安全卫士 | 2025-11-04 | 🟡 审核中 | 3-7天 |
| 火绒安全 | 2025-11-04 | 🟡 审核中 | 3-7天 |

---

## 🛡️ 安全验证

### 文件完整性验证

**官方发布哈希值（v1.4.0）：**

```
MD5:    752CB26CDAC6EE35A4E1AF37C345E14E
SHA256: DB824CB5EBBA03FA9CD1EEDCC8A4A286FFB1BC9AD4BD2FAEE94049CF335DD947
```

**验证方法（Windows PowerShell）：**

```powershell
# 计算MD5
Get-FileHash -Path "PyDayBar-v1.4.exe" -Algorithm MD5

# 计算SHA256
Get-FileHash -Path "PyDayBar-v1.4.exe" -Algorithm SHA256
```

**验证方法（命令提示符）：**

```cmd
certutil -hashfile PyDayBar-v1.4.exe MD5
certutil -hashfile PyDayBar-v1.4.exe SHA256
```

**重要提示：**
- ✅ 哈希值匹配：文件未被篡改，可安全使用
- ❌ 哈希值不匹配：文件可能被修改，请勿使用！

---

## 🔐 隐私保护

### Gaiya 收集哪些数据？

**我们不收集任何个人数据！**

Gaiya 是完全本地运行的应用：
- ✅ 所有数据存储在本地（`%APPDATA%\PyDayBar\`）
- ✅ 无需注册、无需登录
- ✅ 无后台上传
- ✅ 无广告、无追踪

### 唯一的网络请求

**AI功能（可选）：**
- 使用场景：当用户点击"AI智能生成任务"时
- 请求目标：Vercel Serverless Functions（开源API）
- 传输数据：用户输入的任务描述（如"工作日"）
- 返回数据：AI生成的任务列表（纯文本JSON）
- 隐私保护：
  - 不记录用户IP
  - 不存储历史记录
  - 不关联用户身份
  - 可在设置中完全禁用

**网络请求完整代码：**
- 客户端：`ai_client.py`
- 服务端：`vercel_api/plan-tasks.py`（开源）

---

## 🚨 如何安全使用？

### 方案1：添加到信任列表（推荐）

**Windows Defender：**
```
打开"Windows 安全中心"
→ "病毒和威胁防护"
→ "管理设置"
→ "排除项"
→ "添加排除项"
→ 选择 PyDayBar-v1.4.exe
```

**360安全卫士：**
```
打开360安全卫士
→ 设置
→ 信任与阻止
→ 信任区
→ 添加信任文件
→ 选择 PyDayBar-v1.4.exe
```

**火绒安全：**
```
打开火绒安全
→ 菜单
→ 信任区
→ 添加文件
→ 选择 PyDayBar-v1.4.exe
```

### 方案2：从源代码构建（最安全）

如果您对安全有极高要求，可以从源代码自行构建：

```bash
# 1. 克隆仓库
git clone https://github.com/[你的用户名]/PyDayBar.git
cd PyDayBar

# 2. 安装依赖
pip install -r requirements.txt

# 3. 直接运行源代码
python main.py

# 4. 或自行打包
pyinstaller PyDayBar.spec
```

**优点：**
- ✅ 完全可控，可审查每一行代码
- ✅ 自己打包的程序，100%可信
- ✅ 可根据需要修改功能

---

## 🔍 代码审计指南

### 关键安全文件

如果您想审计 Gaiya 的安全性，建议重点查看：

1. **注册表操作**
   - 文件：`autostart_manager.py`
   - 功能：开机自启动管理
   - 权限：仅读写 `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`

2. **文件系统操作**
   - 文件：`pydaybar/utils/path_utils.py`
   - 功能：读写配置文件
   - 范围：仅限 `%APPDATA%\PyDayBar\` 目录

3. **网络请求**
   - 文件：`ai_client.py`
   - 功能：AI任务生成（可选）
   - 目标：`https://jindutiao.vercel.app/api/`
   - 数据：仅发送用户输入的任务描述

### 审计清单

- [ ] 无可疑的网络请求
- [ ] 无访问敏感系统目录
- [ ] 无注册表恶意修改
- [ ] 无进程注入或钩子
- [ ] 无加密货币挖矿
- [ ] 无后门或远程控制

---

## 📞 安全问题报告

如果您发现 PyDayBar 存在安全漏洞，请**负责任地披露**：

### 联系方式

- **GitHub Security**: [Report a vulnerability](https://github.com/[你的用户名]/PyDayBar/security/advisories/new)
- **邮件**: [你的邮箱]（请在主题中标注 [SECURITY]）

### 不要

- ❌ 在公开 Issues 中披露安全漏洞
- ❌ 在社交媒体上公开漏洞细节

### 应该

- ✅ 通过私密渠道报告
- ✅ 给我们合理的修复时间（建议14天）
- ✅ 提供复现步骤和影响评估

---

## 🏆 安全荣誉榜

感谢以下安全研究者的贡献：

*（暂无安全报告）*

---

## 📜 许可证

Gaiya 遵循 [MIT License](LICENSE) 开源协议。

```
MIT License

Copyright (c) 2025 Gaiya Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🔐 安全政策与漏洞响应

### 支持的版本

| 版本 | 支持状态 |
|------|---------|
| 1.5.x | ✅ 完全支持 |
| 1.4.x | ⚠️ 有限支持（仅严重漏洞） |
| < 1.4 | ❌ 不再支持 |

### 漏洞响应时间

- **确认收到**: 24小时内
- **初步评估**: 3个工作日内
- **修复发布**:
  - 🔴 严重（Critical）: 7天内
  - 🟠 高危（High）: 14天内
  - 🟡 中危（Medium）: 30天内

### 报告安全漏洞

**首选方式**: [GitHub Private Security Advisory](https://github.com/jiamizhongshifu/jindutiao/security/advisories/new)

**报告内容应包含**:
- 漏洞描述与影响范围
- 详细的复现步骤
- 概念验证（PoC）代码
- 建议修复方案

### 安全更新发布流程

1. 漏洞确认与评估
2. 在私有分支开发修复
3. 内部测试验证
4. 发布安全更新版本
5. 30天后公开披露细节

---

## 🛡️ 安全架构

### 数据安全

- ✅ 所有API通信使用HTTPS加密
- ✅ 密码使用bcrypt哈希（Supabase默认）
- ✅ Token使用JWT标准
- ⚠️ 本地Token存储在 `~/.gaiya/auth.json`（建议加密）

### API安全措施

- ✅ 所有支付回调有签名验证
- ✅ 输入验证（邮箱、密码、金额等）
- ✅ 支付金额服务端验证（防篡改）
- ⚠️ 计划添加速率限制（防暴力破解）

### 第三方依赖安全

定期使用 GitHub Dependabot 扫描依赖漏洞，保持依赖库更新。

---

## 📋 安全最佳实践

### 对于用户

1. **使用强密码**: 至少8位，包含大小写字母和数字
2. **保护本地凭证**: `~/.gaiya/auth.json` 包含登录Token
3. **验证下载源**: 仅从官方GitHub Releases下载
4. **及时更新**: 使用最新版本获取安全修复

### 对于开发者

1. **环境变量**: 所有敏感凭证通过环境变量配置
2. **代码审查**: 提交前检查是否包含硬编码凭证
3. **输入验证**: 使用 `api/validators.py` 验证所有输入
4. **依赖更新**: 定期运行 `pip list --outdated` 检查更新
5. **安全测试**: 部署前运行 `python -m bandit -r .` 扫描

---

**最后更新**: 2025-11-08
**当前版本**: v1.5.1
