# email_verification_dialog.py 国际化规划文档

## 📅 创建时间
2025-11-23

## 📊 字符串统计
- **原始字符串数**: 44个
- **唯一字符串数**: 42个
- **规划翻译键**: 38个

## 🗂️ 命名空间设计

### 命名空间结构
```
email_verification
├── dialog            # 对话框UI (8个)
├── button            # 按钮文本 (3个)
├── log               # 日志消息 (9个)
├── message           # 用户消息 (13个)
└── confirm           # 确认对话框 (2个)
```

## 📋 详细翻译键列表

### 1. email_verification.dialog - 对话框UI (8个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| title | 验证您的邮箱 | Verify Your Email | 47 |
| sent_title | 验证邮件已发送 | Verification Email Sent | 65 |
| sent_message_html | 我们已向 <b>{email}</b> 发送了一封验证邮件。<br><br>请打开您的邮箱，点击邮件中的<b>验证链接</b>完成注册。<br><br><small>验证完成后，本窗口将自动关闭并登录。</small> | We have sent a verification email to <b>{email}</b>.<br><br>Please open your inbox and click the <b>verification link</b> in the email to complete registration.<br><br><small>This window will automatically close and log you in after verification.</small> | 75-77 |
| waiting_status | ⏳ 等待邮箱验证... | ⏳ Waiting for email verification... | 85 |
| tips_html | 💡 <b>小贴士：</b><br>• 请检查垃圾邮件文件夹<br>• 验证链接有效期为24小时<br>• 如果没有收到邮件，可以点击下方 | 💡 <b>Tips:</b><br>• Check your spam folder<br>• Verification link is valid for 24 hours<br>• If you didn't receive the email, click below | 122-125 |
| verified_success | ✅ 邮箱验证成功！ | ✅ Email Verified Successfully! | 255 |
| welcome_title | 欢迎 | Welcome | 308 |
| welcome_message | 欢迎！{email}\n\n您已成功注册并登录 GaiYa 每日进度条。 | Welcome! {email}\n\nYou have successfully registered and logged into GaiYa Daily Progress Bar. | 309 |

### 2. email_verification.button - 按钮文本 (3个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| resend | 重新发送验证邮件 | Resend Verification Email | 145, 369 |
| cancel | 取消 | Cancel | 170 |
| sending | 发送中... | Sending... | 337 |

### 3. email_verification.log - 日志消息 (9个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| start_polling | [EMAIL-VERIFICATION] 开始轮询验证状态，邮箱: {email} | [EMAIL-VERIFICATION] Start polling verification status, email: {email} | 193 |
| checking | [EMAIL-VERIFICATION] 第{count}次检查验证状态... | [EMAIL-VERIFICATION] Checking verification status (attempt {count})... | 218 |
| not_verified_yet | [EMAIL-VERIFICATION] 尚未验证，继续等待... | [EMAIL-VERIFICATION] Not verified yet, continuing to wait... | 238 |
| check_failed_http | [EMAIL-VERIFICATION] 检查失败: HTTP {status_code} | [EMAIL-VERIFICATION] Check failed: HTTP {status_code} | 240 |
| check_timeout | [EMAIL-VERIFICATION] 检查超时，将在5秒后重试 | [EMAIL-VERIFICATION] Check timeout, retrying in 5 seconds | 243 |
| check_error | [EMAIL-VERIFICATION] 检查错误: {e} | [EMAIL-VERIFICATION] Check error: {e} | 245 |
| verified_log | [EMAIL-VERIFICATION] 验证成功！邮箱: {email} | [EMAIL-VERIFICATION] Verification successful! Email: {email} | 249 |
| auto_login_start | [EMAIL-VERIFICATION] 开始自动登录... | [EMAIL-VERIFICATION] Starting auto login... | 273 |
| auto_login_success | [EMAIL-VERIFICATION] 自动登录成功！ | [EMAIL-VERIFICATION] Auto login successful! | 300 |

