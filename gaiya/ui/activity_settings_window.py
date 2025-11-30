"""
行为识别设置窗口
允许用户配置App分类和行为追踪设置
"""

import logging
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QCheckBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSlider, QSpinBox, QMessageBox,
    QProgressBar, QTextEdit, QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QSignalBlocker
from PySide6.QtGui import QFont, QIcon

from gaiya.data.db_manager import db
from gaiya.services.app_category_manager import app_category_manager

logger = logging.getLogger("gaiya.ui.activity_settings_window")

class ActivitySettingsWindow(QDialog):
    """行为识别设置窗口"""

    # 信号定义
    settings_changed = Signal()
    activity_tracking_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logger

        # 窗口设置
        self.setWindowTitle("行为识别设置")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(700, 500)

        # 数据缓存
        self.app_categories: List[Dict] = []
        self.recent_apps: List[Dict] = []

        # 初始化UI
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("🔍 行为识别设置")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧：设置面板
        left_widget = self.create_settings_panel()
        splitter.addWidget(left_widget)

        # 右侧：App分类表格
        right_widget = self.create_category_table()
        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setSizes([300, 500])

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_button = QPushButton("💾 保存设置")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        reset_button = QPushButton("🔄 重置默认")
        reset_button.clicked.connect(self.reset_defaults)
        button_layout.addWidget(reset_button)

        close_button = QPushButton("✖️ 关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def create_settings_panel(self) -> QWidget:
        """创建设置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 基本设置组
        basic_group = QGroupBox("⚙️ 基本设置")
        basic_layout = QFormLayout(basic_group)

        # 启用行为识别
        self.activity_tracking_checkbox = QCheckBox("启用行为识别")
        self.activity_tracking_checkbox.toggled.connect(self.on_activity_tracking_toggled)
        basic_layout.addRow("行为识别:", self.activity_tracking_checkbox)

        # 采样间隔
        self.polling_interval_spinbox = QSpinBox()
        self.polling_interval_spinbox.setRange(1, 60)
        self.polling_interval_spinbox.setSuffix(" 秒")
        self.polling_interval_spinbox.setValue(5)
        basic_layout.addRow("采样间隔:", self.polling_interval_spinbox)

        # 最小会话时长
        self.min_session_duration_spinbox = QSpinBox()
        self.min_session_duration_spinbox.setRange(1, 300)
        self.min_session_duration_spinbox.setSuffix(" 秒")
        self.min_session_duration_spinbox.setValue(5)
        basic_layout.addRow("最小会话:", self.min_session_duration_spinbox)

        layout.addWidget(basic_group)

        # 隐私设置组
        privacy_group = QGroupBox("🔒 隐私设置")
        privacy_layout = QFormLayout(privacy_group)

        # 数据保留天数
        self.data_retention_days_spinbox = QSpinBox()
        self.data_retention_days_spinbox.setRange(7, 365)
        self.data_retention_days_spinbox.setSuffix(" 天")
        self.data_retention_days_spinbox.setValue(90)
        privacy_layout.addRow("数据保留:", self.data_retention_days_spinbox)

        # 清除历史数据按钮
        clear_data_button = QPushButton("🗑️ 清除所有历史数据")
        clear_data_button.clicked.connect(self.clear_all_data)
        clear_data_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        privacy_layout.addRow("数据清理:", clear_data_button)

        layout.addWidget(privacy_group)

        # 分类统计组
        stats_group = QGroupBox("📊 分类统计")
        stats_layout = QVBoxLayout(stats_group)

        # 分类统计显示
        self.category_stats_labels = {}
        for category in ["PRODUCTIVE", "LEISURE", "NEUTRAL", "UNKNOWN", "IGNORED"]:
            label = QLabel(f"{category}: 0")
            self.category_stats_labels[category] = label
            stats_layout.addWidget(label)

        layout.addWidget(stats_group)

        # 帮助信息
        help_group = QGroupBox("💡 使用说明")
        help_layout = QVBoxLayout(help_group)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        help_text.setPlainText(
            "• 行为识别会记录您在电脑上使用各个应用的时间\n"
            "• 您可以自定义每个应用的分类（生产力/摸鱼/中性）\n"
            "• 被标记为\"忽略\"的应用将不会记录数据\n"
            "• 数据仅存储在本地，不会上传到云端\n"
            "• 建议定期清理历史数据以节省存储空间"
        )
        help_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        help_layout.addWidget(help_text)

        layout.addWidget(help_group)
        layout.addStretch()

        return widget

    def create_category_table(self) -> QWidget:
        """创建App分类表格"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标题
        table_title = QLabel("📱 应用分类管理")
        table_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        layout.addWidget(table_title)

        # 表格
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(4)
        self.category_table.setHorizontalHeaderLabels(["应用名称", "当前分类", "忽略统计", "操作"])

        # 设置表格样式
        header = self.category_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.category_table.setAlternatingRowColors(True)
        self.category_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.category_table)

        # 表格操作按钮
        table_buttons_layout = QHBoxLayout()

        refresh_button = QPushButton("🔄 刷新列表")
        refresh_button.clicked.connect(self.refresh_category_table)
        table_buttons_layout.addWidget(refresh_button)

        add_button = QPushButton("➕ 添加应用")
        add_button.clicked.connect(self.add_app_category)
        table_buttons_layout.addWidget(add_button)

        import_defaults_button = QPushButton("📥 导入默认分类")
        import_defaults_button.clicked.connect(self.import_default_categories)
        table_buttons_layout.addWidget(import_defaults_button)

        table_buttons_layout.addStretch()

        layout.addLayout(table_buttons_layout)

        return widget

    def load_data(self):
        """加载数据"""
        try:
            # 加载App分类数据
            self.app_categories = app_category_manager.get_all_categories()
            self.refresh_category_table()

            # 加载分类统计
            self.update_category_stats()

            # 加载行为识别配置
            self.load_tracking_settings()

            self.logger.info("已加载行为识别设置数据")
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")

    def _get_parent_config(self):
        parent = self.parent()
        if parent and hasattr(parent, 'config'):
            return parent.config
        return None

    def load_tracking_settings(self):
        """根据父窗口配置更新UI控件"""
        config = self._get_parent_config()
        if not config:
            return

        settings = config.get('activity_tracking', {})
        with QSignalBlocker(self.activity_tracking_checkbox):
            self.activity_tracking_checkbox.setChecked(settings.get('enabled', False))
        self.polling_interval_spinbox.setValue(int(settings.get('polling_interval', 5)))
        self.min_session_duration_spinbox.setValue(int(settings.get('min_session_duration', 5)))
        self.data_retention_days_spinbox.setValue(int(settings.get('data_retention_days', 90)))

    def refresh_category_table(self):
        """刷新分类表格"""
        try:
            self.category_table.setRowCount(len(self.app_categories))

            for row, app_data in enumerate(self.app_categories):
                # 应用名称
                self.category_table.setItem(row, 0, QTableWidgetItem(app_data['process_name']))

                # 当前分类
                category_combo = QComboBox()
                category_combo.addItems(["PRODUCTIVE", "LEISURE", "NEUTRAL", "UNKNOWN"])
                current_category = app_data.get('category', 'UNKNOWN')
                category_combo.setCurrentText(current_category)
                category_combo.currentTextChanged.connect(lambda text, r=row: self.on_category_changed(r, text))
                self.category_table.setCellWidget(row, 1, category_combo)

                # 忽略统计
                ignore_checkbox = QCheckBox()
                ignore_checkbox.setChecked(app_data.get('is_ignored', False))
                ignore_checkbox.toggled.connect(lambda checked, r=row: self.on_ignore_toggled(r, checked))
                self.category_table.setCellWidget(row, 2, ignore_checkbox)

                # 操作按钮
                button_layout = QHBoxLayout()
                button_layout.setContentsMargins(5, 5, 5, 5)

                remove_button = QPushButton("❌")
                remove_button.setFixedSize(25, 25)
                remove_button.clicked.connect(lambda _, r=row: self.remove_app_category(r))
                button_layout.addWidget(remove_button)

                button_widget = QWidget()
                button_widget.setLayout(button_layout)
                self.category_table.setCellWidget(row, 3, button_widget)

        except Exception as e:
            self.logger.error(f"刷新分类表格失败: {e}")

    def update_category_stats(self):
        """更新分类统计"""
        try:
            stats = app_category_manager.get_category_stats()
            for category, count in stats.items():
                if category in self.category_stats_labels:
                    self.category_stats_labels[category].setText(f"{category}: {count}")
        except Exception as e:
            self.logger.error(f"更新分类统计失败: {e}")

    def on_activity_tracking_toggled(self, checked: bool):
        """处理行为识别开关"""
        self.activity_tracking_toggled.emit(checked)

    def on_category_changed(self, row: int, category: str):
        """处理分类变更"""
        try:
            if row < len(self.app_categories):
                app_data = self.app_categories[row]
                process_name = app_data['process_name']
                is_ignored = app_data.get('is_ignored', False)

                app_category_manager.set_app_category(process_name, category, is_ignored)
                app_data['category'] = category

                self.update_category_stats()
                self.settings_changed.emit()

        except Exception as e:
            self.logger.error(f"更新分类失败: {e}")

    def on_ignore_toggled(self, row: int, checked: bool):
        """处理忽略开关变更"""
        try:
            if row < len(self.app_categories):
                app_data = self.app_categories[row]
                process_name = app_data['process_name']
                category = app_data.get('category', 'UNKNOWN')

                app_category_manager.set_app_category(process_name, category, checked)
                app_data['is_ignored'] = checked

                self.update_category_stats()
                self.settings_changed.emit()

        except Exception as e:
            self.logger.error(f"更新忽略设置失败: {e}")

    def add_app_category(self):
        """添加应用分类"""
        # 这里可以弹出一个对话框让用户输入应用名称
        # 暂时使用简单的方式
        QMessageBox.information(self, "提示", "请在右侧表格中直接编辑应用分类")

    def remove_app_category(self, row: int):
        """移除应用分类"""
        try:
            if row < len(self.app_categories):
                app_data = self.app_categories[row]
                reply = QMessageBox.question(
                    self, "确认删除",
                    f"确定要删除应用 \"{app_data['process_name']}\" 的分类设置吗？",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # 这里需要在数据库中删除记录
                    # 暂时只从列表中移除
                    self.app_categories.pop(row)
                    self.refresh_category_table()
                    self.settings_changed.emit()

        except Exception as e:
            self.logger.error(f"删除应用分类失败: {e}")

    def import_default_categories(self):
        """导入默认分类"""
        try:
            app_category_manager.import_default_categories()
            self.load_data()
            QMessageBox.information(self, "成功", "已导入默认应用分类")
        except Exception as e:
            self.logger.error(f"导入默认分类失败: {e}")
            QMessageBox.critical(self, "错误", f"导入默认分类失败: {e}")

    def reset_defaults(self):
        """重置默认设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有设置为默认值吗？这将清除所有自定义分类。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                app_category_manager.clear_all_data()
                app_category_manager.import_default_categories()
                self.load_data()
                QMessageBox.information(self, "成功", "已重置为默认设置")
            except Exception as e:
                self.logger.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "错误", f"重置设置失败: {e}")

    def clear_all_data(self):
        """清除所有历史数据"""
        reply = QMessageBox.question(
            self, "确认清除",
            "确定要清除所有历史行为数据吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                db.clear_activity_data()
                QMessageBox.information(self, "成功", "已清除所有历史数据")
            except Exception as e:
                self.logger.error(f"清除数据失败: {e}")
                QMessageBox.critical(self, "错误", f"清除数据失败: {e}")

    def save_settings(self):
        """保存设置"""
        try:
            config = self._get_parent_config()
            if not config:
                QMessageBox.warning(self, "提示", "无法获取配置文件，设置未保存。")
                return

            tracking_config = config.setdefault('activity_tracking', {})
            retention_days = self.data_retention_days_spinbox.value()

            tracking_config.update({
                'enabled': self.activity_tracking_checkbox.isChecked(),
                'polling_interval': self.polling_interval_spinbox.value(),
                'min_session_duration': self.min_session_duration_spinbox.value(),
                'data_retention_days': retention_days
            })

            parent = self.parent()
            if parent and hasattr(parent, 'init_activity_tracker'):
                # 保存配置并应用新的追踪参数
                parent.save_config()
                parent.init_activity_tracker()

            try:
                db.cleanup_old_data(retention_days)
            except Exception as cleanup_error:
                self.logger.error(f"按保留策略清理数据失败: {cleanup_error}")

            self.settings_changed.emit()
            QMessageBox.information(self, "成功", "设置已保存")
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")

    def get_settings(self) -> Dict:
        """获取当前设置"""
        return {
            'activity_tracking_enabled': self.activity_tracking_checkbox.isChecked(),
            'polling_interval': self.polling_interval_spinbox.value(),
            'min_session_duration': self.min_session_duration_spinbox.value(),
            'data_retention_days': self.data_retention_days_spinbox.value()
        }

    def set_settings(self, settings: Dict):
        """设置当前配置"""
        self.activity_tracking_checkbox.setChecked(settings.get('activity_tracking_enabled', False))
        self.polling_interval_spinbox.setValue(settings.get('polling_interval', 5))
        self.min_session_duration_spinbox.setValue(settings.get('min_session_duration', 5))
        self.data_retention_days_spinbox.setValue(settings.get('data_retention_days', 90))
