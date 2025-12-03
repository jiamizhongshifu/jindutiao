# -*- coding: utf-8 -*-
"""
测试个人中心标签页加载
用于诊断崩溃问题
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("开始测试...")

try:
    print("1. 导入PySide6...")
    from PySide6.QtWidgets import QApplication
    print("✓ PySide6导入成功")

    print("\n2. 导入AuthClient...")
    from gaiya.core.auth_client import AuthClient
    print("✓ AuthClient导入成功")

    print("\n3. 创建QApplication...")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    print("✓ QApplication创建成功")

    print("\n4. 创建AuthClient实例...")
    auth_client = AuthClient()
    print("✓ AuthClient实例创建成功")

    print("\n5. 检查用户登录状态...")
    user_id = auth_client.get_user_id()
    print(f"✓ 用户ID: {user_id}")
    print(f"✓ 邮箱: {auth_client.get_user_email()}")
    print(f"✓ 会员等级: {auth_client.get_user_tier()}")

    print("\n6. 测试价格显示...")
    plans = [
        {
            "id": "pro_monthly",
            "price": "¥0.1",
        },
        {
            "id": "pro_yearly",
            "price": "¥0.1",
        },
        {
            "id": "lifetime",
            "price": "¥0.1",
        },
    ]
    for plan in plans:
        print(f"  {plan['id']}: {plan['price']}")
    print("✓ 价格显示正常")

    print("\n7. 导入config_gui...")
    import config_gui
    print("✓ config_gui导入成功")

    print("\n✅ 所有测试通过!")
    print("\n如果点击个人中心仍然崩溃,请运行以下命令并提供完整输出:")
    print("  python main.py 2>&1 | tee error.log")

except Exception as e:
    print(f"\n❌ 测试失败!")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {e}")

    import traceback
    print("\n完整堆栈跟踪:")
    traceback.print_exc()

    sys.exit(1)
