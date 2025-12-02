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
    from validators_enhanced import validate_user_id, validate_plan_type, validate_payment_amount
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from zpay_manager import ZPayManager
    from subscription_manager import SubscriptionManager
    from validators_enhanced import validate_user_id, validate_plan_type, validate_payment_amount
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin


class handler(BaseHTTPRequestHandler):
    """创建支付订单处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()

    def do_POST(self):
        """处理创建订单请求"""
        try:
            # ✅ 安全修复: CORS源白名单验证
            request_origin = self.headers.get('Origin', '')
            self.allowed_origin = get_cors_origin(request_origin)

            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 2. ✅ 安全验证：使用validators_enhanced模块
            user_id = data.get("user_id")
            plan_type = data.get("plan_type")
            pay_type = data.get("pay_type", "alipay")  # 默认支付宝

            # ✅ 安全增强：验证UUID格式的user_id（Supabase Auth使用UUID）
            is_valid, error_msg = validate_user_id(user_id, require_uuid=True)
            if not is_valid:
                self._send_error(400, error_msg)
                print(f"[PAYMENT-CREATE] Invalid user_id format: {user_id}", file=sys.stderr)
                return

            # ✅ 安全修复: 速率限制检查（防止订单创建滥用）
            limiter = RateLimiter()

            # 检查速率限制 (10次/1小时，基于user_id)
            is_allowed, rate_info = limiter.check_rate_limit("payment_create_order", user_id)

            if not is_allowed:
                # 返回429 Too Many Requests
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', self.allowed_origin)
                self.send_header('Retry-After', str(rate_info.get("retry_after", 60)))
                self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
                self.send_header('X-RateLimit-Remaining', '0')
                self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))
                self.end_headers()

                error_response = {
                    "success": False,
                    "error": "Too many payment order requests. Please try again later.",
                    "retry_after": rate_info.get("retry_after", 60)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                print(f"[PAYMENT-CREATE] 🚫 Rate limit exceeded for user: {user_id}", file=sys.stderr)
                return

            # 验证plan_type并获取正确价格
            is_valid, error_msg, correct_price = validate_plan_type(plan_type)
            if not is_valid:
                self._send_error(400, error_msg, rate_info)
                return

            # ✅ 安全：验证支付方式
            if pay_type not in ["alipay", "wxpay"]:
                self._send_error(400, "Invalid pay_type", rate_info)
                return

            print(f"[PAYMENT-CREATE] User {user_id} requesting {plan_type} (¥{correct_price}) via {pay_type}", file=sys.stderr)

            # 3. 获取计划信息（现在价格已经从validators获取，确保一致）
            zpay = ZPayManager()
            plan_info = zpay.get_plan_info(plan_type)

            # ✅ 双重验证：确保price与validators的价格一致
            if abs(plan_info["price"] - correct_price) > 0.01:
                print(f"[SECURITY] Price mismatch detected for {plan_type}", file=sys.stderr)
                self._send_error(500, "Internal price configuration error", rate_info)
                return

            # 4. 生成唯一订单号
            out_trade_no = self._generate_order_no(user_id)

            # 5. 构建回调URL
            # 注意：这里需要替换为实际的域名
            base_url = "https://jindutiao.vercel.app"  # 或从环境变量获取
            notify_url = f"{base_url}/api/payment-notify"

            # 6. 获取客户端IP地址 (用于API方式创建订单)
            # 优先从X-Forwarded-For获取真实IP (Vercel会自动设置)
            client_ip = self.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            if not client_ip:
                client_ip = self.headers.get('X-Real-IP', '')
            if not client_ip:
                client_ip = self.client_address[0]  # 回退到直连IP

            # 7. 创建支付订单 (使用API方式 mapi.php 而非页面跳转方式 submit.php)
            # ✅ 关键修复: API方式更可靠,回调通知成功率更高
            result = zpay.create_api_order(
                out_trade_no=out_trade_no,
                name=plan_info["name"],
                money=plan_info["price"],
                pay_type=pay_type,
                notify_url=notify_url,
                clientip=client_ip,
                param=json.dumps({
                    "user_id": user_id,
                    "plan_type": plan_type
                })  # 附加参数，用于回调时识别用户和套餐
            )

            if result["success"]:
                # 8. 返回支付信息（包含速率限制信息）
                # ⚠️ API方式返回 payurl 而非 payment_url
                self._send_success({
                    "success": True,
                    "payment_url": result["payurl"],  # API方式使用payurl
                    "qrcode": result.get("qrcode", ""),  # 二维码链接
                    "out_trade_no": out_trade_no,
                    "amount": plan_info["price"],
                    "plan_name": plan_info["name"]
                }, rate_info)

                print(f"[PAYMENT-CREATE] Order created: {out_trade_no}", file=sys.stderr)
            else:
                self._send_error(500, result.get("error", "Failed to create order"), rate_info)

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
        user_hash = hashlib.md5(user_id.encode(), usedforsecurity=False).hexdigest()[:6]
        return f"GAIYA{timestamp}{user_hash}"

    def _send_success(self, data: dict, rate_info: dict = None):
        """发送成功响应（包含速率限制响应头）"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', self.allowed_origin)

        # ✅ 添加速率限制响应头
        if rate_info:
            self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            self.send_header('X-RateLimit-Remaining', str(rate_info.get("remaining", 0)))
            self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))

        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, code: int, message: str, rate_info: dict = None):
        """发送错误响应（包含速率限制响应头）"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))

        # ✅ 添加速率限制响应头
        if rate_info:
            self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            self.send_header('X-RateLimit-Remaining', str(rate_info.get("remaining", 0)))
            self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))

        self.end_headers()

        error_response = {
            "success": False,
            "error": message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
