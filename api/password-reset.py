from http.server import BaseHTTPRequestHandler
from pathlib import Path

# 内置一个兜底的重置密码页面，防止静态文件未被打包导致 404
DEFAULT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>重置密码</title>
  <style>
    body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; background:#f7fafc; margin:0; padding:0; display:flex; align-items:center; justify-content:center; min-height:100vh; }
    .card { background:#fff; padding:24px; border-radius:12px; box-shadow:0 12px 30px rgba(0,0,0,.12); width: 420px; max-width: 90%; }
    h1 { margin:0 0 12px; font-size:22px; color:#1a202c; }
    p { margin:0 0 16px; color:#4a5568; }
    label { display:block; margin:12px 0 6px; font-weight:600; color:#2d3748; }
    input { width:100%; padding:10px 12px; border:1px solid #e2e8f0; border-radius:8px; font-size:15px; }
    button { width:100%; margin-top:16px; padding:12px; background:#4c51bf; color:#fff; border:none; border-radius:8px; font-weight:700; cursor:pointer; }
    .error { background:#fff5f5; color:#c53030; padding:10px 12px; border-radius:8px; margin-bottom:10px; display:none; }
    .success { background:#f0fff4; color:#2f855a; padding:10px 12px; border-radius:8px; margin-bottom:10px; display:none; }
  </style>
</head>
<body>
  <div class="card">
    <h1>重置密码</h1>
    <p>请设置新的密码。</p>
    <div id="error" class="error"></div>
    <div id="success" class="success"></div>
    <div class="requirements">
      <strong>密码要求：</strong>
      <ul>
        <li>长度 8-128 位</li>
        <li>必须包含大写字母、小写字母、数字</li>
      </ul>
    </div>
    <label for="password">新密码</label>
    <input id="password" type="password" placeholder="至少 8 位，含大写/小写/数字" />
    <label for="confirm">确认新密码</label>
    <input id="confirm" type="password" placeholder="再次输入新密码" />
    <button id="submit">提交</button>
  </div>
  <script>
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const token = params.get('access_token');
    const type = params.get('type');

    const err = document.getElementById('error');
    const ok = document.getElementById('success');
    const submit = document.getElementById('submit');

    function showError(msg){ err.textContent = msg; err.style.display='block'; ok.style.display='none'; }
    function showSuccess(msg){ ok.textContent = msg; ok.style.display='block'; err.style.display='none'; }

    if (!token || type !== 'recovery') {
      showError('无效或已过期的重置链接，请重新申请重置密码。');
      submit.disabled = true;
    }

    function validatePassword(p1, p2, silent=false) {
      const hasUpper = /[A-Z]/.test(p1);
      const hasLower = /[a-z]/.test(p1);
      const hasDigit = /[0-9]/.test(p1);
      if (p1.length < 8 || p1.length > 128 || !hasUpper || !hasLower || !hasDigit) {
        if (!silent) showError('密码需 8-128 位，且包含大写、小写、数字');
        return false;
      }
      if (p1 !== p2) { if (!silent) showError('两次输入的密码不一致'); return false; }
      if (!silent) { err.style.display='none'; }
      return true;
    }

    document.getElementById('password').addEventListener('input', () => {
      const p1 = document.getElementById('password').value;
      const p2 = document.getElementById('confirm').value;
      validatePassword(p1, p2, true);
    });

    submit.addEventListener('click', async () => {
      const p1 = document.getElementById('password').value;
      const p2 = document.getElementById('confirm').value;
      if (!validatePassword(p1, p2)) return;

      submit.disabled = true;
      try {
        const resp = await fetch('/api/auth-update-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_token: token, new_password: p1 })
        });
        const result = await resp.json();
        if (result.success) {
          showSuccess('密码重置成功，请返回客户端登录。');
        } else {
          showError(result.error || '重置失败，请重试');
        }
      } catch (e) {
        showError('网络错误：' + e.message);
      } finally {
        submit.disabled = false;
      }
    });
  </script>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    """Return the password reset page for Supabase redirect."""

    def do_GET(self):
        try:
            html_path = Path(__file__).resolve().parent.parent / "public" / "password-reset.html"
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
