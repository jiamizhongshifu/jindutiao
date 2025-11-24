#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply i18n to auth_ui.py - Comprehensive replacement using regex
使用正则表达式进行全面替换
"""

import re

def apply_comprehensive_replacements():
    """使用正则表达式进行全面替换"""

    with open('gaiya/ui/auth_ui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    replacements_count = 0

    # 定义所有替换规则（使用正则表达式）
    replacements = [
        # 简单字符串替换（完全匹配）
        (r'"请输入邮箱"', r'tr("auth.email_placeholder")', 'email placeholder'),
        (r'"请输入密码"', r'tr("auth.password_placeholder")', 'password placeholder'),
        (r'"至少6个字符"', r'tr("auth.password_hint")', 'password hint'),
        (r'"请再次输入密码"', r'tr("auth.confirm_password_placeholder")', 'confirm password placeholder'),
        (r'"确认密码"', r'tr("auth.confirm_password_label")', 'confirm password label'),
        (r'"记住登录状态"', r'tr("auth.signin.remember_me")', 'remember me'),
        (r'"登录"', r'tr("auth.signin.btn_login")', 'login button'),
        (r'"忘记密码？"', r'tr("auth.signin.forgot_password")', 'forgot password'),
        (r'"注册账号 >"', r'tr("auth.signup.link_to_register")', 'register link'),
        (r'"注册"', r'tr("auth.signup.btn_register")', 'register button'),
        (r'"< 返回登录"', r'tr("auth.signup.back_to_login")', 'back to login'),
        (r'"使用邮箱登录 >"', r'tr("auth.switch_to_email")', 'switch to email'),

        # 登录/注册过程中的状态消息
        (r'"登录中\.\.\."', r'tr("auth.signin.logging_in")', 'logging in'),
        (r'"注册中\.\.\."', r'tr("auth.signup.registering")', 'registering'),

        # 错误消息
        (r'"输入错误"', r'tr("auth.error.input_error")', 'input error'),
        (r'"请输入邮箱和密码"', r'tr("auth.error.empty_fields")', 'empty fields'),
        (r'"邮箱格式不正确"', r'tr("auth.error.invalid_email")', 'invalid email'),
        (r'"密码至少需要6个字符"', r'tr("auth.error.password_too_short")', 'password too short'),
        (r'"两次输入的密码不一致"', r'tr("auth.error.passwords_mismatch")', 'passwords mismatch'),
        (r'"登录失败"', r'tr("auth.error.login_failed_title")', 'login failed title'),
        (r'"注册失败"', r'tr("auth.error.register_failed_title")', 'register failed title'),
        (r'"连接失败"', r'tr("auth.error.connection_failed")', 'connection failed'),
        (r'"发送失败"', r'tr("auth.error.send_failed")', 'send failed'),
        (r'"无法生成二维码"', r'tr("auth.error.qr_code_failed")', 'QR code failed'),

        # 成功消息
        (r'"登录成功！"', r'tr("auth.signin.success")', 'login success'),
        (r'"注册成功"', r'tr("auth.signup.success_title")', 'register success title'),
        (r'"邮件已发送"', r'tr("auth.reset.email_sent_title")', 'email sent title'),

        # 微信登录
        (r'"请使用微信扫码登录"', r'tr("auth.wechat.scan_prompt")', 'wechat scan prompt'),
        (r'"等待扫码\.\.\."', r'tr("auth.wechat.waiting_scan")', 'waiting scan'),
        (r'"扫码成功，请在手机上确认\.\.\."', r'tr("auth.wechat.confirm_on_phone")', 'confirm on phone'),
        (r'"二维码已过期，正在刷新\.\.\."', r'tr("auth.wechat.qr_expired")', 'QR expired'),
        (r'"正在生成二维码\.\.\."', r'tr("auth.wechat.generating_qr")', 'generating QR'),
        (r'"微信登录功能不可用"', r'tr("auth.wechat.unavailable")', 'wechat unavailable'),
        (r'"功能不可用"', r'tr("auth.wechat.feature_unavailable")', 'feature unavailable'),

        # 密码重置
        (r'"重置密码"', r'tr("auth.reset.title")', 'reset password title'),

        # 带参数的字符串（需要使用f-string或format）
        (r'"登录失败：\{error_msg\}"', r'tr("auth.error.login_failed", error_msg=error_msg)', 'login failed with msg'),
        (r'"注册失败：\{error_msg\}"', r'tr("auth.error.register_failed", error_msg=error_msg)', 'register failed with msg'),
        (r'"发送失败：\{error_msg\}"', r'tr("auth.error.send_failed_with_msg", error_msg=error_msg)', 'send failed with msg'),
        (r'"错误: \{error_msg\}"', r'tr("auth.error.generic_error", error_msg=error_msg)', 'generic error'),
    ]

    # 应用每个替换
    for pattern, replacement, description in replacements:
        matches = re.findall(pattern, content)
        if matches:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count = len(re.findall(pattern, content))
                content = new_content
                replacements_count += count
                print(f"[OK] Replaced: {description} ({count} occurrence(s))")

    # 写回文件
    with open('gaiya/ui/auth_ui.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n[SUCCESS] Total replacements made: {replacements_count}")
    print(f"File updated: gaiya/ui/auth_ui.py")

    return replacements_count

if __name__ == '__main__':
    count = apply_comprehensive_replacements()
