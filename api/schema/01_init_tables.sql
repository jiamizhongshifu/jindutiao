-- GaiYa每日进度条 - Supabase数据库初始化脚本
-- 创建日期: 2025-11-05
-- 描述: 用户认证、订阅管理、样式商店完整schema

-- ============================================================
-- 1. 辅助函数：自动更新updated_at字段
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 2. users表（用户基本信息）
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 认证信息
  email TEXT UNIQUE NOT NULL,
  auth_provider TEXT DEFAULT 'email' CHECK (auth_provider IN ('email', 'wechat', 'apple')),

  -- 个人信息
  username TEXT UNIQUE,
  display_name TEXT,
  avatar_url TEXT,

  -- 用户等级
  user_tier TEXT NOT NULL DEFAULT 'free' CHECK (user_tier IN ('free', 'pro', 'lifetime')),

  -- 统计数据
  total_usage_days INTEGER DEFAULT 0,  -- 总使用天数

  -- 状态
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
  email_verified BOOLEAN DEFAULT FALSE,

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_login_at TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(user_tier);
CREATE INDEX idx_users_status ON users(status);

-- 更新时间戳触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE users IS '用户基本信息表';

-- ============================================================
-- 3. subscriptions表（用户订阅记录）
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 订阅类型
  plan_type TEXT NOT NULL CHECK (plan_type IN ('pro_monthly', 'pro_yearly', 'lifetime')),

  -- 价格信息
  price DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'CNY',

  -- 订阅状态
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
    'active', 'cancelled', 'expired', 'refunded', 'pending'
  )),

  -- 时间管理
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP,  -- NULL表示终身会员
  cancelled_at TIMESTAMP,

  -- 支付信息
  payment_id UUID,  -- 关联到payments表
  payment_provider TEXT CHECK (payment_provider IN ('lemonsqueezy', 'stripe', 'wechat', 'alipay')),

  -- 自动续订
  auto_renew BOOLEAN DEFAULT TRUE,

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_expires ON subscriptions(expires_at);

-- 更新时间戳触发器
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE subscriptions IS '用户订阅记录表';

-- ============================================================
-- 4. payments表（支付记录）
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 订单信息
  order_id TEXT UNIQUE NOT NULL,  -- 外部支付平台订单ID

  -- 支付金额
  amount DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'CNY',

  -- 支付方式
  payment_method TEXT CHECK (payment_method IN (
    'wechat', 'alipay', 'stripe', 'lemonsqueezy', 'apple_pay'
  )),
  payment_provider TEXT,

  -- 支付状态
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'completed', 'failed', 'refunded', 'cancelled'
  )),

  -- 购买内容类型
  item_type TEXT NOT NULL CHECK (item_type IN ('subscription', 'style', 'marker', 'credits')),
  item_id UUID,  -- 关联到subscriptions或progress_bar_styles等
  item_metadata JSONB,  -- 购买详情（JSON格式）

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,

  -- 退款信息
  refunded_at TIMESTAMP,
  refund_reason TEXT
);

-- 创建索引
CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_created ON payments(created_at);

-- 更新时间戳触发器
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE payments IS '支付记录表';

-- ============================================================
-- 5. user_quotas表（已存在，需要确保兼容）
-- ============================================================
-- 注意：此表已在quota_manager.py中定义，这里仅确认schema
-- 如果表不存在，则创建；如果已存在，则跳过

CREATE TABLE IF NOT EXISTS user_quotas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT UNIQUE NOT NULL,
  user_tier TEXT NOT NULL DEFAULT 'free',

  -- 每日任务规划配额
  daily_plan_total INTEGER DEFAULT 3,
  daily_plan_used INTEGER DEFAULT 0,
  daily_plan_reset_at TIMESTAMP,

  -- 周报生成配额
  weekly_report_total INTEGER DEFAULT 1,
  weekly_report_used INTEGER DEFAULT 0,
  weekly_report_reset_at TIMESTAMP,

  -- 对话查询配额
  chat_total INTEGER DEFAULT 10,
  chat_used INTEGER DEFAULT 0,
  chat_reset_at TIMESTAMP,

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quotas_user ON user_quotas(user_id);
CREATE INDEX IF NOT EXISTS idx_quotas_tier ON user_quotas(user_tier);

