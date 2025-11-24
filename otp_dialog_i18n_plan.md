# otp_dialog.py 国际化规划文档

## 📅 创建时间
2025-11-23

## 📊 字符串统计
- **原始字符串数**: 33个
- **唯一字符串数**: 25个
- **规划翻译键**: 22个

## 🗂️ 命名空间设计

### 命名空间结构
```
otp
├── dialog            # 对话框UI (4个)
├── button            # 按钮文本 (6个)
└── message           # 用户消息 (12个)
```

## 📋 详细翻译键列表

### 1. otp.dialog - 对话框UI (4个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| title | 邮箱验证 | Email Verification | 45 |
| sent_title | 验证您的邮箱 | Verify Your Email | 63 |
| sent_message_html | 我们已向 <b>{email}</b> 发送了一封包含6位验证码的邮件 | We have sent a 6-digit verification code to <b>{email}</b> | 72 |
| no_code_question | 没收到验证码？ | Didn't receive the code? | 117 |

### 2. otp.button - 按钮文本 (6个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| verify | 验证 | Verify | 144, 313 |
| cancel | 取消 | Cancel | 169 |
| resend | 重新发送 | Resend | 120(初始), 225, 233, 238, 242, 253(倒计时结束) |
| resend_countdown | 重新发送 ({countdown}s) | Resend ({countdown}s) | 120, 249 |
| sending | 发送中... | Sending... | 199 |
| verifying | 验证中... | Verifying... | 266 |

### 3. otp.message - 用户消息 (12个)
| 翻译键 | 中文 | 英文 | 行号 |
|--------|------|------|------|
| send_failed_title | 发送失败 | Send Failed | 221 |
| send_failed_message | 发送验证码失败 | Failed to send verification code | 222 |
| network_error_title | 网络错误 | Network Error | 229, 304 |
| timeout_title | 超时 | Timeout | 236 |
| timeout_message | 请求超时，请稍后重试 | Request timeout, please try again later | 236 |
| error_title | 错误 | Error | 240, 309 |
| send_error_message | 发送失败：{error} | Send failed: {error} | 240 |
| input_error_title | 输入错误 | Input Error | 261 |
| input_error_message | 请输入完整的6位验证码 | Please enter the complete 6-digit verification code | 261 |
| verify_success_title | 验证成功 | Verification Successful | 284 |
| verify_success_message | 邮箱验证成功！ | Email verification successful! | 285 |
| verify_failed_title | 验证失败 | Verification Failed | 294 |
| verify_failed_message | 验证失败 | Verification failed | 295 |
| verify_error_message | 验证失败：{error} | Verification failed: {error} | 309 |
| final_success_message | 验证成功！ | Verification successful! | 325 |

注意：部分标题重复使用同一个翻译键（如 error_title, network_error_title）

## 🔧 实施策略

### 1. 添加翻译键
- 创建 `add_otp_dialog_i18n_keys.py`
- 添加22个翻译键到 i18n/zh_CN.json 和 i18n/en_US.json

### 2. 自动替换
- 创建 `apply_otp_dialog_i18n.py`
- 使用正则表达式批量替换
- 处理参数化字符串（email, countdown, error）
- 处理HTML富文本（保持`<b>`标签）

### 3. 手动修复
- 检查倒计时逻辑
- 验证按钮状态切换
- 确认参数化翻译正确

### 4. 验证
- 运行 `python -m py_compile gaiya/ui/otp_dialog.py`
- 确保所有翻译键正确引用

## 📈 预期工作量
- **翻译键添加**: 10分钟
- **自动替换**: 15分钟
- **手动修复**: 15分钟
- **验证测试**: 5分钟
- **文档编写**: 10分钟
- **总计**: 约55分钟

## 🎯 质量目标
- 自动化成功率: 60%+
- 代码语法: 100%通过
- 翻译完整性: 100%覆盖
- HTML标签保留: 100%
- 倒计时逻辑: 正确处理

## 📝 特殊注意事项

### HTML富文本
- Line 72: 包含 `<b>` 标签的邮件地址显示
- 需要保留HTML结构，参数化email

### 倒计时逻辑
- Lines 120, 249: 动态倒计时文本 "重新发送 ({countdown}s)"
- 需要正确处理countdown参数

### 按钮状态切换
- 发送中 → 重新发送
- 验证 → 验证中...
- 需要确保所有状态文本都已翻译

### 重复文本处理
- "重新发送" 出现在多处，统一使用 `otp.button.resend`
- "错误" 作为标题，统一使用 `otp.message.error_title`
- "网络错误" 统一使用 `otp.message.network_error_title`

---

**文档创建时间**: 2025-11-23
**预期完成时间**: 2025-11-23
