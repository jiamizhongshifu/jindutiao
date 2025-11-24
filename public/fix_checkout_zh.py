import json

# Read current zh_CN.json
with open('locales/zh_CN.json', 'r', encoding='utf-8') as f:
    zh = json.load(f)

# Update checkout section with Chinese translations
zh['checkout'] = {
    "step_select_plan": "选择套餐",
    "step_login": "登录账户",
    "step_payment": "支付",
    "login_or_register": "登录或注册",
    "email_label": "邮箱地址 *",
    "email_placeholder": "请输入邮箱地址",
    "password_label": "密码 *",
    "password_placeholder": "请输入密码（新用户将自动注册）",
    "agree_terms_prefix": "我已阅读并同意",
    "terms_of_service": "《用户协议》",
    "and": "和",
    "privacy_policy": "《隐私政策》",
    "email_verification_notice": "💡 新用户注册后需验证邮箱，验证链接将发送至您的邮箱",
    "login_button": "登录/注册并继续支付",
    "choose_payment_method": "选择支付方式",
    "wechat_pay": "💚 微信支付（推荐）",
    "wechat_pay_desc": "扫码支付，安全便捷",
    "stripe_pay": "💳 Stripe 国际支付",
    "stripe_coming_soon": "⏳ 准备中，即将上线...",
    "stripe_cards_supported": "支持Visa/Mastercard等国际信用卡",
    "payment_success_tip": "💡 <strong>提示：</strong>支付成功后，会员权益将自动激活，重启应用即可使用",
    "order_summary": "订单摘要",
    "plan": "套餐",
    "validity": "有效期",
    "feature_ai_planning": "✓ 20次/天 AI智能规划",
    "feature_no_watermark": "✓ 去除进度条水印",
    "feature_analytics": "✓ 统计报告分析",
    "feature_cloud_sync": "✓ 数据云同步",
    "feature_scenes": "✓ 场景系统",
    "feature_vip_group": "✓ 加入VIP会员群",
    "total": "总计",
    "no_auto_renewal": "到期后不会自动续费",
    "security_title": "🔒 <strong>安全保障</strong>",
    "security_encryption": "• 所有支付信息经过加密传输",
    "security_refund": "• 7天内未使用可全额退款",
    "security_privacy": "• 完整的隐私保护承诺",
    "need_help": "需要帮助？",
    "view_help_center": "查看帮助中心",
    "plan_pro_monthly": "Pro 月度",
    "plan_pro_yearly": "Pro 年度",
    "plan_lifetime": "终身伙伴",
    "validity_30days": "30天",
    "validity_365days": "365天",
    "validity_forever": "永久"
}

# Save updated file
with open('locales/zh_CN.json', 'w', encoding='utf-8') as f:
    json.dump(zh, f, ensure_ascii=False, indent=2)

print('Checkout section updated with 44 Chinese translations')
print('File saved successfully')
