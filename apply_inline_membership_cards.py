#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用内嵌会员卡片修改脚本
将弹窗模式改为直接在账户tab中展示套餐卡片
"""
import re

def main():
    # 读取文件
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 替换免费用户的显示区域
    old_free_user_section = r'''            if user_tier == "free":
                # 免费用户：显示升级按钮
                tip_label = QLabel\("升级到专业版，解锁所有高级功能："\)
                tip_label\.setStyleSheet\("color: white; font-size: 14px;"\)
                layout\.addWidget\(tip_label\)

                features_label = QLabel\(
                    "✓ 每日智能任务规划 50次/天\\n"
                    "✓ 每周进度报告 10次/周\\n"
                    "✓ AI对话助手 100次/天\\n"
                    "✓ 自定义主题和样式\\n"
                    "✓ 所有高级功能"
                \)
                features_label\.setStyleSheet\("color: #bbb; margin: 10px 0; font-size: 13px;"\)
                layout\.addWidget\(features_label\)

                upgrade_button = QPushButton\("立即升级"\)
                upgrade_button\.setFixedHeight\(40\)
                upgrade_button\.setStyleSheet\("""
                    QPushButton \{
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 10px;
                        font-size: 14px;
                        font-weight: bold;
                    \}
                    QPushButton:hover \{
                        background-color: #F57C00;
                    \}
                """\)
                upgrade_button\.clicked\.connect\(self\._on_upgrade_clicked\)
                layout\.addWidget\(upgrade_button\)'''

    new_free_user_section = '''            if user_tier == "free":
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
                layout.addWidget(purchase_button)'''

    content = re.sub(old_free_user_section, new_free_user_section, content, flags=re.DOTALL)

    # 2. 在_get_tier_name方法之前添加新方法
    new_methods = '''    def _create_simple_plan_card(self, plan: dict, is_selected: bool = False) -> QFrame:
        """创建简单的套餐卡片（使用纯stylesheet，避免QPainter问题）"""
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

'''

    # 在_get_tier_name之前插入
    content = content.replace('    def _get_tier_name(self, tier: str)', new_methods + '    def _get_tier_name(self, tier: str)')

    # 写回文件
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS - Successfully applied inline membership cards modification")

if __name__ == '__main__':
    main()
