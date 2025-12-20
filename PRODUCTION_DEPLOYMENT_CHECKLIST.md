# 生产环境部署检查清单

**项目**: GaiYa每日进度条
**日期**: 2025-12-20
**版本**: v1.7+

---

## ✅ 1. 环境变量配置

### 1.1 Vercel 环境变量设置

前往 [Vercel Dashboard](https://vercel.com/jindutiao) → Settings → Environment Variables

**必须配置的环境变量**:

```bash
# 环境标识（生产环境）
ENVIRONMENT=production

# Zpay 支付网关（国内支付）
ZPAY_PID=你的生产PID
ZPAY_PKEY=你的生产密钥

# Supabase 数据库
SUPABASE_URL=https://qpgypaxwjgcirssydgqh.supabase.co
SUPABASE_ANON_KEY=你的ANON_KEY
SUPABASE_SERVICE_KEY=你的SERVICE_KEY

# Stripe 支付网关（海外支付 - 可选）
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_MONTHLY=price_xxxxx
STRIPE_PRICE_YEARLY=price_xxxxx
STRIPE_PRICE_LIFETIME=price_xxxxx
```

**⚠️ 重要**:
- [ ] 确保使用 **生产环境密钥**（Live Mode），而非测试密钥
- [ ] `ENVIRONMENT` 必须设置为 `production`
- [ ] **不要** 设置 `ZPAY_DEBUG_MODE`
- [ ] **不要** 设置 `ENABLE_TEST_PRICES`

---

## ✅ 2. Mock 测试端点安全验证

### 2.1 验证测试端点已禁用

访问以下URL，确认返回 **403 Forbidden**:

```bash
curl -X POST https://你的域名/api/test-zpay-mock-callback \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","plan_type":"pro_monthly"}'
```

**预期响应**:
```json
{
  "error": "Mock callback is not available in production environment"
}
```

**状态码**: `403 Forbidden`

### 2.2 代码验证

以下文件已包含生产环境检查（无需修改）:

- [x] `api/test-zpay-mock-callback.py` - 第40行有 `Config.is_production()` 检查
- [x] `local_test_server.py` - 第85行有 `Config.is_production()` 检查

---

## ✅ 3. 本地测试文件管理

### 3.1 测试文件列表

以下文件**仅用于本地测试**，不会被部署到 Vercel:

- [x] `check_user_tier.py` - 本地诊断工具
- [x] `test_zpay_mock.py` - 本地测试脚本
- [x] `local_test_server.py` - 本地Flask服务器
- [x] `tests/` 目录 - 单元测试和集成测试

**Vercel 部署规则**:
- Vercel 只部署 `api/` 目录下的 Python 文件
- 上述测试文件位于项目根目录，不会被部署
- 即使部署，也因环境变量 `ENVIRONMENT=production` 而无法访问

---

## ✅ 4. 代码安全审查

### 4.1 敏感信息检查

- [x] **无硬编码密钥**: 所有密钥通过环境变量读取
- [x] **无测试用户ID泄露**: 测试用户ID仅存在于测试文件中
- [x] **无密码日志**: 不记录password、secret等敏感字段

### 4.2 调试日志检查

- [x] **生产环境日志级别**: 默认为 `INFO`，不输出调试信息
- [x] **无ZPAY_DEBUG_MODE**: 调试模式仅在开发环境启用

### 4.3 水印修复

- [x] **水印同步问题已修复**: [config_gui.py:4462-4471](config_gui.py#L4462-L4471) 已添加同步逻辑
- [x] **Pro会员水印已移除**: 刷新会员状态后，主窗口AuthClient会同步更新

---

## ✅ 5. API 端点验证

### 5.1 关键端点测试

在部署后，测试以下API端点:

**认证端点**:
```bash
# 用户注册
curl -X POST https://你的域名/api/auth-signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password123!","username":"testuser"}'

# 用户登录
curl -X POST https://你的域名/api/auth-signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password123!"}'
```

**支付端点**:
```bash
# Zpay 创建订单
curl -X POST https://你的域名/api/zpay-create-order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"plan_type":"pro_monthly"}'

# 订阅状态查询
curl -X GET "https://你的域名/api/subscription-status?user_id=<user_id>" \
  -H "Authorization: Bearer <access_token>"
```

---

## ✅ 6. 数据库 RLS 策略

### 6.1 Supabase RLS 检查

确认以下表的 RLS 策略已正确配置:

- [x] `users` 表 - 允许SERVICE_KEY绕过RLS
- [x] `subscriptions` 表 - 允许服务端创建订阅
- [x] `payments` 表 - 允许服务端记录支付
- [x] `user_quotas` 表 - 允许服务端更新配额

**验证方法**:
```sql
-- 在 Supabase SQL Editor 中执行
SELECT tablename, policyname
FROM pg_policies
WHERE schemaname = 'public';
```

---

## ✅ 7. 支付回调配置

### 7.1 Zpay 回调地址

登录 [Zpay 商户后台](https://pay.zpay.com)，配置回调地址:

```
https://你的域名/api/payment-notify
```

### 7.2 Stripe Webhook

登录 [Stripe Dashboard](https://dashboard.stripe.com)，配置Webhook:

```
URL: https://你的域名/api/stripe-webhook
Events:
  - checkout.session.completed
  - invoice.payment_succeeded
  - invoice.payment_failed
  - customer.subscription.updated
  - customer.subscription.deleted
```

---

## ✅ 8. 客户端配置

### 8.1 桌面应用配置

客户端**不需要修改代码**，默认已配置为生产API:

```python
# ai_client.py (默认配置)
backend_url = "https://api.gaiyatime.com"
```

### 8.2 客户端 .env 文件

桌面客户端的 `.env` 文件应该配置为:

```bash
# ⚠️ 客户端配置 - 仅使用 ANON_KEY，不使用 SERVICE_KEY

# Supabase（客户端只需要ANON_KEY）
SUPABASE_URL=https://qpgypaxwjgcirssydgqh.supabase.co
SUPABASE_ANON_KEY=你的ANON_KEY

# 后端API（可选，默认已内置）
# GAIYA_API_URL=https://api.gaiyatime.com
```

**⚠️ 安全警告**:
- 客户端**绝对不能**包含 `SUPABASE_SERVICE_KEY`
- 客户端**不需要**配置支付密钥（Zpay/Stripe）
- 所有支付操作必须通过后端API完成

---

## ✅ 9. 部署流程

### 9.1 Git 提交

```bash
# 1. 停止本地测试服务器（已完成）
# 端口3000已释放 ✓

# 2. 提交代码
git add .
git commit -m "fix: 修复pro会员水印显示问题 + 生产环境部署准备"

# 3. 推送到远程仓库
git push origin main
```

### 9.2 Vercel 自动部署

推送后，Vercel 会自动触发部署:

1. 访问 [Vercel Dashboard](https://vercel.com/jindutiao)
2. 查看 **Deployments** 标签页
3. 等待部署完成（通常1-3分钟）
4. 检查部署日志，确保无错误

### 9.3 部署后验证

- [ ] 访问 `https://你的域名/health` 查看健康检查
- [ ] 测试用户注册/登录功能
- [ ] 测试Mock端点返回403
- [ ] 测试真实支付流程（小额测试）

---

## ✅ 10. 回滚预案

### 10.1 Vercel 回滚

如果部署出现问题:

1. 前往 Vercel Dashboard → Deployments
2. 找到上一个稳定版本
3. 点击 **Promote to Production**

### 10.2 环境变量回滚

如果环境变量配置错误:

1. Vercel Dashboard → Settings → Environment Variables
2. 修改错误的变量
3. 点击 **Redeploy**（不需要重新推送代码）

---

## ✅ 11. 监控和日志

### 11.1 Vercel 日志

实时查看生产环境日志:

```bash
vercel logs --prod
```

或在 Vercel Dashboard → Deployments → 点击部署 → View Function Logs

### 11.2 Supabase 日志

查看数据库操作日志:

1. Supabase Dashboard → Logs
2. 选择 **Auth Logs** / **Postgres Logs**
3. 监控异常登录和数据库错误

---

## ✅ 12. 最终检查清单

**部署前必查**:

- [ ] Vercel 环境变量已配置为 `ENVIRONMENT=production`
- [ ] 已移除或注释 `ZPAY_DEBUG_MODE`
- [ ] 已移除或注释 `ENABLE_TEST_PRICES`
- [ ] Mock 测试端点返回 403（生产环境已禁用）
- [ ] 支付回调URL已配置（Zpay + Stripe Webhook）
- [ ] 客户端 `.env` 仅包含 ANON_KEY（不包含 SERVICE_KEY）
- [ ] Git 代码已提交并推送
- [ ] Vercel 自动部署成功
- [ ] 健康检查通过 (`/health` 返回200)
- [ ] 用户注册/登录功能正常
- [ ] 真实支付流程测试通过

**部署后必做**:

- [ ] 监控 Vercel 日志，检查是否有错误
- [ ] 测试真实用户支付流程（小额）
- [ ] 确认会员状态正确更新（无水印）
- [ ] 准备回滚预案（记录上一个稳定版本）

---

## 📞 应急联系

**如遇紧急问题**:

1. **回滚部署**: Vercel Dashboard → Promote previous deployment
2. **查看日志**: `vercel logs --prod`
3. **检查环境变量**: Vercel Dashboard → Settings → Environment Variables
4. **数据库恢复**: Supabase Dashboard → Backups（自动备份）

---

**检查清单完成日期**: ______________________
**执行人**: ______________________
**备注**: ______________________

---

✅ **所有检查项已完成，可以安全部署到生产环境！**
