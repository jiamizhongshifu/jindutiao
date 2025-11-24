# GaiYa Desktop Application - Internationalization Implementation Guide

## 📊 Current Status

### Analysis Complete ✅

| Metric | Value |
|--------|-------|
| Total hardcoded Chinese strings | **1,938** |
| UI strings requiring i18n | **1,183** |
| Non-UI strings (logs, docstrings) | **755** |
| Translation keys prepared | **271** (existing) |
| Additional keys needed | **~800-900** |

### Files by Priority

| Priority | File | Hardcoded Strings | Status |
|----------|------|------------------|--------|
| 🔴 HIGH | config_gui.py | 1,033 | Ready to start |
| 🔴 HIGH | main.py | 362 | Partially done (menus) |
| 🟡 MED | gaiya/ui/auth_ui.py | 142 | Not started |
| 🟡 MED | gaiya/ui/membership_ui.py | 82 | Not started |
| 🟢 LOW | statistics_gui.py | 69 | Not started |
| 🟢 LOW | timeline_editor.py | 15 | Not started |

## 🎯 Implementation Strategy

### Phase 1: High-Impact, Low-Effort (Recommended Start)

Focus on **most visible UI elements** first:

1. **Window/Dialog Titles**
2. **Tab Names**
3. **Button Text**
4. **Common Labels**
5. **Message Boxes**

This gives **maximum visual impact** with **minimum changes**.

---

## 🔧 Step-by-Step Guide

### Step 1: Add Import

At the top of the file, add:

```python
from i18n import tr
```

### Step 2: Replace Hardcoded Strings

#### ✅ Before (Hardcoded):
```python
self.setWindowTitle("配置")
save_button = QPushButton("保存")
QLabel("进度条高度:")
QMessageBox.information(self, "提示", "保存成功")
```

#### ✅ After (Internationalized):
```python
self.setWindowTitle(tr('config.title'))
save_button = QPushButton(tr('button.save'))
QLabel(tr('config.bar_height') + ":")
QMessageBox.information(self, tr('message.info'), tr('message.save_success'))
```

### Step 3: Common Patterns

#### Pattern 1: QLabel with trailing colon
```python
# Before
QLabel("语言:")

# After
QLabel(tr('config.language') + ":")
```

#### Pattern 2: QMessageBox
```python
# Before
QMessageBox.warning(self, "警告", "配置文件损坏")

# After
QMessageBox.warning(self, tr('message.warning'), tr('message.config_corrupted'))
```

#### Pattern 3: ComboBox items
```python
# Before
self.language_combo.addItem("跟随系统", "auto")
self.language_combo.addItem("简体中文", "zh_CN")

# After
self.language_combo.addItem(tr('config.language_auto'), "auto")
self.language_combo.addItem(tr('config.language_zh_cn'), "zh_CN")
```

#### Pattern 4: Format strings
```python
# Before
f"剩余配额: {count}次"

# After
tr('ai.quota_remaining', count=count)  # Uses {count} in translation file
```

---

## 📝 Translation Keys Reference

### Available Translation Keys (271 total)

#### Buttons (28 keys - all available!)
```python
tr('button.ok')           # 确定
tr('button.cancel')       # 取消
tr('button.save')         # 保存
tr('button.apply')        # 应用
tr('button.reset')        # 重置
tr('button.close')        # 关闭
tr('button.delete')       # 删除
tr('button.add')          # 添加
tr('button.edit')         # 编辑
tr('button.refresh')      # 刷新
tr('button.confirm')      # 确认
tr('button.import')       # 导入
tr('button.export')       # 导出
tr('button.preview')      # 预览
tr('button.generate')     # 生成
tr('button.login')        # 登录
tr('button.logout')       # 退出登录
tr('button.register')     # 注册
tr('button.upgrade')      # 升级会员
# ... and 9 more
```

#### Config (26 keys)
```python
tr('config.title')               # 配置 / Settings
tr('config.appearance')          # 外观设置
tr('config.tasks')               # 任务管理
tr('config.ai')                  # AI功能
tr('config.account')             # 账号管理
tr('config.scene')               # 场景设置
tr('config.about')               # 关于
tr('config.language')            # 语言
tr('config.bar_height')          # 进度条高度
tr('config.bar_position')        # 进度条位置
tr('config.transparency')        # 透明度
tr('config.background_color')    # 背景颜色
tr('config.corner_radius')       # 圆角大小
tr('config.shadow')              # 阴影效果
tr('config.auto_start')          # 开机自启动
tr('config.marker_settings')     # 时间标记设置 (NEW)
tr('config.marker_type')         # 标记类型 (NEW)
tr('config.marker_size')         # 标记大小 (NEW)
tr('config.marker_speed')        # 动画速度 (NEW)
# ... and more
```

