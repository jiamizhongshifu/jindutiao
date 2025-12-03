"""
GaiYa每日进度条 - 会员购买UI模块 (v2.1-最终修复版)
提供会员套餐选择和支付功能

版本：v2.1 - 完美解决黑色边框问题（QPainter + setStyleSheet清除默认border）
修改时间：2025-11-06 14:50
修复记录：
- 使用QPainter手动绘制渐变背景和边框
- 通过setStyleSheet明确清除QWidget默认border（黑色边框的根源）
- 已验证开发环境无黑色边框残留
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QMessageBox, QWidget,
    QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl, QSize, qVersion, __version__ as pyside_version, QRect, QRectF
from PySide6.QtGui import QFont, QDesktopServices, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
import sys
import os

# 添加父目录到路径以导入core模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gaiya.core.auth_client import AuthClient
from gaiya.i18n.translator import tr


class GradientCardWidget(QWidget):
    """使用QPainter手动绘制的渐变卡片（用于Featured Card）"""

    def __init__(self, bg_colors, parent=None):
        super().__init__(parent)
        self.bg_colors = bg_colors  # (start_color, end_color)
        self.is_selected = False
        self.is_hovered = False
        self.setMouseTracking(True)  # 启用鼠标追踪以支持hover

        # ⚠️ 关键：确保父容器可以绘制背景，子组件不会阻止paintEvent
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 确保widget的背景透明，让QPainter绘制生效
        self.setAutoFillBackground(False)

        # ⚠️ 关键修复：明确清除QWidget默认边框（黑色边框的根源）
        self.setStyleSheet("""
            GradientCardWidget {
                border: none;
                background: transparent;
            }
        """)

        # ⚠️ 终极修复：禁用焦点策略，防止Windows绘制黑色焦点框
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # ⚠️ 底层修复：使用Qt属性完全禁用系统默认绘制
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)  # 完全禁用Qt自动背景填充

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self.update()  # 触发重绘

    def enterEvent(self, event):
        """鼠标进入"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """手动绘制卡片 - 边框绘制在子组件之上"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿

        rect = self.rect()

        # 1. 绘制渐变背景
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, QColor(self.bg_colors[0]))
        gradient.setColorAt(1, QColor(self.bg_colors[1]))

        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 16, 16)

        painter.fillPath(path, QBrush(gradient))

        # ⚠️ 关键修复：移除super().paintEvent(event)调用
        # 这会阻止QWidget的默认绘制，避免在打包环境中产生黑色边框
        # painter.end()  # 不需要结束，直接继续使用

        # 2. 继续使用同一个painter绘制边框
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制边框 - 正式版本
        if self.is_selected:
            # 选中：蓝色粗边框
            pen = QPen(QColor("#0071e3"), 3)
        elif self.is_hovered:
            # Hover：半透明白色较亮边框
            pen = QPen(QColor(255, 255, 255, int(0.6 * 255)), 2)
        else:
            # 默认：半透明白色细边框
            pen = QPen(QColor(255, 255, 255, int(0.3 * 255)), 2)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # 调整rect以避免边框被裁剪
        border_width = 3 if self.is_selected else 2
        adjusted_rect = rect.adjusted(
            border_width // 2,
            border_width // 2,
            -border_width // 2,
            -border_width // 2
        )
        path_border = QPainterPath()
        path_border.addRoundedRect(QRectF(adjusted_rect), 16, 16)
        painter.drawPath(path_border)


class SolidCardWidget(QWidget):
    """使用QPainter手动绘制的纯色卡片（用于Compact Card）"""

    def __init__(self, bg_color_normal, bg_color_selected, bg_color_hover=None, parent=None):
        super().__init__(parent)
        self.bg_color_normal = bg_color_normal
        self.bg_color_selected = bg_color_selected
        self.bg_color_hover = bg_color_hover or bg_color_normal
        self.is_selected = False
        self.is_hovered = False
        self.setMouseTracking(True)

        # ⚠️ 关键修复：明确清除QWidget默认边框（黑色边框的根源）
        self.setStyleSheet("""
            SolidCardWidget {
                border: none;
                background: transparent;
            }
        """)

        # ⚠️ 终极修复：禁用焦点策略，防止Windows绘制黑色焦点框
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # ⚠️ 底层修复：使用Qt属性完全禁用系统默认绘制
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)  # 完全禁用Qt自动背景填充

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self.update()

    def enterEvent(self, event):
        """鼠标进入"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """手动绘制卡片"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # 1. 绘制背景
        if self.is_selected:
            bg_color = QColor(self.bg_color_selected)
        elif self.is_hovered:
            bg_color = QColor(self.bg_color_hover)
        else:
            bg_color = QColor(self.bg_color_normal)

        # 创建圆角路径
        border_radius = 18 if hasattr(self, 'large_card') else 12
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), border_radius, border_radius)

        painter.fillPath(path, QBrush(bg_color))

        # 2. 绘制边框
        if self.is_selected:
            # 选中：蓝色粗边框
            pen = QPen(QColor("#0071e3"), 2)
        elif self.is_hovered:
            # Hover：深色边框
            pen = QPen(QColor(0, 0, 0, int(0.12 * 255)), 1)
        else:
            # 默认：淡色边框
            pen = QPen(QColor(0, 0, 0, int(0.08 * 255)), 1)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        border_width = 2 if self.is_selected else 1
        adjusted_rect = rect.adjusted(
            border_width // 2,
            border_width // 2,
            -border_width // 2,
            -border_width // 2
        )
        path_border = QPainterPath()
        path_border.addRoundedRect(QRectF(adjusted_rect), border_radius, border_radius)
        painter.drawPath(path_border)


