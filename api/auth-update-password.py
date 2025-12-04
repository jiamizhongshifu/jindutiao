"""
更新密码API (用于密码重置流程)
POST /api/auth-update-password
Body: {"access_token": "...", "new_password": "..."}
"""
from http.server import BaseHTTPRequestHandler
import json
import sys

try:
    from auth_manager import AuthManager
    from cors_config import get_cors_origin
    from validators_enhanced import validate_password
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from cors_config import get_cors_origin
    from validators_enhanced import validate_password


class handler(BaseHTTPRequestHandler):
    """更新密码处理器"""

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
        """处理更新密码请求"""
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
            access_token = data.get("access_token")
            new_password = data.get("new_password")

            if not access_token:
                self._send_error(400, "Missing access_token")
                return

            if not new_password:
                self._send_error(400, "Missing new_password")
                return

            # ✅ 安全增强: 验证密码强度
            is_valid_password, password_error = validate_password(new_password)
            if not is_valid_password:
                self._send_error(400, password_error)
                print(f"[AUTH-UPDATE-PASSWORD] Invalid password: {password_error}", file=sys.stderr)
                return

            print(f"[AUTH-UPDATE-PASSWORD] Updating password for token: {access_token[:20]}...", file=sys.stderr)

            # 3. 调用认证管理器
            auth_manager = AuthManager()
            result = auth_manager.update_password(access_token, new_password)

            # 4. 返回响应
            if result.get("success"):
                self._send_success(result)
                print(f"[AUTH-UPDATE-PASSWORD] ✅ Password updated successfully", file=sys.stderr)
            else:
                self._send_error(400, result.get("error", "Update failed"))
                print(f"[AUTH-UPDATE-PASSWORD] ⚠️ Password update failed: {result.get('error')}", file=sys.stderr)

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-UPDATE-PASSWORD] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
        self.end_headers()

        response = {"success": True, **data}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
        self.end_headers()

        error_response = {
            "success": False,
            "error": message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
