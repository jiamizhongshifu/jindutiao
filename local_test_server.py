"""
本地测试服务器 - 用于Windows环境测试Zpay支付回调
绕过 Vercel CLI 在 Windows 上的兼容性问题

使用方法:
    python local_test_server.py

然后访问:
    http://localhost:3000/api/test-zpay-mock-callback
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件中的环境变量
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

# 设置环境变量（模拟 Vercel 环境）
os.environ.setdefault('ENVIRONMENT', 'development')

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# 导入我们的 mock 回调处理器
from api.config import Config
from api.subscription_manager import SubscriptionManager
from api.supabase_client import get_supabase_client
import json
import time
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求


@app.route('/api/test-zpay-mock-callback', methods=['POST', 'GET'])
def test_zpay_mock_callback():
    """Mock Zpay 支付回调端点"""

    # GET 请求返回使用说明
    if request.method == 'GET':
        return """
========================================
Zpay Mock Payment Callback - 使用说明
========================================

此端点用于模拟Zpay支付回调，无需真实支付即可测试订阅升级逻辑。

⚠️ 仅在开发环境可用 (ENVIRONMENT=development)

========================================
测试方法
========================================

使用Python脚本:
    python test_zpay_mock.py

使用curl:
    curl -X POST http://localhost:3000/api/test-zpay-mock-callback \\
      -H "Content-Type: application/json" \\
      -d '{
        "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
        "plan_type": "pro_monthly",
        "scenario": "success"
      }'

