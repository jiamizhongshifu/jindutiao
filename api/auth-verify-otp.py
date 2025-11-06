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
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from auth_send_otp import OTP_STORE


class handler(BaseHTTPRequestHandler):
    """OTP验证处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理OTP验证请求"""
        try:
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

            print(f"[AUTH-VERIFY-OTP] Verifying OTP for: {email}", file=sys.stderr)

            # 3. 从存储中获取OTP
            stored_otp = OTP_STORE.get(email)

            if not stored_otp:
                self._send_error(400, "验证码不存在或已过期")
                return

            # 4. 检查过期时间
            expires_at = datetime.fromisoformat(stored_otp["expires_at"])
            if datetime.now() > expires_at:
                del OTP_STORE[email]
                self._send_error(400, "验证码已过期")
                return

            # 5. 检查尝试次数(防止暴力破解)
            if stored_otp["attempts"] >= 5:
                del OTP_STORE[email]
                self._send_error(429, "验证尝试次数过多，请重新获取验证码")
                return

            # 6. 验证OTP
            if stored_otp["code"] != otp_code:
                stored_otp["attempts"] += 1
                remaining = 5 - stored_otp["attempts"]
                self._send_error(400, f"验证码错误，还剩{remaining}次机会")
                return

            # 7. 验证成功，更新数据库
            auth_manager = AuthManager()

            # 根据purpose执行不同操作
            if stored_otp["purpose"] == "signup":
                # 标记邮箱为已验证
                result = auth_manager.mark_email_verified(email)
            elif stored_otp["purpose"] == "password_reset":
                # 允许重置密码(返回临时token)
                result = {"success": True, "allow_reset": True}
            else:
                result = {"success": True}

            # 8. 清除已使用的OTP
            del OTP_STORE[email]

            if result.get("success"):
                self._send_success({
                    "message": "验证成功",
                    "purpose": stored_otp["purpose"]
                })
                print(f"[AUTH-VERIFY-OTP] OTP verified successfully for: {email}", file=sys.stderr)
            else:
                self._send_error(500, result.get("error", "验证失败"))

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-VERIFY-OTP] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {"success": True, **data}
        self.wfile.write(json.dumps(response).encode('utf-8'))

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
