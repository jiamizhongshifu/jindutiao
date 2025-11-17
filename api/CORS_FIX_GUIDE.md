# CORS安全修复指南

## 问题描述

**当前状态**: 所有API端点使用 `Access-Control-Allow-Origin: *`
**安全风险**: 允许任何域名访问API，可能导致CSRF攻击
**目标**: 限制仅允许可信域名访问

---

## 已完成

✅ **核心模块创建**: `api/cors_config.py`
✅ **参考实现**: `api/auth-signin.py` 已完整修复

---

## 修复步骤（适用于所有API端点）

### 步骤1: 添加导入

在文件顶部的导入部分添加：

```python
# 修改前
try:
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter

# 修复后（添加cors_config导入）
try:
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin  # ✅ 新增
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from rate_limiter import RateLimiter
    from cors_config import get_cors_origin  # ✅ 新增
```

### 步骤2: 修改 do_OPTIONS 方法

```python
# 修改前
def do_OPTIONS(self):
    """处理CORS预检请求"""
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', '*')  # ❌ 不安全
    self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    self.end_headers()

# 修复后
def do_OPTIONS(self):
    """处理CORS预检请求"""
    # ✅ 安全修复: CORS源白名单验证
    request_origin = self.headers.get('Origin', '')
    allowed_origin = get_cors_origin(request_origin)

    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', allowed_origin)  # ✅ 安全
    self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    self.send_header('Access-Control-Max-Age', '3600')  # ✅ 新增：缓存预检请求
    self.end_headers()
```

### 步骤3: 修改 do_POST/do_GET 方法开头

在方法开始的try块中添加：

```python
def do_POST(self):
    """处理请求"""
    try:
        # ✅ 安全修复: CORS源白名单验证（添加在最前面）
        request_origin = self.headers.get('Origin', '')
        self.allowed_origin = get_cors_origin(request_origin)

        # 后续代码...
```

### 步骤4: 修改所有响应头

将所有出现 `Access-Control-Allow-Origin: *` 的地方改为：

```python
# 修改前
self.send_header('Access-Control-Allow-Origin', '*')

# 修复后
self.send_header('Access-Control-Allow-Origin', self.allowed_origin)
```

**注意**: 如果在辅助方法（如 `_send_error`）中使用，且可能在 `allowed_origin` 未设置前被调用，使用：

```python
self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
```

---

## 受影响的文件清单

### 认证端点（高优先级）
- [x] `auth-signin.py` ✅ 已修复（参考实现）
- [ ] `auth-signup.py`
- [ ] `auth-send-otp.py`
- [ ] `auth-verify-otp.py`
- [ ] `auth-reset-password.py`
- [ ] `auth-refresh.py`
- [ ] `auth-signout.py`
- [ ] `auth-confirm-email.py`
- [ ] `auth-check-verification.py`

### 支付端点（高优先级）
- [ ] `payment-create-order.py`
- [ ] `payment-notify.py`
- [ ] `payment-query.py`

### AI功能端点（中优先级）
- [ ] `plan-tasks.py`
- [ ] `generate-weekly-report.py`
- [ ] `chat-query.py`
- [ ] `recommend-theme.py`
- [ ] `generate-theme.py`

### 其他端点（低优先级）
- [ ] `quota-status.py`
- [ ] `subscription-status.py`
- [ ] `styles-list.py`
- [ ] `health.py`

---

## 验证方法

### 开发环境测试

1. **启用开发模式**（允许所有源）:
   ```bash
   export CORS_DEV_MODE=true
   python main.py
   ```

2. **生产模式测试**（仅允许白名单源）:
   ```bash
   # 不设置CORS_DEV_MODE，默认为生产模式
   python main.py
   ```

3. **测试白名单外的源**（应该被拒绝）:
   ```bash
   curl -X POST https://your-api.vercel.app/api/auth-signin \
     -H "Origin: https://malicious-site.com" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"test"}'
   ```

   **预期结果**: 浏览器应拒绝该请求（CORS错误）

4. **测试白名单内的源**（应该成功）:
   ```bash
   curl -X POST https://your-api.vercel.app/api/auth-signin \
     -H "Origin: https://jindutiao.vercel.app" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"test"}'
   ```

   **预期结果**: 正常响应，响应头包含 `Access-Control-Allow-Origin: https://jindutiao.vercel.app`

---

## 配置CORS白名单

如需添加新的允许域名，编辑 `api/cors_config.py`:

```python
ALLOWED_ORIGINS = [
    "https://jindutiao.vercel.app",  # Vercel生产环境
    "https://gaiya.app",             # 自定义域名
    "https://www.gaiya.app",
    "https://new-domain.com",        # ✅ 添加新域名
    "http://localhost:3000",         # 本地开发
]
```

---

## 批量修复建议

对于需要修复的21个端点，建议分批处理：

**第1批（本周）**: 认证和支付端点（12个） - 最关键
**第2批（下周）**: AI功能端点（5个） - 高价值
**第3批（按需）**: 其他端点（4个） - 低优先级

每批修复后立即部署测试，确保无影响。

---

## 常见问题

### Q: 修复后前端无法访问API？

A: 检查以下几点：
1. 前端部署的域名是否在 `ALLOWED_ORIGINS` 白名单中
2. 请求是否包含正确的 `Origin` 头
3. 是否设置了 `CORS_DEV_MODE=true`（仅开发环境）

### Q: 本地开发时如何测试？

A: 方法1（推荐）：设置 `CORS_DEV_MODE=true` 环境变量
方法2：将 `http://localhost:3000` 添加到 `ALLOWED_ORIGINS`

### Q: 如何在Vercel部署中启用开发模式？

A: 不建议在生产环境启用。如果必须，在 Vercel 项目设置 → Environment Variables 中添加：
```
CORS_DEV_MODE=true
```

---

**维护者**: Claude (AI安全审计助手)
**创建日期**: 2025-11-17
**参考实现**: `api/auth-signin.py`
