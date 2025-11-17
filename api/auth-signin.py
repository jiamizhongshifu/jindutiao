"""
用户登录API
POST /api/auth-signin
"""
from http.server import BaseHTTPRequestHandler
import json
import sys

# 导入认证管理器和安全模块
try:
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin
except ImportError:
    # Vercel环境可能需要不同的导入路径
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin


class handler(BaseHTTPRequestHandler):
    """登录API处理器"""

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
        """处理登录请求"""
        try:
            # ✅ 安全修复: CORS源白名单验证
            request_origin = self.headers.get('Origin', '')
            self.allowed_origin = get_cors_origin(request_origin)

            # ✅ 安全修复: 速率限制检查（防止暴力破解）
            limiter = RateLimiter()

            # 获取客户端IP
            client_ip = self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not client_ip:
                client_ip = self.client_address[0] if self.client_address else "unknown"

            # 检查速率限制
            is_allowed, rate_info = limiter.check_rate_limit("auth_signin", client_ip)

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
                    "error": "Too many login attempts. Please try again later.",
                    "retry_after": rate_info.get("retry_after", 60)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                print(f"[AUTH-SIGNIN] 🚫 Rate limit exceeded for IP: {client_ip}", file=sys.stderr)
                return

            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 2. 验证参数
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                self._send_error(400, "Missing email or password")
                return

            print(f"[AUTH-SIGNIN] Login attempt for: {email} from IP: {client_ip}", file=sys.stderr)

            # 3. 调用认证管理器
            auth_manager = AuthManager()
            result = auth_manager.sign_in_with_email(email, password)

            # 4. 返回响应（包含速率限制信息）
            if result["success"]:
                self._send_success(result, rate_info)
                print(f"[AUTH-SIGNIN] Login successful: {email}", file=sys.stderr)
            else:
                self._send_error(401, result.get("error", "Login failed"), rate_info)

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-SIGNIN] Error: {e}", file=sys.stderr)
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
