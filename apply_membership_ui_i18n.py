#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply i18n replacements to membership_ui.py using regex patterns
Based on successful auth_ui approach
"""

import re

def apply_replacements():
    """Apply all i18n replacements"""

    file_path = 'gaiya/ui/membership_ui.py'

    # Read original file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Regex-based replacements (pattern, replacement, description)
    replacements = [
        # Basic dialog elements
        (r'"未登录"', r'tr("membership.not_logged_in")', 'not logged in'),
        (r'"请先登录后再购买会员"', r'tr("membership.login_required")', 'login required'),
        (r'"升级到专业版"', r'tr("membership.upgrade_to_pro")', 'upgrade to pro'),
        (r'"升级 GaiYa 专业版"', r'tr("membership.dialog_title")', 'dialog title'),
        (r'"取消"', r'tr("membership.btn_cancel")', 'cancel button'),
        (r'"立即购买"', r'tr("membership.btn_buy_now")', 'buy now button'),
        (r'"立即开通"', r'tr("membership.btn_activate")', 'activate button'),

        # Plan names and prices
        (r'"连续包月"', r'tr("membership.plan.monthly_name")', 'monthly plan name'),
        (r'"元/月"', r'tr("membership.plan.per_month")', 'per month unit'),
        (r'"¥0\.97/天"', r'tr("membership.plan.monthly_daily_price")', 'monthly daily price'),
        (r'"连续包年"', r'tr("membership.plan.yearly_name")', 'yearly plan name'),
        (r'"元/年"', r'tr("membership.plan.per_year")', 'per year unit'),
        (r'"¥0\.55/天"', r'tr("membership.plan.yearly_daily_price")', 'yearly daily price'),
        (r'"订阅特惠"', r'tr("membership.plan.subscription_deal")', 'subscription deal'),
        (r'"最超值"', r'tr("membership.plan.best_value")', 'best value'),

        # Features
        (r'"智能任务规划 50次/天"', r'tr("membership.feature.smart_planning_50")', 'smart planning feature'),
        (r'"进度报告 10次/周"', r'tr("membership.feature.progress_report_10")', 'progress report feature'),
        (r'"AI助手 100次/天"', r'tr("membership.feature.ai_assistant_100")', 'ai assistant feature'),
        (r'"自定义主题"', r'tr("membership.feature.custom_theme")', 'custom theme feature'),
        (r'"所有专业版功能"', r'tr("membership.feature.all_pro_features")', 'all pro features'),
        (r'"节省40元"', r'tr("membership.feature.save_40")', 'save 40 yuan'),
        (r'"优先客服支持"', r'tr("membership.feature.priority_support")', 'priority support'),
        (r'"新功能优先体验"', r'tr("membership.feature.early_access")', 'early access'),

        # Payment method
        (r'"选择支付方式"', r'tr("membership.payment.select_method")', 'select payment method'),
        (r'"支付宝"', r'tr("membership.payment.alipay")', 'alipay'),
        (r'"微信支付"', r'tr("membership.payment.wechat")', 'wechat pay'),
        (r'"正在创建订单\.\.\."', r'tr("membership.payment.creating_order")', 'creating order'),
        (r'"等待支付"', r'tr("membership.payment.waiting_title")', 'waiting for payment title'),

        # Payment waiting message (multi-line)
        (r'"正在等待支付完成\.\.\.\\n\\n"', r'tr("membership.payment.waiting_line1")', 'waiting line 1'),
        (r'"请在打开的浏览器页面中完成支付。\\n"', r'tr("membership.payment.waiting_line2")', 'waiting line 2'),
        (r'"支付完成后，此窗口将自动关闭。"', r'tr("membership.payment.waiting_line3")', 'waiting line 3'),

        # Payment success
        (r'"支付成功"', r'tr("membership.payment.success_title")', 'payment success title'),
        (r'"支付已完成！\\n您的会员权益已激活。\\n\\n请重新启动应用以生效。"',
         r'tr("membership.payment.success_message")', 'payment success message'),

        # Tier names in _get_tier_name method
        (r'"免费版"', r'tr("membership.plan.free")', 'free tier'),
        (r'"专业版"', r'tr("membership.plan.pro")', 'pro tier'),
        (r'"终身会员"', r'tr("membership.plan.lifetime")', 'lifetime tier'),

        # Error messages
        (r'"未选择套餐"', r'tr("membership.error.no_plan_selected_title")', 'no plan selected title'),
        (r'"请选择一个会员套餐"', r'tr("membership.error.no_plan_selected_message")', 'no plan selected message'),
        (r'"创建订单失败"', r'tr("membership.error.order_creation_failed_title")', 'order creation failed title'),
        (r'f"创建订单失败：\{error_msg\}"',
         r'tr("membership.error.order_creation_failed", error_msg=error_msg)', 'order creation failed with msg'),
    ]

    # Apply each replacement
    total_replaced = 0
    for pattern, replacement, description in replacements:
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            total_replaced += count
            print(f"[OK] Replaced: {description} ({count} occurrence(s))")
        else:
            print(f"[SKIP] Not found: {description}")

    # Check if content changed
    if content == original_content:
        print("\n[WARNING] No changes made to file!")
        return

    # Write modified content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n[SUCCESS] Total replacements: {total_replaced}")
    print(f"Modified file: {file_path}")

if __name__ == '__main__':
    apply_replacements()
