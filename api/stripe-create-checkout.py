"""
创建Stripe Checkout Session API
POST /api/stripe-create-checkout
Body: {
    "user_id": "xxx",
    "user_email": "xxx@example.com",
    "plan_type": "pro_monthly" | "pro_yearly" | "lifetime"
}
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

try:
    from stripe_manager import StripeManager
    from validators_enhanced import validate_user_id, validate_plan_type
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from stripe_manager import StripeManager
    from validators_enhanced import validate_user_id, validate_plan_type
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin


class handler(BaseHTTPRequestHandler):
    """创建Stripe Checkout Session处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()

    def do_POST(self):
        """处理创建Checkout Session请求"""
        try:
            # CORS配置
            request_origin = self.headers.get('Origin', '')
            self.allowed_origin = get_cors_origin(request_origin)

            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 2. 验证参数
            user_id = data.get("user_id")
            user_email = data.get("user_email")
            plan_type = data.get("plan_type")

            # 验证user_id格式
            is_valid, error_msg = validate_user_id(user_id, require_uuid=True)
            if not is_valid:
                self._send_error(400, error_msg)
                print(f"[STRIPE-CHECKOUT] Invalid user_id format: {user_id}", file=sys.stderr)
                return

            # 验证email
            if not user_email or '@' not in user_email:
                self._send_error(400, "Invalid email address")
                return

            # 验证plan_type
            is_valid, error_msg, _ = validate_plan_type(plan_type)
            if not is_valid:
                self._send_error(400, error_msg)
                return

            # 3. 速率限制检查
            limiter = RateLimiter()
            is_allowed, rate_info = limiter.check_rate_limit("stripe_checkout", user_id)

            if not is_allowed:
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', self.allowed_origin)
                self.send_header('Retry-After', str(rate_info.get("retry_after", 60)))
                self.end_headers()

                error_response = {
                    "success": False,
                    "error": "Too many checkout requests. Please try again later.",
                    "retry_after": rate_info.get("retry_after", 60)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                print(f"[STRIPE-CHECKOUT] Rate limit exceeded for user: {user_id}", file=sys.stderr)
                return

            print(f"[STRIPE-CHECKOUT] User {user_id} requesting {plan_type}", file=sys.stderr)

            # 4. 创建Stripe Checkout Session
            stripe_manager = StripeManager()

            # 构建回调URL
            base_url = os.getenv("STRIPE_SUCCESS_URL", "https://jindutiao.vercel.app")
            success_url = f"{base_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{base_url}/payment-cancel"

            result = stripe_manager.create_checkout_session(
                plan_type=plan_type,
                user_email=user_email,
                user_id=user_id,
                success_url=success_url,
                cancel_url=cancel_url
            )

            if result["success"]:
                # 5. 返回Checkout Session信息
                response_data = {
                    "success": True,
                    "session_id": result["session_id"],
                    "checkout_url": result["checkout_url"],
                    "plan_type": plan_type
                }

                # 获取计划信息
                plan_info = stripe_manager.get_plan_info(plan_type)
                if plan_info["success"]:
                    response_data["plan_name"] = plan_info["plan"]["name"]
                    response_data["amount"] = plan_info["plan"]["price"]
                    response_data["currency"] = plan_info["plan"]["currency"]

                self._send_success(response_data, rate_info)
                print(f"[STRIPE-CHECKOUT] Session created: {result['session_id']}", file=sys.stderr)
            else:
                self._send_error(500, result.get("error", "Failed to create checkout session"), rate_info)

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[STRIPE-CHECKOUT] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict, rate_info: dict = None):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', self.allowed_origin)

        if rate_info:
            self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            self.send_header('X-RateLimit-Remaining', str(rate_info.get("remaining", 0)))
            self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))

        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, code: int, message: str, rate_info: dict = None):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))

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
