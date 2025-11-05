# GaiYa 认证系统集成指南

本文档说明如何在 `config_gui.py` 中集成认证和会员管理功能。

## 1. 导入必要的模块

在 `config_gui.py` 文件顶部添加以下导入：

```python
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gaiya'))

from gaiya.core.auth_client import AuthClient
from gaiya.ui.auth_ui import AuthDialog
from gaiya.ui.membership_ui import MembershipDialog
```

## 2. 在ConfigDialog中初始化认证客户端

在 `ConfigDialog.__init__()` 方法中添加：

```python
class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 初始化认证客户端
        self.auth_client = AuthClient()

        # 加载配置...
        self.config = self.load_config()

        # 初始化UI...
        self.init_ui()
```

## 3. 添加账户管理面板

### 3.1 创建账户Tab页

在 `init_ui()` 方法的Tab创建部分添加：

```python
def init_ui(self):
    # ... 现有代码 ...

    # 账户Tab（新增）
    account_tab = QWidget()
    account_layout = QVBoxLayout()

    # 账户信息显示区域
    self.account_info_widget = self._create_account_info_widget()
    account_layout.addWidget(self.account_info_widget)

    # 会员功能区域
    self.membership_widget = self._create_membership_widget()
    account_layout.addWidget(self.membership_widget)

    account_layout.addStretch()
    account_tab.setLayout(account_layout)

    # 添加到TabWidget
    self.tab_widget.addTab(account_tab, "账户")
```

### 3.2 创建账户信息显示组件

```python
def _create_account_info_widget(self) -> QGroupBox:
    """创建账户信息显示组件"""
    group_box = QGroupBox("账户信息")
    layout = QVBoxLayout()

    if self.auth_client.is_logged_in():
        # 已登录状态
        user_email = self.auth_client.get_user_email()
        user_tier = self.auth_client.get_user_tier()

        # 邮箱显示
        email_label = QLabel(f"登录账户: {user_email}")
        email_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(email_label)

        # 会员等级显示
        tier_name = self._get_tier_name(user_tier)
        tier_label = QLabel(f"会员等级: {tier_name}")
        tier_label.setStyleSheet("font-size: 14px; color: #4CAF50;")
        layout.addWidget(tier_label)

        # 登出按钮
        logout_button = QPushButton("退出登录")
        logout_button.clicked.connect(self._on_logout_clicked)
        layout.addWidget(logout_button)

    else:
        # 未登录状态
        info_label = QLabel("您尚未登录")
        info_label.setStyleSheet("color: #999;")
        layout.addWidget(info_label)

        # 登录按钮
        login_button = QPushButton("登录/注册")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        login_button.clicked.connect(self._on_login_clicked)
        layout.addWidget(login_button)

    group_box.setLayout(layout)
    return group_box

def _get_tier_name(self, tier: str) -> str:
    """获取会员等级名称"""
    tier_names = {
        "free": "免费版",
        "pro": "专业版",
        "lifetime": "终身会员"
    }
    return tier_names.get(tier, tier)
```

### 3.3 创建会员功能组件

```python
def _create_membership_widget(self) -> QGroupBox:
    """创建会员功能组件"""
    group_box = QGroupBox("会员功能")
    layout = QVBoxLayout()

    if not self.auth_client.is_logged_in():
        # 未登录提示
        tip_label = QLabel("登录后可查看会员功能")
        tip_label.setStyleSheet("color: #999;")
        layout.addWidget(tip_label)
    else:
        user_tier = self.auth_client.get_user_tier()

        if user_tier == "free":
            # 免费用户：显示升级按钮
            tip_label = QLabel("升级到专业版，解锁所有高级功能：")
            layout.addWidget(tip_label)

            features_label = QLabel(
                "✓ 每日智能任务规划 50次/天\n"
                "✓ 每周进度报告 10次/周\n"
                "✓ AI对话助手 100次/天\n"
                "✓ 自定义主题和样式\n"
                "✓ 所有高级功能"
            )
            features_label.setStyleSheet("color: #666; margin: 10px 0;")
            layout.addWidget(features_label)

            upgrade_button = QPushButton("立即升级")
            upgrade_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            upgrade_button.clicked.connect(self._on_upgrade_clicked)
            layout.addWidget(upgrade_button)
        else:
            # 专业用户：显示配额信息
            quota_info = self._get_quota_info()

            quota_label = QLabel("您的配额状态：")
            layout.addWidget(quota_label)

            for feature, remaining in quota_info.items():
                feature_label = QLabel(f"{feature}: {remaining}")
                feature_label.setStyleSheet("color: #666; margin-left: 10px;")
                layout.addWidget(feature_label)

    group_box.setLayout(layout)
    return group_box

def _get_quota_info(self) -> dict:
    """获取配额信息"""
    result = self.auth_client.get_quota_status()
    if result.get("success", True):
        remaining = result.get("remaining", {})
        return {
            "每日任务规划": f"{remaining.get('daily_plan', 0)} 次",
            "每周进度报告": f"{remaining.get('weekly_report', 0)} 次",
            "AI对话": f"{remaining.get('chat', 0)} 次"
        }
    return {}
```

## 4. 实现事件处理方法

### 4.1 登录/注册

```python
def _on_login_clicked(self):
    """处理登录按钮点击"""
    dialog = AuthDialog(self)
    dialog.login_success.connect(self._on_login_success)
    dialog.exec()

def _on_login_success(self, user_info: dict):
    """登录成功回调"""
    QMessageBox.information(
        self,
        "登录成功",
        f"欢迎回来，{user_info['email']}！"
    )

    # 刷新账户信息显示
    self._refresh_account_ui()
```

