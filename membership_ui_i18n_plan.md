# membership_ui.py 国际化方案

## 文件信息
- **文件**: gaiya/ui/membership_ui.py
- **行数**: 1275行
- **中文字符串**: 47个
- **功能**: 会员购买对话框

## 字符串统计

### 总体统计
- **原始字符串**: 47个
- **去重后**: 约35个唯一翻译键
- **重复字符串**: 约12个

### 分类详情

#### 1. 对话框与导航 (membership命名空间)
- 对话框标题
- 按钮文本（购买、取消）
- 未登录提示

#### 2. 套餐信息 (membership.plan子空间)
- 套餐名称（连续包月、连续包年）
- 价格单位
- 特惠标签

#### 3. 功能特性 (membership.feature子空间)
- 功能描述列表
- 节省金额提示

#### 4. 支付流程 (membership.payment子空间)
- 支付方式选择
- 支付状态提示
- 支付成功/失败消息

#### 5. 错误消息 (membership.error子空间)
- 未选择套餐
- 创建订单失败
- 未登录错误

## 翻译键规划

### membership - 对话框基本元素 (8个)

| 原文 | 翻译键 | 使用次数 |
|------|--------|---------|
| 未登录 | membership.not_logged_in | 1 |
| 请先登录后再购买会员 | membership.login_required | 1 |
| 升级到专业版 | membership.upgrade_to_pro | 1 |
| 升级 GaiYa 专业版 | membership.dialog_title | 1 |
| 取消 | membership.btn_cancel | 1 |
| 立即购买 | membership.btn_buy_now | 2 |
| 立即开通 | membership.btn_activate | 1 |

### membership.plan - 套餐信息 (10个)

| 原文 | 翻译键 |
|------|--------|
| 连续包月 | membership.plan.monthly_name |
| 元/月 | membership.plan.per_month |
| ¥0.97/天 | membership.plan.monthly_daily_price |
| 连续包年 | membership.plan.yearly_name |
| 元/年 | membership.plan.per_year |
| ¥0.55/天 | membership.plan.yearly_daily_price |
| 订阅特惠 | membership.plan.subscription_deal |
| 最超值 | membership.plan.best_value |
| 免费版 | membership.plan.free |
| 专业版 | membership.plan.pro |
| 终身会员 | membership.plan.lifetime |

### membership.feature - 功能特性 (9个)

| 原文 | 翻译键 |
|------|--------|
| 智能任务规划 50次/天 | membership.feature.smart_planning_50 |
| 进度报告 10次/周 | membership.feature.progress_report_10 |
| AI助手 100次/天 | membership.feature.ai_assistant_100 |
| 自定义主题 | membership.feature.custom_theme |
| 所有专业版功能 | membership.feature.all_pro_features |
| 节省40元 | membership.feature.save_40 |
| 优先客服支持 | membership.feature.priority_support |
| 新功能优先体验 | membership.feature.early_access |

### membership.payment - 支付流程 (10个)

| 原文 | 翻译键 |
|------|--------|
| 选择支付方式 | membership.payment.select_method |
| 支付宝 | membership.payment.alipay |
| 微信支付 | membership.payment.wechat |
| 正在创建订单... | membership.payment.creating_order |
| 等待支付 | membership.payment.waiting_title |
| 正在等待支付完成...\n\n | membership.payment.waiting_line1 |
| 请在打开的浏览器页面中完成支付。\n | membership.payment.waiting_line2 |
| 支付完成后，此窗口将自动关闭。 | membership.payment.waiting_line3 |
| 支付成功 | membership.payment.success_title |
| 支付已完成！\n您的会员权益已激活。\n\n请重新启动应用以生效。 | membership.payment.success_message |

### membership.error - 错误消息 (5个)

| 原文 | 翻译键 |
|------|--------|
| 未选择套餐 | membership.error.no_plan_selected_title |
| 请选择一个会员套餐 | membership.error.no_plan_selected_message |
| 创建订单失败 | membership.error.order_creation_failed_title |
| 创建订单失败：{error_msg} | membership.error.order_creation_failed |

### 测试代码（不翻译）
- Line 1264: "请先运行 auth_ui.py 登录" (测试代码)
- Line 1270: "购买成功！套餐: {plan_type}" (测试代码)

### 日志消息（不翻译）
- Line 327: "[DIAG-1] MembershipDialog.__init__ 开始" (调试日志)

## 翻译键总结

### 命名空间统计
| 命名空间 | 翻译键数 | 主要用途 |
|---------|---------|---------|
| membership | 8 | 对话框基本元素 |
| membership.plan | 10 | 套餐信息 |
| membership.feature | 8 | 功能特性 |
| membership.payment | 10 | 支付流程 |
| membership.error | 5 | 错误消息 |
| **总计** | **41** | - |

## 参数化翻译

需要参数的翻译键：
1. `membership.error.order_creation_failed`: `{error_msg}`
2. 测试代码中的参数（不翻译）

## 实施建议

### 分阶段实施

#### 第一阶段：基本UI (8个)
- membership命名空间的所有键
- 预计工作量：20分钟

#### 第二阶段：套餐和功能 (18个)
- membership.plan命名空间
- membership.feature命名空间
- 预计工作量：30分钟

#### 第三阶段：支付和错误 (15个)
- membership.payment命名空间
- membership.error命名空间
- 预计工作量：30分钟

### 总预计工作量
- **翻译键添加**: 15分钟
- **代码自动替换**: 20分钟
- **手动修复**: 30分钟
- **验证和测试**: 15分钟
- **总计**: 1.5小时

## 复杂度评估

### 自动化难度
- **简单替换**: 约35个（单行字符串）
- **中等难度**: 约5个（多行字符串拼接）
- **手动处理**: 约2个（复杂的支付等待消息）

### 预计自动化成功率
约85%（基于auth_ui经验）

## 特殊注意事项

### 1. 价格显示
价格单位（¥0.97/天、¥0.55/天）可能需要根据语言环境调整格式

### 2. 多行消息
支付等待消息由3行组成，需要拼接或使用单个包含换行的翻译键

### 3. 测试代码
main部分的测试代码字符串不需要翻译

### 4. 日志消息
调试日志保持英文

## 修改文件清单

- `gaiya/ui/membership_ui.py`: 约41处修改
- `i18n/zh_CN.json`: 添加41个键
- `i18n/en_US.json`: 添加41个键
