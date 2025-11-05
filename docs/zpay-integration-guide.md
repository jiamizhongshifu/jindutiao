# GaiYa每日进度条 - ZPAY支付集成指南

> **支付服务**: ZPAY（易支付）
> **支持方式**: 支付宝 + 微信支付
> **集成日期**: 2025-11-05

---

## 📋 ZPAY账号信息

### 商户配置

```bash
# 接口地址
ZPAY_API_URL=https://zpayz.cn

# 商户ID
ZPAY_PID=2025040215385823

# 商户密钥
ZPAY_PKEY=Ltb8ZL7kuFg7ZgtnIbuIpJ350FoTXdqu
```

### 环境变量配置

在Vercel中配置以下环境变量：

```bash
ZPAY_PID=2025040215385823
ZPAY_PKEY=Ltb8ZL7kuFg7ZgtnIbuIpJ350FoTXdqu
```

---

## 🔄 完整支付流程

### 流程图

```
用户端                  后端API                  ZPAY服务
  │                      │                        │
  │  1. 选择套餐          │                        │
  ├──────────────────────>│                        │
  │                      │                        │
  │  2. 创建订单          │                        │
  │                      ├───────────────────────>│
  │                      │   POST /submit.php     │
  │                      │                        │
  │  3. 返回支付链接      │                        │
  │<──────────────────────┤                        │
  │                      │                        │
  │  4. 跳转支付页面      │                        │
  ├──────────────────────────────────────────────>│
  │                      │                        │
  │  5. 用户完成支付      │                        │
  │<─────────────────────────────────────────────┤
  │                      │                        │
  │                      │  6. 异步回调           │
  │                      │<───────────────────────┤
  │                      │   GET /payment-notify  │
  │                      │                        │
  │                      │  7. 验证签名           │
  │                      │  8. 激活会员           │
  │                      │                        │
  │                      │  9. 返回success        │
  │                      ├───────────────────────>│
  │                      │                        │
  │  10. 同步跳转         │                        │
  │<─────────────────────────────────────────────┤
  │   gaiya://payment-success                    │
  │                      │                        │
  │  11. 刷新会员状态     │                        │
  ├──────────────────────>│                        │
  │                      │                        │
  │  12. 返回会员信息     │                        │
  │<──────────────────────┤                        │
```

---

## 🛠️ 后端实现

### 1. ZPayManager（支付管理器）

**文件**: `api/zpay_manager.py`

**核心方法**:

```python
# 创建支付订单（页面跳转方式）
create_order(
    out_trade_no,  # 商户订单号
    name,          # 商品名称
    money,         # 金额（元）
    pay_type,      # alipay/wxpay
    notify_url,    # 异步通知地址
    return_url,    # 同步跳转地址
    param          # 附加参数（JSON字符串）
)

# 验证支付回调签名
verify_notify(params)

# 查询订单状态
query_order(out_trade_no)

# 申请退款
request_refund(out_trade_no, money)
```

**MD5签名算法**:

```python
def _generate_sign(params):
    # 1. 移除sign和sign_type，过滤空值
    filtered = {k: v for k, v in params.items()
                if k not in ["sign", "sign_type"] and v}

    # 2. 按ASCII码排序
    sorted_params = sorted(filtered.items())

    # 3. 拼接成 key=value&key=value 格式
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])

    # 4. 加上商户密钥
    sign_str += ZPAY_PKEY

    # 5. MD5加密（小写）
    return hashlib.md5(sign_str.encode()).hexdigest()
```

---

### 2. API端点

#### 2.1 创建支付订单

**端点**: `POST /api/payment-create-order`

**请求**:
```json
{
    "user_id": "user-uuid",
    "plan_type": "pro_monthly",  // pro_monthly, pro_yearly, lifetime
    "pay_type": "alipay"         // alipay, wxpay
}
```

**响应**:
```json
{
    "success": true,
    "payment_url": "https://zpayz.cn/submit.php",
    "params": {
        "pid": "2025040215385823",
        "type": "alipay",
        "out_trade_no": "GAIYA1730880123456abc123",
        "name": "GaiYa Pro 月度会员",
        "money": "9.90",
        "notify_url": "https://jindutiao.vercel.app/api/payment-notify",
        "return_url": "gaiya://payment-success?out_trade_no=xxx",
        "param": "{\"user_id\":\"xxx\",\"plan_type\":\"pro_monthly\"}",
        "sign": "28f9583617d9caf66834292b6ab1cc89",
        "sign_type": "MD5"
    },
    "out_trade_no": "GAIYA1730880123456abc123",
    "amount": 9.9,
    "plan_name": "GaiYa Pro 月度会员"
}
```

---

#### 2.2 支付结果通知（Webhook）

**端点**: `GET /api/payment-notify`

**ZPAY回调参数**:
```
pid=2025040215385823
&name=GaiYa Pro 月度会员
&money=9.90
&out_trade_no=GAIYA1730880123456abc123
&trade_no=2019011922001418111011411195
&param={"user_id":"xxx","plan_type":"pro_monthly"}
&trade_status=TRADE_SUCCESS
&type=alipay
&sign=ef6e3c5c6ff45018e8c82fd66fb056dc
&sign_type=MD5
```

