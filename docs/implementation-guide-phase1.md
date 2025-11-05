# GaiYa每日进度条 - 商业化第一阶段实施指南

> **基于现有架构**: Supabase + QuotaManager
> **目标**: 扩展用户认证和订阅管理功能
> **时间**: Week 1-3（2025-11-05 → 2025-11-26）

---

## 📊 现有架构评估

### ✅ 已有组件

1. **Supabase配置**
   - 环境变量：`SUPABASE_URL`, `SUPABASE_ANON_KEY`
   - 部署：Vercel环境变量配置

2. **配额管理系统**（`api/quota_manager.py`）
   ```python
   class QuotaManager:
       - get_or_create_user()  # 获取或创建用户配额
       - use_quota()           # 使用配额
       - get_quota_status()    # 查询配额状态
       - _check_and_reset_quota()  # 自动重置过期配额
   ```

3. **Supabase表结构**
   - `user_quotas` - 用户配额记录
     - user_id (TEXT, PRIMARY KEY)
     - user_tier (TEXT) - 'free' | 'pro'
     - daily_plan_total/used (INTEGER)
     - weekly_report_total/used (INTEGER)
     - chat_total/used (INTEGER)
     - theme_recommend_total/used (INTEGER)
     - theme_generate_total/used (INTEGER)
     - *_reset_at (TIMESTAMP) - 重置时间

4. **当前配额设置**
   - **Free**:
     - AI任务规划：3次/天
     - 周报生成：1次/周
     - 对话查询：10次/天
     - 主题推荐：5次/天
     - 主题生成：3次/天

   - **Pro**:
     - AI任务规划：50次/天
     - 周报生成：10次/周
     - 对话查询：100次/天
     - 主题推荐：50次/天
     - 主题生成：50次/天

---

## 🎯 需要新增的功能

### 1. 用户认证系统
**目的**: 让用户可以注册、登录，绑定配额到真实用户

**缺失部分**:
- [ ] 用户注册/登录界面
- [ ] 用户认证状态管理
- [ ] 邮箱验证（Magic Link）
- [ ] 用户信息存储（users表）

### 2. 订阅管理系统
**目的**: 管理Pro会员订阅、支付、过期

**缺失部分**:
- [ ] 订阅创建和更新
- [ ] 支付处理
- [ ] 订阅状态检测
- [ ] 自动降级（过期处理）

### 3. 与现有QuotaManager集成
**目的**: 让user_tier动态从订阅状态获取，而非硬编码

**当前问题**:
```python
# ai_client.py:33
self.user_tier = "free"  # 硬编码，需要改为从订阅状态获取
```

**解决方案**:
```python
# 从认证系统获取user_tier
self.user_tier = auth_manager.get_user_tier()  # 'free' | 'pro' | 'lifetime'
```

---

## 📅 Week 1: 数据库扩展和认证框架（7天）

### Day 1: 扩展Supabase数据库表结构

#### 1.1 创建users表

```sql
-- 用户基本信息表
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT,
  avatar_url TEXT,

  -- 认证相关
  email_verified BOOLEAN DEFAULT FALSE,
  last_sign_in_at TIMESTAMP,

  -- 会员等级（从subscriptions表计算得出）
  current_tier TEXT DEFAULT 'free' CHECK (current_tier IN ('free', 'pro', 'lifetime')),

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(current_tier);

-- 更新时间戳触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 1.2 创建subscriptions表

```sql
-- 订阅记录表
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 订阅类型
  tier TEXT NOT NULL CHECK (tier IN ('pro_monthly', 'pro_yearly', 'lifetime')),

  -- 订阅状态
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'canceled', 'expired', 'past_due')),

  -- 时间信息
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP,  -- NULL表示终身
  canceled_at TIMESTAMP,

  -- 支付提供商信息
  payment_provider TEXT CHECK (payment_provider IN ('lemonsqueezy', 'stripe')),
  external_subscription_id TEXT,  -- 第三方订阅ID

  -- 自动续费
  auto_renew BOOLEAN DEFAULT TRUE,

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_expires_at ON subscriptions(expires_at);

