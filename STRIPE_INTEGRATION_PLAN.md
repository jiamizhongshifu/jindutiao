# GaiYa Stripe支付集成方案

## 📋 目标
将Stripe国际支付集成到现有的zpay支付系统中，实现双支付通道并行。

## 🏗️ 架构设计

### 1. 支付方式选择
```
┌─────────────────────────────────────────┐
│         选择支付方式                      │
├─────────────────────────────────────────┤
│  ○ 支付宝  ○ 微信支付  ○ 国际支付(Stripe)  │
└─────────────────────────────────────────┘
```

### 2. 支付流程分支
```python
if selected_pay_type in ['alipay', 'wxpay']:
    # 走zpay流程
    result = auth_client.create_payment_order(plan_type, pay_type)
    payment_url = result['payment_url']
    open_in_browser(payment_url)
    start_polling()  # 轮询支付状态

elif selected_pay_type == 'stripe':
    # 走Stripe流程
    result = auth_client.create_stripe_checkout(plan_type, user_email)
    checkout_url = result['checkout_url']
    open_in_browser(checkout_url)
    # Webhook自动处理，不需要轮询
    show_message("支付窗口已打开,完成支付后会员权益将自动激活")
```

### 3. 数据统一管理

**payments表**：
- zpay订单：payment_method='alipay'/'wxpay', payment_provider='zpay'
- Stripe订单：payment_method='stripe', payment_provider='stripe'

**subscriptions表**：
- 两种支付方式的订阅数据存储在同一张表
- 通过 `payment_provider` 字段区分来源

**users表**：
- user_tier: free/pro/lifetime（不区分支付方式）
- 两种支付方式升级的用户享受相同权益

## 📝 实现清单

### ✅ 后端API（已完成）
- [x] Stripe Checkout Session创建API
- [x] Stripe Webhook事件处理
- [x] 数据库Schema支持Stripe字段
- [x] subscription_manager支持payment_provider参数

### 🔲 前端客户端（待实现）
- [ ] UI: 添加"国际支付(Stripe)"选项
- [ ] UI: 修改购买逻辑支持Stripe分支
- [ ] AuthClient: 添加create_stripe_checkout()方法
- [ ] 测试: 完整支付流程测试

## 🎨 UI设计

### 支付方式选择模块
```
┌─────────────────────────────────────────────────┐
│                选择支付方式                        │
│                                                 │
│  ┌─────────┐  ┌─────────┐  ┌────────────┐     │
│  │ ○ 支付宝 │  │ ○ 微信支付 │  │ ○ 国际支付   │     │
│  │         │  │          │  │ (Stripe)   │     │
│  └─────────┘  └─────────┘  └────────────┘     │
│                                                 │
│  💡 提示：国际支付支持Visa/Mastercard等信用卡      │
└─────────────────────────────────────────────────┘
```

### 价格显示策略
- **国内支付（zpay）**：显示人民币价格（¥29/¥199/¥599）
- **国际支付（Stripe）**：显示美元价格（$4.99/$39.99/$89.99）
- **切换支付方式时自动更新价格显示**

## 🔐 安全性考虑

1. **API密钥安全**
   - Stripe密钥通过环境变量配置（Vercel Environment Variables）
   - 客户端不存储任何敏感凭证

2. **Webhook签名验证**
   - 所有Webhook事件必须通过签名验证 ✅
   - 防止恶意请求伪造支付成功事件

3. **防重复处理**
   - 通过order_id/session_id去重 ✅
   - 避免同一订单重复创建订阅

## 🌍 国际化支持

### 价格对照表
| 套餐类型 | 国内价格(CNY) | 国际价格(USD) | 汇率比例 |
|---------|--------------|--------------|---------|
| 月度会员 | ¥29 | $4.99 | ~1:5.8 |
| 年度会员 | ¥199 | $39.99 | ~1:5.0 |
| 终身会员 | ¥599 | $89.99 | ~1:6.7 |