#### Messages (24 keys)
```python
tr('message.save_success')       # 保存成功
tr('message.save_failed')        # 保存失败
tr('message.load_success')       # 加载成功
tr('message.load_failed')        # 加载失败
tr('message.info')               # 提示
tr('message.warning')            # 警告
tr('message.error')              # 错误
tr('message.success')            # 成功
tr('message.loading')            # 加载中...
tr('message.please_wait')        # 请稍候...
# ... and more
```

#### Tasks (18 keys)
```python
tr('tasks.title')                # 任务管理
tr('tasks.name')                 # 任务名称
tr('tasks.start_time')           # 开始时间
tr('tasks.end_time')             # 结束时间
tr('tasks.color')                # 颜色
tr('tasks.add_task')             # 添加任务
tr('tasks.edit_task')            # 编辑任务
tr('tasks.delete_task')          # 删除任务
tr('tasks.template')             # 模板
tr('tasks.theme')                # 主题配色
# ... and more
```

#### AI (11 keys)
```python
tr('ai.title')                   # AI功能
tr('ai.generate_tasks')          # AI生成任务
tr('ai.generate_theme')          # AI配色推荐
tr('ai.generating')              # AI正在生成中...
tr('ai.quota_remaining')         # 剩余配额: {count}次
tr('ai.quota_exhausted')         # 今日配额已用完
tr('ai.input_placeholder')       # 请描述你的日程安排... (NEW)
# ... and more
```

#### Account (17 keys)
```python
tr('account.title')              # 账号管理
tr('account.not_logged_in')      # 未登录
tr('account.logged_in_as')       # 已登录: {email}
tr('account.email')              # 邮箱
tr('account.password')           # 密码
tr('account.login')              # 登录
tr('account.logout')             # 退出登录
tr('account.register')           # 注册
# ... and more
```

#### Membership (17 keys)
```python
tr('membership.title')           # 会员中心
tr('membership.free')            # 免费版
tr('membership.pro_monthly')     # 月度会员
tr('membership.pro_yearly')      # 年度会员
tr('membership.lifetime')        # 终身会员
tr('membership.current_plan')    # 当前套餐
tr('membership.upgrade')         # 升级
# ... and more
```

Full list: See `i18n/zh_CN.json` and `i18n/en_US.json`

---

## 🛠️ Practical Example: config_gui.py

### Before (Hardcoded - First 50 lines)
```python
class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置")  # ❌
        self.setup_ui()

    def setup_ui(self):
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self.create_appearance_tab(), "外观设置")  # ❌
        tabs.addTab(self.create_tasks_tab(), "任务管理")      # ❌
        tabs.addTab(self.create_ai_tab(), "AI功能")          # ❌

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")      # ❌
        cancel_btn = QPushButton("取消")    # ❌
        reset_btn = QPushButton("重置")     # ❌
```

### After (Internationalized)
```python
from i18n import tr  # ✅ Add import

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('config.title'))  # ✅
        self.setup_ui()

    def setup_ui(self):
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self.create_appearance_tab(), tr('config.appearance'))  # ✅
        tabs.addTab(self.create_tasks_tab(), tr('config.tasks'))            # ✅
        tabs.addTab(self.create_ai_tab(), tr('config.ai'))                  # ✅

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr('button.save'))      # ✅
        cancel_btn = QPushButton(tr('button.cancel'))  # ✅
        reset_btn = QPushButton(tr('button.reset'))    # ✅
```

**Result**: Only ~10 lines changed, but **all tab names and buttons** are now internationalized!

---

## 🚀 Quick Win Checklist

Use this checklist to get maximum impact quickly:

### config_gui.py Quick Wins

- [ ] Add `from i18n import tr` import
- [ ] Replace window title: `setWindowTitle(tr('config.title'))`
- [ ] Replace 6 tab names with tr() calls
- [ ] Replace all button text (Save, Cancel, Apply, etc.)
- [ ] Replace common labels (Language, Height, Position, etc.)
- [ ] Replace QMessageBox titles and messages
- [ ] Test: Switch language to English and verify UI updates

**Estimated time**: 30-60 minutes
**Visual impact**: ~80% of config dialog internationalized

---

## 📚 Adding New Translation Keys

If you encounter a string without an existing key:

### 1. Add to `i18n/zh_CN.json`
```json
{
  "config": {
    "new_setting": "新设置名称"
  }
}
```

