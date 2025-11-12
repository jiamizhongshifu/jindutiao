# GaiYa 微信扫码登录接入技术方案

**文档创建时间**: 2025-11-10
**项目版本**: GaiYa v1.5
**适用场景**: 桌面应用 + 云端API架构

---

## 目录

1. [方案概述](#1-方案概述)
2. [前置准备](#2-前置准备)
3. [技术架构设计](#3-技术架构设计)
4. [OAuth 2.0 完整流程](#4-oauth-20-完整流程)
5. [前端实现](#5-前端实现)
6. [后端实现](#6-后端实现)
7. [安全性考虑](#7-安全性考虑)
8. [用户体验优化](#8-用户体验优化)
9. [实施步骤](#9-实施步骤)
10. [常见问题](#10-常见问题)

---

## 1. 方案概述

### 1.1 业务目标

**用户需求**：
- 在"个人中心"tab的登录注册页面中，**优先展示微信扫码登录**
- 提供"切换到邮箱登录"的选项，将邮箱登录作为备选方案
- 降低登录门槛，提升用户转化率

**技术目标**：
- 接入微信开放平台扫码登录（OAuth 2.0）
- 安全存储用户Token和身份信息
- 保持现有邮箱登录系统不变，作为备选方案
- 支持微信登录用户与邮箱账号绑定

### 1.2 核心优势

| 优势 | 说明 |
|------|------|
| **便捷性** | 无需记住密码，扫码即登录 |
| **安全性** | 利用微信的安全体系，降低密码泄露风险 |
| **用户习惯** | 符合国内用户使用习惯，降低注册门槛 |
| **账号统一** | 可与微信身份绑定，支持多设备同步 |

---

## 2. 前置准备

### 2.1 微信开放平台注册

**步骤**：

1. **注册开发者账号**
   - 访问：https://open.weixin.qq.com
   - 注册并完成开发者认证（企业认证或个人认证）
   - **费用**：企业认证 300元/年（必需）

2. **创建网站应用**
   - 进入"管理中心" → "网站应用"
   - 点击"创建网站应用"
   - 填写应用信息：
     - 应用名称：GaiYa 每日进度条
     - 应用简介：时间管理工具
     - 应用官网：https://gaiya.cn（您的域名）
     - **授权回调域**：`https://jindutiao.vercel.app/api/auth-wechat-callback`

3. **获取凭证**
   - 审核通过后（通常1-3个工作日），获取：
     - **AppID**: `wx1234567890abcdef`（示例）
     - **AppSecret**: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p`（示例）
   - **⚠️ 重要**：AppSecret绝对不能暴露在客户端代码中！

### 2.2 技术准备

**后端技术栈**：
- Vercel Serverless Functions（Python）
- requests库（HTTP请求）
- JWT（用户Token管理）

**前端技术栈**：
- PySide6/Qt（桌面应用UI）
- QWebEngineView（内嵌浏览器组件，用于显示二维码）

**环境变量配置**（Vercel后端）：
```bash
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
JWT_SECRET=your_jwt_secret_key
```

---

## 3. 技术架构设计

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      GaiYa 桌面应用                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AuthDialog (UI层)                                   │   │
│  │  ┌────────────┐  ┌────────────┐                    │   │
│  │  │ 微信扫码登录│  │ 邮箱登录   │                    │   │
│  │  │  (默认)     │  │  (切换)    │                    │   │
│  │  └────────────┘  └────────────┘                    │   │
│  │         ↓                ↓                          │   │
│  │  ┌─────────────────────────────────────────┐       │   │
│  │  │  WeChatLoginWidget (二维码显示)         │       │   │
│  │  │  - QWebEngineView 显示微信二维码        │       │   │
│  │  │  - 轮询检查登录状态                      │       │   │
│  │  └─────────────────────────────────────────┘       │   │
│  │         ↓                                           │   │
│  │  ┌─────────────────────────────────────────┐       │   │
│  │  │  AuthClient (API层)                     │       │   │
│  │  │  - wechat_get_qr_code()                 │       │   │
│  │  │  - wechat_check_scan_status()           │       │   │
│  │  │  - wechat_exchange_token()              │       │   │
│  │  └─────────────────────────────────────────┘       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│              Vercel 后端 (jindutiao.vercel.app)              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API端点:                                            │   │
│  │  - /api/auth-wechat-qrcode  → 生成授权URL          │   │
│  │  - /api/auth-wechat-callback → 处理微信回调        │   │
│  │  - /api/auth-wechat-status  → 轮询登录状态         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│              微信开放平台 API                                │
│  - open.weixin.qq.com/connect/qrconnect (生成二维码)        │
│  - api.weixin.qq.com/sns/oauth2/access_token (获取Token)   │
│  - api.weixin.qq.com/sns/userinfo (获取用户信息)            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 数据流设计

**状态流转**：

```
用户打开登录页面
    ↓
显示微信扫码登录（默认）
    ↓
点击"微信扫码登录"按钮
    ↓
客户端请求后端生成state参数
    ↓
后端生成state，存入Redis/数据库（TTL 5分钟）
    ↓
客户端获取授权URL（带state参数）
    ↓
在QWebEngineView中加载微信二维码页面
    ↓
用户用微信扫描二维码
    ↓
用户在手机上确认授权
    ↓
微信回调后端 /api/auth-wechat-callback?code=xxx&state=xxx
    ↓
后端验证state → 用code换access_token → 获取用户信息
    ↓
后端创建/更新用户账号 → 生成JWT Token
    ↓
后端将state状态更新为"success"，存储JWT Token
    ↓
客户端轮询检测到"success" → 获取JWT Token
    ↓
客户端保存Token → 关闭登录窗口 → 用户登录成功
```

---

## 4. OAuth 2.0 完整流程

### 4.1 阶段1: 请求授权码（生成二维码）

**客户端 → 后端**：
```http
GET /api/auth-wechat-qrcode
```

**后端处理**：
```python
import secrets
import time

def generate_qr_code():
    # 1. 生成唯一的state参数（防CSRF攻击）
    state = secrets.token_urlsafe(32)  # 随机字符串

    # 2. 存入临时存储（Redis或内存，TTL 5分钟）
    cache[state] = {
        "status": "pending",  # pending | scanned | success | error
        "created_at": time.time(),
        "user_token": None
    }

    # 3. 构造微信授权URL
    params = {
        "appid": WECHAT_APP_ID,
        "redirect_uri": "https://jindutiao.vercel.app/api/auth-wechat-callback",
        "response_type": "code",
        "scope": "snsapi_login",  # 网站应用使用snsapi_login
        "state": state
    }

    auth_url = f"https://open.weixin.qq.com/connect/qrconnect?{urlencode(params)}#wechat_redirect"

    return {
        "success": True,
        "auth_url": auth_url,
        "state": state  # 返回给客户端用于轮询
    }
```

**返回给客户端**：
```json
{
    "success": true,
    "auth_url": "https://open.weixin.qq.com/connect/qrconnect?appid=wx...&redirect_uri=...&state=abc123",
    "state": "abc123xyz456..."
}
```

**客户端使用**：
```python
# 在QWebEngineView中加载二维码页面
web_view.setUrl(QUrl(auth_url))
```

### 4.2 阶段2: 用户扫码授权（微信回调）

**用户操作**：
1. 打开微信 → 扫一扫 → 扫描桌面二维码
2. 手机上确认授权

**微信回调后端**：
```http
GET /api/auth-wechat-callback?code=CODE&state=STATE
```

**后端处理**：
```python
def handle_wechat_callback(code: str, state: str):
    # 1. 验证state参数（防止CSRF攻击）
    if state not in cache or cache[state]["status"] != "pending":
        return {"error": "Invalid state"}

    # 2. 用code换取access_token
    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    params = {
        "appid": WECHAT_APP_ID,
        "secret": WECHAT_APP_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }

    response = requests.get(token_url, params=params, timeout=10)
    token_data = response.json()

    if "errcode" in token_data:
        cache[state]["status"] = "error"
        cache[state]["error"] = token_data.get("errmsg")
        return {"error": token_data.get("errmsg")}

    access_token = token_data["access_token"]
    openid = token_data["openid"]

    # 3. 获取用户信息
    userinfo_url = "https://api.weixin.qq.com/sns/userinfo"
    params = {
        "access_token": access_token,
        "openid": openid
    }

    response = requests.get(userinfo_url, params=params, timeout=10)
    user_data = response.json()

    # 4. 创建或更新用户账号
    user = find_or_create_user_by_wechat(
        openid=openid,
        unionid=user_data.get("unionid"),
        nickname=user_data.get("nickname"),
        avatar=user_data.get("headimgurl")
    )

    # 5. 生成JWT Token
    jwt_token = generate_jwt_token(user_id=user["user_id"])

    # 6. 更新state状态
    cache[state] = {
        "status": "success",
        "jwt_token": jwt_token,
        "user_info": {
            "user_id": user["user_id"],
            "email": user["email"],
            "user_tier": user["user_tier"]
        }
    }

    # 7. 返回成功页面（用户在手机上看到）
    return render_template("wechat_success.html")
```

### 4.3 阶段3: 客户端轮询获取Token

**客户端轮询**：
```python
import time

def poll_wechat_login_status(state: str, timeout: int = 120):
    """
    轮询检查微信登录状态

    参数:
        state: 步骤1返回的state参数
        timeout: 超时时间（秒），默认120秒

    返回:
        {
            "status": "success|pending|error|timeout",
            "jwt_token": "...",  # status=success时返回
            "user_info": {...}    # status=success时返回
        }
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        # 每2秒轮询一次
        time.sleep(2)

        response = requests.get(
            f"{backend_url}/api/auth-wechat-status",
            params={"state": state},
            timeout=5
        )

        data = response.json()
        status = data.get("status")

        if status == "success":
            # 登录成功！获取Token
            return {
                "success": True,
                "jwt_token": data["jwt_token"],
                "user_info": data["user_info"]
            }
        elif status == "error":
            # 登录失败
            return {
                "success": False,
                "error": data.get("error", "登录失败")
            }
        # status == "pending" 继续轮询

    # 超时
    return {
        "success": False,
        "error": "登录超时，请重新扫码"
    }
```

**后端轮询接口**：
```python
def check_wechat_status(state: str):
    """
    检查state对应的登录状态
    """
    if state not in cache:
        return {"status": "error", "error": "Invalid state"}

    data = cache[state]

    # 检查是否超时（5分钟）
    if time.time() - data["created_at"] > 300:
        cache.pop(state)
        return {"status": "timeout"}

    if data["status"] == "success":
        # 返回Token（只返回一次，之后删除）
        jwt_token = data["jwt_token"]
        user_info = data["user_info"]
        cache.pop(state)  # 用完即删

        return {
            "status": "success",
            "jwt_token": jwt_token,
            "user_info": user_info
        }
    elif data["status"] == "error":
        error = data.get("error", "Unknown error")
        cache.pop(state)
        return {"status": "error", "error": error}
    else:
        # pending 或 scanned
        return {"status": data["status"]}
```

---

## 5. 前端实现

### 5.1 修改 AuthDialog UI布局

**需求**：
- **默认显示**：微信扫码登录按钮（大按钮）
- **次要显示**："切换到邮箱登录"链接（小字链接）
- **切换后**：显示原有的邮箱登录表单

**修改 `gaiya/ui/auth_ui.py`**：

```python
class AuthDialog(QDialog):
    """认证对话框（支持微信扫码 + 邮箱登录）"""

    login_success = Signal(dict)

    def __init__(self, parent=None, auth_client=None):
        super().__init__(parent)
        self.auth_client = auth_client if auth_client is not None else AuthClient()

        # 登录模式: "wechat" | "email"
        self.login_mode = "wechat"

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("GaiYa - 账户登录")
        self.setMinimumWidth(450)
        self.setMinimumHeight(500)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("欢迎使用 GaiYa")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("每日进度条 - 让时间可视化")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(subtitle_label)

        # 登录方式容器（Stack布局，可切换）
        self.login_stack = QStackedWidget()

        # 微信登录页面
        self.wechat_login_widget = self._create_wechat_login_widget()
        self.login_stack.addWidget(self.wechat_login_widget)

        # 邮箱登录页面（原有的Tab Widget）
        self.email_login_widget = self._create_email_login_widget()
        self.login_stack.addWidget(self.email_login_widget)

        main_layout.addWidget(self.login_stack)

        # 底部说明
        info_label = QLabel("注册即表示同意服务条款和隐私政策")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #999; font-size: 10px;")
        main_layout.addWidget(info_label)

        self.setLayout(main_layout)

    def _create_wechat_login_widget(self) -> QWidget:
        """创建微信扫码登录页面"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 说明文字
        tip_label = QLabel("请选择登录方式")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(tip_label)

        # 微信扫码登录按钮（大按钮）
        wechat_btn = QPushButton("  微信扫码登录")
        wechat_btn.setMinimumHeight(50)
        wechat_btn.setIcon(QIcon("path/to/wechat_icon.png"))  # 微信图标
        wechat_btn.setIconSize(QSize(24, 24))
        wechat_btn.setStyleSheet("""
            QPushButton {
                background-color: #07C160;  /* 微信绿 */
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #06AD56;
            }
            QPushButton:pressed {
                background-color: #059A4C;
            }
        """)
        wechat_btn.clicked.connect(self._on_wechat_login_clicked)
        layout.addWidget(wechat_btn)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        layout.addWidget(separator)

        # 切换到邮箱登录链接
        switch_btn = QPushButton("使用邮箱登录")
        switch_btn.setFlat(True)
        switch_btn.setStyleSheet("""
            QPushButton {
                color: #4CAF50;
                text-decoration: underline;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #45a049;
            }
        """)
        switch_btn.clicked.connect(self._switch_to_email_login)
        layout.addWidget(switch_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_email_login_widget(self) -> QWidget:
        """创建邮箱登录页面（原有的TabWidget）"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 返回按钮
        back_btn = QPushButton("← 返回微信登录")
        back_btn.setFlat(True)
        back_btn.setStyleSheet("color: #666; text-decoration: none;")
        back_btn.clicked.connect(self._switch_to_wechat_login)
        layout.addWidget(back_btn)

        # 原有的Tab Widget（登录/注册）
        self.tab_widget = QTabWidget()
        self.signin_widget = self._create_signin_tab()  # 原有代码
        self.tab_widget.addTab(self.signin_widget, "登录")
        self.signup_widget = self._create_signup_tab()  # 原有代码
        self.tab_widget.addTab(self.signup_widget, "注册")

        layout.addWidget(self.tab_widget)

        widget.setLayout(layout)
        return widget

    def _switch_to_email_login(self):
        """切换到邮箱登录模式"""
        self.login_mode = "email"
        self.login_stack.setCurrentWidget(self.email_login_widget)

    def _switch_to_wechat_login(self):
        """切换到微信登录模式"""
        self.login_mode = "wechat"
        self.login_stack.setCurrentWidget(self.wechat_login_widget)

    def _on_wechat_login_clicked(self):
        """处理微信登录按钮点击"""
        # 显示微信扫码窗口
        wechat_dialog = WeChatScanDialog(self, self.auth_client)
        wechat_dialog.login_success.connect(self._on_wechat_login_success)
        wechat_dialog.exec()

    def _on_wechat_login_success(self, user_info: dict):
        """微信登录成功回调"""
        # 发出登录成功信号
        self.login_success.emit(user_info)
        # 关闭对话框
        self.accept()

    # ... 原有的 _create_signin_tab, _create_signup_tab,
    #     _on_signin_clicked, _on_signup_clicked 等方法保持不变
```

### 5.2 创建微信扫码窗口组件

**新建文件 `gaiya/ui/wechat_scan_dialog.py`**：

```python
"""
GaiYa - 微信扫码登录对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QFont
import logging


class WeChatScanDialog(QDialog):
    """微信扫码登录对话框"""

    login_success = Signal(dict)  # 登录成功信号

    def __init__(self, parent=None, auth_client=None):
        super().__init__(parent)
        self.auth_client = auth_client
        self.state = None  # 用于轮询的state参数
        self.poll_timer = None
        self.logger = logging.getLogger(__name__)

        self.init_ui()
        self.start_wechat_login()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("微信扫码登录")
        self.setMinimumWidth(450)
        self.setMinimumHeight(550)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("请使用微信扫一扫")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 提示文字
        tip_label = QLabel("打开微信扫一扫，扫描下方二维码完成登录")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(tip_label)

        # 二维码显示区域（使用QWebEngineView）
        self.qr_web_view = QWebEngineView()
        self.qr_web_view.setMinimumHeight(350)
        layout.addWidget(self.qr_web_view)

        # 状态提示
        self.status_label = QLabel("正在加载二维码...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)

    def start_wechat_login(self):
        """开始微信登录流程"""
        # 1. 请求后端生成二维码
        result = self.auth_client.wechat_get_qr_code()

        if not result.get("success"):
            error_msg = result.get("error", "获取二维码失败")
            self.logger.error(f"获取微信二维码失败: {error_msg}")
            QMessageBox.critical(self, "错误", f"获取二维码失败：{error_msg}")
            self.reject()
            return

        # 2. 加载二维码页面
        auth_url = result["auth_url"]
        self.state = result["state"]

        self.qr_web_view.setUrl(QUrl(auth_url))
        self.status_label.setText("请使用微信扫描二维码")

        # 3. 开始轮询检查登录状态
        self.start_polling()

    def start_polling(self):
        """开始轮询登录状态"""
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_login_status)
        self.poll_timer.start(2000)  # 每2秒轮询一次

        # 设置120秒超时
        QTimer.singleShot(120000, self.on_timeout)

    def check_login_status(self):
        """检查登录状态"""
        if not self.state:
            return

        result = self.auth_client.wechat_check_scan_status(self.state)
        status = result.get("status")

        if status == "success":
            # 登录成功！
            self.poll_timer.stop()

            user_info = {
                "user_id": result.get("user_id"),
                "email": result.get("email"),
                "user_tier": result.get("user_tier", "free")
            }

            # 保存Token
            jwt_token = result.get("jwt_token")
            refresh_token = result.get("refresh_token")
            self.auth_client._save_tokens(jwt_token, refresh_token, user_info)

            # 发出成功信号
            self.login_success.emit(user_info)

            # 关闭对话框
            self.accept()

        elif status == "scanned":
            # 用户已扫码，等待确认
            self.status_label.setText("扫码成功，请在手机上确认")

        elif status == "error":
            # 登录失败
            self.poll_timer.stop()
            error_msg = result.get("error", "登录失败")
            self.logger.error(f"微信登录失败: {error_msg}")
            QMessageBox.critical(self, "登录失败", f"登录失败：{error_msg}")
            self.reject()

        # status == "pending" 继续轮询

    def on_timeout(self):
        """超时处理"""
        if self.poll_timer and self.poll_timer.isActive():
            self.poll_timer.stop()
            QMessageBox.warning(self, "超时", "登录超时，请重新尝试")
            self.reject()

    def closeEvent(self, event):
        """关闭事件"""
        if self.poll_timer:
            self.poll_timer.stop()
        super().closeEvent(event)
```

### 5.3 扩展 AuthClient 添加微信登录方法

**修改 `gaiya/core/auth_client.py`**，添加以下方法：

```python
class AuthClient:
    # ... 原有代码 ...

    # ==================== 微信登录API ====================

    def wechat_get_qr_code(self) -> Dict:
        """
        获取微信扫码登录的二维码URL和state参数

        返回:
            {
                "success": True,
                "auth_url": "https://open.weixin.qq.com/connect/qrconnect?...",
                "state": "abc123xyz..."
            }
        """
        try:
            response = requests.get(
                f"{self.backend_url}/api/auth-wechat-qrcode",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"获取微信二维码失败: {e}")
            return {
                "success": False,
                "error": f"网络错误: {str(e)}"
            }

    def wechat_check_scan_status(self, state: str) -> Dict:
        """
        检查微信扫码登录状态

        参数:
            state: 步骤1返回的state参数

        返回:
            {
                "status": "pending|scanned|success|error",
                "jwt_token": "...",      # status=success时有
                "refresh_token": "...",  # status=success时有
                "user_id": "...",        # status=success时有
                "email": "...",          # status=success时有
                "user_tier": "free"      # status=success时有
            }
        """
        try:
            response = requests.get(
                f"{self.backend_url}/api/auth-wechat-status",
                params={"state": state},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"检查微信登录状态失败: {e}")
            return {
                "status": "error",
                "error": f"网络错误: {str(e)}"
            }
```

---

## 6. 后端实现

### 6.1 生成二维码接口

**创建文件 `api/auth-wechat-qrcode.py`**：

```python
"""
微信扫码登录 - 生成授权URL
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
import time
from urllib.parse import urlencode

# 临时存储（生产环境应使用Redis）
# 格式: {state: {"status": "pending|success|error", "created_at": timestamp, "jwt_token": None}}
state_cache = {}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """生成微信授权URL"""
        try:
            # 1. 生成唯一的state参数
            state = secrets.token_urlsafe(32)

            # 2. 存入临时缓存（TTL 5分钟）
            state_cache[state] = {
                "status": "pending",
                "created_at": time.time(),
                "jwt_token": None,
                "user_info": None
            }

            # 3. 清理过期的state（超过5分钟）
            cleanup_expired_states()

            # 4. 构造微信授权URL
            wechat_app_id = os.getenv("WECHAT_APP_ID")
            if not wechat_app_id:
                raise ValueError("WECHAT_APP_ID environment variable not set")

            redirect_uri = "https://jindutiao.vercel.app/api/auth-wechat-callback"

            params = {
                "appid": wechat_app_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "snsapi_login",  # 网站应用
                "state": state
            }

            auth_url = f"https://open.weixin.qq.com/connect/qrconnect?{urlencode(params)}#wechat_redirect"

            # 5. 返回结果
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                "success": True,
                "auth_url": auth_url,
                "state": state
            }

            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {
                "success": False,
                "error": str(e)
            }

            self.wfile.write(json.dumps(error_response).encode('utf-8'))


def cleanup_expired_states():
    """清理超过5分钟的state"""
    current_time = time.time()
    expired_states = [
        state for state, data in state_cache.items()
        if current_time - data["created_at"] > 300  # 5分钟
    ]

    for state in expired_states:
        state_cache.pop(state, None)
```

### 6.2 微信回调处理接口

**创建文件 `api/auth-wechat-callback.py`**：

```python
"""
微信扫码登录 - 回调处理
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import requests
import sys

# 导入state缓存（注意：实际项目中应使用共享存储如Redis）
from . import wechat_qrcode
state_cache = wechat_qrcode.state_cache


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理微信回调"""
        try:
            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            code = query_params.get('code', [None])[0]
            state = query_params.get('state', [None])[0]

            if not code or not state:
                raise ValueError("Missing code or state parameter")

            # 2. 验证state
            if state not in state_cache or state_cache[state]["status"] != "pending":
                raise ValueError("Invalid or expired state")

            # 3. 用code换取access_token
            wechat_app_id = os.getenv("WECHAT_APP_ID")
            wechat_app_secret = os.getenv("WECHAT_APP_SECRET")

            token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
            params = {
                "appid": wechat_app_id,
                "secret": wechat_app_secret,
                "code": code,
                "grant_type": "authorization_code"
            }

            token_response = requests.get(token_url, params=params, timeout=10)
            token_data = token_response.json()

            if "errcode" in token_data:
                raise Exception(f"WeChat API error: {token_data.get('errmsg')}")

            access_token = token_data["access_token"]
            openid = token_data["openid"]
            unionid = token_data.get("unionid")  # 可能没有

            # 4. 获取用户信息
            userinfo_url = "https://api.weixin.qq.com/sns/userinfo"
            userinfo_params = {
                "access_token": access_token,
                "openid": openid
            }

            userinfo_response = requests.get(userinfo_url, params=userinfo_params, timeout=10)
            user_data = userinfo_response.json()

            if "errcode" in user_data:
                raise Exception(f"WeChat API error: {user_data.get('errmsg')}")

            # 5. 创建或更新用户账号
            user = find_or_create_user_by_wechat(
                openid=openid,
                unionid=unionid,
                nickname=user_data.get("nickname"),
                avatar=user_data.get("headimgurl"),
                sex=user_data.get("sex"),
                country=user_data.get("country"),
                province=user_data.get("province"),
                city=user_data.get("city")
            )

            # 6. 生成JWT Token
            jwt_token = generate_jwt_token(user_id=user["user_id"])
            refresh_token = generate_refresh_token(user_id=user["user_id"])

            # 7. 更新state状态
            state_cache[state] = {
                "status": "success",
                "created_at": state_cache[state]["created_at"],
                "jwt_token": jwt_token,
                "refresh_token": refresh_token,
                "user_info": {
                    "user_id": user["user_id"],
                    "email": user.get("email"),
                    "user_tier": user.get("user_tier", "free"),
                    "nickname": user.get("nickname"),
                    "avatar": user.get("avatar")
                }
            }

            # 8. 返回成功页面（用户在手机上看到）
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>登录成功</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        text-align: center;
                        padding: 50px 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .success-icon {
                        font-size: 64px;
                        margin-bottom: 20px;
                    }
                    h1 {
                        font-size: 28px;
                        margin-bottom: 10px;
                    }
                    p {
                        font-size: 16px;
                        opacity: 0.9;
                    }
                </style>
            </head>
            <body>
                <div class="success-icon">✅</div>
                <h1>登录成功！</h1>
                <p>请返回桌面应用继续使用</p>
            </body>
            </html>
            """

            self.wfile.write(success_html.encode('utf-8'))

        except Exception as e:
            # 更新state状态为error
            if state and state in state_cache:
                state_cache[state]["status"] = "error"
                state_cache[state]["error"] = str(e)

            # 返回错误页面
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>登录失败</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        text-align: center;
                        padding: 50px 20px;
                        background: #f5f5f5;
                    }}
                    .error-icon {{
                        font-size: 64px;
                        margin-bottom: 20px;
                    }}
                    h1 {{
                        font-size: 28px;
                        color: #e74c3c;
                        margin-bottom: 10px;
                    }}
                    p {{
                        font-size: 16px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="error-icon">❌</div>
                <h1>登录失败</h1>
                <p>{str(e)}</p>
                <p>请返回桌面应用重试</p>
            </body>
            </html>
            """

            self.wfile.write(error_html.encode('utf-8'))


def find_or_create_user_by_wechat(openid, unionid, nickname, avatar, **kwargs):
    """
    根据微信OpenID查找或创建用户

    实际项目中应连接数据库实现此逻辑
    """
    # TODO: 实现数据库查询和创建逻辑
    # 伪代码示例:
    """
    user = db.query(User).filter(User.wechat_openid == openid).first()

    if not user:
        # 创建新用户
        user = User(
            wechat_openid=openid,
            wechat_unionid=unionid,
            nickname=nickname,
            avatar=avatar,
            user_tier="free",
            created_at=datetime.now()
        )
        db.add(user)
        db.commit()
    else:
        # 更新用户信息
        user.nickname = nickname
        user.avatar = avatar
        db.commit()

    return {
        "user_id": user.id,
        "email": user.email,
        "user_tier": user.user_tier,
        "nickname": user.nickname,
        "avatar": user.avatar
    }
    """

    # 临时返回示例数据
    return {
        "user_id": f"wechat_{openid}",
        "email": None,  # 微信登录可能没有邮箱
        "user_tier": "free",
        "nickname": nickname,
        "avatar": avatar
    }


def generate_jwt_token(user_id: str) -> str:
    """生成JWT Token"""
    import jwt
    from datetime import datetime, timedelta

    jwt_secret = os.getenv("JWT_SECRET", "your_secret_key")

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30),  # 30天过期
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return token


def generate_refresh_token(user_id: str) -> str:
    """生成Refresh Token"""
    import secrets
    # 简易实现，实际项目应存储到数据库
    return secrets.token_urlsafe(64)
```

### 6.3 状态轮询接口

**创建文件 `api/auth-wechat-status.py`**：

```python
"""
微信扫码登录 - 状态轮询
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import time

# 导入state缓存
from . import wechat_qrcode
state_cache = wechat_qrcode.state_cache


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """检查微信登录状态"""
        try:
            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            state = query_params.get('state', [None])[0]

            if not state:
                raise ValueError("Missing state parameter")

            # 2. 检查state是否存在
            if state not in state_cache:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                response = {
                    "status": "error",
                    "error": "Invalid or expired state"
                }

                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # 3. 获取状态数据
            data = state_cache[state]

            # 4. 检查是否超时（5分钟）
            if time.time() - data["created_at"] > 300:
                state_cache.pop(state)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                response = {
                    "status": "timeout",
                    "error": "Login timeout"
                }

                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # 5. 返回状态
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            status = data["status"]

            if status == "success":
                # 返回Token并删除state（仅返回一次）
                response = {
                    "status": "success",
                    "jwt_token": data["jwt_token"],
                    "refresh_token": data["refresh_token"],
                    "user_id": data["user_info"]["user_id"],
                    "email": data["user_info"].get("email"),
                    "user_tier": data["user_info"].get("user_tier", "free"),
                    "nickname": data["user_info"].get("nickname"),
                    "avatar": data["user_info"].get("avatar")
                }

                # 用完即删
                state_cache.pop(state)

            elif status == "error":
                # 返回错误并删除state
                response = {
                    "status": "error",
                    "error": data.get("error", "Unknown error")
                }

                state_cache.pop(state)

            else:
                # pending 或其他状态，继续轮询
                response = {
                    "status": status
                }

            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {
                "status": "error",
                "error": str(e)
            }

            self.wfile.write(json.dumps(error_response).encode('utf-8'))
```

---

## 7. 安全性考虑

### 7.1 关键安全措施

| 威胁 | 防御措施 |
|------|----------|
| **CSRF攻击** | 使用state参数（随机字符串），每次请求生成新的state |
| **重放攻击** | state只能使用一次，使用后立即删除 |
| **Token泄露** | AppSecret仅存储在后端，绝不暴露给客户端 |
| **中间人攻击** | 所有请求使用HTTPS加密 |
| **存储安全** | JWT Token存储在用户目录下的隐藏文件（~/.gaiya/auth.json），权限600 |

### 7.2 安全最佳实践

1. **环境变量管理**
   ```bash
   # Vercel后端设置环境变量（不要硬编码！）
   WECHAT_APP_ID=wx1234567890abcdef
   WECHAT_APP_SECRET=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
   JWT_SECRET=your_super_secret_jwt_key
   ```

2. **HTTPS强制**
   - 所有API调用必须使用HTTPS
   - 微信开放平台要求回调域必须是HTTPS

3. **Token有效期管理**
   - Access Token: 30天
   - Refresh Token: 90天
   - 定期刷新Token，避免长期有效

4. **日志安全**
   - 不要在日志中记录敏感信息（code, token, secret）
   - 仅记录必要的调试信息

---

## 8. 用户体验优化

### 8.1 快速登录优化

**微信新功能：桌面快捷登录**（微信 3.9.11+ Windows, 4.0.0+ Mac）

如果用户已登录桌面微信，可以无需扫码直接确认登录。

**实现方式**：
在生成授权URL时，添加参数 `pc_login=true`：

```python
params = {
    "appid": WECHAT_APP_ID,
    "redirect_uri": redirect_uri,
    "response_type": "code",
    "scope": "snsapi_login",
    "state": state,
    "pc_login": "true"  # 启用桌面快捷登录
}
```

### 8.2 UI交互优化

1. **加载提示**
   - 显示"正在加载二维码..."
   - 显示加载动画

2. **扫码状态提示**
   - 用户扫码后，显示"扫码成功，请在手机上确认"
   - 实时更新状态

3. **超时处理**
   - 120秒超时后，提示用户刷新二维码
   - 提供"刷新二维码"按钮

4. **错误处理**
   - 网络错误：提示"网络连接失败，请检查网络"
   - 授权失败：提示"授权失败，请重新尝试"

5. **便捷切换**
   - 提供醒目的"使用邮箱登录"链接
   - 切换后保留用户输入的数据（如果有）

---

## 9. 实施步骤

### 9.1 准备阶段（1-2天）

- [ ] **任务1**: 注册微信开放平台开发者账号
- [ ] **任务2**: 创建网站应用并提交审核
- [ ] **任务3**: 准备域名和HTTPS证书（如需）
- [ ] **任务4**: 阅读微信官方文档，熟悉API

### 9.2 后端开发阶段（2-3天）

- [ ] **任务5**: 创建3个后端API接口：
  - `api/auth-wechat-qrcode.py`
  - `api/auth-wechat-callback.py`
  - `api/auth-wechat-status.py`
- [ ] **任务6**: 配置Vercel环境变量
- [ ] **任务7**: 实现用户创建/查询逻辑（数据库）
- [ ] **任务8**: 实现JWT Token生成和验证
- [ ] **任务9**: 后端接口测试（使用Postman或curl）

### 9.3 前端开发阶段（3-4天）

- [ ] **任务10**: 修改 `AuthDialog`，添加微信登录入口
- [ ] **任务11**: 创建 `WeChatScanDialog` 微信扫码窗口
- [ ] **任务12**: 扩展 `AuthClient`，添加微信登录方法
- [ ] **任务13**: 集成 `QWebEngineView`，显示二维码
- [ ] **任务14**: 实现轮询逻辑，检查登录状态
- [ ] **任务15**: 实现错误处理和超时逻辑
- [ ] **任务16**: 前端UI美化和交互优化

### 9.4 测试阶段（2-3天）

- [ ] **任务17**: 单元测试（后端API）
- [ ] **任务18**: 集成测试（前后端联调）
- [ ] **任务19**: 用户体验测试（真实设备测试）
- [ ] **任务20**: 安全测试（CSRF、重放攻击等）
- [ ] **任务21**: 性能测试（并发登录测试）

### 9.5 部署上线阶段（1天）

- [ ] **任务22**: Vercel后端部署
- [ ] **任务23**: 更新桌面应用版本
- [ ] **任务24**: 监控日志，观察登录成功率
- [ ] **任务25**: 准备回滚方案（如果出现问题）

**预计总耗时**: 8-12天（不包括微信审核时间）

---

## 10. 常见问题

### Q1: 微信开放平台审核需要多久？
**A**: 通常1-3个工作日，提交完整的资料可以加快审核速度。

### Q2: 个人开发者可以申请吗？
**A**: 可以，但需要完成个人认证。企业认证的审核速度更快且权限更多。

### Q3: 回调域可以是localhost吗？
**A**: 不可以。微信要求回调域必须是公网域名，且必须支持HTTPS。开发时可以使用内网穿透工具（如ngrok）。

### Q4: 如何处理用户微信账号与邮箱账号的绑定？
**A**:
- 方案1：首次微信登录时，询问用户是否绑定已有邮箱账号
- 方案2：在个人中心提供"账号绑定"功能
- 方案3：自动合并账号（需谨慎处理）

### Q5: 微信登录后，用户的邮箱从哪里来？
**A**: 微信登录默认不提供邮箱信息。可以：
- 首次登录时要求用户补充邮箱
- 使用微信OpenID作为唯一标识，不强制邮箱

### Q6: 如何测试微信登录？
**A**:
1. 使用微信开放平台提供的测试账号
2. 使用内网穿透工具（ngrok）将本地后端暴露到公网
3. 在微信开放平台配置测试回调域

### Q7: QWebEngineView显示二维码卡顿怎么办？
**A**:
- 启用硬件加速：`QWebEngineView.settings().setAttribute(...)`
- 优化页面加载速度
- 使用更轻量的二维码显示方案（如直接显示图片）

### Q8: 如何实现"记住登录"功能？
**A**:
- 使用Refresh Token机制
- Token过期前自动刷新
- 用户手动退出时清除Token

---

## 附录

### A. 微信官方文档链接

- **网站应用微信登录开发指南**: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html
- **微信开放平台**: https://open.weixin.qq.com
- **OAuth 2.0授权**: https://oauth.net/2/

### B. 依赖库安装

**后端（Vercel）**：
```bash
pip install requests PyJWT
```

**前端（PySide6）**：
```bash
pip install PySide6 PySide6-WebEngine
```

### C. 示例项目参考

- **Python微信登录示例**: https://github.com/wechat-sdk/python-wechat
- **Qt WebEngine示例**: https://doc.qt.io/qt-6/qtwebengine-examples.html

---

**文档维护**: 请在接入过程中遇到问题时，及时更新本文档，帮助后续开发者。

**最后更新**: 2025-11-10
**作者**: Claude AI Assistant
**版本**: v1.0
