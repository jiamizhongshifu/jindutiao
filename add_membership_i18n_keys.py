#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add membership UI i18n keys to translation files
"""

import json

def add_membership_keys():
    """Add membership translation keys"""

    # Membership keys - Chinese
    membership_keys_zh = {
        "membership": {
            # Table headers
            "table_headers": {
                "feature": "功能特性",
                "free": "免费版",
                "monthly": "Pro 月度",
                "yearly": "Pro 年度",
                "lifetime": "会员合伙人"
            },
            # Group titles
            "groups": {
                "core_features": "【核心功能】",
                "advanced_features": "【高级功能】",
                "benefits": "【会员权益】"
            },
            # Feature names
            "features": {
                "daily_progress_bar": "每日进度条显示",
                "ai_task_planning": "AI 智能任务规划",
                "stats_report": "统计报告分析",
                "theme_customization": "主题自定义",
                "pomodoro": "番茄时钟",
                "cloud_sync": "数据云同步",
                "scene_system": "场景系统",
                "early_access": "抢先体验新功能",
                "vip_group": "加入VIP会员群",
                "validity_period": "有效期",
                "referral_commission": "引荐返现比例",
                "exclusive_community": "专属合伙人社群",
                "consultation_service": "1v1咨询服务"
            },
            # Feature values
            "values": {
                "with_watermark": "✓ 带水印",
                "no_watermark": "✓ 无水印",
                "times_per_day": "{count}次/天",
                "days": "{count}天",
                "permanent": "永久",
                "checkmark": "✓",
                "cross": "✗",
                "dash": "-",
                "percent": "{value}%"
            },
            # UI labels
            "ui": {
                "upgrade_member": "升级会员",
                "become_partner": "成为合伙人",
                "login_required": "需要登录",
                "login_benefits": "登录后您将享有：",
                "member_tips": "💡 会员提示",
                "comparison_title": "💎 会员方案详细对比",
                "per_month": "/月",
                "per_year": "/年",
                "limited_offer": "限量1000名",
                "one_time_payment": "一次付费",
                "lifetime_access": "终身可用",
                "logout_success": "退出成功",
                "account_updated": "您的账户信息已更新。"
            },
            # Payment related
            "payment": {
                "select_method": "选择支付方式",
                "select_prompt": "请选择支付方式：",
                "wechat_pay": "💚 微信支付",
                "cancel": "取消",
                "confirm_payment": "确认支付",
                "waiting_payment": "等待支付",
                "create_order_failed": "创建订单失败",
                "channel": "渠道",
                "possible_reasons": "可能的原因：",
                "suggested_actions": "建议操作：",
                "debug_info": "调试信息：",
                "error": "错误",
                "payment_window_opened": "支付窗口已打开",
                "create_session_failed": "创建支付会话失败",
                "payment_exception": "支付异常",
                "check_payment_status": "检查支付状态",
                "payment_success": "支付成功",
                "stop_polling": "停止支付状态轮询"
            }
        }
    }

    # Membership keys - English
    membership_keys_en = {
        "membership": {
            # Table headers
            "table_headers": {
                "feature": "Features",
                "free": "Free",
                "monthly": "Pro Monthly",
                "yearly": "Pro Yearly",
                "lifetime": "Partner"
            },
            # Group titles
            "groups": {
                "core_features": "【Core Features】",
                "advanced_features": "【Advanced Features】",
                "benefits": "【Member Benefits】"
            },
            # Feature names
            "features": {
                "daily_progress_bar": "Daily Progress Bar",
                "ai_task_planning": "AI Task Planning",
                "stats_report": "Statistics & Reports",
                "theme_customization": "Theme Customization",
                "pomodoro": "Pomodoro Timer",
                "cloud_sync": "Cloud Sync",
                "scene_system": "Scene System",
                "early_access": "Early Access to New Features",
                "vip_group": "VIP Member Group",
                "validity_period": "Validity Period",
                "referral_commission": "Referral Commission",
                "exclusive_community": "Exclusive Partner Community",
                "consultation_service": "1-on-1 Consultation"
            },
            # Feature values
            "values": {
                "with_watermark": "✓ With Watermark",
                "no_watermark": "✓ No Watermark",
                "times_per_day": "{count} times/day",
                "days": "{count} days",
                "permanent": "Permanent",
                "checkmark": "✓",
                "cross": "✗",
                "dash": "-",
                "percent": "{value}%"
            },
            # UI labels
            "ui": {
                "upgrade_member": "Upgrade Membership",
                "become_partner": "Become Partner",
                "login_required": "Login Required",
                "login_benefits": "After login, you will enjoy:",
                "member_tips": "💡 Member Tips",
                "comparison_title": "💎 Membership Plan Comparison",
                "per_month": "/month",
                "per_year": "/year",
                "limited_offer": "Limited to 1000",
                "one_time_payment": "One-time Payment",
                "lifetime_access": "Lifetime Access",
                "logout_success": "Logout Successful",
                "account_updated": "Your account information has been updated."
            },
            # Payment related
            "payment": {
                "select_method": "Select Payment Method",
                "select_prompt": "Please select payment method:",
                "wechat_pay": "💚 WeChat Pay",
                "cancel": "Cancel",
                "confirm_payment": "Confirm Payment",
                "waiting_payment": "Waiting for Payment",
                "create_order_failed": "Failed to Create Order",
                "channel": "Channel",
                "possible_reasons": "Possible reasons:",
                "suggested_actions": "Suggested actions:",
                "debug_info": "Debug info:",
                "error": "Error",
                "payment_window_opened": "Payment window opened",
                "create_session_failed": "Failed to create payment session",
                "payment_exception": "Payment Exception",
                "check_payment_status": "Check Payment Status",
                "payment_success": "Payment Successful",
                "stop_polling": "Stop payment status polling"
            }
        }
    }

    # Read existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Add membership keys
    zh_cn['membership'] = membership_keys_zh['membership']
    en_us['membership'] = membership_keys_en['membership']

    # Write back files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Membership translation keys added!")

    # Count keys
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    total_keys = count_keys(membership_keys_zh['membership'])
    print(f"Total new keys: {total_keys}")

if __name__ == '__main__':
    add_membership_keys()
