# HTTP工具函数迁移指南

## ✅ Priority 11: 代码重复提取 (CODE_DEDUPLICATION)

本指南帮助开发者将现有API端点迁移到统一的HTTP工具函数，减少代码重复。

---

## 📋 目标

1. **统一请求解析** - 所有API使用相同的请求体解析逻辑
2. **统一响应格式** - 成功/错误响应使用一致的格式
3. **减少代码重复** - 消除每个文件中的 `_send_success`、`_send_error` 重复代码
4. **提高可维护性** - 修改一处，全局生效

---

## 🛠️ 核心工具函数

### 1. 请求体解析

**旧代码** (每个文件都重复):
```python
def do_POST(self):
    try:
        # 1. 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._send_error(400, "Empty request body")
            return

        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)

        # ... 业务逻辑 ...

    except json.JSONDecodeError:
        self._send_error(400, "Invalid JSON")
    except Exception as e:
        self._send_error(500, f"Internal server error: {str(e)}")
```

**新代码** (使用 `parse_request_body`):
```python
from http_utils import parse_request_body, send_success_response, send_error_response

def do_POST(self):
    # 1. 解析请求体（自动处理错误）
    data, error = parse_request_body(self)
    if error:
        send_error_response(self, 400, error)
        return

    # 2. 业务逻辑（使用 data）
    try:
        # ... 业务逻辑 ...

    except Exception as e:
        send_error_response(self, 500, f"Internal server error: {str(e)}")
```

### 2. 字段验证

**旧代码**:
```python
email = data.get("email")
password = data.get("password")

if not email or not password:
    self._send_error(400, "Missing email or password", rate_info)
    return
```

**新代码**:
```python
from http_utils import validate_required_fields, send_error_response

is_valid, error = validate_required_fields(
    data,
    ["email", "password"],
    {"email": "邮箱", "password": "密码"}  # 可选的中文名称
)
if not is_valid:
    send_error_response(self, 400, error, rate_info)
    return

email = data["email"]
password = data["password"]
```

### 3. 发送成功响应

**旧代码**:
```python
def _send_success(self, data: dict, rate_info: dict = None):
    """发送成功响应（包含速率限制响应头）"""
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.send_header('Access-Control-Allow-Origin', self.allowed_origin)

    # 添加速率限制响应头
    if rate_info:
        self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
        self.send_header('X-RateLimit-Remaining', str(rate_info.get("remaining", 0)))
        self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))

    self.end_headers()

    response = {"success": True, **data}
    self.wfile.write(json.dumps(response).encode('utf-8'))
```

**新代码**:
```python
from http_utils import send_success_response

# 简单！一行搞定
send_success_response(self, {
    "message": "操作成功",
    "user_id": user_id
}, rate_info)
```

### 4. 发送错误响应

**旧代码**:
```python
def _send_error(self, code: int, message: str, rate_info: dict = None):
    """发送错误响应（包含速率限制响应头）"""
    self.send_response(code)
    self.send_header('Content-Type', 'application/json')
    self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))

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

**新代码**:
```python
from http_utils import send_error_response

# 简单！
send_error_response(self, 400, "Missing email", rate_info)

# 带额外详情
send_error_response(self, 401, "Invalid credentials", rate_info, details={
    "attempts_left": 2,
    "locked_until": "2025-01-01T00:00:00Z"
})
```

---

## 🔄 完整迁移示例

### 示例1: auth-signin.py

**迁移前** (150+ 行):
```python
from http.server import BaseHTTPRequestHandler
import json
import sys
from validators import validate_email
from auth_manager import AuthManager
from rate_limiter import RateLimiter

class handler(BaseHTTPRequestHandler):
    allowed_origin = '*'

    def do_POST(self):
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
            password = data.get("password")

            if not email or not password:
                self._send_error(400, "Missing email or password")
                return

            # 3. 邮箱验证
            is_valid_email, email_error = validate_email(email)
            if not is_valid_email:
                self._send_error(400, email_error)
                return

            # 4. 业务逻辑
            auth_manager = AuthManager()
            result = auth_manager.sign_in_with_email(email, password)

            if result["success"]:
                self._send_success(result)
            else:
                self._send_error(401, result.get("error", "Login failed"))

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        # 30+ 行重复代码...
        pass

    def _send_error(self, code: int, message: str):
        # 20+ 行重复代码...
        pass
```

**迁移后** (60+ 行，减少60%):
```python
from http.server import BaseHTTPRequestHandler
from http_utils import (
    parse_request_body,
    validate_required_fields,
    send_success_response,
    send_error_response,
    handle_internal_error
)
from validators import validate_email
from auth_manager import AuthManager
from rate_limiter import RateLimiter

