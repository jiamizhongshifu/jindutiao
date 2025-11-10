# GaiYa OTP邮箱验证 - 快速配置指南 🚀

> **当前状态**: OTP功能已启用（开发模式）
> **更新时间**: 2025-11-11
> **提交**: b4005b6

---

## ✅ 已完成的工作

### 前端集成
- ✅ `gaiya/ui/auth_ui.py` - OTP验证流程已启用
- ✅ `gaiya/core/auth_client.py` - 添加 `send_otp()` 和 `verify_otp()` API
- ✅ `gaiya/ui/otp_dialog.py` - 6位数字输入对话框（已存在）

### 后端集成
- ✅ `api/auth-send-otp.py` - 发送OTP API（已存在）
- ✅ `api/auth-verify-otp.py` - 验证OTP API（已存在）
- ✅ `api/auth_manager.py` - 集成Resend邮件服务

### 当前行为
- 📧 **未配置Resend**: OTP输出到控制台（开发模式）
- 📧 **配置Resend后**: 发送精美HTML邮件到用户邮箱

---

## 🔧 配置步骤

### 步骤1: 配置Supabase（必须）⚠️

**操作**：
1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 选择你的项目
3. 进入 `Authentication` → `Providers` → `Email`
4. **关闭** "Confirm email" 开关
5. 点击 **Save** 保存

**原因**:
- 我们使用自己的OTP系统，不需要Supabase的默认邮件确认
- 关闭后用户注册立即创建账号，但需要通过OTP验证邮箱

---

### 步骤2: 配置Resend邮件服务（推荐）

#### 方案A: 本地开发测试（当前）

**不需要任何配置！**
- OTP会输出到Vercel控制台日志
- 适合本地开发和测试
- 查看OTP：`vercel logs` 或 Vercel Dashboard → Functions → Logs

#### 方案B: 生产环境（发送真实邮件）

