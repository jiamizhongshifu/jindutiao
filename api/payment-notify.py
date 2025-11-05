"""
支付结果异步通知API
GET /api/payment-notify
ZPAY会通过GET方式发送支付结果通知
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
from urllib.parse import parse_qs, urlparse

try:
    from zpay_manager import ZPayManager
    from subscription_manager import SubscriptionManager
    from supabase import create_client, Client
    import os
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from zpay_manager import ZPayManager
    from subscription_manager import SubscriptionManager
    from supabase import create_client, Client

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


class handler(BaseHTTPRequestHandler):
    """支付通知处理器"""

    def do_GET(self):
        """处理支付通知（ZPAY使用GET方式）"""
        try:
            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            params = {}
            for key, value in parse_qs(parsed_url.query).items():
                params[key] = value[0] if len(value) == 1 else value

            print(f"[PAYMENT-NOTIFY] Received notification: {params.get('out_trade_no')}", file=sys.stderr)

            # 2. 验证签名
            zpay = ZPayManager()
            if not zpay.verify_notify(params):
                print(f"[PAYMENT-NOTIFY] Invalid signature!", file=sys.stderr)
                self._send_response("fail")
                return

            # 3. 检查支付状态
            trade_status = params.get("trade_status")
            if trade_status != "TRADE_SUCCESS":
                print(f"[PAYMENT-NOTIFY] Trade status is not SUCCESS: {trade_status}", file=sys.stderr)
                self._send_response("fail")
                return

            # 4. 提取订单信息
            out_trade_no = params.get("out_trade_no")
            trade_no = params.get("trade_no")
            money = float(params.get("money", "0"))
            param_str = params.get("param", "{}")

            # 解析附加参数
            try:
                param_data = json.loads(param_str)
                user_id = param_data.get("user_id")
                plan_type = param_data.get("plan_type")
            except:
                print(f"[PAYMENT-NOTIFY] Failed to parse param: {param_str}", file=sys.stderr)
                self._send_response("fail")
                return

            print(f"[PAYMENT-NOTIFY] Processing payment for user {user_id}, plan: {plan_type}", file=sys.stderr)

            # 5. 检查订单是否已处理（防止重复通知）
            if self._is_order_processed(out_trade_no):
                print(f"[PAYMENT-NOTIFY] Order already processed: {out_trade_no}", file=sys.stderr)
                self._send_response("success")
                return

            # 6. 创建支付记录
            payment_id = self._create_payment_record(
                user_id=user_id,
                order_id=out_trade_no,
                trade_no=trade_no,
                amount=money,
                plan_type=plan_type,
                payment_method=params.get("type", "alipay")
            )

            if not payment_id:
                print(f"[PAYMENT-NOTIFY] Failed to create payment record", file=sys.stderr)
                self._send_response("fail")
                return

            # 7. 创建订阅并激活会员
            sub_manager = SubscriptionManager()
            result = sub_manager.create_subscription(user_id, plan_type, payment_id)

            if result["success"]:
                print(f"[PAYMENT-NOTIFY] Subscription activated for user {user_id}", file=sys.stderr)
                self._send_response("success")
            else:
                print(f"[PAYMENT-NOTIFY] Failed to create subscription: {result.get('error')}", file=sys.stderr)
                self._send_response("fail")

        except Exception as e:
            print(f"[PAYMENT-NOTIFY] Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self._send_response("fail")

    def _is_order_processed(self, out_trade_no: str) -> bool:
        """检查订单是否已处理"""
        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = client.table("payments").select("*").eq(
                "order_id", out_trade_no
            ).eq("status", "completed").execute()

            return bool(response.data)

        except Exception as e:
            print(f"[PAYMENT-NOTIFY] Error checking order: {e}", file=sys.stderr)
            return False

    def _create_payment_record(
        self,
        user_id: str,
        order_id: str,
        trade_no: str,
        amount: float,
        plan_type: str,
        payment_method: str
    ) -> str:
        """创建支付记录"""
        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)

            payment_data = {
                "user_id": user_id,
                "order_id": order_id,
                "amount": amount,
                "currency": "CNY",
                "payment_method": payment_method,
                "payment_provider": "zpay",
                "status": "completed",
                "item_type": "subscription",
                "item_metadata": json.dumps({
                    "plan_type": plan_type,
                    "trade_no": trade_no
                }),
                "completed_at": "now()"
            }

            response = client.table("payments").insert(payment_data).execute()

            if response.data:
                return response.data[0]["id"]

            return None

        except Exception as e:
            print(f"[PAYMENT-NOTIFY] Error creating payment record: {e}", file=sys.stderr)
            return None

    def _send_response(self, status: str):
        """
        发送响应

        Args:
            status: "success" 或 "fail"
        """
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(status.encode('utf-8'))