class DualGradientCardWidget(QWidget):
    """使用QPainter手动绘制的双渐变卡片（用于Plan Card，支持两种渐变状态）"""

    def __init__(self, gradient_normal, gradient_selected, parent=None):
        super().__init__(parent)
        # gradient_normal和gradient_selected分别是(start_color, end_color)元组
        self.gradient_normal = gradient_normal
        self.gradient_selected = gradient_selected
        self.is_selected = False
        self.is_hovered = False
        self.setMouseTracking(True)
        self.large_card = True  # 标记为大卡片，使用18px圆角

        # ⚠️ 关键修复：明确清除QWidget默认边框（黑色边框的根源）
        self.setStyleSheet("""
            DualGradientCardWidget {
                border: none;
                background: transparent;
            }
        """)

        # ⚠️ 终极修复：禁用焦点策略，防止Windows绘制黑色焦点框
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # ⚠️ 底层修复：使用Qt属性完全禁用系统默认绘制
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)  # 完全禁用Qt自动背景填充

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self.update()

    def enterEvent(self, event):
        """鼠标进入"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """手动绘制卡片"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # 1. 绘制渐变背景
        if self.is_selected:
            start_color, end_color = self.gradient_selected
        else:
            start_color, end_color = self.gradient_normal

        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, QColor(start_color))
        gradient.setColorAt(1, QColor(end_color))

        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 18, 18)

        painter.fillPath(path, QBrush(gradient))

        # 2. 绘制边框
        if self.is_selected:
            # 选中：蓝色粗边框
            pen = QPen(QColor("#0071e3"), 2)
        elif self.is_hovered:
            # Hover：深色边框
            pen = QPen(QColor(0, 0, 0, int(0.12 * 255)), 1)
        else:
            # 默认：淡色边框
            pen = QPen(QColor(0, 0, 0, int(0.06 * 255)), 1)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        border_width = 2 if self.is_selected else 1
        adjusted_rect = rect.adjusted(
            border_width // 2,
            border_width // 2,
            -border_width // 2,
            -border_width // 2
        )
        path_border = QPainterPath()
        path_border.addRoundedRect(QRectF(adjusted_rect), 18, 18)
        painter.drawPath(path_border)


