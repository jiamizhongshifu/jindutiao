#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace all remaining 119 UI strings in config_gui.py
"""

import re

def replace_final_strings():
    """Replace all remaining UI strings"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    modified_count = 0

    # === 1. Error messages with {e} or {str(e)} ===
    error_replacements = [
        (r'"加载场景设置失败: \{e\}"', 'tr("scenes.messages.load_failed", error=e)'),
        (r'"加载通知设置失败: \{e\}"', 'tr("notifications.messages.load_failed", error=e)'),
        (r'"加载个人中心标签页失败: \{e\}"', 'tr("profile.messages.load_failed", error=e)'),
        (r'"加载关于标签页失败: \{e\}\\n\\n请检查日志文件获取详细信息"',
         'tr("about.messages.load_failed", error=e)'),
        (r'"无法保存模板:\\n\{str\(e\)\}"', 'tr("tasks.messages.template_save_failed", error=str(e))'),
        (r'"模板文件格式错误:\\n\{str\(e\)\}"', 'tr("tasks.messages.template_format_error", error=str(e))'),
        (r'"加载模板失败:\\n\{str\(e\)\}"', 'tr("tasks.messages.template_load_failed", error=str(e))'),
        (r'"无法删除模板:\\n\{str\(e\)\}"', 'tr("tasks.messages.template_delete_failed", error=str(e))'),
        (r'"模板文件不存在:\\n\{filename\}"', 'tr("tasks.messages.template_file_not_exist", filename=filename)'),
        (r'"保存失败:\\n\{str\(e\)\}"', 'tr("tasks.messages.save_failed_with_error", error=str(e))'),
        (r'"无法连接到更新服务器\\n\\n\{str\(e\)\}"', 'tr("updates.messages.cannot_connect", error=str(e))'),
        (r'"发生未知错误\\n\\n\{str\(e\)\}"', 'tr("updates.messages.unknown_error", error=str(e))'),
        (r'"二维码图片不存在\\n路径: \{qrcode_path\}"', 'tr("about.messages.qr_not_exist", path=qrcode_path)'),
    ]

    for pattern, replacement in error_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches
            print(f"  Replaced {matches}x error message: {pattern[:40]}...")

    # === 2. QGroupBox section headers ===
    groupbox_replacements = [
        (r'QGroupBox\("🔧 基本设置"\)', 'QGroupBox(tr("appearance.sections.basic_settings"))'),
        (r'QGroupBox\("🎨 颜色设置"\)', 'QGroupBox(tr("appearance.sections.color_settings"))'),
        (r'QGroupBox\("✨ 视觉效果"\)', 'QGroupBox(tr("appearance.sections.visual_effects"))'),
        (r'QGroupBox\("🤖 AI智能规划"\)', 'QGroupBox(tr("tasks.sections.ai_planning"))'),
        (r'QGroupBox\("🎨 预设主题配色"\)', 'QGroupBox(tr("tasks.sections.preset_themes"))'),
        (r'QGroupBox\("📋 预设模板"\)', 'QGroupBox(tr("tasks.sections.preset_templates"))'),
        (r'QGroupBox\("💾 我的模板"\)', 'QGroupBox(tr("tasks.sections.my_templates"))'),
        (r'QGroupBox\("🎨 可视化时间轴编辑器"\)', 'QGroupBox(tr("tasks.sections.visual_timeline"))'),
        (r'QGroupBox\("📅 模板自动应用管理"\)', 'QGroupBox(tr("tasks.sections.auto_apply_management"))'),
        (r'QGroupBox\("⚙️ 基础设置"\)', 'QGroupBox(tr("scenes.sections.basic_settings"))'),
        (r'QGroupBox\("🎬 场景选择"\)', 'QGroupBox(tr("scenes.sections.scene_selection"))'),
        (r'QGroupBox\("🛠️ 高级功能"\)', 'QGroupBox(tr("scenes.sections.advanced_features"))'),
        (r'QGroupBox\("⏰ 提醒时机"\)', 'QGroupBox(tr("notifications.sections.reminder_timing"))'),
        (r'QGroupBox\("🔔 任务开始前提醒"\)', 'QGroupBox(tr("notifications.sections.task_start_reminder"))'),
        (r'QGroupBox\("🔕 任务结束前提醒"\)', 'QGroupBox(tr("notifications.sections.task_end_reminder"))'),
        (r'QGroupBox\("🌙 免打扰时段"\)', 'QGroupBox(tr("notifications.sections.do_not_disturb"))'),
    ]

    for pattern, replacement in groupbox_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    print(f"  Replaced {sum(len(re.findall(p, content)) for p, _ in groupbox_replacements)} QGroupBox headers")

    # === 3. QPushButton buttons ===
    button_replacements = [
        (r'QPushButton\("📁 浏览"\)', 'QPushButton(tr("appearance.labels.browse"))'),
        (r'QPushButton\("🔄 刷新配额"\)', 'QPushButton(tr("tasks.buttons.refresh_quota"))'),
        (r'QPushButton\("➕ 添加任务"\)', 'QPushButton(tr("tasks.buttons.add_task"))'),
        (r'QPushButton\("📂 加载自定义模板"\)', 'QPushButton(tr("tasks.buttons.load_custom_template"))'),
        (r'QPushButton\("🗑️ 清空所有任务"\)', 'QPushButton(tr("tasks.buttons.clear_all_tasks"))'),
        (r'QPushButton\("➕ 添加规则"\)', 'QPushButton(tr("tasks.buttons.add_rule"))'),
        (r'QPushButton\("🔍 测试日期"\)', 'QPushButton(tr("tasks.buttons.test_date"))'),
        (r'QPushButton\("📂 加载"\)', 'QPushButton(tr("tasks.buttons.load"))'),
        (r'QPushButton\("🔄 刷新场景"\)', 'QPushButton(tr("scenes.buttons.refresh_scenes"))'),
        (r'QPushButton\("🎨 打开场景编辑器"\)', 'QPushButton(tr("scenes.buttons.open_scene_editor"))'),
        (r'QPushButton\("退出登录"\)', 'QPushButton(tr("profile.buttons.logout"))'),
        (r'QPushButton\("🔑 点击登录 / 注册"\)', 'QPushButton(tr("profile.buttons.login_register"))'),
        (r'QPushButton\("升级会员"\)', 'QPushButton(tr("profile.buttons.upgrade_membership"))'),
        (r'QPushButton\("成为合伙人"\)', 'QPushButton(tr("profile.buttons.become_partner"))'),
        (r'QPushButton\("确认支付"\)', 'QPushButton(tr("payment.buttons.confirm_payment"))'),
        (r'QPushButton\("立即更新"\)', 'QPushButton(tr("updates.buttons.update_now"))'),
        (r'QPushButton\("前往下载"\)', 'QPushButton(tr("updates.buttons.go_to_download"))'),
    ]

    for pattern, replacement in button_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 4. QLabel labels ===
    label_replacements = [
        (r'QLabel\("自定义:"\)', 'QLabel(tr("appearance.labels.custom"))'),
        (r'QLabel\("\(line=线条, image=图片, gif=动画\)"\)', 'QLabel(tr("appearance.labels.hint_line_image_gif"))'),
        (r'QLabel\("\(正值向右,负值向左\)"\)', 'QLabel(tr("appearance.labels.hint_horizontal"))'),
        (r'QLabel\("\(正值向上,负值向下\)"\)', 'QLabel(tr("appearance.labels.hint_vertical"))'),
        (r'QLabel\("\(100%=原速, 200%=2倍速\)"\)', 'QLabel(tr("appearance.labels.hint_speed"))'),
        (r'QLabel\("💡 用自然语言描述您的计划,AI将自动生成任务时间表"\)', 'QLabel(tr("tasks.hints.ai_description"))'),
        (r'QLabel\("描述您的计划:"\)', 'QLabel(tr("tasks.labels.describe_plan"))'),
        (r'QLabel\("配额状态: 加载中..."\)', 'QLabel(tr("tasks.labels.quota_status_loading"))'),
        (r'QLabel\("双击表格单元格可以编辑任务内容"\)', 'QLabel(tr("tasks.hints.double_click_edit"))'),
        (r'QLabel\("选择主题:"\)', 'QLabel(tr("tasks.labels.select_theme"))'),
        (r'QLabel\("配色预览:"\)', 'QLabel(tr("tasks.labels.color_preview"))'),
        (r'QLabel\("快速加载:"\)', 'QLabel(tr("tasks.labels.quick_load"))'),
        (r'QLabel\("模板加载中..."\)', 'QLabel(tr("tasks.labels.template_loading"))'),
        (r'QLabel\("💡 提示：拖动色块边缘可调整任务时长"\)', 'QLabel(tr("tasks.hints.drag_to_adjust"))'),
        (r'QLabel\("💡 为每个模板设置自动应用的日期规则，到了指定时间会自动加载对应模板"\)',
         'QLabel(tr("tasks.hints.auto_apply_description"))'),
        (r'QLabel\("当前场景:"\)', 'QLabel(tr("scenes.labels.current_scene"))'),
        (r'QLabel\("配置场景效果,让进度条更具个性化"\)', 'QLabel(tr("scenes.labels.description"))'),
        (r'QLabel\("场景编辑器可以创建和编辑自定义场景效果"\)', 'QLabel(tr("scenes.messages.editor_description"))'),
        (r'QLabel\("配置任务提醒通知,让您不会错过任何重要时刻"\)', 'QLabel(tr("notifications.labels.description"))'),
        (r'QLabel\("选择在任务开始前多久提醒\(可多选\):"\)', 'QLabel(tr("notifications.labels.select_before_start"))'),
        (r'QLabel\("选择在任务结束前多久提醒\(可多选\):"\)', 'QLabel(tr("notifications.labels.select_before_end"))'),
        (r'QLabel\("\(在此时间后不发送通知\)"\)', 'QLabel(tr("notifications.labels.hint_after_time"))'),
        (r'QLabel\("\(在此时间前不发送通知\)"\)', 'QLabel(tr("notifications.labels.hint_before_time"))'),
        (r'QLabel\("示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰"\)',
         'QLabel(tr("notifications.labels.example_time_range"))'),
        (r'QLabel\("个人中心"\)', 'QLabel(tr("profile.sections.profile_center"))'),
        (r'QLabel\("会员套餐对比"\)', 'QLabel(tr("profile.labels.membership_comparison"))'),
        (r'QLabel\("👋 欢迎使用 GaiYa 每日进度条"\)', 'QLabel(tr("profile.messages.welcome"))'),
        (r'QLabel\("登录后即可使用 AI智能规划、数据云同步等高级功能"\)', 'QLabel(tr("profile.messages.login_benefits"))'),
        (r'QLabel\("🎁 登录后享受的权益："\)', 'QLabel(tr("profile.messages.benefits_title"))'),
        (r'QLabel\("选择支付方式"\)', 'QLabel(tr("payment.labels.select_payment_method"))'),
        (r'QLabel\("请选择支付方式："\)', 'QLabel(tr("payment.labels.please_select_payment"))'),
        (r'QLabel\("等待支付"\)', 'QLabel(tr("payment.labels.waiting_payment"))'),
        (r'QLabel\("扫描二维码，直接反馈问题"\)', 'QLabel(tr("about.labels.scan_qr_feedback"))'),
        (r'QLabel\("扫一扫上面的二维码图案，加我为朋友。"\)', 'QLabel(tr("about.labels.scan_add_friend"))'),
    ]

    for pattern, replacement in label_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 5. Simple QMessageBox messages ===
    messagebox_replacements = [
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"主题管理器未初始化，请稍后再试"',
         r'\1tr("tasks.messages.theme_manager_not_initialized")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"请先选择一个主题"',
         r'\1tr("tasks.messages.please_select_theme")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"应用主题失败"',
         r'\1tr("tasks.messages.apply_theme_failed")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"已应用主题配色到任务"',
         r'\1tr("tasks.messages.theme_color_applied_to_tasks")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"请选择一个场景"',
         r'\1tr("scenes.messages.please_select_scene")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*tr\("common\.dialog_titles\.cannot_save"\),\s*)"当前没有任何任务,无法保存为模板!"',
         r'\1tr("tasks.messages.cannot_save_empty")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"请先创建自定义模板"',
         r'\1tr("tasks.messages.please_create_template_first")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"没有设置被保存"',
         r'\1tr("tasks.messages.no_settings_saved")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"测试模板匹配"',
         r'\1tr("tasks.messages.test_template_match")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"感谢您的支持！"',
         r'\1tr("profile.messages.thank_you")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"网络请求超时，请检查网络连接"',
         r'\1tr("updates.messages.network_timeout")'),
        (r'(QMessageBox\.\w+\([^,]+,\s*[^,]+,\s*)"已取消"',
         r'\1tr("updates.messages.cancelled")'),
    ]

    for pattern, replacement in messagebox_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 6. Complex messages with formatting ===
    complex_replacements = [
        (r'"所有任务已清空\\n\\n记得点击【保存所有设置】按钮来保存更改"',
         'tr("tasks.messages.all_tasks_cleared")'),
        (r'"配置和任务已保存!\\n\\n如果 Gaiya 正在运行,更改会自动生效。"',
         'tr("common.messages.config_saved")'),
    ]

    for pattern, replacement in complex_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            modified_count += matches

    # === 7. f-strings with complex variables ===
    # These need special handling

    # "邮箱：{email}  |  会员等级：{tier_name}"
    content = re.sub(
        r'f"邮箱：\{email\}  \|  会员等级：\{tier_name\}"',
        'tr("profile.labels.user_info", email=email, tier_name=tier_name)',
        content
    )

    # "已应用主题: {self.theme_manager.get_current_theme().get('name', '未知')}"
    content = re.sub(
        r'f"已应用主题: \{self\.theme_manager\.get_current_theme\(\)\.get\(\'name\', \'[^\']*\'\)\}"',
        'tr("tasks.messages.theme_applied", theme_name=self.theme_manager.get_current_theme().get(\'name\', \'\'))',
        content
    )

    # "您选择的套餐：{plan['name']} - {plan['price_cny']}{plan['period']}"
    content = re.sub(
        r'f"您选择的套餐：\{plan\[\'name\'\]\} - \{plan\[\'price_cny\'\]\}\{plan\[\'period\'\]\}"',
        'tr("payment.labels.selected_plan", plan_name=plan[\'name\'], price=plan[\'price_cny\'], period=plan[\'period\'])',
        content
    )

    # "版本 v{__version__}"
    content = re.sub(
        r'f"版本 v\{__version__\}"',
        'tr("about.labels.version", version=__version__)',
        content
    )

    # "模板 {name} 已删除"
    content = re.sub(
        r'f"模板 \{name\} 已删除"',
        'tr("tasks.messages.template_deleted", name=name)',
        content
    )

    # Write back
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print(f"\nTotal replacements: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing final UI strings in config_gui.py...")
    replace_final_strings()
    print("\nDone!")
