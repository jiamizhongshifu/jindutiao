#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply i18n to _create_account_tab() method
Automatically replace Chinese strings with tr() function calls
"""

import re

def apply_i18n_replacements():
    """Apply i18n replacements to config_gui.py"""

    with open('config_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Track replacements
    replacements_made = []
    replacements_skipped = []

    # Define replacements with line numbers for verification
    replacements = [
        # Basic account status
        ('        title_label = QLabel("个人中心")',
         '        title_label = QLabel(tr("account.title"))',
         2963),

        ('        email = auth_client.get_user_email() or "未登录"',
         '        email = auth_client.get_user_email() or tr("account.not_logged_in")',
         2970),

        ('        if email != "未登录":',
         '        if email != tr("account.not_logged_in"):',
         2973),

        ('            tier_names = {"free": "免费用户", "pro": "高级版", "lifetime": "会员合伙人"}',
         '            tier_names = {"free": tr("account.tier_free"), "pro": tr("account.tier_pro"), "lifetime": tr("account.tier_partner")}',
         2978),

        ('            info_label = QLabel(f"邮箱：{email}  |  会员等级：{tier_name}")',
         '            info_label = QLabel(tr("account.user_info", email=email, tier_name=tier_name))',
         2980),

        ('            logout_btn = QPushButton("退出登录")',
         '            logout_btn = QPushButton(tr("account.logout"))',
         2986),

        ('        if email != "未登录":',
         '        if email != tr("account.not_logged_in"):',
         2996),

        ('                tip_label = QLabel("会员套餐对比")',
         '                tip_label = QLabel(tr("account.membership_comparison"))',
         2998),

        # Plan data - Pro Monthly
        ('                        "name": "Pro 月度",',
         '                        "name": tr("account.plan_pro_monthly_name"),',
         3011),

        ('                        "period": "/月",',
         '                        "period": tr("account.per_month"),',
         3013),

        ('                        "validity": "有效期30天",',
         '                        "validity": tr("account.validity_30_days"),',
         3014),

        ('                        "renewal": "到期后不会自动扣费",',
         '                        "renewal": tr("account.no_auto_renewal"),',
         3015),

        ('                        "features": ["所有免费功能 +", "20次/天 AI智能规划", "统计报告分析", "去除进度条水印", "番茄时钟", "数据云同步", "场景系统", "抢先体验新功能", "加入VIP会员群"]',
         '                        "features": [tr("account.feature_all_free_plus"), tr("account.feature_ai_20_per_day"), tr("account.feature_statistics"), tr("account.feature_remove_watermark"), tr("account.feature_pomodoro"), tr("account.feature_cloud_sync"), tr("account.feature_scene_system"), tr("account.feature_early_access"), tr("account.feature_vip_group")]',
         3017),

        # Plan data - Pro Yearly
        ('                        "name": "Pro 年度",',
         '                        "name": tr("account.plan_pro_yearly_name"),',
         3021),

        ('                        "period": "/年",',
         '                        "period": tr("account.per_year"),',
         3023),

        ('                        "discount_badge": "节省 40%",',
         '                        "discount_badge": tr("account.save_40_percent"),',
         3026),

        ('                        "validity": "有效期365天",',
         '                        "validity": tr("account.validity_365_days"),',
         3027),

        ('                        "renewal": "到期后不会自动扣费",',
         '                        "renewal": tr("account.no_auto_renewal"),',
         3028),

        ('                        "features": ["所有免费功能 +", "20次/天 AI智能规划", "统计报告分析", "去除进度条水印", "番茄时钟", "数据云同步", "场景系统", "抢先体验新功能", "加入VIP会员群"]',
         '                        "features": [tr("account.feature_all_free_plus"), tr("account.feature_ai_20_per_day"), tr("account.feature_statistics"), tr("account.feature_remove_watermark"), tr("account.feature_pomodoro"), tr("account.feature_cloud_sync"), tr("account.feature_scene_system"), tr("account.feature_early_access"), tr("account.feature_vip_group")]',
         3030),

        # Plan data - Lifetime
        ('                        "name": "会员合伙人",',
         '                        "name": tr("account.tier_partner"),',
         3034),

        ('                        "validity": "永久有效",',
         '                        "validity": tr("account.lifetime_validity"),',
         3037),

        ('                        "renewal": "一次购买,终身可用",',
         '                        "renewal": tr("account.one_time_purchase"),',
         3038),

        ('                        "features": ["所有免费功能 +", "50次/天 AI智能规划", "统计报告分析", "去除进度条水印", "番茄时钟", "数据云同步", "场景系统", "33%引荐返现比例", "专属合伙人社群", "优先体验所有新功能", "专属1v1咨询服务", "共同成长,分享价值"]',
         '                        "features": [tr("account.feature_all_free_plus"), tr("account.feature_ai_50_per_day"), tr("account.feature_statistics"), tr("account.feature_remove_watermark"), tr("account.feature_pomodoro"), tr("account.feature_cloud_sync"), tr("account.feature_scene_system"), tr("account.feature_referral_33"), tr("account.feature_partner_community"), tr("account.feature_priority_access"), tr("account.feature_1v1_consulting"), tr("account.feature_grow_together")]',
         3040),

        # Thank you message
        ('                info_label = QLabel("感谢您的支持！")',
         '                info_label = QLabel(tr("account.thank_you_support"))',
         3176),

        # Login UI
        ('            welcome_label = QLabel("👋 欢迎使用 GaiYa 每日进度条")',
         '            welcome_label = QLabel(tr("account.welcome_message"))',
         3184),

        ('            tip_label = QLabel("登录后即可使用 AI智能规划、数据云同步等高级功能")',
         '            tip_label = QLabel(tr("account.login_benefit_hint"))',
         3189),

        ('            login_button = QPushButton("🔑 点击登录 / 注册")',
         '            login_button = QPushButton(tr("account.btn_login_register"))',
         3195),

        ('            features_label = QLabel("🎁 登录后享受的权益：")',
         '            features_label = QLabel(tr("account.login_benefits_title"))',
         3225),

        # Features list
        ('                "• 免费用户：每天 3 次 AI智能规划配额",',
         '                tr("account.benefit_free_user"),',
         3230),

        ('                "• Pro会员：每天 20 次 AI智能规划配额",',
         '                tr("account.benefit_pro_user"),',
         3231),

        ('                "• 数据云同步：自定义模板和历史统计同步到云端",',
         '                tr("account.benefit_cloud_sync"),',
         3232),

        ('                "• 模板自动应用：根据日期规则自动切换任务模板",',
         '                tr("account.benefit_auto_template"),',
         3233),

        ('                "• 优先获取新功能和更新",',
         '                tr("account.benefit_priority_updates"),',
         3234),

        ('                "• 加入专属VIP会员群，获取更多支持"',
         '                tr("account.benefit_vip_support")',
         3235),
    ]

    # Apply each replacement
    for old, new, line_num in replacements:
        if old in content:
            content = content.replace(old, new, 1)  # Replace only first occurrence
            replacements_made.append((line_num, old[:50]))
        else:
            replacements_skipped.append((line_num, old[:50]))

    # Write back
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.write(content)

    # Write report to file
    with open('account_tab_i18n_replacement_log.txt', 'w', encoding='utf-8') as f:
        f.write("=== _create_account_tab() i18n Replacement Report ===\n\n")
        f.write(f"Total replacements attempted: {len(replacements)}\n")
        f.write(f"Successfully replaced: {len(replacements_made)}\n")
        f.write(f"Skipped (not found): {len(replacements_skipped)}\n\n")

        if replacements_made:
            f.write("✅ Successfully Replaced:\n")
            for line_num, text in replacements_made:
                f.write(f"  Line {line_num}: {text}...\n")

        if replacements_skipped:
            f.write("\n⚠️ Skipped (need manual fix):\n")
            for line_num, text in replacements_skipped:
                f.write(f"  Line {line_num}: {text}...\n")

    print(f"Replacement complete!")
    print(f"Successfully replaced: {len(replacements_made)}/{len(replacements)}")
    print(f"Skipped: {len(replacements_skipped)}")
    print(f"Check account_tab_i18n_replacement_log.txt for details")

if __name__ == '__main__':
    apply_i18n_replacements()
