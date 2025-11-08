"""
创建支付订单API
POST /api/payment-create-order
Body: {
    "user_id": "xxx",
    "plan_type": "pro_monthly" | "pro_yearly" | "lifetime",
    "pay_type": "alipay" | "wxpay"
}
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import time

try:
    from zpay_manager import ZPayManager
    from subscription_manager import SubscriptionManager
    from validators import validate_user_id, validate_plan_type, validate_payment_amount
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from zpay_manager import ZPayManager
    from subscription_manager import SubscriptionManager
    from validators import validate_user_id, validate_plan_type, validate_payment_amount


class handler(BaseHTTPRequestHandler):
    """创建支付订单处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理创建订单请求"""
        try:
            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 2. ✅ 安全验证：使用validators模块
            user_id = data.get("user_id")
            plan_type = data.get("plan_type")
            pay_type = data.get("pay_type", "alipay")  # 默认支付宝

            # 验证user_id
            is_valid, error_msg = validate_user_id(user_id)
            if not is_valid:
                self._send_error(400, error_msg)
                return

            # 验证plan_type并获取正确价格
            is_valid, error_msg, correct_price = validate_plan_type(plan_type)
            if not is_valid:
                self._send_error(400, error_msg)
                return

            # ✅ 安全：验证支付方式
            if pay_type not in ["alipay", "wxpay"]:
                self._send_error(400, "Invalid pay_type")
                return

            print(f"[PAYMENT-CREATE] User {user_id} requesting {plan_type} (¥{correct_price}) via {pay_type}", file=sys.stderr)

            # 3. 获取计划信息（现在价格已经从validators获取，确保一致）
            zpay = ZPayManager()
            plan_info = zpay.get_plan_info(plan_type)

            # ✅ 双重验证：确保price与validators的价格一致
            if abs(plan_info["price"] - correct_price) > 0.01:
                print(f"[SECURITY] Price mismatch detected for {plan_type}", file=sys.stderr)
                self._send_error(500, "Internal price configuration error")
                return

            # 4. 生成唯一订单号
            out_trade_no = self._generate_order_no(user_id)

            # 5. 构建回调URL
            # 注意：这里需要替换为实际的域名
            base_url = "https://jindutiao.vercel.app"  # 或从环境变量获取
            notify_url = f"{base_url}/api/payment-notify"
            return_url = f"gaiya://payment-success?out_trade_no={out_trade_no}"

            # 6. 创建支付订单
            # 注意：不指定cid，让ZPAY自动选择可用渠道
            # 如果遇到特定渠道问题，ZPAY会自动切换到其他可用渠道
            result = zpay.create_order(
                out_trade_no=out_trade_no,
                name=plan_info["name"],
                money=plan_info["price"],
                pay_type=pay_type,
                notify_url=notify_url,
                return_url=return_url,
                param=json.dumps({
                    "user_id": user_id,
                    "plan_type": plan_type
                })  # 附加参数，用于回调时识别用户和套餐
            )

            if result["success"]:
                # 7. 返回支付信息
                self._send_success({
                    "success": True,
                    "payment_url": result["payment_url"],
                    "params": result["params"],
                    "out_trade_no": out_trade_no,
                    "amount": plan_info["price"],
                    "plan_name": plan_info["name"]
                })

                print(f"[PAYMENT-CREATE] Order created: {out_trade_no}", file=sys.stderr)
            else:
                self._send_error(500, result.get("error", "Failed to create order"))

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[PAYMENT-CREATE] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _generate_order_no(self, user_id: str) -> str:
        """
        生成唯一订单号

        格式: GAIYA{timestamp}{user_id_hash}
        """
        import hashlib
        timestamp = str(int(time.time() * 1000))  # 毫秒时间戳
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:6]
        return f"GAIYA{timestamp}{user_hash}"

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        error_response = {
            "success": False,
            "error": message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
