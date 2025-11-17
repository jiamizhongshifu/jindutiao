"""
发送OTP验证码
POST /api/auth-send-otp
用于桌面应用的邮箱验证（发送6位数字验证码）
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import random
import os
from datetime import datetime, timedelta

try:
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin

# 简单的内存存储(生产环境应使用Redis或数据库)
OTP_STORE = {}


class handler(BaseHTTPRequestHandler):
    """OTP发送处理器"""

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
        """处理OTP发送请求"""
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
            purpose = data.get("purpose", "signup")  # signup, password_reset

            if not email:
                self._send_error(400, "Missing email")
                return

            # ✅ 安全修复: 速率限制检查（防止短信/邮件轰炸）
            limiter = RateLimiter()

            # 检查速率限制 (3次/1小时，基于email)
            is_allowed, rate_info = limiter.check_rate_limit("auth_send_otp", email)

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
                    "error": "Too many OTP requests. Please try again later.",
                    "retry_after": rate_info.get("retry_after", 60)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                print(f"[AUTH-OTP] 🚫 Rate limit exceeded for email: {email}", file=sys.stderr)
                return

            print(f"[AUTH-OTP] Sending OTP to: {email}, purpose: {purpose}", file=sys.stderr)

            # 3. 生成6位数字OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = datetime.now() + timedelta(minutes=10)  # 10分钟有效期

            # 4. 存储OTP到数据库
            auth_manager = AuthManager()
            store_result = auth_manager.store_otp(email, otp_code, purpose, expires_at.isoformat())

            if not store_result.get("success"):
                self._send_error(500, f"存储验证码失败: {store_result.get('error')}")
                return

            # 5. 发送邮件(使用Resend邮件服务)
            result = auth_manager.send_otp_email(email, otp_code, purpose)

            if result.get("success"):
                self._send_success({
                    "message": result.get("message", "验证码已发送到您的邮箱"),
                    "expires_in": 600  # 秒
                }, rate_info)
                print(f"[AUTH-OTP] OTP sent successfully to {email}", file=sys.stderr)
            else:
                self._send_error(500, result.get("error", "Failed to send OTP"), rate_info)

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-OTP] Error: {e}", file=sys.stderr)
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