### 4.2 登出

```python
def _on_logout_clicked(self):
    """处理登出按钮点击"""
    reply = QMessageBox.question(
        self,
        "确认登出",
        "确定要退出登录吗？",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        result = self.auth_client.signout()

        if result.get("success"):
            QMessageBox.information(self, "已登出", "您已成功退出登录")
            self._refresh_account_ui()
```

### 4.3 升级会员

```python
def _on_upgrade_clicked(self):
    """处理升级按钮点击"""
    dialog = MembershipDialog(self.auth_client, self)
    dialog.purchase_success.connect(self._on_purchase_success)
    dialog.exec()

def _on_purchase_success(self, plan_type: str):
    """购买成功回调"""
    # 刷新账户信息
    self._refresh_account_ui()

    QMessageBox.information(
        self,
        "购买成功",
        "您的会员权益已激活！\n请重新启动应用以生效。"
    )
```

### 4.4 刷新UI

```python
def _refresh_account_ui(self):
    """刷新账户相关UI"""
    # 移除旧的账户信息组件
    old_widget = self.account_info_widget
    old_widget.deleteLater()

    # 创建新的账户信息组件
    self.account_info_widget = self._create_account_info_widget()

    # 更新布局（需要根据实际布局结构调整）
    # account_layout.replaceWidget(old_widget, self.account_info_widget)

    # 同样刷新会员功能组件
    old_membership_widget = self.membership_widget
    old_membership_widget.deleteLater()
    self.membership_widget = self._create_membership_widget()
```

## 5. 在AI功能中集成配额检查

### 5.1 修改AI任务生成功能

在调用AI功能前检查配额：

```python
def generate_ai_tasks(self):
    """生成AI任务"""
    # 检查登录状态
    if not self.auth_client.is_logged_in():
        QMessageBox.warning(
            self,
            "需要登录",
            "请先登录后再使用AI功能"
        )
        return

    # 检查配额
    quota_result = self.auth_client.get_quota_status()
    remaining = quota_result.get("remaining", {})

    if remaining.get("daily_plan", 0) <= 0:
        # 配额不足，提示升级
        reply = QMessageBox.question(
            self,
            "配额不足",
            "您今日的AI任务规划次数已用完。\n\n"
            "升级到专业版可获得每日50次配额。\n\n"
            "是否立即升级？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._on_upgrade_clicked()

        return

    # 继续执行AI任务生成...
    # ...
```

## 6. 实现Token自动刷新

### 6.1 在主窗口中添加定时器

```python
class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ... 现有代码 ...

        # 设置Token刷新定时器（每30分钟检查一次）
        self.token_refresh_timer = QTimer()
        self.token_refresh_timer.setInterval(30 * 60 * 1000)  # 30分钟
        self.token_refresh_timer.timeout.connect(self._refresh_token_if_needed)
        self.token_refresh_timer.start()

    def _refresh_token_if_needed(self):
        """如果需要则刷新Token"""
        if self.auth_client.is_logged_in():
            result = self.auth_client.refresh_access_token()

            if not result.get("success"):
                # Token刷新失败，可能已过期
                QMessageBox.warning(
                    self,
                    "登录已过期",
                    "您的登录状态已过期，请重新登录"
                )
                self._refresh_account_ui()
```

## 7. 完整集成示例

以下是一个完整的集成示例（精简版）：

```python
# config_gui.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gaiya'))

from gaiya.core.auth_client import AuthClient
from gaiya.ui.auth_ui import AuthDialog
from gaiya.ui.membership_ui import MembershipDialog

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 初始化认证客户端
        self.auth_client = AuthClient()

        # 加载配置
        self.config = self.load_config()

        # 初始化UI
        self.init_ui()

        # 启动Token刷新定时器
        self._start_token_refresh_timer()

    def init_ui(self):
        """初始化UI"""
        # ... 现有代码 ...

        # 添加账户Tab
        account_tab = self._create_account_tab()
        self.tab_widget.addTab(account_tab, "账户")

    def _create_account_tab(self) -> QWidget:
        """创建账户Tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.account_info_widget = self._create_account_info_widget()
        layout.addWidget(self.account_info_widget)

        self.membership_widget = self._create_membership_widget()
        layout.addWidget(self.membership_widget)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # ... 其他方法（参见上面的代码片段）...
```

## 8. 测试清单

集成完成后，请按以下清单测试：

- [ ] 未登录状态下显示登录按钮
- [ ] 点击登录按钮打开登录对话框
- [ ] 注册新账户成功
- [ ] 登录已有账户成功
- [ ] 登录成功后显示用户信息
- [ ] 免费用户显示升级按钮
- [ ] 点击升级按钮打开会员购买对话框
- [ ] 选择套餐并完成支付流程
- [ ] 支付成功后刷新会员状态
- [ ] 专业用户显示配额信息
- [ ] AI功能检查配额限制
- [ ] 配额不足时提示升级
- [ ] 退出登录成功
- [ ] Token自动刷新正常工作

## 9. 注意事项

1. **错误处理**: 所有API调用都应该检查返回的`success`字段，并适当处理错误
2. **UI响应**: 网络请求时应该禁用相关按钮，防止重复点击
3. **数据同步**: 登录/登出后应该刷新所有相关UI组件
4. **配额限制**: 在调用AI功能前务必检查配额，提供友好的提示
5. **安全性**: Token存储在本地文件中，确保文件权限正确设置

## 10. 下一步

集成完成后，可以进一步优化：

1. 添加会员到期提醒
2. 实现配额使用统计图表
3. 添加购买历史记录查询
4. 实现邀请奖励功能
5. 添加客服支持入口
