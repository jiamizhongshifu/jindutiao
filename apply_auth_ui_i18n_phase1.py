#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply i18n to auth_ui.py - Phase 1: Simple replacements
处理简单的单行字符串替换
"""

import re

def apply_phase1_replacements():
    """第一阶段：处理简单的单行替换"""

    with open('gaiya/ui/auth_ui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 需要导入tr函数
    # 检查是否已经导入
    if 'from i18n.translator import tr' not in content:
        # 在AuthClient导入后添加tr导入
        content = content.replace(
            'from gaiya.core.auth_client import AuthClient',
            'from gaiya.core.auth_client import AuthClient\nfrom i18n.translator import tr'
        )

    replacements_made = []
    replacements_skipped = []

    # 定义简单替换（单行，无复杂逻辑）
    replacements = [
        # 窗口标题和欢迎信息
        ('        self.setWindowTitle("GaiYa - 账户登录")',
         '        self.setWindowTitle(tr("auth.window_title"))',
         49),

        ('        title_label = QLabel("欢迎使用 GaiYa")',
         '        title_label = QLabel(tr("auth.welcome"))',
         59),

        ('        subtitle_label = QLabel("每日进度条 - 让时间可视化")',
         '        subtitle_label = QLabel(tr("auth.subtitle"))',
         68),

        ('        info_label = QLabel("注册即表示同意服务条款和隐私政策")',
         '        info_label = QLabel(tr("auth.terms_notice"))',
         92),

        # 登录表单字段（第一次出现 - signin页面）
        ('        email_label = QLabel("邮箱地址")',
         '        email_label = QLabel(tr("auth.email_label"))',
         106),

        ('        self.signin_email = QLineEdit()\n        self.signin_email.setPlaceholderText("请输入邮箱")',
         '        self.signin_email = QLineEdit()\n        self.signin_email.setPlaceholderText(tr("auth.email_placeholder"))',
         107),

        ('        password_label = QLabel("密码")',
         '        password_label = QLabel(tr("auth.password_label"))',
         112),

        ('        self.signin_password = QLineEdit()\n        self.signin_password.setPlaceholderText("请输入密码")',
         '        self.signin_password = QLineEdit()\n        self.signin_password.setPlaceholderText(tr("auth.password_placeholder"))',
         113),

        # 记住登录和登录按钮
        ('        remember_checkbox = QCheckBox("记住登录状态")',
         '        remember_checkbox = QCheckBox(tr("auth.signin.remember_me"))',
         119),

        ('        signin_btn = QPushButton("登录")',
         '        signin_btn = QPushButton(tr("auth.signin.btn_login"))',
         123),

        # 忘记密码链接
        ('        forgot_link = QPushButton("忘记密码？")',
         '        forgot_link = QPushButton(tr("auth.signin.forgot_password"))',
         147),

        # 注册链接
        ('        signup_link = QPushButton("注册账号 >")',
         '        signup_link = QPushButton(tr("auth.signup.link_to_register"))',
         153),

        # 注册表单字段（第二次出现 - signup页面）
        ('        email_label = QLabel("邮箱地址")',
         '        email_label = QLabel(tr("auth.email_label"))',
         196),

        ('        self.signup_email = QLineEdit()\n        self.signup_email.setPlaceholderText("请输入邮箱")',
         '        self.signup_email = QLineEdit()\n        self.signup_email.setPlaceholderText(tr("auth.email_placeholder"))',
         197),

        ('        password_label = QLabel("密码")',
         '        password_label = QLabel(tr("auth.password_label"))',
         202),

        ('        self.signup_password = QLineEdit()\n        self.signup_password.setPlaceholderText("至少6个字符")',
         '        self.signup_password = QLineEdit()\n        self.signup_password.setPlaceholderText(tr("auth.password_hint"))',
         203),

        # 确认密码
        ('        confirm_label = QLabel("确认密码")',
         '        confirm_label = QLabel(tr("auth.confirm_password_label"))',
         209),

        ('        self.signup_confirm = QLineEdit()\n        self.signup_confirm.setPlaceholderText("请再次输入密码")',
         '        self.signup_confirm = QLineEdit()\n        self.signup_confirm.setPlaceholderText(tr("auth.confirm_password_placeholder"))',
         210),

        # 注册按钮
        ('        signup_btn = QPushButton("注册")',
         '        signup_btn = QPushButton(tr("auth.signup.btn_register"))',
         216),

        # 返回登录链接
        ('        back_link = QPushButton("< 返回登录")',
         '        back_link = QPushButton(tr("auth.signup.back_to_login"))',
         240),

        # 微信登录文本
        ('        instruction_label = QLabel("请使用微信扫码登录")',
         '        instruction_label = QLabel(tr("auth.wechat.scan_prompt"))',
         542),

        ('        self.wechat_status_label = QLabel("等待扫码...")',
         '        self.wechat_status_label = QLabel(tr("auth.wechat.waiting_scan"))',
         574),

        ('        switch_link = QPushButton("使用邮箱登录 >")',
         '        switch_link = QPushButton(tr("auth.switch_to_email"))',
         519),

        ('        switch_link = QPushButton("使用邮箱登录 >")',
         '        switch_link = QPushButton(tr("auth.switch_to_email"))',
         589),
    ]

    # 应用每个替换
    for old, new, line_num in replacements:
        if old in content:
            content = content.replace(old, new, 1)  # 只替换第一次出现
            replacements_made.append((line_num, old[:50]))
        else:
            replacements_skipped.append((line_num, old[:50]))

    # 写回文件
    with open('gaiya/ui/auth_ui.py', 'w', encoding='utf-8') as f:
        f.write(content)

    # 生成报告
    with open('auth_ui_i18n_phase1_log.txt', 'w', encoding='utf-8') as f:
        f.write("=== auth_ui.py Phase 1 Replacement Report ===\n\n")
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

    print(f"Phase 1 complete!")
    print(f"Successfully replaced: {len(replacements_made)}/{len(replacements)}")
    print(f"Skipped: {len(replacements_skipped)}")
    print(f"Check auth_ui_i18n_phase1_log.txt for details")

if __name__ == '__main__':
    apply_phase1_replacements()
