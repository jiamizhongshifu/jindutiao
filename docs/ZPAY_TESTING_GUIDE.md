# Zpay支付测试指南

本指南详细说明如何测试Zpay支付回调和订阅升级功能。

---

## 📋 目录

1. [测试环境配置](#测试环境配置)
2. [方案1: Mock支付测试（推荐）](#方案1-mock支付测试推荐)
3. [方案2: 0.01元真实支付测试](#方案2-001元真实支付测试)
4. [常见问题](#常见问题)

---

## 测试环境配置

### 1. 设置环境变量

编辑 `.env` 文件，添加或修改以下配置：

```bash
# 环境设置（必须）
ENVIRONMENT=development

# Zpay配置（已有）
ZPAY_PID=2025040215385823
ZPAY_PKEY=Ltb8ZL7kuFg7ZgtnIbuIpJ350FoTXdqu

# Zpay调试模式（可选，启用后会输出详细日志）
ZPAY_DEBUG_MODE=true

# Supabase配置（必须）
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 2. 安装依赖

```bash
# 安装Vercel CLI（如果没有）
npm install -g vercel

# 安装Python依赖
pip install requests
```

### 3. 启动本地服务

```bash
# 在项目根目录运行
vercel dev
```

服务启动后，应该看到类似输出：
```
Ready! Available at http://localhost:3000
```

---

## 方案1: Mock支付测试（推荐）

**优点：**
- ✅ **完全免费**，不产生任何费用
- ✅ 快速测试订阅升级逻辑
- ✅ 可以反复测试各种场景
- ✅ 无需等待真实支付回调

**适用场景：**
- 开发阶段快速验证逻辑
- 测试不同订阅类型的升级
- 测试支付失败的错误处理

### 使用方法

#### 方法A: 使用Python测试脚本（推荐）

```bash
# 1. 测试Pro月度订阅
python test_zpay_mock.py

# 2. 测试Pro年度订阅
python test_zpay_mock.py --plan pro_yearly

# 3. 测试终身会员
python test_zpay_mock.py --plan lifetime

# 4. 测试支付失败场景
python test_zpay_mock.py --scenario failed

# 5. 测试指定用户
python test_zpay_mock.py --user YOUR_USER_ID --plan pro_monthly
```

**预期输出示例：**

```
============================================================
🧪 Zpay Mock Payment Test
============================================================
📤 发送请求到: http://localhost:3000/api/test-zpay-mock-callback
📦 请求参数:
{
  "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
  "plan_type": "pro_monthly",
  "scenario": "success"
}

📨 响应状态码: 200

✅ Mock支付回调成功！

📊 响应数据:
{
  "status": "success",
  "message": "Mock payment callback processed successfully",
  ...
}

============================================================
✨ 订阅升级成功！
============================================================
用户ID: df15202c-2ff0-4b12-9fc0-a1029d6000a7
订阅类型: pro
支付方式: zpay
交易ID: MOCK_ZPAY_1734668800
到期时间: 2025-01-20T00:00:00

🎉 测试通过！请在GaiYa客户端验证会员状态。
```

#### 方法B: 使用curl命令

```bash
# Pro月度订阅
curl -X POST http://localhost:3000/api/test-zpay-mock-callback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
    "plan_type": "pro_monthly",
    "scenario": "success"
  }'

# Pro年度订阅
curl -X POST http://localhost:3000/api/test-zpay-mock-callback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
    "plan_type": "pro_yearly",
    "scenario": "success"
  }'

# 终身会员
curl -X POST http://localhost:3000/api/test-zpay-mock-callback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",
    "plan_type": "lifetime",
    "scenario": "success"
  }'
```

### 验证结果

#### 1. 检查API响应

确认响应中包含：
```json
{
  "status": "success",
  "upgrade_result": {
    "user_id": "...",
    "tier": "pro",
    "payment_method": "zpay",
    "transaction_id": "MOCK_ZPAY_..."
  }
}
```

#### 2. 检查数据库

登录Supabase控制台，检查 `user_subscriptions` 表：

```sql
SELECT * FROM user_subscriptions
WHERE user_id = 'df15202c-2ff0-4b12-9fc0-a1029d6000a7'
ORDER BY created_at DESC
LIMIT 1;
```

应该看到新插入的订阅记录。

#### 3. 验证客户端

在GaiYa桌面客户端中：
1. 打开配置界面
2. 进入"个人中心"标签
3. 检查会员状态是否显示为 Pro/Lifetime
4. 刷新页面验证数据同步

---

## 方案2: 0.01元真实支付测试

**优点：**
- ✅ 验证完整的支付流程
- ✅ 测试真实的支付网关集成
- ✅ 验证回调签名验证逻辑

**成本：**
- 💰 每次测试约 0.01元（1分钱）

**适用场景：**
- 上线前最终验证
- 测试生产环境配置
- 验证Zpay回调集成

### 配置测试价格

#### 方法A: 临时修改价格配置（推荐）

编辑 `api/config.py`，在 `get_plan_prices()` 方法中添加测试逻辑：

```python
@staticmethod
def get_plan_prices() -> Dict[str, Decimal]:
    """获取订阅计划价格"""

    # ⚠️ 测试模式：使用0.01元测试价格
    if Config.is_development() and os.getenv("ENABLE_TEST_PRICES", "false").lower() == "true":
        return {
            "pro_monthly": Decimal("0.01"),
            "pro_yearly": Decimal("0.01"),
            "lifetime": Decimal("0.01"),
        }

    # 生产价格
    return {
        "pro_monthly": Decimal(os.getenv("PLAN_PRICE_PRO_MONTHLY", "29.0")),
        "pro_yearly": Decimal(os.getenv("PLAN_PRICE_PRO_YEARLY", "199.0")),
        "lifetime": Decimal(os.getenv("PLAN_PRICE_LIFETIME", "1200.0")),
    }
```

然后在 `.env` 中启用：

```bash
ENVIRONMENT=development
ENABLE_TEST_PRICES=true
```

#### 方法B: 使用环境变量（推荐用于Vercel部署）

在 `.env` 中设置：

```bash
PLAN_PRICE_PRO_MONTHLY=0.01
PLAN_PRICE_PRO_YEARLY=0.01
PLAN_PRICE_LIFETIME=0.01
```

### 执行测试

1. **启动本地服务（或使用Vercel部署）**

   ```bash
   vercel dev  # 本地
   # 或访问: https://your-vercel-app.vercel.app
   ```

2. **运行GaiYa客户端**

   ```bash
   python main.py
   # 或运行打包的exe
   ```

3. **触发支付流程**

   - 打开配置界面
   - 进入"个人中心" → "会员中心"
   - 点击"升级会员"
   - 选择Pro月度/年度/终身
   - 点击"立即支付"

4. **完成支付**

   - 浏览器打开支付页面
   - 选择支付宝或微信支付
   - 扫码支付 **0.01元**
   - 等待支付成功回调

5. **验证结果**

   - 支付成功后，页面应该跳转到成功页面
   - GaiYa客户端会员状态应该自动更新
   - 检查Supabase数据库订阅记录

### 测试后清理

**重要：测试完成后，恢复生产价格！**

```bash
# 方法1: 删除.env中的测试价格配置
# PLAN_PRICE_PRO_MONTHLY=0.01  # 删除此行
# PLAN_PRICE_PRO_YEARLY=0.01   # 删除此行
# PLAN_PRICE_LIFETIME=0.01     # 删除此行

# 方法2: 关闭测试价格开关
ENABLE_TEST_PRICES=false

# 方法3: 恢复生产环境
ENVIRONMENT=production
```

---

## 常见问题

### Q1: Mock回调返回403错误

**原因：** 环境变量 `ENVIRONMENT` 设置为 `production`

**解决：**
```bash
# 在.env中设置
ENVIRONMENT=development
```

### Q2: 连接失败 - 无法连接到localhost:3000

**原因：** 本地Vercel服务未启动

**解决：**
```bash
# 确保在项目根目录运行
vercel dev
```

### Q3: 订阅升级失败 - Supabase错误

**原因：** Supabase配置不正确或用户不存在

**解决：**
1. 检查 `.env` 中的 `SUPABASE_URL` 和 `SUPABASE_KEY`
2. 确认用户ID在数据库中存在
3. 检查数据库表权限

### Q4: 真实支付测试后如何退款？

**答：**
- Zpay平台通常支持退款，需要登录商户后台操作
- 由于金额极小（0.01元），通常不需要退款
- 建议使用Mock测试为主，真实支付仅用于最终验证

### Q5: 如何测试不同用户的订阅升级？

**Mock测试：**
```bash
python test_zpay_mock.py --user YOUR_USER_ID_1 --plan pro_monthly
python test_zpay_mock.py --user YOUR_USER_ID_2 --plan pro_yearly
```

**真实支付：**
- 在GaiYa客户端登录不同用户账号
- 每个用户独立完成支付流程

### Q6: 能否在生产环境使用Mock测试？

**不能！** Mock测试端点在生产环境被强制禁用，这是安全设计。

生产环境只能使用真实支付测试（0.01元）。

---

## 测试检查清单

### Mock测试（开发阶段）

- [ ] 环境变量 `ENVIRONMENT=development` 已设置
- [ ] Vercel本地服务已启动 (`vercel dev`)
- [ ] Python测试脚本运行成功
- [ ] API响应状态为 `success`
- [ ] Supabase数据库订阅记录已创建
- [ ] GaiYa客户端会员状态已更新

### 真实支付测试（上线前）

- [ ] 测试价格配置已启用（0.01元）
- [ ] GaiYa客户端成功创建支付订单
- [ ] 支付页面正常打开
- [ ] 支付成功（花费0.01元）
- [ ] 支付回调成功处理
- [ ] 订阅状态正确升级
- [ ] 测试完成后恢复生产价格

---

## 附录：API端点说明

### Mock回调端点

**地址：** `http://localhost:3000/api/test-zpay-mock-callback`

**方法：** POST

**请求体：**
```json
{
  "user_id": "用户ID",
  "plan_type": "pro_monthly|pro_yearly|lifetime",
  "scenario": "success|failed"
}
```

**响应示例：**
```json
{
  "status": "success",
  "message": "Mock payment callback processed successfully",
  "mock_data": {
    "trade_no": "MOCK_ZPAY_1734668800",
    "out_trade_no": "MOCK_1734668800",
    "trade_status": "TRADE_SUCCESS",
    ...
  },
  "upgrade_result": {
    "user_id": "...",
    "tier": "pro",
    "payment_method": "zpay",
    "transaction_id": "MOCK_ZPAY_1734668800",
    "expires_at": "2025-01-20T00:00:00"
  }
}
```

### 真实支付端点

**创建订单：** `POST /api/payment-create-order`

**支付回调：** `POST /api/payment-notify`（由Zpay调用）

**查询订单：** `POST /api/payment-query`

---

## 支持

如有问题，请查看：
- [api/README.md](../api/README.md) - API部署指南
- [SECURITY_FIX_PROGRESS.md](../SECURITY_FIX_PROGRESS.md) - 安全修复记录
- [.env.example](../.env.example) - 环境变量配置示例

**最后更新：** 2024-12-20