**1. 注册Resend账号**
- 访问 [Resend.com](https://resend.com/)
- 免费额度：**3000封/月**（足够使用）
- 无需信用卡

**2. 验证域名（可选）**

**选项A: 使用测试域名**（最快）
```
发件人: noreply@resend.dev
优点: 无需验证，立即可用
缺点: 显示"via resend.dev"
```

**选项B: 使用自己的域名**（推荐）
```
发件人: noreply@yourdomain.com
优点: 专业，无第三方标识
缺点: 需要添加DNS记录

步骤:
1. Resend Dashboard → Domains → Add Domain
2. 输入 yourdomain.com
3. 添加提供的DNS记录（TXT, MX, CNAME）
4. 等待验证（通常几分钟）
```

**3. 获取API Key**
```
Resend Dashboard → API Keys → Create API Key
权限: Full Access（或Send access）
复制API Key（仅显示一次！）
```

**4. 配置环境变量**

**Vercel环境变量**（必须）:
```bash
# 进入 Vercel Dashboard
1. 选择项目 jindutiao
2. Settings → Environment Variables
3. 添加新变量：
   Name: RESEND_API_KEY
   Value: re_xxxxxxxxxxxxx（你的API Key）
   Environment: Production, Preview, Development（全选）
4. 点击 Save
5. 重新部署项目（Vercel会自动触发）
```

**5. 修改发件人地址**（如果使用自己的域名）

修改 `api/auth_manager.py:469`：
```python
"from": "GaiYa <noreply@yourdomain.com>",  # 改为你的域名
```

提交并推送到GitHub，Vercel会自动部署。

---

## 🧪 测试流程

### 开发模式测试（当前）

1. **运行桌面应用**：
   ```bash
   python config_gui.py
   ```

2. **注册新用户**：
   - 点击"个人中心" → "登录"
   - 切换到"注册"标签
   - 填写邮箱和密码
   - 点击"注册"

3. **查看OTP验证码**：
   - 弹出OTP输入对话框
   - 查看Vercel控制台日志或本地终端
   - 找到 `[DEV MODE] OTP Code for xxx@example.com: 123456`

4. **输入验证码**：
   - 在对话框中输入6位验证码
   - 验证成功后自动登录

### 生产模式测试（配置Resend后）

1. **注册新用户**（同上）

2. **检查邮箱**：
   - 用户会收到精美的HTML邮件
   - 标题："欢迎注册GaiYa - 验证您的邮箱"
   - 内容包含6位验证码

3. **输入验证码**（同上）

4. **验证Resend日志**：
   - 登录 Resend Dashboard → Emails
   - 查看发送记录和状态

---

## 📊 功能特性

### OTP安全特性
- ✅ 6位随机数字（100000-999999）
- ✅ 10分钟有效期
- ✅ 最多5次验证尝试
- ✅ 60秒重发冷却
- ✅ 防暴力破解

### 邮件模板
- ✅ 响应式HTML设计
- ✅ 注册欢迎邮件（绿色主题）
- ✅ 密码重置邮件（橙色主题）
- ✅ 清晰的验证码展示
- ✅ 安全提示和有效期说明

### 用户体验
```
注册流程：
1. 用户填写邮箱密码 → 点击注册
   ↓
2. 后端创建账号 → 发送OTP
   ↓
3. 自动弹出OTP输入对话框
   ↓
4. 用户输入验证码 → 自动验证
   ↓
5. 验证成功 → 自动登录应用
```

---

## ⚠️ 注意事项

### Supabase配置
- ⚠️ **必须关闭** "Confirm email" 开关
- ⚠️ 否则用户会收到两封邮件（Supabase的 + 我们的OTP）

### Resend配置
- 💡 本地测试无需配置Resend
- 💡 生产环境建议配置，提供更好的用户体验
- 💡 使用自己的域名发件人更专业

### 邮件发送限制
- Resend免费版：3000封/月
- 如果用户量大，考虑升级或使用其他服务（SendGrid, AWS SES）

---

## 🐛 常见问题

### Q: 为什么OTP没有发送到邮箱？
**A**: 检查以下几点：
1. Vercel环境变量 `RESEND_API_KEY` 是否配置
2. Resend账号是否激活
3. 发件人地址是否已验证（如果使用自己的域名）
4. 查看Vercel函数日志，搜索 `[ERROR]` 或 `[WARNING]`

### Q: OTP验证码输入错误？
**A**:
- 检查验证码是否过期（10分钟有效期）
- 最多尝试5次，超过后需重新获取
- 点击"重新发送"获取新验证码（60秒冷却）

### Q: 用户注册后没有弹出OTP对话框？
**A**:
- 检查前端代码是否最新（`git pull`）
- 查看桌面应用控制台是否有错误
- 确认后端API `/api/auth-send-otp` 返回成功

### Q: 想切换回不验证邮箱（方案A）？
**A**:
修改 `gaiya/ui/auth_ui.py:314-344`，注释OTP流程，改为直接登录：
```python
if result.get("success"):
    # 直接登录（方案A）
    user_info = {
        "user_id": result.get("user_id"),
        "email": email,
        "user_tier": "free"
    }
    self.login_success.emit(user_info)
    self.accept()
```

---

## 📈 下一步优化（可选）

### P1 - 前端增强验证
- [ ] 邮箱格式正则验证（不只是检查 `@`）
- [ ] 密码强度指示器（弱/中/强）
- [ ] 实时错误提示（输入时即时反馈）

### P2 - 后端安全增强
- [ ] 请求频率限制（防恶意注册）
- [ ] IP黑名单机制
- [ ] 邮箱域名黑名单（过滤临时邮箱）

### P3 - 用户体验优化
- [ ] 支持多语言邮件模板（中/英）
- [ ] 邮件模板可视化编辑
- [ ] 发送状态实时追踪

---

## 📞 技术支持

**文档**:
- 详细指南: `docs/desktop-email-verification-guide.md`
- API文档: `api/README.md`

**相关文件**:
```
前端:
  gaiya/ui/auth_ui.py         # 注册流程入口
  gaiya/ui/otp_dialog.py      # OTP输入对话框
  gaiya/core/auth_client.py   # API客户端

后端:
  api/auth-send-otp.py        # 发送OTP API
  api/auth-verify-otp.py      # 验证OTP API
  api/auth_manager.py         # 邮件发送逻辑
```

**日志查看**:
```bash
# Vercel控制台日志
vercel logs --follow

# 或在 Vercel Dashboard
Functions → 选择函数 → Logs
```

---

**当前状态**: ✅ 开发模式运行正常，可以开始测试！
**推荐**: 先在开发模式测试完整流程，确认无误后再配置Resend
