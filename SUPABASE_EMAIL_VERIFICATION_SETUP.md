# Supabase 邮箱验证配置指南

> 使用Supabase内置的邮箱验证服务，替代自定义OTP验证码方案

## 为什么使用Supabase邮箱验证？

### 当前问题（自定义OTP方案）
- ❌ Resend测试域名只能发送到账号所有者邮箱
- ❌ 需要自己管理OTP存储和过期逻辑
- ❌ 验证码输入错误500崩溃问题
- ❌ 时区处理复杂

### Supabase方案优势
- ✅ **开箱即用**：Supabase Auth自带邮箱验证
- ✅ **无限制**：不受测试域名限制，支持任意邮箱
- ✅ **更安全**：使用一次性验证链接，而非6位数字验证码
- ✅ **零维护**：不需要管理OTP表和过期逻辑
- ✅ **官方支持**：使用Supabase的邮件服务或自定义SMTP

---

## 配置步骤

### 步骤1：启用邮箱验证

1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 选择您的项目（`jindutiao`）
3. 进入 **Authentication → Settings**
4. 找到 **Email Auth** 部分

#### 关键配置项：

**Enable email confirmations（启用邮箱确认）**
```
□ Enable email confirmations
```
- ✅ **勾选此项**
- 作用：用户注册时必须点击邮件中的验证链接才能登录

**Confirm email（确认邮件设置）**
```
□ Enable email change confirmations
  - If enabled, both the user's current and new email will be sent a confirmation link
```
- 建议：根据需求选择（一般不勾选）

**Confirm email template（确认邮件模板）**
- 位置：`Authentication → Email Templates → Confirm signup`
- 默认模板已包含验证链接，可自定义文案和样式

---

### 步骤2：配置邮件服务

Supabase提供两种邮件发送方式：

#### 方案A：使用Supabase内置邮件服务（推荐 - 简单）

**优点：**
- ✅ 零配置，开箱即用
- ✅ 免费额度：每小时60封

**限制：**
- ⚠️ 邮件可能被标记为垃圾邮件（发件人是 `noreply@mail.app.supabase.io`）
- ⚠️ 自定义品牌受限

**配置：**
无需额外配置，Supabase默认使用内置邮件服务。

#### 方案B：使用自定义SMTP服务（生产环境推荐）

**优点：**
- ✅ 使用自己的域名发送（如 `noreply@gaiya.cn`）
- ✅ 更高的送达率
- ✅ 更大的发送量

**支持的SMTP服务：**
- SendGrid
- AWS SES
- Mailgun
- Resend（是的，可以配置Resend作为SMTP）
- 自建SMTP服务器

**配置步骤：**
1. 在 `Authentication → Settings` 中找到 **SMTP Settings**
2. 启用 `Enable Custom SMTP`
3. 填写SMTP配置：
   ```
   SMTP Host: smtp.resend.com（以Resend为例）
   SMTP Port: 587
   SMTP User: resend
   SMTP Password: <your-resend-api-key>
   Sender Email: noreply@yourdomain.com
   Sender Name: GaiYa进度条
   ```
4. 点击 **Save** 并测试发送

---

### 步骤3：配置数据库触发器（关键！）

**问题：** Supabase Auth 的 `email_confirmed_at` 字段存储在 `auth.users` 表（私有schema），我们的 `public.users` 表需要同步更新 `email_verified` 字段。

**解决方案：** 使用数据库触发器监听 `auth.users` 的变化，自动更新 `public.users`。

#### 创建触发器函数：

在 **SQL Editor** 中执行以下SQL：

```sql
-- 1. 创建触发器函数
CREATE OR REPLACE FUNCTION public.handle_email_verification()
RETURNS TRIGGER AS $$
BEGIN
  -- 当 auth.users 的 email_confirmed_at 从 NULL 变为非 NULL 时
  -- 更新 public.users 的 email_verified 和 status 字段
  IF NEW.email_confirmed_at IS NOT NULL AND (OLD.email_confirmed_at IS NULL OR OLD.email_confirmed_at <> NEW.email_confirmed_at) THEN
    UPDATE public.users
    SET
      email_verified = TRUE,
      status = 'active',
      updated_at = NOW()
    WHERE id = NEW.id;

    RAISE NOTICE 'Email verified for user: %', NEW.email;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. 创建触发器（在 auth.users 表上）
DROP TRIGGER IF EXISTS on_email_confirmed ON auth.users;

CREATE TRIGGER on_email_confirmed
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_email_verification();

-- 3. 授予必要的权限
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres, service_role;
```

#### 验证触发器：