**处理流程**:
1. 验证签名（`verify_notify`）
2. 检查 `trade_status == "TRADE_SUCCESS"`
3. 检查订单是否已处理（防止重复）
4. 创建payment记录
5. 创建subscription并激活会员
6. 返回 `"success"`（纯文本）

**⚠️ 重要**:
- 必须返回纯文本 `"success"`，否则ZPAY会重复发送通知
- 必须验证签名，防止伪造通知
- 必须防止重复处理同一订单

---

#### 2.3 查询订单状态

**端点**: `GET /api/payment-query?out_trade_no=xxx`

**响应**:
```json
{
    "success": true,
    "order": {
        "out_trade_no": "GAIYA1730880123456abc123",
        "trade_no": "2019011922001418111011411195",
        "name": "GaiYa Pro 月度会员",
        "money": "9.90",
        "status": "paid",  // paid/unpaid
        "type": "alipay",
        "addtime": "2025-11-05 10:30:00",
        "endtime": "2025-11-05 10:35:00"
    }
}
```

---

## 💻 客户端实现

### 1. 发起支付

```python
# config_gui.py

def on_purchase_clicked(self, plan_type: str, pay_type: str):
    """处理购买按钮点击"""

    # 1. 检查是否已登录
    if not self.is_logged_in():
        QMessageBox.warning(self, "请先登录", "购买会员前请先登录您的账号")
        self.show_auth_dialog()
        return

    # 2. 调用后端API创建订单
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/payment-create-order",
            json={
                "user_id": self.get_current_user_id(),
                "plan_type": plan_type,
                "pay_type": pay_type
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data["success"]:
                # 3. 使用form表单跳转到支付页面
                self.open_payment_page(data["payment_url"], data["params"])

                # 4. 启动支付状态轮询
                self.start_payment_polling(data["out_trade_no"])
            else:
                QMessageBox.warning(self, "创建订单失败", data.get("error"))
        else:
            QMessageBox.warning(self, "网络错误", "无法连接到服务器")

    except Exception as e:
        QMessageBox.critical(self, "错误", f"创建订单失败：{str(e)}")


def open_payment_page(self, payment_url: str, params: dict):
    """打开支付页面（使用浏览器）"""
    import webbrowser

    # 方式1：拼接URL参数（GET方式）
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{payment_url}?{param_str}"
    webbrowser.open(full_url)

    # 方式2：使用POST表单（更安全，推荐）
    # 需要生成HTML文件并打开
    html_content = f"""
    <html>
    <body>
    <form id="payform" action="{payment_url}" method="POST">
    """

    for key, value in params.items():
        html_content += f'<input type="hidden" name="{key}" value="{value}" />'

    html_content += """
    </form>
    <script>document.getElementById('payform').submit();</script>
    </body>
    </html>
    """

    # 保存到临时文件并打开
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_file = f.name

    webbrowser.open(f"file://{temp_file}")
```

---

### 2. 支付状态轮询

```python
def start_payment_polling(self, out_trade_no: str):
    """启动支付状态轮询"""

    # 创建定时器，每5秒查询一次
    self.payment_timer = QTimer()
    self.payment_timer.timeout.connect(
        lambda: self.check_payment_status(out_trade_no)
    )
    self.payment_timer.start(5000)  # 5秒

    # 最多轮询10分钟
    self.polling_count = 0
    self.max_polling_count = 120  # 10分钟 = 120次


def check_payment_status(self, out_trade_no: str):
    """检查支付状态"""

    self.polling_count += 1

    # 超时停止轮询
    if self.polling_count > self.max_polling_count:
        self.payment_timer.stop()
        QMessageBox.information(
            self,
            "支付超时",
            "支付超时，请稍后手动刷新会员状态"
        )
        return

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/payment-query",
            params={"out_trade_no": out_trade_no},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()

            if data["success"]:
                order = data["order"]

                if order["status"] == "paid":
                    # 支付成功！
                    self.payment_timer.stop()
                    self.on_payment_success(order)

    except Exception as e:
        print(f"轮询支付状态失败: {e}")


def on_payment_success(self, order: dict):
    """支付成功处理"""

    # 1. 显示成功提示
    QMessageBox.information(
        self,
        "支付成功！",
        f"恭喜您成功购买 {order['name']}\n"
        f"支付金额：¥{order['money']}\n\n"
        "会员权益已激活，请重启应用生效"
    )

    # 2. 刷新用户信息
    self.refresh_user_info()

    # 3. 更新UI显示会员标识
    self.update_membership_badge()
```

---

### 3. Deep Link处理（可选）

如果支持Deep Link（`gaiya://payment-success`），可以实现：

