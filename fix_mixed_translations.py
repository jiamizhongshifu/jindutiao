#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix mixed Chinese-English translations"""
import json

# Mapping of mixed translations to fix
# Format: old_value -> new_value
fixes = {
    # Dialog translations
    "Select具体Date:": "Select Specific Date:",
    "Please at leastSelect一个Day of week": "Please select at least one day of week",
    "请Select规则类型": "Please select rule type",
    "Are you sure you want to delete这条规则?": "Are you sure you want to delete this rule?",
    "Select图片文件 (JPG/PNG/GIF/WebP)": "Select image file (JPG/PNG/GIF/WebP)",
    "请Select一个Scene": "Please select a scene",
    "Are you sure you want to 退出当前account？\\n\\n退出后将以guest身份继续使用，free user功能将受到限制。?": "Are you sure you want to logout?\\n\\nAfter logout, you will continue as a guest with limited features.",
    "SelectPayment方式": "Select Payment Method",
    "您Select的Plan：{plan['name']} - {plan['price_cny']}{plan['period']}": "Selected Plan: {plan['name']} - {plan['price_cny']}{plan['period']}",
    "请SelectPayment方式:": "Please select payment method:",
    "已Cancel": "Cancelled",
    "Update已Cancel": "Update cancelled",

    # General translations
    "✅ 启用": "✅ Enabled",
    "❌ 禁用": "❌ Disabled",
    "按Day of week重复": "Repeat by Day of Week",
    "Monthly重复": "Repeat Monthly",
    "特定Date": "Specific Dates",
    "Monthly的哪些天?（用逗号分隔，例如: 1,15,28）": "Which days of the month? (comma-separated, e.g.: 1,15,28)",
    "+ 添加Date": "+ Add Date",
    "Please enterMonthly的Date": "Please enter monthly date",
    "Date必须在1-31之间": "Date must be between 1-31",
    "Please at least添加一个Date": "Please add at least one date",
    "确认Delete": "Confirm Delete",
    "规则已Delete": "Rule deleted",
    "测试Date匹配": "Test Date Match",
    "测试Date: {selected_date.strftime('%Y-%m-%d %A')}": "Test Date: {selected_date.strftime('%Y-%m-%d %A')}",
    "建议：Delete或禁用其中某些规则，避免冲突": "Suggestion: Delete or disable some rules to avoid conflicts",
    "🔍 执行测试": "🔍 Run Test",
    "👤 个人中心": "👤 Account Center",
    "📖 关于": "📖 About",
    "自定义:": "Custom:",
    "📁 浏览": "📁 Browse",
    "✨ 视觉效果": "✨ Visual Effects",
    "描述您的计划:": "Describe your plan:",
    "Quota状态: Load中...": "Quota Status: Loading...",
    "快速Load:": "Quick Load:",
    "➕ 添加规则": "➕ Add Rule",
    "🔍 测试Date": "🔍 Test Date",
    "🛠 ️ 高级功能": "🛠️ Advanced Features",
    "描述: {description}\\n版本: {version}  作者: {author}": "Description: {description}\\nVersion: {version}  Author: {author}",
    "RefreshScene列表时出错:\\n{e}": "Error refreshing scene list:\\n{e}",
    "⏰ Reminder时机": "⏰ Reminder Timing",
    "🌙 免打扰时段": "🌙 Do Not Disturb",
    "启用Do Not Disturb时段": "Enable Do Not Disturb Period",
    "个人Medium心": "Account Center",
    "Advanced版": "Pro Version",
    "有效期30day": "Valid for 30 days",
    "数据云Sync": "Cloud Data Sync",
    "Scene系统": "Scene System",
    "有效期365day": "Valid for 365 days",
    "👋 欢迎使用 GaiYa Daily进度条": "👋 Welcome to GaiYa Daily Progress Bar",
    "• 优先获取新功能和Update": "• Early access to new features and updates",
    "您当前是Free User。Upgrade高级版可解锁更多功能。": "You are currently a free user. Upgrade to Pro to unlock more features.",
    "您YesAdvanced版用户，可以使用所有功能。": "You are a Pro user, you can use all features.",
    "您的账户信息已Update。": "Your account information has been updated.",
    "欢迎回来，{user_info.get('email', '用户')}！\\n\\n": "Welcome back, {user_info.get('email', 'User')}!\\n\\n",
    "Confirm退出": "Confirm Logout",
    "• 更多高级功能和服务\\n\\n": "• More advanced features and services\\n\\n",
    "GaiYaDaily进度条": "GaiYa Daily Progress Bar",
    "Daily进度条显示": "Daily Progress Bar Display",
    "✓ 带水印": "✓ With watermark",
    "✓ 无水印": "✓ No watermark",
    "【Advanced功能】": "【Advanced Features】",
    "💚 微信Payment": "💚 WeChat Pay",
    "💳 国际Payment (Stripe)": "💳 International Payment (Stripe)",
    "确认Payment": "Confirm Payment",
    "等待Payment": "Waiting for Payment",
    "正在等待Payment完成...\\n\\n": "Waiting for payment to complete...\\n\\n",
    "请在Open的浏览器页面中完成Payment。\\n": "Please complete payment in the opened browser page.\\n",
    "Payment完成后，此窗口将自动Close。": "This window will close automatically after payment is completed.",
    "Payment渠道暂时不可用：{error_msg}\\n\\n": "Payment channel temporarily unavailable: {error_msg}\\n\\n",
    "• Payment渠道临时维护中\\n": "• Payment channel under maintenance\\n",
    "• 需要在商户后台完成渠道签约\\n\\n": "• Channel contract needs to be completed in merchant backend\\n\\n",
    "1. 稍后重试（5-10minute后）\\n": "1. Retry later (after 5-10 minutes)\\n",
    "2. 联系Payment服务商客服（zpayz.cn）": "2. Contact payment provider support (zpayz.cn)",
    "• Payment方式: {pay_type}": "• Payment method: {pay_type}",
    "Payment窗口已Open": "Payment window opened",
    "StripePayment页面已在浏览器中Open。\\n\\n": "Stripe payment page has been opened in browser.\\n\\n",
    "请在浏览器中完成Payment。\\n": "Please complete payment in browser.\\n",
    "• 用户ID: {user_id}\\n": "• User ID: {user_id}\\n",
    "StripePayment异常: {str(e)}": "Stripe payment exception: {str(e)}",
    "Payment异常": "Payment Exception",
    "处理StripePayment时发生异常：\\n\\n{error_msg}\\n\\n请查看日志获取详细信息。": "Exception occurred while processing Stripe payment:\\n\\n{error_msg}\\n\\nPlease check logs for details.",
    "2. 尝试切换Payment方式（Payment宝/微信）\\n": "2. Try switching payment method (Alipay/WeChat)\\n",
    "3. 联系Payment服务商客服（zpayz.cn）": "3. Contact payment provider support (zpayz.cn)",
    "确认Clear": "Confirm Clear",
    "无法Save": "Cannot Save",
    "TemplateManager尚未Initialization，延迟500ms后重试": "TemplateManager not initialized yet, retry after 500ms",
    "已Delete": "Deleted",
    "测试Date: {test_datetime.strftime('%Y-%m-%d %A')}": "Test Date: {test_datetime.strftime('%Y-%m-%d %A')}",
    "\\nDate类型: {date_type}": "\\nDate Type: {date_type}",
    "\\n✅ 最佳匹配（优先级最高）: {best_match['name']}": "\\n✅ Best Match (Highest Priority): {best_match['name']}",
    "→ 将自动Load: {best_match['filename']}": "→ Will auto-load: {best_match['filename']}",
    "✓ 今日剩余: {daily_plan_remaining} 次规划": "✓ Remaining today: {daily_plan_remaining} plans",
    "⚠ ️ 今日Quota已用完": "⚠️ Daily quota exhausted",
    "⚠ ️ 无法连接云服务（请点击Refresh重试）": "⚠️ Cannot connect to cloud service (click Refresh to retry)",
    "请先描述您的计划!\\n\\n例如: 明day9点开会1Small时,然后写代码到下午5点": "Please describe your plan first!\\n\\nExample: Meeting at 9am for 1 hour, then coding until 5pm",
    "Confirm替换": "Confirm Replace",
    "📊 Token使用: {token_usage}\\n\\n": "📊 Token Usage: {token_usage}\\n\\n",
    "无Update说明": "No update notes",
    "\\n详Fine内容请访问 GitHub Release 页面查看...": "\\nFor detailed information, please visit GitHub Release page...",
    "未找到可执行文件，请手动前往 GitHub Download": "Executable file not found, please download manually from GitHub",
    "正在DownloadUpdate...": "Downloading update...",
    "自动Update": "Auto Update",
    "Download完成": "Download Complete",
    "无法自动Update": "Cannot Auto Update",
    "当前以源码方式运行，None法自动替换程序。\\n请手动替换可执行文件。": "Currently running from source code, cannot auto-replace program.\\nPlease replace executable manually.",
    "准备Update": "Preparing Update",
    "程序将Close并自动完成Update，Please wait...": "Program will close and complete update automatically, please wait...",
    "无法InstallUpdate：{str(e)}\\n\\n请手动替换程序文件": "Cannot install update: {str(e)}\\n\\nPlease replace program files manually",
    "检查Medium...": "Checking...",
    "v{latest_version} 可Update": "v{latest_version} available for update",
    "发现新Version": "New Version Found",
    "发现新版本 v{latest_version}": "New version found: v{latest_version}",
    "当前版本: v{current_version}\\n\\n核心Update:\\n{changelog_highlights}": "Current Version: v{current_version}\\n\\nCore Updates:\\n{changelog_highlights}",
    "立即Update": "Update Now",
    "前往Download": "Go to Download",
    "已YesLatest Version": "Already Latest Version",
    "当前版本 v{current_version} 已是最新版本！": "Current version v{current_version} is already the latest!",
    "暂None发布Version": "No Released Version Yet",
    "当前版本: v{__version__}\\n\\n项目仓库暂未发布正式版本，敬请期待！\\n\\n您可以访问 GitHub 仓库查看最新开发进展：\\n{APP_METADATA['repository']}": "Current Version: v{__version__}\\n\\nNo official version released yet, stay tuned!\\n\\nYou can visit GitHub repository to see latest development:\\n{APP_METADATA['repository']}",
    "无法连接到Update服务器\\n\\n{str(e)}": "Cannot connect to update server\\n\\n{str(e)}",
    "Add创始人微信": "Add Founder on WeChat",
    "无法Load二维码图片": "Cannot load QR code image",
    "二维码图片不存在\\n路径: {qrcode_path}": "QR code image does not exist\\nPath: {qrcode_path}",
}

def apply_fixes(data, fixes_dict):
    """Recursively apply fixes to dictionary values"""
    for key, value in data.items():
        if isinstance(value, dict):
            apply_fixes(value, fixes_dict)
        elif isinstance(value, str) and value in fixes_dict:
            data[key] = fixes_dict[value]
            print(f"Fixed: {key}")

# Load English translation file
with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
    en_data = json.load(f)

# Apply fixes
print("Applying fixes...")
apply_fixes(en_data, fixes)

# Save updated file
with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
    json.dump(en_data, f, ensure_ascii=False, indent=2)

print(f"\\nFixed {len([v for v in en_data.values() if isinstance(v, dict)])} translations")
print("Updated en_US.json saved successfully!")
