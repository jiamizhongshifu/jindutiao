# -*- coding: utf-8 -*-
"""
测试Z-Pay凭证配置
验证环境变量是否正确配置
"""
import sys
import io
import os

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("Z-Pay凭证配置检查")
print("="*60)
print()

# 1. 检查本地环境变量
print("1. 检查本地环境变量")
print("-" * 40)

zpay_pid = os.getenv("ZPAY_PID")
zpay_pkey = os.getenv("ZPAY_PKEY")

if zpay_pid:
    print(f"✓ ZPAY_PID: {zpay_pid[:10]}... (长度: {len(zpay_pid)})")
else:
    print("✗ ZPAY_PID: 未配置")

if zpay_pkey:
    print(f"✓ ZPAY_PKEY: {zpay_pkey[:10]}... (长度: {len(zpay_pkey)})")
else:
    print("✗ ZPAY_PKEY: 未配置")

print()

# 2. 检查是否是占位符
print("2. 检查是否是占位符值")
print("-" * 40)

placeholder_keywords = ['your_', 'here', 'example', 'test', 'demo', 'placeholder']
is_placeholder = False

if zpay_pid:
    for keyword in placeholder_keywords:
        if keyword.lower() in zpay_pid.lower():
            print(f"⚠️ ZPAY_PID 可能是占位符 (包含'{keyword}')")
            is_placeholder = True
            break
    if not is_placeholder:
        print(f"✓ ZPAY_PID 看起来是真实值")

if zpay_pkey:
    is_placeholder_key = False
    for keyword in placeholder_keywords:
        if keyword.lower() in zpay_pkey.lower():
            print(f"⚠️ ZPAY_PKEY 可能是占位符 (包含'{keyword}')")
            is_placeholder_key = True
            break
    if not is_placeholder_key:
        print(f"✓ ZPAY_PKEY 看起来是真实值")

print()

# 3. 测试Z-Pay API连接
print("3. 测试Z-Pay API连接")
print("-" * 40)

if not zpay_pid or not zpay_pkey:
    print("❌ 无法测试: 环境变量未配置")
else:
    try:
        sys.path.insert(0, 'api')
        from zpay_manager import ZPayManager
        import hashlib

        # 创建测试订单号
        test_order_no = f"TEST_{int(__import__('time').time())}"

        # 测试签名生成
        print("测试签名算法...")
        params = {
            "pid": zpay_pid,
            "out_trade_no": test_order_no
        }

        # 按ASCII排序
        sorted_params = sorted(params.items())
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_str += zpay_pkey

        expected_sign = hashlib.md5(sign_str.encode(), usedforsecurity=False).hexdigest()
        print(f"✓ 签名生成成功: {expected_sign[:16]}...")
        print()

        # 测试查询API (使用不存在的订单)
        print("测试Z-Pay查询API...")
        zpay = ZPayManager()
        result = zpay.query_order(out_trade_no="NONEXISTENT_ORDER_12345")

        print(f"API返回: {result}")
        print()

        # 分析返回结果
        if result.get("success") == False:
            error = result.get("error", "")
            if "pid不存在" in error or "key错误" in error:
                print("❌ 凭证验证失败!")
                print(f"   错误: {error}")
                print()
                print("可能原因:")
                print("  1. ZPAY_PID 或 ZPAY_PKEY 配置错误")
                print("  2. 商户账户已停用")
                print("  3. IP白名单限制")
            elif "未找到" in error or "不存在" in error:
                print("✅ 凭证验证成功!")
                print("   (订单不存在错误说明凭证是正确的)")
            else:
                print(f"⚠️ 未知错误: {error}")
        else:
            print("✅ API调用成功")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

print()
print("="*60)
print()

# 4. 提供建议
print("💡 建议:")
print("-" * 40)

if not zpay_pid or not zpay_pkey:
    print("1. 请设置环境变量 ZPAY_PID 和 ZPAY_PKEY")
    print("   Windows命令行:")
    print("     set ZPAY_PID=你的商户ID")
    print("     set ZPAY_PKEY=你的商户密钥")
    print()
    print("   或在 .env 文件中配置")
elif is_placeholder:
    print("1. 请替换占位符为真实的Z-Pay商户凭证")
    print("2. 登录 https://z-pay.cn/ 获取真实凭证")
else:
    print("1. 本地配置看起来正常")
    print("2. 确认Vercel环境变量与本地一致")
    print("3. 如果API仍然返回'pid错误',请:")
    print("   - 检查Z-Pay商户账户状态")
    print("   - 确认账户已实名认证")
    print("   - 联系Z-Pay技术支持")

print()
print("="*60)
