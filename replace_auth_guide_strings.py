#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace auth guide and remaining UI strings with tr() calls
"""

import re

def replace_auth_guide_strings():
    """Replace auth guide and remaining UI strings with translation calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Track modifications
    modified_count = 0

    # 1. Replace feature names in _check_login_and_guide calls
    # "模板自动应用"
    pattern1 = r'_check_login_and_guide\("模板自动应用"\)'
    replacement1 = '_check_login_and_guide(tr("auth.features.template_auto_apply"))'
    matches1 = len(re.findall(pattern1, content))
    if matches1 > 0:
        content = re.sub(pattern1, replacement1, content)
        modified_count += matches1

    # "AI智能规划"
    pattern2 = r'_check_login_and_guide\("AI智能规划"\)'
    replacement2 = '_check_login_and_guide(tr("auth.features.ai_smart_planning"))'
    matches2 = len(re.findall(pattern2, content))
    if matches2 > 0:
        content = re.sub(pattern2, replacement2, content)
        modified_count += matches2

    # 2. Replace default parameter value
    pattern3 = r'def _check_login_and_guide\(self, feature_name: str = "此功能"\)'
    replacement3 = 'def _check_login_and_guide(self, feature_name: str = None)'
    if re.search(pattern3, content):
        content = re.sub(pattern3, replacement3, content)
        modified_count += 1

    # Add default value handling at the beginning of the function
    # Find the function and add the default handling
    function_pattern = r'(def _check_login_and_guide\(self, feature_name: str = None\) -> bool:\s+"""[^"]*""")\s+from'
    function_replacement = r'''\1
        if feature_name is None:
            feature_name = tr("auth.features.this_feature")
        from'''
    if re.search(function_pattern, content, re.DOTALL):
        content = re.sub(function_pattern, function_replacement, content, flags=re.DOTALL)
        modified_count += 1

    # 3. Replace auth guide dialog content
    # Replace the multi-line f-string in the QMessageBox.question call
    guide_pattern = r'f"💡 \{feature_name\}需要登录后才能使用。\\n\\n"\s+f"登录后您将享有：\\n"\s+f"• 免费用户：3次/天 AI智能规划\\n"\s+f"• Pro会员：20次/天 AI智能规划\\n"\s+f"• 更多高级功能和服务\\n\\n"\s+f"是否前往个人中心登录？"'

    guide_replacement = '''f"💡 {feature_name}需要登录后才能使用。\\n\\n" + \\
            tr("auth.guide.benefits_intro") + "\\n" + \\
            tr("auth.guide.free_user_quota") + "\\n" + \\
            tr("auth.guide.pro_member_quota") + "\\n" + \\
            tr("auth.guide.more_features") + "\\n\\n" + \\
            tr("auth.guide.go_to_login")'''

    if re.search(guide_pattern, content, re.DOTALL):
        content = re.sub(guide_pattern, guide_replacement, content, flags=re.DOTALL)
        modified_count += 6  # 5 guide strings + 1 f-string structure

    # 4. Replace warning dialog title
    pattern4 = r'QMessageBox\.warning\(\s+self,\s+"警告",'
    replacement4 = 'QMessageBox.warning(\n                        self,\n                        tr("common.dialog_titles.warning"),'
    matches4 = len(re.findall(pattern4, content, re.DOTALL))
    if matches4 > 0:
        content = re.sub(pattern4, replacement4, content, flags=re.DOTALL)
        modified_count += matches4

    # 5. Replace autostart failure message
    pattern5 = r'"开机自启动设置失败\\n\\n可能需要管理员权限或系统限制"'
    replacement5 = 'tr("autostart.messages.setup_failed")'
    matches5 = len(re.findall(pattern5, content))
    if matches5 > 0:
        content = re.sub(pattern5, replacement5, content)
        modified_count += matches5

    # 6. Replace dialog window titles
    # "GaiYa每日进度条"
    pattern6 = r'setWindowTitle\("GaiYa每日进度条"\)'
    replacement6 = 'setWindowTitle(tr("about.dialog_title"))'
    matches6 = len(re.findall(pattern6, content))
    if matches6 > 0:
        content = re.sub(pattern6, replacement6, content)
        modified_count += matches6

    # "致 GaiYa 会员合伙人的一封信"
    pattern7 = r'QLabel\("致 GaiYa 会员合伙人的一封信"\)'
    replacement7 = 'QLabel(tr("about.letter_title"))'
    matches7 = len(re.findall(pattern7, content))
    if matches7 > 0:
        content = re.sub(pattern7, replacement7, content)
        modified_count += matches7

    # "邀请您共同成长，共享价值"
    pattern8 = r'QLabel\("邀请您共同成长，共享价值"\)'
    replacement8 = 'QLabel(tr("about.letter_subtitle"))'
    matches8 = len(re.findall(pattern8, content))
    if matches8 > 0:
        content = re.sub(pattern8, replacement8, content)
        modified_count += matches8

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Total replacements made: {modified_count}")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Replacing auth guide and remaining UI strings...")
    replace_auth_guide_strings()
    print("Done!")