-- 更新时间戳触发器
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 订阅变更时自动更新users.current_tier的触发器
CREATE OR REPLACE FUNCTION update_user_tier_from_subscription()
RETURNS TRIGGER AS $$
BEGIN
  -- 当订阅状态变为active时，更新用户tier
  IF NEW.status = 'active' THEN
    UPDATE users
    SET current_tier = CASE
      WHEN NEW.tier = 'lifetime' THEN 'lifetime'
      ELSE 'pro'
    END
    WHERE id = NEW.user_id;

  -- 当订阅状态变为expired或canceled时，降级为free（除非有其他active订阅）
  ELSIF NEW.status IN ('expired', 'canceled') THEN
    UPDATE users
    SET current_tier = COALESCE(
      (SELECT CASE WHEN tier = 'lifetime' THEN 'lifetime' ELSE 'pro' END
       FROM subscriptions
       WHERE user_id = NEW.user_id AND status = 'active'
       ORDER BY expires_at DESC NULLS FIRST
       LIMIT 1),
      'free'
    )
    WHERE id = NEW.user_id;
  END IF;

  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_tier_on_subscription_change
  AFTER INSERT OR UPDATE OF status ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_user_tier_from_subscription();
```

#### 1.3 创建payments表

```sql
-- 支付记录表
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,

  -- 金额信息
  amount DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'CNY' CHECK (currency IN ('CNY', 'USD')),

  -- 支付状态
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),

  -- 支付提供商
  payment_provider TEXT CHECK (payment_provider IN ('lemonsqueezy', 'stripe', 'alipay', 'wechat')),
  payment_method TEXT,  -- 'card', 'alipay', 'wechat', etc.
  external_payment_id TEXT,  -- 第三方支付ID

  -- 失败原因
  failure_reason TEXT,

  -- 时间戳
  paid_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX idx_payments_status ON payments(status);

-- 更新时间戳触发器
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 1.4 创建user_sync_data表（云同步）

```sql
-- 云同步数据表
CREATE TABLE user_sync_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 数据类型
  data_type TEXT NOT NULL CHECK (data_type IN ('config', 'tasks', 'themes', 'templates')),

  -- 数据内容（JSONB格式，支持查询）
  data JSONB NOT NULL,

  -- 版本控制
  version INTEGER DEFAULT 1,

  -- 设备信息
  device_id TEXT NOT NULL,
  device_name TEXT,

  -- 同步时间
  synced_at TIMESTAMP DEFAULT NOW(),

  -- 创建时间
  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_sync_data_user_id ON user_sync_data(user_id);
CREATE INDEX idx_sync_data_type ON user_sync_data(data_type);
CREATE INDEX idx_sync_data_device ON user_sync_data(device_id);
CREATE INDEX idx_sync_data_synced_at ON user_sync_data(synced_at);

-- 唯一约束：同一用户同一数据类型同一设备只保留最新版本
CREATE UNIQUE INDEX idx_sync_data_unique_latest
  ON user_sync_data(user_id, data_type, device_id);
```

#### 1.5 配置Row Level Security (RLS)

```sql
-- 启用RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sync_data ENABLE ROW LEVEL SECURITY;

-- users表策略：用户只能查看和修改自己的信息
CREATE POLICY users_select_own ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY users_update_own ON users
  FOR UPDATE USING (auth.uid() = id);

-- subscriptions表策略：用户只能查看自己的订阅
CREATE POLICY subscriptions_select_own ON subscriptions
  FOR SELECT USING (user_id = auth.uid());

-- payments表策略：用户只能查看自己的支付记录
CREATE POLICY payments_select_own ON payments
  FOR SELECT USING (user_id = auth.uid());

-- user_sync_data表策略：用户只能访问自己的同步数据
CREATE POLICY sync_data_select_own ON user_sync_data
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY sync_data_insert_own ON user_sync_data
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY sync_data_update_own ON user_sync_data
  FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY sync_data_delete_own ON user_sync_data
  FOR DELETE USING (user_id = auth.uid());

-- 服务端策略（使用service_role key时绕过RLS）
```

