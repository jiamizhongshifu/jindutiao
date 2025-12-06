-- payment_cache 表: 缓存支付状态供客户端快速查询
-- 由 webhook 回调写入,客户端轮询读取

CREATE TABLE IF NOT EXISTS payment_cache (
    -- 商户订单号(主键)
    out_trade_no TEXT PRIMARY KEY,
    
    -- Z-Pay 订单号
    trade_no TEXT,
    
    -- 支付状态: paid / unpaid
    status TEXT NOT NULL DEFAULT 'unpaid',
    
    -- 订单金额
    money TEXT,
    
    -- 业务参数(包含 user_id|plan_type)
    param TEXT,
    
    -- 商品名称
    name TEXT,
    
    -- 支付方式: alipay / wxpay
    type TEXT,
    
    -- 支付完成时间
    paid_at TIMESTAMPTZ,
    
    -- 记录更新时间
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引加速查询
CREATE INDEX IF NOT EXISTS idx_payment_cache_status ON payment_cache(status);
CREATE INDEX IF NOT EXISTS idx_payment_cache_updated_at ON payment_cache(updated_at);

-- 创建自动清理旧记录的函数(超过7天的记录)
CREATE OR REPLACE FUNCTION cleanup_old_payment_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM payment_cache
    WHERE updated_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- 说明: 
-- 1. 支付成功后,webhook 回调会写入 status='paid' 的记录
-- 2. 客户端轮询查询时优先读取此表,避免频繁调用 Z-Pay API
-- 3. 定期清理旧记录节省存储空间
