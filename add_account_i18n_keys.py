#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add missing account i18n keys"""
import json

# New keys to add
new_keys_zh = {
    "account": {
        "plan_monthly_name": "Pro 月度",
        "plan_yearly_name": "Pro 年度",
        "plan_lifetime_name": "会员合伙人",
        "plan_period_month": "/月",
        "plan_period_year": "/年",
        "plan_validity_30days": "有效期30天",
        "plan_validity_365days": "有效期365天",
        "plan_validity_lifetime": "永久有效",
        "plan_no_auto_renewal": "到期后不会自动扣费",
        "plan_one_time_payment": "一次购买,终身可用",
        "plan_save_40_percent": "节省 40%",
        "plan_limited_to_100": "imited to 100",
        "comparison_table_features": "功能特性",
        "comparison_table_free": "免费版",
        "comparison_table_monthly": "Pro 月度",
        "comparison_table_yearly": "Pro 年度",
        "comparison_table_lifetime": "会员合伙人",
        "features_group_core": "【核心功能】",
        "features_group_advanced": "【高级功能】",
        "features_group_benefits": "【会员权益】",
        "feature_progress_bar": "每日进度条显示",
        "feature_progress_bar_free": "✓ 带水印",
        "feature_progress_bar_paid": "✓ 无水印",
        "feature_ai_planning": "AI 智能任务规划",
        "feature_ai_planning_free": "3次/天",
        "feature_ai_planning_monthly": "20次/天",
        "feature_ai_planning_yearly": "20次/天",
        "feature_ai_planning_lifetime": "50次/天",
        "feature_theme_custom": "主题自定义",
        "feature_validity": "有效期",
        "feature_validity_free": "-",
        "feature_validity_monthly": "30天",
        "feature_validity_yearly": "365天",
        "feature_validity_lifetime": "永久",
        "feature_referral_rate": "引荐返现比例",
        "member_tips_text": "GaiYa 致力于做优秀的时间管理工具，始终坚持无广告、无打扰、无冗余，简单而纯粹，我们将继续提供更加令人愉悦的用户体验。\\n\\n与此同时，我们深知，一个产品能够长久持续地运营下去，也需要有稳定的发展模式。如果你有意支持我们，可以开通会员，享受更丰富的 AI 功能，非常感谢你的支持！"
    }
}

new_keys_en = {
    "account": {
        "plan_monthly_name": "Pro Monthly",
        "plan_yearly_name": "Pro Yearly",
        "plan_lifetime_name": "Lifetime Partner",
        "plan_period_month": "/month",
        "plan_period_year": "/year",
        "plan_validity_30days": "Valid for 30 days",
        "plan_validity_365days": "Valid for 365 days",
        "plan_validity_lifetime": "Lifetime Access",
        "plan_no_auto_renewal": "No auto-renewal after expiration",
        "plan_one_time_payment": "One-time payment, lifetime access",
        "plan_save_40_percent": "Save 40%",
        "plan_limited_to_100": "Limited to 100",
        "comparison_table_features": "Features",
        "comparison_table_free": "Free",
        "comparison_table_monthly": "Pro Monthly",
        "comparison_table_yearly": "Pro Yearly",
        "comparison_table_lifetime": "Lifetime Partner",
        "features_group_core": "【Core Features】",
        "features_group_advanced": "【Advanced Features】",
        "features_group_benefits": "【Member Benefits】",
        "feature_progress_bar": "Daily Progress Bar",
        "feature_progress_bar_free": "✓ With watermark",
        "feature_progress_bar_paid": "✓ No watermark",
        "feature_ai_planning": "AI Task Planning",
        "feature_ai_planning_free": "3 times/day",
        "feature_ai_planning_monthly": "20 times/day",
        "feature_ai_planning_yearly": "20 times/day",
        "feature_ai_planning_lifetime": "50 times/day",
        "feature_theme_custom": "Theme Customization",
        "feature_validity": "Validity Period",
        "feature_validity_free": "-",
        "feature_validity_monthly": "30 days",
        "feature_validity_yearly": "365 days",
        "feature_validity_lifetime": "Lifetime",
        "feature_referral_rate": "Referral Cashback Rate",
        "member_tips_text": "GaiYa is committed to being an excellent time management tool, always adhering to no ads, no interruptions, no redundancy, simple and pure. We will continue to provide a more pleasant user experience.\\n\\nAt the same time, we know that for a product to operate sustainably in the long run, it also needs a stable development model. If you are willing to support us, you can become a member and enjoy richer AI features. Thank you very much for your support!"
    }
}

def merge_dict_recursive(target, source):
    """Recursively merge source dict into target dict"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            merge_dict_recursive(target[key], value)
        else:
            target[key] = value

# Load and update zh_CN.json
with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
    zh_data = json.load(f)

merge_dict_recursive(zh_data, new_keys_zh)

with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
    json.dump(zh_data, f, ensure_ascii=False, indent=2)

print("✓ Updated zh_CN.json")

# Load and update en_US.json
with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
    en_data = json.load(f)

merge_dict_recursive(en_data, new_keys_en)

with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
    json.dump(en_data, f, ensure_ascii=False, indent=2)

print("✓ Updated en_US.json")
print(f"✓ Added {len(new_keys_zh['account'])} new account keys")
