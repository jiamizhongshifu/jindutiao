# 注册验证完成但弹窗不关闭问题修复

## 问题现象

用户点击了Gmail中的验证邮件，但应用中的验证弹窗仍然显示"⏳ 等待邮箱验证..."，不会自动关闭和登录。

## 根本原因

代码从 `public.users` 表查询 `email_verified` 字段来判断验证状态，但这个字段需要通过**数据库触发器**从 `auth.users.email_confirmed_at` 自动同步。

当前状态：
- ✅ 用户在 Supabase Auth 中已验证（`auth.users.email_confirmed_at` 已更新）
- ❌ `public.users.email_verified` 字段未同步（触发器未配置）
- ❌ 后端查询返回 `verified: false`

## 解决方案：配置Supabase数据库触发器

### 步骤1：登录Supabase Dashboard

访问 [Supabase Dashboard](https://supabase.com/dashboard) → 选择你的项目 → 左侧菜单 **SQL Editor**

### 步骤2：创建同步函数

在SQL Editor中执行以下SQL：

```sql
-- 创建函数：当auth.users的email_confirmed_at更新时，同步到public.users.email_verified
CREATE OR REPLACE FUNCTION sync_email_verification()
RETURNS TRIGGER AS $$
BEGIN
  -- 当email_confirmed_at字段从NULL变为非NULL时（即邮箱验证完成）
  IF OLD.email_confirmed_at IS NULL AND NEW.email_confirmed_at IS NOT NULL THEN
    -- 更新public.users表的email_verified和status字段
    UPDATE public.users
    SET
      email_verified = TRUE,
      status = 'active',
      updated_at = NOW()
    WHERE id = NEW.id;

    RAISE NOTICE 'User % email verified, synced to public.users', NEW.email;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 步骤3：创建触发器

```sql
-- 创建触发器：监听auth.users表的更新
DROP TRIGGER IF EXISTS on_auth_user_email_verified ON auth.users;

CREATE TRIGGER on_auth_user_email_verified
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION sync_email_verification();
```

### 步骤4：验证触发器是否创建成功

```sql
-- 查询触发器列表，确认触发器已创建
SELECT
  trigger_name,
  event_manipulation,
  event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'auth'
  AND trigger_name = 'on_auth_user_email_verified';
```

应该返回：
```
trigger_name                  | event_manipulation | event_object_table
------------------------------|--------------------|-----------------
on_auth_user_email_verified  | UPDATE             | users
```

### 步骤5（可选）：手动修复已验证但未同步的用户

如果有用户已经验证了邮箱，但 `public.users` 表未同步，执行以下SQL手动修复：

```sql
-- 查询已验证但未同步的用户
SELECT
  au.id,
  au.email,
  au.email_confirmed_at,
  pu.email_verified
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE au.email_confirmed_at IS NOT NULL
  AND (pu.email_verified IS NULL OR pu.email_verified = FALSE);

-- 如果有未同步的用户，执行同步
UPDATE public.users pu
SET
  email_verified = TRUE,
  status = 'active',
  updated_at = NOW()
FROM auth.users au
WHERE pu.id = au.id
  AND au.email_confirmed_at IS NOT NULL
  AND (pu.email_verified IS NULL OR pu.email_verified = FALSE);
```

## 测试验证

1. 使用新邮箱注册一个测试账号
2. 点击验证邮件
3. 观察应用中的验证弹窗是否自动关闭并登录

如果成功，控制台应该显示：
```
[EMAIL-VERIFICATION] 验证成功！邮箱: test@example.com
[EMAIL-VERIFICATION] 自动登录成功！
```

## 推荐方案

**✅ 使用数据库触发器**（上述步骤1-5）

**优点**：
- 自动同步，无需手动维护
- 性能好（只在验证时触发一次）
- 安全（不需要暴露Service Role Key）
- 可维护性强

**缺点**：
- 需要一次性配置

## 相关文件

- `api/auth_manager.py:220-260` - 验证状态检查逻辑
- `gaiya/ui/email_verification_dialog.py:196-246` - 客户端轮询逻辑

## 参考文档

- [Supabase Database Triggers](https://supabase.com/docs/guides/database/postgres/triggers)
- [Supabase Auth Schema](https://supabase.com/docs/guides/auth/auth-schema)