### 4. email_verification.message - 用户消息 (13个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| timeout_warning | ⏰ 验证超时，请重新发送验证邮件 | ⏰ Verification timeout, please resend verification email | 203 |
| verified_success_title | 验证成功 | Verification Successful | 279 |
| verified_success_message | 邮箱验证成功！请使用您的邮箱和密码登录。 | Email verification successful! Please log in with your email and password. | 280 |
| login_failed_title | 登录失败 | Login Failed | 316 |
| auto_login_failed_title | 自动登录失败 | Auto Login Failed | 319, 328 |
| auto_login_failed_message | 邮箱验证成功，但自动登录失败：{error}\n\n请手动登录。 | Email verification successful, but auto login failed: {error}\n\nPlease log in manually. | 320 |
| auto_login_error_message | 邮箱验证成功，但自动登录出错：{error}\n\n请手动登录。 | Email verification successful, but auto login error: {error}\n\nPlease log in manually. | 329 |
| resend_success_title | 发送成功 | Sent Successfully | 349 |
| resend_success_message | 验证邮件已重新发送，请查收您的邮箱。 | Verification email has been resent, please check your inbox. | 350 |
| resend_failed_title | 发送失败 | Send Failed | 357 |
| resend_failed_message | 重新发送失败，请稍后重试 | Resend failed, please try again later | 358 |
| resend_error_title | 错误 | Error | 364 |
| resend_error_message | 重新发送失败：{error} | Resend failed: {error} | 365 |

### 5. email_verification.confirm - 确认对话框 (2个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| cancel_title | 取消验证 | Cancel Verification | 375 |
| cancel_message | 您确定要取消邮箱验证吗？\n\n取消后，您需要在验证邮箱后才能登录。 | Are you sure you want to cancel email verification?\n\nAfter cancellation, you will need to verify your email before logging in. | 376 |

### 保留的原始字符串
以下字符串是调试日志，不需要翻译：
- Line 325: `f"[EMAIL-VERIFICATION] 自动登录错误: {e}"` - 与auto_login_error_message重复
- Line 404: `f"验证成功！用户信息：{user_info}"` - 调试日志，不对用户显示

## 🔧 实施策略

### 1. 添加翻译键
- 创建 `add_email_verification_i18n_keys.py`
- 添加38个翻译键到 i18n/zh_CN.json 和 i18n/en_US.json

### 2. 自动替换
- 创建 `apply_email_verification_i18n.py`
- 使用正则表达式模式批量替换
- 处理参数化字符串（email, count, status_code, e, error）
- 处理HTML富文本字符串（保持HTML标签）

### 3. 手动修复
- 检查多行字符串拼接
- 验证HTML标签保留正确
- 确认参数化翻译正确

### 4. 验证
- 运行 `python -m py_compile gaiya/ui/email_verification_dialog.py`
- 确保所有翻译键正确引用

## 📈 预期工作量
- **翻译键添加**: 15分钟
- **自动替换**: 25分钟
- **手动修复**: 20分钟
- **验证测试**: 10分钟
- **文档编写**: 20分钟
- **总计**: 约1小时30分钟

## 🎯 质量目标
- 自动化成功率: 70%+
- 代码语法: 100%通过
- 翻译完整性: 100%覆盖
- HTML标签保留: 100% (保持<b>、<br>、<small>等标签)
- emoji保留: 100% (⏳, 💡, ✅, ⏰)

## 📝 特殊注意事项

### HTML富文本处理
该对话框使用HTML格式的富文本显示（QLabel支持）：
- 需要保留HTML标签：`<b>`, `<br>`, `<small>`
- 翻译时确保标签位置正确
- 参数化时保持HTML结构

### 多行字符串拼接
Lines 75-77, 122-125 使用字符串拼接创建HTML内容：
```python
f"我们已向 <b>{self.email}</b> 发送了一封验证邮件。<br><br>" +
"请打开您的邮箱，点击邮件中的<b>验证链接</b>完成注册。<br><br>" +
"<small>验证完成后，本窗口将自动关闭并登录。</small>"
```
这些需要手动处理或使用单个翻译键。

---

**文档创建时间**: 2025-11-23
**预期完成时间**: 2025-11-23