COMMENT ON TABLE user_quotas IS 'AI功能配额管理表';

-- ============================================================
-- 6. progress_bar_styles表（进度条样式库）
-- ============================================================
CREATE TABLE IF NOT EXISTS progress_bar_styles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 基本信息
  style_id TEXT UNIQUE NOT NULL,  -- 样式唯一标识（如cyber-glitch-001）
  name TEXT NOT NULL,  -- 样式名称
  name_en TEXT,
  description TEXT,

  -- 分类
  category TEXT NOT NULL CHECK (category IN (
    'basic', 'anime', 'cyberpunk', 'nature', 'tech', 'custom'
  )),

  -- 访问控制
  tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'shop')),
  author_id UUID REFERENCES users(id),  -- 作者（用户上传的样式）
  author_type TEXT DEFAULT 'official' CHECK (author_type IN ('official', 'user')),

  -- 文件信息
  preview_thumbnail TEXT,  -- 缩略图URL
  preview_video TEXT,  -- 预览视频URL
  files JSONB NOT NULL,  -- 样式文件列表（QML + assets）

  -- 版本和兼容性
  version TEXT DEFAULT '1.0.0',
  compatible_versions TEXT[] DEFAULT ARRAY['1.5.0'],

  -- 统计数据
  downloads INTEGER DEFAULT 0,
  rating DECIMAL(3,2) DEFAULT 0.0,
  favorites INTEGER DEFAULT 0,

  -- 定价（样式商店）
  price DECIMAL(10,2) DEFAULT 0.0,
  currency TEXT DEFAULT 'CNY',

  -- 状态
  status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
  featured BOOLEAN DEFAULT FALSE,  -- 是否精选

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_styles_category ON progress_bar_styles(category);
CREATE INDEX idx_styles_tier ON progress_bar_styles(tier);
CREATE INDEX idx_styles_author ON progress_bar_styles(author_id);
CREATE INDEX idx_styles_status ON progress_bar_styles(status);
CREATE INDEX idx_styles_featured ON progress_bar_styles(featured);

-- 更新时间戳触发器
CREATE TRIGGER update_styles_updated_at BEFORE UPDATE ON progress_bar_styles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE progress_bar_styles IS '进度条样式库';

-- ============================================================
-- 7. time_markers表（时间标记库）
-- ============================================================
CREATE TABLE IF NOT EXISTS time_markers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 基本信息
  marker_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,

  -- 分类
  category TEXT NOT NULL CHECK (category IN (
    'basic', 'animated', 'holiday', 'anime', 'custom'
  )),

  -- 访问控制
  tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'shop')),
  author_id UUID REFERENCES users(id),

  -- 文件信息
  preview_image TEXT,
  file_url TEXT NOT NULL,  -- 标记文件URL（图片/动图）
  file_type TEXT CHECK (file_type IN ('png', 'jpg', 'gif', 'webp')),
  file_size INTEGER,  -- 文件大小（bytes）

  -- 统计和定价
  downloads INTEGER DEFAULT 0,
  rating DECIMAL(3,2) DEFAULT 0.0,
  price DECIMAL(10,2) DEFAULT 0.0,
  currency TEXT DEFAULT 'CNY',

  -- 状态
  status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_markers_category ON time_markers(category);
CREATE INDEX idx_markers_tier ON time_markers(tier);
CREATE INDEX idx_markers_status ON time_markers(status);

-- 更新时间戳触发器
CREATE TRIGGER update_markers_updated_at BEFORE UPDATE ON time_markers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE time_markers IS '时间标记库';

