from http.server import BaseHTTPRequestHandler
from pathlib import Path

# 兜底页面，防止静态文件未部署导致 404
DEFAULT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>邮箱验证成功</title>
  <style>
    body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; background:#f7fafc; margin:0; padding:0; display:flex; align-items:center; justify-content:center; min-height:100vh; }
    .card { background:#fff; padding:24px; border-radius:12px; box-shadow:0 12px 30px rgba(0,0,0,.12); width: 420px; max-width: 90%; text-align:center; }
    h1 { margin:0 0 12px; font-size:22px; color:#1a202c; }
    p { margin:0 0 16px; color:#4a5568; }
    .btn { display:inline-block; margin-top:12px; padding:12px 20px; background:#4c51bf; color:#fff; text-decoration:none; border-radius:8px; font-weight:700; }
  </style>
</head>
<body>
  <div class="card">
    <h1>✅ 邮箱验证成功</h1>
    <p>现在可以返回客户端使用邮箱和密码登录。</p>
    <a class="btn" href="#" onclick="window.close(); return false;">关闭页面</a>
  </div>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    """Return email verified page."""

    def do_GET(self):
        try:
            html_path = Path(__file__).resolve().parent.parent / "public" / "email-verified.html"
            if html_path.exists():
                content = html_path.read_text(encoding="utf-8")
            else:
                content = DEFAULT_HTML

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Internal error: {e}".encode("utf-8"))
