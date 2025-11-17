# 日志规范化迁移指南

## ✅ Priority 10: 日志规范化 (LOG_STANDARDIZATION)

本指南帮助开发者将现有的print日志迁移到统一的日志规范系统。

---

## 📋 目标

1. **统一日志格式** - 所有日志使用相同的时间戳、级别、模块名格式
2. **敏感信息脱敏** - 自动脱敏邮箱、IP、Token等敏感数据
3. **日志级别控制** - 支持DEBUG/INFO/WARNING/ERROR/CRITICAL级别
4. **环境感知** - 生产环境和开发环境使用不同的日志详细程度

---

## 🛠️ 使用方法

### 1. 导入日志工具

```python
from logger_util import get_logger

# 在函数/类开头创建logger实例
logger = get_logger("模块名")  # 例如: "auth-signin", "payment-create-order"
```

### 2. 替换print语句

**旧代码** (使用print):
```python
print(f"[AUTH-SIGNIN] Login attempt for: {email} from IP: {client_ip}", file=sys.stderr)
```

**新代码** (使用logger):
```python
logger.info("Login attempt", email=email, client_ip=client_ip)
```

**输出对比**:
```
# 旧格式（不一致，可能泄露敏感信息）
[AUTH-SIGNIN] Login attempt for: user@example.com from IP: 192.168.1.1

# 新格式（统一格式，自动脱敏）
[2025-11-17T10:30:45.123Z] [INFO] [auth-signin] Login attempt email=u***@example.com | client_ip=192.168.***.***
```

---

## 📊 日志级别使用指南

### DEBUG - 详细调试信息
仅在开发环境显示（设置`LOG_LEVEL=DEBUG`）

```python
logger.debug("Detailed debug info", data=some_complex_data)
logger.debug("Function called with params", params=params_dict)
```

### INFO - 一般操作信息（默认）
正常的业务操作记录

```python
logger.info("User logged in successfully", email=email, user_id=user_id)
logger.info("Order created", order_id=order_id, amount=amount)
logger.info("Email sent", recipient=email, purpose="verification")
```

### WARNING - 警告信息
潜在问题，但不影响正常运行

```python
logger.warning("Rate limit exceeded", ip=client_ip, endpoint="auth-signin")
logger.warning("Fallback to default config", reason="config file not found")
logger.warning("API request failed, retrying", error=str(e), retry_count=retry)
```

### ERROR - 错误信息
操作失败，需要关注

```python
logger.error("Login failed", email=email, error=str(e))
logger.error("Payment processing failed", order_id=order_id, error=error_msg)
logger.error("Database query failed", query="users.select", error=str(e))
```

### CRITICAL - 严重错误
系统级错误，需要立即处理

```python
logger.critical("Database connection lost", error=str(e))
logger.critical("Critical security violation detected", user_id=user_id, action=action)
```

---

## 🔒 自动脱敏功能

logger_util会自动识别并脱敏以下类型的敏感信息：

### 1. 邮箱地址
```python
logger.info("User signup", email="user@example.com")
# 输出: email=u***@example.com
```

### 2. IP地址
```python
logger.info("API request", client_ip="192.168.1.100", ip_address="10.0.0.1")
# 输出: client_ip=192.168.***.*** | ip_address=10.0.***.***
```

### 3. Token/密钥/密码
```python
logger.info("Auth token received", access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
# 输出: access_token=eyJh...VC***

logger.debug("API key", api_key="sk-1234567890abcdef")
# 输出: api_key=sk-1...def***
```

### 4. UUID
```python
logger.info("User created", user_id="550e8400-e29b-41d4-a716-446655440000")
# 输出: user_id=550e8400***
```

### 5. 普通数据（不脱敏）
```python
logger.info("Order created", plan_type="pro_monthly", amount=29.0)
# 输出: plan_type=pro_monthly | amount=29.0
```

---

## ⚙️ 环境变量配置

### LOG_LEVEL - 日志级别
控制显示哪些级别的日志

```bash
# 开发环境 - 显示所有日志
LOG_LEVEL=DEBUG

# 生产环境 - 仅显示INFO及以上级别（默认）
LOG_LEVEL=INFO

# 严格模式 - 仅显示错误和警告
LOG_LEVEL=WARNING
```

### LOG_VERBOSE - 详细模式
⚠️ **生产环境必须禁用** - 显示未脱敏的原始数据

```bash
# 开发/调试环境（显示完整邮箱、IP等）
LOG_VERBOSE=true

# 生产环境（默认，自动脱敏）
LOG_VERBOSE=false
```

---

## 🔄 完整迁移示例

### 示例1: auth-signin.py

