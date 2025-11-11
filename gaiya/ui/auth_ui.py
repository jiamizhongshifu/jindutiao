"""
GaiYa每日进度条 - 认证UI模块
提供登录和注册对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QMessageBox, QCheckBox,
    QStackedWidget, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
import sys
import os

# 添加父目录到路径以导入core模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gaiya.core.auth_client import AuthClient
from gaiya.ui.email_verification_dialog import EmailVerificationDialog


class AuthDialog(QDialog):
    """认证对话框（登录/注册）"""

    # 信号：登录成功时发出
    login_success = Signal(dict)  # 传递user_info

    def __init__(self, parent=None, auth_client=None):
        super().__init__(parent)
        # 使用传入的auth_client实例，如果没有则创建新的
        self.auth_client = auth_client if auth_client is not None else AuthClient()

        # 微信登录相关状态
        self.wechat_state = None  # 微信登录state参数
        self.polling_timer = None  # 轮询定时器

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

        # 创建StackedWidget（微信登录 vs 邮箱登录）
        self.stacked_widget = QStackedWidget()

        # 页面0: 微信登录（延迟加载，避免QWebEngineView初始化导致卡顿）
        # 先添加一个占位widget，真正切换到微信登录时才创建
        self.wechat_widget = None
        self.wechat_placeholder = QWidget()  # 占位
        self.stacked_widget.addWidget(self.wechat_placeholder)

        # 页面1: 邮箱登录/注册
        email_widget = self._create_email_login_widget()
        self.stacked_widget.addWidget(email_widget)

        # 默认显示邮箱登录（微信登录功能暂时屏蔽，待后端API完成后启用）
        self.stacked_widget.setCurrentIndex(1)  # 0=微信登录, 1=邮箱登录

        main_layout.addWidget(self.stacked_widget)

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

            # 检查是否是SSL错误
            if "SSL" in error_msg or "ssl" in error_msg or "连接失败" in error_msg:
                # SSL连接失败，提供详细的排查建议
                QMessageBox.critical(
                    self,
                    "连接失败",
                    f"客户端无法连接到服务器（SSL问题）\n\n"
                    f"技术详情：{error_msg}\n\n"
                    f"可能的解决方案：\n"
                    f"1. 检查网络连接是否正常\n"
                    f"2. 确认没有使用代理或VPN\n"
                    f"3. 暂时关闭防火墙/安全软件重试\n"
                    f"4. 更新Windows系统到最新版本\n\n"
                    f"如果问题持续，请联系技术支持。"
                )
            else:
                # 其他错误，直接显示
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
            # 使用Supabase内置邮箱验证
            # 1. 注册成功，Supabase已自动发送验证邮件
            verification_dialog = EmailVerificationDialog(
                parent=self,
                email=email,
                password=password,  # 传递密码用于验证成功后自动登录
                user_id=result.get("user_id")
            )

            # 连接验证成功信号
            verification_dialog.verification_success.connect(
                lambda user_info: self._on_email_verified(user_info)
            )

            if verification_dialog.exec() == QDialog.DialogCode.Accepted:
                # 用户已验证成功并自动登录（由EmailVerificationDialog处理）
                # 这里不需要额外操作，信号已触发
                pass
            else:
                # 用户取消验证，提示可以稍后登录
                QMessageBox.information(
                    self,
                    "注册成功",
                    "您的账号已创建，验证邮件已发送。\n\n"
                    "请验证邮箱后登录。如果没有收到邮件，请检查垃圾邮件文件夹。"
                )
        else:
            # 注册失败
            error_msg = result.get("error", "注册失败")

            # 检查是否是SSL错误
            if "SSL" in error_msg or "ssl" in error_msg or "连接失败" in error_msg:
                # 提供浏览器注册的选项
                reply = QMessageBox.question(
                    self,
                    "连接失败",
                    f"客户端无法连接到服务器（SSL问题）\n\n"
                    f"技术详情：{error_msg}\n\n"
                    f"是否使用浏览器完成注册？\n"
                    f"（注册成功后，您可以返回客户端登录）",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # 打开浏览器到注册页面
                    import webbrowser
                    signup_url = f"{self.auth_client.backend_url}/#/signup?email={email}"
                    webbrowser.open(signup_url)

                    # 提示用户
                    QMessageBox.information(
                        self,
                        "浏览器注册",
                        "已在浏览器中打开注册页面。\n\n"
                        "请完成注册后，返回客户端使用\"登录\"标签页登录。"
                    )
            else:
                # 其他错误，直接显示
                QMessageBox.critical(self, "注册失败", f"注册失败：{error_msg}")

    def _on_email_verified(self, user_info: dict):
        """邮箱验证成功的回调"""
        print(f"[AUTH-UI] 邮箱验证成功，用户信息: {user_info}")

        # 发出登录成功信号
        self.login_success.emit(user_info)

        # 关闭认证对话框
        self.accept()

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

    def _create_wechat_login_widget(self) -> QWidget:
        """创建微信登录页面（带二维码）"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 提示文字
        tip_label = QLabel("请使用微信扫码登录")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(tip_label)

        # QR码显示区域（使用QWebEngineView）
        self.qr_code_view = QWebEngineView()
        self.qr_code_view.setMinimumSize(300, 300)
        self.qr_code_view.setMaximumSize(300, 300)

        # 初始显示加载提示
        self.qr_code_view.setHtml("""
            <html>
            <body style="display: flex; align-items: center; justify-content: center;
                         height: 100%; margin: 0; font-family: Arial; color: #666;">
                <div style="text-align: center;">
                    <p style="font-size: 16px;">正在加载二维码...</p>
                    <p style="font-size: 12px; color: #999;">请稍候</p>
                </div>
            </body>
            </html>
        """)

        # 将QR码视图居中
        qr_container = QWidget()
        qr_layout = QHBoxLayout(qr_container)
        qr_layout.addStretch()
        qr_layout.addWidget(self.qr_code_view)
        qr_layout.addStretch()
        layout.addWidget(qr_container)

        # 状态标签
        self.status_label = QLabel("等待扫码...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(separator)

        # 切换到邮箱登录按钮
        switch_button = QPushButton("使用邮箱登录 >")
        switch_button.setFlat(True)
        switch_button.setStyleSheet("""
            QPushButton {
                color: #2196F3;
                font-size: 14px;
                padding: 10px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #0b7dda;
            }
        """)
        switch_button.clicked.connect(self._switch_to_email_login)
        layout.addWidget(switch_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        widget.setLayout(layout)

        # 启动微信登录流程
        QTimer.singleShot(500, self._start_wechat_login)

        return widget

    def _create_email_login_widget(self) -> QWidget:
        """创建邮箱登录/注册页面（包含原有Tab）"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # 原有的Tab切换（登录/注册）
        self.tab_widget = QTabWidget()

        # 登录Tab
        self.signin_widget = self._create_signin_tab()
        self.tab_widget.addTab(self.signin_widget, "登录")

        # 注册Tab
        self.signup_widget = self._create_signup_tab()
        self.tab_widget.addTab(self.signup_widget, "注册")

        layout.addWidget(self.tab_widget)

        layout.addSpacing(10)

        # 分隔线
        # separator = QFrame()
        # separator.setFrameShape(QFrame.Shape.HLine)
        # separator.setFrameShadow(QFrame.Shadow.Sunken)
        # separator.setStyleSheet("background-color: #e0e0e0;")
        # layout.addWidget(separator)

        # # 返回微信登录按钮（已禁用微信登录，隐藏此按钮）
        # back_button = QPushButton("< 返回微信登录")
        # back_button.setFlat(True)
        # back_button.setStyleSheet("""
        #     QPushButton {
        #         color: #2196F3;
        #         font-size: 14px;
        #         padding: 10px;
        #         text-decoration: underline;
        #     }
        #     QPushButton:hover {
        #         color: #0b7dda;
        #     }
        # """)
        # back_button.clicked.connect(self._switch_to_wechat_login)
        # layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        widget.setLayout(layout)
        return widget

    def _switch_to_email_login(self):
        """切换到邮箱登录模式"""
        self.stacked_widget.setCurrentIndex(1)
        # 停止微信登录轮询（如果正在进行）
        if self.polling_timer and self.polling_timer.isActive():
            self.polling_timer.stop()

    def _switch_to_wechat_login(self):
        """切换到微信登录模式（延迟加载）"""
        # 如果微信登录widget还未创建，现在创建它
        if self.wechat_widget is None:
            print("[AUTH-UI] 延迟创建微信登录widget（QWebEngineView）...")
            self.wechat_widget = self._create_wechat_login_widget()
            # 替换占位符
            self.stacked_widget.removeWidget(self.wechat_placeholder)
            self.stacked_widget.insertWidget(0, self.wechat_widget)
            self.wechat_placeholder.deleteLater()
            print("[AUTH-UI] 微信登录widget创建完成")

        self.stacked_widget.setCurrentIndex(0)
        # 重新启动微信登录流程
        self._start_wechat_login()

    def _start_wechat_login(self):
        """启动微信登录流程（获取二维码URL）"""
        try:
            # 更新状态
            self.status_label.setText("正在生成二维码...")

            # 调用AuthClient获取微信二维码URL
            result = self.auth_client.wechat_get_qr_code()

            if result.get("success"):
                # 获取二维码URL和state
                qr_url = result.get("qr_url")
                self.wechat_state = result.get("state")

                # 在QWebEngineView中加载微信授权页面
                self.qr_code_view.setUrl(QUrl(qr_url))

                # 更新状态
                self.status_label.setText("等待扫码...")

                # 启动轮询定时器（每2秒检查一次）
                if self.polling_timer is None:
                    self.polling_timer = QTimer(self)
                    self.polling_timer.timeout.connect(self._check_wechat_scan_status)

                self.polling_timer.start(2000)  # 2秒轮询一次
            else:
                # 获取二维码失败
                error_msg = result.get("error", "无法生成二维码")
                self.status_label.setText(f"错误: {error_msg}")
                self.qr_code_view.setHtml(f"""
                    <html>
                    <body style="display: flex; align-items: center; justify-content: center;
                                 height: 100%; margin: 0; font-family: Arial; color: #f44336;">
                        <div style="text-align: center;">
                            <p style="font-size: 16px;">⚠️ {error_msg}</p>
                            <p style="font-size: 12px; color: #999;">请尝试使用邮箱登录</p>
                        </div>
                    </body>
                    </html>
                """)
        except Exception as e:
            # 异常处理
            self.status_label.setText(f"错误: {str(e)}")
            self.qr_code_view.setHtml(f"""
                <html>
                <body style="display: flex; align-items: center; justify-content: center;
                             height: 100%; margin: 0; font-family: Arial; color: #f44336;">
                    <div style="text-align: center;">
                        <p style="font-size: 16px;">⚠️ 加载失败</p>
                        <p style="font-size: 12px; color: #999;">{str(e)}</p>
                    </div>
                </body>
                </html>
            """)

    def _check_wechat_scan_status(self):
        """轮询检查扫码状态（每2秒）"""
        if not self.wechat_state:
            return

        try:
            # 调用AuthClient检查扫码状态
            result = self.auth_client.wechat_check_scan_status(self.wechat_state)

            status = result.get("status")

            if status == "pending":
                # 仍在等待扫码
                self.status_label.setText("等待扫码...")
            elif status == "scanned":
                # 已扫码，等待确认
                self.status_label.setText("扫码成功，请在手机上确认...")
            elif status == "success":
                # 登录成功
                self.status_label.setText("登录成功！")

                # 停止轮询
                if self.polling_timer:
                    self.polling_timer.stop()

                # 获取用户信息
                user_info = result.get("user_info", {})

                # 发出登录成功信号
                self.login_success.emit(user_info)

                # 关闭对话框
                self.accept()
            elif status == "expired":
                # 二维码过期
                self.status_label.setText("二维码已过期，正在刷新...")
                if self.polling_timer:
                    self.polling_timer.stop()
                # 重新生成二维码
                QTimer.singleShot(1000, self._start_wechat_login)
            elif status == "error":
                # 登录失败
                error_msg = result.get("error", "登录失败")
                self.status_label.setText(f"错误: {error_msg}")
                if self.polling_timer:
                    self.polling_timer.stop()
        except Exception as e:
            # 异常处理
            self.status_label.setText(f"检查状态失败: {str(e)}")


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
