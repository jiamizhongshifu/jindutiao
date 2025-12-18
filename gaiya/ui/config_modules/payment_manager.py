"""
GaiYa Config Modules - Payment Manager
Handles all payment-related functionality for the configuration window.

Extracted from config_gui.py to improve maintainability.
"""
import logging
from functools import partial
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QProgressDialog
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import QRectF, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class PaymentOptionCard(QWidget):
    """Payment option card widget - uses QPainter for reliable rendering in PyInstaller

    Card-based selection without radio buttons:
    - Normal: white background + 2px gray border #D0D0D0
    - Hover: light gray background + darker border #999999
    - Selected: white background + 3px cyan border #4ECDC4 (matches plan cards)

    Implementation note:
    Uses QPainter manual drawing instead of setStyleSheet to avoid PyInstaller
    packaging issues where stylesheet borders appear on child components instead
    of parent container (reference: membership_ui.py SolidCardWidget).
    """

    # Signal emitted when card is clicked with payment method ID
    clicked = Signal(str)

    def __init__(self, pay_method_id, parent=None):
        super().__init__(parent)
        self._pay_method_id = pay_method_id
        self._is_selected = False
        self._is_hovering = False

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # CRITICAL: Clear QWidget default border and background (prevents black border in packaging)
        self.setStyleSheet("""
            PaymentOptionCard {
                border: none;
                background: transparent;
            }
        """)

        # CRITICAL: Disable focus to prevent Windows from drawing black focus frame
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # CRITICAL: Disable system default rendering (exactly like SolidCardWidget)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)

        self.setMinimumHeight(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, selected: bool):
        """Set selection state and trigger repaint"""
        self._is_selected = selected
        self.update()  # Trigger paintEvent

    def enterEvent(self, event):
        """Mouse enter event - trigger hover state"""
        self._is_hovering = True
        self.update()  # Trigger paintEvent
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse leave event - clear hover state"""
        self._is_hovering = False
        self.update()  # Trigger paintEvent
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Mouse press event - emit clicked signal"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._pay_method_id)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        """Manual drawing using QPainter - ensures consistent rendering in PyInstaller"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Anti-aliasing for smooth edges

        rect = self.rect()

        # 1. Draw background
        if self._is_selected:
            bg_color = QColor("#FFFFFF")  # White
        elif self._is_hovering:
            bg_color = QColor("#EEEEEE")  # Light gray
        else:
            bg_color = QColor("#FFFFFF")  # White

        # Create rounded rectangle path
        border_radius = 8
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), border_radius, border_radius)

        painter.fillPath(path, QBrush(bg_color))

        # 2. Draw border
        if self._is_selected:
            # Selected: cyan thick border (3px #4ECDC4)
            pen = QPen(QColor("#4ECDC4"), 3)
        elif self._is_hovering:
            # Hover: dark gray border (2px #999999)
            pen = QPen(QColor("#999999"), 2)
        else:
            # Normal: light gray border (2px #D0D0D0)
            pen = QPen(QColor("#D0D0D0"), 2)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Adjust rect to prevent border clipping
        border_width = 3 if self._is_selected else 2
        adjusted_rect = rect.adjusted(
            border_width // 2,
            border_width // 2,
            -border_width // 2,
            -border_width // 2
        )

        path_border = QPainterPath()
        path_border.addRoundedRect(QRectF(adjusted_rect), border_radius, border_radius)
        painter.drawPath(path_border)

        painter.end()


