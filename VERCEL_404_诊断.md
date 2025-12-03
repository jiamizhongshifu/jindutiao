# Vercel payment-query 404错误诊断

## 🔍 问题现象

从Vercel日志和测试结果看:

1. ✅ **订单创建成功**: `[PAYMENT-CREATE] Order created: GAIYA1764737631885308748`
2. ✅ **支付完成**: 用户在浏览器中看到"支付成功"
3. ❌ **查询订单失败**: `payment-query` API返回 `{"success": false, "error": "订单编号不存在"}`
4. ❌ **大量JSON解析错误**: `[ZPAY-QUERY] Error: Expecting ',' delimiter`

## 🎯 根本原因

**Z-Pay API返回的JSON格式有语法错误!**

从Vercel日志看到的典型错误:
```
[ZPAY-QUERY] Error: Expecting ',' delimiter or ')': line 1 column 186 (char 185)
```

这说明当Z-Pay返回订单数据时,JSON字符串中有格式问题,导致Python `json.loads()` 解析失败。

### 可能的原因:

1. **param字段包含未转义的JSON** - 我们在创建订单时传入:
   ```python
   param=json.dumps({
       "user_id": "xxx",
       "plan_type": "pro_monthly"
   })
   ```

   Z-Pay可能把这个JSON字符串直接拼接到返回结果中,导致嵌套JSON格式错误:
   ```json
   {
       "code": 1,
       "param": "{"user_id":"xxx","plan_type":"pro_monthly"}"  // ❌ 引号未转义
   }
   ```

2. **中文字符编码问题** - `name` 字段包含中文 "Pro月度订阅",可能导致编码问题

3. **其他特殊字符** - 订单数据中的某些字段包含特殊字符

## 🔧 解决方案

### 方案1: 修复JSON解析 (临时方案)

在 `zpay_manager.py` 的 `query_order` 方法中,增强错误处理:

```python
try:
    result = response.json()
except json.JSONDecodeError as e:
    # 尝试修复常见的JSON格式问题
    text = response.text
    # 1. 转义未转义的引号
    # 2. 修复其他常见问题
    try:
        result = json.loads(fixed_text)
    except:
        # 如果仍然失败,返回错误
        return {"success": False, "error": "Invalid JSON from Z-Pay"}
```

### 方案2: 简化param参数 (推荐)

不使用JSON格式的param,改用简单的字符串分隔:

```python
# 修改 payment-create-order.py line 147-150
param=f"{user_id}|{plan_type}"  # 使用简单分隔符代替JSON
```

然后在查询时解析:
```python
# 客户端解析param
parts = order.get("param", "").split("|")
if len(parts) == 2:
    user_id, plan_type = parts
```

### 方案3: 使用URL编码 (最安全)

在传入param前进行URL编码:

```python
import urllib.parse

param_data = json.dumps({"user_id": user_id, "plan_type": plan_type})
param=urllib.parse.quote(param_data)
```

查询时解码:
```python
import urllib.parse

param_str = urllib.parse.unquote(order.get("param", ""))
param_data = json.loads(param_str)
```

## 🚨 当前状态

- **你已经支付成功** - ¥0.1已扣款
- **订单存在于Z-Pay系统** - 但查询时JSON解析失败
- **客户端轮询失败** - 无法获取订单状态,所以无法触发会员升级

## ✅ 临时解决方案 - 手动升级

由于你已经支付成功但会员状态未更新,可以使用手动升级脚本:

```bash
python emergency_upgrade.py
```

这个脚本会:
1. 读取你的user_id
2. 直接调用 `/api/manual-upgrade-subscription`
3. 更新你的会员状态

## 🔨 修复建议 (按优先级排序)

### 优先级1: 立即修复 - 使用简单分隔符

**修改文件**: `api/payment-create-order.py`

```python
# Line 147-150 修改为:
param=f"{user_id}|{plan_type}"
```

**修改文件**: `gaiya/ui/membership_ui.py`

```python
# Line 1210-1217 修改为:
param_str = order.get("param", "")
if "|" in param_str:
    parts = param_str.split("|")
    if len(parts) == 2:
        user_id, plan_type = parts
```

### 优先级2: 验证修复效果

修改后:
1. 推送代码到GitHub
2. 等待Vercel部署
3. 重新打包客户端
4. 测试支付流程

### 优先级3: 长期优化

1. 添加Z-Pay API响应的完整日志
2. 实现JSON修复逻辑
3. 添加更多错误处理

## 📝 下一步行动

1. **立即**: 运行 `python emergency_upgrade.py` 手动升级你的账户
2. **短期**: 实施方案2 - 使用简单分隔符代替JSON
3. **测试**: 完成修改后重新测试支付流程
4. **验证**: 确保下次支付能自动升级会员

---

**诊断时间**: 2025-12-03
**订单号**: GAIYA1764737631885308748
**状态**: 已支付但未升级
