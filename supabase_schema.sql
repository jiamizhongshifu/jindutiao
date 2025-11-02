-- PyDayBar 配额管理系统数据库表
-- 创建日期: 2025-11-02

-- 1. 创建用户配额表
CREATE TABLE IF NOT EXISTS user_quotas (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_tier TEXT NOT NULL DEFAULT 'free',

    -- 每日任务规划配额
    daily_plan_total INTEGER NOT NULL DEFAULT 3,
    daily_plan_used INTEGER NOT NULL DEFAULT 0,
    daily_plan_reset_at TIMESTAMP WITH TIME ZONE,

    -- 周报配额
    weekly_report_total INTEGER NOT NULL DEFAULT 1,
    weekly_report_used INTEGER NOT NULL DEFAULT 0,
    weekly_report_reset_at TIMESTAMP WITH TIME ZONE,

    -- 聊天配额
    chat_total INTEGER NOT NULL DEFAULT 10,
    chat_used INTEGER NOT NULL DEFAULT 0,
    chat_reset_at TIMESTAMP WITH TIME ZONE,

    -- 主题推荐配额
    theme_recommend_total INTEGER NOT NULL DEFAULT 5,
    theme_recommend_used INTEGER NOT NULL DEFAULT 0,
    theme_recommend_reset_at TIMESTAMP WITH TIME ZONE,

    -- 主题生成配额
    theme_generate_total INTEGER NOT NULL DEFAULT 3,
    theme_generate_used INTEGER NOT NULL DEFAULT 0,
    theme_generate_reset_at TIMESTAMP WITH TIME ZONE,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),

    -- 约束：每个用户只有一条记录
    CONSTRAINT unique_user_id UNIQUE (user_id)
);

-- 2. 创建索引以加快查询
CREATE INDEX IF NOT EXISTS idx_user_quotas_user_id ON user_quotas(user_id);
CREATE INDEX IF NOT EXISTS idx_user_quotas_user_tier ON user_quotas(user_tier);

-- 3. 创建触发器：自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_quotas_updated_at
    BEFORE UPDATE ON user_quotas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 4. 插入默认测试用户数据
INSERT INTO user_quotas (
    user_id,
    user_tier,
    daily_plan_total,
    daily_plan_used,
    daily_plan_reset_at
) VALUES (
    'user_demo',
    'free',
    3,
    0,
    TIMEZONE('utc', NOW()) + INTERVAL '1 day'
) ON CONFLICT (user_id) DO NOTHING;

-- 5. 创建配额重置函数（用于定时任务）
CREATE OR REPLACE FUNCTION reset_daily_quotas()
RETURNS void AS $$
BEGIN
    UPDATE user_quotas
    SET
        daily_plan_used = 0,
        daily_plan_reset_at = TIMEZONE('utc', NOW()) + INTERVAL '1 day'
    WHERE daily_plan_reset_at < TIMEZONE('utc', NOW());

    UPDATE user_quotas
    SET
        chat_used = 0,
        chat_reset_at = TIMEZONE('utc', NOW()) + INTERVAL '1 day'
    WHERE chat_reset_at < TIMEZONE('utc', NOW());

    UPDATE user_quotas
    SET
        theme_recommend_used = 0,
        theme_recommend_reset_at = TIMEZONE('utc', NOW()) + INTERVAL '1 day'
    WHERE theme_recommend_reset_at < TIMEZONE('utc', NOW());

    UPDATE user_quotas
    SET
        theme_generate_used = 0,
        theme_generate_reset_at = TIMEZONE('utc', NOW()) + INTERVAL '1 day'
    WHERE theme_generate_reset_at < TIMEZONE('utc', NOW());
END;
$$ LANGUAGE plpgsql;

-- 6. 创建周配额重置函数
CREATE OR REPLACE FUNCTION reset_weekly_quotas()
RETURNS void AS $$
BEGIN
    UPDATE user_quotas
    SET
        weekly_report_used = 0,
        weekly_report_reset_at = TIMEZONE('utc', NOW()) + INTERVAL '7 days'
    WHERE weekly_report_reset_at < TIMEZONE('utc', NOW());
END;
$$ LANGUAGE plpgsql;

-- 7. 启用行级安全（RLS）- 可选，提高安全性
ALTER TABLE user_quotas ENABLE ROW LEVEL SECURITY;

-- 创建策略：允许所有操作（因为使用service_role key）
CREATE POLICY "Enable all operations for service role"
    ON user_quotas
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 完成！现在可以使用配额系统了