========================================
        """, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    # ========== 安全检查：仅开发环境可用 ==========
    if Config.is_production():
        logger.warning("[MOCK] Attempted to access mock callback in production")
        return jsonify({
            "error": "Mock callback is not available in production environment"
        }), 403

    try:
        # ========== 读取请求参数 ==========
        if request.is_json:
            params = request.get_json()
            logger.info(f"[MOCK] Received JSON params: {params}")
        else:
            params = request.form.to_dict()
            logger.info(f"[MOCK] Received form params: {params}")

        # ========== 从请求中提取或使用默认值 ==========
        user_id = params.get('user_id', 'df15202c-2ff0-4b12-9fc0-a1029d6000a7')
        plan_type = params.get('plan_type', 'pro_monthly')
        scenario = params.get('scenario', 'success')

        # ========== 生成模拟订单数据 ==========
        timestamp = int(time.time())
        out_trade_no = params.get('out_trade_no', f"MOCK_{timestamp}")

        # 获取对应计划的价格
        plan_prices = {
            "pro_monthly": "29.00",
            "pro_yearly": "199.00",
            "lifetime": "1200.00"
        }

        plan_names = {
            "pro_monthly": "Pro Monthly Subscription",
            "pro_yearly": "Pro Yearly Subscription",
            "lifetime": "Lifetime Membership"
        }

        money = params.get('money', plan_prices.get(plan_type, "29.00"))

        # ========== 构造模拟回调数据 ==========
        if scenario == 'success':
            mock_callback = {
                "pid": Config.get_zpay_pid(),
                "trade_no": f"MOCK_ZPAY_{timestamp}",
                "out_trade_no": out_trade_no,
                "type": params.get('type', 'alipay'),
                "name": plan_names.get(plan_type, "Test Product"),
                "money": money,
                "trade_status": "TRADE_SUCCESS",
                "param": json.dumps({
                    "user_id": user_id,
                    "plan_type": plan_type
                })
            }

            # 生成模拟签名
            sign_str = f"{mock_callback['pid']}{mock_callback['trade_no']}{mock_callback['out_trade_no']}{mock_callback['type']}{mock_callback['name']}{mock_callback['money']}{mock_callback['trade_status']}{Config.get_zpay_pkey()}"
            mock_callback['sign'] = hashlib.md5(sign_str.encode()).hexdigest()

            logger.info(f"[MOCK] Generated success callback: {mock_callback}")

            # ========== 调用真实的订阅管理器处理升级 ==========
            try:
                # 解析附加参数
                param_data = json.loads(mock_callback.get('param', '{}'))
                user_id = param_data.get('user_id')
                plan_type = param_data.get('plan_type')

                # 1. 先创建支付记录（模拟真实流程）
                supabase = get_supabase_client()
                payment_data = {
                    "user_id": user_id,
                    "order_id": mock_callback['out_trade_no'],
                    "amount": float(mock_callback['money']),
                    "currency": "CNY",
                    "payment_method": mock_callback.get('type', 'alipay'),
                    "payment_provider": "zpay",
                    "status": "completed",
                    "item_type": "subscription",
                    "item_metadata": json.dumps({
                        "plan_type": plan_type,
                        "trade_no": mock_callback['trade_no']
                    }),
                    "completed_at": "now()"
                }

                payment_response = supabase.table("payments").insert(payment_data).execute()

                if not payment_response.data:
                    raise Exception("Failed to create payment record")

                payment_id = payment_response.data[0]["id"]
                logger.info(f"[MOCK] Created payment record: {payment_id}")

                # 2. 创建订阅
                sub_manager = SubscriptionManager()
                result = sub_manager.create_subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    payment_id=payment_id,
                    payment_provider='zpay'
                )

                logger.info(f"[MOCK] Subscription creation result: {result}")

                # 检查订阅创建是否成功
                if result.get("success"):
                    # 返回成功响应
                    return jsonify({
                        "status": "success",
                        "message": "Mock payment callback processed successfully",
                        "mock_data": mock_callback,
                        "subscription_result": result,
                        "note": "This is a MOCK payment callback for testing purposes"
                    }), 200
                else:
                    # 订阅创建失败
                    return jsonify({
                        "status": "error",
                        "message": f"Subscription creation failed: {result.get('error', 'Unknown error')}",
                        "mock_data": mock_callback
                    }), 500

            except Exception as e:
                logger.error(f"[MOCK] Subscription creation failed: {str(e)}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": f"Subscription creation failed: {str(e)}",
                    "mock_data": mock_callback
                }), 500

        else:
            # 失败场景
            mock_callback = {
                "pid": Config.get_zpay_pid(),
                "trade_no": f"MOCK_ZPAY_FAIL_{timestamp}",
                "out_trade_no": out_trade_no,
                "type": params.get('type', 'alipay'),
                "name": plan_names.get(plan_type, "Test Product"),
                "money": money,
                "trade_status": "TRADE_CLOSED",
                "param": json.dumps({
                    "user_id": user_id,
                    "plan_type": plan_type
                })
            }

            logger.info(f"[MOCK] Generated failed callback: {mock_callback}")

            return jsonify({
                "status": "failed",
                "message": "Mock payment failed scenario",
                "mock_data": mock_callback,
                "note": "This simulates a failed payment for testing error handling"
            }), 200

    except Exception as e:
        logger.error(f"[MOCK] Error processing mock callback: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "Failed to process mock callback"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "ok",
        "environment": Config.get_environment(),
        "zpay_configured": Config.is_zpay_configured()
    }), 200


if __name__ == '__main__':
    import sys
    # 设置标准输出编码为UTF-8，避免Windows GBK编码问题
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("=" * 60)
    print("Local Test Server Starting")
    print("=" * 60)
    print(f"Environment: {Config.get_environment()}")
    print(f"Zpay Config: {'OK' if Config.is_zpay_configured() else 'Not configured'}")
    print()
    print("Available Endpoints:")
    print("  - http://localhost:3000/api/test-zpay-mock-callback (Mock Payment Callback)")
    print("  - http://localhost:3000/health (Health Check)")
    print()
    print("Test Command:")
    print("  python test_zpay_mock.py")
    print()
    print("Press Ctrl+C to stop server")
    print("=" * 60)

    # 启动 Flask 服务器
    app.run(
        host='0.0.0.0',
        port=3000,
        debug=True,
        use_reloader=False  # 避免重复启动
    )
