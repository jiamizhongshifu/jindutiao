"""
样式管理器 - 提供统一的Qt组件样式

本模块基于 theme_light.py 的颜色规范，为所有Qt组件提供统一的样式表（QSS）。
所有样式遵循MacOS极简风格。

使用方法：
    from gaiya.ui.style_manager import StyleManager

    # 应用到整个应用
    app.setStyleSheet(StyleManager.get_app_stylesheet())

    # 应用到单个组件
    button.setStyleSheet(StyleManager.button_minimal())

设计原则：
1. 极简主义：优先使用黑白灰，仅主要操作使用彩色
2. 一致性：所有同类组件保持统一样式
3. 可访问性：确保足够的对比度和点击区域
"""

from gaiya.ui.theme_light import LightTheme as Theme


class StyleManager:
    """样式管理器 - MacOS极简风格

    提供所有Qt组件的统一样式表（QSS）。
    """

    # ============================================================
    # 应用级样式
    # ============================================================
    @staticmethod
    def get_app_stylesheet() -> str:
        """
        获取应用级全局样式表

        包含：
        - 窗口基础背景
        - 全局字体大小
        - Tab标签样式
        - 滚动条样式

        Returns:
            完整的应用级QSS字符串
        """
        return f"""
            /* ========================================
               全局窗口样式
               ======================================== */
            QMainWindow, QDialog, QWidget {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                font-size: {Theme.FONT_BODY}px;
            }}

            /* ========================================
               Tab标签（QTabWidget）
               ======================================== */
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_SMALL}px;
                background-color: {Theme.BG_PRIMARY};
                padding: 5px;
            }}

            QTabBar::tab {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-bottom: none;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: {Theme.RADIUS_SMALL}px;
                border-top-right-radius: {Theme.RADIUS_SMALL}px;
            }}

            QTabBar::tab:selected {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border-bottom: 2px solid {Theme.ACCENT_GREEN};
                font-weight: bold;
            }}

            QTabBar::tab:hover:!selected {{
                background-color: {Theme.BG_HOVER};
            }}

            /* ========================================
               分组框（QGroupBox）
               ======================================== */
            QGroupBox {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_MEDIUM}px;
                margin-top: 12px;
                padding: 15px;
                font-size: {Theme.FONT_BODY}px;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {Theme.TEXT_SECONDARY};
                font-size: {Theme.FONT_SUBTITLE}px;
                font-weight: bold;
            }}

            /* ========================================
               滚动条（QScrollBar）
               ======================================== */
            QScrollBar:vertical {{
                border: none;
                background: {Theme.BG_SECONDARY};
                width: 10px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {Theme.BORDER_NORMAL};
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {Theme.BORDER_HOVER};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar:horizontal {{
                border: none;
                background: {Theme.BG_SECONDARY};
                height: 10px;
                margin: 0px;
            }}

            QScrollBar::handle:horizontal {{
                background: {Theme.BORDER_NORMAL};
                min-width: 20px;
                border-radius: 5px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background: {Theme.BORDER_HOVER};
            }}

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

    # ============================================================
    # 按钮样式（MacOS极简风格）
    # ============================================================
    @staticmethod
    def button_minimal() -> str:
        """
        极简按钮（MacOS风格）- 白底黑边框

        特点：
        - 白色背景 + 细黑边框
        - 悬停时背景变浅灰
        - 圆角6px（MacOS标准）

        适用场景：
        - 普通操作（取消、关闭、刷新等）
        - 次要操作

        Returns:
            按钮QSS字符串
        """
        return f"""
            QPushButton {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_NORMAL};
                border-radius: {Theme.RADIUS_MEDIUM}px;
                padding: 6px 16px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
                border: 1px solid {Theme.BORDER_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.BG_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {Theme.BG_DISABLED};
                color: {Theme.TEXT_DISABLED};
                border: 1px solid {Theme.BORDER_LIGHT};
            }}
        """

    @staticmethod
    def button_primary() -> str:
        """
        主要按钮 - 绿色填充（唯一使用彩色的按钮）

        特点：
        - 绿色背景（#4CAF50）
        - 白色文字
        - 加粗字体
        - 圆角6px

        适用场景：
        - 保存操作
        - 确认操作
        - 主要提交操作

        Returns:
            主要按钮QSS字符串
        """
        return f"""
            QPushButton {{
                background-color: {Theme.ACCENT_GREEN};
                color: {Theme.TEXT_WHITE};
                border: none;
                border-radius: {Theme.RADIUS_MEDIUM}px;
                padding: 8px 20px;
                font-size: {Theme.FONT_BODY}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_GREEN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT_GREEN_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {Theme.BG_DISABLED};
                color: {Theme.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def button_danger() -> str:
        """
        危险按钮 - 红色填充（用于删除/清空等危险操作）

        特点：
        - 红色背景
        - 白色文字
        - 圆角6px

        适用场景：
        - 删除操作
        - 清空操作
        - 不可恢复的操作

        Returns:
            危险按钮QSS字符串
        """
        return f"""
            QPushButton {{
                background-color: {Theme.ACCENT_RED};
                color: {Theme.TEXT_WHITE};
                border: none;
                border-radius: {Theme.RADIUS_MEDIUM}px;
                padding: 6px 16px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_RED_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #b71c1c;
            }}
            QPushButton:disabled {{
                background-color: {Theme.BG_DISABLED};
                color: {Theme.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def button_text() -> str:
        """
        文本按钮 - 无背景无边框（用于链接式操作）

        特点：
        - 透明背景
        - 无边框
        - 蓝色文字（链接色）
        - 悬停时文字变深

        适用场景：
        - 链接式操作
        - 次要操作（"了解更多"、"查看详情"等）

        Returns:
            文本按钮QSS字符串
        """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.ACCENT_BLUE};
                border: none;
                padding: 4px 8px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QPushButton:hover {{
                color: {Theme.ACCENT_BLUE_HOVER};
                text-decoration: underline;
            }}
            QPushButton:pressed {{
                color: #0d47a1;
            }}
            QPushButton:disabled {{
                color: {Theme.TEXT_DISABLED};
            }}
        """

    # ============================================================
    # 输入框样式
    # ============================================================
    @staticmethod
    def input_text() -> str:
        """
        文本输入框 (QLineEdit)

        特点：
        - 白色背景 + 细边框
        - 焦点时绿色边框
        - 圆角4px
        - 内边距8px

        Returns:
            文本输入框QSS字符串
        """
        return f"""
            QLineEdit {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_NORMAL};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QLineEdit:hover {{
                border: 1px solid {Theme.BORDER_HOVER};
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.BORDER_FOCUS};
            }}
            QLineEdit:disabled {{
                background-color: {Theme.BG_DISABLED};
                color: {Theme.TEXT_DISABLED};
                border: 1px solid {Theme.BORDER_LIGHT};
            }}
        """

    @staticmethod
    def input_number() -> str:
        """
        数字输入框 (QSpinBox, QDoubleSpinBox)

        Returns:
            数字输入框QSS字符串
        """
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_NORMAL};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QSpinBox:hover, QDoubleSpinBox:hover {{
                border: 1px solid {Theme.BORDER_HOVER};
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {Theme.BORDER_FOCUS};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                border: none;
                background-color: transparent;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                border: none;
                background-color: transparent;
            }}
        """

    @staticmethod
    def input_time() -> str:
        """
        时间输入框 (QTimeEdit)

        Returns:
            时间输入框QSS字符串
        """
        return f"""
            QTimeEdit {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_NORMAL};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QTimeEdit:hover {{
                border: 1px solid {Theme.BORDER_HOVER};
            }}
            QTimeEdit:focus {{
                border: 2px solid {Theme.BORDER_FOCUS};
            }}
            QTimeEdit::up-button, QTimeEdit::down-button {{
                border: none;
                background-color: transparent;
            }}
        """

    @staticmethod
    def dropdown() -> str:
        """
        下拉框 (QComboBox)

        Returns:
            下拉框QSS字符串
        """
        return f"""
            QComboBox {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_NORMAL};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QComboBox:hover {{
                border: 1px solid {Theme.BORDER_HOVER};
            }}
            QComboBox:focus {{
                border: 2px solid {Theme.BORDER_FOCUS};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_PRIMARY};
                border: 1px solid {Theme.BORDER_NORMAL};
                selection-background-color: {Theme.BG_HOVER};
                selection-color: {Theme.TEXT_PRIMARY};
            }}
        """

    # ============================================================
    # 复选框和单选框
    # ============================================================
    @staticmethod
    def checkbox() -> str:
        """
        复选框 (QCheckBox)

        Returns:
            复选框QSS字符串
        """
        return f"""
            QCheckBox {{
                color: {Theme.TEXT_PRIMARY};
                font-size: {Theme.FONT_BODY}px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {Theme.BORDER_NORMAL};
                border-radius: 3px;
                background-color: {Theme.BG_PRIMARY};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {Theme.BORDER_HOVER};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.ACCENT_GREEN};
                border: 1px solid {Theme.ACCENT_GREEN};
            }}
            QCheckBox:disabled {{
                color: {Theme.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def radio_button() -> str:
        """
        单选按钮 (QRadioButton)

        Returns:
            单选按钮QSS字符串
        """
        return f"""
            QRadioButton {{
                color: {Theme.TEXT_PRIMARY};
                font-size: {Theme.FONT_BODY}px;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {Theme.BORDER_NORMAL};
                border-radius: 9px;
                background-color: {Theme.BG_PRIMARY};
            }}
            QRadioButton::indicator:hover {{
                border: 1px solid {Theme.BORDER_HOVER};
            }}
            QRadioButton::indicator:checked {{
                background-color: {Theme.ACCENT_GREEN};
                border: 1px solid {Theme.ACCENT_GREEN};
            }}
            QRadioButton:disabled {{
                color: {Theme.TEXT_DISABLED};
            }}
        """

    # ============================================================
    # 表格样式
    # ============================================================
    @staticmethod
    def table() -> str:
        """
        表格 (QTableWidget)

        Returns:
            表格QSS字符串
        """
        return f"""
            QTableWidget {{
                background-color: {Theme.BG_PRIMARY};
                alternate-background-color: {Theme.BG_TERTIARY};
                gridline-color: {Theme.BORDER_LIGHT};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_SMALL}px;
                font-size: {Theme.FONT_BODY}px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {Theme.BG_HOVER};
                color: {Theme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_SECONDARY};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {Theme.BORDER_NORMAL};
                font-weight: bold;
            }}
        """

    # ============================================================
    # 标签样式
    # ============================================================
    @staticmethod
    def label_title() -> str:
        """
        标题标签 - 大标题（18px加粗）

        Returns:
            标题QSS字符串
        """
        return f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: {Theme.FONT_TITLE}px;
                font-weight: bold;
            }}
        """

    @staticmethod
    def label_subtitle() -> str:
        """
        副标题标签 - 副标题（14px加粗）

        Returns:
            副标题QSS字符串
        """
        return f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: {Theme.FONT_SUBTITLE}px;
                font-weight: bold;
            }}
        """

    @staticmethod
    def label_body() -> str:
        """
        正文标签 - 普通文字（13px）

        Returns:
            正文QSS字符串
        """
        return f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: {Theme.FONT_BODY}px;
            }}
        """

    @staticmethod
    def label_hint() -> str:
        """
        提示标签 - 灰色提示文字（11px）

        Returns:
            提示QSS字符串
        """
        return f"""
            QLabel {{
                color: {Theme.TEXT_HINT};
                font-size: {Theme.FONT_SMALL}px;
            }}
        """


# ============================================================
# 便捷函数
# ============================================================
def apply_light_theme(app):
    """
    为整个应用应用浅色主题

    Args:
        app: QApplication 实例

    用法:
        from gaiya.ui.style_manager import apply_light_theme
        apply_light_theme(app)
    """
    app.setStyleSheet(StyleManager.get_app_stylesheet())
    print("[主题] 已应用浅色主题（MacOS极简风格）")