### 2. Add to `i18n/en_US.json`
```json
{
  "config": {
    "new_setting": "New Setting Name"
  }
}
```

### 3. Use in code
```python
QLabel(tr('config.new_setting'))
```

---

## ⚠️ What NOT to Internationalize

**Keep these in Chinese** (no need to translate):

### 1. Logger Messages
```python
# Keep as is
self.logger.info("用户保存了配置")
self.logger.debug(f"加载配置: {path}")
```

### 2. Docstrings
```python
# Keep as is
def save_config(self):
    """保存配置到文件"""
    pass
```

### 3. Comments
```python
# Keep as is
# 初始化UI组件
self.setup_ui()
```

### 4. Exception Messages (Internal)
```python
# Keep as is (internal debugging)
raise ValueError("配置文件格式错误")
```

**Only internationalize**: UI-visible text (labels, buttons, dialogs, tooltips, etc.)

---

## 🧪 Testing

### Manual Testing

1. Set language to English in config:
```json
{
  "language": "en_US"
}
```

2. Restart application

3. Verify internationalized elements show English

4. Check console for missing translation warnings:
```
[i18n] Missing translation: some.key
```

### Automated Testing

```python
def test_i18n_coverage():
    """Test that all UI strings use tr()"""
    # Read config_gui.py
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find Chinese strings not in tr()
    chinese_pattern = r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']'
    matches = re.finditer(chinese_pattern, content)

    for match in matches:
        line = content[:match.start()].count('\n') + 1
        if 'tr(' not in content[match.start()-20:match.start()]:
            if 'logger' not in content[match.start()-50:match.start()]:
                print(f"Line {line}: {match.group(1)}")
```

---

## 📈 Progress Tracking

### Current Progress

| Component | Total Strings | Internationalized | % Complete |
|-----------|--------------|-------------------|------------|
| Tray Menu | 16 | 16 | ✅ 100% |
| Language Settings | 4 | 4 | ✅ 100% |
| Config Dialog | 1,033 | 0 | ⏳ 0% |
| Auth UI | 142 | 0 | ⏳ 0% |
| Membership UI | 82 | 0 | ⏳ 0% |
| Other Files | 661 | 0 | ⏳ 0% |
| **TOTAL** | **1,938** | **20** | **1%** |

### Estimated Effort

| Task | Estimated Time | Priority |
|------|---------------|----------|
| config_gui.py (basic) | 1-2 hours | 🔴 HIGH |
| config_gui.py (complete) | 4-6 hours | 🔴 HIGH |
| main.py dialogs | 1-2 hours | 🔴 HIGH |
| Auth UI | 1-2 hours | 🟡 MED |
| Membership UI | 1 hour | 🟡 MED |
| Other files | 2-3 hours | 🟢 LOW |
| **TOTAL** | **10-16 hours** | |

---

## 💡 Tips & Best Practices

### 1. Use Meaningful Keys
```python
# ✅ Good
tr('config.bar_height')
tr('tasks.add_task')

# ❌ Bad
tr('label1')
tr('text_123')
```

### 2. Keep Format Parameters
```python
# ✅ Good
tr('ai.quota_remaining', count=5)  # Uses: "剩余配额: {count}次"

# ❌ Bad
f"剩余配额: {count}次"  # Hardcoded
```

### 3. Batch Similar Changes
Do all buttons at once, all labels at once, etc.

### 4. Test Frequently
Test after each batch of changes, not at the end.

### 5. Use Search & Replace Carefully
```
Find:    QPushButton\("(.*?)"\)
Replace: QPushButton(tr('button.$1'))
```
Then manually review and fix the keys.

---

## 🎯 Next Steps

### Immediate (Today)
1. ✅ Review this guide
2. ⏳ Internationalize config_gui.py tab names and buttons (30 min)
3. ⏳ Test English language switch

### Short-term (This Week)
4. ⏳ Complete config_gui.py all labels
5. ⏳ Internationalize main.py message boxes
6. ⏳ Internationalize auth_ui.py

### Long-term (This Month)
7. ⏳ Complete all remaining files
8. ⏳ Add automated i18n coverage tests
9. ⏳ Professional English translation review

---

## 📞 Support

If you encounter issues:
1. Check `i18n/zh_CN.json` for available keys
2. Search this guide for similar patterns
3. Test your changes incrementally
4. Review application logs for i18n warnings

---

**Generated by**: GaiYa I18n Analysis Tool
**Date**: 2025-11-22
**Translation Keys**: 271 ready, ~800-900 more needed
**Estimated Completion**: 10-16 hours of focused work