class handler(BaseHTTPRequestHandler):
    allowed_origin = '*'

    def do_POST(self):
        # 1. 解析请求体
        data, error = parse_request_body(self)
        if error:
            send_error_response(self, 400, error)
            return

        # 2. 验证必需字段
        is_valid, error = validate_required_fields(
            data,
            ["email", "password"],
            {"email": "邮箱", "password": "密码"}
        )
        if not is_valid:
            send_error_response(self, 400, error)
            return

        email = data["email"]
        password = data["password"]

        # 3. 邮箱验证
        is_valid_email, email_error = validate_email(email)
        if not is_valid_email:
            send_error_response(self, 400, email_error)
            return

        # 4. 业务逻辑
        try:
            auth_manager = AuthManager()
            result = auth_manager.sign_in_with_email(email, password)

            if result["success"]:
                send_success_response(self, result)
            else:
                send_error_response(self, 401, result.get("error", "Login failed"))

        except Exception as e:
            handle_internal_error(self, e, "processing user login")
```

---

## 🎯 使用 BaseAPIHandler 基类（可选）

如果你希望进一步简化代码，可以继承 `BaseAPIHandler` 基类：

```python
from http_utils import BaseAPIHandler
from validators import validate_email
from auth_manager import AuthManager

class handler(BaseAPIHandler):
    def do_POST(self):
        # 1. 解析请求体（自动处理错误）
        data, error = self.parse_body()
        if error:
            return  # 错误已自动发送

        # 2. 验证字段（自动处理错误）
        is_valid, error = self.validate_fields(
            data,
            ["email", "password"],
            {"email": "邮箱", "password": "密码"}
        )
        if not is_valid:
            return  # 错误已自动发送

        # 3. 业务逻辑
        try:
            auth_manager = AuthManager()
            result = auth_manager.sign_in_with_email(data["email"], data["password"])

            if result["success"]:
                self.send_success(result)  # 使用基类方法
            else:
                self.send_error(401, result.get("error", "Login failed"))

        except Exception as e:
            self.handle_error(e, "processing user login")
```

---

## 📝 迁移清单

对于每个API文件，按以下步骤迁移：

- [ ] 1. 在文件顶部导入 `http_utils` 函数
- [ ] 2. 将请求体解析替换为 `parse_request_body()`
- [ ] 3. 将字段验证替换为 `validate_required_fields()`
- [ ] 4. 删除 `_send_success()` 方法，替换为 `send_success_response()`
- [ ] 5. 删除 `_send_error()` 方法，替换为 `send_error_response()`
- [ ] 6. 将异常处理替换为 `handle_internal_error()`
- [ ] 7. 运行测试验证功能正常
- [ ] 8. 代码审查确认响应格式一致

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **使用关键字参数传递数据**
   ```python
   send_success_response(self, {
       "message": "操作成功",
       "user_id": user_id
   }, rate_info)  # ✅ 好
   ```

2. **错误消息清晰具体**
   ```python
   send_error_response(self, 400, "Missing email", rate_info)  # ✅ 好
   send_error_response(self, 400, "Invalid request")  # ❌ 差（太模糊）
   ```

3. **使用中文字段名提升用户体验**
   ```python
   validate_required_fields(
       data,
       ["email", "password"],
       {"email": "邮箱", "password": "密码"}  # ✅ 好
   )
   ```

4. **统一错误处理**
   ```python
   try:
       # 业务逻辑
   except Exception as e:
       handle_internal_error(self, e, "processing payment")  # ✅ 好
   ```

### ❌ 避免做法

1. **避免混用旧代码和新代码**
2. **避免在多个地方重复验证逻辑**
3. **避免手动构造响应格式**
4. **避免忘记传递 rate_info 参数**

---

## 🧪 测试验证

迁移完成后，运行以下测试验证：

```bash
# 1. 单元测试
python -m pytest tests/unit/test_http_utils.py -v

# 2. API集成测试
python -m pytest tests/integration/ -v

# 3. 手动测试
curl -X POST http://localhost:3000/api/auth-signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123"}'
```

---

## 📊 迁移进度跟踪

| 模块 | 状态 | 代码行数减少 | 负责人 | 备注 |
|------|------|------------|-------|------|
| http_utils.py | ✅ 已完成 | - | Claude | 核心模块 |
| auth-signin.py | ⏳ 待迁移 | 预计 -60 行 | - | 示例文件 |
| auth-signup.py | ⏳ 待迁移 | 预计 -55 行 | - | |
| auth-send-otp.py | ⏳ 待迁移 | 预计 -50 行 | - | |
| payment-create-order.py | ⏳ 待迁移 | 预计 -45 行 | - | |
| ... | | | | |

**预计总收益**:
- 减少代码行数：~1000+ 行（27个文件 × 平均40行/文件）
- 提高可维护性：修改一处，全局生效
- 统一响应格式：更好的API一致性

---

## 🔗 相关文档

- **核心模块**: `api/http_utils.py`
- **单元测试**: `tests/unit/test_http_utils.py`
- **验证工具**: `api/validators.py`
- **日志工具**: `api/logger_util.py`
- **安全审计报告**: `SECURITY_FIX_PROGRESS.md` (Priority 11)

---

**维护者**: Claude (AI安全审计助手)
**创建日期**: 2025-11-17
**版本**: 1.0
