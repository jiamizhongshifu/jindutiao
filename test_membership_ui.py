#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试会员购买对话框界面
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from gaiya.ui.membership_ui import MembershipDialog
from gaiya.core.auth_client import AuthClient


def main():
    app = QApplication(sys.argv)

    # 创建认证客户端
    auth_client = AuthClient()

    # 检查登录状态
    if not auth_client.is_logged_in():
        print("当前未登录,将显示一个模拟的会员购买界面")
        print("(实际使用时需要先登录)")
        print()

        # 为了测试界面,临时模拟登录状态
        # 注意:这仅用于UI测试,实际使用时必须真实登录
        import json
        auth_file = project_root / "data" / ".gaiya_auth"
        auth_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入临时测试凭证
        test_auth = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "tier": "free",
            "session_token": "test_token_for_ui_preview"
        }
        with open(auth_file, 'w', encoding='utf-8') as f:
            json.dump(test_auth, f)

        print(f"✓ 已创建临时测试凭证: {auth_file}")
        print("  (测试完成后请删除此文件)")
        print()

        # 重新加载认证客户端
        auth_client = AuthClient()

    # 显示会员购买对话框
    dialog = MembershipDialog(auth_client)

    # 监听购买成功信号
    def on_purchase_success(plan_type):
        print(f"\n✓ 购买成功! 套餐: {plan_type}")

    dialog.purchase_success.connect(on_purchase_success)

    # 显示对话框
    result = dialog.exec()

    if result:
        print("\n用户点击了'立即购买'")
    else:
        print("\n用户取消了购买")

    return 0


if __name__ == "__main__":
    sys.exit(main())