#### 1.6 配置Supabase Auth

在Supabase Dashboard中配置：

1. **Enable Email Auth**
   - 启用Email Provider
   - 配置Magic Link（无密码登录）
   - 设置Email Templates（自定义登录邮件）

2. **配置Redirect URLs**
   - 本地开发：`http://localhost:3000/auth/callback`
   - 生产环境：`gaiya://auth/callback`（自定义URI scheme）

3. **可选：配置OAuth Providers**
   - Google OAuth（后续）
   - GitHub OAuth（后续）

---

### Day 2-4: 开发认证管理器（3天）

#### 2.1 创建AuthManager类

创建文件：`gaiya/core/auth_manager.py`

```python
"""
GaiYa每日进度条 - 用户认证管理器
基于Supabase Auth实现无密码登录
"""
import os
from typing import Optional, Dict
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """用户认证管理器"""

    def __init__(self):
        """初始化Supabase客户端"""
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_ANON_KEY", "")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured")
            self.client = None
        else:
            try:
                self.client: Client = create_client(supabase_url, supabase_key)
                logger.info("AuthManager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AuthManager: {e}")
                self.client = None

    def send_magic_link(self, email: str) -> Dict:
        """
        发送Magic Link登录邮件

        Args:
            email: 用户邮箱

        Returns:
            {
                "success": True/False,
                "message": "邮件已发送" / 错误信息
            }
        """
        if not self.client:
            return {"success": False, "message": "认证服务未配置"}

        try:
            # Supabase会自动发送Magic Link邮件
            response = self.client.auth.sign_in_with_otp({
                "email": email,
                "options": {
                    "email_redirect_to": "gaiya://auth/callback"
                }
            })

            logger.info(f"Magic link sent to {email}")
            return {
                "success": True,
                "message": f"登录链接已发送到 {email}，请查收邮件"
            }

        except Exception as e:
            logger.error(f"Failed to send magic link: {e}")
            return {
                "success": False,
                "message": f"发送失败: {str(e)}"
            }

    def verify_token(self, token: str) -> Dict:
        """
        验证Magic Link令牌

        Args:
            token: OTP token from email link

        Returns:
            {
                "success": True/False,
                "user": {...} / None,
                "session": {...} / None
            }
        """
        if not self.client:
            return {"success": False, "user": None}

        try:
            response = self.client.auth.verify_otp({
                "email": "...",  # 需要存储临时email
                "token": token,
                "type": "email"
            })

            if response.user:
                # 在users表中创建或更新用户记录
                self._sync_user_to_db(response.user)

                logger.info(f"User logged in: {response.user.email}")
                return {
                    "success": True,
                    "user": response.user,
                    "session": response.session
                }
            else:
                return {"success": False, "user": None}

        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return {"success": False, "user": None}

    def _sync_user_to_db(self, auth_user):
        """
        同步Supabase Auth用户到users表
        """
        try:
            # 使用upsert（存在则更新，不存在则插入）
            self.client.table("users").upsert({
                "id": auth_user.id,
                "email": auth_user.email,
                "email_verified": auth_user.email_confirmed_at is not None,
                "last_sign_in_at": auth_user.last_sign_in_at
            }).execute()

            logger.info(f"Synced user to DB: {auth_user.email}")
        except Exception as e:
            logger.error(f"Failed to sync user to DB: {e}")

    def get_current_user(self) -> Optional[Dict]:
        """
        获取当前登录用户信息

        Returns:
            User对象 或 None
        """
        if not self.client:
            return None

        try:
            response = self.client.auth.get_user()
            return response.user if response else None
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None

    def get_user_tier(self, user_id: Optional[str] = None) -> str:
        """
        获取用户会员等级

        Args:
            user_id: 用户ID，如果为None则获取当前用户

        Returns:
            'free' | 'pro' | 'lifetime'
        """
        if not self.client:
            return "free"

        try:
            if not user_id:
                current_user = self.get_current_user()
                if not current_user:
                    return "free"
                user_id = current_user.id

            # 从users表查询current_tier
            response = self.client.table("users").select("current_tier").eq("id", user_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0].get("current_tier", "free")
            else:
                return "free"

        except Exception as e:
            logger.error(f"Failed to get user tier: {e}")
            return "free"

    def sign_out(self) -> bool:
        """
        退出登录

        Returns:
            True表示成功，False表示失败
        """
        if not self.client:
            return False

        try:
            self.client.auth.sign_out()
            logger.info("User signed out")
            return True
        except Exception as e:
            logger.error(f"Sign out failed: {e}")
            return False

    def save_session(self, session: Dict):
        """
        保存Session到本地（用于持久化登录状态）

        Args:
            session: Supabase session对象
        """
        import json
        from pathlib import Path

        try:
            session_file = Path.home() / ".gaiya" / "session.json"
            session_file.parent.mkdir(exist_ok=True)

            with open(session_file, 'w') as f:
                json.dump({
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                    "expires_at": session.expires_at
                }, f)

            logger.info("Session saved to local file")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def load_session(self) -> Optional[Dict]:
        """
        从本地加载Session

        Returns:
            Session字典 或 None
        """
        import json
        from pathlib import Path

        try:
            session_file = Path.home() / ".gaiya" / "session.json"

            if not session_file.exists():
                return None

            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # 使用refresh_token恢复session
            response = self.client.auth.set_session(
                session_data["access_token"],
                session_data["refresh_token"]
            )

            if response.session:
                logger.info("Session restored from local file")
                return response.session
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
```

