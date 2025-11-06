#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加账户tab的完整内容和延迟加载逻辑
"""
import re

def main():
    # 读取文件
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 修改on_tab_changed方法，添加账户tab的处理
    old_on_tab_changed = r'''    def on_tab_changed\(self, index\):
        """标签页切换时的处理\(实现懒加载\)"""
        if index == 2:  # 通知设置标签页（主题设置已移除）
            if self\.notification_tab_widget is None:
                self\._load_notification_tab\(\)'''

    new_on_tab_changed = '''    def on_tab_changed(self, index):
        """标签页切换时的处理(实现懒加载)"""
        if index == 2:  # 通知设置标签页（主题设置已移除）
            if self.notification_tab_widget is None:
                self._load_notification_tab()
        elif index == 3:  # 账户标签页
            if self.account_tab_widget is None:
                self._load_account_tab()'''

    content = re.sub(old_on_tab_changed, new_on_tab_changed, content, flags=re.DOTALL)

    # 2. 在_load_notification_tab方法之后添加_load_account_tab方法
    load_notification_tab_end = r'            self\.tabs\.insertTab\(2, self\.notification_tab_widget, "🔔 通知设置"\)\n'

    new_load_account_tab = '''            self.tabs.insertTab(2, self.notification_tab_widget, "🔔 通知设置")

    def _load_account_tab(self):
        """加载账户标签页"""
        if self.account_tab_widget is not None:
            return  # 已经加载过了

        try:
            self.account_tab_widget = self._create_account_tab()
            self.tabs.setTabEnabled(3, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.account_tab_widget, "👤 账户")
            self.tabs.setCurrentIndex(3)  # 切换到账户标签页
        except Exception as e:
            import logging
            logging.error(f"加载账户标签页失败: {e}")
            # 显示错误提示
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"加载账户标签页失败: {e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.account_tab_widget = error_widget
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.account_tab_widget, "👤 账户")
'''

    content = re.sub(load_notification_tab_end, new_load_account_tab, content)

    # 3. 在_get_tier_name方法之前添加账户tab相关的所有方法
    get_tier_name_start = r'    def _get_tier_name\(self, tier: str\)'

    new_account_methods = '''    def _create_account_tab(self):
        """创建账户标签页"""
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("账户信息")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 获取用户信息
        from gaiya.ui.auth_ui import AuthManager
        auth_manager = AuthManager()
        user_info = auth_manager.get_user_info()

        if user_info:
            email = user_info.get('email', '未登录')
            user_tier = user_info.get('user_tier', 'free')

            # 显示邮箱
            email_label = QLabel(f"邮箱：{email}")
            email_label.setStyleSheet("color: white; font-size: 14px; margin-bottom: 15px;")
            layout.addWidget(email_label)

            # 显示会员等级
            tier_name = self._get_tier_name(user_tier)
            tier_label = QLabel(f"会员等级：{tier_name}")
            tier_label.setStyleSheet("color: white; font-size: 14px; margin-bottom: 20px;")
            layout.addWidget(tier_label)

            # 根据用户等级显示不同内容
            if user_tier == "free":
                # 免费用户：直接显示3个付费套餐卡片
                tip_label = QLabel("选择适合你的套餐：")
                tip_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; margin-bottom: 10px;")
                layout.addWidget(tip_label)

                # 创建卡片容器（水平布局）
                cards_layout = QHBoxLayout()
                cards_layout.setSpacing(12)

                # 套餐数据
                plans = [
                    {
                        "id": "pro_monthly",
                        "name": "专业版 - 月付",
                        "price": "¥29",
                        "period": "/月",
                        "color": "#FF6B6B",
                        "features": ["50次/天 任务规划", "10次/周 进度报告", "100次/天 AI对话"]
                    },
                    {
                        "id": "pro_yearly",
                        "name": "专业版 - 年付",
                        "price": "¥199",
                        "period": "/年",
                        "color": "#4ECDC4",
                        "features": ["50次/天 任务规划", "10次/周 进度报告", "100次/天 AI对话", "💰 省30%"]
                    },
                    {
                        "id": "lifetime",
                        "name": "终身会员",
                        "price": "¥499",
                        "period": "买断",
                        "color": "#95A99C",
                        "features": ["无限使用所有功能", "一次付费永久使用", "⭐ 最超值"]
                    }
                ]

                # 创建3个卡片
                self.plan_cards = []
                self.selected_plan_id = "pro_yearly"  # 默认选中年付
                for i, plan in enumerate(plans):
                    card = self._create_simple_plan_card(plan, i == 1)  # 年付默认选中
                    cards_layout.addWidget(card)
                    self.plan_cards.append(card)

                layout.addLayout(cards_layout)

                # 前往付费按钮
                purchase_button = QPushButton("前往付费")
                purchase_button.setFixedHeight(44)
                purchase_button.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 12px;
                        font-size: 15px;
                        font-weight: bold;
                        margin-top: 15px;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                    }
                    QPushButton:pressed {
                        background-color: #E65100;
                    }
                """)
                purchase_button.clicked.connect(self._on_purchase_clicked)
                layout.addWidget(purchase_button)
            else:
                # 付费用户：显示会员信息和管理选项
                info_label = QLabel("感谢您的支持！")
                info_label.setStyleSheet("color: white; font-size: 14px;")
                layout.addWidget(info_label)
        else:
            # 未登录：显示登录提示
            login_label = QLabel("请先登录")
            login_label.setStyleSheet("color: white; font-size: 14px;")
            layout.addWidget(login_label)

        layout.addStretch()

        scroll_area.setWidget(content_widget)
        return scroll_area

    def _create_simple_plan_card(self, plan: dict, is_selected: bool = False):
        """创建简单的套餐卡片（使用纯stylesheet，避免QPainter问题）"""
        from PySide6.QtWidgets import QFrame
        card = QFrame()
        card.setObjectName(f"plan_card_{plan['id']}")
        card.setFixedSize(220, 200)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        # 卡片样式（使用stylesheet）
        border_color = plan['color'] if is_selected else "#555"
        border_width = "3px" if is_selected else "2px"

        card.setStyleSheet(f"""
            QFrame#plan_card_{plan['id']} {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {plan['color']},
                    stop:1 rgba(30, 30, 30, 220)
                );
                border: {border_width} solid {border_color};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        # 套餐名称
        name_label = QLabel(plan['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # 价格
        price_layout = QHBoxLayout()
        price_layout.setSpacing(2)
        price_label = QLabel(plan['price'])
        price_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent;")
        period_label = QLabel(plan['period'])
        period_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); background: transparent;")
        period_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        price_layout.addStretch()
        price_layout.addWidget(price_label)
        price_layout.addWidget(period_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        layout.addSpacing(5)

        # 特性列表
        for feature in plan['features']:
            feature_label = QLabel(f"• {feature}")
            feature_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.85); background: transparent;")
            layout.addWidget(feature_label)

        layout.addStretch()

        # 存储plan_id用于点击识别
        card.plan_id = plan['id']

        # 点击事件
        card.mousePressEvent = lambda e: self._on_plan_card_clicked(plan['id'])

        return card

    def _on_plan_card_clicked(self, plan_id: str):
        """处理套餐卡片点击"""
        self.selected_plan_id = plan_id

        # 更新所有卡片的选中状态
        plans_data = [
            {"id": "pro_monthly", "color": "#FF6B6B"},
            {"id": "pro_yearly", "color": "#4ECDC4"},
            {"id": "lifetime", "color": "#95A99C"}
        ]

        for i, card in enumerate(self.plan_cards):
            plan = plans_data[i]
            is_selected = (plan['id'] == plan_id)
            border_color = plan['color'] if is_selected else "#555"
            border_width = "3px" if is_selected else "2px"

            card.setStyleSheet(f"""
                QFrame#plan_card_{plan['id']} {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 {plan['color']},
                        stop:1 rgba(30, 30, 30, 220)
                    );
                    border: {border_width} solid {border_color};
                    border-radius: 12px;
                }}
            """)

    def _on_purchase_clicked(self):
        """处理前往付费按钮点击"""
        from PySide6.QtWidgets import QMessageBox
        plan_names = {
            "pro_monthly": "专业版 - 月付",
            "pro_yearly": "专业版 - 年付",
            "lifetime": "终身会员"
        }
        plan_name = plan_names.get(self.selected_plan_id, self.selected_plan_id)

        QMessageBox.information(
            self,
            "前往付费",
            f"您选择了：{plan_name}\\n\\n付费功能正在开发中...\\n将为您跳转到支付页面"
        )

    def _get_tier_name(self, tier: str)'''

    content = re.sub(get_tier_name_start, new_account_methods, content)

    # 写回文件
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS - Account tab content added")

if __name__ == '__main__':
    main()
