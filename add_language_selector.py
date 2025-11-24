#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在配置界面的外观tab添加语言选择器
"""

def add_language_selector():
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找"开机自启动"选项的位置，在它后面添加语言选择器
    autostart_section = '''        # 开机自启动
        autostart_container = QWidget()
        autostart_layout = QHBoxLayout(autostart_container)
        autostart_layout.setContentsMargins(0, 0, 0, 0)

        self.autostart_check = QCheckBox("开机自动启动")'''

    if autostart_section not in content:
        print("Could not find autostart section")
        return False

    # 在开机自启动之前添加语言选择器
    language_selector_code = '''        # 语言选择
        language_container = QWidget()
        language_layout = QHBoxLayout(language_container)
        language_layout.setContentsMargins(0, 0, 0, 0)

        self.language_combo = QComboBox()
        self.language_combo.setStyleSheet(StyleManager.input_dropdown())
        self.language_combo.addItem(tr("config.language_zh_cn"), "zh_CN")
        self.language_combo.addItem(tr("config.language_en_us"), "en_US")

        # 设置当前语言
        current_lang = self.config.get('language', 'zh_CN') if self.config else 'zh_CN'
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()

        basic_layout.addRow(tr("config.language") + ":", language_container)

        '''

    # 插入语言选择器代码
    content = content.replace(autostart_section, language_selector_code + autostart_section)

    # 添加语言切换处理函数（在类的某个方法之后）
    # 查找一个合适的插入点 - 在save_config方法之前
    marker = '    def save_config(self):'
    if marker in content:
        handler_code = '''    def on_language_changed(self, index):
        """处理语言切换"""
        if not self.config:
            return

        new_lang = self.language_combo.currentData()
        old_lang = self.config.get('language', 'zh_CN')

        if new_lang == old_lang:
            return

        # 更新配置
        self.config['language'] = new_lang

        # 保存配置
        try:
            import json
            from gaiya.utils import path_utils
            app_dir = path_utils.get_app_dir()
            config_path = app_dir / 'config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)

            # 提示用户需要重启应用
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                tr("config.restart_required_title", fallback="Restart Required"),
                tr("config.restart_required_message", fallback="Language change will take effect after restarting the application.")
            )
        except Exception as e:
            logging.error(f"Failed to save language setting: {e}")

    '''
        content = content.replace(marker, handler_code + marker)

    # 写回文件
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Language selector added successfully!")
    return True

if __name__ == '__main__':
    add_language_selector()
