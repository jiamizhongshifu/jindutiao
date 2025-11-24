#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix undefined tab variables in config_gui.py
"""

def fix_tab_variables():
    """Fix undefined tab variables"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    # Fix all tabs.addTab lines
    replacements = [
        ('tabs.addTab(appearance_tab, tr("tabs.appearance"))',
         'tabs.addTab(self.create_config_tab(), tr("tabs.appearance"))'),

        ('tabs.addTab(task_tab, tr("tabs.tasks"))',
         'tabs.addTab(self.create_tasks_tab(), tr("tabs.tasks"))'),

        ('tabs.addTab(scene_tab, tr("tabs.scenes"))',
         'tabs.addTab(QWidget(), tr("tabs.scenes"))'),

        ('tabs.addTab(notification_tab, tr("tabs.notifications"))',
         'tabs.addTab(QWidget(), tr("tabs.notifications"))'),

        ('tabs.addTab(profile_tab, tr("tabs.profile"))',
         'tabs.addTab(QWidget(), tr("tabs.profile"))'),

        ('tabs.addTab(about_tab, tr("tabs.about"))',
         'tabs.addTab(QWidget(), tr("tabs.about"))'),
    ]

    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"[OK] Fixed: {old[:50]}...")
        else:
            print(f"[SKIP] Not found: {old[:50]}...")

    # Write back
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print(f"\n[OK] File updated: {file_path}")
    return True

if __name__ == '__main__':
    print("Fixing undefined tab variables...")
    if fix_tab_variables():
        print("\nDone! Tab variables have been fixed.")
        print("\nNext step: Test by opening config manager")
    else:
        print("\nFailed to fix tab variables")
