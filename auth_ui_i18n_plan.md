# auth_ui.py 国际化方案

## 文件信息
- **文件**: gaiya/ui/auth_ui.py
- **行数**: 804行
- **中文字符串**: 101个
- **功能**: 登录/注册对话框

## 字符串分类统计

### 总体统计
- **原始字符串**: 101个
- **去重后**: 约70个唯一翻译键
- **重复字符串**: 约31个

### 分类详情

#### 1. 通用认证文本 (auth命名空间)
- 窗口标题、欢迎语、副标题
- 表单字段标签（邮箱、密码）
- 占位符文本
- 底部说明文本

#### 2. 登录功能 (auth.signin子空间)
- 登录按钮
- 记住登录状态
- 忘记密码链接
- 登录状态提示

#### 3. 注册功能 (auth.signup子空间)
- 注册按钮
- 密码确认字段
- 注册成功消息
- 返回登录链接

#### 4. 错误消息 (auth.error子空间)
- 输入验证错误（邮箱格式、密码长度、密码不一致）
- 登录失败
- 注册失败
- 连接失败（SSL问题）
- 网络错误

#### 5. 成功消息 (auth.success子空间)
- 登录成功
- 注册成功
- 邮件发送成功

#### 6. 微信登录 (auth.wechat子空间)
- 微信登录提示
- 扫码状态
- 切换到邮箱登录

#### 7. 密码重置 (auth.reset子空间)
- 重置密码对话框
- 邮件发送提示

## 翻译键规划

### auth - 通用认证文本 (15个)

| 原文 | 翻译键 | 使用次数 |
|------|--------|---------|
| GaiYa - 账户登录 | auth.window_title | 1 |
| 欢迎使用 GaiYa | auth.welcome | 1 |
| 每日进度条 - 让时间可视化 | auth.subtitle | 1 |
| 注册即表示同意服务条款和隐私政策 | auth.terms_notice | 1 |
| 邮箱地址 | auth.email_label | 2 |
| 请输入邮箱 | auth.email_placeholder | 2 |
| 密码 | auth.password_label | 2 |
| 请输入密码 | auth.password_placeholder | 2 |
| 确认密码 | auth.confirm_password_label | 1 |
| 请再次输入密码 | auth.confirm_password_placeholder | 1 |
| 至少6个字符 | auth.password_hint | 1 |
| 使用邮箱登录 > | auth.switch_to_email | 2 |

### auth.signin - 登录功能 (6个)

| 原文 | 翻译键 |
|------|--------|
| 登录 | auth.signin.btn_login |
| 记住登录状态 | auth.signin.remember_me |
| 忘记密码？ | auth.signin.forgot_password |
| 登录中... | auth.signin.logging_in |
| 登录成功！ | auth.signin.success |
| 登录成功！用户信息: {user_info} | auth.signin.success_with_info |

### auth.signup - 注册功能 (7个)

| 原文 | 翻译键 |
|------|--------|
| 注册 | auth.signup.btn_register |
| 注册账号 > | auth.signup.link_to_register |
| < 返回登录 | auth.signup.back_to_login |
| 注册中... | auth.signup.registering |
| 注册成功 | auth.signup.success_title |
| 您的账号已创建，验证邮件已发送。\n\n请验证邮箱后登录。如果没有收到邮件，请检查垃圾邮件文件夹。 | auth.signup.success_message |
| 浏览器注册 | auth.signup.browser_register_title |
| 已在浏览器中打开注册页面。\n\n请完成注册后，返回客户端使用\标签页登录。 | auth.signup.browser_register_message |

### auth.error - 错误消息 (20个)

| 原文 | 翻译键 |
|------|--------|
| 输入错误 | auth.error.input_error |
| 请输入邮箱和密码 | auth.error.empty_fields |
| 邮箱格式不正确 | auth.error.invalid_email |
| 密码至少需要6个字符 | auth.error.password_too_short |
| 两次输入的密码不一致 | auth.error.passwords_mismatch |
| 登录失败 | auth.error.login_failed_title |
| 登录失败：{error_msg} | auth.error.login_failed |
| 注册失败 | auth.error.register_failed_title |
| 注册失败：{error_msg} | auth.error.register_failed |
| 连接失败 | auth.error.connection_failed |
| 客户端无法连接到服务器（SSL问题）\n\n | auth.error.ssl_error_intro |
| 技术详情：{error_msg}\n\n | auth.error.technical_details |
| 可能的解决方案：\n | auth.error.solutions_intro |
| 1. 检查网络连接是否正常\n | auth.error.solution_check_network |
| 2. 确认没有使用代理或VPN\n | auth.error.solution_no_proxy |
| 3. 暂时关闭防火墙/安全软件重试\n | auth.error.solution_disable_firewall |
| 4. 更新Windows系统到最新版本\n\n | auth.error.solution_update_windows |
| 如果问题持续，请联系技术支持。 | auth.error.contact_support |
| 是否使用浏览器完成注册？\n（注册成功后，您可以返回客户端登录） | auth.error.browser_fallback_prompt |
| 发送失败 | auth.error.send_failed |
| 发送失败：{error_msg} | auth.error.send_failed_with_msg |
| 无法生成二维码 | auth.error.qr_code_failed |
| 错误: {error_msg} | auth.error.generic_error |
| 错误: {str(e)} | auth.error.exception_error |
| 检查状态失败: {str(e)} | auth.error.status_check_failed |

