"""
Qt-Material 主题效果测试
测试Gaiya项目常用组件在Material Design下的显示效果
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QLabel, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QTextEdit, QGroupBox, QTabWidget
)
from PySide6.QtCore import Qt
from qt_material import apply_stylesheet, list_themes


class MaterialTestWindow(QMainWindow):
    """Material Design主题测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gaiya - Qt-Material 主题测试")
        self.setGeometry(100, 100, 800, 600)

        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 主题选择器
        theme_group = self._create_theme_selector()
        main_layout.addWidget(theme_group)

        # 创建标签页
        tabs = QTabWidget()
        tabs.addTab(self._create_form_tab(), "📝 表单组件")
        tabs.addTab(self._create_buttons_tab(), "🔘 按钮组件")
        tabs.addTab(self._create_inputs_tab(), "⌨️ 输入组件")
        main_layout.addWidget(tabs)

    def _create_theme_selector(self):
        """创建主题选择器"""
        group = QGroupBox("🎨 主题切换")
        layout = QHBoxLayout(group)

        # 暗色主题
        dark_themes = ['dark_teal.xml', 'dark_blue.xml', 'dark_cyan.xml',
                       'dark_purple.xml', 'dark_pink.xml']
        for theme in dark_themes:
            btn = QPushButton(theme.replace('dark_', '').replace('.xml', '').title())
            btn.clicked.connect(lambda checked, t=theme: self.change_theme(t))
            layout.addWidget(btn)

        # 明亮主题
        layout.addWidget(QLabel(" | "))
        light_themes = ['light_teal.xml', 'light_blue.xml', 'light_cyan.xml']
        for theme in light_themes:
            btn = QPushButton(theme.replace('light_', '').replace('.xml', '').title() + ' (Light)')
            btn.clicked.connect(lambda checked, t=theme: self.change_theme(t))
            layout.addWidget(btn)

        return group

    def _create_form_tab(self):
        """创建表单组件标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 配置项示例（模拟Gaiya配置管理器）
        form_group = QGroupBox("⚙️ 配置项示例")
        form_layout = QVBoxLayout(form_group)

        # 进度条高度
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("进度条高度:"))
        height_spin = QSpinBox()
        height_spin.setRange(5, 50)
        height_spin.setValue(10)
        height_spin.setSuffix(" px")
        row1.addWidget(height_spin)
        row1.addStretch()
        form_layout.addLayout(row1)

        # 标记图片路径
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("标记图片:"))
        path_input = QLineEdit("kun.webp")
        row2.addWidget(path_input)
        browse_btn = QPushButton("浏览...")
        row2.addWidget(browse_btn)
        form_layout.addLayout(row2)

        # 下拉选择
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("位置:"))
        position_combo = QComboBox()
        position_combo.addItems(["top", "bottom"])
        position_combo.setCurrentText("bottom")
        row3.addWidget(position_combo)
        row3.addStretch()
        form_layout.addLayout(row3)

        # 复选框
        enable_shadow = QCheckBox("启用阴影效果")
        enable_shadow.setChecked(True)
        form_layout.addWidget(enable_shadow)

        autostart = QCheckBox("开机自启动")
        form_layout.addWidget(autostart)

        layout.addWidget(form_group)
        layout.addStretch()

        return widget

    def _create_buttons_tab(self):
        """创建按钮组件标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        btn_group = QGroupBox("🔘 按钮样式")
        btn_layout = QVBoxLayout(btn_group)

        # 主要按钮
        primary_btn = QPushButton("💾 保存配置")
        primary_btn.setMinimumHeight(40)
        btn_layout.addWidget(primary_btn)

        # 次要按钮
        secondary_btn = QPushButton("🔄 重新加载")
        secondary_btn.setMinimumHeight(40)
        btn_layout.addWidget(secondary_btn)

        # 危险按钮
        danger_btn = QPushButton("🗑️ 删除任务")
        danger_btn.setMinimumHeight(40)
        btn_layout.addWidget(danger_btn)

        # 禁用按钮
        disabled_btn = QPushButton("已禁用")
        disabled_btn.setEnabled(False)
        disabled_btn.setMinimumHeight(40)
        btn_layout.addWidget(disabled_btn)

        # 按钮组
        row = QHBoxLayout()
        row.addWidget(QPushButton("确定"))
        row.addWidget(QPushButton("取消"))
        row.addWidget(QPushButton("应用"))
        btn_layout.addLayout(row)

        layout.addWidget(btn_group)
        layout.addStretch()

        return widget

    def _create_inputs_tab(self):
        """创建输入组件标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        input_group = QGroupBox("⌨️ 输入控件")
        input_layout = QVBoxLayout(input_group)

        # 单行输入
        input_layout.addWidget(QLabel("任务名称:"))
        task_input = QLineEdit()
        task_input.setPlaceholderText("请输入任务名称...")
        input_layout.addWidget(task_input)

        # 多行输入
        input_layout.addWidget(QLabel("任务描述:"))
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("输入任务的详细描述...")
        desc_input.setMaximumHeight(100)
        input_layout.addWidget(desc_input)

        # 数字输入
        row = QHBoxLayout()
        row.addWidget(QLabel("任务时长:"))
        duration_spin = QSpinBox()
        duration_spin.setRange(1, 480)
        duration_spin.setValue(30)
        duration_spin.setSuffix(" 分钟")
        row.addWidget(duration_spin)
        row.addStretch()
        input_layout.addLayout(row)

        layout.addWidget(input_group)
        layout.addStretch()

        return widget

    def change_theme(self, theme_name):
        """切换主题"""
        extra = {
            'density_scale': '0',
            'font_family': 'Microsoft YaHei',
            'font_size': '13px',
        }
        apply_stylesheet(QApplication.instance(), theme=theme_name, extra=extra)
        print(f"✅ 已切换到主题: {theme_name}")


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 应用默认Material主题（盖亚蓝绿色）
    extra = {
        'density_scale': '0',
        'font_family': 'Microsoft YaHei',
        'font_size': '13px',
    }
    apply_stylesheet(app, theme='dark_teal.xml', extra=extra)

    # 显示可用主题列表
    print("🎨 Qt-Material 可用主题:")
    themes = list_themes()
    for i, theme in enumerate(themes, 1):
        print(f"  {i}. {theme}")

    window = MaterialTestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
