# GaiYa 认证系统测试指南

本文档提供认证系统的完整测试流程和验证清单。

## 测试环境准备

### 1. 确保后端服务正常运行

后端已部署在 Vercel：`https://jindutiao.vercel.app`

验证后端API可用性：
```bash
# 测试健康检查
curl https://jindutiao.vercel.app/api/health

# 测试配额查询
curl "https://jindutiao.vercel.app/api/quota-status?user_tier=free"
```

### 2. 启动配置管理器

```bash
cd C:\Users\Sats\Downloads\jindutiao
python config_gui.py
```

## 测试清单

### ✅ 阶段1：UI显示测试

- [ ] **启动应用**
  - 应用成功启动，无崩溃
  - 主题正常加载（dark_teal Material主题）

- [ ] **账户Tab显示**
  - 切换到"👤 账户"标签页
  - 账户信息组正常显示
  - 会员功能组正常显示

- [ ] **未登录状态UI**
  - 显示"您尚未登录"提示
  - "登录/注册"按钮可见且可点击
  - 会员功能组显示"登录后可查看会员功能"

### ✅ 阶段2：注册流程测试

- [ ] **打开注册对话框**
  - 点击"登录/注册"按钮
  - 认证对话框弹出
  - 包含"登录"和"注册"两个Tab

- [ ] **切换到注册Tab**
  - 注册Tab可正常切换
  - 表单包含：用户名（可选）、邮箱、密码、确认密码

- [ ] **表单验证**
  - 空邮箱：显示"请输入邮箱和密码"
  - 错误邮箱格式：显示"邮箱格式不正确"
  - 短密码（<6字符）：显示"密码至少需要6个字符"
  - 密码不一致：显示"两次输入的密码不一致"

- [ ] **成功注册**
  - 输入有效信息：
    ```
    用户名: test_user
    邮箱: test@example.com
    密码: test123456
    确认密码: test123456
    ```
  - 点击"注册"按钮
  - 注册按钮文本变为"注册中..."
  - 成功后显示"注册成功"对话框
  - 对话框关闭，返回主窗口

- [ ] **登录状态更新**
  - 账户信息组显示登录邮箱
  - 显示会员等级：免费版（黄色标识）
  - 显示"退出登录"按钮

### ✅ 阶段3：登录流程测试

- [ ] **登出测试**
  - 点击"退出登录"按钮
  - 显示确认对话框
  - 点击"是"
  - 显示"已登出"提示
  - UI恢复为未登录状态

- [ ] **重新登录**
  - 点击"登录/注册"按钮
  - 切换到"登录"Tab
  - 输入之前注册的邮箱和密码
  - 点击"登录"按钮
  - 登录按钮文本变为"登录中..."
  - 成功后显示"登录成功"对话框
  - 账户信息更新

- [ ] **忘记密码功能**
  - 登录Tab中点击"忘记密码？"
  - 弹出输入框
  - 输入邮箱
  - 显示"邮件已发送"提示

### ✅ 阶段4：会员购买流程测试

- [ ] **升级按钮可见**
  - 免费用户登录后
  - 会员功能组显示升级提示
  - 列出专业版功能列表
  - "立即升级"按钮可见

- [ ] **打开会员购买对话框**
  - 点击"立即升级"按钮
  - 会员购买对话框弹出
  - 标题："升级到专业版"
  - 显示当前账户信息

- [ ] **套餐展示**
  - 显示3个套餐卡片：
    - 月度会员（¥9.9）
    - 年度会员（¥99，带⭐推荐标签）
    - 终身会员（¥299）
  - 每个卡片显示价格和功能列表
  - 卡片可点击选中（边框变绿）

- [ ] **支付方式选择**
  - 支付方式组包含"支付宝"和"微信支付"
  - 支付宝默认选中
  - 可切换支付方式

