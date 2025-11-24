"""
GaiYa每日进度条 - OTP验证对话框
用于邮箱验证和密码重置的OTP输入界面
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIntValidator
import sys
import os
import requests
import urllib3

# 禁用SSL警告（临时解决SSL兼容性问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加父目录到路径以导入core模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n.translator import tr


class OTPDialog(QDialog):
    """OTP验证对话框"""

    # 信号：验证成功时发出
    verification_success = Signal()

    def __init__(self, parent=None, email=None, purpose="signup"):
        super().__init__(parent)
        self.email = email
        self.purpose = purpose  # signup, password_reset
        self.backend_url = os.getenv("GAIYA_API_URL", "https://api.gaiyatime.com")

        # 倒计时相关
        self.countdown = 60
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._update_countdown)

        self.init_ui()
        self._send_otp()  # 自动发送OTP

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(tr("otp.dialog.title"))
        self.setMinimumWidth(450)
        self.setMinimumHeight(350)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # 图标
        icon_label = QLabel("📧")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(tr("otp.dialog.sent_title"))
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 说明文字
        desc_label = QLabel(tr("otp.dialog.sent_message_html", email=self.email))
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666; font-size: 13px;")
        main_layout.addWidget(desc_label)

        # OTP输入框布局
        otp_layout = QHBoxLayout()
        otp_layout.setSpacing(10)
        self.otp_inputs = []

        for i in range(6):
            input_field = QLineEdit()
            input_field.setMaxLength(1)
            input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            input_field.setValidator(QIntValidator(0, 9))  # 只允许数字
            input_field.setMinimumSize(50, 60)
            input_field.setMaximumSize(50, 60)
            input_field.setStyleSheet("""
                QLineEdit {
                    font-size: 24px;
                    font-weight: bold;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    padding: 10px;
                }
                QLineEdit:focus {
                    border-color: #4CAF50;
                }
            """)

            # 自动跳转到下一个输入框
            input_field.textChanged.connect(
                lambda text, idx=i: self._on_digit_entered(text, idx)
            )

            otp_layout.addWidget(input_field)
            self.otp_inputs.append(input_field)

        main_layout.addLayout(otp_layout)

        # 重新发送按钮
        resend_layout = QHBoxLayout()
        resend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.resend_label = QLabel(tr("otp.dialog.no_code_question"))
        self.resend_label.setStyleSheet("color: #666; font-size: 12px;")

        self.resend_button = QPushButton(tr("otp.button.resend_countdown", countdown=60))
        self.resend_button.setFlat(True)
        self.resend_button.setEnabled(False)
        self.resend_button.setStyleSheet("""
            QPushButton {
                color: #4CAF50;
                text-decoration: underline;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #45a049;
            }
            QPushButton:disabled {
                color: #ccc;
            }
        """)
        self.resend_button.clicked.connect(self._send_otp)

        resend_layout.addWidget(self.resend_label)
        resend_layout.addWidget(self.resend_button)

        main_layout.addLayout(resend_layout)

        # 验证按钮
        self.verify_button = QPushButton(tr("otp.button.verify"))
        self.verify_button.setMinimumHeight(45)
        self.verify_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
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
        self.verify_button.clicked.connect(self._on_verify_clicked)
        main_layout.addWidget(self.verify_button)

        # 取消按钮
        cancel_button = QPushButton(tr("otp.button.cancel"))
        cancel_button.setFlat(True)
        cancel_button.setStyleSheet("color: #999;")
        cancel_button.clicked.connect(self.reject)
        main_layout.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch()
        self.setLayout(main_layout)

        # 焦点设置到第一个输入框
        self.otp_inputs[0].setFocus()

    def _on_digit_entered(self, text: str, index: int):
        """处理数字输入"""
        if text and index < 5:
            # 自动跳转到下一个输入框
            self.otp_inputs[index + 1].setFocus()

        # 检查是否所有输入框都填满
        if all(input_field.text() for input_field in self.otp_inputs):
            self.verify_button.setEnabled(True)
            # 自动触发验证
            self._on_verify_clicked()
        else:
            self.verify_button.setEnabled(False)

    def _send_otp(self):
        """发送OTP验证码"""
        try:
            self.resend_button.setEnabled(False)
            self.resend_button.setText(tr("otp.button.sending"))

            response = requests.post(
                f"{self.backend_url}/api/auth-send-otp",
                json={
                    "email": self.email,
                    "purpose": self.purpose
                },
                timeout=10,
                verify=False  # 禁用SSL验证（解决Windows SSL兼容性问题）
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 启动倒计时
                    self.countdown = 60
                    self.countdown_timer.start(1000)
                    # 不弹窗提示，用户已经在对话框中看到说明文字了
                else:
                    QMessageBox.warning(
                        self,
                        tr("otp.message.send_failed_title"),
                        data.get("error", tr("otp.message.send_failed_message"))
                    )
                    self.resend_button.setEnabled(True)
                    self.resend_button.setText(tr("otp.button.resend"))
            else:
                QMessageBox.critical(
                    self,
                    tr("otp.message.network_error_title"),
                    f"HTTP {response.status_code}"
                )
                self.resend_button.setEnabled(True)
                self.resend_button.setText(tr("otp.button.resend"))

        except requests.exceptions.Timeout:
            QMessageBox.critical(self, tr("otp.message.timeout_title"), tr("otp.message.timeout_message"))
            self.resend_button.setEnabled(True)
            self.resend_button.setText(tr("otp.button.resend"))
        except Exception as e:
            QMessageBox.critical(self, tr("otp.message.error_title"), tr("otp.message.send_error_message", error=str(e)))
            self.resend_button.setEnabled(True)
            self.resend_button.setText(tr("otp.button.resend"))

    def _update_countdown(self):
        """更新倒计时"""
        self.countdown -= 1

        if self.countdown > 0:
            self.resend_button.setText(tr("otp.button.resend_countdown", countdown=self.countdown))
        else:
            self.countdown_timer.stop()
            self.resend_button.setEnabled(True)
            self.resend_button.setText(tr("otp.button.resend"))

    def _on_verify_clicked(self):
        """处理验证按钮点击"""
        # 获取输入的OTP
        otp_code = "".join(input_field.text() for input_field in self.otp_inputs)

        if len(otp_code) != 6:
            QMessageBox.warning(self, tr("otp.message.input_error_title"), tr("otp.message.input_error_message"))
            return

        # 禁用按钮
        self.verify_button.setEnabled(False)
        self.verify_button.setText(tr("otp.button.verifying"))

        try:
            response = requests.post(
                f"{self.backend_url}/api/auth-verify-otp",
                json={
                    "email": self.email,
                    "otp_code": otp_code
                },
                timeout=10,
                verify=False  # 禁用SSL验证（解决Windows SSL兼容性问题）
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    QMessageBox.information(
                        self,
                        tr("otp.message.verify_success_title"),
                        tr("otp.message.verify_success_message")
                    )

                    # 发出成功信号
                    self.verification_success.emit()

                    # 关闭对话框
                    self.accept()
                else:
                    error_msg = data.get("error", tr("otp.message.verify_failed_message"))
                    QMessageBox.warning(self, tr("otp.message.verify_failed_title"), error_msg)

                    # 清空输入框
                    for input_field in self.otp_inputs:
                        input_field.clear()
                    self.otp_inputs[0].setFocus()
            else:
                QMessageBox.critical(
                    self,
                    tr("otp.message.network_error_title"),
                    f"HTTP {response.status_code}"
                )

        except Exception as e:
            QMessageBox.critical(self, tr("otp.message.error_title"), tr("otp.message.verify_error_message", error=str(e)))

        finally:
            self.verify_button.setEnabled(True)
            self.verify_button.setText(tr("otp.button.verify"))


if __name__ == "__main__":
    # 测试OTP对话框
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = OTPDialog(email="test@example.com")

    def on_success():
        print(tr("otp.message.final_success_message"))

    dialog.verification_success.connect(on_success)
    dialog.exec()

    sys.exit(app.exec())