class PaymentManager(QObject):
    """Manages all payment-related functionality.

    Signals:
        payment_started: Emitted when a payment process begins
        payment_success: Emitted when payment is confirmed successful
        payment_failed: Emitted when payment fails (with error message)
        subscription_refreshed: Emitted when subscription status is updated
    """

    # Signals for payment events
    payment_started = Signal(str)  # plan_id
    payment_success = Signal(str, str)  # plan_name, tier
    payment_failed = Signal(str)  # error_message
    subscription_refreshed = Signal()

    # Plan information mapping
    PLAN_INFO = {
        "pro_monthly": {"name": "Pro 月度", "price_cny": "¥29", "price_usd": "$4.99", "period": "/月"},
        "pro_yearly": {"name": "Pro 年度", "price_cny": "¥199", "price_usd": "$39.99", "period": "/年"},
        "lifetime": {"name": "会员合伙人", "price_cny": "¥599", "price_usd": "$89.99", "period": ""}
    }

    # Plan name to type mapping
    PLAN_TYPE_MAP = {
        "Pro月度订阅": "pro_monthly",
        "Pro年度订阅": "pro_yearly",
        "团队合伙人": "team_partner"
    }

    def __init__(self, parent_widget: QWidget, i18n=None, ai_client=None):
        """Initialize PaymentManager.

        Args:
            parent_widget: Parent widget for dialogs
            i18n: Internationalization translator instance
            ai_client: AI client instance for tier synchronization
        """
        super().__init__(parent_widget)
        self._parent = parent_widget
        self._i18n = i18n
        self._ai_client = ai_client

        # Payment state
        self._current_pay_type: Optional[str] = None
        self._current_plan_id: Optional[str] = None
        self.selected_plan_id: Optional[str] = None

        # Dialog and timer references
        self.payment_polling_dialog: Optional[QDialog] = None
        self.payment_timer: Optional[QTimer] = None
        self.current_out_trade_no: Optional[str] = None
        self.current_trade_no: Optional[str] = None
        self.current_plan_name: Optional[str] = None

        # Network manager for QR code downloads
        self.network_manager: Optional[QNetworkAccessManager] = None

        # Worker references (prevent garbage collection)
        self._payment_worker = None
        self._payment_progress: Optional[QProgressDialog] = None
        self._status_check_worker = None
        self._manual_upgrade_worker = None
        self._subscription_refresh_worker = None
        self._manual_upgrade_context: Dict[str, Any] = {}

    def tr(self, key: str) -> str:
        """Translate a key using i18n if available."""
        if self._i18n:
            return self._i18n.tr(key)
        return key

    def show_payment_method_dialog(self, plan_id: str):
        """Display payment method selection dialog.

        Args:
            plan_id: The plan identifier (e.g., 'pro_monthly', 'pro_yearly', 'lifetime')
        """
        plan = self.PLAN_INFO.get(plan_id, {})

        # Add defensive check for empty plan
        if not plan:
            QMessageBox.warning(
                self._parent,
                "错误",
                f"无效的套餐ID: {plan_id}\n\n请联系客服处理。"
            )
            return

        # Create dialog
        dialog = QDialog(self._parent)
        dialog.setWindowTitle(self.tr("account.select_payment_method"))
        dialog.setFixedWidth(420)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_text = f"您选择的套餐：{plan['name']} - {plan['price_cny']}{plan['period']}"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                background: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Separator
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(separator)

        # Hint text
        hint_label = QLabel("请选择支付方式：")
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
                background: transparent;
            }
        """)
        layout.addWidget(hint_label)

        # Track selected payment method
        selected_payment = ["alipay"]  # Use list to allow modification in nested function

        # Create payment cards
        alipay_card = self._create_payment_option_card(
            "alipay",
            "🔵 支付宝",
            f"{plan['price_cny']}{plan['period']}",
            ""
        )
        layout.addWidget(alipay_card)

        wxpay_card = self._create_payment_option_card(
            "wxpay",
            "💚 微信支付",
            f"{plan['price_cny']}{plan['period']}",
            ""
        )
        layout.addWidget(wxpay_card)

        stripe_card = self._create_payment_option_card(
            "stripe",
            "💳 国际支付 (Stripe)",
            f"{plan['price_usd']}{plan['period']}",
            "支持 Visa/Mastercard/Amex"
        )
        layout.addWidget(stripe_card)

        # Store cards for easy access
        cards = {
            "alipay": alipay_card,
            "wxpay": wxpay_card,
            "stripe": stripe_card
        }

        # Handle card selection
        def on_card_clicked(pay_method_id):
            """Update selection when card is clicked"""
            selected_payment[0] = pay_method_id
            # Update visual state of all cards
            for method_id, card in cards.items():
                card.set_selected(method_id == pay_method_id)

        # Connect card click signals
        alipay_card.clicked.connect(on_card_clicked)
        wxpay_card.clicked.connect(on_card_clicked)
        stripe_card.clicked.connect(on_card_clicked)

        # Set initial selection (alipay)
        on_card_clicked("alipay")

        layout.addSpacing(10)

        # Button area
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        cancel_button = QPushButton(self.tr("button.cancel"))
        cancel_button.setFixedHeight(40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666666;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        confirm_button = QPushButton(self.tr("membership.payment.confirm_payment"))
        confirm_button.setFixedHeight(40)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        def on_confirm():
            """Handle confirm button click - use selected payment method"""
            pay_method = selected_payment[0]
            dialog.accept()

            if pay_method == "alipay":
                self.on_alipay_selected(plan_id)
            elif pay_method == "wxpay":
                self.on_wxpay_selected(plan_id)
            elif pay_method == "stripe":
                self.on_stripe_selected(plan_id)

        confirm_button.clicked.connect(on_confirm)
        button_layout.addWidget(confirm_button)

        layout.addLayout(button_layout)

        # Show dialog
        dialog.exec()

    def _create_payment_option_card(self, pay_method_id: str, title: str, price: str, subtitle: str) -> PaymentOptionCard:
        """Create a payment option card widget.

        Args:
            pay_method_id: Payment method identifier
            title: Card title (e.g., "🔵 支付宝")
            price: Price display text
            subtitle: Optional subtitle text

        Returns:
            PaymentOptionCard widget
        """
        card = PaymentOptionCard(pay_method_id)

        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(15)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        # Title and price in one row
        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #333333;
                background: transparent;
                border: none;
            }
        """)
        title_row.addWidget(title_label)

        title_row.addStretch()

        price_label = QLabel(price)
        price_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                background: transparent;
                border: none;
            }
        """)
        title_row.addWidget(price_label)

        content_layout.addLayout(title_row)

        # Subtitle (if provided)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #666666;
                    background: transparent;
                    border: none;
                }
            """)
            content_layout.addWidget(subtitle_label)

        main_layout.addLayout(content_layout)

        return card

    def on_alipay_selected(self, plan_id: str):
        """Handle Alipay payment selection.

        Args:
            plan_id: The plan identifier
        """
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker

        pay_type = "alipay"
        self._current_pay_type = pay_type
        self._current_plan_id = plan_id

        logging.info(f"[支付调试] 支付宝支付 - plan_type: {plan_id}, pay_type: {pay_type}")

        # Create progress dialog
        self._payment_progress = QProgressDialog(
            "正在创建支付订单...",
            "取消",
            0, 0,  # Indeterminate progress bar
            self._parent
        )
        self._payment_progress.setWindowTitle("请稍候")
        self._payment_progress.setWindowModality(Qt.WindowModal)
        self._payment_progress.setMinimumDuration(0)  # Show immediately
        self._payment_progress.show()

        # Use async worker to avoid UI blocking
        auth_client = AuthClient()
        self._payment_worker = AsyncNetworkWorker(
            auth_client.create_payment_order,
            plan_type=plan_id,
            pay_type=pay_type
        )
        self._payment_worker.success.connect(self._on_alipay_order_created)
        self._payment_worker.error.connect(self._on_payment_error)
        self._payment_worker.start()

        self.payment_started.emit(plan_id)

    def _on_alipay_order_created(self, result: dict):
        """Callback for successful Alipay order creation.

        Args:
            result: API response containing order details
        """
        from gaiya.core.auth_client import AuthClient

        # Close progress dialog
        if self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        logging.info(f"[支付调试] 支付宝订单创建结果: {result}")

        if result.get("success"):
            # Get order details
            qrcode_url = result.get("qrcode_url")
            out_trade_no = result.get("out_trade_no")
            trade_no = result.get("trade_no")
            amount = result.get("amount")
            plan_name = result.get("plan_name", "Pro月度订阅")
            pay_type = self._current_pay_type or result.get("pay_type", "") or "alipay"

            if pay_type == "alipay":
                pay_type_name = "支付宝"
            elif pay_type == "wxpay":
                pay_type_name = "微信支付"
            else:
                pay_type_name = "支付宝或微信"

            logging.info(f"[PAYMENT] Order created: {out_trade_no}, trade_no: {trade_no}")
            logging.info(f"[PAYMENT] QR code URL: {qrcode_url[:80] if qrcode_url else 'None'}...")

            # Create QR code payment dialog
            self._show_qr_payment_dialog(
                qrcode_url, out_trade_no, trade_no, amount, plan_name, pay_type_name
            )
        else:
            self._handle_order_creation_error(result, "alipay")

    def _show_qr_payment_dialog(self, qrcode_url: str, out_trade_no: str, trade_no: str,
                                 amount: float, plan_name: str, pay_type_name: str):
        """Display QR code payment dialog.

        Args:
            qrcode_url: URL to the QR code image
            out_trade_no: External trade number
            trade_no: Internal trade number
            amount: Payment amount
            plan_name: Plan display name
            pay_type_name: Payment method display name
        """
        from gaiya.core.auth_client import AuthClient

        dialog = QDialog(self._parent)
        dialog.setWindowTitle("扫码支付")
        dialog.setModal(True)
        dialog.setMinimumSize(400, 500)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel(f"购买 {plan_name}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Amount
        amount_label = QLabel(f"¥{amount:.2f}")
        amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        amount_label.setStyleSheet("font-size: 24px; color: #FF6B35; font-weight: bold;")
        layout.addWidget(amount_label)

        # QR code placeholder
        qr_label = QLabel("正在加载二维码...")
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_label.setMinimumSize(300, 300)
        qr_label.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 8px;")
        layout.addWidget(qr_label)

        # Hint
        hint = QLabel(f"请使用{pay_type_name}扫描二维码完成支付")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(hint)

        # Order number
        order_label = QLabel(f"订单号: {out_trade_no}")
        order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        order_label.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(order_label)

        # Button layout
        button_layout = QHBoxLayout()

        # Cancel button
        cancel_btn = QPushButton("取消支付")
        cancel_btn.clicked.connect(lambda: self._cancel_payment_dialog(dialog))
        button_layout.addWidget(cancel_btn)

        # Confirm payment button
        confirm_btn = QPushButton("已完成支付")
        confirm_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        confirm_btn.clicked.connect(lambda: self.confirm_payment_manually(dialog, out_trade_no, plan_name))
        button_layout.addWidget(confirm_btn)

        layout.addLayout(button_layout)

        # Save dialog reference
        self.payment_polling_dialog = dialog
        self.current_out_trade_no = out_trade_no
        self.current_trade_no = trade_no
        self.current_plan_name = plan_name

        # Download and display QR code
        self._download_qrcode(qrcode_url, qr_label)

        # Start payment status polling
        auth_client = AuthClient()
        self.payment_timer = QTimer()
        self.payment_timer.setInterval(3000)
        self.payment_timer.timeout.connect(partial(self._check_payment_status, out_trade_no, trade_no, auth_client))
        self.payment_timer.start()

        # Show dialog
        dialog.exec()

    def _download_qrcode(self, qrcode_url: str, qr_label: QLabel):
        """Download and display QR code image.

        Args:
            qrcode_url: URL to the QR code image
            qr_label: Label widget to display the QR code
        """
        if not self.network_manager:
            self.network_manager = QNetworkAccessManager(self._parent)

        request = QNetworkRequest(QUrl(qrcode_url))
        reply = self.network_manager.get(request)

        def on_finished():
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                pixmap = QPixmap()
                pixmap.loadFromData(data)

                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    qr_label.setPixmap(scaled_pixmap)
                    logging.info("[PAYMENT] QR code loaded successfully")
                else:
                    qr_label.setText("二维码加载失败\n请刷新重试")
                    logging.error("[PAYMENT] Failed to parse QR code image")
            else:
                error_msg = reply.errorString()
                qr_label.setText(f"二维码加载失败\n{error_msg}")
                logging.error(f"[PAYMENT] Failed to download QR code: {error_msg}")

            reply.deleteLater()

        reply.finished.connect(on_finished)

    def _handle_order_creation_error(self, result: dict, pay_type: str):
        """Handle order creation error.

        Args:
            result: API response with error details
            pay_type: Payment type that failed
        """
        error_msg = result.get("error", "创建订单失败")
        plan_id = self._current_plan_id

        if "MERCHANT_STATUS_NOT_NORMAL" in error_msg or "渠道" in error_msg:
            detailed_msg = (
                f"支付渠道暂时不可用：{error_msg}\n\n"
                "可能的原因：\n"
                "• 支付渠道临时维护中\n"
                "• 需要在商户后台完成渠道签约\n\n"
                "建议操作：\n"
                "1. 稍后重试（5-10分钟后）\n"
                "2. 联系支付服务商客服（zpayz.cn）"
            )
            logging.error(f"[PAYMENT] Channel error: {error_msg}")
        else:
            detailed_msg = (
                f"创建订单失败：{error_msg}\n\n"
                f"调试信息：\n"
                f"• 套餐类型: {plan_id}\n"
                f"• 支付方式: {pay_type}"
            )
            logging.error(f"[PAYMENT] Create order failed - plan_type: {plan_id}, error: {error_msg}")

        QMessageBox.critical(self._parent, self.tr("membership.payment.create_order_failed"), detailed_msg)
        self.payment_failed.emit(error_msg)

    def on_wxpay_selected(self, plan_id: str):
        """Handle WeChat Pay selection.

        Args:
            plan_id: The plan identifier
        """
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker

        pay_type = "wxpay"
        self._current_pay_type = pay_type
        self._current_plan_id = plan_id

        logging.info(f"[支付调试] 微信支付 - plan_type: {plan_id}, pay_type: {pay_type}")

        # Create progress dialog
        self._payment_progress = QProgressDialog(
            "正在创建支付订单...",
            "取消",
            0, 0,
            self._parent
        )
        self._payment_progress.setWindowTitle("请稍候")
        self._payment_progress.setWindowModality(Qt.WindowModal)
        self._payment_progress.setMinimumDuration(0)
        self._payment_progress.show()

        # Use async worker
        auth_client = AuthClient()
        self._payment_worker = AsyncNetworkWorker(
            auth_client.create_payment_order,
            plan_type=plan_id,
            pay_type=pay_type
        )
        self._payment_worker.success.connect(self._on_wxpay_order_created)
        self._payment_worker.error.connect(self._on_payment_error)
        self._payment_worker.start()

        self.payment_started.emit(plan_id)

    def _on_wxpay_order_created(self, result: dict):
        """Callback for successful WeChat Pay order creation.

        Args:
            result: API response containing order details
        """
        # Close progress dialog
        if self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        logging.info(f"[支付调试] 微信支付订单创建结果: {result}")

        if result.get("success"):
            # Get order details
            qrcode_url = result.get("qrcode_url")
            out_trade_no = result.get("out_trade_no")
            trade_no = result.get("trade_no")
            amount = result.get("amount")
            plan_name = result.get("plan_name", "Pro月度订阅")
            pay_type = self._current_pay_type or result.get("pay_type", "") or "wxpay"

            if pay_type == "alipay":
                pay_type_name = "支付宝"
            elif pay_type == "wxpay":
                pay_type_name = "微信支付"
            else:
                pay_type_name = "支付宝或微信"

            logging.info(f"[PAYMENT] Order created: {out_trade_no}, trade_no: {trade_no}")
            logging.info(f"[PAYMENT] QR code URL: {qrcode_url[:80] if qrcode_url else 'None'}...")

            # Create QR code payment dialog
            self._show_qr_payment_dialog(
                qrcode_url, out_trade_no, trade_no, amount, plan_name, pay_type_name
            )
        else:
            self._handle_order_creation_error(result, "wxpay")

    def _on_payment_error(self, error_msg: str):
        """Handle payment order creation error.

        Args:
            error_msg: Error message from the API
        """
        # Close progress dialog
        if self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        # Get context
        plan_id = self._current_plan_id or 'unknown'
        pay_type = self._current_pay_type or 'unknown'

        # Generate detailed message
        if "MERCHANT_STATUS_NOT_NORMAL" in error_msg or "渠道" in error_msg:
            detailed_msg = (
                f"支付渠道暂时不可用：{error_msg}\n\n"
                "可能的原因：\n"
                "• 支付渠道临时维护中\n"
                "• 需要在商户后台完成渠道签约\n\n"
                "建议操作：\n"
                "1. 稍后重试（5-10分钟后）\n"
                "2. 联系支付服务商客服（zpayz.cn）"
            )
            logging.error(f"[PAYMENT] Channel error: {error_msg}")
        else:
            detailed_msg = (
                f"创建订单失败：{error_msg}\n\n"
                f"调试信息：\n"
                f"• 套餐类型: {plan_id}\n"
                f"• 支付方式: {pay_type}"
            )
            logging.error(f"[PAYMENT] Create order failed - plan_type: {plan_id}, error: {error_msg}")

        QMessageBox.critical(self._parent, self.tr("membership.payment.create_order_failed"), detailed_msg)
        self.payment_failed.emit(error_msg)

    def on_stripe_selected(self, plan_id: str):
        """Handle Stripe international payment selection.

        Args:
            plan_id: The plan identifier
        """
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker

        auth_client = AuthClient()

        logging.info(f"[STRIPE] 创建Stripe Checkout Session - plan_type: {plan_id}")

        # Get user info
        user_id = auth_client.get_user_id()
        email = auth_client.get_user_email()

        logging.info(f"[STRIPE] 用户信息 - user_id: {user_id}, email: {email}")

        if not user_id or not email:
            error_msg = "用户信息不完整，请重新登录"
            logging.error(f"[STRIPE] {error_msg}")
            QMessageBox.critical(self._parent, self.tr("membership.payment.error"), error_msg)
            return

        # Save context for callbacks
        self._current_pay_type = "stripe"
        self._current_plan_id = plan_id

        # Create progress dialog
        self._payment_progress = QProgressDialog(
            "正在创建支付订单...",
            "取消",
            0, 0,
            self._parent
        )
        self._payment_progress.setWindowTitle("请稍候")
        self._payment_progress.setWindowModality(Qt.WindowModal)
        self._payment_progress.setMinimumDuration(0)
        self._payment_progress.show()

        # Use async worker
        self._payment_worker = AsyncNetworkWorker(
            auth_client.create_stripe_checkout_session,
            plan_type=plan_id,
            user_id=user_id,
            user_email=email
        )
        self._payment_worker.success.connect(self._on_stripe_session_created)
        self._payment_worker.error.connect(self._on_payment_error)
        self._payment_worker.start()

        self.payment_started.emit(plan_id)

    def _on_stripe_session_created(self, result: dict):
        """Callback for successful Stripe Checkout Session creation.

        Args:
            result: API response containing session details
        """
        # Close progress dialog
        if self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        logging.info(f"[STRIPE] Checkout Session创建结果: {result}")

        if result.get("success"):
            checkout_url = result.get("checkout_url")
            session_id = result.get("session_id")

            logging.info(f"[STRIPE] Opening Stripe Checkout: {checkout_url[:100] if checkout_url else 'None'}...")
            logging.info(f"[STRIPE] Session ID: {session_id}")

            # Open Stripe Checkout in browser
            QDesktopServices.openUrl(QUrl(checkout_url))

            # Show info message
            QMessageBox.information(
                self._parent,
                "支付窗口已打开",
                "Stripe支付页面已在浏览器中打开。\n\n"
                "请在浏览器中完成支付。\n"
                "支付成功后，会员权益将自动激活。"
            )
        else:
            error_msg = result.get("error", "创建支付会话失败")
            plan_id = self._current_plan_id
            detailed_msg = (
                f"创建Stripe支付会话失败：{error_msg}\n\n"
                f"调试信息：\n"
                f"• 套餐类型: {plan_id}"
            )
            logging.error(f"[STRIPE] Create checkout session failed: {error_msg}")
            QMessageBox.critical(self._parent, self.tr("membership.payment.create_session_failed"), detailed_msg)
            self.payment_failed.emit(error_msg)

    def _check_payment_status(self, out_trade_no: str, trade_no: str, auth_client):
        """Check payment status asynchronously.

        Args:
            out_trade_no: External trade number
            trade_no: Internal trade number
            auth_client: AuthClient instance
        """
        from gaiya.core.async_worker import AsyncNetworkWorker

        # Skip if previous check is still running
        if self._status_check_worker and self._status_check_worker.isRunning():
            logging.info("[PAYMENT] Previous status check still running, skipping...")
            return

        logging.info(f"[PAYMENT] Checking payment status for order: {out_trade_no}")

        # Create async worker
        self._status_check_worker = AsyncNetworkWorker(
            auth_client.query_payment_order,
            out_trade_no,
            trade_no=trade_no
        )
        self._status_check_worker.success.connect(self._on_payment_status_checked)
        self._status_check_worker.error.connect(self._on_payment_status_check_error)
        self._status_check_worker.start()

    def _on_payment_status_checked(self, result: dict):
        """Callback for payment status check.

        Args:
            result: API response with payment status
        """
        from gaiya.core.auth_client import AuthClient

        order = result.get("order", {})
        status = order.get("status")

        logging.info(f"[PAYMENT] Status check result: {status}")

        # Try manual upgrade to bypass Vercel cache
        try:
            auth_client = AuthClient()
            user_id = auth_client.get_user_id()
            plan_name = self.current_plan_name or "Pro订阅"
            out_trade_no = self.current_out_trade_no

            plan_type = self.PLAN_TYPE_MAP.get(plan_name, "pro_monthly")

            if out_trade_no and user_id:
                logging.info(f"[PAYMENT] Vercel query returned: {status}, trying manual upgrade to verify real status...")
                upgrade_result = auth_client.manual_upgrade_subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    out_trade_no=out_trade_no
                )

                if upgrade_result.get("success"):
                    # Payment confirmed!
                    logging.info("[PAYMENT] Manual upgrade succeeded - payment is CONFIRMED!")
                    self.stop_payment_polling()

                    # Sync tier to AI client
                    new_tier = upgrade_result.get("user_tier", "free")
                    if self._ai_client:
                        self._ai_client.set_user_tier(new_tier)
                        logging.info(f"[AI Client] 会员升级后已同步tier: {new_tier}")

                    QMessageBox.information(
                        self._parent,
                        "支付成功",
                        f"{plan_name}已成功激活!\n\n会员状态已更新"
                    )

                    self.payment_success.emit(plan_name, new_tier)
                    self.subscription_refreshed.emit()
                else:
                    # Not paid yet
                    error_msg = upgrade_result.get('error', '')
                    if 'not paid' in error_msg.lower() or 'unpaid' in error_msg.lower():
                        logging.info("[PAYMENT] Manual upgrade confirms: order not paid yet, continue polling...")
                    else:
                        logging.warning(f"[PAYMENT] Manual upgrade failed: {error_msg}")

        except Exception as e:
            logging.error(f"[PAYMENT] Manual upgrade check error: {e}")

    def _on_payment_status_check_error(self, error_msg: str):
        """Callback for payment status check error (non-critical).

        Args:
            error_msg: Error message
        """
        logging.warning(f"[PAYMENT] Status check error (continuing polling): {error_msg}")

    def confirm_payment_manually(self, dialog: QDialog, out_trade_no: str, plan_name: str):
        """Manually confirm payment completion.

        Args:
            dialog: Payment dialog to close
            out_trade_no: External trade number
            plan_name: Plan display name
        """
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker

        # Stop polling
        if self.payment_timer:
            self.payment_timer.stop()

        # Close dialog
        dialog.close()

        logging.info(f"[PAYMENT] User manually confirmed payment: {out_trade_no}")

        # Get user_id and plan_type
        auth_client = AuthClient()
        user_id = auth_client.get_user_id()

        plan_type = self.PLAN_TYPE_MAP.get(plan_name, "pro_monthly")

        logging.info(f"[PAYMENT] Triggering manual upgrade for user {user_id}, plan {plan_type}")

        # Save context for callbacks
        self._manual_upgrade_context = {
            'plan_name': plan_name,
            'out_trade_no': out_trade_no,
            'auth_client': auth_client
        }

        # Use async worker
        self._manual_upgrade_worker = AsyncNetworkWorker(
            auth_client.trigger_manual_upgrade,
            out_trade_no=out_trade_no,
            user_id=user_id,
            plan_type=plan_type
        )
        self._manual_upgrade_worker.success.connect(self._on_manual_upgrade_success)
        self._manual_upgrade_worker.error.connect(self._on_manual_upgrade_error)
        self._manual_upgrade_worker.start()

    def _on_manual_upgrade_success(self, result: dict):
        """Callback for successful manual upgrade API call.

        Args:
            result: API response
        """
        from gaiya.core.async_worker import AsyncNetworkWorker

        ctx = self._manual_upgrade_context
        plan_name = ctx.get('plan_name', '会员')
        out_trade_no = ctx.get('out_trade_no', '')
        auth_client = ctx.get('auth_client')

        if result.get("success"):
            logging.info(f"[PAYMENT] Manual upgrade API success: {out_trade_no}")

            # Refresh subscription status async
            if auth_client:
                self._subscription_refresh_worker = AsyncNetworkWorker(
                    auth_client.get_subscription_status
                )
                self._subscription_refresh_worker.success.connect(
                    lambda r: self._on_manual_upgrade_subscription_refreshed(r, plan_name)
                )
                self._subscription_refresh_worker.error.connect(
                    lambda e: self._on_manual_upgrade_subscription_error(e, plan_name)
                )
                self._subscription_refresh_worker.start()
            else:
                QMessageBox.information(self._parent, "支付成功", f"{plan_name}已成功激活!\n\n请重启应用以刷新会员状态。")
        else:
            error_msg = result.get("error", "激活失败")
            QMessageBox.warning(self._parent, "激活失败", f"会员激活失败: {error_msg}\n\n请联系客服处理")
            logging.error(f"[PAYMENT] Manual upgrade failed: {error_msg}")

    def _on_manual_upgrade_error(self, error_msg: str):
        """Callback for manual upgrade API error.

        Args:
            error_msg: Error message
        """
        logging.error(f"[PAYMENT] Manual upgrade error: {error_msg}")
        QMessageBox.critical(self._parent, "错误", f"激活过程出错: {error_msg}\n\n请联系客服处理")

    def _on_manual_upgrade_subscription_refreshed(self, subscription_result: dict, plan_name: str):
        """Callback for successful subscription refresh after manual upgrade.

        Args:
            subscription_result: API response with subscription status
            plan_name: Plan display name
        """
        ctx = self._manual_upgrade_context
        out_trade_no = ctx.get('out_trade_no', '')

        if subscription_result.get("success"):
            new_tier = subscription_result.get('user_tier', 'free')
            logging.info(f"[PAYMENT] Subscription status refreshed: {new_tier}")

            # Sync tier to AI client
            if self._ai_client:
                self._ai_client.set_user_tier(new_tier)
                logging.info(f"[AI Client] 会员升级后已同步tier: {new_tier}")

            QMessageBox.information(self._parent, "支付成功", f"{plan_name}已成功激活!\n\n会员状态已更新")

            self.payment_success.emit(plan_name, new_tier)
            self.subscription_refreshed.emit()
        else:
            QMessageBox.information(self._parent, "支付成功", f"{plan_name}已成功激活!\n\n请重启应用以刷新会员状态。")

        logging.info(f"[PAYMENT] Manual upgrade successful: {out_trade_no}")

    def _on_manual_upgrade_subscription_error(self, error_msg: str, plan_name: str):
        """Callback for subscription refresh error after manual upgrade (non-critical).

        Args:
            error_msg: Error message
            plan_name: Plan display name
        """
        logging.warning(f"[PAYMENT] Subscription refresh failed after upgrade: {error_msg}")
        # Upgrade succeeded, just refresh failed
        QMessageBox.information(self._parent, "支付成功", f"{plan_name}已成功激活!\n\n请重启应用以刷新会员状态。")

    def _cancel_payment_dialog(self, dialog: QDialog):
        """Cancel payment dialog.

        Args:
            dialog: Dialog to close
        """
        # Stop polling
        if self.payment_timer:
            self.payment_timer.stop()

        # Close dialog
        dialog.close()

        logging.info("[PAYMENT] Payment cancelled by user")

    def stop_payment_polling(self):
        """Stop payment status polling."""
        if self.payment_timer:
            self.payment_timer.stop()

        if self.payment_polling_dialog:
            self.payment_polling_dialog.close()

    def on_plan_button_clicked(self, plan_id: str):
        """Handle plan button click - show payment method dialog.

        Args:
            plan_id: The plan identifier
        """
        try:
            self.selected_plan_id = plan_id
            self.show_payment_method_dialog(plan_id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self._parent, "错误", f"点击升级会员按钮时发生错误：\n\n{str(e)}")

    def cleanup(self):
        """Clean up resources before destruction."""
        # Stop timers
        if self.payment_timer:
            self.payment_timer.stop()
            self.payment_timer = None

        # Close dialogs
        if self.payment_polling_dialog:
            self.payment_polling_dialog.close()
            self.payment_polling_dialog = None

        if self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None