class MembershipDialog(QDialog):
    """会员购买对话框"""

    # 信号：购买成功时发出
    purchase_success = Signal(str)  # 传递plan_type

    def __init__(self, auth_client: AuthClient = None, parent=None):
        super().__init__(parent)
        self.auth_client = auth_client or AuthClient()

        # ========== 诊断日志：环境信息 ==========
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"[DIAG-1] MembershipDialog.__init__ 开始", file=sys.stderr)
        print(f"[DIAG-1] Qt version: {qVersion()}", file=sys.stderr)
        print(f"[DIAG-1] PySide6 version: {pyside_version}", file=sys.stderr)
        app = QApplication.instance()
        if app:
            print(f"[DIAG-1] QApplication style: {app.style().objectName()}", file=sys.stderr)
            print(f"[DIAG-1] Platform name: {app.platformName()}", file=sys.stderr)
            screen = app.primaryScreen()
            if screen:
                print(f"[DIAG-1] Device pixel ratio: {screen.devicePixelRatio()}", file=sys.stderr)
                print(f"[DIAG-1] Logical DPI: {screen.logicalDotsPerInch()}", file=sys.stderr)
        print(f"[DIAG-1] Parent: {type(parent).__name__ if parent else 'None'}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        # 检查登录状态
        if not self.auth_client.is_logged_in():
            QMessageBox.warning(
                parent,
                tr("membership.not_logged_in"),
                tr("membership.login_required")
            )
            self.reject()
            return

        self.selected_plan = None
        self.selected_pay_type = "alipay"

        # 初始化支付轮询相关属性
        self.payment_timer = None
        self.payment_polling_dialog = None
        self.polling_count = 0
        self.polling_error_count = 0

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(tr("membership.upgrade_to_pro"))

        # ⚠️ 关键修复：明确禁用窗口调整大小功能
        # 仅setFixedSize不够，还需要设置窗口标志移除调整大小边框
        self.setFixedSize(1170, 640)  # 增加高度以容纳支付方式选择模块

        # 设置窗口标志：移除调整大小的句柄
        # 保留关闭按钮和标题栏，但禁用调整大小
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint  # 移除最大化按钮
        )
        # 更彻底的方案：完全禁用调整大小
        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint, True)

        # 设置对话框背景色，防止移动时出现白色块
        self.setStyleSheet("QDialog { background-color: white; }")

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === 顶部标题区域 ===
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_widget.setAutoFillBackground(True)  # 启用自动填充背景
        header_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # 启用样式背景
        header_widget.setStyleSheet("#headerWidget { background-color: #f5f5f7; }")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(40, 35, 40, 25)
        header_layout.setSpacing(8)

        # 标题
        title_label = QLabel(tr("membership.dialog_title"))
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #1d1d1f; background: transparent; border: none; }")
        header_layout.addWidget(title_label)

        # 当前用户信息
        user_email = self.auth_client.get_user_email()
        user_tier = self.auth_client.get_user_tier()
        user_info_label = QLabel(f"{user_email} · {self._get_tier_name(user_tier)}")
        user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_info_label.setStyleSheet("QLabel { color: #86868b; font-size: 13px; background: transparent; border: none; }")
        header_layout.addWidget(user_info_label)

        main_layout.addWidget(header_widget)

        # === 套餐选择区域（中间内容区） ===
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setAutoFillBackground(True)  # 启用自动填充背景
        content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # 启用样式背景
        content_widget.setStyleSheet("#contentWidget { background-color: white; }")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 25)
        content_layout.setSpacing(25)

        # 套餐卡片
        plans_widget = self._create_plans_widget()
        content_layout.addWidget(plans_widget)

        # 支付方式选择
        payment_method_widget = self._create_payment_method_widget()
        content_layout.addWidget(payment_method_widget)

        main_layout.addWidget(content_widget)

        # === 底部按钮区域 ===
        footer_widget = QWidget()
        footer_widget.setObjectName("footerWidget")
        footer_widget.setAutoFillBackground(True)  # 启用自动填充背景
        footer_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # 启用样式背景
        footer_widget.setStyleSheet("#footerWidget { background-color: #f5f5f7; border-top: 1px solid rgba(0,0,0,0.08); }")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(40, 20, 40, 20)
        footer_layout.setSpacing(15)

        footer_layout.addStretch()

        # 取消按钮（次要）
        cancel_button = QPushButton(tr("membership.btn_cancel"))
        cancel_button.setFixedSize(120, 44)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f5f7;
                border-color: #86868b;
            }
            QPushButton:pressed {
                background-color: #e8e8ed;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_button)

        # 购买按钮（主要，Apple蓝）
        self.purchase_button = QPushButton(tr("membership.btn_buy_now"))
        self.purchase_button.setFixedSize(160, 44)
        self.purchase_button.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0077ed;
            }
            QPushButton:pressed {
                background-color: #006edb;
            }
            QPushButton:disabled {
                background-color: #d2d2d7;
                color: #86868b;
            }
        """)
        self.purchase_button.clicked.connect(self._on_purchase_clicked)
        footer_layout.addWidget(self.purchase_button)

        main_layout.addWidget(footer_widget)

        self.setLayout(main_layout)

    def _create_plans_widget(self) -> QWidget:
        """创建套餐选择组件 - 单行布局"""
        widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)  # 缩小卡片间距 15 → 12
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 套餐按钮组（在创建卡片前初始化）
        self.plan_button_group = QButtonGroup()

        # === 单行展示3个套餐 ===

        # 月度会员（橙色卡片）
        monthly_plan = self._create_featured_card(
            plan_type="pro_monthly",
            title=tr("membership.plan.monthly_name"),
            price="29",
            original_price="39",
            unit=tr("membership.plan.per_month"),
            period_price=tr("membership.plan.monthly_daily_price"),
            badge=tr("membership.btn_activate"),
            features=[
                tr("membership.feature.smart_planning_50"),
                tr("membership.feature.progress_report_10"),
                tr("membership.feature.ai_assistant_100"),
                tr("membership.feature.custom_theme")
            ],
            bg_colors=["#ffb347", "#ff9f2e"],  # 橙色渐变
            is_recommended=False
        )
        main_layout.addWidget(monthly_plan)

        # 年度会员（蓝色卡片 - 最推荐）
        yearly_plan = self._create_featured_card(
            plan_type="pro_yearly",
            title=tr("membership.plan.yearly_name"),
            price="199",
            original_price="239",
            unit=tr("membership.plan.per_year"),
            period_price=tr("membership.plan.yearly_daily_price"),
            badge=tr("membership.plan.subscription_deal"),
            features=[
                tr("membership.feature.all_pro_features"),
                tr("membership.feature.save_40"),
                tr("membership.feature.priority_support"),
                tr("membership.feature.early_access")
            ],
            bg_colors=["#5ba3ff", "#3d8eff"],  # 蓝色渐变
            is_recommended=True
        )
        main_layout.addWidget(yearly_plan)

        # 终身会员（紫色卡片）- 暂时隐藏，后续调整价格后再启用
        # lifetime_plan = self._create_featured_card(
        #     plan_type="lifetime",
        #     title=tr("membership.plan.lifetime"),
        #     price="299",
        #     original_price="399",
        #     unit="元/终身",
        #     period_price="一次付费永久使用",
        #     badge="永久使用",
        #     features=[
        #         "所有会员功能",
        #         "一次付费终身享受",
        #         "未来新功能免费",
        #         "VIP客服支持"
        #     ],
        #     bg_colors=["#b794f6", "#9f7aea"],  # 紫色渐变
        #     is_recommended=False
        # )
        # main_layout.addWidget(lifetime_plan)

        widget.setLayout(main_layout)
        return widget

    def _create_featured_card(
        self,
        plan_type: str,
        title: str,
        price: str,
        original_price: str,
        unit: str,
        period_price: str,
        badge: str,
        features: list,
        bg_colors: list,
        is_recommended: bool = False
    ) -> QWidget:
        """创建主推套餐卡片 - 彩色大卡片（使用QPainter手动绘制）"""
        # ========== 诊断日志：Featured Card 创建 ==========
        print(f"\n[DIAG-QPainter] === Creating Featured Card (QPainter): {plan_type} ===", file=sys.stderr)

        # === 主容器 ===
        # ⚠️ 使用GradientCardWidget，完全手动绘制背景和边框
        card_container = GradientCardWidget(bg_colors=bg_colors)
        card_container.setProperty("plan_type", plan_type)
        card_container.setCursor(Qt.CursorShape.PointingHandCursor)
        card_container.setFixedWidth(360)
        card_container.setFixedHeight(230)

        print(f"[DIAG-QPainter] Container type: {type(card_container).__name__}", file=sys.stderr)
        print(f"[DIAG-QPainter] Container size: {card_container.size()}", file=sys.stderr)
        print(f"[DIAG-QPainter] Using QPainter manual rendering (no stylesheet)", file=sys.stderr)

        # === 主布局 ===
        main_layout = QVBoxLayout(card_container)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(24, 20, 24, 20)

        # === 顶部：标题 + 徽章 ===
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("QLabel { color: white; border: none; background: transparent; }")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        # 徽章
        badge_label = QLabel(f"👑 {badge}" if is_recommended else badge)
        badge_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.25);
                color: white;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
                border: none;
                border-radius: 10px;
            }
        """)
        top_layout.addWidget(badge_label)

        main_layout.addLayout(top_layout)

        # === 价格区域 ===
        price_layout = QHBoxLayout()
        price_layout.setSpacing(8)

        # 主价格
        price_label = QLabel(f"¥{price}")
        price_font = QFont()
        price_font.setPointSize(36)
        price_font.setWeight(QFont.Weight.Bold)
        price_label.setFont(price_font)
        price_label.setStyleSheet("QLabel { color: white; letter-spacing: -1px; border: none; background: transparent; }")
        price_layout.addWidget(price_label)

        # 原价（删除线）
        original_price_label = QLabel(f"¥{original_price}")
        original_price_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 16px;
                text-decoration: line-through;
                border: none;
                background: transparent;
            }
        """)
        price_layout.addWidget(original_price_label, alignment=Qt.AlignmentFlag.AlignBottom)

        price_layout.addStretch()

        main_layout.addLayout(price_layout)

        # 单位 + 折算价
        unit_layout = QVBoxLayout()
        unit_layout.setSpacing(2)

        unit_label = QLabel(unit)
        unit_label.setStyleSheet("QLabel { color: rgba(255, 255, 255, 0.85); font-size: 14px; border: none; background: transparent; }")
        unit_layout.addWidget(unit_label)

        period_label = QLabel(period_price)
        period_label.setStyleSheet("QLabel { color: rgba(255, 255, 255, 0.7); font-size: 12px; border: none; background: transparent; }")
        unit_layout.addWidget(period_label)

        main_layout.addLayout(unit_layout)

        main_layout.addSpacing(10)

        # === 功能列表（紧凑型） ===
        features_text = " · ".join(features)
        features_label = QLabel(features_text)
        features_label.setWordWrap(True)
        features_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                line-height: 1.5;
                border: none;
                background: transparent;
            }
        """)
        main_layout.addWidget(features_label)

        main_layout.addStretch()

        # === 隐藏的RadioButton ===
        radio = QRadioButton()
        radio.setProperty("plan_type", plan_type)
        radio.setVisible(False)
        self.plan_button_group.addButton(radio)
        main_layout.addWidget(radio)

        # === 交互逻辑 ===
        # 点击整个卡片时选中
        def mousePressEvent(event):
            radio.setChecked(True)
            # GradientCardWidget会处理自己的鼠标事件

        card_container.mousePressEvent = mousePressEvent

        def on_toggled(checked):
            if checked:
                self._on_plan_selected(plan_type)
            # 更新选中状态（由GradientCardWidget的QPainter处理）
            card_container.set_selected(checked)

        radio.toggled.connect(on_toggled)

        # 设置初始状态为未选中
        card_container.set_selected(False)

        print(f"[DIAG-QPainter] Featured Card setup complete", file=sys.stderr)

        # 默认选中年度会员
        if is_recommended:
            radio.setChecked(True)

        return card_container

    def _create_compact_card(
        self,
        plan_type: str,
        title: str,
        price: str,
        unit: str,
        description: str
    ) -> QWidget:
        """创建紧凑型卡片 - 灰色小卡片（使用QPainter手动绘制）"""
        # ========== 诊断日志：Compact Card 创建 ==========
        print(f"\n[DIAG-QPainter] === Creating Compact Card (QPainter): {plan_type} ===", file=sys.stderr)

        # === 主容器 ===
        # ⚠️ 使用SolidCardWidget，完全手动绘制背景和边框
        card_container = SolidCardWidget(
            bg_color_normal="#f5f5f7",
            bg_color_selected="#e8f2ff",
            bg_color_hover="#ebebed"
        )
        card_container.setProperty("plan_type", plan_type)
        card_container.setCursor(Qt.CursorShape.PointingHandCursor)
        card_container.setFixedWidth(270)
        card_container.setFixedHeight(100)

        print(f"[DIAG-QPainter] Container type: {type(card_container).__name__}", file=sys.stderr)
        print(f"[DIAG-QPainter] Using QPainter manual rendering (no stylesheet)", file=sys.stderr)

        # === 主布局 ===
        main_layout = QHBoxLayout(card_container)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 16, 20, 16)

        # === 左侧：价格 ===
        price_layout = QVBoxLayout()
        price_layout.setSpacing(2)

        price_label = QLabel(f"¥{price}")
        price_font = QFont()
        price_font.setPointSize(24)
        price_font.setWeight(QFont.Weight.Bold)
        price_label.setFont(price_font)
        price_label.setStyleSheet("QLabel { color: #1d1d1f; border: none; background: transparent; }")
        price_layout.addWidget(price_label)

        unit_label = QLabel(unit)
        unit_label.setStyleSheet("QLabel { color: #86868b; font-size: 12px; border: none; background: transparent; }")
        price_layout.addWidget(unit_label)

        main_layout.addLayout(price_layout)

        # === 右侧：标题 + 描述 ===
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("QLabel { color: #1d1d1f; border: none; background: transparent; }")
        info_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { color: #86868b; font-size: 11px; border: none; background: transparent; }")
        info_layout.addWidget(desc_label)

        main_layout.addLayout(info_layout, 1)

        # === 隐藏的RadioButton ===
        radio = QRadioButton()
        radio.setProperty("plan_type", plan_type)
        radio.setVisible(False)
        self.plan_button_group.addButton(radio)
        main_layout.addWidget(radio)

        # === 交互逻辑 ===
        def mousePressEvent(event):
            radio.setChecked(True)
            # SolidCardWidget会处理自己的鼠标事件

        card_container.mousePressEvent = mousePressEvent

        def on_toggled(checked):
            if checked:
                self._on_plan_selected(plan_type)
            # 更新选中状态（由SolidCardWidget的QPainter处理）
            card_container.set_selected(checked)

        radio.toggled.connect(on_toggled)

        # 设置初始状态为未选中
        card_container.set_selected(False)

        print(f"[DIAG-QPainter] Compact Card setup complete", file=sys.stderr)

        return card_container

    def _create_plan_card(
        self,
        plan_type: str,
        title: str,
        price: str,
        unit: str,
        features: list,
        recommended: bool = False
    ) -> QWidget:
        """创建套餐卡片 - Apple风格（极简优雅，使用QPainter手动绘制）"""
        # === 主容器（可点击） ===
        # ⚠️ 使用DualGradientCardWidget，完全手动绘制背景和边框
        card_container = DualGradientCardWidget(
            gradient_normal=("#ffffff", "#fafafa"),  # 未选中：白色渐变
            gradient_selected=("#f5f9ff", "#e8f2ff")  # 选中：蓝色渐变
        )
        card_container.setProperty("plan_type", plan_type)
        card_container.setCursor(Qt.CursorShape.PointingHandCursor)

        # === 卡片布局 ===
        main_layout = QVBoxLayout(card_container)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(32, 36, 32, 36)

        # === 推荐标签（顶部，仅年度套餐） ===
        if recommended:
            badge = QLabel(tr("membership.plan.best_value"))
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet("""
                QLabel {
                    color: #0071e3;
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    padding: 4px 0px;
                    background-color: transparent;
                    border: none;
                }
            """)
            main_layout.addWidget(badge)
            main_layout.addSpacing(8)

        # === 标题 ===
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(21)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #1d1d1f; background: transparent; border: none; }")
        main_layout.addWidget(title_label)

        main_layout.addSpacing(20)

        # === 价格区域（核心视觉焦点） ===
        price_container = QWidget()
        price_container.setStyleSheet("QWidget { background-color: transparent; }")
        price_layout = QVBoxLayout(price_container)
        price_layout.setSpacing(4)
        price_layout.setContentsMargins(0, 0, 0, 0)

        # 价格
        price_label = QLabel(f"¥{price}")
        price_font = QFont()
        price_font.setPointSize(48)
        price_font.setWeight(QFont.Weight.Bold)
        price_label.setFont(price_font)
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("QLabel { color: #1d1d1f; letter-spacing: -1px; background: transparent; border: none; }")
        price_layout.addWidget(price_label)

        # 单位（紧贴价格下方）
        unit_label = QLabel(unit)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_label.setStyleSheet("""
            QLabel {
                color: #86868b;
                font-size: 14px;
                font-weight: 400;
                background: transparent;
                border: none;
            }
        """)
        price_layout.addWidget(unit_label)

        main_layout.addWidget(price_container)
        main_layout.addSpacing(28)

        # === 分隔线（细线） ===
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("QFrame { background-color: rgba(0, 0, 0, 0.08); border: none; }")
        main_layout.addWidget(divider)

        main_layout.addSpacing(24)

        # === 功能列表 ===
        features_container = QWidget()
        features_container.setStyleSheet("QWidget { background-color: transparent; }")
        features_layout = QVBoxLayout(features_container)
        features_layout.setSpacing(12)
        features_layout.setContentsMargins(0, 0, 0, 0)

        for feature in features:
            # 每个功能项
            feature_widget = QWidget()
            feature_widget.setStyleSheet("QWidget { background-color: transparent; }")
            feature_h_layout = QHBoxLayout(feature_widget)
            feature_h_layout.setContentsMargins(0, 0, 0, 0)
            feature_h_layout.setSpacing(10)

            # 图标（使用蓝色对勾）
            icon_label = QLabel("✓")
            icon_label.setFixedSize(16, 16)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("""
                QLabel {
                    color: #0071e3;
                    font-size: 14px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                }
            """)
            feature_h_layout.addWidget(icon_label)

            # 文字
            feature_label = QLabel(feature)
            feature_label.setWordWrap(True)
            feature_label.setStyleSheet("""
                QLabel {
                    color: #1d1d1f;
                    font-size: 13px;
                    font-weight: 400;
                    line-height: 1.4;
                    background: transparent;
                    border: none;
                }
            """)
            feature_h_layout.addWidget(feature_label, 1)

            features_layout.addWidget(feature_widget)

        main_layout.addWidget(features_container)
        main_layout.addStretch()

        # === 隐藏的RadioButton（用于选择状态管理） ===
        radio = QRadioButton()
        radio.setProperty("plan_type", plan_type)
        radio.setVisible(False)  # 完全隐藏
        self.plan_button_group.addButton(radio)
        main_layout.addWidget(radio)

        # === 交互逻辑 ===
        # 监听选择变化
        def on_toggled(checked):
            if checked:
                self._on_plan_selected(plan_type)
            # 更新选中状态（由DualGradientCardWidget的QPainter处理）
            card_container.set_selected(checked)

        radio.toggled.connect(on_toggled)

        # 点击整个卡片时选中
        def mousePressEvent(event):
            radio.setChecked(True)
            # DualGradientCardWidget会处理自己的鼠标事件

        card_container.mousePressEvent = mousePressEvent

        # 设置初始状态为未选中
        card_container.set_selected(False)

        # === 卡片尺寸 ===
        card_container.setFixedWidth(340)
        card_container.setFixedHeight(520)

        return card_container

    def _create_payment_method_widget(self) -> QWidget:
        """创建支付方式选择组件 - Apple风格"""
        # 外层容器（透明，用于边距）
        outer_container = QWidget()
        outer_container.setStyleSheet("QWidget { background-color: transparent; }")
        outer_layout = QVBoxLayout(outer_container)
        outer_layout.setContentsMargins(0, 20, 0, 25)  # 增加上下边距：top=20, bottom=25
        outer_layout.setSpacing(0)

        # 内层容器（白色背景，确保可见）
        container = QWidget()
        container.setObjectName("paymentMethodContainer")
        container.setStyleSheet("""
            #paymentMethodContainer {
                background-color: #f8f9fa;
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.1);
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # 标题（居中）
        title_label = QLabel(tr("membership.payment.select_method"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                font-size: 15px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(title_label)

        # 支付方式选项（居中布局）
        payment_layout = QHBoxLayout()
        payment_layout.setSpacing(15)

        # 支付方式按钮组
        self.payment_button_group = QButtonGroup()

        # 左侧弹性空间
        payment_layout.addStretch()

        # 支付宝
        alipay_radio = QRadioButton(tr("membership.payment.alipay"))
        alipay_radio.setProperty("pay_type", "alipay")
        alipay_radio.setChecked(True)
        alipay_radio.setStyleSheet("""
            QRadioButton {
                color: #1d1d1f;
                font-size: 14px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #0071e3;
                border: 2px solid #0071e3;
                border-radius: 9px;
            }
            QRadioButton::indicator:unchecked {
                background-color: white;
                border: 2px solid #d2d2d7;
                border-radius: 9px;
            }
        """)
        self.payment_button_group.addButton(alipay_radio)
        payment_layout.addWidget(alipay_radio)

        # 微信支付
        wxpay_radio = QRadioButton(tr("membership.payment.wechat"))
        wxpay_radio.setProperty("pay_type", "wxpay")
        wxpay_radio.setStyleSheet(alipay_radio.styleSheet())
        self.payment_button_group.addButton(wxpay_radio)
        payment_layout.addWidget(wxpay_radio)

        # 右侧弹性空间
        payment_layout.addStretch()

        # 监听选择变化
        self.payment_button_group.buttonClicked.connect(self._on_payment_method_changed)

        layout.addLayout(payment_layout)
        outer_layout.addWidget(container)
        return outer_container

    def _on_plan_selected(self, plan_type: str):
        """套餐选择变化"""
        self.selected_plan = plan_type

    def _on_payment_method_changed(self, button):
        """支付方式变化"""
        self.selected_pay_type = button.property("pay_type")

    def _on_purchase_clicked(self):
        """处理购买按钮点击"""
        if not self.selected_plan:
            QMessageBox.warning(self, tr("membership.error.no_plan_selected_title"), tr("membership.error.no_plan_selected_message"))
            return

        # 禁用购买按钮
        self.purchase_button.setEnabled(False)
        self.purchase_button.setText(tr("membership.payment.creating_order"))

        # 创建支付订单
        user_id = self.auth_client.get_user_id()
        result = self.auth_client.create_payment_order(
            plan_type=self.selected_plan,
            pay_type=self.selected_pay_type
        )

        # 恢复按钮状态
        self.purchase_button.setEnabled(True)
        self.purchase_button.setText(tr("membership.btn_buy_now"))

        if result.get("success"):
            # 订单创建成功
            payment_url = result.get("payment_url")
            out_trade_no = result.get("out_trade_no")
            amount = result.get("amount")
            plan_name = result.get("plan_name")

            # ✅ 修复: mapi.php方式返回完整payurl,无需拼接参数
            # payment_url已经包含所有必要参数
            print(f"[MEMBERSHIP] Opening payment URL: {payment_url[:100]}...")

            # 直接在浏览器中打开支付URL
            QDesktopServices.openUrl(QUrl(payment_url))

            # 开始轮询支付状态
            self._start_payment_polling(out_trade_no)

        else:
            # 订单创建失败
            error_msg = result.get("error", tr("membership.error.order_creation_failed_title"))
            QMessageBox.critical(self, tr("membership.error.order_creation_failed_title"), tr("membership.error.order_creation_failed", error_msg=error_msg))

    def _start_payment_polling(self, out_trade_no: str):
        """开始轮询支付状态"""
        # 显示等待对话框
        self.payment_polling_dialog = QMessageBox(self)
        self.payment_polling_dialog.setWindowTitle(tr("membership.payment.waiting_title"))
        self.payment_polling_dialog.setText(
            tr("membership.payment.waiting_line1") +
            tr("membership.payment.waiting_line2") +
            tr("membership.payment.waiting_line3")
        )
        self.payment_polling_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
        self.payment_polling_dialog.setIcon(QMessageBox.Icon.Information)

        # 创建定时器轮询支付状态
        self.payment_timer = QTimer()
        self.payment_timer.setInterval(3000)  # 每3秒查询一次
        self.payment_timer.timeout.connect(lambda: self._check_payment_status(out_trade_no))

        # ✅ 修复: 延迟5秒后开始轮询
        # 原因: submit.php只返回支付URL,订单是在用户访问支付页面时才由Z-Pay创建
        # 需要给用户时间打开页面和Z-Pay系统创建订单
        print(f"[MEMBERSHIP] Payment polling will start in 5 seconds for order: {out_trade_no}")
        QTimer.singleShot(5000, self.payment_timer.start)

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

                print(f"[MEMBERSHIP] Payment detected as paid: {out_trade_no}")

                # ✅ 方案A：主动触发会员升级(不依赖Z-Pay回调)
                # 从订单的param参数中获取user_id和plan_type
                try:
                    param_str = order.get("param", "")

                    # ✅ 新格式: 使用简单分隔符 "user_id|plan_type"
                    if "|" in param_str:
                        parts = param_str.split("|")
                        if len(parts) == 2:
                            user_id, plan_type = parts
                        else:
                            user_id = plan_type = None
                    else:
                        # 兼容旧格式: JSON
                        try:
                            import json
                            param_data = json.loads(param_str) if param_str else {}
                            user_id = param_data.get("user_id")
                            plan_type = param_data.get("plan_type")
                        except:
                            user_id = plan_type = None

                    if user_id and plan_type:
                        print(f"[MEMBERSHIP] Triggering manual upgrade: user={user_id}, plan={plan_type}")

                        # 调用后端API手动更新会员状态
                        upgrade_result = self.auth_client.manual_upgrade_subscription(
                            user_id=user_id,
                            plan_type=plan_type,
                            out_trade_no=out_trade_no
                        )

                        if upgrade_result.get("success"):
                            print("[MEMBERSHIP] Manual upgrade successful!")
                        else:
                            print(f"[MEMBERSHIP] Manual upgrade failed: {upgrade_result.get('error')}")
                    else:
                        print(f"[MEMBERSHIP] Warning: Missing user_id or plan_type in order param: {param_str}")

                except Exception as e:
                    print(f"[MEMBERSHIP] Error during manual upgrade: {e}")

                # 延迟刷新会员状态以显示最新数据
                QTimer.singleShot(1000, self._refresh_subscription_status)

                QMessageBox.information(
                    self,
                    tr("membership.payment.success_title"),
                    tr("membership.payment.success_message")
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

    def _refresh_subscription_status(self):
        """
        刷新订阅状态（支付成功后调用）

        ⚠️ 关键修复：支付回调可能有延迟,需要重试机制
        - 首次刷新：立即执行
        - 如果失败或状态未更新：1秒后重试,最多重试3次
        """
        print("[MEMBERSHIP] 开始刷新会员状态...")

        result = self.auth_client.get_subscription_status()

        if result.get("success"):
            user_tier = result.get("user_tier", "free")
            is_active = result.get("is_active", False)

            print(f"[MEMBERSHIP] 会员状态刷新成功: tier={user_tier}, active={is_active}")

            # 检查是否真的升级成功了
            if is_active and user_tier in ["pro", "lifetime"]:
                print("[MEMBERSHIP] ✓ 会员升级确认成功!")
                return
            else:
                print(f"[MEMBERSHIP] ⚠️ 状态异常: tier={user_tier}, active={is_active}")
        else:
            print(f"[MEMBERSHIP] 刷新失败: {result.get('error')}")

        # 如果刷新失败或状态未更新,尝试重试
        retry_count = getattr(self, '_refresh_retry_count', 0)
        if retry_count < 3:
            self._refresh_retry_count = retry_count + 1
            print(f"[MEMBERSHIP] 1秒后进行第 {self._refresh_retry_count} 次重试...")
            QTimer.singleShot(1000, self._refresh_subscription_status)
        else:
            print("[MEMBERSHIP] ✗ 已达到最大重试次数,请手动刷新或重新登录")
            self._refresh_retry_count = 0

    def _get_tier_name(self, tier: str) -> str:
        """获取会员等级名称"""
        tier_names = {
            "free": tr("membership.plan.free"),
            "pro": tr("membership.plan.pro"),
            "lifetime": tr("membership.plan.lifetime")
        }
        return tier_names.get(tier, tier)

    def _get_pay_type_name(self, pay_type: str) -> str:
        """获取支付方式名称"""
        pay_type_names = {
            "alipay": tr("membership.payment.alipay"),
            "wxpay": tr("membership.payment.wechat")
        }
        return pay_type_names.get(pay_type, pay_type)

    # paintEvent, moveEvent, resizeEvent 已移除
    # 原因：白色块问题已通过 MSWindowsFixedSizeDialogHint 窗口标志从根本解决
    # 强制重绘反而会在打包环境中干扰 QFrame 样式表渲染，导致黑色边框出现

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)

        # ========== 诊断日志：ShowEvent ==========
        print(f"\n[DIAG-FINAL] === ShowEvent ===", file=sys.stderr)

        # 统计QWidget数量（卡片都是QWidget了）
        all_widgets = self.findChildren(QWidget)
        print(f"[DIAG-FINAL] Found {len(all_widgets)} QWidget children", file=sys.stderr)
        print(f"[DIAG-FINAL] Using QWidget instead of QFrame - no frame border issues", file=sys.stderr)
        print(f"[DIAG-FINAL] === ShowEvent Complete ===\n", file=sys.stderr)

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