- [ ] **创建支付订单**
  - 选择一个套餐（如月度会员）
  - 点击"立即购买"按钮
  - 按钮文本变为"正在创建订单..."
  - 显示订单确认对话框：
    ```
    套餐: GaiYa专业版 - 月度会员
    金额: ¥9.9
    支付方式: 支付宝
    订单号: GAIYA...
    ```
  - 点击"确定"

- [ ] **支付流程**
  - 浏览器自动打开支付页面
  - 显示"等待支付"对话框
  - 对话框文本："正在等待支付完成..."
  - 可以点击"Cancel"取消等待

- [ ] **支付状态轮询**（需要实际支付或模拟）
  - 每3秒自动查询一次支付状态
  - 支付完成后，等待对话框自动关闭
  - 显示"支付成功"提示
  - 提示"请重新启动应用以生效"
  - 会员购买对话框关闭

- [ ] **会员状态更新**（重启后）
  - 重启应用
  - 账户信息显示会员等级：专业版（绿色标识）
  - 会员功能组显示配额信息：
    ```
    每日任务规划: 50 次
    每周进度报告: 10 次
    AI对话: 100 次
    ```

### ✅ 阶段5：Token管理测试

- [ ] **Token持久化**
  - 登录成功后关闭应用
  - 重新启动应用
  - 账户信息自动显示（无需重新登录）
  - 检查Token文件：`~/.gaiya/auth.json`
    ```json
    {
      "access_token": "...",
      "refresh_token": "...",
      "user_info": { ... },
      "saved_at": "..."
    }
    ```

- [ ] **Token自动刷新**
  - 保持应用运行30分钟
  - Token刷新定时器应该触发
  - 检查日志，无错误信息
  - 用户无感知刷新

- [ ] **Token过期处理**
  - 手动删除或修改Token文件
  - 重启应用
  - 账户信息显示未登录状态
  - 使用AI功能时提示登录

### ✅ 阶段6：集成测试（AI功能配额检查）

**注意：此功能为可选集成，当前版本可能尚未实现**

- [ ] **未登录时使用AI功能**
  - 切换到"任务管理"Tab
  - 点击"✨ 智能生成任务"
  - 应该提示"请先登录后再使用AI功能"

- [ ] **免费用户配额限制**
  - 登录免费账户
  - 使用AI功能（生成任务）
  - 达到每日3次限制后
  - 提示"配额不足"
  - 询问是否升级

- [ ] **专业用户无限制**
  - 登录专业账户
  - 使用AI功能
  - 无配额限制提示
  - 正常生成任务

### ✅ 阶段7：错误处理测试

- [ ] **网络错误**
  - 断开网络连接
  - 尝试登录
  - 显示"无法连接到服务器"错误

- [ ] **错误的登录凭据**
  - 使用错误的邮箱或密码登录
  - 显示具体错误信息（如"密码错误"）

- [ ] **重复注册**
  - 使用已注册的邮箱再次注册
  - 显示"邮箱已被注册"错误

- [ ] **支付失败**
  - 创建订单后不支付
  - 点击"Cancel"取消等待
  - 对话框正常关闭
  - 可以重新尝试

## 自动化测试脚本

### 测试Token文件读写

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'gaiya'))

from gaiya.core.auth_client import AuthClient

# 测试Token管理
auth_client = AuthClient()

# 检查初始状态
print(f"初始登录状态: {auth_client.is_logged_in()}")

# 模拟保存Token
auth_client._save_tokens(
    access_token="test_access_token",
    refresh_token="test_refresh_token",
    user_info={"user_id": "test_user", "email": "test@example.com"}
)

print(f"保存后登录状态: {auth_client.is_logged_in()}")
print(f"用户邮箱: {auth_client.get_user_email()}")
print(f"用户ID: {auth_client.get_user_id()}")

# 重新加载
new_client = AuthClient()
print(f"重新加载后登录状态: {new_client.is_logged_in()}")
print(f"重新加载后用户邮箱: {new_client.get_user_email()}")

# 清除Token
new_client._clear_tokens()
print(f"清除后登录状态: {new_client.is_logged_in()}")
```

### 测试API调用

```python
from gaiya.core.auth_client import AuthClient

