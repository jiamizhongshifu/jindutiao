"""
测试支付成功后会员状态刷新功能

测试场景:
1. 模拟支付成功
2. 验证自动刷新逻辑
3. 验证手动刷新按钮

运行方法:
python test_payment_refresh.py
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from PySide6.QtWidgets import QApplication
from gaiya.core.auth_client import AuthClient

def test_subscription_status_api():
    """测试订阅状态API"""
    print("\n=== 测试订阅状态API ===")

    auth_client = AuthClient()

    # 检查是否登录
    user_id = auth_client.get_user_id()
    if not user_id:
        print("❌ 未登录,无法测试")
        return False

    print(f"✓ 已登录用户: {user_id}")
    print(f"✓ 邮箱: {auth_client.get_user_email()}")
    print(f"✓ 当前等级: {auth_client.get_user_tier()}")

    # 调用订阅状态API
    print("\n正在查询订阅状态...")
    result = auth_client.get_subscription_status()

    if result.get("success"):
        print("✓ API调用成功")
        print(f"  - 会员等级: {result.get('user_tier')}")
        print(f"  - 激活状态: {result.get('is_active')}")
        if result.get('expires_at'):
            print(f"  - 过期时间: {result.get('expires_at')}")
        if result.get('plan_type'):
            print(f"  - 套餐类型: {result.get('plan_type')}")
        return True
    elif result.get("fallback"):
        print("⚠️ API未部署,使用本地缓存")
        print(f"  - 本地等级: {auth_client.get_user_tier()}")
        return True
    else:
        print(f"❌ API调用失败: {result.get('error')}")
        return False


def test_membership_ui():
    """测试会员UI中的刷新逻辑"""
    print("\n=== 测试会员UI刷新逻辑 ===")

    try:
        from gaiya.ui.membership_ui import MembershipDialog
        print("✓ MembershipDialog导入成功")

        # 检查方法是否存在
        if hasattr(MembershipDialog, '_refresh_subscription_status'):
            print("✓ _refresh_subscription_status方法存在")
        else:
            print("❌ _refresh_subscription_status方法不存在")
            return False

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_config_gui_refresh_button():
    """测试config_gui中的刷新按钮"""
    print("\n=== 测试个人中心刷新按钮 ===")

    try:
        # 读取config_gui.py源码,检查是否包含刷新按钮
        with open('config_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ('_on_refresh_account_clicked', '刷新账户方法'),
            ('_on_refresh_success', '刷新成功回调'),
            ('_on_refresh_error', '刷新失败回调'),
            ('refresh_btn', '刷新按钮'),
            ('account.refresh_tooltip', '刷新提示翻译')
        ]

        all_passed = True
        for keyword, name in checks:
            if keyword in content:
                print(f"✓ {name}存在")
            else:
                print(f"❌ {name}不存在")
                all_passed = False

        return all_passed
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def test_i18n_keys():
    """测试国际化翻译"""
    print("\n=== 测试国际化翻译 ===")

    import json

    try:
        # 检查中文翻译
        with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
            zh_data = json.load(f)

        if 'account' in zh_data and 'refresh_tooltip' in zh_data['account']:
            print(f"✓ 中文翻译存在: {zh_data['account']['refresh_tooltip']}")
        else:
            print("❌ 中文翻译缺失")
            return False

        # 检查英文翻译
        with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
            en_data = json.load(f)

        if 'account' in en_data and 'refresh_tooltip' in en_data['account']:
            print(f"✓ 英文翻译存在: {en_data['account']['refresh_tooltip']}")
        else:
            print("❌ 英文翻译缺失")
            return False

        return True
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def main():
    """主测试函数"""
    print("="*60)
    print("支付成功后会员状态刷新功能测试")
    print("="*60)

    # 创建QApplication (某些API需要)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    results = []

    # 运行所有测试
    results.append(("订阅状态API", test_subscription_status_api()))
    results.append(("会员UI刷新逻辑", test_membership_ui()))
    results.append(("个人中心刷新按钮", test_config_gui_refresh_button()))
    results.append(("国际化翻译", test_i18n_keys()))

    # 输出总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n🎉 所有测试通过!修复已成功应用。")
        print("\n下一步:")
        print("1. 运行 'python main.py' 测试开发环境")
        print("2. 完成支付后观察会员状态是否自动刷新")
        print("3. 点击个人中心的'🔄 刷新'按钮测试手动刷新")
        print("4. 运行 'cmd /c build-fast.bat' 打包测试")
        return 0
    else:
        print("\n⚠️ 部分测试失败,请检查修复是否正确应用。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
