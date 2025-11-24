#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add language selector to config_gui.py appearance tab
Version 2: Use regex for more reliable insertion
"""

import re

def add_language_selector():
    """Add language selector UI component"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    # Language selector code to insert (with proper indentation)
    language_selector_code = '''        # 语言设置组 - Language Settings
        language_group = QGroupBox(tr("settings.language.section_title"))
        language_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        language_layout = QFormLayout()
        language_layout.setVerticalSpacing(12)
        language_layout.setHorizontalSpacing(10)

        # 语言选择下拉框
        from i18n.translator import get_language, set_language, get_available_languages

        self.language_combo = QComboBox()
        self.language_combo.setStyleSheet(StyleManager.input_select())

        # 添加可用语言
        available_langs = get_available_languages()
        current_lang = get_language()

        for lang_code in available_langs:
            # 显示本地化的语言名称
            lang_name = tr(f"settings.language.{lang_code}")
            self.language_combo.addItem(lang_name, lang_code)

            # 设置当前选中项
            if lang_code == current_lang:
                self.language_combo.setCurrentIndex(self.language_combo.count() - 1)

        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        language_layout.addRow(tr("settings.language.select_language"), self.language_combo)

        language_group.setLayout(language_layout)
        layout.addWidget(language_group)

'''

    # Use regex to find insertion point (before basic_group)
    # Match the comment line and the basic_group line
    pattern = re.compile(
        r'(        # [^\n]*基本设置[^\n]*\n        basic_group = QGroupBox)',
        re.MULTILINE
    )

    match = pattern.search(content)
    if match:
        # Insert language selector code before the matched pattern
        content = pattern.sub(language_selector_code + match.group(1), content)
        print("[OK] Language selector code inserted")
    else:
        print("[ERROR] Could not find insertion point using regex")
        print("Trying direct string search...")

        # Try direct string match
        if 'basic_group = QGroupBox(tr("appearance.sections.basic_settings"))' in content:
            print("Found basic_group line")
            # Insert before this line
            content = content.replace(
                '        # ',
                language_selector_code + '        # ',
                1  # Only replace first occurrence in appearance section
            )
            print("[OK] Inserted using fallback method")
        else:
            return False

    # Now add the language change handler method
    handler_code = '''
    def _on_language_changed(self, index):
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
            self.config['language'] = lang_code

'''

    # Find save_config method to insert handler before it
    handler_pattern = r'(    def save_config\()'
    if re.search(handler_pattern, content):
        content = re.sub(handler_pattern, handler_code + r'\1', content)
        print("[OK] Language change handler added")
    else:
        print("[WARN] Could not find save_config method")

    # Write back
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print(f"[OK] File updated: {file_path}")
    return True

if __name__ == '__main__':
    print("Adding language selector to config_gui.py (v2)...")
    if add_language_selector():
        print("\nDone! Language selector has been added.")
        print("\nNext steps:")
        print("1. Test language switching in the application")
        print("2. Verify syntax: python -m py_compile config_gui.py")
    else:
        print("\nFailed to add language selector")
