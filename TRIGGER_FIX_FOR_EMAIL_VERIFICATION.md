# Email Verification Trigger 修复方案

**问题诊断时间：** 2025-11-11
**问题现象：** 用户点击验证链接后，看到成功页面，但 EmailVerificationDialog 不关闭，轮询显示 `verified: False`

---

## 🔍 根本原因分析

### 问题链条：

```
1. 用户点击验证链接
   ↓
2. Supabase 更新 auth.users.email_confirmed_at ✅
   ↓
3. Trigger 触发，执行 UPDATE public.users WHERE id = NEW.id
   ↓
4. ❌ 但是 public.users 表中没有这条记录！
   ↓
5. UPDATE 不会创建记录，什么都没发生
   ↓
6. 轮询 API 查询 public.users.email_verified 仍然是 FALSE
   ↓
7. EmailVerificationDialog 永远等待 ❌
```

### 为什么 public.users 中没有记录？

在 `api/auth_manager.py:82-87` 中：

```python
try:
    db_response = self.client.table("users").insert(user_data).execute()
    print(f"[AUTH-SIGNUP] User record created in database", file=sys.stderr)
except Exception as db_error:
    print(f"[AUTH-SIGNUP] Warning: Failed to create user record (will retry after verification): {db_error}", file=sys.stderr)
    # 继续，因为Auth用户已创建成功  ← 这里静默忽略了失败！
```

**场景：用户 `drmrzhong@gmail.com` 多次注册测试**

1. 第一次注册：两个表都创建成功
2. 后续注册：
   - `auth.users` 已存在（Supabase可能更新或返回已存在用户）
   - `public.users.insert()` 失败（ID或email唯一约束冲突）
   - 异常被捕获，静默忽略
3. 结果：
   - `auth.users` 有记录（可能是新的user_id）
   - `public.users` 有旧记录（旧的user_id）
   - **两个表的ID不匹配！**

---

## ✅ 解决方案

### 方案1：修改 Trigger 使用 INSERT ON CONFLICT（推荐）

**优势：**
- 如果记录不存在，自动创建
- 如果记录存在，更新
- 健壮性最高

**SQL：**

```sql
-- 修改触发器函数，使用 UPSERT 逻辑
CREATE OR REPLACE FUNCTION public.handle_email_verification()
RETURNS TRIGGER AS $$
BEGIN
  -- 当 auth.users 的 email_confirmed_at 从 NULL 变为非 NULL 时
  IF NEW.email_confirmed_at IS NOT NULL AND
     (OLD.email_confirmed_at IS NULL OR OLD.email_confirmed_at <> NEW.email_confirmed_at) THEN

    -- 使用 INSERT ON CONFLICT 实现 UPSERT
    INSERT INTO public.users (
      id,
      email,
      username,
      email_verified,
      status,
      user_tier,
      auth_provider,
      created_at,
      updated_at
    )
    VALUES (
      NEW.id,
      NEW.email,
      COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
      TRUE,
      'active',
      'free',
      'email',
      NOW(),
      NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
      email_verified = TRUE,
      status = 'active',
      updated_at = NOW();

    RAISE NOTICE 'Email verified for user: % (ID: %)', NEW.email, NEW.id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 重新创建触发器（确保使用新函数）
DROP TRIGGER IF EXISTS on_email_confirmed ON auth.users;

CREATE TRIGGER on_email_confirmed
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_email_verification();
```

**测试方法：**

在 Supabase SQL Editor 中手动触发：

```sql
-- 1. 查看当前状态
SELECT id, email, email_verified FROM public.users WHERE email = 'drmrzhong@gmail.com';

-- 2. 手动设置 auth.users 的 email_confirmed_at（模拟验证）
UPDATE auth.users
SET email_confirmed_at = NOW()
WHERE email = 'drmrzhong@gmail.com';

-- 3. 再次查看 public.users（应该自动更新了）
SELECT id, email, email_verified FROM public.users WHERE email = 'drmrzhong@gmail.com';
```

---

### 方案2：修改注册代码使用 UPSERT

**修改 `api/auth_manager.py:82-87`：**

```python
# 2. 创建或更新用户记录
user_data = {
    "id": auth_response.user.id,
    "email": email,
    "username": username or email.split("@")[0],
    "user_tier": "free",
    "auth_provider": "email",
    "email_verified": False,  # 待邮箱验证
    "status": "pending_verification"  # 待验证状态
}

try:
    # 使用 upsert 代替 insert，避免ID冲突
    db_response = self.client.table("users").upsert(
        user_data,
        on_conflict="id"  # 如果ID冲突，则更新
    ).execute()
    print(f"[AUTH-SIGNUP] User record created/updated in database", file=sys.stderr)
except Exception as db_error:
    print(f"[AUTH-SIGNUP] Warning: Failed to create user record: {db_error}", file=sys.stderr)
    # 继续，因为Auth用户已创建成功
```

---

### 方案3：清理旧数据重新测试（临时）

如果想快速验证修复，可以先清理旧数据：

```sql
-- 在 Supabase Dashboard 中执行

-- 1. 删除 public.users 中的旧记录
DELETE FROM public.users WHERE email = 'drmrzhong@gmail.com';

-- 2. 删除 auth.users 中的旧记录（需要在 Authentication → Users 界面手动删除）

-- 3. 重新注册测试
```

---

## 🚀 推荐实施步骤

1. **立即修复 Trigger（方案1）**
   - 在 Supabase SQL Editor 中执行新的 Trigger SQL
   - 这样即使旧用户也能被正确处理

2. **修改注册代码（方案2）**
   - 避免未来再次出现ID冲突
   - 提高代码健壮性

3. **测试验证**
   - 使用 `drmrzhong@gmail.com` 重新注册
   - 或者使用全新的邮箱测试

4. **添加调试日志**
   - 在 `check_email_verification` 中添加更详细的日志
   - 确认 `public.users` 表中的数据状态

---

## 📋 验证清单

执行修复后，验证以下内容：

- [ ] Trigger SQL 已在 Supabase 中执行
- [ ] auth_manager.py 已修改为使用 upsert
- [ ] 清理了旧的测试用户数据
- [ ] 重新注册测试
- [ ] 收到验证邮件
- [ ] 点击验证链接，看到成功页面
- [ ] 返回应用，EmailVerificationDialog 自动关闭
- [ ] 应用显示已登录状态

---

## 🎯 期望结果

修复后的完整流程：

```
1. 用户注册 → 两个表都创建记录（使用 upsert）
   ↓
2. 用户点击验证链接 → auth.users.email_confirmed_at 更新
   ↓
3. Trigger 触发 → INSERT ON CONFLICT 创建或更新 public.users
   ↓
4. 轮询 API 检测到 email_verified = TRUE
   ↓
5. EmailVerificationDialog 显示成功并自动登录
   ↓
6. 用户愉快地使用应用 🎉
```

---

**修复完成时间：** 待执行
**状态：** ⏳ 等待用户在 Supabase Dashboard 执行 Trigger SQL
