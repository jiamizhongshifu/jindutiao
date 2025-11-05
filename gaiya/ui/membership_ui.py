"""
GaiYa每日进度条 - 会员购买UI模块
提供会员套餐选择和支付功能
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QMessageBox, QWidget,
    QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QFont, QDesktopServices
import sys
import os

# 添加父目录到路径以导入core模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_client import AuthClient


class MembershipDialog(QDialog):
    """会员购买对话框"""

    # 信号：购买成功时发出
    purchase_success = Signal(str)  # 传递plan_type

    def __init__(self, auth_client: AuthClient = None, parent=None):
        super().__init__(parent)
        self.auth_client = auth_client or AuthClient()

        # 检查登录状态
        if not self.auth_client.is_logged_in():
            QMessageBox.warning(
                parent,
                "未登录",
                "请先登录后再购买会员"
            )
            self.reject()
            return

        self.selected_plan = None
        self.selected_pay_type = "alipay"
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("升级到专业版")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("选择您的会员套餐")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 当前用户信息
        user_email = self.auth_client.get_user_email()
        user_tier = self.auth_client.get_user_tier()
        user_info_label = QLabel(f"当前账户: {user_email} | 当前等级: {self._get_tier_name(user_tier)}")
        user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_info_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(user_info_label)

        # 套餐选择区域
        plans_widget = self._create_plans_widget()
        main_layout.addWidget(plans_widget)

        # 支付方式选择
        payment_method_widget = self._create_payment_method_widget()
        main_layout.addWidget(payment_method_widget)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setMinimumSize(100, 40)
        cancel_button.clicked.connect(self.reject)

        self.purchase_button = QPushButton("立即购买")
        self.purchase_button.setMinimumSize(150, 40)
        self.purchase_button.setStyleSheet("""
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
        self.purchase_button.clicked.connect(self._on_purchase_clicked)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.purchase_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _create_plans_widget(self) -> QWidget:
        """创建套餐选择组件"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(20)

        # 套餐按钮组
        self.plan_button_group = QButtonGroup()

        # 月度套餐
        monthly_plan = self._create_plan_card(
            plan_type="pro_monthly",
            title="月度会员",
            price="9.9",
            unit="元/月",
            features=[
                "每日智能任务规划 50次/天",
                "每周进度报告 10次/周",
                "AI对话助手 100次/天",
                "自定义主题和样式",
                "所有高级功能"
            ]
        )
        self.plan_button_group.addButton(monthly_plan)
        layout.addWidget(monthly_plan)

        # 年度套餐（推荐）
        yearly_plan = self._create_plan_card(
            plan_type="pro_yearly",
            title="年度会员",
            price="99",
            unit="元/年",
            features=[
                "所有月度会员功能",
                "节省20元（相当于8.3元/月）",
                "优先客服支持",
                "未来新功能优先体验"
            ],
            recommended=True
        )
        self.plan_button_group.addButton(yearly_plan)
        layout.addWidget(yearly_plan)

        # 终身会员
        lifetime_plan = self._create_plan_card(
            plan_type="lifetime",
            title="终身会员",
            price="299",
            unit="元/终身",
            features=[
                "所有会员功能永久使用",
                "一次付费，终身享受",
                "未来所有新功能免费",
                "VIP客服支持"
            ]
        )
        self.plan_button_group.addButton(lifetime_plan)
        layout.addWidget(lifetime_plan)

        widget.setLayout(layout)
        return widget

    def _create_plan_card(
        self,
        plan_type: str,
        title: str,
        price: str,
        unit: str,
        features: list,
        recommended: bool = False
    ) -> QRadioButton:
        """创建套餐卡片"""
        # 使用自定义的GroupBox作为卡片
        card = QRadioButton()
        card.setProperty("plan_type", plan_type)

        # 卡片布局
        card_layout = QVBoxLayout()
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # 推荐标签
        if recommended:
            recommend_label = QLabel("⭐ 推荐")
            recommend_label.setStyleSheet("""
                background-color: #FF9800;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            """)
            recommend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(recommend_label)

        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)

        # 价格
        price_label = QLabel(f"¥{price}")
        price_font = QFont()
        price_font.setPointSize(24)
        price_font.setBold(True)
        price_label.setFont(price_font)
        price_label.setStyleSheet("color: #4CAF50;")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(price_label)

        # 单位
        unit_label = QLabel(unit)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_label.setStyleSheet("color: #666; font-size: 12px;")
        card_layout.addWidget(unit_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        card_layout.addWidget(separator)

        # 功能列表
        for feature in features:
            feature_label = QLabel(f"✓ {feature}")
            feature_label.setWordWrap(True)
            feature_label.setStyleSheet("color: #333; font-size: 13px;")
            card_layout.addWidget(feature_label)

        card_layout.addStretch()

        # 创建容器Widget
        container = QWidget()
        container.setLayout(card_layout)
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 10px;
            }
        """)

        # 将容器设置为RadioButton的样式
        card.setText("")  # 隐藏默认文本
        card.setStyleSheet("""
            QRadioButton {
                min-width: 180px;
                min-height: 400px;
            }
            QRadioButton::indicator {
                width: 0px;
                height: 0px;
            }
            QRadioButton:checked {
                border: 3px solid #4CAF50;
                border-radius: 10px;
            }
        """)

        # 点击时更新选中状态
        card.toggled.connect(lambda checked: self._on_plan_selected(plan_type) if checked else None)

        return card

    def _create_payment_method_widget(self) -> QGroupBox:
        """创建支付方式选择组件"""
        group_box = QGroupBox("支付方式")
        layout = QHBoxLayout()

        # 支付方式按钮组
        self.payment_button_group = QButtonGroup()

        # 支付宝
        alipay_radio = QRadioButton("支付宝")
        alipay_radio.setProperty("pay_type", "alipay")
        alipay_radio.setChecked(True)
        self.payment_button_group.addButton(alipay_radio)
        layout.addWidget(alipay_radio)

        # 微信支付
        wxpay_radio = QRadioButton("微信支付")
        wxpay_radio.setProperty("pay_type", "wxpay")
        self.payment_button_group.addButton(wxpay_radio)
        layout.addWidget(wxpay_radio)

        layout.addStretch()

        # 监听选择变化
        self.payment_button_group.buttonClicked.connect(self._on_payment_method_changed)

        group_box.setLayout(layout)
        return group_box

    def _on_plan_selected(self, plan_type: str):
        """套餐选择变化"""
        self.selected_plan = plan_type

    def _on_payment_method_changed(self, button):
        """支付方式变化"""
        self.selected_pay_type = button.property("pay_type")

    def _on_purchase_clicked(self):
        """处理购买按钮点击"""
        if not self.selected_plan:
            QMessageBox.warning(self, "未选择套餐", "请选择一个会员套餐")
            return

        # 禁用购买按钮
        self.purchase_button.setEnabled(False)
        self.purchase_button.setText("正在创建订单...")

        # 创建支付订单
        user_id = self.auth_client.get_user_id()
        result = self.auth_client.create_payment_order(
            plan_type=self.selected_plan,
            pay_type=self.selected_pay_type
        )

        # 恢复按钮状态
        self.purchase_button.setEnabled(True)
        self.purchase_button.setText("立即购买")

        if result.get("success"):
            # 订单创建成功
            payment_url = result.get("payment_url")
            out_trade_no = result.get("out_trade_no")
            amount = result.get("amount")
            plan_name = result.get("plan_name")

            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                "订单已创建",
                f"订单信息:\n"
                f"套餐: {plan_name}\n"
                f"金额: ¥{amount}\n"
                f"支付方式: {self._get_pay_type_name(self.selected_pay_type)}\n"
                f"订单号: {out_trade_no}\n\n"
                f"点击'确定'将在浏览器中打开支付页面",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Ok:
                # 在浏览器中打开支付URL
                QDesktopServices.openUrl(QUrl(payment_url))

                # 开始轮询支付状态
                self._start_payment_polling(out_trade_no)

        else:
            # 订单创建失败
            error_msg = result.get("error", "创建订单失败")
            QMessageBox.critical(self, "创建订单失败", f"创建订单失败：{error_msg}")

    def _start_payment_polling(self, out_trade_no: str):
        """开始轮询支付状态"""
        # 显示等待对话框
        self.payment_polling_dialog = QMessageBox(self)
        self.payment_polling_dialog.setWindowTitle("等待支付")
        self.payment_polling_dialog.setText(
            "正在等待支付完成...\n\n"
            "请在打开的浏览器页面中完成支付。\n"
            "支付完成后，此窗口将自动关闭。"
        )
        self.payment_polling_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
        self.payment_polling_dialog.setIcon(QMessageBox.Icon.Information)

        # 创建定时器轮询支付状态
        self.payment_timer = QTimer()
        self.payment_timer.setInterval(3000)  # 每3秒查询一次
        self.payment_timer.timeout.connect(lambda: self._check_payment_status(out_trade_no))
        self.payment_timer.start()

        # 监听取消按钮
        self.payment_polling_dialog.rejected.connect(self._stop_payment_polling)

        # 显示对话框（非阻塞）
        self.payment_polling_dialog.show()

    def _check_payment_status(self, out_trade_no: str):
        """检查支付状态"""
        result = self.auth_client.query_payment_order(out_trade_no)

        if result.get("success"):
            order = result.get("order", {})
            status = order.get("status")

            if status == "paid":
                # 支付成功
                self._stop_payment_polling()

                QMessageBox.information(
                    self,
                    "支付成功",
                    "支付已完成！\n您的会员权益已激活。\n\n请重新启动应用以生效。"
                )

                # 发出购买成功信号
                self.purchase_success.emit(self.selected_plan)

                # 关闭对话框
                self.accept()

    def _stop_payment_polling(self):
        """停止支付状态轮询"""
        if hasattr(self, 'payment_timer'):
            self.payment_timer.stop()

        if hasattr(self, 'payment_polling_dialog'):
            self.payment_polling_dialog.close()

    def _get_tier_name(self, tier: str) -> str:
        """获取会员等级名称"""
        tier_names = {
            "free": "免费版",
            "pro": "专业版",
            "lifetime": "终身会员"
        }
        return tier_names.get(tier, tier)

    def _get_pay_type_name(self, pay_type: str) -> str:
        """获取支付方式名称"""
        pay_type_names = {
            "alipay": "支付宝",
            "wxpay": "微信支付"
        }
        return pay_type_names.get(pay_type, pay_type)

    def closeEvent(self, event):
        """关闭事件"""
        # 停止支付轮询
        self._stop_payment_polling()
        super().closeEvent(event)


if __name__ == "__main__":
    # 测试会员购买对话框
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 需要先登录
    auth_client = AuthClient()
    if not auth_client.is_logged_in():
        print("请先运行 auth_ui.py 登录")
        sys.exit(1)

    dialog = MembershipDialog(auth_client)

    def on_purchase_success(plan_type):
        print(f"购买成功！套餐: {plan_type}")

    dialog.purchase_success.connect(on_purchase_success)
    dialog.exec()

    sys.exit(app.exec())
