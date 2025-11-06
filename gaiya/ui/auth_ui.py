"""
GaiYa每日进度条 - 认证UI模块
提供登录和注册对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import sys
import os

# 添加父目录到路径以导入core模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_client import AuthClient


class AuthDialog(QDialog):
    """认证对话框（登录/注册）"""

    # 信号：登录成功时发出
    login_success = Signal(dict)  # 传递user_info

    def __init__(self, parent=None, auth_client=None):
        super().__init__(parent)
        # 使用传入的auth_client实例，如果没有则创建新的
        self.auth_client = auth_client if auth_client is not None else AuthClient()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("GaiYa - 账户登录")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("欢迎使用 GaiYa")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("每日进度条 - 让时间可视化")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(subtitle_label)

        # Tab切换（登录/注册）
        self.tab_widget = QTabWidget()

        # 登录Tab
        self.signin_widget = self._create_signin_tab()
        self.tab_widget.addTab(self.signin_widget, "登录")

        # 注册Tab
        self.signup_widget = self._create_signup_tab()
        self.tab_widget.addTab(self.signup_widget, "注册")

        main_layout.addWidget(self.tab_widget)

        # 底部说明
        info_label = QLabel("注册即表示同意服务条款和隐私政策")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #999; font-size: 10px;")
        main_layout.addWidget(info_label)

        self.setLayout(main_layout)

    def _create_signin_tab(self) -> QWidget:
        """创建登录Tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 邮箱输入
        email_label = QLabel("邮箱地址")
        self.signin_email_input = QLineEdit()
        self.signin_email_input.setPlaceholderText("请输入邮箱")
        self.signin_email_input.setMinimumHeight(35)

        # 密码输入
        password_label = QLabel("密码")
        self.signin_password_input = QLineEdit()
        self.signin_password_input.setPlaceholderText("请输入密码")
        self.signin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signin_password_input.setMinimumHeight(35)

        # 记住登录
        self.remember_checkbox = QCheckBox("记住登录状态")
        self.remember_checkbox.setChecked(True)

        # 登录按钮
        signin_button = QPushButton("登录")
        signin_button.setMinimumHeight(40)
        signin_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        signin_button.clicked.connect(self._on_signin_clicked)

        # 忘记密码链接
        forgot_button = QPushButton("忘记密码？")
        forgot_button.setFlat(True)
        forgot_button.setStyleSheet("color: #4CAF50; text-decoration: underline;")
        forgot_button.clicked.connect(self._on_forgot_password)

        # 添加组件
        layout.addWidget(email_label)
        layout.addWidget(self.signin_email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.signin_password_input)
        layout.addWidget(self.remember_checkbox)
        layout.addSpacing(10)
        layout.addWidget(signin_button)
        layout.addWidget(forgot_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_signup_tab(self) -> QWidget:
        """创建注册Tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 用户名输入
        username_label = QLabel("用户名（可选）")
        self.signup_username_input = QLineEdit()
        self.signup_username_input.setPlaceholderText("请输入用户名")
        self.signup_username_input.setMinimumHeight(35)

        # 邮箱输入
        email_label = QLabel("邮箱地址")
        self.signup_email_input = QLineEdit()
        self.signup_email_input.setPlaceholderText("请输入邮箱")
        self.signup_email_input.setMinimumHeight(35)

        # 密码输入
        password_label = QLabel("密码")
        self.signup_password_input = QLineEdit()
        self.signup_password_input.setPlaceholderText("至少6个字符")
        self.signup_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_password_input.setMinimumHeight(35)

        # 确认密码
        confirm_password_label = QLabel("确认密码")
        self.signup_confirm_password_input = QLineEdit()
        self.signup_confirm_password_input.setPlaceholderText("请再次输入密码")
        self.signup_confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_password_input.setMinimumHeight(35)

        # 注册按钮
        signup_button = QPushButton("注册")
        signup_button.setMinimumHeight(40)
        signup_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0c5a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        signup_button.clicked.connect(self._on_signup_clicked)

        # 添加组件
        layout.addWidget(username_label)
        layout.addWidget(self.signup_username_input)
        layout.addWidget(email_label)
        layout.addWidget(self.signup_email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.signup_password_input)
        layout.addWidget(confirm_password_label)
        layout.addWidget(self.signup_confirm_password_input)
        layout.addSpacing(10)
        layout.addWidget(signup_button)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _on_signin_clicked(self):
        """处理登录按钮点击"""
        email = self.signin_email_input.text().strip()
        password = self.signin_password_input.text()

        # 验证输入
        if not email or not password:
            QMessageBox.warning(self, "输入错误", "请输入邮箱和密码")
            return

        # 简单的邮箱格式验证
        if "@" not in email:
            QMessageBox.warning(self, "输入错误", "邮箱格式不正确")
            return

        # 禁用登录按钮，防止重复点击
        signin_button = self.sender()
        signin_button.setEnabled(False)
        signin_button.setText("登录中...")

        # 调用登录API
        result = self.auth_client.signin(email, password)

        # 恢复按钮状态
        signin_button.setEnabled(True)
        signin_button.setText("登录")

        if result.get("success"):
            # 登录成功
            user_info = {
                "user_id": result.get("user_id"),
                "email": result.get("email"),
                "user_tier": result.get("user_tier", "free")
            }

            # 发出登录成功信号
            self.login_success.emit(user_info)

            # 关闭对话框
            self.accept()
        else:
            # 登录失败
            error_msg = result.get("error", "登录失败")
            QMessageBox.critical(self, "登录失败", f"登录失败：{error_msg}")

    def _on_signup_clicked(self):
        """处理注册按钮点击"""
        username = self.signup_username_input.text().strip()
        email = self.signup_email_input.text().strip()
        password = self.signup_password_input.text()
        confirm_password = self.signup_confirm_password_input.text()

        # 验证输入
        if not email or not password:
            QMessageBox.warning(self, "输入错误", "请输入邮箱和密码")
            return

        if "@" not in email:
            QMessageBox.warning(self, "输入错误", "邮箱格式不正确")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "输入错误", "密码至少需要6个字符")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "输入错误", "两次输入的密码不一致")
            return

        # 禁用注册按钮
        signup_button = self.sender()
        signup_button.setEnabled(False)
        signup_button.setText("注册中...")

        # 调用注册API
        result = self.auth_client.signup(
            email=email,
            password=password,
            username=username if username else None
        )

        # 恢复按钮状态
        signup_button.setEnabled(True)
        signup_button.setText("注册")

        if result.get("success"):
            # 注册成功（方案A: 禁用邮箱确认，直接登录）
            user_info = {
                "user_id": result.get("user_id"),
                "email": result.get("email"),
                "user_tier": "free"
            }

            # 发出登录成功信号
            self.login_success.emit(user_info)

            # 关闭对话框
            self.accept()

            # 方案C（OTP验证）已禁用，如需启用请参考 docs/desktop-email-verification-guide.md
        else:
            # 注册失败
            error_msg = result.get("error", "注册失败")
            QMessageBox.critical(self, "注册失败", f"注册失败：{error_msg}")

    def _on_forgot_password(self):
        """处理忘记密码"""
        email, ok = self._show_input_dialog(
            "重置密码",
            "请输入您的注册邮箱，我们将发送重置密码的邮件："
        )

        if not ok or not email:
            return

        if "@" not in email:
            QMessageBox.warning(self, "输入错误", "邮箱格式不正确")
            return

        # 调用重置密码API
        result = self.auth_client.reset_password(email)

        if result.get("success"):
            QMessageBox.information(
                self,
                "邮件已发送",
                f"重置密码的邮件已发送到 {email}，请查收。"
            )
        else:
            error_msg = result.get("error", "发送失败")
            QMessageBox.critical(self, "发送失败", f"发送失败：{error_msg}")

    def _show_input_dialog(self, title: str, label: str) -> tuple:
        """显示输入对话框（简易实现）"""
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return text, ok


if __name__ == "__main__":
    # 测试认证对话框
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = AuthDialog()

    def on_login_success(user_info):
        print(f"登录成功！用户信息: {user_info}")

    dialog.login_success.connect(on_login_success)
    dialog.exec()

    sys.exit(app.exec())