```python
# main.py

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 注册Deep Link处理
        self.register_deep_link_handler()

    def register_deep_link_handler(self):
        """注册Deep Link处理（Windows注册表）"""
        import winreg

        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Classes\gaiya"
            )
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:GaiYa Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

            command_key = winreg.CreateKey(key, r"shell\open\command")
            exe_path = sys.executable
            winreg.SetValue(
                command_key,
                "",
                winreg.REG_SZ,
                f'"{exe_path}" "%1"'
            )

            winreg.CloseKey(command_key)
            winreg.CloseKey(key)

        except Exception as e:
            print(f"注册Deep Link失败: {e}")

    def handle_deep_link(self, url: str):
        """处理Deep Link"""
        # 解析URL: gaiya://payment-success?out_trade_no=xxx
        if url.startswith("gaiya://payment-success"):
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            out_trade_no = params.get("out_trade_no", [None])[0]

            if out_trade_no:
                # 查询订单并激活会员
                self.check_and_activate_membership(out_trade_no)
```

---

## 🧪 测试指南

### 1. 本地测试

```bash
# 1. 启动Vercel本地开发服务器
vercel dev

# 2. 测试创建订单
curl -X POST http://localhost:3000/api/payment-create-order \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "plan_type": "pro_monthly",
    "pay_type": "alipay"
  }'

# 3. 测试查询订单
curl "http://localhost:3000/api/payment-query?out_trade_no=GAIYA1730880123456abc123"
```

---

### 2. 支付测试（生产环境）

⚠️ **注意**: ZPAY可能需要真实支付测试，请使用小金额测试（如¥0.01）

**测试流程**:
1. 在配置界面点击"购买会员"
2. 选择"Pro月度 - ¥9.9"
3. 选择"支付宝支付"
4. 跳转到ZPAY支付页面
5. 使用支付宝扫码或登录支付
6. 支付完成后等待回调
7. 验证会员已激活

---

### 3. Webhook测试

使用工具模拟ZPAY回调：

```bash
# 生成签名
params="money=9.90&name=GaiYa Pro 月度会员&out_trade_no=GAIYA123&param={}&pid=2025040215385823&trade_no=ZPAY123&trade_status=TRADE_SUCCESS&type=alipay"
sign=$(echo -n "${params}Ltb8ZL7kuFg7ZgtnIbuIpJ350FoTXdqu" | md5sum | awk '{print $1}')

# 发送回调
curl "https://jindutiao.vercel.app/api/payment-notify?${params}&sign=${sign}&sign_type=MD5"
```

---

## 🛡️ 安全注意事项

### 1. 签名验证

**必须验证所有回调的签名**，防止伪造通知：

```python
if not zpay.verify_notify(params):
    # 签名无效，拒绝处理
    return "fail"
```

### 2. 金额验证

**必须验证支付金额与套餐价格一致**：

```python
plan_info = zpay.get_plan_info(plan_type)
received_money = float(params.get("money"))

if abs(received_money - plan_info["price"]) > 0.01:
    # 金额不匹配，可能被篡改
    return "fail"
```

### 3. 防止重复处理

**检查订单是否已处理**：

```python
if self._is_order_processed(out_trade_no):
    # 已处理，直接返回成功
    return "success"
```

### 4. 密钥保护

- ✅ 使用环境变量存储密钥
- ✅ 不要将密钥提交到Git
- ✅ 定期更换密钥

---

## 📊 订阅计划定价

| 套餐 | plan_type | 价格 | 商品名称 |
|-----|-----------|------|---------|
| Pro月度 | `pro_monthly` | ¥9.9 | GaiYa Pro 月度会员 |
| Pro年度 | `pro_yearly` | ¥59.0 | GaiYa Pro 年度会员 |
| 终身会员 | `lifetime` | ¥199.0 | GaiYa 终身会员 |

---

## 🐛 常见问题

### Q1: 支付后没有收到回调怎么办？

**A**: 检查以下几点：
1. `notify_url` 是否可公网访问
2. 服务器是否正确返回 `"success"`
3. 查看ZPAY后台的通知日志
4. 使用支付状态轮询作为备用方案

---

### Q2: 如何测试退款功能？

**A**: 使用小金额测试：

```python
zpay = ZPayManager()
result = zpay.request_refund(
    out_trade_no="GAIYA123",
    money=0.01
)
```

---

### Q3: 如何处理支付超时？

**A**: 客户端轮询10分钟后，引导用户手动刷新：

```python
# 在配置界面添加"刷新会员状态"按钮
def refresh_membership():
    response = requests.get(
        f"{BACKEND_URL}/api/subscription-status",
        params={"user_id": user_id}
    )
    # 更新UI
```

---

## 📁 文件清单

### 后端
- ✅ `api/zpay_manager.py` - ZPAY支付管理器
- ✅ `api/payment-create-order.py` - 创建订单API
- ✅ `api/payment-notify.py` - 支付回调API
- ✅ `api/payment-query.py` - 查询订单API

### 文档
- ✅ `docs/zpay-integration-guide.md` - 本文档
- ✅ `docs/pay.md` - ZPAY原始接口文档

---

**文档维护**:
- 创建日期：2025-11-05
- 最后更新：2025-11-05
- 负责人：技术团队
