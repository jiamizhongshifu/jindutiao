# 阶段1执行指南：提高核心模块覆盖率

> **目标**: 在2-3天内将核心模块覆盖率提升至60-70%
> **当前状态**: auth(44%), subscription(41%), quota(54%), zpay(0%)

---

## 📋 执行检查清单

### Day 1: auth_manager.py (44% → 70%)

**上午任务** (4小时):
- [ ] 1. 运行覆盖率报告，导出未覆盖函数列表
- [ ] 2. 编写会话管理测试（5个测试用例）
- [ ] 3. 编写管理员功能测试（3个测试用例）
- [ ] 4. 运行测试验证（预期11/11通过）

**下午任务** (4小时):
- [ ] 5. 编写边界条件测试（4个测试用例）
- [ ] 6. 编写错误恢复测试（3个测试用例）
- [ ] 7. 编写安全加固测试（3个测试用例）
- [ ] 8. 最终验证：覆盖率≥70%

**预期产出**: +18个测试，覆盖率从44%提升到70%

---

### Day 2上午: subscription_manager.py (41% → 65%)

**任务** (4小时):
- [ ] 1. 编写订阅升级/降级测试（3个测试）
- [ ] 2. 编写订阅续费测试（3个测试）
- [ ] 3. 编写退款和取消测试（3个测试）
- [ ] 4. 编写订阅状态转换测试（3个测试）
- [ ] 5. 编写批量操作测试（3个测试）
- [ ] 6. 验证覆盖率≥65%

**预期产出**: +15个测试

---

### Day 2下午: quota_manager.py (54% → 70%)

**任务** (3小时):
- [ ] 1. 编写配额消耗测试（3个测试）
- [ ] 2. 编写配额重置逻辑测试（3个测试）
- [ ] 3. 编写配额历史记录测试（2个测试）
- [ ] 4. 编写并发安全测试（2个测试）
- [ ] 5. 验证覆盖率≥70%

**预期产出**: +10个测试

---

### Day 3: zpay_manager.py (0% → 60%)

**全天任务** (8小时):
- [ ] 1. 阅读zpay_manager.py源代码（1小时）
- [ ] 2. 创建测试文件和Mock框架（1小时）
- [ ] 3. 编写支付订单创建测试（4个测试，1小时）
- [ ] 4. 编写支付回调处理测试（4个测试，1.5小时）
- [ ] 5. 编写支付查询测试（3个测试，0.5小时）
- [ ] 6. 编写退款处理测试（4个测试，1小时）
- [ ] 7. 编写安全测试（5个测试，1.5小时）
- [ ] 8. 编写支付对账测试（5个测试，1小时）
- [ ] 9. 最终验证：覆盖率≥60%

**预期产出**: 新建test_zpay_manager.py，25个测试

---

## 🔍 步骤1: 识别未覆盖代码

**运行以下命令生成详细覆盖率报告**:

```bash
# 生成HTML覆盖率报告
python -m pytest tests/unit/test_auth_manager.py --cov=api/auth_manager.py --cov-report=html --cov-report=term-missing

# 查看未覆盖的行号
# 输出示例：
# api/auth_manager.py:125-145    Missing
# api/auth_manager.py:200-210    Missing
```

**打开HTML报告**:
```bash
start htmlcov/index.html  # Windows
# 查看红色标记的未覆盖代码
```

---

## 📝 测试用例编写模板

### 模板1: 会话管理测试

```python
class TestSessionManagement:
    """测试会话管理功能"""

    def test_refresh_session_success(self, auth_manager, mock_supabase_client):
        """测试成功刷新会话"""
        # Arrange: 准备Mock数据
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.access_token = "new_access_token"
        mock_response.session.refresh_token = "new_refresh_token"
        mock_supabase_client.auth.refresh_session.return_value = mock_response

        # Act: 执行刷新
        result = auth_manager.refresh_session("old_refresh_token")

        # Assert: 验证结果
        assert result["success"] is True
        assert result["access_token"] == "new_access_token"
        mock_supabase_client.auth.refresh_session.assert_called_once()

    def test_refresh_session_expired_token(self, auth_manager, mock_supabase_client):
        """测试刷新过期token"""
        # Arrange
        mock_supabase_client.auth.refresh_session.side_effect = Exception("Token expired")

        # Act
        result = auth_manager.refresh_session("expired_token")

        # Assert
        assert result["success"] is False
        assert "expired" in result["error"].lower()
```

---

### 模板2: 订阅升级测试

```python
class TestSubscriptionUpgrade:
    """测试订阅升级功能"""

    def test_upgrade_from_monthly_to_yearly(self, subscription_manager, mock_supabase_client):
        """测试从月度升级到年度订阅"""
        # Arrange: 用户当前有月度订阅（还剩15天）
        current_subscription = {
            "id": "sub-123",
            "plan_type": "pro_monthly",
            "expires_at": (datetime.now() + timedelta(days=15)).isoformat()
        }
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[current_subscription]
        )

        # Mock升级后的订阅
        upgraded_sub = Mock()
        upgraded_sub.data = [{"id": "sub-456", "plan_type": "pro_yearly"}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = upgraded_sub

        # Act: 执行升级
        result = subscription_manager.upgrade_subscription(
            user_id="user-123",
            new_plan="pro_yearly",
            payment_id="pay-upgrade"
        )

        # Assert: 验证升级成功
        assert result["success"] is True
        assert result["plan_type"] == "pro_yearly"

        # 验证旧订阅被取消
        cancel_call = mock_supabase_client.table.return_value.update.call_args
        assert cancel_call[0][0]["status"] == "cancelled"

        # 验证剩余天数折算（可选：高级测试）
        # 15天月度 ≈ 0.04年，升级后应延长过期时间
```