### auth.wechat - 微信登录 (11个)

| 原文 | 翻译键 |
|------|--------|
| 微信登录功能不可用 | auth.wechat.unavailable |
| 当前版本未包含 WebEngine 模块\n请使用邮箱登录 | auth.wechat.no_webengine |
| 请使用微信扫码登录 | auth.wechat.scan_prompt |
| 等待扫码... | auth.wechat.waiting_scan |
| 扫码成功，请在手机上确认... | auth.wechat.confirm_on_phone |
| 二维码已过期，正在刷新... | auth.wechat.qr_expired |
| 正在生成二维码... | auth.wechat.generating_qr |
| 功能不可用 | auth.wechat.feature_unavailable |
| 微信登录功能需要 WebEngine 模块支持。\n\n当前版本为了减小体积已移除该模块。\n请使用邮箱登录方式。 | auth.wechat.webengine_required |

### auth.reset - 密码重置 (4个)

| 原文 | 翻译键 |
|------|--------|
| 重置密码 | auth.reset.title |
| 请输入您的注册邮箱，我们将发送重置密码的邮件： | auth.reset.prompt |
| 邮件已发送 | auth.reset.email_sent_title |
| 重置密码的邮件已发送到 {email}，请查收。 | auth.reset.email_sent_message |

### 日志消息（不翻译，保持英文）
以下日志消息保持英文，不需要翻译：
- `[AUTH-UI] 邮箱验证成功，用户信息: {user_info}`
- `[AUTH-UI] WebEngine 不可用，自动切换到邮箱登录`
- `[AUTH-UI] 延迟创建微信登录widget（QWebEngineView）...`
- `[AUTH-UI] 微信登录widget创建完成`

## 翻译键总结

### 命名空间统计
| 命名空间 | 翻译键数 | 主要用途 |
|---------|---------|---------|
| auth | 15 | 通用认证文本 |
| auth.signin | 6 | 登录功能 |
| auth.signup | 7 | 注册功能 |
| auth.error | 20 | 错误消息 |
| auth.wechat | 11 | 微信登录 |
| auth.reset | 4 | 密码重置 |
| **总计** | **63** | - |

## 参数化翻译

需要参数的翻译键：
1. `auth.error.technical_details`: `{error_msg}`
2. `auth.error.login_failed`: `{error_msg}`
3. `auth.error.register_failed`: `{error_msg}`
4. `auth.error.send_failed_with_msg`: `{error_msg}`
5. `auth.error.generic_error`: `{error_msg}`
6. `auth.error.exception_error`: `{e}`
7. `auth.error.status_check_failed`: `{e}`
8. `auth.reset.email_sent_message`: `{email}`
9. `auth.signin.success_with_info`: `{user_info}` (日志，不翻译)

## 实施建议

### 分阶段实施
由于字符串数量较多（63个），建议分3个阶段：

#### 第一阶段：核心UI文本 (15个)
- auth命名空间的所有键
- 预计工作量：30分钟

#### 第二阶段：登录和注册 (13个)
- auth.signin命名空间
- auth.signup命名空间
- 预计工作量：30分钟

#### 第三阶段：错误处理和其他 (35个)
- auth.error命名空间
- auth.wechat命名空间
- auth.reset命名空间
- 预计工作量：1-1.5小时

### 总预计工作量
- **翻译键添加**: 30分钟
- **代码自动替换**: 30分钟
- **手动修复**: 1小时
- **验证和测试**: 30分钟
- **总计**: 2.5-3小时

## 复杂度评估

### 自动化难度
- **简单替换**: 约40个（单行字符串，无复杂逻辑）
- **中等难度**: 约15个（多行字符串，需要拼接）
- **手动处理**: 约8个（复杂的错误消息组合）

### 预计自动化成功率
约70-75%（基于ConfigManager经验）

## 修改文件清单

- `gaiya/ui/auth_ui.py`: 约63处修改
- `i18n/zh_CN.json`: 添加63个键
- `i18n/en_US.json`: 添加63个键
