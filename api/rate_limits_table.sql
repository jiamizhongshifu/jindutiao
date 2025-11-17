-- GaiYa速率限制表
-- 用于跨Serverless函数实例追踪API请求频率

CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    limit_key TEXT NOT NULL,           -- 限制键（endpoint:key_type:identifier_hash）
    endpoint TEXT NOT NULL,             -- API端点标识符
    identifier TEXT NOT NULL,           -- 原始标识符（IP/用户ID/邮箱）
    identifier_type TEXT NOT NULL,      -- 标识符类型（ip/user_id/email）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_rate_limits_key_time
ON rate_limits(limit_key, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_rate_limits_created_at
ON rate_limits(created_at);

-- 添加注释
COMMENT ON TABLE rate_limits IS 'API速率限制记录表';
COMMENT ON COLUMN rate_limits.limit_key IS '限制键，格式: endpoint:key_type:identifier_hash';
COMMENT ON COLUMN rate_limits.endpoint IS 'API端点标识符，如: auth_signin, payment_create_order';
COMMENT ON COLUMN rate_limits.identifier IS '原始标识符（IP地址、用户ID或邮箱）';
COMMENT ON COLUMN rate_limits.identifier_type IS '标识符类型: ip, user_id, email';
COMMENT ON COLUMN rate_limits.created_at IS '请求时间戳';

-- 可选：启用Row Level Security (RLS)
-- ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;

-- 可选：创建自动清理策略（删除24小时前的记录）
-- 需要启用pg_cron扩展
-- SELECT cron.schedule(
--     'cleanup-rate-limits',
--     '0 * * * *',  -- 每小时执行
--     $$DELETE FROM rate_limits WHERE created_at < NOW() - INTERVAL '24 hours'$$
-- );