auth_client = AuthClient()

# 测试配额查询（无需登录）
quota = auth_client.get_quota_status()
print(f"免费用户配额: {quota}")

# 测试注册（使用新邮箱）
result = auth_client.signup(
    email="test_new@example.com",
    password="test123456",
    username="Test User"
)
print(f"注册结果: {result}")

# 测试登录
result = auth_client.signin(
    email="test_new@example.com",
    password="test123456"
)
print(f"登录结果: {result}")

# 测试订阅状态查询
sub_status = auth_client.get_subscription_status()
print(f"订阅状态: {sub_status}")
```

## 常见问题排查

### 问题1：账户Tab加载失败

**症状**：切换到账户Tab时显示"加载账户信息失败"

**排查步骤**：
1. 检查导入是否正确：`from gaiya.core.auth_client import AuthClient`
2. 检查`gaiya/`目录结构是否完整
3. 查看错误日志：日志中应有详细错误信息
4. 验证`AuthClient`初始化：在Python中手动导入测试

**解决方案**：
```python
# 测试导入
try:
    from gaiya.core.auth_client import AuthClient
    print("导入成功")
    client = AuthClient()
    print(f"客户端初始化成功，后端URL: {client.backend_url}")
except Exception as e:
    print(f"导入或初始化失败: {e}")
```

### 问题2：登录对话框无法打开

**症状**：点击"登录/注册"按钮无响应

**排查步骤**：
1. 检查`AuthDialog`导入
2. 检查按钮连接的槽函数：`login_button.clicked.connect(self._on_login_clicked)`
3. 查看控制台错误日志

**解决方案**：
在`_on_login_clicked`方法中添加调试输出：
```python
def _on_login_clicked(self):
    print("登录按钮被点击")
    try:
        dialog = AuthDialog(self)
        dialog.login_success.connect(self._on_login_success)
        dialog.exec()
    except Exception as e:
        print(f"打开登录对话框失败: {e}")
```

### 问题3：支付页面无法打开

**症状**：点击"立即购买"后浏览器未打开

**排查步骤**：
1. 检查订单创建是否成功：查看返回的`payment_url`
2. 检查`QDesktopServices.openUrl`调用
3. 验证URL格式是否正确

**解决方案**：
```python
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

url = "https://pay.zpay.com/..."
print(f"尝试打开URL: {url}")
result = QDesktopServices.openUrl(QUrl(url))
print(f"打开结果: {result}")
```

### 问题4：Token刷新失败

**症状**：日志中出现"Token刷新失败"警告

**可能原因**：
- Refresh Token已过期
- 网络连接问题
- 后端API异常

**解决方案**：
1. 手动重新登录
2. 检查网络连接
3. 验证后端`/api/auth-refresh`端点可用性

## 测试报告模板

### 测试执行记录

```
测试日期: 2025-11-XX
测试人员: XXX
环境: Windows 10 / Python 3.11
后端: https://jindutiao.vercel.app

阶段1：UI显示测试 - ✅ 通过
阶段2：注册流程测试 - ✅ 通过
阶段3：登录流程测试 - ✅ 通过
阶段4：会员购买流程测试 - ⚠️ 部分通过
  - 订单创建成功
  - 支付页面打开成功
  - 实际支付未测试（需要真实支付）
阶段5：Token管理测试 - ✅ 通过
阶段6：AI功能配额检查 - ⏭️ 跳过（未实现）
阶段7：错误处理测试 - ✅ 通过

总体评价：认证系统基本功能正常，可以进入生产环境测试。
```

## 下一步优化建议

1. **AI功能配额集成**：在`generate_ai_tasks()`方法中添加配额检查
2. **更友好的错误提示**：细化错误信息，提供解决建议
3. **支付状态推送**：考虑使用WebSocket实时推送支付状态，而非轮询
4. **会员到期提醒**：添加会员到期倒计时和续费提醒
5. **多设备登录管理**：支持查看和管理其他设备的登录状态
