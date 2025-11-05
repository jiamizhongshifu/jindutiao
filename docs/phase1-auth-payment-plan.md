# GaiYa每日进度条 - Phase 1: 认证与支付开发计划

> **版本**: v1.6.0 Phase 1
> **开发周期**: 3-4周
> **核心目标**: 完成用户认证系统 + 支付集成，实现基本的会员购买流程

---

## 🎯 开发范围

### ✅ 本阶段开发
1. **用户认证系统** - 完整的注册/登录/Token管理
2. **支付集成** - 支持国内外支付方式
3. **订阅购买流程** - 从浏览定价到激活会员的完整链路
4. **客户端UI** - 登录注册界面 + 会员购买界面

### ❌ 本阶段不开发
- 样式商店（延后至v1.7+）
- 样式上传和审核（延后）
- 创作者收益系统（延后）
- 样式QML实现（延后）

---

## 📅 开发时间表

### Week 1: 认证系统开发

#### 后端API（3天）
- [x] ✅ 已完成：`/api/auth-signin` - 用户登录
- [x] ✅ 已完成：`/api/auth-signup` - 用户注册
- [ ] **Day 1**: `/api/auth-signout` - 用户登出
- [ ] **Day 1**: `/api/auth-refresh` - 刷新Token
- [ ] **Day 2**: `/api/auth-reset-password` - 重置密码
- [ ] **Day 3**: 测试所有认证端点

#### 客户端UI（2天）
- [ ] **Day 4**: 设计登录/注册界面（参考主流应用）
- [ ] **Day 5**: 实现登录/注册逻辑（调用后端API）

---

### Week 2: 支付服务研究与选型

#### 支付服务商调研（2天）
- [ ] **Day 1**: LemonSqueezy调研
  - 优势：独立开发者友好，无月费，支持全球支付
  - 费率：5% + Stripe手续费
  - 支持：信用卡、PayPal、Apple Pay

- [ ] **Day 1**: Stripe调研
  - 优势：功能强大，生态完善
  - 费率：2.9% + $0.30/笔
  - 支持：信用卡、各种钱包

- [ ] **Day 2**: 国内支付调研
  - 微信支付官方SDK
  - 支付宝开放平台
  - 聚合支付（如Ping++）

#### 支付方案决策（1天）
- [ ] **Day 3**: 制定支付策略
  - 国际用户：LemonSqueezy / Stripe
  - 国内用户：微信支付 / 支付宝
  - 测试环境配置

---

### Week 3: 支付集成开发

#### 后端支付API（4天）

##### LemonSqueezy集成（推荐优先）
- [ ] **Day 1**: 配置LemonSqueezy商店
  - 创建Product（Pro月度/年度/终身）
  - 配置Webhook URL
  - 获取API密钥

- [ ] **Day 2**: 实现支付API
  ```python
  # api/payment-create-checkout.py
  POST /api/payment-create-checkout
  {
    "user_id": "xxx",
    "plan_type": "pro_monthly" | "pro_yearly" | "lifetime",
    "return_url": "gaiya://payment-success"
  }
  # 返回：checkout_url（跳转到LemonSqueezy支付页面）
  ```

- [ ] **Day 3**: 实现Webhook回调
  ```python
  # api/payment-webhook.py
  POST /api/payment-webhook
  # 接收LemonSqueezy的支付成功通知
  # 验证签名 → 创建订阅 → 激活会员
  ```

- [ ] **Day 4**: 测试支付流程
  - 使用测试卡号完成支付
  - 验证Webhook正确触发
  - 确认用户等级正确升级

#### 客户端支付UI（3天）
- [ ] **Day 5**: 设计会员购买页面
  - 定价方案展示（3个档位）
  - Pro功能对比表
  - 购买按钮

- [ ] **Day 6**: 实现支付逻辑
  - 调用 `/api/payment-create-checkout`
  - 打开浏览器跳转到支付页面
  - 监听支付回调（Deep Link: `gaiya://payment-success`）

- [ ] **Day 7**: 实现会员状态同步
  - 支付成功后刷新用户信息
  - 更新UI显示会员标识
  - 解锁Pro功能

---

### Week 4: 集成测试与优化

#### 完整流程测试（3天）
- [ ] **Day 1**: 端到端测试
  ```
  1. 新用户注册 → 验证邮箱 → 登录成功
  2. 浏览会员定价 → 选择年度套餐
  3. 跳转支付 → 完成支付 → 回到应用
  4. 验证会员激活 → 配额升级 → AI功能可用
  5. 重启应用 → 登录状态保持 → 会员状态持久化
  ```

- [ ] **Day 2**: 异常场景测试
  - 支付失败处理
  - 网络中断恢复
  - Token过期刷新
  - 重复支付检测

- [ ] **Day 3**: 性能优化
  - API响应时间优化
  - UI加载体验优化
  - 错误提示优化

