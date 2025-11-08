-- ============================================================================
-- GaiYa 盖亚每日进度条 - Supabase RLS 安全策略配置脚本
-- ============================================================================
--
-- 用途：配置Row Level Security (RLS)策略，确保用户数据安全
-- 执行方式：在Supabase Dashboard → SQL Editor 中直接粘贴执行
-- 执行时间：约30秒
--
-- 注意事项：
--   1. 本脚本假设表已存在，仅创建RLS策略
--   2. 如果策略已存在，会先删除旧策略再创建新策略
--   3. 执行前请确认您有足够的权限
--   4. 建议先在测试环境执行，验证无误后再在生产环境执行
--
-- ============================================================================

-- ============================================================================
-- 第一步：启用所有表的 RLS
-- ============================================================================

-- 为 users 表启用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 为 user_quotas 表启用 RLS
ALTER TABLE user_quotas ENABLE ROW LEVEL SECURITY;

-- 为 subscriptions 表启用 RLS
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- 为 payments 表启用 RLS（如果表存在）
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'payments') THEN
        ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;

-- ============================================================================
-- 第二步：删除旧策略（如果存在，避免重复执行时报错）
-- ============================================================================

-- users 表旧策略
DROP POLICY IF EXISTS "Users can view own data" ON users;
DROP POLICY IF EXISTS "Users can update own data" ON users;
DROP POLICY IF EXISTS "Users can insert own data" ON users;

-- user_quotas 表旧策略
DROP POLICY IF EXISTS "Authenticated users can view own quota" ON user_quotas;
DROP POLICY IF EXISTS "System can update quotas" ON user_quotas;
DROP POLICY IF EXISTS "API can insert quotas" ON user_quotas;

-- subscriptions 表旧策略
DROP POLICY IF EXISTS "Users can view own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "No direct subscription updates" ON subscriptions;
DROP POLICY IF EXISTS "API can insert subscriptions" ON subscriptions;

-- payments 表旧策略
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'payments') THEN
        DROP POLICY IF EXISTS "Users can view own payments" ON payments;
        DROP POLICY IF EXISTS "API can insert payments" ON payments;
    END IF;
END $$;

-- ============================================================================
-- 第三步：创建 users 表的 RLS 策略
-- ============================================================================

-- 策略1：用户只能查看自己的数据
-- 注意：两边都转换为 TEXT 确保类型匹配
CREATE POLICY "Users can view own data"
ON users
FOR SELECT
USING (id::text = auth.uid()::text);

-- 策略2：用户只能更新自己的数据
CREATE POLICY "Users can update own data"
ON users
FOR UPDATE
USING (id::text = auth.uid()::text);

-- 策略3：允许用户注册时插入自己的数据
-- 注意：这里使用 auth.uid() 确保只能插入自己的记录
CREATE POLICY "Users can insert own data"
ON users
FOR INSERT
WITH CHECK (id::text = auth.uid()::text);

-- ============================================================================
-- 第四步：创建 user_quotas 表的 RLS 策略
-- ============================================================================

-- 策略1：认证用户可以查看自己的配额
-- 重要：两边都转换为 TEXT 确保类型匹配
CREATE POLICY "Authenticated users can view own quota"
ON user_quotas
FOR SELECT
USING (user_id::text = auth.uid()::text);

-- 策略2：禁止客户端直接更新配额（仅API通过Service Role Key更新）
-- USING (false) 表示任何客户端请求都会被拒绝
-- 只有使用 Service Role Key 的服务端代码才能更新
CREATE POLICY "System can update quotas"
ON user_quotas
FOR UPDATE
USING (false);

-- 策略3：允许API创建新用户的配额记录
-- 这在用户首次注册时需要
CREATE POLICY "API can insert quotas"
ON user_quotas
FOR INSERT
WITH CHECK (user_id::text = auth.uid()::text);

-- ============================================================================
-- 第五步：创建 subscriptions 表的 RLS 策略
-- ============================================================================

-- 策略1：用户可以查看自己的订阅记录
CREATE POLICY "Users can view own subscriptions"
ON subscriptions
FOR SELECT
USING (user_id::text = auth.uid()::text);

-- 策略2：禁止客户端直接修改订阅（仅通过支付回调API）
-- 订阅状态的改变必须通过支付回调验证后由API修改
CREATE POLICY "No direct subscription updates"
ON subscriptions
FOR UPDATE
USING (false);

-- 策略3：允许API创建订阅记录（支付成功后）
CREATE POLICY "API can insert subscriptions"
ON subscriptions
FOR INSERT
WITH CHECK (user_id::text = auth.uid()::text);

-- ============================================================================
-- 第六步：创建 payments 表的 RLS 策略（如果表存在）
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'payments') THEN
        -- 策略1：用户可以查看自己的支付记录
        EXECUTE 'CREATE POLICY "Users can view own payments"
                ON payments
                FOR SELECT
                USING (user_id::text = auth.uid()::text)';

        -- 策略2：允许API插入支付记录
        EXECUTE 'CREATE POLICY "API can insert payments"
                ON payments
                FOR INSERT
                WITH CHECK (user_id::text = auth.uid()::text)';
    END IF;
END $$;

-- ============================================================================
-- 第七步：验证配置（可选，建议执行）
-- ============================================================================

-- 查看所有表的 RLS 启用状态
SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('users', 'user_quotas', 'subscriptions', 'payments')
ORDER BY tablename;

-- 查看所有已创建的策略
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
    AND tablename IN ('users', 'user_quotas', 'subscriptions', 'payments')
ORDER BY tablename, policyname;

-- ============================================================================
-- 配置完成！
-- ============================================================================

-- 输出成功消息
DO $$
BEGIN
    RAISE NOTICE '✅ RLS策略配置完成！';
    RAISE NOTICE '';
    RAISE NOTICE '已配置的安全策略：';
    RAISE NOTICE '  - users 表：用户只能查看/更新自己的数据';
    RAISE NOTICE '  - user_quotas 表：用户只能查看配额，更新需通过API';
    RAISE NOTICE '  - subscriptions 表：用户只能查看订阅，修改需通过API';
    RAISE NOTICE '  - payments 表：用户只能查看支付记录（如果表存在）';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  下一步：请在 config_gui.py 中测试以下功能：';
    RAISE NOTICE '  1. 用户登录后能否查看自己的配额';
    RAISE NOTICE '  2. 用户登录后能否查看自己的订阅';
    RAISE NOTICE '  3. 用户能否查看其他用户的数据（应该被拒绝）';
END $$;
