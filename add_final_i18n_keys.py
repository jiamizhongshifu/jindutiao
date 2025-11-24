#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add all remaining translation keys for the 119 UI strings
"""

import json
from pathlib import Path

def deep_merge(target, source):
    """Deep merge source dict into target dict"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value

def add_final_keys():
    """Add all remaining translation keys"""

    # New keys in Chinese
    final_zh = {
        "appearance": {
            "sections": {
                "basic_settings": "🔧 基本设置",
                "color_settings": "🎨 颜色设置",
                "visual_effects": "✨ 视觉效果"
            },
            "labels": {
                "custom": "自定义:",
                "browse": "📁 浏览",
                "hint_line_image_gif": "(line=线条, image=图片, gif=动画)",
                "hint_horizontal": "(正值向右,负值向左)",
                "hint_vertical": "(正值向上,负值向下)",
                "hint_speed": "(100%=原速, 200%=2倍速)"
            }
        },
        "tasks": {
            "sections": {
                "ai_planning": "🤖 AI智能规划",
                "preset_themes": "🎨 预设主题配色",
                "preset_templates": "📋 预设模板",
                "my_templates": "💾 我的模板",
                "visual_timeline": "🎨 可视化时间轴编辑器",
                "auto_apply_management": "📅 模板自动应用管理"
            },
            "labels": {
                "describe_plan": "描述您的计划:",
                "quota_status_loading": "配额状态: 加载中...",
                "select_theme": "选择主题:",
                "color_preview": "配色预览:",
                "quick_load": "快速加载:",
                "template_loading": "模板加载中..."
            },
            "buttons": {
                "refresh_quota": "🔄 刷新配额",
                "add_task": "➕ 添加任务",
                "load_custom_template": "📂 加载自定义模板",
                "clear_all_tasks": "🗑️ 清空所有任务",
                "add_rule": "➕ 添加规则",
                "test_date": "🔍 测试日期",
                "load": "📂 加载"
            },
            "hints": {
                "ai_description": "💡 用自然语言描述您的计划,AI将自动生成任务时间表",
                "double_click_edit": "双击表格单元格可以编辑任务内容",
                "drag_to_adjust": "💡 提示：拖动色块边缘可调整任务时长",
                "auto_apply_description": "💡 为每个模板设置自动应用的日期规则，到了指定时间会自动加载对应模板"
            },
            "messages": {
                "theme_manager_not_initialized": "主题管理器未初始化，请稍后再试",
                "please_select_theme": "请先选择一个主题",
                "theme_applied": "已应用主题: {theme_name}",
                "apply_theme_failed": "应用主题失败",
                "theme_color_applied_to_tasks": "已应用主题配色到任务",
                "all_tasks_cleared": "所有任务已清空\\n\\n记得点击【保存所有设置】按钮来保存更改",
                "cannot_save_empty": "当前没有任何任务,无法保存为模板!",
                "please_create_template_first": "请先创建自定义模板",
                "no_settings_saved": "没有设置被保存",
                "test_template_match": "测试模板匹配",
                "template_deleted": "模板 {name} 已删除",
                "save_failed_with_error": "保存失败:\\n{error}",
                "template_save_failed": "无法保存模板:\\n{error}",
                "template_format_error": "模板文件格式错误:\\n{error}",
                "template_load_failed": "加载模板失败:\\n{error}",
                "template_file_not_exist": "模板文件不存在:\\n{filename}",
                "template_delete_failed": "无法删除模板:\\n{error}"
            }
        },
        "scenes": {
            "sections": {
                "basic_settings": "⚙️ 基础设置",
                "scene_selection": "🎬 场景选择",
                "advanced_features": "🛠️ 高级功能"
            },
            "labels": {
                "current_scene": "当前场景:",
                "description": "配置场景效果,让进度条更具个性化"
            },
            "buttons": {
                "refresh_scenes": "🔄 刷新场景",
                "open_scene_editor": "🎨 打开场景编辑器"
            },
            "messages": {
                "please_select_scene": "请选择一个场景",
                "editor_description": "场景编辑器可以创建和编辑自定义场景效果",
                "load_failed": "加载场景设置失败: {error}"
            }
        },
        "notifications": {
            "sections": {
                "basic_settings": "⚙️ 基础设置",
                "reminder_timing": "⏰ 提醒时机",
                "task_start_reminder": "🔔 任务开始前提醒",
                "task_end_reminder": "🔕 任务结束前提醒",
                "do_not_disturb": "🌙 免打扰时段"
            },
            "labels": {
                "description": "配置任务提醒通知,让您不会错过任何重要时刻",
                "select_before_start": "选择在任务开始前多久提醒(可多选):",
                "select_before_end": "选择在任务结束前多久提醒(可多选):",
                "hint_after_time": "(在此时间后不发送通知)",
                "hint_before_time": "(在此时间前不发送通知)",
                "example_time_range": "示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰"
            },
            "messages": {
                "load_failed": "加载通知设置失败: {error}"
            }
        },
        "profile": {
            "sections": {
                "profile_center": "个人中心"
            },
            "labels": {
                "user_info": "邮箱：{email}  |  会员等级：{tier_name}",
                "membership_comparison": "会员套餐对比"
            },
            "buttons": {
                "logout": "退出登录",
                "login_register": "🔑 点击登录 / 注册",
                "upgrade_membership": "升级会员",
                "become_partner": "成为合伙人"
            },
            "messages": {
                "welcome": "👋 欢迎使用 GaiYa 每日进度条",
                "login_benefits": "登录后即可使用 AI智能规划、数据云同步等高级功能",
                "benefits_title": "🎁 登录后享受的权益：",
                "thank_you": "感谢您的支持！",
                "load_failed": "加载个人中心标签页失败: {error}"
            }
        },
        "payment": {
            "labels": {
                "select_payment_method": "选择支付方式",
                "please_select_payment": "请选择支付方式：",
                "selected_plan": "您选择的套餐：{plan_name} - {price}{period}",
                "waiting_payment": "等待支付"
            },
            "buttons": {
                "confirm_payment": "确认支付"
            }
        },
        "about": {
            "labels": {
                "version": "版本 v{version}",
                "scan_qr_feedback": "扫描二维码，直接反馈问题",
                "scan_add_friend": "扫一扫上面的二维码图案，加我为朋友。"
            },
            "messages": {
                "load_failed": "加载关于标签页失败: {error}\\n\\n请检查日志文件获取详细信息",
                "qr_not_exist": "二维码图片不存在\\n路径: {path}"
            }
        },
        "updates": {
            "buttons": {
                "update_now": "立即更新",
                "go_to_download": "前往下载"
            },
            "messages": {
                "network_timeout": "网络请求超时，请检查网络连接",
                "cannot_connect": "无法连接到更新服务器\\n\\n{error}",
                "unknown_error": "发生未知错误\\n\\n{error}",
                "cancelled": "已取消"
            }
        },
        "common": {
            "dialog_titles": {
                "cannot_save": "无法保存",
                "save_failed": "保存失败",
                "delete_success": "删除成功",
                "delete_failed": "删除失败"
            },
            "messages": {
                "config_saved": "配置和任务已保存!\\n\\n如果 Gaiya 正在运行,更改会自动生效。"
            }
        }
    }

    # New keys in English
    final_en = {
        "appearance": {
            "sections": {
                "basic_settings": "🔧 Basic Settings",
                "color_settings": "🎨 Color Settings",
                "visual_effects": "✨ Visual Effects"
            },
            "labels": {
                "custom": "Custom:",
                "browse": "📁 Browse",
                "hint_line_image_gif": "(line=line, image=image, gif=animation)",
                "hint_horizontal": "(positive=right, negative=left)",
                "hint_vertical": "(positive=up, negative=down)",
                "hint_speed": "(100%=normal, 200%=2x speed)"
            }
        },
        "tasks": {
            "sections": {
                "ai_planning": "🤖 AI Planning",
                "preset_themes": "🎨 Preset Themes",
                "preset_templates": "📋 Preset Templates",
                "my_templates": "💾 My Templates",
                "visual_timeline": "🎨 Visual Timeline Editor",
                "auto_apply_management": "📅 Template Auto-Apply Management"
            },
            "labels": {
                "describe_plan": "Describe your plan:",
                "quota_status_loading": "Quota Status: Loading...",
                "select_theme": "Select Theme:",
                "color_preview": "Color Preview:",
                "quick_load": "Quick Load:",
                "template_loading": "Loading template..."
            },
            "buttons": {
                "refresh_quota": "🔄 Refresh Quota",
                "add_task": "➕ Add Task",
                "load_custom_template": "📂 Load Custom Template",
                "clear_all_tasks": "🗑️ Clear All Tasks",
                "add_rule": "➕ Add Rule",
                "test_date": "🔍 Test Date",
                "load": "📂 Load"
            },
            "hints": {
                "ai_description": "💡 Describe your plan in natural language, AI will automatically generate a task schedule",
                "double_click_edit": "Double-click table cells to edit task content",
                "drag_to_adjust": "💡 Tip: Drag color block edges to adjust task duration",
                "auto_apply_description": "💡 Set auto-apply date rules for each template, the corresponding template will be loaded automatically at the specified time"
            },
            "messages": {
                "theme_manager_not_initialized": "Theme manager not initialized, please try again later",
                "please_select_theme": "Please select a theme first",
                "theme_applied": "Theme applied: {theme_name}",
                "apply_theme_failed": "Failed to apply theme",
                "theme_color_applied_to_tasks": "Theme colors applied to tasks",
                "all_tasks_cleared": "All tasks cleared\\n\\nRemember to click the [Save All Settings] button to save changes",
                "cannot_save_empty": "No tasks available, cannot save as template!",
                "please_create_template_first": "Please create a custom template first",
                "no_settings_saved": "No settings were saved",
                "test_template_match": "Test Template Match",
                "template_deleted": "Template {name} deleted",
                "save_failed_with_error": "Save failed:\\n{error}",
                "template_save_failed": "Cannot save template:\\n{error}",
                "template_format_error": "Template file format error:\\n{error}",
                "template_load_failed": "Failed to load template:\\n{error}",
                "template_file_not_exist": "Template file does not exist:\\n{filename}",
                "template_delete_failed": "Cannot delete template:\\n{error}"
            }
        },
        "scenes": {
            "sections": {
                "basic_settings": "⚙️ Basic Settings",
                "scene_selection": "🎬 Scene Selection",
                "advanced_features": "🛠️ Advanced Features"
            },
            "labels": {
                "current_scene": "Current Scene:",
                "description": "Configure scene effects to personalize your progress bar"
            },
            "buttons": {
                "refresh_scenes": "🔄 Refresh Scenes",
                "open_scene_editor": "🎨 Open Scene Editor"
            },
            "messages": {
                "please_select_scene": "Please select a scene",
                "editor_description": "Scene editor allows you to create and edit custom scene effects",
                "load_failed": "Failed to load scene settings: {error}"
            }
        },
        "notifications": {
            "sections": {
                "basic_settings": "⚙️ Basic Settings",
                "reminder_timing": "⏰ Reminder Timing",
                "task_start_reminder": "🔔 Task Start Reminder",
                "task_end_reminder": "🔕 Task End Reminder",
                "do_not_disturb": "🌙 Do Not Disturb"
            },
            "labels": {
                "description": "Configure task reminder notifications so you won't miss any important moments",
                "select_before_start": "Select how long before task start to remind (multiple selections allowed):",
                "select_before_end": "Select how long before task end to remind (multiple selections allowed):",
                "hint_after_time": "(No notifications sent after this time)",
                "hint_before_time": "(No notifications sent before this time)",
                "example_time_range": "Example: 22:00 - 08:00 means no disturbance from 10 PM to 8 AM"
            },
            "messages": {
                "load_failed": "Failed to load notification settings: {error}"
            }
        },
        "profile": {
            "sections": {
                "profile_center": "Profile Center"
            },
            "labels": {
                "user_info": "Email: {email}  |  Tier: {tier_name}",
                "membership_comparison": "Membership Plan Comparison"
            },
            "buttons": {
                "logout": "Logout",
                "login_register": "🔑 Login / Register",
                "upgrade_membership": "Upgrade Membership",
                "become_partner": "Become Partner"
            },
            "messages": {
                "welcome": "👋 Welcome to GaiYa Daily Progress Bar",
                "login_benefits": "Login to use AI Planning, Cloud Sync and other premium features",
                "benefits_title": "🎁 Benefits after login:",
                "thank_you": "Thank you for your support!",
                "load_failed": "Failed to load profile tab: {error}"
            }
        },
        "payment": {
            "labels": {
                "select_payment_method": "Select Payment Method",
                "please_select_payment": "Please select payment method:",
                "selected_plan": "Your selected plan: {plan_name} - {price}{period}",
                "waiting_payment": "Waiting for payment"
            },
            "buttons": {
                "confirm_payment": "Confirm Payment"
            }
        },
        "about": {
            "labels": {
                "version": "Version v{version}",
                "scan_qr_feedback": "Scan QR code for feedback",
                "scan_add_friend": "Scan the QR code above to add me as a friend."
            },
            "messages": {
                "load_failed": "Failed to load about tab: {error}\\n\\nPlease check log file for details",
                "qr_not_exist": "QR code image does not exist\\nPath: {path}"
            }
        },
        "updates": {
            "buttons": {
                "update_now": "Update Now",
                "go_to_download": "Go to Download"
            },
            "messages": {
                "network_timeout": "Network request timeout, please check network connection",
                "cannot_connect": "Cannot connect to update server\\n\\n{error}",
                "unknown_error": "Unknown error occurred\\n\\n{error}",
                "cancelled": "Cancelled"
            }
        },
        "common": {
            "dialog_titles": {
                "cannot_save": "Cannot Save",
                "save_failed": "Save Failed",
                "delete_success": "Delete Success",
                "delete_failed": "Delete Failed"
            },
            "messages": {
                "config_saved": "Configuration and tasks saved!\\n\\nChanges will take effect automatically if Gaiya is running."
            }
        }
    }

    # Load and merge zh_CN
    zh_file = Path('i18n/zh_CN.json')
    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    deep_merge(zh_data, final_zh)

    with open(zh_file, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated {zh_file}")

    # Load and merge en_US
    en_file = Path('i18n/en_US.json')
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    deep_merge(en_data, final_en)

    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated {en_file}")
    print("\nAdded translation keys for:")
    print("  - Appearance settings (9 keys)")
    print("  - Tasks management (36 keys)")
    print("  - Scenes settings (9 keys)")
    print("  - Notifications (11 keys)")
    print("  - Profile center (10 keys)")
    print("  - Payment (5 keys)")
    print("  - About page (5 keys)")
    print("  - Updates (6 keys)")
    print("  - Common messages (5 keys)")
    print("\nTotal: ~96 new keys")

if __name__ == '__main__':
    add_final_keys()