**迁移前**:
```python
import sys

def do_POST(self):
    try:
        print(f"[AUTH-SIGNIN] Login attempt for: {email} from IP: {client_ip}", file=sys.stderr)

        # ... 业务逻辑 ...

        print(f"[AUTH-SIGNIN] Login successful: {email}", file=sys.stderr)
    except Exception as e:
        print(f"[AUTH-SIGNIN] Error: {e}", file=sys.stderr)
```

**迁移后**:
```python
from logger_util import get_logger

# 在文件顶部创建logger
logger = get_logger("auth-signin")

def do_POST(self):
    try:
        logger.info("Login attempt", email=email, client_ip=client_ip)

        # ... 业务逻辑 ...

        logger.info("Login successful", email=email, user_id=user_id)
    except Exception as e:
        logger.error("Login failed", email=email, error=str(e))
```

### 示例2: payment-create-order.py

**迁移前**:
```python
print(f"[PAYMENT-CREATE] User {user_id} requesting {plan_type} (¥{correct_price}) via {pay_type}", file=sys.stderr)
print(f"[PAYMENT-CREATE] Order created: {out_trade_no}", file=sys.stderr)
print(f"[SECURITY] Price mismatch detected for {plan_type}", file=sys.stderr)
print(f"[PAYMENT-CREATE] 🚫 Rate limit exceeded for user: {user_id}", file=sys.stderr)
```

**迁移后**:
```python
logger = get_logger("payment-create-order")

logger.info("Payment request", user_id=user_id, plan_type=plan_type, price=correct_price, pay_type=pay_type)
logger.info("Order created successfully", out_trade_no=out_trade_no, amount=amount)
logger.warning("Price mismatch detected", plan_type=plan_type, expected=correct_price, actual=plan_info["price"])
logger.warning("Rate limit exceeded", user_id=user_id, endpoint="payment-create-order")
```

---

## 📝 迁移清单

对于每个API文件，按以下步骤迁移：

- [  ] 1. 在文件顶部导入 `from logger_util import get_logger`
- [ ] 2. 创建logger实例: `logger = get_logger("模块名")`
- [ ] 3. 将所有 `print(..., file=sys.stderr)` 替换为对应级别的logger调用
- [ ] 4. 移除emoji图标（如🚫、✅等），使用日志级别表达严重程度
- [ ] 5. 将消息和参数分离（消息作为第一个参数，数据作为关键字参数）
- [ ] 6. 测试验证日志输出格式和脱敏功能

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **消息简洁清晰**
   ```python
   logger.info("User login attempt", email=email, ip=client_ip)  # ✅ 好
   logger.info(f"User {email} from {client_ip} is trying to login")  # ❌ 差（不会自动脱敏）
   ```

2. **使用关键字参数传递数据**
   ```python
   logger.error("Payment failed", order_id=order_id, error=str(e))  # ✅ 好
   logger.error(f"Payment failed: {order_id}, error: {e}")  # ❌ 差
   ```

3. **选择合适的日志级别**
   ```python
   logger.info("User logged in")  # ✅ 正常操作
   logger.warning("Rate limit exceeded")  # ✅ 潜在问题
   logger.error("Database query failed")  # ✅ 操作失败
   ```

4. **不要在消息中包含敏感信息**
   ```python
   logger.info("Login attempt", email=email)  # ✅ 好（自动脱敏）
   logger.info(f"Login attempt for {email}")  # ❌ 差（不会脱敏）
   ```

### ❌ 避免做法

1. **避免使用f-string拼接敏感信息**
2. **避免手动格式化时间戳**
3. **避免混用print和logger**
4. **避免在生产环境开启LOG_VERBOSE**

---

## 🧪 测试验证

迁移完成后，运行以下测试验证：

```bash
# 1. 单元测试
python -m pytest tests/unit/test_logger_util.py -v

# 2. 集成测试（可选）
LOG_LEVEL=DEBUG python -m api.auth-signin  # 测试迁移后的模块

# 3. 验证脱敏功能
LOG_VERBOSE=false python -m api.auth-signin  # 确保敏感信息已脱敏
LOG_VERBOSE=true python -m api.auth-signin   # 开发模式查看完整信息
```

---

## 📊 迁移进度跟踪

| 模块 | 状态 | 日志数量 | 负责人 | 备注 |
|------|------|---------|-------|------|
| logger_util.py | ✅ 已完成 | - | Claude | 核心模块 |
| auth-signin.py | ⏳ 待迁移 | 5 | - | 参考实现 |
| auth-signup.py | ⏳ 待迁移 | 6 | - | |
| payment-create-order.py | ⏳ 待迁移 | 6 | - | |
| ... | | | | |

---

## 🔗 相关文档

- **核心模块**: `api/logger_util.py`
- **单元测试**: `tests/unit/test_logger_util.py`
- **安全审计报告**: `SECURITY_FIX_PROGRESS.md` (Priority 10)

---

**维护者**: Claude (AI安全审计助手)
**创建日期**: 2025-11-17
**版本**: 1.0