#### Bug修复与文档（2天）
- [ ] **Day 4**: 修复测试中发现的问题
- [ ] **Day 5**: 编写用户文档和开发文档

---

## 🔧 技术实现细节

### 1. 认证API实现

#### 登出API
```python
# api/auth-signout.py
from http.server import BaseHTTPRequestHandler
import json
from auth_manager import AuthManager

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. 读取Authorization Header
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            self._send_error(401, "Missing or invalid token")
            return

        access_token = auth_header.replace('Bearer ', '')

        # 2. 调用AuthManager登出
        auth_manager = AuthManager()
        result = auth_manager.sign_out(access_token)

        # 3. 返回响应
        if result["success"]:
            self._send_success({"message": "Signed out successfully"})
        else:
            self._send_error(400, result.get("error"))
```

#### Token刷新API
```python
# api/auth-refresh.py
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. 从请求体获取refresh_token
        body = json.loads(self.rfile.read(...))
        refresh_token = body.get("refresh_token")

        # 2. 调用AuthManager刷新
        auth_manager = AuthManager()
        result = auth_manager.refresh_access_token(refresh_token)

        # 3. 返回新的access_token和refresh_token
        if result["success"]:
            self._send_success({
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"]
            })
```

---

### 2. 支付API实现

#### LemonSqueezy支付流程

**Step 1: 创建Checkout**
```python
# api/payment-create-checkout.py
import requests
from http.server import BaseHTTPRequestHandler
import json

LEMONSQUEEZY_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY")
LEMONSQUEEZY_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(...))
        user_id = body.get("user_id")
        plan_type = body.get("plan_type")

        # 1. 根据plan_type获取对应的Product Variant ID
        variant_ids = {
            "pro_monthly": "123456",  # LemonSqueezy中创建的产品变体ID
            "pro_yearly": "123457",
            "lifetime": "123458"
        }
        variant_id = variant_ids.get(plan_type)

        # 2. 调用LemonSqueezy API创建Checkout
        response = requests.post(
            "https://api.lemonsqueezy.com/v1/checkouts",
            headers={
                "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "checkout_data": {
                            "custom": {
                                "user_id": user_id  # 传递用户ID到支付页面
                            }
                        }
                    },
                    "relationships": {
                        "store": {"data": {"type": "stores", "id": LEMONSQUEEZY_STORE_ID}},
                        "variant": {"data": {"type": "variants", "id": variant_id}}
                    }
                }
            }
        )

        checkout_data = response.json()
        checkout_url = checkout_data["data"]["attributes"]["url"]

        # 3. 返回支付链接
        self._send_success({
            "checkout_url": checkout_url,
            "checkout_id": checkout_data["data"]["id"]
        })
```

**Step 2: 处理Webhook**
```python
# api/payment-webhook.py
import hmac
import hashlib
from subscription_manager import SubscriptionManager

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. 验证Webhook签名
        signature = self.headers.get("X-Signature")
        body = self.rfile.read(...)

        expected_signature = hmac.new(
            LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if signature != expected_signature:
            self._send_error(401, "Invalid signature")
            return

        # 2. 解析Webhook数据
        data = json.loads(body)
        event_name = data["meta"]["event_name"]

        if event_name == "order_created":
            # 订单创建成功
            user_id = data["data"]["attributes"]["custom"]["user_id"]
            variant_id = data["data"]["attributes"]["variant_id"]
            order_id = data["data"]["id"]

            # 3. 创建支付记录
            # 4. 创建订阅
            # 5. 激活会员
            sub_manager = SubscriptionManager()

            # 先创建payment记录
            payment_data = {
                "user_id": user_id,
                "order_id": order_id,
                "amount": ...,
                "payment_method": "lemonsqueezy",
                "status": "completed",
                "item_type": "subscription"
            }
            # 插入到payments表...

            # 再创建subscription
            plan_type = self._get_plan_type_by_variant(variant_id)
            result = sub_manager.create_subscription(user_id, plan_type, payment_id)

        self._send_success({"received": True})
```

---

### 3. 客户端UI实现

#### 登录注册界面设计

