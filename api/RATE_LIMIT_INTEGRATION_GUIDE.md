# API速率限制集成指南

## 概述

速率限制器已实现，用于防止API滥用、暴力破解攻击和资源耗尽。本指南说明如何在其他API端点中集成速率限制功能。

## 架构

- **存储**: Supabase `rate_limits` 表
- **核心模块**: `api/rate_limiter.py`
- **已集成端点**: `auth-signin.py` (示例)

## 速率限制规则配置

当前配置的规则（在 `rate_limiter.py` 中）:

| 端点标识符 | 最大请求数 | 时间窗口 | 限制键类型 | 说明 |
|-----------|----------|---------|-----------|------|
| `auth_signin` | 5 | 60秒 | IP | 防止暴力破解 |
| `auth_signup` | 3 | 5分钟 | IP | 防止批量注册 |
| `auth_send_otp` | 3 | 1小时 | Email | 防止短信/邮件轰炸 |
| `auth_verify_otp` | 5 | 5分钟 | Email | 防止OTP暴力破解 |
| `auth_reset_password` | 3 | 1小时 | IP | 防止密码重置滥用 |
| `payment_create_order` | 10 | 1小时 | User ID | 防止订单创建滥用 |
| `plan_tasks` | 20 | 24小时 | User ID | 防止AI资源滥用 |
| `generate_weekly_report` | 10 | 24小时 | User ID | 防止AI资源滥用 |
| `chat_query` | 50 | 1小时 | User ID | 防止对话API滥用 |

## 集成步骤

### 1. 导入RateLimiter模块

在API端点文件顶部添加导入：

```python
try:
    from rate_limiter import RateLimiter
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from rate_limiter import RateLimiter
```

### 2. 在do_POST/do_GET方法开始处添加速率限制检查

#### 对于基于IP的限制（登录、注册等）:

```python
def do_POST(self):
    """处理请求"""
    try:
        # ✅ 速率限制检查
        limiter = RateLimiter()

        # 获取客户端IP
        client_ip = self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = self.client_address[0] if self.client_address else "unknown"

        # 检查速率限制（使用对应的endpoint标识符）
        is_allowed, rate_info = limiter.check_rate_limit("auth_signup", client_ip)

        if not is_allowed:
            # 返回429 Too Many Requests
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Retry-After', str(rate_info.get("retry_after", 60)))
            self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            self.send_header('X-RateLimit-Remaining', '0')
            self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))
            self.end_headers()

            error_response = {
                "success": False,
                "error": "Too many requests. Please try again later.",
                "retry_after": rate_info.get("retry_after", 60)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
            return

        # ... 后续正常请求处理逻辑
```

#### 对于基于User ID的限制（AI功能、支付等）:

```python
def do_POST(self):
    """处理请求"""
    try:
        # 1. 先读取请求参数获取user_id
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)

        user_id = data.get("user_id")
        if not user_id:
            self._send_error(400, "Missing user_id")
            return

        # ✅ 速率限制检查（基于user_id）
        limiter = RateLimiter()
        is_allowed, rate_info = limiter.check_rate_limit("plan_tasks", user_id)

        if not is_allowed:
            # 返回429 Too Many Requests
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Retry-After', str(rate_info.get("retry_after", 60)))
            self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            self.send_header('X-RateLimit-Remaining', '0')
            self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))
            self.end_headers()

            error_response = {
                "success": False,
                "error": "Daily AI quota exceeded. Please try again tomorrow.",
                "retry_after": rate_info.get("retry_after", 60)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
            return

        # ... 后续正常请求处理逻辑
```

#### 对于基于Email的限制（OTP发送）:

```python
def do_POST(self):
    """处理请求"""
    try:
        # 1. 先读取请求参数获取email
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)

        email = data.get("email")
        if not email:
            self._send_error(400, "Missing email")
            return

        # ✅ 速率限制检查（基于email）
        limiter = RateLimiter()
        is_allowed, rate_info = limiter.check_rate_limit("auth_send_otp", email)

        if not is_allowed:
            # 返回429 Too Many Requests
            # ... （同上）
```

