"""
验证OTP验证码
POST /api/auth-verify-otp
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime

try:
    from auth_manager import AuthManager
    from auth_send_otp import OTP_STORE  # 导入OTP存储(生产环境用Redis)
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from auth_send_otp import OTP_STORE
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin


class handler(BaseHTTPRequestHandler):
    """OTP验证处理器"""

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
        """处理OTP验证请求"""
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

            # 2. 验证参数
            email = data.get("email")
            otp_code = data.get("otp_code")

            if not email or not otp_code:
                self._send_error(400, "Missing email or otp_code")
                return

            # ✅ 安全修复: 速率限制检查（防止OTP暴力破解）
            limiter = RateLimiter()

            # 检查速率限制 (5次/5分钟，基于email)
            is_allowed, rate_info = limiter.check_rate_limit("auth_verify_otp", email)

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
                    "error": "Too many OTP verification attempts. Please try again later.",
                    "retry_after": rate_info.get("retry_after", 60)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                print(f"[AUTH-VERIFY-OTP] 🚫 Rate limit exceeded for email: {email}", file=sys.stderr)
                return

            print(f"[AUTH-VERIFY-OTP] Verifying OTP for: {email}", file=sys.stderr)

            # 3. 使用 auth_manager 验证 OTP（从数据库）
            auth_manager = AuthManager()
            verify_result = auth_manager.verify_otp(email, otp_code)

            if not verify_result.get("success"):
                self._send_error(400, verify_result.get("error", "验证失败"), rate_info)
                return

            # 4. 验证成功，根据purpose执行不同操作
            purpose = verify_result.get("purpose", "signup")

            if purpose == "signup":
                # 标记邮箱为已验证
                mark_result = auth_manager.mark_email_verified(email)
                if not mark_result.get("success"):
                    print(f"[AUTH-VERIFY-OTP] Warning: Failed to mark email verified: {mark_result.get('error')}", file=sys.stderr)
                    # 不影响验证成功的结果，只记录警告

            # 5. 返回成功
            self._send_success({
                "message": "验证成功",
                "purpose": purpose
            }, rate_info)
            print(f"[AUTH-VERIFY-OTP] OTP verified successfully for: {email}", file=sys.stderr)

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-VERIFY-OTP] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

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

        response = {"success": True, **data}
        self.wfile.write(json.dumps(response).encode('utf-8'))

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
