"""
邮箱确认处理页面
GET /api/auth-confirm-email?token=xxx
用于处理Supabase发送的邮箱确认链接
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import sys

try:
    from auth_manager import AuthManager
    from cors_config import get_cors_origin
except ImportError:
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from cors_config import get_cors_origin


class handler(BaseHTTPRequestHandler):
    """邮箱确认处理器"""

    def do_GET(self):
        """处理邮箱确认请求"""
        try:
            # ✅ 安全修复: CORS源白名单验证（虽然是GET，但保持一致性）
            request_origin = self.headers.get('Origin', '')
            self.allowed_origin = get_cors_origin(request_origin)

            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            token = params.get('token', [None])[0]
            type_param = params.get('type', ['signup'])[0]

            if not token:
                self._send_html_error("缺少验证令牌")
                return

            print(f"[AUTH-CONFIRM] Processing email confirmation, type: {type_param}", file=sys.stderr)

            # 2. 调用认证管理器验证邮箱
            auth_manager = AuthManager()
            result = auth_manager.verify_email(token)

            # 3. 返回友好的HTML页面
            if result.get("success"):
                self._send_success_page()
                print(f"[AUTH-CONFIRM] Email confirmed successfully", file=sys.stderr)
            else:
                error_msg = result.get("error", "验证失败")
                self._send_html_error(error_msg)

        except Exception as e:
            print(f"[AUTH-CONFIRM] Error: {e}", file=sys.stderr)
            self._send_html_error(f"服务器错误: {str(e)}")

    def _send_success_page(self):
        """发送成功页面"""
        html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮箱验证成功 - GaiYa每日进度条</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        .icon {
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 1s ease infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 15px;
        }
        p {
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 30px;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            font-size: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .footer {
            margin-top: 30px;
            color: #999;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✅</div>
        <h1>邮箱验证成功！</h1>
        <p>您的邮箱已成功验证。现在可以返回 GaiYa每日进度条 应用并登录您的账号了。</p>
        <p style="font-size: 14px; color: #999;">如果应用未自动刷新，请手动关闭并重新打开应用。</p>
        <div class="footer">
            GaiYa每日进度条 - 让时间可视化
        </div>
    </div>
    <script>
        // 5秒后自动关闭页面
        setTimeout(() => {
            window.close();
        }, 5000);
    </script>
</body>
</html>
"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _send_html_error(self, error_message):
        """发送错误页面"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>验证失败 - GaiYa每日进度条</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}
        .icon {{
            font-size: 80px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #e74c3c;
            font-size: 28px;
            margin-bottom: 15px;
        }}
        p {{
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 30px;
        }}
        .error-detail {{
            background: #fef5f5;
            border: 1px solid #fee;
            border-radius: 10px;
            padding: 15px;
            color: #e74c3c;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .button {{
            display: inline-block;
            background: #e74c3c;
            color: white;
            padding: 15px 40px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            font-size: 16px;
            transition: transform 0.2s;
        }}
        .button:hover {{
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>邮箱验证失败</h1>
        <p>无法完成邮箱验证，请重试或联系客服。</p>
        <div class="error-detail">
            错误详情: {error_message}
        </div>
        <a href="https://jindutiao.vercel.app" class="button">返回首页</a>
    </div>
</body>
</html>
"""
        self.send_response(400)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
