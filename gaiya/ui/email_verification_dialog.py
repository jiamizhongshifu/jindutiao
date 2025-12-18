"""
GaiYa每日进度条 - 邮箱验证对话框
使用Supabase内置邮箱验证，替代自定义OTP方案
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
import sys
import os
import requests
import urllib3

# 禁用SSL警告（临时解决SSL兼容性问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加父目录到路径以导入core模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n.translator import tr
from gaiya.core.async_worker import AsyncNetworkWorker


class EmailVerificationDialog(QDialog):
    """邮箱验证对话框（使用Supabase邮箱验证链接）"""

    # 信号：验证成功时发出
    verification_success = Signal(dict)  # 传递用户信息

    def __init__(self, parent=None, email=None, password=None, user_id=None):
        super().__init__(parent)
        self.email = email
        self.password = password  # 用于验证成功后自动登录
        self.user_id = user_id
        self.backend_url = os.getenv("GAIYA_API_URL", "https://api.gaiyatime.com")

        # 轮询定时器
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_verification_status)
        self.check_count = 0  # 轮询次数计数
        self.max_check_count = 120  # 最多检查120次（10分钟，每5秒一次）

        self.init_ui()
        self._start_polling()  # 开始轮询

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(tr("email_verification.dialog.title"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # 图标
        icon_label = QLabel("📧")
        icon_font = QFont()
        icon_font.setPointSize(64)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(tr("email_verification.dialog.sent_title"))
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 说明文字
        desc_label = QLabel(tr("email_verification.dialog.sent_message_html", email=self.email))
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666; font-size: 14px; line-height: 1.6;")
        main_layout.addWidget(desc_label)

        # 状态标签
        self.status_label = QLabel(tr("email_verification.dialog.waiting_status"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
                background-color: #f0f9f0;
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.status_label)

        # 进度条（使用静态样式，避免无限动画导致卡顿）
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # 使用固定范围而非无限动画
        self.progress_bar.setValue(50)  # 设置为50%
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        main_layout.addStretch()

        # 提示区域
        tips_label = QLabel(tr("email_verification.dialog.tips_html"))
        tips_label.setWordWrap(True)
        tips_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 8px;
                border-left: 3px solid #2196F3;
            }
        """)
        main_layout.addWidget(tips_label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 重新发送按钮
        self.resend_button = QPushButton(tr("email_verification.button.resend"))
        self.resend_button.setMinimumHeight(40)
        self.resend_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.resend_button.clicked.connect(self._resend_verification_email)
        button_layout.addWidget(self.resend_button)

        # 取消按钮
        cancel_button = QPushButton(tr("email_verification.button.cancel"))
        cancel_button.setMinimumHeight(40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _start_polling(self):
        """开始轮询验证状态"""
        print(tr("email_verification.log.start_polling", email=self.email))
        self.check_timer.start(5000)  # 每5秒检查一次（减少频率，降低卡顿）

    def _check_verification_status(self):
        """检查验证状态"""
        self.check_count += 1

        # 超过最大检查次数，停止轮询
        if self.check_count > self.max_check_count:
            self.check_timer.stop()
            self.status_label.setText(tr("email_verification.message.timeout_warning"))
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    font-size: 15px;
                    font-weight: bold;
                    padding: 10px;
                    background-color: #fff3e0;
                    border-radius: 8px;
                }
            """)
            self.progress_bar.setVisible(False)
            return

        try:
            print(tr("email_verification.log.checking", count=self.check_count))

            response = requests.post(
                f"{self.backend_url}/api/auth-check-verification",
                json={
                    "email": self.email,
                    "user_id": self.user_id
                },
                timeout=10,
                verify=False  # 禁用SSL验证（解决Windows SSL兼容性问题）
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("verified"):
                    # 验证成功！
                    self._on_verification_success(data)
                else:
                    # 尚未验证，继续等待
                    print(tr("email_verification.log.not_verified_yet"))
            else:
                print(tr("email_verification.log.check_failed_http", status_code=response.status_code))

        except requests.exceptions.Timeout:
            print(tr("email_verification.log.check_timeout"))
        except Exception as e:
            print(tr("email_verification.log.check_error", e=str(e)))

    def _on_verification_success(self, data):
        """验证成功"""
        print(tr("email_verification.log.verified_log", email=self.email))

        # 停止轮询
        self.check_timer.stop()

        # 更新UI
        self.status_label.setText(tr("email_verification.dialog.verified_success"))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                background-color: #e8f5e9;
                border-radius: 8px;
            }
        """)
        self.progress_bar.setVisible(False)

        # 自动登录
        self._auto_login()

    def _auto_login(self):
        """验证成功后自动登录 - 异步版本，避免UI阻塞"""
        print(tr("email_verification.log.auto_login_start"))

        if not self.password:
            # 如果没有密码，只能提示用户手动登录
            QMessageBox.information(
                self,
                tr("email_verification.message.verified_success_title"),
                tr("email_verification.message.verified_success_message")
            )
            self.accept()
            return

        # ✅ 性能优化: 使用异步Worker避免UI卡顿
        from gaiya.core.auth_client import AuthClient
        auth_client = AuthClient()

        self._auto_login_worker = AsyncNetworkWorker(
            auth_client.signin,
            self.email,
            self.password
        )
        self._auto_login_worker.success.connect(self._on_auto_login_success)
        self._auto_login_worker.error.connect(self._on_auto_login_error)
        self._auto_login_worker.start()

    def _on_auto_login_success(self, result: dict):
        """自动登录成功回调"""
        if result.get("success"):
            # 登录成功
            user_info = {
                "user_id": result.get("user_id"),
                "email": result.get("email"),
                "user_tier": result.get("user_tier", "free")
            }

            print(tr("email_verification.log.auto_login_success"))

            # 发出验证成功信号（携带用户信息）
            self.verification_success.emit(user_info)

            # 关闭对话框
            self.accept()
        else:
            # 登录失败
            error_msg = result.get("error", tr("email_verification.message.login_failed_title"))
            QMessageBox.warning(
                self,
                tr("email_verification.message.auto_login_failed_title"),
                tr("email_verification.message.auto_login_failed_message", error=error_msg)
            )
            self.accept()

    def _on_auto_login_error(self, error_msg: str):
        """自动登录API失败回调"""
        print(tr("email_verification.log.auto_login_error", e=error_msg))
        QMessageBox.warning(
            self,
            tr("email_verification.message.auto_login_failed_title"),
            tr("email_verification.message.auto_login_error_message", error=error_msg)
        )
        self.accept()

    def _resend_verification_email(self):
        """重新发送验证邮件 - 异步版本，避免UI阻塞"""
        self.resend_button.setEnabled(False)
        self.resend_button.setText(tr("email_verification.button.sending"))

        # ✅ 性能优化: 使用异步Worker避免UI卡顿
        from gaiya.core.auth_client import AuthClient
        auth_client = AuthClient()

        # 使用原密码重新注册（Supabase会检测到已存在，只发送验证邮件）
        self._resend_worker = AsyncNetworkWorker(
            auth_client.signup,
            email=self.email,
            password=self.password or "temp_password_for_resend"
        )
        self._resend_worker.success.connect(self._on_resend_success)
        self._resend_worker.error.connect(self._on_resend_error)
        self._resend_worker.start()

    def _on_resend_success(self, result: dict):
        """重发验证邮件成功回调"""
        # 恢复按钮状态
        self.resend_button.setEnabled(True)
        self.resend_button.setText(tr("email_verification.button.resend"))

        if result.get("success") or "already registered" in result.get("error", "").lower():
            QMessageBox.information(
                self,
                tr("email_verification.message.resend_success_title"),
                tr("email_verification.message.resend_success_message")
            )
            # 重置计数器
            self.check_count = 0
        else:
            QMessageBox.warning(
                self,
                tr("email_verification.message.resend_failed_title"),
                result.get("error", tr("email_verification.message.resend_failed_message"))
            )

    def _on_resend_error(self, error_msg: str):
        """重发验证邮件失败回调"""
        # 恢复按钮状态
        self.resend_button.setEnabled(True)
        self.resend_button.setText(tr("email_verification.button.resend"))

        QMessageBox.critical(
            self,
            tr("email_verification.message.resend_error_title"),
            tr("email_verification.message.resend_error_message", error=error_msg)
        )

    def _on_cancel(self):
        """用户点击取消"""
        reply = QMessageBox.question(
            self,
            tr("email_verification.confirm.cancel_title"),
            tr("email_verification.confirm.cancel_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.check_timer.stop()
            self.reject()

    def closeEvent(self, event):
        """关闭对话框时停止轮询"""
        self.check_timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    # 测试EmailVerificationDialog
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = EmailVerificationDialog(
        email="test@example.com",
        password="test123",
        user_id="test-user-id"
    )

    def on_success(user_info):
        print(f"验证成功！用户信息：{user_info}")

    dialog.verification_success.connect(on_success)
    dialog.exec()

    sys.exit(app.exec())