```python
# config_gui.py 中添加认证相关UI

class AuthDialog(QDialog):
    """登录/注册对话框"""

    def __init__(self, parent=None, mode="signin"):
        super().__init__(parent)
        self.setWindowTitle("GaiYa每日进度条 - 账号登录" if mode == "signin" else "注册账号")
        self.setFixedSize(400, 500)
        self.mode = mode

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("resources/logo.png").scaled(80, 80)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # 标题
        title = QLabel("欢迎使用 GaiYa每日进度条" if self.mode == "signin" else "创建你的账号")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # 邮箱输入
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("邮箱地址")
        self.email_input.setMinimumHeight(40)
        layout.addWidget(self.email_input)

        # 密码输入
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码（至少6位）")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)

        # 注册模式：确认密码
        if self.mode == "signup":
            self.password_confirm_input = QLineEdit()
            self.password_confirm_input.setPlaceholderText("确认密码")
            self.password_confirm_input.setEchoMode(QLineEdit.Password)
            self.password_confirm_input.setMinimumHeight(40)
            layout.addWidget(self.password_confirm_input)

        # 主按钮
        self.submit_btn = QPushButton("登录" if self.mode == "signin" else "注册")
        self.submit_btn.setMinimumHeight(45)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b8d4;
                color: white;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00acc1;
            }
        """)
        self.submit_btn.clicked.connect(self.on_submit)
        layout.addWidget(self.submit_btn)

        # 切换模式链接
        switch_layout = QHBoxLayout()
        switch_text = "还没有账号？" if self.mode == "signin" else "已有账号？"
        switch_btn_text = "立即注册" if self.mode == "signin" else "去登录"

        switch_label = QLabel(switch_text)
        switch_btn = QPushButton(switch_btn_text)
        switch_btn.setFlat(True)
        switch_btn.setStyleSheet("color: #00b8d4; text-decoration: underline;")
        switch_btn.clicked.connect(self.switch_mode)

        switch_layout.addStretch()
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(switch_btn)
        switch_layout.addStretch()
        layout.addLayout(switch_layout)

        layout.addStretch()

    def on_submit(self):
        """提交登录/注册"""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        # 验证输入
        if not email or not password:
            QMessageBox.warning(self, "输入错误", "请填写邮箱和密码")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "密码太短", "密码至少需要6个字符")
            return

        # 注册模式：验证密码确认
        if self.mode == "signup":
            password_confirm = self.password_confirm_input.text()
            if password != password_confirm:
                QMessageBox.warning(self, "密码不匹配", "两次输入的密码不一致")
                return

        # 调用API
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("处理中...")

        if self.mode == "signin":
            self.do_signin(email, password)
        else:
            self.do_signup(email, password)

    def do_signin(self, email, password):
        """执行登录"""
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/auth-signin",
                json={"email": email, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 保存Token
                    self.save_tokens(data["access_token"], data["refresh_token"])

                    # 保存用户信息
                    self.save_user_info(data)

                    QMessageBox.information(self, "登录成功", f"欢迎回来，{email}！")
                    self.accept()
                else:
                    QMessageBox.warning(self, "登录失败", data.get("error", "未知错误"))
            else:
                QMessageBox.warning(self, "登录失败", "服务器错误，请稍后重试")

        except Exception as e:
            QMessageBox.critical(self, "网络错误", f"无法连接到服务器：{str(e)}")

        finally:
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("登录")

    def save_tokens(self, access_token, refresh_token):
        """保存Token到本地"""
        config_path = Path.home() / ".gaiya" / "auth.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "saved_at": datetime.now().isoformat()
            }, f)
```

#### 会员购买界面

