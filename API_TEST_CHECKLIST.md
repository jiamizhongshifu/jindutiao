# API测试检查清单

## ✅ 基础端点（已验证）
- [x] GET `/api/health` - 健康检查
- [x] GET `/api/quota-status?user_tier=free` - 配额查询

## 🆕 认证端点（需要测试）

### 1. 注册
```bash
curl -X POST https://jindutiao.vercel.app/api/auth-signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "username": "testuser"
  }'
```

**预期响应**:
```json
{
  "success": true,
  "user_id": "uuid",
  "email": "test@example.com",
  "access_token": "...",
  "refresh_token": "..."
}
```

### 2. 登录
```bash
curl -X POST https://jindutiao.vercel.app/api/auth-signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'
```

**预期响应**:
```json
{
  "success": true,
  "user_id": "uuid",
  "email": "test@example.com",
  "user_tier": "free",
  "access_token": "...",
  "refresh_token": "..."
}
```

### 3. 登出
```bash
curl -X POST https://jindutiao.vercel.app/api/auth-signout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. 刷新Token
```bash
curl -X POST https://jindutiao.vercel.app/api/auth-refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## 🆕 订阅端点

### 查询订阅状态
```bash
curl "https://jindutiao.vercel.app/api/subscription-status?user_id=YOUR_USER_ID"
```

## 🆕 样式商店端点

### 获取样式列表
```bash
curl "https://jindutiao.vercel.app/api/styles-list?user_id=YOUR_USER_ID&user_tier=free"
```

**预期响应**:
```json
{
  "success": true,
  "styles": [
    {
      "style_id": "...",
      "name": "经典纯色",
      "category": "basic",
      "tier": "free",
      "accessible": true
    },
    ...
  ]
}
```

## 🆕 支付端点（需要ZPay配置）

### 创建支付订单
```bash
curl -X POST https://jindutiao.vercel.app/api/payment-create-order \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "plan_type": "pro_monthly",
    "pay_type": "alipay"
  }'
```

## ❌ 常见错误排查

### 错误1: 500 Internal Server Error
**可能原因**: 缺少环境变量
**解决方法**: 检查Vercel环境变量配置

### 错误2: 404 NOT_FOUND
**可能原因**:
- Vercel部署未完成
- 路由配置问题
**解决方法**:
- 等待2-3分钟部署完成
- 检查vercel.json配置

### 错误3: Supabase相关错误
**可能原因**: Supabase配置或数据库表未创建
**解决方法**:
1. 确认SUPABASE_URL和SUPABASE_ANON_KEY已配置
2. 在Supabase执行 `api/schema/01_init_tables.sql`
3. 在Supabase执行 `api/schema/02_seed_data.sql`

## 📊 测试优先级

1. **P0 (必须工作)**:
   - /api/auth-signin
   - /api/auth-signup
   - /api/subscription-status

2. **P1 (重要)**:
   - /api/auth-refresh
   - /api/styles-list

3. **P2 (可选)**:
   - /api/payment-* (需要支付配置)
   - /api/auth-reset-password

## 🎯 下一步

1. 等待Vercel部署完成（2-3分钟）
2. 测试P0端点
3. 如果失败，检查Vercel日志
4. 配置缺失的环境变量
5. 在Supabase执行数据库脚本