```sql
-- 查看触发器是否创建成功
SELECT
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement
FROM information_schema.triggers
WHERE trigger_name = 'on_email_confirmed';
```

---

### 步骤4：自定义邮件模板（可选）

1. 进入 `Authentication → Email Templates`
2. 选择 `Confirm signup`
3. 自定义邮件内容：

**推荐模板（中文）：**

```html
<h2>欢迎注册 GaiYa 每日进度条！</h2>

<p>感谢您注册 GaiYa 每日进度条。</p>

<p>请点击下方按钮验证您的邮箱地址：</p>

<p>
  <a href="{{ .ConfirmationURL }}" style="
    display: inline-block;
    padding: 12px 24px;
    background-color: #4CAF50;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-weight: bold;
  ">验证邮箱</a>
</p>

<p>或复制以下链接到浏览器：<br>
{{ .ConfirmationURL }}</p>

<p><small>此链接将在24小时后过期。如果您没有注册GaiYa账号，请忽略此邮件。</small></p>

<hr>
<p style="color: #999; font-size: 12px;">
  GaiYa 每日进度条 - 让每一天都清晰可见<br>
  https://jindutiao.vercel.app
</p>
```

**关键变量：**
- `{{ .ConfirmationURL }}` - Supabase自动生成的验证链接
- `{{ .Token }}` - 验证令牌（如果需要自定义验证页面）
- `{{ .Email }}` - 用户邮箱
- `{{ .SiteURL }}` - 您的应用URL

4. 点击 **Save** 保存模板

---

### 步骤5：配置重定向URL（可选）

**默认行为：** 用户点击验证链接后，会被重定向到 Supabase 默认页面。

**自定义重定向：** 可以设置验证成功后跳转到您的应用。

1. 在 `Authentication → URL Configuration` 中
2. 找到 **Redirect URLs**
3. 添加：
   ```
   https://jindutiao.vercel.app/auth/callback
   https://localhost:3000/auth/callback (开发环境)
   ```

**注意：** 桌面应用不需要Web重定向，验证完成后会通过API轮询检测到验证状态。

---

## 前端实现

### 注册流程改造

**旧流程（自定义OTP）：**
```
1. 用户注册 → 创建账号
2. 弹出OTPDialog → 用户输入6位验证码
3. 提交验证 → 验证OTP
4. 验证成功 → 登录
```

**新流程（Supabase邮箱验证）：**
```
1. 用户注册 → 创建账号（Supabase自动发送验证邮件）
2. 弹出EmailVerificationDialog → 显示等待状态
3. 用户打开邮箱 → 点击验证链接
4. 前端轮询检测 → 验证状态变为已验证
5. 自动登录 → 关闭对话框
```

### 前端代码示例（待实现）

**文件：** `gaiya/ui/email_verification_dialog.py`

关键功能：
- 显示"请前往邮箱验证"的提示
- 每3秒轮询一次 `/api/auth-check-verification`
- 检测到验证成功后，显示成功动画
- 提供"重新发送"按钮（如果邮件丢失）
- 提供"直接登录"按钮（如果用户已在浏览器中验证）

---

## 测试流程

### 步骤1：测试注册

1. 打开桌面应用，点击"注册"
2. 输入邮箱（任意有效邮箱，不再受限）和密码
3. 点击"注册"

**预期结果：**
- ✅ 注册成功
- ✅ 弹出"等待邮箱验证"对话框
- ✅ 控制台日志：`[AUTH-SIGNUP] verification email sent by Supabase`

### 步骤2：检查邮件

1. 打开注册时使用的邮箱
2. 查找来自 Supabase 的邮件
   - 发件人：`noreply@mail.app.supabase.io`（默认）或您配置的自定义域名
   - 主题：`Confirm Your Signup` 或自定义主题

**如果没有收到邮件：**
- 检查垃圾邮件文件夹
- 在 Supabase Dashboard → Logs 中查看邮件发送日志
- 确认邮箱地址输入正确

### 步骤3：点击验证链接

1. 点击邮件中的"验证邮箱"按钮或链接
2. 浏览器会打开一个Supabase页面（如果未配置自定义重定向）

**预期结果：**
- ✅ 显示"Email confirmed" 或类似成功消息
- ✅ 数据库中 `auth.users` 的 `email_confirmed_at` 被设置为当前时间
- ✅ 触发器自动更新 `public.users` 的 `email_verified = TRUE`

### 步骤4：验证对话框检测

回到桌面应用，观察"等待验证"对话框：

**预期行为：**
- ✅ 对话框中的轮询检测到 `email_verified = TRUE`
- ✅ 显示"验证成功！"消息
- ✅ 自动调用登录API获取Token
- ✅ 关闭对话框，进入应用（已登录状态）

