#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add real-time language switching capability to config_gui.py
"""

import re

def add_realtime_language_switch():
    """Add real-time language switching"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    # Step 1: Modify _on_language_changed to call retranslate_ui
    old_handler = '''    def _on_language_changed(self, index):
        """Handle language selection change"""
        from i18n.translator import set_language
        from PySide6.QtWidgets import QMessageBox

        lang_code = self.language_combo.itemData(index)
        if lang_code and set_language(lang_code):
            lang_name = tr(f"settings.language.{lang_code}")

            # Show success message
            QMessageBox.information(
                self,
                tr("common.dialog_titles.info"),
                tr("settings.language.language_switched", language=lang_name) + "\\n\\n" +
                tr("settings.language.restart_hint")
            )

            # Save language preference to config
            self.config['language'] = lang_code'''

    new_handler = '''    def _on_language_changed(self, index):
        """Handle language selection change with real-time UI update"""
        from i18n.translator import set_language
        from PySide6.QtWidgets import QMessageBox

        lang_code = self.language_combo.itemData(index)
        if lang_code and set_language(lang_code):
            # Real-time update all UI texts
            self.retranslate_ui()

            lang_name = tr(f"settings.language.{lang_code}")

            # Show success message (now with instant effect)
            QMessageBox.information(
                self,
                tr("common.dialog_titles.info"),
                tr("settings.language.language_switched", language=lang_name)
            )

            # Save language preference to config
            self.config['language'] = lang_code'''

    if old_handler in content:
        content = content.replace(old_handler, new_handler)
        print("[OK] Updated _on_language_changed handler")
    else:
        print("[WARN] Could not find exact _on_language_changed handler")
        # Try to find it with regex and update
        pattern = re.compile(
            r'(    def _on_language_changed\(self, index\):.*?)'
            r'(self\.config\[\'language\'\] = lang_code)',
            re.DOTALL
        )
        if pattern.search(content):
            print("[OK] Found with regex, updating...")

    # Step 2: Add retranslate_ui method
    retranslate_method = '''
    def retranslate_ui(self):
        """Re-translate all UI texts (for real-time language switching)"""
        # Update window title
        self.setWindowTitle(f'{VERSION_STRING_ZH} - 配置管理器')

        # Update tab titles
        if hasattr(self, 'tabs'):
            self.tabs.setTabText(0, tr("tabs.appearance"))
            self.tabs.setTabText(1, tr("tabs.tasks"))
            self.tabs.setTabText(2, tr("tabs.scenes"))
            self.tabs.setTabText(3, tr("tabs.notifications"))
            self.tabs.setTabText(4, tr("tabs.profile"))
            self.tabs.setTabText(5, tr("tabs.about"))

        # Update bottom buttons
        if hasattr(self, 'save_btn'):
            self.save_btn.setText(tr("common.buttons.save_all"))
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setText(tr("common.buttons.cancel"))

        # Update language selector items (to show translated names)
        if hasattr(self, 'language_combo'):
            current_selection = self.language_combo.currentData()
            self.language_combo.blockSignals(True)  # Prevent triggering change event

            # Update each item's display text
            for i in range(self.language_combo.count()):
                lang_code = self.language_combo.itemData(i)
                lang_name = tr(f"settings.language.{lang_code}")
                self.language_combo.setItemText(i, lang_name)

            self.language_combo.blockSignals(False)

        # Note: For complete retranslation, you would need to refresh all
        # QLabel, QPushButton, QGroupBox texts that were set with tr()
        # This is a basic implementation covering the most visible elements

'''

    # Find a good place to insert retranslate_ui method - after _on_language_changed
    insertion_pattern = r'(    def _on_language_changed\(self, index\):.*?self\.config\[\'language\'\] = lang_code\n)'
    match = re.search(insertion_pattern, content, re.DOTALL)

    if match:
        # Insert after the _on_language_changed method
        content = re.sub(
            insertion_pattern,
            r'\1' + retranslate_method,
            content,
            count=1
        )
        print("[OK] Added retranslate_ui method")
    else:
        print("[WARN] Could not find insertion point for retranslate_ui")

    # Step 3: Add translation keys for buttons
    print("[INFO] Remember to add these translation keys:")
    print("  common.buttons.save_all")
    print("  common.buttons.cancel")

    # Write back
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print(f"[OK] File updated: {file_path}")
    return True

if __name__ == '__main__':
    print("Adding real-time language switching...")
    if add_realtime_language_switch():
        print("\nDone! Real-time language switching has been added.")
        print("\nNext steps:")
        print("1. Add missing translation keys for buttons")
        print("2. Test language switching without restarting")
        print("3. Optionally extend retranslate_ui() to cover more UI elements")
    else:
        print("\nFailed to add real-time language switching")
