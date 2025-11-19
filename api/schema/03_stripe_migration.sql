-- GaiYa每日进度条 - Stripe支付支持迁移脚本
-- 创建日期: 2025-11-19
-- 描述: 为支持Stripe海外支付添加必要的字段

-- ============================================================
-- 1. payments表添加Stripe字段
-- ============================================================

-- 添加Stripe相关字段
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS trade_no TEXT,
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
ADD COLUMN IF NOT EXISTS stripe_payment_intent_id TEXT,
ADD COLUMN IF NOT EXISTS plan_type TEXT;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_payments_trade_no ON payments(trade_no);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_customer ON payments(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_subscription ON payments(stripe_subscription_id);

COMMENT ON COLUMN payments.trade_no IS '交易流水号（ZPAY的trade_no或Stripe的subscription_id）';
COMMENT ON COLUMN payments.stripe_customer_id IS 'Stripe客户ID';
COMMENT ON COLUMN payments.stripe_subscription_id IS 'Stripe订阅ID';
COMMENT ON COLUMN payments.stripe_payment_intent_id IS 'Stripe支付意图ID';
COMMENT ON COLUMN payments.plan_type IS '购买的计划类型（pro_monthly/pro_yearly/lifetime）';

-- ============================================================
-- 2. subscriptions表添加Stripe字段
-- ============================================================

-- 添加Stripe订阅相关字段
ALTER TABLE subscriptions
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS stripe_status TEXT,
ADD COLUMN IF NOT EXISTS current_period_start TIMESTAMP,
ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMP;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_sub ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);

COMMENT ON COLUMN subscriptions.stripe_subscription_id IS 'Stripe订阅ID';
COMMENT ON COLUMN subscriptions.stripe_customer_id IS 'Stripe客户ID';
COMMENT ON COLUMN subscriptions.stripe_status IS 'Stripe订阅状态（active/past_due/canceled等）';
COMMENT ON COLUMN subscriptions.current_period_start IS '当前订阅周期开始时间';
COMMENT ON COLUMN subscriptions.current_period_end IS '当前订阅周期结束时间';

-- ============================================================
-- 3. users表添加Stripe客户ID
-- ============================================================

ALTER TABLE users
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT UNIQUE;

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);

COMMENT ON COLUMN users.stripe_customer_id IS 'Stripe客户ID（用于管理订阅）';

-- ============================================================
-- 4. 更新payments表的payment_method约束
-- ============================================================

-- 确保payment_method包含stripe
-- 注意：如果约束已存在且正确，此操作会失败，可以忽略
DO $$
BEGIN
    -- 尝试删除旧约束
    ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_payment_method_check;

    -- 添加新约束（包含stripe）
    ALTER TABLE payments ADD CONSTRAINT payments_payment_method_check
    CHECK (payment_method IN (
        'wechat', 'alipay', 'stripe', 'lemonsqueezy', 'apple_pay'
    ));
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Constraint update skipped: %', SQLERRM;
END $$;

-- ============================================================
-- 5. 更新subscriptions表的payment_provider约束
-- ============================================================

DO $$
BEGIN
    -- 尝试删除旧约束
    ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_payment_provider_check;

    -- 添加新约束
    ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_payment_provider_check
    CHECK (payment_provider IN ('lemonsqueezy', 'stripe', 'wechat', 'alipay', 'zpay'));
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Constraint update skipped: %', SQLERRM;
END $$;

-- ============================================================
-- 完成标记
-- ============================================================
-- Stripe迁移完成
-- 现在可以使用Stripe进行海外支付
