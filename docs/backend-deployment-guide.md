# GaiYa每日进度条 - 后端系统部署指南

> **版本**: v1.6.0 商业化功能
> **创建日期**: 2025-11-05
> **技术栈**: Supabase + Vercel Serverless Functions

---

## 📋 部署清单

### 前置条件

- ✅ Supabase项目已创建（已完成）
- ✅ Supabase环境变量已配置（SUPABASE_URL, SUPABASE_ANON_KEY）
- ✅ Vercel项目已部署
- ⏳ 支付服务集成（待完成）

### 已完成模块

- ✅ 数据库表结构设计（11个表）
- ✅ 初始数据seed脚本（基础样式+示例用户）
- ✅ AuthManager 认证管理器
- ✅ SubscriptionManager 订阅管理器
- ✅ StyleManager 样式管理器
- ✅ QuotaManager 配额管理器（已有）

---

## 🗄️ 数据库部署

### 步骤 1: 执行SQL脚本

登录Supabase控制台，在SQL编辑器中依次执行：

#### 1.1 创建表结构

```bash
# 文件位置
api/schema/01_init_tables.sql
```

**包含的表：**
1. `users` - 用户基本信息
2. `subscriptions` - 订阅记录
3. `payments` - 支付记录
4. `user_quotas` - AI功能配额（已存在，脚本会检查）
5. `progress_bar_styles` - 进度条样式库
6. `time_markers` - 时间标记库
7. `user_purchased_styles` - 用户购买记录
8. `user_favorites` - 用户收藏
9. `creator_earnings` - 创作者收益
10. `withdrawal_requests` - 提现申请

**操作步骤：**
1. 打开 Supabase 控制台 → SQL Editor
2. 复制 `01_init_tables.sql` 内容
3. 粘贴到编辑器并执行
4. 确认所有表创建成功（检查Table Editor）

#### 1.2 插入初始数据

```bash
# 文件位置
api/schema/02_seed_data.sql
```

**包含的数据：**
- 基础样式：4个（Free用户）
- 高级样式：12个（Pro用户）
- 基础时间标记：3个（Free）
- 高级时间标记：3个（Pro）
- 测试用户：3个（free/pro/lifetime）

**操作步骤：**
1. 在 SQL Editor 中执行 `02_seed_data.sql`
2. 验证数据插入成功：
   ```sql
   SELECT COUNT(*) FROM progress_bar_styles; -- 应该是 16
   SELECT COUNT(*) FROM time_markers; -- 应该是 6
   SELECT COUNT(*) FROM users WHERE email LIKE '%@example.com'; -- 应该是 3
   ```

### 步骤 2: 配置Row Level Security（可选）

Supabase默认启用RLS。如果需要配置访问权限策略：

```sql
-- 示例：允许用户访问自己的数据
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own data"
  ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
  ON users FOR UPDATE
  USING (auth.uid() = id);

-- 其他表的策略根据业务需求配置
```

---

## 🔧 API接口部署

### 已部署的API端点

当前Vercel上已部署的端点：
- `/api/health` - 健康检查
- `/api/quota-status` - 配额查询
- `/api/plan-tasks` - AI任务规划

### 需要新增的API端点

#### 认证相关

1. **POST** `/api/auth/signup`
   - 功能：用户注册
   - 管理器：`AuthManager.sign_up_with_email()`

2. **POST** `/api/auth/signin`
   - 功能：用户登录
   - 管理器：`AuthManager.sign_in_with_email()`

3. **POST** `/api/auth/signout`
   - 功能：用户登出
   - 管理器：`AuthManager.sign_out()`

4. **POST** `/api/auth/refresh`
   - 功能：刷新访问令牌
   - 管理器：`AuthManager.refresh_access_token()`

#### 订阅相关

5. **GET** `/api/subscription/status`
   - 功能：查询订阅状态
   - 管理器：`SubscriptionManager.check_subscription_status()`

6. **POST** `/api/subscription/create`
   - 功能：创建订阅（需要先完成支付）
   - 管理器：`SubscriptionManager.create_subscription()`

7. **POST** `/api/subscription/cancel`
   - 功能：取消订阅
   - 管理器：`SubscriptionManager.cancel_subscription()`

8. **GET** `/api/subscription/pricing`
   - 功能：获取定价方案
   - 管理器：`SubscriptionManager.get_pricing_info()`

#### 样式商店相关

9. **GET** `/api/styles/list`
   - 功能：获取样式列表
   - 管理器：`StyleManager.get_available_styles()`

10. **GET** `/api/styles/{style_id}`
    - 功能：获取样式详情
    - 管理器：`StyleManager.get_style_details()`

11. **POST** `/api/styles/purchase`
    - 功能：购买样式
    - 管理器：`StyleManager.purchase_style()`

12. **POST** `/api/styles/favorite`
    - 功能：收藏/取消收藏
    - 管理器：`StyleManager.toggle_favorite()`

