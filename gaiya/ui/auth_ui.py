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
import sys
import os

# WebEngine 可选导入（用于微信登录，如果不可用则禁用微信登录功能）
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    QWebEngineView = None  # 占位，避免后续代码引用时报错

# 添加父目录到路径以导入core模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gaiya.core.auth_client import AuthClient
from i18n.translator import tr
from gaiya.core.async_worker import AsyncNetworkWorker
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
        self.setWindowTitle(tr("auth.window_title"))
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel(tr("auth.welcome"))
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel(tr("auth.subtitle"))
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
        info_label = QLabel(tr("auth.terms_notice"))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #999; font-size: 10px;")
        main_layout.addWidget(info_label)

        self.setLayout(main_layout)

    def _create_signin_page(self) -> QWidget:
        """创建登录页面（带ghost button注册入口）"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 邮箱输入
        email_label = QLabel(tr("auth.email_label"))
        self.signin_email_input = QLineEdit()
        self.signin_email_input.setPlaceholderText(tr("auth.email_placeholder"))
        self.signin_email_input.setMinimumHeight(35)

        # 密码输入
        password_label = QLabel(tr("auth.password_label"))
        self.signin_password_input = QLineEdit()
        self.signin_password_input.setPlaceholderText(tr("auth.password_placeholder"))
        self.signin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signin_password_input.setMinimumHeight(35)

        # 记住登录
        self.remember_checkbox = QCheckBox(tr("auth.signin.remember_me"))
        self.remember_checkbox.setChecked(True)

        # 登录按钮
        signin_button = QPushButton(tr("auth.signin.btn_login"))
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
        forgot_button = QPushButton(tr("auth.signin.forgot_password"))
        forgot_button.setFlat(True)
        forgot_button.setStyleSheet("color: #4CAF50; text-decoration: underline;")
        forgot_button.clicked.connect(self._on_forgot_password)

        # Ghost button - 注册账号
        signup_ghost_button = QPushButton(tr("auth.signup.link_to_register"))
        signup_ghost_button.setMinimumHeight(40)
        signup_ghost_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2196F3;
                border: 2px solid #2196F3;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(33, 150, 243, 0.2);
            }
        """)
        signup_ghost_button.clicked.connect(self._switch_to_signup)

        # 添加组件
        layout.addWidget(email_label)
        layout.addWidget(self.signin_email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.signin_password_input)
        layout.addWidget(self.remember_checkbox)
        layout.addSpacing(10)
        layout.addWidget(signin_button)
        layout.addWidget(forgot_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(signup_ghost_button)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_signup_page(self) -> QWidget:
        """创建注册页面（带ghost button返回登录）"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 邮箱输入
        email_label = QLabel(tr("auth.email_label"))
        self.signup_email_input = QLineEdit()
        self.signup_email_input.setPlaceholderText(tr("auth.email_placeholder"))
        self.signup_email_input.setMinimumHeight(35)

        # 密码输入
        password_label = QLabel(tr("auth.password_label"))
        self.signup_password_input = QLineEdit()
        self.signup_password_input.setPlaceholderText(tr("auth.password_hint"))
        self.signup_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_password_input.setMinimumHeight(35)

        # 确认密码
        confirm_password_label = QLabel(tr("auth.confirm_password_label"))
        self.signup_confirm_password_input = QLineEdit()
        self.signup_confirm_password_input.setPlaceholderText(tr("auth.confirm_password_placeholder"))
        self.signup_confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_password_input.setMinimumHeight(35)

        # 注册按钮
        signup_button = QPushButton(tr("auth.signup.btn_register"))
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

        # Ghost button - 返回登录
        signin_ghost_button = QPushButton(tr("auth.signup.back_to_login"))
        signin_ghost_button.setMinimumHeight(40)
        signin_ghost_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2196F3;
                border: 2px solid #2196F3;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(33, 150, 243, 0.2);
            }
        """)
        signin_ghost_button.clicked.connect(self._switch_to_signin)

        # 添加组件（移除了用户名字段）
        layout.addWidget(email_label)
        layout.addWidget(self.signup_email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.signup_password_input)
        layout.addWidget(confirm_password_label)
        layout.addWidget(self.signup_confirm_password_input)
        layout.addSpacing(10)
        layout.addWidget(signup_button)
        layout.addSpacing(10)
        layout.addWidget(signin_ghost_button)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _on_signin_clicked(self):
        """处理登录按钮点击"""
        email = self.signin_email_input.text().strip()
        password = self.signin_password_input.text()

        # 验证输入
        if not email or not password:
            QMessageBox.warning(self, tr("auth.error.input_error"), tr("auth.error.empty_fields"))
            return

        # 简单的邮箱格式验证
        if "@" not in email:
            QMessageBox.warning(self, tr("auth.error.input_error"), tr("auth.error.invalid_email"))
            return

        # 禁用登录按钮，防止重复点击
        signin_button = self.sender()
        signin_button.setEnabled(False)
        signin_button.setText(tr("auth.signin.logging_in"))

        # 调用登录API
        result = self.auth_client.signin(email, password)

        # 恢复按钮状态
        signin_button.setEnabled(True)
        signin_button.setText(tr("auth.signin.btn_login"))

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
            error_msg = result.get("error", tr("auth.error.login_failed_title"))

            # 检查是否是SSL错误
            if "SSL" in error_msg or "ssl" in error_msg or tr("auth.error.connection_failed") in error_msg:
                # SSL连接失败，提供详细的排查建议
                QMessageBox.critical(
                    self,
                    tr("auth.error.connection_failed"),
                    tr("auth.error.ssl_error_intro") +
                    tr("auth.error.technical_details", error_msg=error_msg) +
                    tr("auth.error.solutions_intro") +
                    tr("auth.error.solution_check_network") +
                    tr("auth.error.solution_no_proxy") +
                    tr("auth.error.solution_disable_firewall") +
                    tr("auth.error.solution_update_windows") +
                    tr("auth.error.contact_support")
                )
            else:
                # 其他错误，直接显示
                QMessageBox.critical(self, tr("auth.error.login_failed_title"), tr("auth.error.login_failed", error_msg=error_msg))

    def _on_signup_clicked(self):
        """处理注册按钮点击"""
        email = self.signup_email_input.text().strip()
        password = self.signup_password_input.text()
        confirm_password = self.signup_confirm_password_input.text()

        # 验证输入
        if not email or not password:
            QMessageBox.warning(self, tr("auth.error.input_error"), tr("auth.error.empty_fields"))
            return

        if "@" not in email:
            QMessageBox.warning(self, tr("auth.error.input_error"), tr("auth.error.invalid_email"))
            return

        if len(password) < 6:
            QMessageBox.warning(self, tr("auth.error.input_error"), tr("auth.error.password_too_short"))
            return

        if password != confirm_password:
            QMessageBox.warning(self, tr("auth.error.input_error"), tr("auth.error.passwords_mismatch"))
            return

        # 禁用注册按钮
        signup_button = self.sender()
        signup_button.setEnabled(False)
        signup_button.setText(tr("auth.signup.registering"))

        # 保存按钮引用供回调使用
        self._signup_button = signup_button
        self._signup_email = email
        self._signup_password = password

        # 使用异步Worker执行注册API（避免UI阻塞）
        self._signup_worker = AsyncNetworkWorker(
            self.auth_client.signup,
            email=email,
            password=password
        )
        self._signup_worker.success.connect(self._on_signup_success)
        self._signup_worker.error.connect(self._on_signup_error)
        self._signup_worker.start()

    def _on_signup_success(self, result: dict):
        """注册成功回调"""
        # 恢复按钮状态
        self._signup_button.setEnabled(True)
        self._signup_button.setText(tr("auth.signup.btn_register"))

        if result.get("success"):
            # 使用Supabase内置邮箱验证
            # 1. 注册成功，Supabase已自动发送验证邮件
            verification_dialog = EmailVerificationDialog(
                parent=self,
                email=self._signup_email,
                password=self._signup_password,  # 传递密码用于验证成功后自动登录
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
                    tr("auth.signup.success_title"),
                    tr("auth.signup.success_message")
                )

    def _on_signup_error(self, error_msg: str):
        """注册失败回调"""
        # 恢复按钮状态
        self._signup_button.setEnabled(True)
        self._signup_button.setText(tr("auth.signup.btn_register"))

        # 检查是否是SSL错误
        if "SSL" in error_msg or "ssl" in error_msg or tr("auth.error.connection_failed") in error_msg:
            # 提供浏览器注册的选项
            reply = QMessageBox.question(
                self,
                tr("auth.error.connection_failed"),
                tr("auth.error.ssl_error_intro") +
                tr("auth.error.technical_details", error_msg=error_msg) +
                tr("auth.error.browser_fallback_prompt"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 打开浏览器到注册页面
                import webbrowser
                signup_url = f"{self.auth_client.backend_url}/#/signup?email={self._signup_email}"
                webbrowser.open(signup_url)

                # 提示用户
                QMessageBox.information(
                    self,
                    tr("auth.signup.browser_register_title"),
                    tr("auth.signup.browser_register_message")
                )
        else:
            # 其他错误，直接显示
            QMessageBox.critical(self, tr("auth.error.register_failed_title"), tr("auth.error.register_failed", error_msg=error_msg))

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
            tr("auth.reset.title"),
            tr("auth.reset.prompt")
        )

        if not ok or not email:
            return

        if "@" not in email:
            QMessageBox.warning(self, tr("auth.error.input_error"), tr("auth.error.invalid_email"))
            return

        # 调用重置密码API
        result = self.auth_client.reset_password(email)

        if result.get("success"):
            QMessageBox.information(
                self,
                tr("auth.reset.email_sent_title"),
                tr("auth.reset.email_sent_message", email=email)
            )
        else:
            error_msg = result.get("error", tr("auth.error.send_failed"))
            QMessageBox.critical(self, tr("auth.error.send_failed"), tr("auth.error.send_failed_with_msg", error_msg=error_msg))

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

        # 检查 WebEngine 是否可用
        if not HAS_WEBENGINE:
            # WebEngine 不可用，显示提示信息
            tip_label = QLabel(tr("auth.wechat.unavailable"))
            tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tip_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f44336;")
            layout.addWidget(tip_label)

            info_label = QLabel(tr("auth.wechat.no_webengine"))
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(info_label)

            layout.addSpacing(20)

            # 切换到邮箱登录按钮
            switch_button = QPushButton(tr("auth.switch_to_email"))
            switch_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            switch_button.clicked.connect(self._switch_to_email_login)
            layout.addWidget(switch_button, alignment=Qt.AlignmentFlag.AlignCenter)

            layout.addStretch()
            widget.setLayout(layout)
            return widget

        # WebEngine 可用，正常创建微信登录界面
        # 提示文字
        tip_label = QLabel(tr("auth.wechat.scan_prompt"))
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
        self.status_label = QLabel(tr("auth.wechat.waiting_scan"))
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
        switch_button = QPushButton(tr("auth.switch_to_email"))
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
        """创建邮箱登录/注册页面（使用StackedWidget + Ghost按钮导航）"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # 使用StackedWidget替代TabWidget（页面0=登录, 页面1=注册）
        self.auth_pages = QStackedWidget()

        # 页面0: 登录页面（带ghost buttontr("auth.signup.link_to_register")）
        self.signin_widget = self._create_signin_page()
        self.auth_pages.addWidget(self.signin_widget)

        # 页面1: 注册页面（带ghost buttontr("auth.signup.back_to_login")）
        self.signup_widget = self._create_signup_page()
        self.auth_pages.addWidget(self.signup_widget)

        # 默认显示登录页面
        self.auth_pages.setCurrentIndex(0)

        layout.addWidget(self.auth_pages)

        widget.setLayout(layout)
        return widget

    def _switch_to_email_login(self):
        """切换到邮箱登录模式"""
        self.stacked_widget.setCurrentIndex(1)
        # 停止微信登录轮询（如果正在进行）
        if self.polling_timer and self.polling_timer.isActive():
            self.polling_timer.stop()

    def _switch_to_signup(self):
        """切换到注册页面（通过ghost button）"""
        self.auth_pages.setCurrentIndex(1)

    def _switch_to_signin(self):
        """切换到登录页面（通过ghost button）"""
        self.auth_pages.setCurrentIndex(0)

    def _switch_to_wechat_login(self):
        """切换到微信登录模式（延迟加载）"""
        # 检查 WebEngine 是否可用
        if not HAS_WEBENGINE:
            print("[AUTH-UI] WebEngine 不可用，自动切换到邮箱登录")
            QMessageBox.warning(
                self,
                tr("auth.wechat.feature_unavailable"),
                tr("auth.wechat.webengine_required")
            )
            self._switch_to_email_login()
            return

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
            self.status_label.setText(tr("auth.wechat.generating_qr"))

            # 调用AuthClient获取微信二维码URL
            result = self.auth_client.wechat_get_qr_code()

            if result.get("success"):
                # 获取二维码URL和state
                qr_url = result.get("qr_url")
                self.wechat_state = result.get("state")

                # 在QWebEngineView中加载微信授权页面
                self.qr_code_view.setUrl(QUrl(qr_url))

                # 更新状态
                self.status_label.setText(tr("auth.wechat.waiting_scan"))

                # 启动轮询定时器（每2秒检查一次）
                if self.polling_timer is None:
                    self.polling_timer = QTimer(self)
                    self.polling_timer.timeout.connect(self._check_wechat_scan_status)

                self.polling_timer.start(2000)  # 2秒轮询一次
            else:
                # 获取二维码失败
                error_msg = result.get("error", tr("auth.error.qr_code_failed"))
                self.status_label.setText(tr("auth.error.generic_error", error_msg=error_msg))
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
            self.status_label.setText(tr("auth.error.exception_error", e=str(e)))
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
                self.status_label.setText(tr("auth.wechat.waiting_scan"))
            elif status == "scanned":
                # 已扫码，等待确认
                self.status_label.setText(tr("auth.wechat.confirm_on_phone"))
            elif status == "success":
                # 登录成功
                self.status_label.setText(tr("auth.signin.success"))

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
                self.status_label.setText(tr("auth.wechat.qr_expired"))
                if self.polling_timer:
                    self.polling_timer.stop()
                # 重新生成二维码
                QTimer.singleShot(1000, self._start_wechat_login)
            elif status == "error":
                # 登录失败
                error_msg = result.get("error", tr("auth.error.login_failed_title"))
                self.status_label.setText(tr("auth.error.generic_error", error_msg=error_msg))
                if self.polling_timer:
                    self.polling_timer.stop()
        except Exception as e:
            # 异常处理
            self.status_label.setText(tr("auth.error.status_check_failed", e=str(e)))


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
