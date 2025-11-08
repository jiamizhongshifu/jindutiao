# 部署安全指南

## Vercel 环境变量配置

### 必需环境变量

在 Vercel 项目设置 → Environment Variables 中配置：

```bash
# Supabase配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# ZPAY支付配置
ZPAY_PID=your-zpay-pid
ZPAY_PKEY=your-zpay-secret-key

# AI服务配置（如使用）
TUZI_API_KEY=your-tuzi-api-key
```

### 安全检查清单

- [ ] ✅ 所有敏感凭证已通过环境变量配置
- [ ] ✅ `.env` 文件已添加到 `.gitignore`
- [ ] ✅ Supabase RLS（Row Level Security）策略已启用
- [ ] ✅ ZPAY回调IP白名单已配置（如支持）
- [ ] ✅ Vercel Functions日志级别已设置为生产模式

## Supabase RLS 策略示例

### users 表

```sql
-- 用户只能查看自己的数据
CREATE POLICY "Users can view own data"
ON users FOR SELECT
USING (auth.uid() = id);

-- 用户只能更新自己的数据
CREATE POLICY "Users can update own data"
ON users FOR UPDATE
USING (auth.uid() = id);
```

### user_quotas 表

```sql
-- 认证用户可以查看自己的配额
CREATE POLICY "Authenticated users can view own quota"
ON user_quotas FOR SELECT
USING (auth.uid()::text = user_id);

-- 只有系统可以更新配额（通过Service Role Key）
CREATE POLICY "System can update quotas"
ON user_quotas FOR UPDATE
USING (false);  -- 客户端无权限，仅API可操作
```

### subscriptions 表

```sql
-- 用户可以查看自己的订阅
CREATE POLICY "Users can view own subscriptions"
ON subscriptions FOR SELECT
USING (auth.uid()::text = user_id);

-- 禁止客户端直接修改订阅（仅通过API）
CREATE POLICY "No direct subscription updates"
ON subscriptions FOR UPDATE
USING (false);
```

## 安全配置验证

### 测试Supabase RLS

```bash
# 1. 使用Anon Key（应该只能访问自己的数据）
curl -H "apikey: YOUR_ANON_KEY" \
     -H "Authorization: Bearer USER_JWT_TOKEN" \
     https://your-project.supabase.co/rest/v1/users?id=eq.test-user

# 2. 尝试访问其他用户数据（应该被拒绝）
curl -H "apikey: YOUR_ANON_KEY" \
     https://your-project.supabase.co/rest/v1/users?id=eq.other-user
```

### 测试支付回调验证

```bash
# 测试无签名请求（应该被拒绝）
curl -X POST https://your-app.vercel.app/api/payment-notify \
     -d '{"out_trade_no":"TEST001","trade_status":"success"}'

# 测试错误签名（应该被拒绝）
curl -X POST https://your-app.vercel.app/api/payment-notify \
     -d '{"out_trade_no":"TEST001","sign":"fake_signature"}'
```

## 生产环境部署流程

### 1. 准备阶段

- [ ] 确认所有代码已提交到Git
- [ ] 确认测试文件中无硬编码凭证
- [ ] 运行安全扫描：`python -m bandit -r api/`
- [ ] 更新版本号

### 2. Vercel配置

```bash
# 连接Vercel CLI
vercel login

# 设置环境变量（生产环境）
vercel env add SUPABASE_URL production
vercel env add SUPABASE_ANON_KEY production
vercel env add ZPAY_PID production
vercel env add ZPAY_PKEY production

# 部署
vercel --prod
```

### 3. 部署后验证

- [ ] 测试API健康检查：`curl https://your-app.vercel.app/api/health`
- [ ] 测试配额查询（需要Token）
- [ ] 测试支付创建（小额测试订单）
- [ ] 检查Vercel Functions日志无敏感信息泄露

## 监控与告警

### Vercel Analytics

启用 Vercel Analytics 监控：
- API响应时间
- 错误率
- 异常流量模式

### Supabase Dashboard

定期检查：
- 异常的数据库查询
- RLS策略绕过尝试
- 未授权访问日志

## 应急响应

### 凭证泄露应急流程

1. **立即轮换凭证**
   ```bash
   # Supabase: 在Dashboard重置Project API Keys
   # ZPAY: 联系客服重置密钥
   ```

2. **更新环境变量**
   ```bash
   vercel env rm ZPAY_PKEY production
   vercel env add ZPAY_PKEY production  # 输入新值
   ```

3. **重新部署**
   ```bash
   vercel --prod --force
   ```

4. **通知用户**（如影响用户数据）

### 检测到攻击时

1. 暂时禁用受影响的API端点
2. 分析Vercel Functions日志
3. 修复漏洞
4. 重新部署
5. 发布安全公告

## 定期安全维护

### 每周

- [ ] 检查Vercel Functions日志异常
- [ ] 监控API错误率

### 每月

- [ ] 更新依赖库：`pip list --outdated`
- [ ] 审查Supabase访问日志
- [ ] 检查有效订阅与实际用户一致性

### 每季度

- [ ] 轮换API密钥
- [ ] 进行渗透测试
- [ ] 更新安全文档

---

**最后更新**: 2025-11-08
**负责人**: GaiYa 运维团队
