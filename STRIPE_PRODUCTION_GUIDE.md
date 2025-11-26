# Stripe 生产环境激活指南

本文档说明如何将 GaiYa 的 Stripe 支付从测试模式切换到生产模式。

---

## 📋 前置准备清单

### 1. Stripe 账户要求
- ✅ 已注册 Stripe 账户 (https://dashboard.stripe.com)
- ✅ 已完成企业/个人信息验证
- ✅ 已绑定银行账户用于收款
- ✅ 已通过 Stripe KYC 审核

### 2. 必需的企业信息
- 企业名称/个人姓名
- 企业地址/个人地址
- 税务信息 (Tax ID / EIN)
- 银行账户信息
- 企业类型 (个人/公司/非盈利)

---

## 🚀 激活步骤

### 第一步: 激活 Stripe 生产模式

1. **登录 Stripe Dashboard**
   - 访问: https://dashboard.stripe.com
   - 使用你的 Stripe 账户登录

2. **完成账户激活**
   - 点击左上角的 "测试模式" 切换按钮
   - 如果看到 "激活你的账户" 提示,点击进入
   - 按照指引填写所有必需信息:
     ```
     ✓ 企业详情 (Business details)
     ✓ 银行账户 (Bank account)
     ✓ 公开的企业信息 (Public business information)
     ✓ 产品/服务描述
     ```

3. **等待审核**
   - 提交后,Stripe 通常在 1-3 个工作日内完成审核
   - 审核通过后,你将收到邮件通知
   - 此时账户状态会从 "受限" 变为 "已激活"

---

### 第二步: 创建生产环境的产品和价格

当前使用的是**测试价格ID**,需要在生产环境中重新创建:

#### 1. 进入产品管理
- Dashboard → 产品 (Products)
- 点击 "添加产品" (Add product)

#### 2. 创建产品: GaiYa 高级版

**产品 1: 月度会员**
```
名称: GaiYa Pro - Monthly
描述: GaiYa 高级版月度会员,解锁所有高级功能
价格: $4.99 USD/月 (或 ¥29 CNY/月)
类型: 订阅 (Recurring)
计费周期: 每月 (Monthly)
```

**产品 2: 年度会员**
```
名称: GaiYa Pro - Yearly
描述: GaiYa 高级版年度会员,享受17%折扣
价格: $39.99 USD/年 (或 ¥199 CNY/年)
类型: 订阅 (Recurring)
计费周期: 每年 (Yearly)
```

**产品 3: 终身会员**
```
名称: GaiYa Lifetime Partnership
描述: GaiYa 会员合伙人,一次性购买,终身有效
价格: $99.99 USD (或 ¥599 CNY)
类型: 一次性 (One-time payment)
```

#### 3. 获取生产环境价格ID
创建完产品后,每个价格会生成一个 **Price ID**:
- 格式: `price_xxxxxxxxxxxxx` (不是以 `price_test_` 开头)
- 记录下这3个价格ID,后续配置需要

---

### 第三步: 获取生产环境密钥

#### 1. 获取 Secret Key (密钥)
- Dashboard → 开发者 (Developers) → API 密钥 (API keys)
- 切换到 **"生产模式"** (Live mode)
- 找到 **"Secret key"**:
  ```
  格式: sk_live_xxxxxxxxxxxxxxxxxxxxx
  ```
- 点击 "显示" (Reveal) 并**复制保存**
- ⚠️ **重要**: 此密钥极其敏感,切勿泄露或提交到代码库

#### 2. 获取 Webhook Secret (Webhook密钥)
- Dashboard → 开发者 (Developers) → Webhooks
- 点击 "添加端点" (Add endpoint)
- 填写 Webhook URL:
  ```
  https://api.gaiyatime.com/api/stripe-webhook.py
  ```
- 选择监听的事件:
  ```
  ✓ checkout.session.completed (结账完成)
  ✓ invoice.payment_succeeded (订阅支付成功)
  ✓ customer.subscription.deleted (订阅取消)
  ```
- 点击 "添加端点" (Add endpoint)
- 创建成功后,点击端点详情
- 找到 **"Signing secret"**:
  ```
  格式: whsec_xxxxxxxxxxxxxxxxxxxxx
  ```
- **复制保存**此密钥

---

### 第四步: 配置 Vercel 环境变量

#### 1. 登录 Vercel Dashboard
- 访问: https://vercel.com
- 找到你的项目: `jindutiao`

#### 2. 添加/更新环境变量
- 项目设置 (Settings) → 环境变量 (Environment Variables)
- 添加以下生产环境变量:

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `STRIPE_SECRET_KEY` | `sk_live_xxxxxxxx` | 生产环境密钥 |
| `STRIPE_WEBHOOK_SECRET` | `whsec_xxxxxxxx` | Webhook签名密钥 |
| `STRIPE_PRICE_MONTHLY` | `price_xxxxxxxx` | 月度会员价格ID |
| `STRIPE_PRICE_YEARLY` | `price_xxxxxxxx` | 年度会员价格ID |
| `STRIPE_PRICE_LIFETIME` | `price_xxxxxxxx` | 终身会员价格ID |

#### 3. 环境选择
每个变量都需要选择应用环境:
- ✅ **Production** (必选)
- ✅ **Preview** (可选,用于测试分支)
- ❌ **Development** (本地开发保持使用测试密钥)

#### 4. 保存并重新部署
- 点击 "Save" (保存)
- Vercel 会自动提示重新部署
- 点击 "Redeploy" (重新部署)
- 等待部署完成 (约1-2分钟)

---

### 第五步: 验证生产环境配置

#### 1. 检查 Vercel 部署日志
```bash
# 查看最新部署的日志
# 应该看到:
[Stripe] Manager initialized successfully
```

#### 2. 测试真实支付流程
**⚠️ 重要提示**:
- 这将发起**真实的支付交易**
- 请使用真实的银行卡进行小额测试 (例如 $0.50)
- 或使用 Stripe 提供的[测试银行卡](https://stripe.com/docs/testing#international-cards)

**测试步骤**:
1. 访问官网: https://www.gaiyatime.com
2. 点击 "升级会员"
3. 选择 "国际支付 (Stripe)"
4. 填写邮箱/密码,完成注册/登录
5. 使用真实银行卡完成支付
6. 检查:
   - ✓ 跳转到 Stripe Checkout 页面
   - ✓ 页面显示 **正式价格** (不是测试价格)
   - ✓ 支付成功后跳转回你的网站
   - ✓ 用户账户升级为会员
   - ✓ Stripe Dashboard 中看到真实订单

#### 3. 验证 Webhook 接收
- Stripe Dashboard → 开发者 → Webhooks
- 点击你的 Webhook 端点
- 查看 "最近的事件" (Recent events)
- 确认看到 `checkout.session.completed` 事件
- 状态应为 **"Succeeded"** (成功)

---

## 🔒 安全注意事项

### 1. 密钥管理
- ❌ **永远不要**将生产密钥提交到 Git
- ❌ **永远不要**在代码中硬编码密钥
- ✅ **始终**使用环境变量存储密钥
- ✅ **定期轮换**密钥 (建议每6个月)

### 2. Webhook 安全
当前代码已实现签名验证:
```python
# api/stripe_manager.py
def verify_webhook_signature(self, payload, signature):
    """验证 Webhook 签名"""
    return stripe.Webhook.construct_event(
        payload, signature, self.webhook_secret
    )
```

### 3. 访问控制
- 限制 Stripe Dashboard 访问权限
- 启用双因素认证 (2FA)
- 定期审查 API 密钥使用情况

---

## 💰 定价建议

### 建议的定价策略

**当前人民币定价**:
- 月度会员: ¥29
- 年度会员: ¥199 (相当于 ¥16.6/月,省¥149)
- 终身会员: ¥599

**Stripe 美元定价建议** (考虑汇率 + 国际支付手续费):
- 月度会员: **$4.99** (~¥36, 溢价25%)
- 年度会员: **$39.99** (~¥288, 溢价44%)
- 终身会员: **$99.99** (~¥720, 溢价20%)

**溢价理由**:
1. Stripe 手续费: 2.9% + $0.30
2. 货币转换费用
3. 国际支付风险溢价
4. 便于定价策略差异化

---

## 📊 监控与分析

### 1. Stripe Dashboard 监控
- 收入概览 (Revenue)
- 订阅管理 (Subscriptions)
- 客户管理 (Customers)
- 失败支付 (Failed payments)

### 2. 关键指标
- 支付成功率 (Payment success rate)
- 订阅流失率 (Churn rate)
- 平均订单价值 (AOV)
- 退款率 (Refund rate)

### 3. 告警设置
建议在 Stripe Dashboard 中设置告警:
- ✓ Webhook 失败
- ✓ 大额支付 (>$100)
- ✓ 异常退款
- ✓ 高风险交易

---

## 🛠️ 故障排查

### 问题 1: Webhook 未收到
**症状**: 支付成功,但用户账户未升级

**排查步骤**:
1. 检查 Webhook URL 是否正确: `https://api.gaiyatime.com/api/stripe-webhook.py`
2. 检查 Webhook 密钥是否正确配置
3. 查看 Vercel 函数日志: Vercel Dashboard → Functions → Logs
4. 查看 Stripe Webhook 日志: Dashboard → Webhooks → 你的端点 → 事件

**解决方案**:
```bash
# 检查环境变量
echo $STRIPE_WEBHOOK_SECRET

# 重新部署
git commit --allow-empty -m "Redeploy for webhook fix"
git push
```

### 问题 2: 支付失败
**症状**: 用户点击支付后显示错误

**排查步骤**:
1. 检查价格ID是否正确 (生产环境不能用 `price_test_` 开头)
2. 检查 Secret Key 是否为生产密钥 (以 `sk_live_` 开头)
3. 查看浏览器控制台错误信息
4. 查看 Stripe Dashboard → 日志 (Logs)

### 问题 3: 价格显示错误
**症状**: 显示的是测试价格,不是生产价格

**原因**: 环境变量未更新

**解决方案**:
1. 确认 Vercel 环境变量中的价格ID是生产价格ID
2. 重新部署项目
3. 清除浏览器缓存

---

## 📞 支持资源

### Stripe 官方资源
- [Stripe 文档](https://stripe.com/docs)
- [Stripe 支持中心](https://support.stripe.com)
- [Stripe API 参考](https://stripe.com/docs/api)
- [Stripe 测试卡号](https://stripe.com/docs/testing)

### 联系方式
- Stripe 客服: support@stripe.com
- 实时聊天: Dashboard 右下角聊天按钮
- 电话支持: 仅企业账户可用

---

## ✅ 检查清单

激活完成前,请确认以下所有项目:

**账户激活**
- [ ] Stripe 账户已完成 KYC 验证
- [ ] 银行账户已绑定
- [ ] 账户状态显示 "已激活"

**产品配置**
- [ ] 已创建3个生产环境产品
- [ ] 已获取3个生产价格ID
- [ ] 价格ID格式正确 (不含 `test`)

**密钥配置**
- [ ] 已获取生产 Secret Key (`sk_live_`)
- [ ] 已创建并获取 Webhook Secret (`whsec_`)
- [ ] 所有密钥已添加到 Vercel 环境变量
- [ ] 已重新部署 Vercel 项目

**测试验证**
- [ ] 已完成真实支付测试
- [ ] Webhook 事件正常接收
- [ ] 用户账户正确升级
- [ ] Stripe Dashboard 显示真实订单

**安全检查**
- [ ] 代码中无硬编码密钥
- [ ] 已启用 Stripe Dashboard 双因素认证
- [ ] Webhook 签名验证已启用

---

## 🎉 恭喜!

完成以上所有步骤后,你的 Stripe 生产环境就正式激活了!

现在用户可以通过 Stripe 进行真实的国际支付,购买 GaiYa 会员服务。

**下一步建议**:
1. 监控前几天的支付数据,确保一切正常
2. 设置 Stripe Radar 防欺诈规则
3. 配置自动发票和收据邮件
4. 考虑启用 Stripe Billing 订阅管理功能

---

**文档版本**: v1.0
**最后更新**: 2025-11-26
**维护者**: Claude Code

如有任何问题,请查阅 Stripe 官方文档或联系 Stripe 支持团队。
