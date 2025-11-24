#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 email_verification_dialog.py 的翻译键到 i18n 文件
"""

import json

def add_email_verification_keys():
    """添加email_verification_dialog的翻译键"""

    # 定义所有翻译键（中文和英文）
    email_verification_keys_zh = {
        "email_verification": {
            "dialog": {
                # 对话框UI
                "title": "验证您的邮箱",
                "sent_title": "验证邮件已发送",
                "sent_message_html": "我们已向 <b>{email}</b> 发送了一封验证邮件。<br><br>请打开您的邮箱，点击邮件中的<b>验证链接</b>完成注册。<br><br><small>验证完成后，本窗口将自动关闭并登录。</small>",
                "waiting_status": "⏳ 等待邮箱验证...",
                "tips_html": "💡 <b>小贴士：</b><br>• 请检查垃圾邮件文件夹<br>• 验证链接有效期为24小时<br>• 如果没有收到邮件，可以点击下方",
                "verified_success": "✅ 邮箱验证成功！",
                "welcome_title": "欢迎",
                "welcome_message": "欢迎！{email}\\n\\n您已成功注册并登录 GaiYa 每日进度条。"
            },

            "button": {
                # 按钮文本
                "resend": "重新发送验证邮件",
                "cancel": "取消",
                "sending": "发送中..."
            },

            "log": {
                # 日志消息
                "start_polling": "[EMAIL-VERIFICATION] 开始轮询验证状态，邮箱: {email}",
                "checking": "[EMAIL-VERIFICATION] 第{count}次检查验证状态...",
                "not_verified_yet": "[EMAIL-VERIFICATION] 尚未验证，继续等待...",
                "check_failed_http": "[EMAIL-VERIFICATION] 检查失败: HTTP {status_code}",
                "check_timeout": "[EMAIL-VERIFICATION] 检查超时，将在5秒后重试",
                "check_error": "[EMAIL-VERIFICATION] 检查错误: {e}",
                "verified_log": "[EMAIL-VERIFICATION] 验证成功！邮箱: {email}",
                "auto_login_start": "[EMAIL-VERIFICATION] 开始自动登录...",
                "auto_login_success": "[EMAIL-VERIFICATION] 自动登录成功！",
                "auto_login_error": "[EMAIL-VERIFICATION] 自动登录错误: {e}"
            },

            "message": {
                # 用户消息
                "timeout_warning": "⏰ 验证超时，请重新发送验证邮件",
                "verified_success_title": "验证成功",
                "verified_success_message": "邮箱验证成功！请使用您的邮箱和密码登录。",
                "login_failed_title": "登录失败",
                "auto_login_failed_title": "自动登录失败",
                "auto_login_failed_message": "邮箱验证成功，但自动登录失败：{error}\\n\\n请手动登录。",
                "auto_login_error_message": "邮箱验证成功，但自动登录出错：{error}\\n\\n请手动登录。",
                "resend_success_title": "发送成功",
                "resend_success_message": "验证邮件已重新发送，请查收您的邮箱。",
                "resend_failed_title": "发送失败",
                "resend_failed_message": "重新发送失败，请稍后重试",
                "resend_error_title": "错误",
                "resend_error_message": "重新发送失败：{error}"
            },

            "confirm": {
                # 确认对话框
                "cancel_title": "取消验证",
                "cancel_message": "您确定要取消邮箱验证吗？\\n\\n取消后，您需要在验证邮箱后才能登录。"
            }
        }
    }

    email_verification_keys_en = {
        "email_verification": {
            "dialog": {
                # Dialog UI
                "title": "Verify Your Email",
                "sent_title": "Verification Email Sent",
                "sent_message_html": "We have sent a verification email to <b>{email}</b>.<br><br>Please open your inbox and click the <b>verification link</b> in the email to complete registration.<br><br><small>This window will automatically close and log you in after verification.</small>",
                "waiting_status": "⏳ Waiting for email verification...",
                "tips_html": "💡 <b>Tips:</b><br>• Check your spam folder<br>• Verification link is valid for 24 hours<br>• If you didn't receive the email, click below",
                "verified_success": "✅ Email Verified Successfully!",
                "welcome_title": "Welcome",
                "welcome_message": "Welcome! {email}\\n\\nYou have successfully registered and logged into GaiYa Daily Progress Bar."
            },

            "button": {
                # Button text
                "resend": "Resend Verification Email",
                "cancel": "Cancel",
                "sending": "Sending..."
            },

            "log": {
                # Log messages
                "start_polling": "[EMAIL-VERIFICATION] Start polling verification status, email: {email}",
                "checking": "[EMAIL-VERIFICATION] Checking verification status (attempt {count})...",
                "not_verified_yet": "[EMAIL-VERIFICATION] Not verified yet, continuing to wait...",
                "check_failed_http": "[EMAIL-VERIFICATION] Check failed: HTTP {status_code}",
                "check_timeout": "[EMAIL-VERIFICATION] Check timeout, retrying in 5 seconds",
                "check_error": "[EMAIL-VERIFICATION] Check error: {e}",
                "verified_log": "[EMAIL-VERIFICATION] Verification successful! Email: {email}",
                "auto_login_start": "[EMAIL-VERIFICATION] Starting auto login...",
                "auto_login_success": "[EMAIL-VERIFICATION] Auto login successful!",
                "auto_login_error": "[EMAIL-VERIFICATION] Auto login error: {e}"
            },

            "message": {
                # User messages
                "timeout_warning": "⏰ Verification timeout, please resend verification email",
                "verified_success_title": "Verification Successful",
                "verified_success_message": "Email verification successful! Please log in with your email and password.",
                "login_failed_title": "Login Failed",
                "auto_login_failed_title": "Auto Login Failed",
                "auto_login_failed_message": "Email verification successful, but auto login failed: {error}\\n\\nPlease log in manually.",
                "auto_login_error_message": "Email verification successful, but auto login error: {error}\\n\\nPlease log in manually.",
                "resend_success_title": "Sent Successfully",
                "resend_success_message": "Verification email has been resent, please check your inbox.",
                "resend_failed_title": "Send Failed",
                "resend_failed_message": "Resend failed, please try again later",
                "resend_error_title": "Error",
                "resend_error_message": "Resend failed: {error}"
            },

            "confirm": {
                # Confirmation dialogs
                "cancel_title": "Cancel Verification",
                "cancel_message": "Are you sure you want to cancel email verification?\\n\\nAfter cancellation, you will need to verify your email before logging in."
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加email_verification命名空间
    zh_cn['email_verification'] = email_verification_keys_zh['email_verification']
    en_us['email_verification'] = email_verification_keys_en['email_verification']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计email_verification命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    key_count = count_keys(email_verification_keys_zh['email_verification'])
    print(f"新增 email_verification 命名空间翻译键: {key_count} 个")

if __name__ == '__main__':
    add_email_verification_keys()
