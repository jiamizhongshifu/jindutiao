"""
Stripe集成测试脚本
测试Checkout Session创建和基本功能
"""
import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置
API_BASE_URL = "http://localhost:3000"  # 本地测试
# API_BASE_URL = "https://jindutiao.vercel.app"  # 生产环境测试

# 测试数据
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # 示例UUID
TEST_EMAIL = "test@example.com"

def test_stripe_manager():
    """测试Stripe Manager初始化"""
    print("\n" + "="*60)
    print("测试 1: Stripe Manager 初始化")
    print("="*60)

    try:
        # 添加api目录到路径
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
        from stripe_manager import StripeManager

        manager = StripeManager()
        print("✅ Stripe Manager 初始化成功")
        print(f"   - Secret Key: {manager.secret_key[:7]}...")
        print(f"   - 月度价格ID: {manager.price_ids.get('pro_monthly', 'N/A')}")
        print(f"   - 年度价格ID: {manager.price_ids.get('pro_yearly', 'N/A')}")
        print(f"   - 终身价格ID: {manager.price_ids.get('lifetime', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_get_plan_info():
    """测试获取计划信息"""
    print("\n" + "="*60)
    print("测试 2: 获取计划信息")
    print("="*60)

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
        from stripe_manager import StripeManager

        manager = StripeManager()

        plans = ["pro_monthly", "pro_yearly", "lifetime"]
        for plan in plans:
            result = manager.get_plan_info(plan)
            if result["success"]:
                plan_data = result["plan"]
                print(f"\n✅ {plan}:")
                print(f"   - 名称: {plan_data['name']}")
                print(f"   - 价格: ${plan_data['price']} {plan_data['currency']}")
                print(f"   - 周期: {plan_data['interval']}")
            else:
                print(f"❌ {plan}: {result.get('error')}")

        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_create_checkout_session():
    """测试创建Checkout Session（需要本地或Vercel API运行）"""
    print("\n" + "="*60)
    print("测试 3: 创建Checkout Session")
    print("="*60)

    try:
        # 测试月度会员
        payload = {
            "user_id": TEST_USER_ID,
            "user_email": TEST_EMAIL,
            "plan_type": "pro_monthly"
        }

        print(f"\n发送请求到: {API_BASE_URL}/api/stripe-create-checkout")
        print(f"请求数据: {payload}")

        response = requests.post(
            f"{API_BASE_URL}/api/stripe-create-checkout",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"\n响应状态: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("\n✅ Checkout Session 创建成功!")
                print(f"   - Session ID: {data.get('session_id')}")
                print(f"   - Checkout URL: {data.get('checkout_url')}")
                print(f"   - Plan: {data.get('plan_name')}")
                print(f"   - Amount: ${data.get('amount')} {data.get('currency')}")
                print(f"\n🔗 在浏览器中打开支付页面:")
                print(f"   {data.get('checkout_url')}")
                return True
            else:
                print(f"❌ API返回失败: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"   响应: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n⚠️  无法连接到 {API_BASE_URL}")
        print("   请确保:")
        print("   1. 本地测试: 运行 'vercel dev' 启动本地服务器")
        print("   2. 生产测试: 修改 API_BASE_URL 为 Vercel 部署地址")
        return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_price_ids_exist():
    """验证Stripe价格ID是否配置"""
    print("\n" + "="*60)
    print("测试 4: 验证价格ID配置")
    print("="*60)

    price_ids = {
        "STRIPE_PRICE_MONTHLY": os.getenv("STRIPE_PRICE_MONTHLY"),
        "STRIPE_PRICE_YEARLY": os.getenv("STRIPE_PRICE_YEARLY"),
        "STRIPE_PRICE_LIFETIME": os.getenv("STRIPE_PRICE_LIFETIME")
    }

    all_configured = True
    for name, value in price_ids.items():
        if value and value.startswith("price_"):
            print(f"✅ {name}: {value}")
        else:
            print(f"❌ {name}: 未配置或格式错误")
            all_configured = False

    return all_configured

def test_webhook_signature():
    """测试Webhook签名验证逻辑"""
    print("\n" + "="*60)
    print("测试 5: Webhook签名验证（模拟）")
    print("="*60)

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret or not webhook_secret.startswith("whsec_"):
        print("⚠️  STRIPE_WEBHOOK_SECRET 未配置")
        print("   在配置Stripe Webhook后，需要设置此环境变量")
        return False
    else:
        print(f"✅ Webhook Secret 已配置: {webhook_secret[:10]}...")
        print("   注意: 实际签名验证需要在Stripe发送真实事件后测试")
        return True

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 Stripe集成测试套件")
    print("="*60)

    # 检查环境变量
    if not os.getenv("STRIPE_SECRET_KEY"):
        print("\n❌ 错误: STRIPE_SECRET_KEY 未配置")
        print("   请先配置 .env 文件")
        return

    results = []

    # 运行测试
    results.append(("Stripe Manager初始化", test_stripe_manager()))
    results.append(("获取计划信息", test_get_plan_info()))
    results.append(("价格ID配置", test_price_ids_exist()))
    results.append(("Webhook签名配置", test_webhook_signature()))
    results.append(("创建Checkout Session", test_create_checkout_session()))

    # 输出总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！Stripe集成配置正确。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")

    # 下一步提示
    print("\n" + "="*60)
    print("📝 下一步操作")
    print("="*60)

    if passed >= 4:  # 前4个测试通过
        print("\n1. 启动本地开发服务器（如果未启动）:")
        print("   vercel dev")
        print("\n2. 重新运行此脚本测试API:")
        print("   python test_stripe_integration.py")
        print("\n3. 使用测试卡号完成支付:")
        print("   卡号: 4242 4242 4242 4242")
        print("   有效期: 任意未来日期")
        print("   CVC: 任意3位数")
        print("\n4. 检查Supabase数据库验证订阅创建:")
        print("   - users表: user_tier 应更新为 'pro'")
        print("   - subscriptions表: 应有新记录")
        print("   - payments表: 应有支付记录")

if __name__ == "__main__":
    main()
