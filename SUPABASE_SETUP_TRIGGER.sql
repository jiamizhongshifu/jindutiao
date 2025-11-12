-- ============================================
-- Supabase邮箱验证同步触发器配置
-- 用途：自动同步 auth.users.email_confirmed_at 到 public.users.email_verified
-- ============================================

-- 步骤1：创建同步函数
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

-- 步骤2：创建触发器
DROP TRIGGER IF EXISTS on_auth_user_email_verified ON auth.users;

CREATE TRIGGER on_auth_user_email_verified
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION sync_email_verification();

-- 步骤3：手动修复已验证但未同步的用户
UPDATE public.users pu
SET
  email_verified = TRUE,
  status = 'active',
  updated_at = NOW()
FROM auth.users au
WHERE pu.id = au.id
  AND au.email_confirmed_at IS NOT NULL
  AND (pu.email_verified IS NULL OR pu.email_verified = FALSE);

-- 步骤4：验证触发器是否创建成功
SELECT
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'auth'
  AND trigger_name = 'on_auth_user_email_verified';