-- ============================================================
-- 8. user_purchased_styles表（用户购买记录）
-- ============================================================
CREATE TABLE IF NOT EXISTS user_purchased_styles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 购买的样式
  item_type TEXT NOT NULL CHECK (item_type IN ('style', 'marker')),
  item_id UUID,  -- 关联到progress_bar_styles或time_markers

  -- 购买信息
  price DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'CNY',
  payment_id UUID REFERENCES payments(id),

  -- 时间戳
  purchased_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_purchased_user ON user_purchased_styles(user_id);
CREATE INDEX idx_purchased_item ON user_purchased_styles(item_id);

-- 唯一约束：同一用户不能重复购买同一样式
CREATE UNIQUE INDEX idx_purchased_unique
  ON user_purchased_styles(user_id, item_type, item_id);

COMMENT ON TABLE user_purchased_styles IS '用户购买的样式和标记记录';

-- ============================================================
-- 9. user_favorites表（用户收藏）
-- ============================================================
CREATE TABLE IF NOT EXISTS user_favorites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  item_type TEXT NOT NULL CHECK (item_type IN ('style', 'marker')),
  item_id UUID,

  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_favorites_user ON user_favorites(user_id);

-- 唯一约束
CREATE UNIQUE INDEX idx_favorites_unique
  ON user_favorites(user_id, item_type, item_id);

COMMENT ON TABLE user_favorites IS '用户收藏的样式和标记';

-- ============================================================
-- 10. creator_earnings表（创作者收益记录）
-- ============================================================
CREATE TABLE IF NOT EXISTS creator_earnings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 收益来源
  item_type TEXT NOT NULL CHECK (item_type IN ('style', 'marker')),
  item_id UUID,
  purchase_id UUID REFERENCES user_purchased_styles(id),

  -- 收益金额
  amount DECIMAL(10,2) NOT NULL,  -- 作者实际获得（70%）
  original_price DECIMAL(10,2) NOT NULL,  -- 原始售价（100%）
  platform_fee DECIMAL(10,2) NOT NULL,  -- 平台手续费（30%）
  currency TEXT DEFAULT 'CNY',

  -- 提现状态
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'available', 'withdrawn', 'processing'
  )),
  withdrawn_at TIMESTAMP,

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_earnings_user ON creator_earnings(user_id);
CREATE INDEX idx_earnings_status ON creator_earnings(status);
CREATE INDEX idx_earnings_created ON creator_earnings(created_at);

COMMENT ON TABLE creator_earnings IS '创作者收益记录';

-- ============================================================
-- 11. withdrawal_requests表（提现申请）
-- ============================================================
CREATE TABLE IF NOT EXISTS withdrawal_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 提现金额
  amount DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'CNY',

  -- 提现方式
  payment_method TEXT NOT NULL CHECK (payment_method IN ('alipay', 'wechat', 'bank')),
  payment_account TEXT NOT NULL,  -- 收款账号（加密存储）
  account_name TEXT,  -- 收款人姓名

  -- 审核状态
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'approved', 'processing', 'completed', 'rejected'
  )),

  -- 审核信息
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMP,
  rejection_reason TEXT,

  -- 支付信息
  transaction_id TEXT,  -- 支付平台交易ID
  completed_at TIMESTAMP,

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_withdrawal_user ON withdrawal_requests(user_id);
CREATE INDEX idx_withdrawal_status ON withdrawal_requests(status);
CREATE INDEX idx_withdrawal_created ON withdrawal_requests(created_at);

-- 更新时间戳触发器
CREATE TRIGGER update_withdrawal_updated_at BEFORE UPDATE ON withdrawal_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE withdrawal_requests IS '创作者提现申请记录';

-- ============================================================
-- 完成标记
-- ============================================================
-- 数据库初始化完成
-- 下一步：运行 02_seed_data.sql 插入初始数据
