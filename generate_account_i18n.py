#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为个人中心生成i18n翻译
"""

import json
from pathlib import Path

# 个人中心专用的翻译映射
ACCOUNT_CENTER_TRANSLATIONS = {
    # === 会员账号相关 ===
    "membership": {
        "not_logged_in": {"zh": "未登录", "en": "Not Logged In"},
        "free_user": {"zh": "免费用户", "en": "Free User"},
        "pro_user": {"zh": "高级版", "en": "Pro"},
        "lifetime_member": {"zh": "终身会员", "en": "Lifetime Member"},
        "user": {"zh": "用户", "en": "User"},
        "join_vip_group": {"zh": "加入VIP会员群", "en": "Join VIP Community"},
        "free_user_quota_msg": {"zh": "• 免费用户：每天 3 次 AI智能规划配额", "en": "• Free users: 3 AI smart planning quotas per day"},
        "pro_member_quota_msg": {"zh": "• Pro会员：每天 20 次 AI智能规划配额", "en": "• Pro members: 20 AI smart planning quotas per day"},
        "vip_support_msg": {"zh": "• 加入专属VIP会员群，获取更多支持", "en": "• Join exclusive VIP community for more support"},
        "upgrade_to_pro_msg": {"zh": "您当前是免费用户。升级高级版可解锁更多功能。", "en": "You are currently a free user. Upgrade to Pro to unlock more features."},
        "pro_user_msg": {"zh": "您是高级版用户，可以使用所有功能。", "en": "You are a Pro user with access to all features."},
        "lifetime_member_msg": {"zh": "您是终身会员，尊享所有高级功能。", "en": "You are a lifetime member, enjoying all premium features."},
        "go_to_login": {"zh": "是否前往个人中心登录？", "en": "Go to account center to log in?"},
        "user_info_incomplete": {"zh": "用户信息不完整，请重新登录", "en": "User information incomplete, please log in again"},
        "payment_auto_activate": {"zh": "支付成功后，会员权益将自动激活。", "en": "Membership benefits will be automatically activated after successful payment."},
        "member_benefits_title": {"zh": "【会员权益】", "en": "【Membership Benefits】"},
        "welcome_back": {"zh": "欢迎回来，", "en": "Welcome back, "},
        "thank_you_support": {"zh": "感谢您的支持！", "en": "Thank you for your support!"},
    },

    # === 套餐价格相关 ===
    "plan": {
        "monthly": {"zh": "/月", "en": "/month"},
        "yearly": {"zh": "/年", "en": "/year"},
        "validity_30_days": {"zh": "有效期30天", "en": "Valid for 30 days"},
        "validity_365_days": {"zh": "有效期365天", "en": "Valid for 365 days"},
        "save_40_percent": {"zh": "节省 40%", "en": "Save 40%"},
        "lifetime_valid": {"zh": "永久有效", "en": "Lifetime Access"},
        "one_time_purchase": {"zh": "一次购买,终身可用", "en": "One-time purchase, lifetime access"},
        "no_auto_renew": {"zh": "到期后不会自动扣费", "en": "No automatic renewal after expiration"},
        "validity": {"zh": "有效期", "en": "Validity"},
        "30_days": {"zh": "30天", "en": "30 Days"},
        "365_days": {"zh": "365天", "en": "365 Days"},
        "lifetime": {"zh": "永久", "en": "Lifetime"},
    },

    # === 功能特性描述 ===
    "feature": {
        "all_free_features_plus": {"zh": "所有免费功能 +", "en": "All Free Features +"},
        "statistics_analysis": {"zh": "统计报告分析", "en": "Statistics & Reports"},
        "remove_watermark": {"zh": "去除进度条水印", "en": "Remove Progress Bar Watermark"},
        "pomodoro_clock": {"zh": "番茄时钟", "en": "Pomodoro Timer"},
        "cloud_sync": {"zh": "数据云同步", "en": "Cloud Data Sync"},
        "scene_system": {"zh": "场景系统", "en": "Scene System"},
        "early_access": {"zh": "抢先体验新功能", "en": "Early Access to New Features"},
        "priority_new_features": {"zh": "优先体验所有新功能", "en": "Priority access to all new features"},
        "referral_commission": {"zh": "33%引荐返现比例", "en": "33% Referral Commission"},
        "referral_commission_rate": {"zh": "引荐返现比例", "en": "Referral Commission Rate"},
        "partner_community": {"zh": "专属合伙人社群", "en": "Exclusive Partner Community"},
        "one_on_one_consultation": {"zh": "专属1v1咨询服务", "en": "Exclusive 1-on-1 Consultation"},
        "one_on_one": {"zh": "1v1咨询服务", "en": "1-on-1 Consultation"},
        "grow_together": {"zh": "共同成长,分享价值", "en": "Grow together, share value"},
        "cloud_sync_desc": {"zh": "• 数据云同步：自定义模板和历史统计同步到云端", "en": "• Cloud Data Sync: Custom templates and historical statistics synced to cloud"},
        "auto_apply_desc": {"zh": "• 模板自动应用：根据日期规则自动切换任务模板", "en": "• Auto-apply Templates: Automatically switch task templates based on date rules"},
        "priority_updates_desc": {"zh": "• 优先获取新功能和更新", "en": "• Priority access to new features and updates"},

        # 功能特性表格
        "feature_list": {"zh": "功能特性", "en": "Features"},
        "free_version": {"zh": "免费版", "en": "Free"},
        "core_features": {"zh": "【核心功能】", "en": "【Core Features】"},
        "advanced_features": {"zh": "【高级功能】", "en": "【Advanced Features】"},
        "daily_progress_bar": {"zh": "每日进度条显示", "en": "Daily Progress Bar"},
        "with_watermark": {"zh": "✓ 带水印", "en": "✓ With Watermark"},
        "no_watermark": {"zh": "✓ 无水印", "en": "✓ No Watermark"},
        "ai_smart_planning": {"zh": "AI 智能任务规划", "en": "AI Smart Task Planning"},
        "times_per_day": {"zh": "次/天", "en": "/day"},
        "theme_customization": {"zh": "主题自定义", "en": "Theme Customization"},
    },

    # === 支付流程相关 ===
    "payment": {
        "select_payment_method": {"zh": "选择支付方式", "en": "Select Payment Method"},
        "wechat_pay": {"zh": "💚 微信支付", "en": "💚 WeChat Pay"},
        "stripe_pay": {"zh": "💳 国际支付 (Stripe)", "en": "💳 International Payment (Stripe)"},
        "waiting_payment": {"zh": "等待支付", "en": "Waiting for Payment"},
        "payment_window_auto_close": {"zh": "支付完成后，此窗口将自动关闭。", "en": "This window will close automatically after payment is completed."},
        "payment_channel": {"zh": "渠道", "en": "Channel"},
        "contact_support": {"zh": "2. 联系支付服务商客服（zpayz.cn）", "en": "2. Contact payment service customer support (zpayz.cn)"},
        "contact_support_stripe": {"zh": "3. 联系支付服务商客服（zpayz.cn）", "en": "3. Contact payment service customer support (zpayz.cn)"},
        "payment_method": {"zh": "• 支付方式: {pay_type}", "en": "• Payment method: {pay_type}"},
        "user_email": {"zh": "• 邮箱: {email}", "en": "• Email: {email}"},
    },

    # === UI界面文本 ===
    "ui": {
        "confirm_delete": {"zh": "确认删除", "en": "Confirm Delete"},
        "confirm_clear": {"zh": "确认清空", "en": "Confirm Clear"},
        "select_template": {"zh": "选择模板", "en": "Select Template"},
        "select_template_to_load": {"zh": "请选择要加载的自定义模板:", "en": "Please select a custom template to load:"},
        "confirm_load_template": {"zh": "确认加载模板", "en": "Confirm Load Template"},
        "select_marker_image": {"zh": "选择时间标记图片", "en": "Select Time Marker Image"},
        "select_color": {"zh": "选择颜色", "en": "Select Color"},
        "confirm_replace": {"zh": "确认替换", "en": "Confirm Replace"},
        "remember_to_save": {"zh": "记得点击【保存所有设置】按钮来保存更改", "en": "Remember to click [Save All Settings] button to save changes"},
        "cannot_connect_cloud": {"zh": "⚠️ 无法连接云服务（请点击刷新重试）", "en": "⚠️ Cannot connect to cloud service (click refresh to retry)"},
        "please_wait": {"zh": "请稍候", "en": "Please wait"},
        "ai_processing": {"zh": "AI正在处理上一个请求,请稍候...", "en": "AI is processing the previous request, please wait..."},
        "ai_initializing": {"zh": "AI服务正在初始化", "en": "AI Service Initializing"},
        "ai_starting": {"zh": "AI服务正在后台启动中,请稍候片刻再试...", "en": "AI service is starting in the background, please try again in a moment..."},
        "ai_generating": {"zh": "⏳ AI正在生成...", "en": "⏳ AI is generating..."},
        "ai_smart_generate": {"zh": "✨ 智能生成任务", "en": "✨ Smart Generate Tasks"},
        "connecting_cloud": {"zh": "⏳ 正在连接云服务...", "en": "⏳ Connecting to cloud service..."},
        "input_empty": {"zh": "输入为空", "en": "Input is empty"},
    },

    # === 提示消息 ===
    "message": {
        "save_success": {"zh": "保存成功", "en": "Saved successfully"},
        "save_failed": {"zh": "保存失败", "en": "Save failed"},
        "load_success": {"zh": "加载成功", "en": "Loaded successfully"},
        "delete_success": {"zh": "删除成功", "en": "Deleted successfully"},
        "delete_failed": {"zh": "删除失败", "en": "Delete failed"},
        "generate_success": {"zh": "生成成功", "en": "Generated successfully"},
        "generate_failed": {"zh": "生成失败", "en": "Generation failed"},
        "error_occurred": {"zh": "发生错误", "en": "An error occurred"},
        "cannot_save_empty": {"zh": "无法保存", "en": "Cannot save"},
        "no_tasks_to_save": {"zh": "当前没有任何任务,无法保存为模板!", "en": "No tasks available, cannot save as template!"},
        "no_custom_templates": {"zh": "没有自定义模板", "en": "No custom templates"},
        "no_custom_templates_placeholder": {"zh": "(暂无自定义模板)", "en": "(No custom templates yet)"},
        "template_not_exist": {"zh": "模板不存在", "en": "Template does not exist"},
        "confirm_delete_task": {"zh": "确定要删除第 {row + 1} 个任务吗?", "en": "Are you sure to delete task #{row + 1}?"},
        "confirm_delete_template": {"zh": "确定要删除模板 ", "en": "Are you sure to delete template "},
        "template_deleted": {"zh": " 已删除", "en": " has been deleted"},
        "time_error": {"zh": "时间错误", "en": "Time Error"},
        "time_overlap_warning": {"zh": "时间重叠警告", "en": "Time Overlap Warning"},
        "ai_no_tasks_generated": {"zh": "AI未能生成任何任务,请尝试更详细地描述您的计划。", "en": "AI failed to generate any tasks, please try to describe your plan in more detail."},
        "quota_remaining": {"zh": "✓ 今日剩余: {daily_plan_remaining} 次规划", "en": "✓ Remaining today: {daily_plan_remaining} planning(s)"},
        "quota_exhausted": {"zh": "⚠️ 今日配额已用完", "en": "⚠️ Today's quota exhausted"},
        "new_task": {"zh": "新任务", "en": "New Task"},
        "work_off": {"zh": "下班", "en": "Off Work"},
        "template_loaded_count": {"zh": "成功加载 {len(templates)} 个模板按钮", "en": "Successfully loaded {len(templates)} template button(s)"},
        "custom_template_count": {"zh": ", 0)}个任务)", "en": ", 0)} tasks)"},
        "template_auto_apply_loaded": {"zh": "已加载 {len(templates)} 个模板的自动应用设置", "en": "Loaded auto-apply settings for {len(templates)} template(s)"},
        "template_auto_apply_saved": {"zh": "已保存 {updated_count} 个模板的自动应用设置", "en": "Saved auto-apply settings for {updated_count} template(s)"},
        "autostart_enabled": {"zh": "(将在开机时自动启动)", "en": "(Will start automatically on boot)"},
        "autostart_disabled": {"zh": "(未启用)", "en": "(Not enabled)"},
        "autostart_set_disabled": {"zh": "自启动设置{", "en": "Autostart setting {"},
        "disabled": {"zh": "禁用", "en": "disabled"},
    },

    # === 其他文本 ===
    "other": {
        "image_files": {"zh": "图片文件 (*.jpg *.jpeg *.png *.gif *.webp)", "en": "Image files (*.jpg *.jpeg *.png *.gif *.webp)"},
        "delete_task": {"zh": "删除任务", "en": "Delete Task"},
        "clear_all_tasks": {"zh": "清空所有任务", "en": "Clear All Tasks"},
        "save_as_template": {"zh": "💾 保存为模板", "en": "💾 Save as Template"},
        "template_name": {"zh": "模板名称", "en": "Template Name"},
        "apply_time": {"zh": "应用时间", "en": "Apply Time"},
        "status": {"zh": "状态", "en": "Status"},
        "actions": {"zh": "操作", "en": "Actions"},
        "custom_template_format": {"zh": "自定义模板 ({len(tasks)}个任务)", "en": "Custom Template ({len(tasks)} tasks)"},
        "test_date": {"zh": "测试日期: {test_datetime.strftime(", "en": "Test date: {test_datetime.strftime("},
        "weekday": {"zh": "  - weekday: 工作日", "en": "  - weekday: Weekday"},
        "weekend": {"zh": "  - weekend: 周末", "en": "  - weekend: Weekend"},
        "holiday": {"zh": "  - holiday: 节假日", "en": "  - holiday: Holiday"},
        "any": {"zh": "任意", "en": "Any"},
        "will_auto_load": {"zh": "   → 将自动加载: {best_match[", "en": "   → Will auto-load: {best_match["},
        "no_match": {"zh": "  (无匹配模板)", "en": "  (No matching template)"},
        "will_use_default": {"zh": "   → 将使用默认24小时模板", "en": "   → Will use default 24-hour template"},
    }
}

def generate_flat_translations():
    """将嵌套的翻译字典展平为account命名空间下的key"""
    zh_flat = {}
    en_flat = {}

    for category, items in ACCOUNT_CENTER_TRANSLATIONS.items():
        for key, translations in items.items():
            full_key = f"account.{category}.{key}"
            zh_flat[full_key] = translations['zh']
            en_flat[full_key] = translations['en']

    return zh_flat, en_flat

def main():
    print("Generating i18n translations for account center...")

    zh_translations, en_translations = generate_flat_translations()

    print(f"Generated {len(zh_translations)} translation keys")

    # 保存为JSON文件供后续合并
    output_zh = Path('account_center_i18n_zh.json')
    output_en = Path('account_center_i18n_en.json')

    with open(output_zh, 'w', encoding='utf-8') as f:
        json.dump(zh_translations, f, ensure_ascii=False, indent=2)

    with open(output_en, 'w', encoding='utf-8') as f:
        json.dump(en_translations, f, ensure_ascii=False, indent=2)

    print(f"Chinese translations saved to: {output_zh}")
    print(f"English translations saved to: {output_en}")

    # 生成替换映射供代码更新使用
    replacement_map = {}
    for category, items in ACCOUNT_CENTER_TRANSLATIONS.items():
        for key, translations in items.items():
            zh_text = translations['zh']
            i18n_key = f"account.{category}.{key}"
            replacement_map[zh_text] = i18n_key

    output_map = Path('account_center_replacement_map.json')
    with open(output_map, 'w', encoding='utf-8') as f:
        json.dump(replacement_map, f, ensure_ascii=False, indent=2)

    print(f"Replacement map saved to: {output_map}")
    print(f"\nTotal: {len(zh_translations)} keys generated")

if __name__ == '__main__':
    main()
