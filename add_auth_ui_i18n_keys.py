#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 auth_ui.py 的翻译键到 i18n 文件
"""

import json

def add_auth_ui_keys():
    """添加auth_ui的翻译键"""

    # 定义所有翻译键（中文和英文）
    auth_keys_zh = {
        "auth": {
            # 通用认证文本
            "window_title": "GaiYa - 账户登录",
            "welcome": "欢迎使用 GaiYa",
            "subtitle": "每日进度条 - 让时间可视化",
            "terms_notice": "注册即表示同意服务条款和隐私政策",
            "email_label": "邮箱地址",
            "email_placeholder": "请输入邮箱",
            "password_label": "密码",
            "password_placeholder": "请输入密码",
            "confirm_password_label": "确认密码",
            "confirm_password_placeholder": "请再次输入密码",
            "password_hint": "至少6个字符",
            "switch_to_email": "使用邮箱登录 >",

            "signin": {
                "btn_login": "登录",
                "remember_me": "记住登录状态",
                "forgot_password": "忘记密码？",
                "logging_in": "登录中...",
                "success": "登录成功！",
                "success_with_info": "登录成功！用户信息: {user_info}"
            },

            "signup": {
                "btn_register": "注册",
                "link_to_register": "注册账号 >",
                "back_to_login": "< 返回登录",
                "registering": "注册中...",
                "success_title": "注册成功",
                "success_message": "您的账号已创建，验证邮件已发送。\n\n请验证邮箱后登录。如果没有收到邮件，请检查垃圾邮件文件夹。",
                "browser_register_title": "浏览器注册",
                "browser_register_message": "已在浏览器中打开注册页面。\n\n请完成注册后，返回客户端使用\"邮箱登录\"标签页登录。"
            },

            "error": {
                "input_error": "输入错误",
                "empty_fields": "请输入邮箱和密码",
                "invalid_email": "邮箱格式不正确",
                "password_too_short": "密码至少需要6个字符",
                "passwords_mismatch": "两次输入的密码不一致",
                "login_failed_title": "登录失败",
                "login_failed": "登录失败：{error_msg}",
                "register_failed_title": "注册失败",
                "register_failed": "注册失败：{error_msg}",
                "connection_failed": "连接失败",
                "ssl_error_intro": "客户端无法连接到服务器（SSL问题）\n\n",
                "technical_details": "技术详情：{error_msg}\n\n",
                "solutions_intro": "可能的解决方案：\n",
                "solution_check_network": "1. 检查网络连接是否正常\n",
                "solution_no_proxy": "2. 确认没有使用代理或VPN\n",
                "solution_disable_firewall": "3. 暂时关闭防火墙/安全软件重试\n",
                "solution_update_windows": "4. 更新Windows系统到最新版本\n\n",
                "contact_support": "如果问题持续，请联系技术支持。",
                "browser_fallback_prompt": "是否使用浏览器完成注册？\n（注册成功后，您可以返回客户端登录）",
                "send_failed": "发送失败",
                "send_failed_with_msg": "发送失败：{error_msg}",
                "qr_code_failed": "无法生成二维码",
                "generic_error": "错误: {error_msg}",
                "exception_error": "错误: {e}",
                "status_check_failed": "检查状态失败: {e}"
            },

            "wechat": {
                "unavailable": "微信登录功能不可用",
                "no_webengine": "当前版本未包含 WebEngine 模块\n请使用邮箱登录",
                "scan_prompt": "请使用微信扫码登录",
                "waiting_scan": "等待扫码...",
                "confirm_on_phone": "扫码成功，请在手机上确认...",
                "qr_expired": "二维码已过期，正在刷新...",
                "generating_qr": "正在生成二维码...",
                "feature_unavailable": "功能不可用",
                "webengine_required": "微信登录功能需要 WebEngine 模块支持。\n\n当前版本为了减小体积已移除该模块。\n请使用邮箱登录方式。"
            },

            "reset": {
                "title": "重置密码",
                "prompt": "请输入您的注册邮箱，我们将发送重置密码的邮件：",
                "email_sent_title": "邮件已发送",
                "email_sent_message": "重置密码的邮件已发送到 {email}，请查收。"
            }
        }
    }

    auth_keys_en = {
        "auth": {
            # General authentication text
            "window_title": "GaiYa - Account Login",
            "welcome": "Welcome to GaiYa",
            "subtitle": "Daily Progress Bar - Visualize Your Time",
            "terms_notice": "By registering, you agree to the Terms of Service and Privacy Policy",
            "email_label": "Email Address",
            "email_placeholder": "Enter your email",
            "password_label": "Password",
            "password_placeholder": "Enter your password",
            "confirm_password_label": "Confirm Password",
            "confirm_password_placeholder": "Re-enter your password",
            "password_hint": "At least 6 characters",
            "switch_to_email": "Use Email Login >",

            "signin": {
                "btn_login": "Login",
                "remember_me": "Remember me",
                "forgot_password": "Forgot password?",
                "logging_in": "Logging in...",
                "success": "Login successful!",
                "success_with_info": "Login successful! User info: {user_info}"
            },

            "signup": {
                "btn_register": "Register",
                "link_to_register": "Create Account >",
                "back_to_login": "< Back to Login",
                "registering": "Registering...",
                "success_title": "Registration Successful",
                "success_message": "Your account has been created and a verification email has been sent.\n\nPlease verify your email before logging in. If you don't receive the email, please check your spam folder.",
                "browser_register_title": "Browser Registration",
                "browser_register_message": "Registration page has been opened in your browser.\n\nAfter completing registration, please return to the client and use the \"Email Login\" tab to sign in."
            },

            "error": {
                "input_error": "Input Error",
                "empty_fields": "Please enter email and password",
                "invalid_email": "Invalid email format",
                "password_too_short": "Password must be at least 6 characters",
                "passwords_mismatch": "Passwords do not match",
                "login_failed_title": "Login Failed",
                "login_failed": "Login failed: {error_msg}",
                "register_failed_title": "Registration Failed",
                "register_failed": "Registration failed: {error_msg}",
                "connection_failed": "Connection Failed",
                "ssl_error_intro": "Client cannot connect to server (SSL issue)\n\n",
                "technical_details": "Technical details: {error_msg}\n\n",
                "solutions_intro": "Possible solutions:\n",
                "solution_check_network": "1. Check your network connection\n",
                "solution_no_proxy": "2. Ensure no proxy or VPN is active\n",
                "solution_disable_firewall": "3. Temporarily disable firewall/security software\n",
                "solution_update_windows": "4. Update Windows to the latest version\n\n",
                "contact_support": "If the problem persists, please contact technical support.",
                "browser_fallback_prompt": "Would you like to complete registration using your browser?\n(After successful registration, you can return to the client to log in)",
                "send_failed": "Send Failed",
                "send_failed_with_msg": "Send failed: {error_msg}",
                "qr_code_failed": "Failed to generate QR code",
                "generic_error": "Error: {error_msg}",
                "exception_error": "Error: {e}",
                "status_check_failed": "Status check failed: {e}"
            },

            "wechat": {
                "unavailable": "WeChat Login Unavailable",
                "no_webengine": "WebEngine module not included in current version\nPlease use email login",
                "scan_prompt": "Please scan with WeChat to login",
                "waiting_scan": "Waiting for scan...",
                "confirm_on_phone": "Scan successful, please confirm on your phone...",
                "qr_expired": "QR code expired, refreshing...",
                "generating_qr": "Generating QR code...",
                "feature_unavailable": "Feature Unavailable",
                "webengine_required": "WeChat login requires WebEngine module support.\n\nThis module has been removed in the current version to reduce size.\nPlease use email login instead."
            },

            "reset": {
                "title": "Reset Password",
                "prompt": "Please enter your registered email address, and we will send a password reset email:",
                "email_sent_title": "Email Sent",
                "email_sent_message": "A password reset email has been sent to {email}. Please check your inbox."
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加auth命名空间
    zh_cn['auth'] = auth_keys_zh['auth']
    en_us['auth'] = auth_keys_en['auth']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计auth命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    auth_key_count = count_keys(auth_keys_zh['auth'])
    print(f"新增 auth 命名空间翻译键: {auth_key_count} 个")

if __name__ == '__main__':
    add_auth_ui_keys()
