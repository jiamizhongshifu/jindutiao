#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 membership_ui.py 的翻译键到 i18n 文件
"""

import json

def add_membership_keys():
    """添加membership_ui的翻译键"""

    # 定义所有翻译键（中文和英文）
    membership_keys_zh = {
        "membership": {
            # 对话框基本元素
            "not_logged_in": "未登录",
            "login_required": "请先登录后再购买会员",
            "upgrade_to_pro": "升级到专业版",
            "dialog_title": "升级 GaiYa 专业版",
            "btn_cancel": "取消",
            "btn_buy_now": "立即购买",
            "btn_activate": "立即开通",

            "plan": {
                # 套餐名称和价格
                "monthly_name": "连续包月",
                "per_month": "元/月",
                "monthly_daily_price": "¥0.97/天",
                "yearly_name": "连续包年",
                "per_year": "元/年",
                "yearly_daily_price": "¥0.55/天",
                "subscription_deal": "订阅特惠",
                "best_value": "最超值",
                "free": "免费版",
                "pro": "专业版",
                "lifetime": "终身会员"
            },

            "feature": {
                # 功能特性
                "smart_planning_50": "智能任务规划 50次/天",
                "progress_report_10": "进度报告 10次/周",
                "ai_assistant_100": "AI助手 100次/天",
                "custom_theme": "自定义主题",
                "all_pro_features": "所有专业版功能",
                "save_40": "节省40元",
                "priority_support": "优先客服支持",
                "early_access": "新功能优先体验"
            },

            "payment": {
                # 支付流程
                "select_method": "选择支付方式",
                "alipay": "支付宝",
                "wechat": "微信支付",
                "creating_order": "正在创建订单...",
                "waiting_title": "等待支付",
                "waiting_line1": "正在等待支付完成...\n\n",
                "waiting_line2": "请在打开的浏览器页面中完成支付。\n",
                "waiting_line3": "支付完成后，此窗口将自动关闭。",
                "success_title": "支付成功",
                "success_message": "支付已完成！\n您的会员权益已激活。\n\n请重新启动应用以生效。"
            },

            "error": {
                # 错误消息
                "no_plan_selected_title": "未选择套餐",
                "no_plan_selected_message": "请选择一个会员套餐",
                "order_creation_failed_title": "创建订单失败",
                "order_creation_failed": "创建订单失败：{error_msg}"
            }
        }
    }

    membership_keys_en = {
        "membership": {
            # Dialog basic elements
            "not_logged_in": "Not Logged In",
            "login_required": "Please log in before purchasing membership",
            "upgrade_to_pro": "Upgrade to Pro",
            "dialog_title": "Upgrade GaiYa Pro",
            "btn_cancel": "Cancel",
            "btn_buy_now": "Buy Now",
            "btn_activate": "Activate Now",

            "plan": {
                # Plan names and prices
                "monthly_name": "Monthly Subscription",
                "per_month": "/month",
                "monthly_daily_price": "$0.97/day",
                "yearly_name": "Annual Subscription",
                "per_year": "/year",
                "yearly_daily_price": "$0.55/day",
                "subscription_deal": "Subscription Deal",
                "best_value": "Best Value",
                "free": "Free",
                "pro": "Pro",
                "lifetime": "Lifetime"
            },

            "feature": {
                # Features
                "smart_planning_50": "Smart Planning 50/day",
                "progress_report_10": "Progress Report 10/week",
                "ai_assistant_100": "AI Assistant 100/day",
                "custom_theme": "Custom Themes",
                "all_pro_features": "All Pro Features",
                "save_40": "Save $40",
                "priority_support": "Priority Support",
                "early_access": "Early Access to New Features"
            },

            "payment": {
                # Payment process
                "select_method": "Select Payment Method",
                "alipay": "Alipay",
                "wechat": "WeChat Pay",
                "creating_order": "Creating order...",
                "waiting_title": "Waiting for Payment",
                "waiting_line1": "Waiting for payment to complete...\n\n",
                "waiting_line2": "Please complete the payment in the opened browser page.\n",
                "waiting_line3": "This window will close automatically after payment.",
                "success_title": "Payment Successful",
                "success_message": "Payment completed!\nYour membership benefits have been activated.\n\nPlease restart the application for changes to take effect."
            },

            "error": {
                # Error messages
                "no_plan_selected_title": "No Plan Selected",
                "no_plan_selected_message": "Please select a membership plan",
                "order_creation_failed_title": "Order Creation Failed",
                "order_creation_failed": "Order creation failed: {error_msg}"
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加membership命名空间
    zh_cn['membership'] = membership_keys_zh['membership']
    en_us['membership'] = membership_keys_en['membership']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计membership命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    membership_key_count = count_keys(membership_keys_zh['membership'])
    print(f"新增 membership 命名空间翻译键: {membership_key_count} 个")

if __name__ == '__main__':
    add_membership_keys()
