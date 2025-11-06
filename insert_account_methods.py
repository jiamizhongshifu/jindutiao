#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在第2395行之前插入所有账户tab相关方法
"""

def main():
    # 读取文件
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 在2395行之前（索引2394）插入所有账户相关方法
    insert_pos = 2394  # 在第2395行之前插入

    account_methods = '''
    def _create_account_tab(self):
        """创建账户标签页"""
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel("账户信息")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title_label)

        from gaiya.ui.auth_ui import AuthManager
        auth_manager = AuthManager()
        user_info = auth_manager.get_user_info()

        if user_info:
            email = user_info.get('email', '未登录')
            user_tier = user_info.get('user_tier', 'free')

            email_label = QLabel(f"邮箱：{email}")
            email_label.setStyleSheet("color: white; font-size: 14px; margin-bottom: 15px;")
            layout.addWidget(email_label)

            tier_names = {"free": "免费用户", "pro": "专业版", "lifetime": "终身会员"}
            tier_name = tier_names.get(user_tier, user_tier)
            tier_label = QLabel(f"会员等级：{tier_name}")
            tier_label.setStyleSheet("color: white; font-size: 14px; margin-bottom: 20px;")
            layout.addWidget(tier_label)

            if user_tier == "free":
                tip_label = QLabel("选择适合你的套餐：")
                tip_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; margin-bottom: 10px;")
                layout.addWidget(tip_label)

                cards_layout = QHBoxLayout()
                cards_layout.setSpacing(12)

                plans = [
                    {"id": "pro_monthly", "name": "专业版 - 月付", "price": "¥29", "period": "/月", "color": "#FF6B6B", "features": ["50次/天 任务规划", "10次/周 进度报告", "100次/天 AI对话"]},
                    {"id": "pro_yearly", "name": "专业版 - 年付", "price": "¥199", "period": "/年", "color": "#4ECDC4", "features": ["50次/天 任务规划", "10次/周 进度报告", "100次/天 AI对话", "💰 省30%"]},
                    {"id": "lifetime", "name": "终身会员", "price": "¥499", "period": "买断", "color": "#95A99C", "features": ["无限使用所有功能", "一次付费永久使用", "⭐ 最超值"]}
                ]

                self.plan_cards = []
                self.selected_plan_id = "pro_yearly"
                for i, plan in enumerate(plans):
                    card = self._create_simple_plan_card(plan, i == 1)
                    cards_layout.addWidget(card)
                    self.plan_cards.append(card)

                layout.addLayout(cards_layout)

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
                info_label = QLabel("感谢您的支持！")
                info_label.setStyleSheet("color: white; font-size: 14px;")
                layout.addWidget(info_label)
        else:
            login_label = QLabel("请先登录")
            login_label.setStyleSheet("color: white; font-size: 14px;")
            layout.addWidget(login_label)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _create_simple_plan_card(self, plan: dict, is_selected: bool = False):
        """创建简单的套餐卡片"""
        from PySide6.QtWidgets import QFrame
        card = QFrame()
        card.setObjectName(f"plan_card_{plan['id']}")
        card.setFixedSize(220, 200)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        border_color = plan['color'] if is_selected else "#555"
        border_width = "3px" if is_selected else "2px"

        card.setStyleSheet(f"""
            QFrame#plan_card_{plan['id']} {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {plan['color']}, stop:1 rgba(30, 30, 30, 220));
                border: {border_width} solid {border_color};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        name_label = QLabel(plan['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

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

        for feature in plan['features']:
            feature_label = QLabel(f"• {feature}")
            feature_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.85); background: transparent;")
            layout.addWidget(feature_label)

        layout.addStretch()
        card.plan_id = plan['id']
        card.mousePressEvent = lambda e: self._on_plan_card_clicked(plan['id'])
        return card

    def _on_plan_card_clicked(self, plan_id: str):
        """处理套餐卡片点击"""
        self.selected_plan_id = plan_id
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
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {plan['color']}, stop:1 rgba(30, 30, 30, 220));
                    border: {border_width} solid {border_color};
                    border-radius: 12px;
                }}
            """)

    def _on_purchase_clicked(self):
        """处理前往付费按钮点击"""
        from PySide6.QtWidgets import QMessageBox
        plan_names = {"pro_monthly": "专业版 - 月付", "pro_yearly": "专业版 - 年付", "lifetime": "终身会员"}
        plan_name = plan_names.get(self.selected_plan_id, self.selected_plan_id)
        QMessageBox.information(self, "前往付费", f"您选择了：{plan_name}\\n\\n付费功能正在开发中...\\n将为您跳转到支付页面")

'''

    lines.insert(insert_pos, account_methods)

    # 写回文件
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("SUCCESS - Account methods inserted at line 2395")

if __name__ == '__main__':
    main()
