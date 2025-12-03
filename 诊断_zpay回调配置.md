# Z-Pay回调未到达问题诊断

## 🔴 问题确认

从您提供的Vercel日志截图可以看到:
- ✅ **订单创建成功**: `[PAYMENT-CREATE] Order created: GAIYA1764727660522308748`
- ❌ **没有回调日志**: 日志中完全没有 `[PAYMENT-NOTIFY]` 相关记录
- ✅ **支付已完成**: 您已经完成了¥0.1的支付

**结论**: Z-Pay的支付回调通知没有发送到Vercel服务器,或者被某处拦截了。

## 🔍 可能的原因

### 1. Z-Pay商户后台未配置通知地址 (最可能)

**问题**: Z-Pay商户后台可能没有配置全局的异步通知地址。

**检查方法**:
1. 登录Z-Pay商户后台: https://zpayz.cn/
2. 进入 **系统设置** 或 **API配置**
3. 查找 **异步通知地址** 或 **回调地址** 设置
4. 应该填写: `https://jindutiao.vercel.app/api/payment-notify`

**注意**: 即使创建订单时传递了 `notify_url` 参数,有些支付平台仍然要求在后台设置全局回调地址。

### 2. 回调URL被Z-Pay防火墙拦截

**问题**: Z-Pay可能无法访问Vercel的域名或IP。

**测试方法**:
```bash
# 从Z-Pay服务器测试访问(如果有SSH访问权限)
curl https://jindutiao.vercel.app/api/payment-notify
```

**排查**:
- 检查Vercel是否有IP白名单限制
- 检查Vercel函数是否有地域限制

### 3. 商户账户状态问题

**问题**: 商户账户可能处于测试模式或受限状态。

**检查**:
- 商户账户是否已实名认证
- 是否处于测试模式(测试模式可能不发送回调)
- 账户余额或状态是否正常

### 4. notify_url参数未正确传递

**问题**: 创建订单时notify_url可能未正确传递给Z-Pay。

**验证**: 让我检查创建订单时的实际参数...

## 🛠️ 立即检查步骤

### 第一步: 验证订单创建时的notify_url

让我创建一个脚本查看Z-Pay实际收到的订单参数:

```python
# 查询订单详情,确认notify_url是否正确
python test_query_zpay_order.py GAIYA1764727660522308748
```

### 第二步: 检查Z-Pay商户后台配置

**必做**:
1. 登录 https://zpayz.cn/
2. 找到 **系统设置** → **API配置**
3. 查看 **异步通知地址** 是否配置
4. 如果为空,设置为: `https://jindutiao.vercel.app/api/payment-notify`

### 第三步: 手动触发回调测试

使用curl模拟Z-Pay发送回调:

```bash
curl "https://jindutiao.vercel.app/api/payment-notify?pid=your_merchant_id_here&out_trade_no=TEST123&trade_no=ZPAY123&money=0.10&trade_status=TRADE_SUCCESS&type=wxpay&name=测试&param={}&sign=test_signature&sign_type=MD5"
```

然后查看Vercel日志是否出现 `[PAYMENT-NOTIFY]`。

## 💡 临时解决方案

在找到根本原因之前,您可以:

### 方案A: 主动查询订单状态

修改客户端轮询逻辑,使用 `payment-query` API主动查询:

```python
# 在gaiya/ui/membership_ui.py的轮询逻辑中
# 如果Z-Pay query返回status=1(已支付),直接更新数据库
```

### 方案B: 手动升级账户

使用我之前创建的脚本:

```bash
python manual_upgrade.py
```

按提示选择套餐类型即可。

## 📋 需要提供的信息

为了进一步诊断,请提供:

1. **Z-Pay商户ID**: 从 `api/zpay_manager.py` 中的 `your_merchant_id_here`
2. **商户后台截图**:
   - 系统设置/API配置页面
   - 异步通知地址配置(如果有)
3. **订单详情**:
   - 在Z-Pay后台查看订单 `GAIYA1764727660522308748`
   - 查看订单的"通知记录"或"回调日志"

## 🎯 下一步行动

### 立即执行:
1. **检查Z-Pay商户后台** - 查看异步通知地址配置
2. **运行下面的诊断脚本** - 查询订单详情

### 如果确认是Z-Pay配置问题:
- 在商户后台设置全局回调URL
- 或联系Z-Pay技术支持

### 如果是其他原因:
- 我可以实现主动查询方案(客户端定期查询订单状态)
- 修改为支付完成后立即查询一次状态
