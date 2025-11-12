# Supabase环境变量配置指南

## 问题现象
- 注册时提示"注册失败: HTTP 400"
- 但关闭应用重新打开后，显示已成功登录

## 根本原因
Vercel部署缺少Supabase环境变量，导致注册API返回400错误。

## 解决方案

### 步骤1：获取Supabase凭证

1. 访问 [Supabase Dashboard](https://app.supabase.com/)
2. 选择你的项目
3. 点击左侧菜单 **Settings** → **API**
4. 复制以下信息：
   - **Project URL**（例如：`https://xxxxxx.supabase.co`）
   - **anon public** key（一长串字符串）

### 步骤2：在Vercel配置环境变量

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择项目 **jindutiao**
3. 点击 **Settings** 标签页
4. 点击左侧 **Environment Variables**
5. 添加以下两个环境变量：

| Name | Value | Environment |
|------|-------|-------------|
| `SUPABASE_URL` | 你的Supabase Project URL | Production, Preview, Development |
| `SUPABASE_ANON_KEY` | 你的Supabase anon key | Production, Preview, Development |

6. 点击 **Save** 保存

### 步骤3：重新部署

环境变量添加后，需要重新部署才能生效：

1. 在Vercel项目页面，点击 **Deployments** 标签页
2. 点击最新部署右侧的 **...** 菜单
3. 选择 **Redeploy**
4. 等待部署完成（1-3分钟）

### 步骤4：测试验证

重新部署后，测试注册功能：

```bash
# 测试注册API
curl -X POST "https://jindutiao.vercel.app/api/auth-signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456"
  }'
```

预期返回：
```json
{
  "success": true,
  "user_id": "...",
  "email": "test@example.com",
  "access_token": "...",
  "refresh_token": "..."
}
```

## 排查步骤

如果配置后仍有问题，按以下顺序排查：

### 1. 确认环境变量已生效

在Vercel Dashboard：
- Settings → Environment Variables
- 确认 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY` 都存在
- 确认它们应用于 **Production** 环境

### 2. 查看部署日志

在Vercel Dashboard：
- Deployments → 点击最新部署
- 查看 **Build Logs**，确认没有错误
- 查看 **Functions** → `auth-signup` → **Logs**

预期看到：
```
AuthManager initialized successfully
```

如果看到：
```
WARNING: Supabase credentials not configured
```

说明环境变量未生效，需要重新部署。

### 3. 测试Supabase连接

创建一个测试端点 `api/test-supabase.py`：

```python
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_ANON_KEY", "")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        self.wfile.write(json.dumps({
            "supabase_url_configured": bool(supabase_url),
            "supabase_key_configured": bool(supabase_key),
            "supabase_url_preview": supabase_url[:20] + "..." if supabase_url else ""
        }).encode())
```

访问 `https://jindutiao.vercel.app/api/test-supabase` 查看环境变量是否配置。

### 4. 检查Supabase项目状态

在Supabase Dashboard：
- 确认项目处于 **Active** 状态
- 检查 **Table Editor** → `users` 表是否存在
- 检查 **Authentication** → **Settings** → **Auth Providers**

## 常见问题

### Q1: 配置后仍然报400
**原因**：环境变量未重新部署就生效

**解决**：手动触发Redeploy

### Q2: Supabase凭证在哪里找？
**答案**：Supabase Dashboard → Settings → API → Project URL 和 anon public key

### Q3: 为什么之前注册成功了但提示失败？
**答案**：注册时虽然返回400，但Auth用户可能已创建。需要配置环境变量后才能正常使用。

## 相关文件
- `api/auth_manager.py:12-30` - Supabase客户端初始化
- `api/auth-signup.py:57-59` - 注册API调用auth_manager
- `gaiya/core/auth_client.py:18` - 客户端backend_url配置
