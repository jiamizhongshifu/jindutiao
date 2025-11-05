"""
刷新访问令牌API
POST /api/auth-refresh
Body: {"refresh_token": "xxx"}
"""
from http.server import BaseHTTPRequestHandler
import json
import sys

try:
    from auth_manager import AuthManager
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager


class handler(BaseHTTPRequestHandler):
    """刷新Token处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理刷新Token请求"""
        try:
            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 2. 验证参数
            refresh_token = data.get("refresh_token")

            if not refresh_token:
                self._send_error(400, "Missing refresh_token")
                return

            print(f"[AUTH-REFRESH] Refresh token request received", file=sys.stderr)

            # 3. 调用认证管理器
            auth_manager = AuthManager()
            result = auth_manager.refresh_access_token(refresh_token)

            # 4. 返回响应
            if result["success"]:
                self._send_success({
                    "success": True,
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"]
                })
                print(f"[AUTH-REFRESH] Token refreshed successfully", file=sys.stderr)
            else:
                self._send_error(401, result.get("error", "Token refresh failed"))

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-REFRESH] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

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