13. **GET** `/api/creator/earnings`
    - 功能：查询创作者收益
    - 管理器：`StyleManager.get_creator_earnings()`

---

## 📝 API端点实现示例

### 示例1: 用户登录

创建文件：`api/auth-signin.py`

```python
from http.server import BaseHTTPRequestHandler
import json
from api.auth_manager import AuthManager

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)

        email = data.get("email")
        password = data.get("password")

        # 2. 调用认证管理器
        auth_manager = AuthManager()
        result = auth_manager.sign_in_with_email(email, password)

        # 3. 返回响应
        self.send_response(200 if result["success"] else 400)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps(result).encode('utf-8'))
```

### 示例2: 样式列表查询

创建文件：`api/styles-list.py`

```python
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse
from api.style_manager import StyleManager

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. 解析查询参数
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        user_id = params.get("user_id", [None])[0]
        user_tier = params.get("user_tier", ["free"])[0]
        category = params.get("category", [None])[0]

        # 2. 调用样式管理器
        style_manager = StyleManager()
        styles = style_manager.get_available_styles(user_id, user_tier, category)

        # 3. 返回响应
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            "success": True,
            "styles": styles,
            "count": len(styles)
        }

        self.wfile.write(json.dumps(response).encode('utf-8'))
```

---

## 🔒 安全配置

### 环境变量

确保以下环境变量已在Vercel配置：

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Vercel API（可选）
GAIYA_API_URL=https://your-project.vercel.app
```

### CORS配置

在所有API响应中添加CORS头：

```python
self.send_header('Access-Control-Allow-Origin', '*')
self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
```

---

## 🧪 测试验证

### 1. 数据库测试

```sql
-- 测试1: 检查表是否创建成功
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';

-- 测试2: 检查基础样式数量
SELECT tier, COUNT(*) FROM progress_bar_styles
GROUP BY tier;
-- 期望结果：free=4, pro=12

-- 测试3: 检查测试用户
SELECT email, user_tier FROM users
WHERE email LIKE '%@example.com';
```

### 2. API端点测试

使用curl或Postman测试：

```bash
# 测试健康检查
curl https://your-project.vercel.app/api/health

# 测试配额查询
curl "https://your-project.vercel.app/api/quota-status?user_tier=free"

# 测试样式列表（需要实现后）
curl "https://your-project.vercel.app/api/styles/list?user_tier=pro"
```

### 3. 客户端集成测试

在桌面应用中测试：

```python
# 测试认证
response = requests.post(
    "https://your-project.vercel.app/api/auth/signin",
    json={"email": "test@example.com", "password": "password"}
)
print(response.json())

# 测试订阅状态
response = requests.get(
    "https://your-project.vercel.app/api/subscription/status",
    params={"user_id": "xxx"}
)
print(response.json())
```

---

## 🚀 下一步计划

### Phase 1: 完善API端点（1-2周）

- [ ] 实现所有认证相关API
- [ ] 实现订阅管理API
- [ ] 实现样式商店API
- [ ] 编写API文档

### Phase 2: 支付集成（2-3周）

- [ ] 集成LemonSqueezy（国际支付）
- [ ] 集成Stripe（备选）
- [ ] 集成微信支付/支付宝（国内）
- [ ] 实现Webhook回调

### Phase 3: 客户端适配（2-3周）

- [ ] 更新配置界面，添加登录/注册入口
- [ ] 实现订阅购买流程
- [ ] 实现样式商店UI
- [ ] 实现样式下载和应用
- [ ] 测试完整购买流程

### Phase 4: 创作者功能（2周）

- [ ] 实现样式上传界面
- [ ] 实现审核流程（后台）
- [ ] 实现收益查询
- [ ] 实现提现申请

---

## 📚 相关文档

- [进度条样式系统设计](./progress-bar-style-system.md)
- [商业化开发计划](./commercialization-plan.md)
- [API接口文档](./api-documentation.md)（待创建）

---

## 🐛 故障排查

### 问题1: 数据库连接失败

**症状**: API返回 "Supabase not configured"

**解决方案**:
1. 检查环境变量是否正确配置
2. 验证Supabase项目是否激活
3. 确认网络连接正常

### 问题2: API返回404

**症状**: Vercel部署成功但API无法访问

**解决方案**:
1. 检查 `vercel.json` 路由配置
2. 确认API文件名格式正确（`api/xxx.py`）
3. 查看Vercel部署日志

### 问题3: 样式数据为空

**症状**: 查询样式列表返回空数组

**解决方案**:
1. 确认已执行 `02_seed_data.sql`
2. 检查用户等级参数是否正确
3. 验证数据库中的样式状态为 'published'

---

**维护信息**:
- 创建日期：2025-11-05
- 最后更新：2025-11-05
- 负责人：技术团队
