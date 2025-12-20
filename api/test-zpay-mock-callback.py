"""
测试用：模拟Zpay支付回调
用于测试订阅升级逻辑，无需真实支付

⚠️ 安全限制:
- 仅在开发环境可用 (ENVIRONMENT=development)
- 生产环境返回403禁止访问

使用方法:
1. 设置环境变量: ENVIRONMENT=development
2. 启动本地服务: vercel dev
3. POST请求到: http://localhost:3000/api/test-zpay-mock-callback
4. 请求体示例见下方

测试场景:
- 场景1: Pro月度订阅支付成功
- 场景2: Pro年度订阅支付成功
- 场景3: 终身会员支付成功
- 场景4: 支付失败场景
"""
from http.server import BaseHTTPRequestHandler
from api.config import Config
from api.subscription_manager import SubscriptionManager
from api.supabase_client import get_supabase_client
import json
import time
import hashlib
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理POST请求 - 模拟Zpay支付回调"""

        # ========== 安全检查：仅开发环境可用 ==========
        if Config.is_production():
            logger.warning("[MOCK] Attempted to access mock callback in production")
            self.send_response(403)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Mock callback is not available in production environment"
            }).encode())
            return

        try:
            # ========== 读取请求参数 ==========
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            # 尝试解析JSON（如果发送的是JSON）
            try:
                params = json.loads(post_data)
                logger.info(f"[MOCK] Received JSON params: {params}")
            except json.JSONDecodeError:
                # 如果不是JSON，尝试解析form-urlencoded
                from urllib.parse import parse_qs
                params = {}
                for key, value in parse_qs(post_data).items():
                    params[key] = value[0] if len(value) == 1 else value
                logger.info(f"[MOCK] Received form params: {params}")

            # ========== 从请求中提取或使用默认值 ==========
            user_id = params.get('user_id', 'df15202c-2ff0-4b12-9fc0-a1029d6000a7')  # 默认测试用户
            plan_type = params.get('plan_type', 'pro_monthly')  # 默认月度会员
            scenario = params.get('scenario', 'success')  # success/failed

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

                # 生成模拟签名（使用真实的签名逻辑）
                sign_str = f"{mock_callback['pid']}{mock_callback['trade_no']}{mock_callback['out_trade_no']}{mock_callback['type']}{mock_callback['name']}{mock_callback['money']}{mock_callback['trade_status']}{Config.get_zpay_pkey()}"
                mock_callback['sign'] = hashlib.md5(sign_str.encode()).hexdigest()

                logger.info(f"[MOCK] Generated success callback: {mock_callback}")

                # ========== 调用真实的订阅管理器处理升级 ==========
                try:
                    supabase = get_supabase_client()
                    sub_manager = SubscriptionManager(supabase)

                    # 解析附加参数
                    param_data = json.loads(mock_callback.get('param', '{}'))

                    # 执行订阅升级
                    result = sub_manager.upgrade_subscription(
                        user_id=param_data.get('user_id'),
                        plan_type=param_data.get('plan_type'),
                        payment_method='zpay',
                        transaction_id=mock_callback['trade_no']
                    )

                    logger.info(f"[MOCK] Subscription upgrade result: {result}")

                    # 返回成功响应
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "success",
                        "message": "Mock payment callback processed successfully",
                        "mock_data": mock_callback,
                        "upgrade_result": result,
                        "note": "This is a MOCK payment callback for testing purposes"
                    }, ensure_ascii=False, indent=2).encode('utf-8'))

                except Exception as e:
                    logger.error(f"[MOCK] Subscription upgrade failed: {str(e)}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": f"Subscription upgrade failed: {str(e)}",
                        "mock_data": mock_callback
                    }, ensure_ascii=False).encode('utf-8'))

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

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "failed",
                    "message": "Mock payment failed scenario",
                    "mock_data": mock_callback,
                    "note": "This simulates a failed payment for testing error handling"
                }, ensure_ascii=False, indent=2).encode('utf-8'))

        except Exception as e:
            logger.error(f"[MOCK] Error processing mock callback: {str(e)}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "message": "Failed to process mock callback"
            }).encode())

    def do_GET(self):
        """处理GET请求 - 返回使用说明"""

        if Config.is_production():
            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Mock callback is not available in production')
            return

        usage_guide = """
========================================
Zpay Mock Payment Callback - 使用说明
========================================

此端点用于模拟Zpay支付回调，无需真实支付即可测试订阅升级逻辑。

⚠️ 仅在开发环境可用 (ENVIRONMENT=development)

========================================
测试方法
========================================

方法1: 使用curl命令
-------------------
# 测试Pro月度订阅成功
curl -X POST http://localhost:3000/api/test-zpay-mock-callback \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
    "plan_type": "pro_monthly",
    "scenario": "success"
  }'

# 测试Pro年度订阅成功
curl -X POST http://localhost:3000/api/test-zpay-mock-callback \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
    "plan_type": "pro_yearly",
    "scenario": "success"
  }'

# 测试终身会员成功
curl -X POST http://localhost:3000/api/test-zpay-mock-callback \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
    "plan_type": "lifetime",
    "scenario": "success"
  }'

# 测试支付失败场景
curl -X POST http://localhost:3000/api/test-zpay-mock-callback \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
    "plan_type": "pro_monthly",
    "scenario": "failed"
  }'

方法2: 使用Python脚本
--------------------
见项目根目录的 test_zpay_mock.py

========================================
请求参数说明
========================================

user_id (可选):
  用户ID，默认: df15202c-2ff0-4b12-9fc0-a1029d6000a7

plan_type (可选):
  订阅类型，可选值:
  - pro_monthly (月度会员)
  - pro_yearly (年度会员)
  - lifetime (终身会员)
  默认: pro_monthly

scenario (可选):
  测试场景，可选值:
  - success (支付成功)
  - failed (支付失败)
  默认: success

out_trade_no (可选):
  商户订单号，默认自动生成

========================================
验证方法
========================================

1. 检查API响应状态
2. 检查Supabase数据库user_subscriptions表
3. 在GaiYa客户端查看会员状态是否更新

========================================
"""

        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(usage_guide.encode('utf-8'))