#### 2.2 创建SubscriptionManager类

创建文件：`gaiya/core/subscription_manager.py`

```python
"""
GaiYa每日进度条 - 订阅管理器
管理Pro会员订阅、支付、过期处理
"""
import os
from typing import Optional, Dict, List
from supabase import create_client, Client
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """订阅管理器"""

    def __init__(self):
        """初始化Supabase客户端"""
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_ANON_KEY", "")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured")
            self.client = None
        else:
            try:
                self.client: Client = create_client(supabase_url, supabase_key)
                logger.info("SubscriptionManager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SubscriptionManager: {e}")
                self.client = None

    def get_active_subscription(self, user_id: str) -> Optional[Dict]:
        """
        获取用户的激活订阅

        Args:
            user_id: 用户ID

        Returns:
            订阅记录 或 None
        """
        if not self.client:
            return None

        try:
            response = self.client.table("subscriptions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .order("expires_at", desc=True)\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to get active subscription: {e}")
            return None

    def create_subscription(self, user_id: str, tier: str, payment_provider: str, external_id: str) -> Optional[Dict]:
        """
        创建订阅记录

        Args:
            user_id: 用户ID
            tier: 'pro_monthly' | 'pro_yearly' | 'lifetime'
            payment_provider: 'lemonsqueezy' | 'stripe'
            external_id: 第三方订阅ID

        Returns:
            订阅记录 或 None
        """
        if not self.client:
            return None

        try:
            # 计算过期时间
            if tier == "lifetime":
                expires_at = None  # 终身不过期
            elif tier == "pro_monthly":
                expires_at = datetime.now() + timedelta(days=30)
            elif tier == "pro_yearly":
                expires_at = datetime.now() + timedelta(days=365)
            else:
                logger.error(f"Invalid tier: {tier}")
                return None

            # 创建订阅
            response = self.client.table("subscriptions").insert({
                "user_id": user_id,
                "tier": tier,
                "status": "active",
                "started_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "payment_provider": payment_provider,
                "external_subscription_id": external_id
            }).execute()

            logger.info(f"Created subscription for user {user_id}: {tier}")
            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return None

    def check_expired_subscriptions(self):
        """
        检查并处理过期订阅（定时任务）
        """
        if not self.client:
            return

        try:
            # 查找所有已过期但状态仍为active的订阅
            now = datetime.now().isoformat()
            response = self.client.table("subscriptions")\
                .select("*")\
                .eq("status", "active")\
                .lt("expires_at", now)\
                .execute()

            for subscription in response.data:
                # 更新状态为expired
                self.client.table("subscriptions")\
                    .update({"status": "expired"})\
                    .eq("id", subscription["id"])\
                    .execute()

                logger.info(f"Expired subscription {subscription['id']} for user {subscription['user_id']}")

        except Exception as e:
            logger.error(f"Failed to check expired subscriptions: {e}")
```

