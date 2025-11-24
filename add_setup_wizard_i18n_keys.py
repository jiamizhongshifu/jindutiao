#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 setup_wizard.py 的翻译键到 i18n 文件
"""

import json

def add_setup_wizard_keys():
    """添加setup_wizard的翻译键"""

    # 定义所有翻译键（中文和英文）
    wizard_keys_zh = {
        "wizard": {
            "window": {
                "title": "快速配置"
            },
            "template_page": {
                "title": "选择任务模板",
                "subtitle": "为你推荐3个热门模板，选择最适合的一个即可快速开始",
                "ai_option_label": "或者，让AI根据你的需求智能生成任务：",
                "ai_button": "🤖 AI智能生成任务",
                "ai_note": "💡 点击后将关闭向导，打开配置界面使用AI生成"
            },
            "templates": {
                "work_weekday": {
                    "name": "📊 工作日模板",
                    "description": "适合上班族。包含：通勤、会议、工作、午休、晚餐、学习等典型工作日任务。"
                },
                "student": {
                    "name": "🎓 学生模板",
                    "description": "适合学生党。包含：早读、上课、自习、运动、社团活动等校园生活任务。"
                },
                "freelancer": {
                    "name": "💼 自由职业模板",
                    "description": "适合自由工作者。包含：客户沟通、项目开发、创作时间、休息等灵活时间安排。"
                }
            },
            "complete_page": {
                "title": "配置完成！🎉",
                "subtitle": "你已成功完成基础配置，现在可以开始使用 GaiYa 了",
                "summary_title": "✅ 已完成的配置：",
                "selected_template": "已选择任务模板: {template_name}",
                "position_label": "进度条位置: 屏幕底部（固定）",
                "suggestions_title": "下一步建议:",
                "tips_title": "💡 快速上手提示："
            },
            "suggestions": {
                "customize_tasks": "• 打开配置界面自定义任务时间和颜色",
                "set_reminders": "• 设置任务提醒时间",
                "choose_theme": "• 选择喜欢的主题配色"
            },
            "tips": {
                "right_click_config": "• 右键点击进度条可以打开配置界面",
                "tray_menu": "• 系统托盘图标右键菜单提供快捷操作",
                "double_click_toggle": "• 支持快捷键：双击隐藏/显示进度条",
                "free_quota": "• 免费用户每天有3次AI任务规划配额"
            }
        }
    }

    wizard_keys_en = {
        "wizard": {
            "window": {
                "title": "Quick Setup"
            },
            "template_page": {
                "title": "Select Task Template",
                "subtitle": "We recommend 3 popular templates, choose the one that suits you best to get started quickly",
                "ai_option_label": "Or, let AI intelligently generate tasks based on your needs:",
                "ai_button": "🤖 AI Smart Task Generation",
                "ai_note": "💡 Click to close the wizard and open the configuration interface to use AI generation"
            },
            "templates": {
                "work_weekday": {
                    "name": "📊 Workday Template",
                    "description": "Suitable for office workers. Includes: commute, meetings, work, lunch break, dinner, study and other typical workday tasks."
                },
                "student": {
                    "name": "🎓 Student Template",
                    "description": "Suitable for students. Includes: morning reading, classes, self-study, sports, club activities and other campus life tasks."
                },
                "freelancer": {
                    "name": "💼 Freelancer Template",
                    "description": "Suitable for freelancers. Includes: client communication, project development, creative time, rest and other flexible time arrangements."
                }
            },
            "complete_page": {
                "title": "Configuration Complete! 🎉",
                "subtitle": "You have successfully completed the basic configuration, now you can start using GaiYa",
                "summary_title": "✅ Completed Configuration:",
                "selected_template": "Selected Task Template: {template_name}",
                "position_label": "Progress Bar Position: Bottom of Screen (Fixed)",
                "suggestions_title": "Next Steps:",
                "tips_title": "💡 Quick Start Tips:"
            },
            "suggestions": {
                "customize_tasks": "• Open the configuration interface to customize task time and colors",
                "set_reminders": "• Set task reminder time",
                "choose_theme": "• Choose your favorite theme color"
            },
            "tips": {
                "right_click_config": "• Right-click the progress bar to open the configuration interface",
                "tray_menu": "• Right-click menu on the system tray icon provides quick actions",
                "double_click_toggle": "• Shortcut support: Double-click to hide/show progress bar",
                "free_quota": "• Free users have 3 AI task planning quotas per day"
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加wizard命名空间
    zh_cn['wizard'] = wizard_keys_zh['wizard']
    en_us['wizard'] = wizard_keys_en['wizard']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计wizard命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    key_count = count_keys(wizard_keys_zh['wizard'])
    print(f"新增 wizard 命名空间翻译键: {key_count} 个")

if __name__ == '__main__':
    add_setup_wizard_keys()
