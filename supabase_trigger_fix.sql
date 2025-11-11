-- ============================================================================
-- Email Verification Trigger 修复
-- 解决问题：当 auth.users 更新时，自动创建或更新 public.users 记录
-- ============================================================================

-- 1. 删除旧的触发器函数和触发器（如果存在）
DROP TRIGGER IF EXISTS on_email_confirmed ON auth.users;
DROP FUNCTION IF EXISTS public.handle_email_verification();

-- 2. 创建新的触发器函数（使用 UPSERT 逻辑）
CREATE OR REPLACE FUNCTION public.handle_email_verification()
RETURNS TRIGGER AS $$
BEGIN
  -- 当 auth.users 的 email_confirmed_at 从 NULL 变为非 NULL 时
  IF NEW.email_confirmed_at IS NOT NULL AND
     (OLD.email_confirmed_at IS NULL OR OLD.email_confirmed_at <> NEW.email_confirmed_at) THEN

    -- 使用 INSERT ON CONFLICT 实现 UPSERT
    -- 如果记录不存在，创建新记录；如果存在，更新验证状态
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
      -- 从 Auth 用户元数据中获取 username，如果没有则从邮箱提取
      COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
      TRUE,  -- 邮箱已验证
      'active',  -- 激活状态
      'free',  -- 默认免费用户
      'email',  -- 邮箱认证方式
      NOW(),
      NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
      email_verified = TRUE,
      status = 'active',
      updated_at = NOW();

    -- 记录日志（可在 Supabase Dashboard → Database → Logs 中查看）
    RAISE NOTICE 'Email verified for user: % (ID: %)', NEW.email, NEW.id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. 创建触发器（在 auth.users 表上）
CREATE TRIGGER on_email_confirmed
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_email_verification();

-- ============================================================================
-- 验证测试 SQL（可选，用于检查状态）
-- ============================================================================

-- 注释掉了测试查询，避免执行时报错
-- 如果需要测试，请手动执行以下查询：

/*
-- 查看 auth.users 中的状态
SELECT id::text as user_id, email, email_confirmed_at
FROM auth.users
WHERE email = 'drmrzhong@gmail.com';

-- 查看 public.users 中的状态
SELECT id::text as user_id, email, email_verified, status
FROM public.users
WHERE email = 'drmrzhong@gmail.com';

-- 如果需要手动触发验证（测试用）
UPDATE auth.users
SET email_confirmed_at = NOW()
WHERE email = 'drmrzhong@gmail.com';

-- 再次检查 public.users 是否更新
SELECT id::text as user_id, email, email_verified, status
FROM public.users
WHERE email = 'drmrzhong@gmail.com';
*/