---

### Day 5-7: 前端UI开发（3天）

#### 3.1 在config_gui.py添加登录界面

在`config_gui.py`中添加新的Tab：

```python
def _create_account_tab(self):
    """创建账号管理Tab"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # 登录状态显示
    self.login_status_group = QGroupBox("账号状态")
    login_layout = QVBoxLayout(self.login_status_group)

    # 未登录状态
    self.not_logged_in_widget = self._create_login_form()
    login_layout.addWidget(self.not_logged_in_widget)

    # 已登录状态
    self.logged_in_widget = self._create_account_info()
    self.logged_in_widget.hide()
    login_layout.addWidget(self.logged_in_widget)

    layout.addWidget(self.login_status_group)

    # 会员状态
    self.membership_group = self._create_membership_section()
    layout.addWidget(self.membership_group)

    layout.addStretch()
    return widget

def _create_login_form(self):
    """创建登录表单"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # 标题
    title = QLabel("登录 GaiYa 账号")
    title.setStyleSheet("font-size: 16px; font-weight: bold;")
    layout.addWidget(title)

    # 邮箱输入
    self.email_input = QLineEdit()
    self.email_input.setPlaceholderText("请输入邮箱地址")
    layout.addWidget(QLabel("邮箱:"))
    layout.addWidget(self.email_input)

    # 登录按钮
    self.send_magic_link_btn = QPushButton("发送登录链接")
    self.send_magic_link_btn.clicked.connect(self.on_send_magic_link)
    layout.addWidget(self.send_magic_link_btn)

    # 说明
    info = QLabel("我们会向您的邮箱发送一个登录链接，点击即可登录")
    info.setWordWrap(True)
    info.setStyleSheet("color: gray; font-size: 12px;")
    layout.addWidget(info)

    return widget

def _create_account_info(self):
    """创建已登录用户信息显示"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # 用户信息
    self.user_email_label = QLabel()
    self.user_tier_label = QLabel()

    layout.addWidget(QLabel("已登录账号:"))
    layout.addWidget(self.user_email_label)
    layout.addWidget(QLabel("会员等级:"))
    layout.addWidget(self.user_tier_label)

    # 退出登录按钮
    logout_btn = QPushButton("退出登录")
    logout_btn.clicked.connect(self.on_logout)
    layout.addWidget(logout_btn)

    return widget

def on_send_magic_link(self):
    """发送Magic Link"""
    email = self.email_input.text().strip()

    if not email:
        QMessageBox.warning(self, "提示", "请输入邮箱地址")
        return

    # 调用AuthManager
    result = self.auth_manager.send_magic_link(email)

    if result["success"]:
        QMessageBox.information(self, "成功", result["message"])
    else:
        QMessageBox.critical(self, "错误", result["message"])
```

---

## 📝 总结

### Week 1 交付物
- [ ] Supabase新增4张表（users, subscriptions, payments, user_sync_data）
- [ ] RLS策略配置完成
- [ ] AuthManager类（gaiya/core/auth_manager.py）
- [ ] SubscriptionManager类（gaiya/core/subscription_manager.py）
- [ ] 登录界面UI（config_gui.py新Tab）

### Week 1 验收标准
- [ ] 用户可以输入邮箱并收到登录链接
- [ ] 点击链接后可以成功登录（需要实现URI handler）
- [ ] 登录后可以查看用户信息和会员等级
- [ ] 用户可以退出登录

---

**下一步**: Week 2 支付集成（详见后续文档）