### 步骤5：验证登录状态

1. 检查应用右上角是否显示用户邮箱（已登录）
2. 尝试访问需要登录的功能（如会员中心）

**预期结果：**
- ✅ 用户已登录
- ✅ 可以正常使用所有功能

---

## 故障排查

### 问题1：没有收到验证邮件

**检查清单：**
1. ✅ Supabase Dashboard → Authentication → Settings
   - "Enable email confirmations" 已勾选
2. ✅ Supabase Dashboard → Logs → Edge Logs
   - 搜索 "email" 关键词，查看邮件发送日志
3. ✅ 检查垃圾邮件文件夹
4. ✅ 使用真实的、可接收邮件的邮箱地址

**解决方案：**
- 如果日志显示邮件已发送但未收到 → 使用自定义SMTP
- 如果日志没有发送记录 → 检查是否启用了邮箱确认

### 问题2：触发器未生效

**症状：** 点击验证链接后，`public.users` 的 `email_verified` 仍是 `FALSE`

**检查：**
```sql
-- 1. 检查触发器是否存在
SELECT * FROM information_schema.triggers
WHERE trigger_name = 'on_email_confirmed';

-- 2. 检查 auth.users 的验证状态
SELECT id, email, email_confirmed_at
FROM auth.users
WHERE email = 'test@example.com';

-- 3. 检查 public.users 的同步状态
SELECT id, email, email_verified, status
FROM public.users
WHERE email = 'test@example.com';
```

**解决方案：**
- 重新执行触发器创建SQL
- 检查触发器函数的权限：`GRANT ... TO service_role`

### 问题3：验证成功但前端未检测到

**症状：** 已点击验证链接，但对话框仍显示"等待验证"

**检查：**
1. 打开浏览器开发者工具 → Network
2. 观察 `/api/auth-check-verification` 的响应
3. 检查返回的 `verified` 字段是否为 `true`

**可能原因：**
- 前端轮询间隔过长 → 减少间隔到2-3秒
- API返回缓存 → 在API中添加 `Cache-Control: no-cache` 头
- 触发器未生效 → 见"问题2"

### 问题4：验证链接过期

**症状：** 点击验证链接显示 "Token has expired"

**原因：** Supabase验证链接默认24小时过期

**解决方案：**
1. 在"等待验证"对话框中添加"重新发送邮件"按钮
2. 实现重新发送逻辑：
   ```python
   # API: /api/auth-resend-verification
   auth_manager.resend_verification_email(email)
   ```

---

## 与自定义OTP方案的对比

| 功能 | 自定义OTP | Supabase邮箱验证 |
|------|----------|------------------|
| **发送限制** | ❌ Resend测试域名限制 | ✅ 无限制 |
| **验证方式** | 6位数字验证码 | 一次性验证链接 |
| **安全性** | ⚠️ 验证码可能被猜测 | ✅ 一次性token，更安全 |
| **用户体验** | ⚠️ 需要手动输入验证码 | ✅ 点击链接即可 |
| **维护成本** | ❌ 需要管理OTP表 | ✅ Supabase自动管理 |
| **时区问题** | ❌ 需要处理时区转换 | ✅ Supabase自动处理 |
| **错误处理** | ❌ 500崩溃 | ✅ 稳定可靠 |
| **部署复杂度** | ⚠️ 需要配置Resend API | ✅ 零配置（内置服务） |

**结论：** Supabase邮箱验证方案在所有方面都优于自定义OTP方案，强烈推荐迁移。

---

## 下一步

### 立即可做：
1. ✅ 执行SQL创建数据库触发器
2. ✅ 在Supabase Dashboard启用邮箱确认
3. ✅ 测试注册流程

### 后续优化：
1. 配置自定义SMTP（使用自己的域名）
2. 自定义邮件模板（品牌化）
3. 添加"重新发送验证邮件"功能
4. 优化验证成功后的用户引导

### 需要前端配合：
1. 将 `OTPDialog` 改为 `EmailVerificationDialog`
2. 实现轮询检测验证状态
3. 验证成功后自动登录
4. 提供"重新发送"和"取消"按钮

---

## 参考文档

- [Supabase Auth - Email Confirmation](https://supabase.com/docs/guides/auth/auth-email)
- [Supabase Database Triggers](https://supabase.com/docs/guides/database/postgres/triggers)
- [Supabase Email Templates](https://supabase.com/docs/guides/auth/auth-email-templates)
- [Custom SMTP Setup](https://supabase.com/docs/guides/auth/auth-smtp)

---

**创建时间：** 2025-11-11
**作者：** Claude AI Assistant
**适用项目：** GaiYa 每日进度条