### 用户体验优化
1. **自动货币检测**（可选）
   - 根据用户IP或系统语言自动推荐支付方式
   - 中国大陆用户默认选择zpay
   - 海外用户默认选择Stripe

2. **支付说明**
   - 国内支付：支持支付宝、微信支付
   - 国际支付：支持Visa、Mastercard、American Express等

## 📊 数据流程图

```
用户购买
    ↓
选择套餐(plan_type) + 选择支付方式(pay_type)
    ↓
    ├─ alipay/wxpay
    │   ↓
    │   POST /api/create-payment (zpay)
    │   ↓
    │   返回 payment_url
    │   ↓
    │   浏览器打开支付页面
    │   ↓
    │   客户端轮询支付状态
    │   ↓
    │   检测到支付成功 → 刷新用户信息
    │
    └─ stripe
        ↓
        POST /api/stripe-create-checkout
        ↓
        返回 checkout_url
        ↓
        浏览器打开Stripe支付页面
        ↓
        用户完成支付
        ↓
        Stripe发送Webhook → /api/stripe-webhook
        ↓
        自动创建订阅、升级用户、更新配额
        ↓
        用户刷新应用看到会员权益激活
```

## 🧪 测试计划

### 国内支付测试
- [ ] 支付宝支付流程
- [ ] 微信支付流程
- [ ] 支付状态轮询
- [ ] 支付成功后用户升级

### 国际支付测试
- [ ] Stripe Checkout页面加载
- [ ] 测试卡支付（4242 4242 4242 4242）
- [ ] Webhook事件接收
- [ ] 数据库自动更新
- [ ] 用户升级验证

### 边界情况测试
- [ ] 重复支付（同一订单）
- [ ] 网络中断时的处理
- [ ] 支付超时场景
- [ ] 取消支付场景

## 📈 监控指标

### 关键指标
1. **支付成功率**
   - zpay成功率 vs Stripe成功率
   - 各套餐的转化率

2. **支付方式分布**
   - 支付宝 vs 微信 vs Stripe 使用比例
   - 地域分布（国内 vs 海外）

3. **Webhook处理**
   - Webhook接收成功率
   - 平均处理时间
   - 错误日志

## 🚀 部署流程

1. **环境变量配置**（Vercel）
   - STRIPE_SECRET_KEY ✅
   - STRIPE_PUBLISHABLE_KEY ✅
   - STRIPE_WEBHOOK_SECRET ✅
   - STRIPE_PRICE_MONTHLY ✅
   - STRIPE_PRICE_YEARLY ✅
   - STRIPE_PRICE_LIFETIME ✅

2. **代码部署**
   - 更新 membership_ui.py（添加Stripe选项）
   - 更新 auth_client.py（添加Stripe API调用）
   - 提交代码到Git
   - Vercel自动部署

3. **测试验证**
   - 在开发环境测试完整流程
   - 使用Stripe测试卡验证支付
   - 检查数据库记录完整性

## 📞 用户支持

### 常见问题
1. **Q: 国际支付和国内支付有什么区别？**
   A: 国际支付使用Stripe，支持Visa/Mastercard等国际信用卡，价格为美元。国内支付使用支付宝/微信，价格为人民币。

2. **Q: 支付成功后会员权益多久激活？**
   A: 国际支付（Stripe）为即时激活，支付成功后立即生效。国内支付通常在1-2分钟内激活。

3. **Q: 可以使用国际信用卡在国内支付吗？**
   A: 建议使用"国际支付(Stripe)"选项，支持所有国际信用卡。

## 🔄 未来优化

1. **智能支付推荐**
   - 根据用户地理位置自动推荐最优支付方式
   - 显示每种支付方式的优惠信息

2. **优惠券系统**
   - Stripe支持promotion codes
   - 可以在Checkout时输入优惠码

3. **订阅管理**
   - 用户可以在应用内查看订阅状态
   - Stripe订阅用户可以在Stripe Customer Portal自助管理

4. **多货币支持**
   - 扩展到更多国家和地区
   - 支持欧元、日元等其他货币
