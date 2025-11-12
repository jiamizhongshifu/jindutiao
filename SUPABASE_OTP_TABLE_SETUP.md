# Supabase触发器权限问题诊断和解决方案

## 问题现象

新用户注册并点击验证邮件后，`public.users.email_verified` 字段仍然是 `false`，触发器未自动同步。

## 可能的原因

### 1. 触发器权限不足
触发器函数可能没有足够的权限访问 `auth.users` 表或更新 `public.users` 表。

### 2. 触发器未正确绑定
触发器可能没有正确绑定到 `auth.users` 表。

### 3. Supabase Auth的特殊机制
Supabase Auth可能使用内部机制更新 `email_confirmed_at`，不触发标准的 UPDATE 触发器。

---

## 诊断步骤

### 步骤1：检查触发器是否存在

在Supabase SQL Editor执行：

```sql
-- 查询触发器
SELECT
  trigger_schema,
  trigger_name,
  event_manipulation,
  event_object_schema,
  event_object_table,
  action_timing,
  action_statement
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_email_verified';
```

**期望结果**：应该返回一条记录，显示触发器绑定在 `auth.users` 表上。

**如果没有结果**：触发器未创建成功，需要重新创建。

### 步骤2：检查函数权限

```sql
-- 查询函数定义和权限
SELECT
  routine_schema,
  routine_name,
  routine_type,
  security_type,
  definer
FROM information_schema.routines
WHERE routine_name = 'sync_email_verification';
```

**期望结果**：
- `security_type` 应该是 `DEFINER`
- 函数应该存在

### 步骤3：手动测试触发器

```sql
-- 查看当前待验证的用户
SELECT
  au.id,
  au.email,
  au.email_confirmed_at,
  pu.email_verified
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE au.email = 'drmrzhong+2@gmail.com';
```

**如果 `email_confirmed_at` 不是 NULL**：说明Supabase Auth已验证，但触发器未同步。

### 步骤4：手动执行同步

```sql
-- 手动同步验证状态
UPDATE public.users pu
SET
  email_verified = TRUE,
  status = 'active',
  updated_at = NOW()
FROM auth.users au
WHERE pu.id = au.id
  AND au.email = 'drmrzhong+2@gmail.com'
  AND au.email_confirmed_at IS NOT NULL;
```

执行后，应用中的验证弹窗应该立即自动关闭。

---

## 替代方案：使用Database Webhooks（推荐）

如果触发器方案不工作，使用Supabase的Database Webhooks是更可靠的方案。

### 配置步骤

1. **在Supabase Dashboard中**：
   - Database → Webhooks
   - 点击 "Create a new webhook"

2. **配置Webhook**：
   ```
   Name: sync-email-verification
   Table: auth.users
   Events: UPDATE
   Type: HTTP Request
   Method: POST
   URL: https://api.gaiyatime.com/api/sync-verification
   HTTP Headers:
     Authorization: Bearer YOUR_SERVICE_ROLE_KEY
   ```

3. **创建同步端点**（`api/sync-verification.py`）：
   ```python
   from http.server import BaseHTTPRequestHandler
   import json
   import os
   from supabase import create_client
   
   class handler(BaseHTTPRequestHandler):
       def do_POST(self):
           # 读取webhook payload
           content_length = int(self.headers.get('Content-Length', 0))
           body = self.rfile.read(content_length).decode('utf-8')
           data = json.loads(body)
           
           # 获取更新的用户记录
           record = data.get('record', {})
           old_record = data.get('old_record', {})
           
           # 检查是否是邮箱验证事件
           if (old_record.get('email_confirmed_at') is None and 
               record.get('email_confirmed_at') is not None):
               
               # 使用Service Role Key更新public.users
               client = create_client(
                   os.getenv('SUPABASE_URL'),
                   os.getenv('SUPABASE_SERVICE_KEY')
               )
               
               client.table('users').update({
                   'email_verified': True,
                   'status': 'active'
               }).eq('id', record['id']).execute()
               
               print(f"Synced verification for user {record['email']}")
           
           # 返回成功
           self.send_response(200)
           self.send_header('Content-Type', 'application/json')
           self.end_headers()
           self.wfile.write(json.dumps({"success": True}).encode())
   ```

---

## 最简单的解决方案：修改后端查询逻辑（强烈推荐）

**不依赖触发器，直接查询 auth.users 表**

修改 `api/auth_manager.py`，添加Service Role权限查询：

### 步骤1：添加Service Role Key到环境变量

在 `.env` 文件（或Vercel环境变量）中添加：
```
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

### 步骤2：修改 check_email_verification() 方法

```python
import os
from supabase import create_client

class AuthManager:
    def __init__(self):
        # 普通客户端（使用Anon Key）
        self.client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        # Admin客户端（使用Service Role Key）
        self.admin_client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
    
    def check_email_verification(self, user_id: str = None, email: str = None) -> Dict:
        """
        检查邮箱验证状态（直接查询auth.users表，不依赖触发器）
        """
        try:
            # 使用admin权限查询auth.users表
            if email:
                # 通过email查询
                response = self.admin_client.auth.admin.list_users()
                user = next((u for u in response if u.email == email), None)
            elif user_id:
                # 通过user_id查询
                user = self.admin_client.auth.admin.get_user_by_id(user_id)
            else:
                return {"success": False, "error": "Missing email or user_id"}
            
            if not user:
                return {
                    "success": True,
                    "verified": False,
                    "message": "等待邮箱验证..."
                }
            
            # 检查email_confirmed_at字段
            is_verified = user.email_confirmed_at is not None
            
            if is_verified:
                # 验证成功，同时更新public.users表
                self.client.table("users").update({
                    "email_verified": True,
                    "status": "active"
                }).eq("id", user.id).execute()
                
                return {
                    "success": True,
                    "verified": True,
                    "user_id": user.id,
                    "email": user.email,
                    "message": "邮箱验证成功！"
                }
            else:
                return {
                    "success": True,
                    "verified": False,
                    "message": "等待邮箱验证..."
                }
        
        except Exception as e:
            print(f"[CHECK-VERIFICATION] Error: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
```

---

## 推荐方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Database Trigger** | 自动化，无需额外代码 | 权限复杂，可能不触发 | ⭐⭐⭐ |
| **Database Webhook** | 可靠，Supabase官方支持 | 需要额外端点 | ⭐⭐⭐⭐ |
| **直接查询auth.users** | 最简单，最可靠 | 需要Service Role Key | ⭐⭐⭐⭐⭐ |

**建议使用第3种方案（直接查询auth.users）**，因为：
1. 最简单，不依赖触发器或Webhook
2. 最可靠，直接读取Supabase Auth的官方数据
3. 实时性好，每次轮询都能立即获取最新状态

---

## 立即修复当前用户

在Supabase SQL Editor执行：

```sql
UPDATE public.users pu
SET
  email_verified = TRUE,
  status = 'active',
  updated_at = NOW()
FROM auth.users au
WHERE pu.id = au.id
  AND au.email = 'drmrzhong+2@gmail.com'
  AND au.email_confirmed_at IS NOT NULL;
```

执行后，应用中的验证弹窗应该在5秒内自动关闭。