```python
class MembershipDialog(QDialog):
    """会员购买对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("升级到 GaiYa Pro")
        self.setFixedSize(800, 600)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("解锁更多强大功能")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # 定价方案
        plans_layout = QHBoxLayout()

        # 月度套餐
        monthly_plan = self.create_plan_card(
            "Pro 月度",
            "¥9.9",
            "/月",
            "pro_monthly",
            features=[
                "高级进度条样式",
                "AI任务规划：50次/天",
                "多设备同步",
                "优先客服支持"
            ]
        )
        plans_layout.addWidget(monthly_plan)

        # 年度套餐（推荐）
        yearly_plan = self.create_plan_card(
            "Pro 年度",
            "¥59",
            "/年",
            "pro_yearly",
            features=[
                "所有月度功能",
                "相当于 ¥4.9/月",
                "节省 17%",
                "年度报告"
            ],
            recommended=True
        )
        plans_layout.addWidget(yearly_plan)

        # 终身会员
        lifetime_plan = self.create_plan_card(
            "终身会员",
            "¥199",
            "一次性",
            "lifetime",
            features=[
                "所有Pro功能",
                "终身免费更新",
                "专属徽章",
                "新功能抢先体验"
            ]
        )
        plans_layout.addWidget(lifetime_plan)

        layout.addLayout(plans_layout)

        layout.addStretch()

    def create_plan_card(self, name, price, period, plan_type, features, recommended=False):
        """创建定价卡片"""
        card = QGroupBox()
        if recommended:
            card.setStyleSheet("""
                QGroupBox {
                    border: 2px solid #00b8d4;
                    border-radius: 10px;
                    background-color: #f0f9ff;
                }
            """)

        layout = QVBoxLayout(card)

        # 推荐标签
        if recommended:
            rec_label = QLabel("🔥 推荐")
            rec_label.setAlignment(Qt.AlignCenter)
            rec_label.setStyleSheet("color: #00b8d4; font-weight: bold;")
            layout.addWidget(rec_label)

        # 套餐名称
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(name_label)

        # 价格
        price_label = QLabel(f"{price}<span style='font-size: 14px;'>{period}</span>")
        price_label.setAlignment(Qt.AlignCenter)
        price_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #00b8d4;")
        layout.addWidget(price_label)

        # 功能列表
        for feature in features:
            feature_label = QLabel(f"✓ {feature}")
            feature_label.setStyleSheet("margin: 5px;")
            layout.addWidget(feature_label)

        layout.addStretch()

        # 购买按钮
        buy_btn = QPushButton("立即购买")
        buy_btn.setMinimumHeight(40)
        buy_btn.clicked.connect(lambda: self.on_purchase(plan_type))
        layout.addWidget(buy_btn)

        return card

    def on_purchase(self, plan_type):
        """处理购买"""
        # 1. 检查是否已登录
        if not self.is_logged_in():
            QMessageBox.warning(self, "请先登录", "购买会员前请先登录您的账号")
            # 打开登录对话框
            return

        # 2. 调用支付API
        try:
            user_id = self.get_current_user_id()

            response = requests.post(
                f"{BACKEND_URL}/api/payment-create-checkout",
                json={
                    "user_id": user_id,
                    "plan_type": plan_type,
                    "return_url": "gaiya://payment-success"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                checkout_url = data["checkout_url"]

                # 3. 打开浏览器跳转到支付页面
                import webbrowser
                webbrowser.open(checkout_url)

                QMessageBox.information(
                    self,
                    "跳转到支付页面",
                    "已在浏览器中打开支付页面\n完成支付后会自动激活会员"
                )

                # 4. 启动支付状态轮询
                self.start_payment_polling(user_id)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建支付失败：{str(e)}")
```

---

## 💳 支付服务商对比

### LemonSqueezy（推荐）

**优势**:
- ✅ 独立开发者友好，无月费
- ✅ 自动处理税务和发票
- ✅ 支持全球支付方式
- ✅ Webhook集成简单
- ✅ 支持订阅和一次性支付

**费率**:
- 5% + Stripe手续费（约2.9% + $0.30）
- 总计约：8% + $0.30/笔

**文档**: https://docs.lemonsqueezy.com/

---

### Stripe

**优势**:
- ✅ 功能最强大
- ✅ 生态系统完善
- ✅ 支持多种支付方式
- ✅ 文档详细

**劣势**:
- ❌ 税务处理需要手动配置
- ❌ 对中国开发者不太友好

**费率**:
- 国际卡：2.9% + $0.30/笔
- 国内卡：3.4% + ¥2/笔

---

### 国内支付（微信/支付宝）

**优势**:
- ✅ 国内用户体验最好
- ✅ 费率较低（0.6%）

**劣势**:
- ❌ 需要企业资质
- ❌ 审核流程复杂
- ❌ 无法支持国际用户

**建议**:
- 初期使用LemonSqueezy
- 用户量增长后再接入国内支付

---

## 📋 开发检查清单

### 后端API
- [x] ✅ POST `/api/auth-signin` - 登录
- [x] ✅ POST `/api/auth-signup` - 注册
- [ ] POST `/api/auth-signout` - 登出
- [ ] POST `/api/auth-refresh` - 刷新Token
- [ ] POST `/api/payment-create-checkout` - 创建支付
- [ ] POST `/api/payment-webhook` - 支付回调
- [x] ✅ GET `/api/subscription-status` - 订阅状态

### 客户端UI
- [ ] 登录界面
- [ ] 注册界面
- [ ] 会员购买界面
- [ ] 支付状态监听
- [ ] Token自动刷新
- [ ] 会员状态显示

### 测试
- [ ] 注册流程测试
- [ ] 登录流程测试
- [ ] 支付流程测试（测试环境）
- [ ] Token刷新测试
- [ ] 会员激活测试
- [ ] 异常场景测试

---

## 🚀 下一步行动

### 立即开始（本周）

1. **完善认证API**（1-2天）
   - 实现 `/api/auth-signout`
   - 实现 `/api/auth-refresh`
   - 测试所有认证端点

2. **支付服务选型**（1天）
   - 注册LemonSqueezy账号
   - 创建测试商店和产品
   - 获取API密钥和Webhook密钥

3. **客户端UI设计**（2天）
   - 使用Figma设计登录/注册界面
   - 设计会员购买界面
   - 确定交互流程

---

**下一次会议讨论**:
1. 确认支付服务商选择（LemonSqueezy vs Stripe）
2. 审查UI设计稿
3. 确定测试计划

---

**文档维护**:
- 创建日期：2025-11-05
- 最后更新：2025-11-05
- 负责人：技术团队