---

### 模板3: 并发安全测试

```python
class TestConcurrencySafety:
    """测试并发场景下的数据一致性"""

    def test_concurrent_quota_consumption(self, quota_manager, mock_supabase_client):
        """测试并发消耗配额时的原子性"""
        import threading

        # Arrange: 用户有3次配额
        user_quota = {
            "user_id": "user-123",
            "daily_plan_used": 0,
            "daily_plan_total": 3
        }
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[user_quota]
        )

        # 模拟数据库原子更新
        consumed_count = [0]  # 模拟数据库计数器
        lock = threading.Lock()

        def mock_consume():
            with lock:
                if consumed_count[0] < 3:
                    consumed_count[0] += 1
                    return Mock(data=[{"daily_plan_used": consumed_count[0]}])
                else:
                    raise Exception("Quota exceeded")

        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = mock_consume

        # Act: 10个线程同时尝试消耗配额
        threads = []
        results = []

        def consume():
            try:
                result = quota_manager.consume_quota("user-123", "daily_plan")
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        for _ in range(10):
            t = threading.Thread(target=consume)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Assert: 只有3次成功，7次失败
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if "error" in r or not r.get("success")]

        assert len(successful) == 3  # 仅3次成功
        assert len(failed) == 7       # 7次失败（配额不足）
```

---

### 模板4: 支付安全测试

```python
class TestPaymentSecurity:
    """测试支付相关的安全性"""

    def test_payment_signature_tampering_detection(self, zpay_manager):
        """测试支付签名篡改检测"""
        # Arrange: 合法的支付回调数据
        callback_data = {
            "out_trade_no": "ORDER123",
            "total_amount": "29.00",
            "trade_status": "TRADE_SUCCESS",
            "sign": "valid_signature_here"
        }

        # Act: 篡改金额后验证签名
        tampered_data = callback_data.copy()
        tampered_data["total_amount"] = "1.00"  # 篡改金额

        result = zpay_manager.verify_payment_callback(tampered_data)

        # Assert: 签名验证应失败
        assert result["success"] is False
        assert "签名验证失败" in result["error"]

    def test_payment_replay_attack_prevention(self, zpay_manager, mock_supabase_client):
        """测试支付重放攻击防御"""
        # Arrange: 已处理过的支付回调
        callback_data = {
            "out_trade_no": "ORDER123",
            "total_amount": "29.00",
            "trade_status": "TRADE_SUCCESS"
        }

        # Mock数据库查询：订单已处理
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"status": "paid", "processed": True}]
        )

        # Act: 重复发送相同回调
        result = zpay_manager.handle_payment_callback(callback_data)

        # Assert: 应拒绝重复处理
        assert result["success"] is False
        assert "重复" in result["error"] or "已处理" in result["error"]

        # 验证数据库未被二次更新
        update_calls = mock_supabase_client.table.return_value.update.call_count
        assert update_calls == 0
```

---

## 🔧 调试技巧

### 1. 查看Mock调用历史

```python
# 查看某个Mock方法被调用了多少次
print(mock_supabase_client.table.call_count)

# 查看调用参数
print(mock_supabase_client.table.call_args_list)

# 重置Mock状态
mock_supabase_client.reset_mock()
```

### 2. 使用pytest断点调试

```python
def test_complex_scenario():
    # ...
    import pdb; pdb.set_trace()  # 设置断点
    result = some_function()
```

### 3. 输出覆盖率到文件

```bash
# 生成覆盖率报告到coverage.txt
python -m pytest tests/unit/ --cov=api --cov-report=term-missing > coverage.txt
```

---

## ✅ 每日验收标准

### Day 1结束前:
```bash
# 运行auth_manager测试
python -m pytest tests/unit/test_auth_manager.py -v

# 检查覆盖率（应≥70%）
python -m pytest tests/unit/test_auth_manager.py --cov=api/auth_manager.py --cov-report=term

# 预期输出：
# api/auth_manager.py    320    96    70%
```

### Day 2结束前:
```bash
# 运行subscription和quota测试
python -m pytest tests/unit/test_subscription_manager.py tests/unit/test_quota_manager.py -v

# 检查覆盖率
python -m pytest tests/unit/ --cov=api/subscription_manager.py --cov=api/quota_manager.py --cov-report=term

# 预期：
# subscription_manager.py    147    51    65%
# quota_manager.py          108    32    70%
```

### Day 3结束前:
```bash
# 运行zpay_manager测试
python -m pytest tests/unit/test_zpay_manager.py -v

# 检查覆盖率（应≥60%）
python -m pytest tests/unit/test_zpay_manager.py --cov=api/zpay_manager.py --cov-report=term

# 预期：
# zpay_manager.py    117    47    60%
```

### 最终验收（Day 3结束）:
```bash
# 运行所有单元测试
python -m pytest tests/unit/ -v

# 预期：130+ passed（99原有 + 43新增）

# 整体覆盖率
python -m pytest tests/unit/ --cov=api --cov-report=term

# 预期：
# TOTAL    2200    1400    36%  （从16%提升到36%）
```

---

## 🚀 立即开始

**第一步：运行基准测试**
```bash
cd C:\Users\Sats\Downloads\jindutiao
python -m pytest tests/unit/ --cov=api --cov-report=html --cov-report=term-missing
```

**第二步：打开覆盖率报告**
```bash
start htmlcov/index.html
# 重点查看auth_manager.py的红色（未覆盖）代码
```

**第三步：开始编写第一个测试**
```bash
# 打开测试文件
code tests/unit/test_auth_manager.py

# 添加TestSessionManagement类（参考上面的模板）
```

**GO! GO! GO!** 🎯
