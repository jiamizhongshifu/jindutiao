# -*- coding: utf-8 -*-
"""
检查API价格是否已更新
"""
import sys
import io
import requests

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("检查API价格更新状态")
print("="*60)
print()

# 从本地subscription_manager.py读取价格
print("1. 本地代码价格:")
try:
    sys.path.insert(0, 'api')
    from subscription_manager import SubscriptionManager
    sm = SubscriptionManager()

    for plan_type, plan_data in sm.PLANS.items():
        print(f"  {plan_type}: ¥{plan_data['price']}")

    local_monthly_price = sm.PLANS['pro_monthly']['price']
    print(f"\n✓ 本地月度价格: ¥{local_monthly_price}")
except Exception as e:
    print(f"❌ 读取本地价格失败: {e}")
    local_monthly_price = None

print()
print("2. Vercel部署状态:")
print("  检查方法: 访问 https://vercel.com/你的项目/deployments")
print("  最近提交: feat: 设置测试价格0.1元")
print()

print("3. 测试建议:")
if local_monthly_price == 0.1:
    print("  ✓ 本地代码已更新为测试价格")
    print("  ⏳ 等待Vercel部署完成(通常2-3分钟)")
    print("  📝 部署完成后,支付页面将显示¥0.1")
    print()
    print("  或者:")
    print("  💡 如果Vercel部署慢,可以暂时使用原价¥199测试")
    print("     (测试刷新功能不需要真的支付)")
else:
    print("  ⚠️ 本地代码可能未正确更新")

print()
print("="*60)
