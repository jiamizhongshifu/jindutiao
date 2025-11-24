#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix the auth guide f-string that has literal newlines
"""

def fix_auth_guide_fstring():
    """Fix the broken f-string in auth guide dialog"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find and fix the broken f-string (around line 3365)
    for i in range(len(lines)):
        # Look for the line with f"💡 {feature_name}需要登录后才能使用。
        if 'f"💡 {feature_name}需要登录后才能使用' in lines[i]:
            # Replace the broken f-string and following lines
            # Line 3365: f"💡 {feature_name}需要登录后才能使用。\n\n" + \
            lines[i] = '            f"💡 {feature_name}需要登录后才能使用。\\n\\n" + \\\n'

            # Line 3367-3368: tr("auth.guide.benefits_intro") + "\n" + \
            if i+2 < len(lines) and 'tr("auth.guide.benefits_intro")' in lines[i+2]:
                lines[i+2] = '            tr("auth.guide.benefits_intro") + "\\n" + \\\n'

            # Line 3369-3370: tr("auth.guide.free_user_quota") + "\n" + \
            if i+4 < len(lines) and 'tr("auth.guide.free_user_quota")' in lines[i+4]:
                lines[i+4] = '            tr("auth.guide.free_user_quota") + "\\n" + \\\n'

            # Line 3371-3372: tr("auth.guide.pro_member_quota") + "\n" + \
            if i+6 < len(lines) and 'tr("auth.guide.pro_member_quota")' in lines[i+6]:
                lines[i+6] = '            tr("auth.guide.pro_member_quota") + "\\n" + \\\n'

            # Line 3373-3376: tr("auth.guide.more_features") + "\n\n" + \
            if i+8 < len(lines) and 'tr("auth.guide.more_features")' in lines[i+8]:
                lines[i+8] = '            tr("auth.guide.more_features") + "\\n\\n" + \\\n'

            break

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("Fixed auth guide f-string!")

if __name__ == '__main__':
    fix_auth_guide_fstring()