### 3. 修改响应方法以包含速率限制响应头

更新 `_send_success` 和 `_send_error` 方法：

```python
def _send_success(self, data: dict, rate_info: dict = None):
    """发送成功响应（包含速率限制响应头）"""
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.send_header('Access-Control-Allow-Origin', '*')

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
    self.send_header('Access-Control-Allow-Origin', '*')

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
```

### 4. 更新调用响应方法时传入rate_info

```python
# 成功时
self._send_success(result, rate_info)

# 错误时
self._send_error(401, "Authentication failed", rate_info)
```

## 优先级建议

根据安全审计报告，建议按以下优先级应用速率限制：

### 🔴 第一优先级（本周必须）:
1. ✅ `auth-signin.py` - 已完成
2. ⏳ `auth-signup.py` - 防止批量注册
3. ⏳ `auth-send-otp.py` - 防止短信轰炸
4. ⏳ `payment-create-order.py` - 防止订单滥用

### 🟠 第二优先级（下周）:
5. ⏳ `auth-verify-otp.py`
6. ⏳ `auth-reset-password.py`
7. ⏳ `plan-tasks.py`
8. ⏳ `generate-weekly-report.py`

### 🟡 第三优先级（按需）:
9. ⏳ `chat-query.py`
10. ⏳ 其他AI功能端点

## 数据库设置

### 1. 创建rate_limits表

在Supabase SQL Editor中执行 `rate_limits_table.sql`:

```sql
-- 见 rate_limits_table.sql 文件
```

### 2. 配置自动清理（可选）

使用Vercel Cron Jobs或Supabase定时任务定期清理过期记录：

```python
# 创建一个单独的清理端点
# api/cleanup-rate-limits.py

from rate_limiter import RateLimiter

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        limiter = RateLimiter()
        limiter.cleanup_expired_records(hours=24)
        # 返回成功响应
```

然后在 `vercel.json` 中配置：

```json
{
  "crons": [{
    "path": "/api/cleanup-rate-limits",
    "schedule": "0 */6 * * *"  // 每6小时执行一次
  }]
}
```

## 响应头说明

客户端可以使用以下响应头来实现友好的用户体验：

- `X-RateLimit-Limit`: 总请求限制数
- `X-RateLimit-Remaining`: 剩余请求数
- `X-RateLimit-Reset`: 限制重置的ISO 8601时间戳
- `Retry-After`: （仅在429响应时）建议重试的秒数

## 错误处理

速率限制器采用**安全降级**策略：

- ✅ Supabase未配置时：允许请求，记录警告日志
- ✅ 查询失败时：允许请求，记录错误日志
- ✅ 端点未配置规则时：允许请求，记录警告日志

这确保速率限制不会成为系统的单点故障。

## 调整速率限制规则

修改 `rate_limiter.py` 中的 `RATE_LIMITS` 字典：

```python
RATE_LIMITS = {
    "your_endpoint": {
        "max_requests": 10,        # 最大请求数
        "window_seconds": 3600,    # 时间窗口（秒）
        "key_type": "ip"           # "ip", "user_id", 或 "email"
    }
}
```

## 测试建议

1. **单元测试**: 测试速率限制逻辑
2. **集成测试**: 测试端点是否正确返回429
3. **负载测试**: 验证高并发场景下的性能
4. **安全测试**: 验证是否成功阻止暴力破解

## 监控建议

在生产环境中，建议监控：

- 429响应的频率（过高可能说明正常用户受影响）
- rate_limits表的增长速度
- Supabase查询性能
- 客户端重试行为

## 注意事项

1. **IP获取**: Vercel环境中使用 `X-Forwarded-For` 头获取真实IP
2. **时区**: 所有时间戳使用UTC
3. **隐私保护**: identifier被哈希处理，保护用户隐私
4. **清理策略**: 建议保留24小时内的记录
5. **用户体验**: 提供清晰的错误消息和重试时间
