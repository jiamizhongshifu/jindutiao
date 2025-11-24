#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 otp_dialog.py 的翻译键到 i18n 文件
"""

import json

def add_otp_dialog_keys():
    """添加otp_dialog的翻译键"""

    # 定义所有翻译键（中文和英文）
    otp_keys_zh = {
        "otp": {
            "dialog": {
                "title": "邮箱验证",
                "sent_title": "验证您的邮箱",
                "sent_message_html": "我们已向 <b>{email}</b> 发送了一封包含6位验证码的邮件",
                "no_code_question": "没收到验证码？"
            },
            "button": {
                "verify": "验证",
                "cancel": "取消",
                "resend": "重新发送",
                "resend_countdown": "重新发送 ({countdown}s)",
                "sending": "发送中...",
                "verifying": "验证中..."
            },
            "message": {
                "send_failed_title": "发送失败",
                "send_failed_message": "发送验证码失败",
                "network_error_title": "网络错误",
                "timeout_title": "超时",
                "timeout_message": "请求超时，请稍后重试",
                "error_title": "错误",
                "send_error_message": "发送失败：{error}",
                "input_error_title": "输入错误",
                "input_error_message": "请输入完整的6位验证码",
                "verify_success_title": "验证成功",
                "verify_success_message": "邮箱验证成功！",
                "verify_failed_title": "验证失败",
                "verify_failed_message": "验证失败",
                "verify_error_message": "验证失败：{error}",
                "final_success_message": "验证成功！"
            }
        }
    }

    otp_keys_en = {
        "otp": {
            "dialog": {
                "title": "Email Verification",
                "sent_title": "Verify Your Email",
                "sent_message_html": "We have sent a 6-digit verification code to <b>{email}</b>",
                "no_code_question": "Didn't receive the code?"
            },
            "button": {
                "verify": "Verify",
                "cancel": "Cancel",
                "resend": "Resend",
                "resend_countdown": "Resend ({countdown}s)",
                "sending": "Sending...",
                "verifying": "Verifying..."
            },
            "message": {
                "send_failed_title": "Send Failed",
                "send_failed_message": "Failed to send verification code",
                "network_error_title": "Network Error",
                "timeout_title": "Timeout",
                "timeout_message": "Request timeout, please try again later",
                "error_title": "Error",
                "send_error_message": "Send failed: {error}",
                "input_error_title": "Input Error",
                "input_error_message": "Please enter the complete 6-digit verification code",
                "verify_success_title": "Verification Successful",
                "verify_success_message": "Email verification successful!",
                "verify_failed_title": "Verification Failed",
                "verify_failed_message": "Verification failed",
                "verify_error_message": "Verification failed: {error}",
                "final_success_message": "Verification successful!"
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加otp命名空间
    zh_cn['otp'] = otp_keys_zh['otp']
    en_us['otp'] = otp_keys_en['otp']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计otp命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    key_count = count_keys(otp_keys_zh['otp'])
    print(f"新增 otp 命名空间翻译键: {key_count} 个")

if __name__ == '__main__':
    add_otp_dialog_keys()
