# P1-1: 核心交互优化实施计划

> **执行周期**: 3.5周 (Day 25 - Day 49)
> **负责人**: 前端开发 × 1
> **预算**: ¥36,000
> **最后更新**: 2025-12-10
> **状态**: 📋 计划中

---

## 📊 调研总结

### 现有实现分析

**1. 悬停检测机制** (已实现)
- **文件**: [main.py:2587-2678](../main.py#L2587-L2678)
- **实现**: `mouseMoveEvent()` 检测鼠标位置,通过比对百分比确定悬停任务
- **状态管理**: `self.hovered_task_index` 变量 (-1 表示无悬停)
- **渲染触发**: 悬停状态改变时调用 `self.update()` 触发重绘

**2. 当前悬停提示** (简单实现)
- **文件**: [main.py:3430-3495](../main.py#L3430-L3495)
- **实现**: 在 `paintEvent()` 中用 QPainter 直接绘制
- **显示内容**: `任务名称 (开始-结束时间)` 单行文本
- **视觉样式**: 任务颜色背景 + 白色边框 + 文字颜色

**3. 任务数据结构** (需扩展)
- **文件**: [tasks.json](../tasks.json)
- **当前字段**: `id`, `start`, `end`, `task`, `color`, `text_color`
- **缺少字段**: `emoji`, `description`, `progress`, `completed`

**4. UI 组件参考**
- **FeatureCard**: 悬停动画效果 ([gaiya/ui/onboarding/feature_card.py](../gaiya/ui/onboarding/feature_card.py))
- **TaskReviewWindow**: 卡片式布局 ([gaiya/ui/task_review_window.py](../gaiya/ui/task_review_window.py))
- **PomodoroPanel**: 浮动面板定位 ([gaiya/ui/pomodoro_panel.py](../gaiya/ui/pomodoro_panel.py))

---

## 🎯 任务分解

### P1-1.3: 富文本悬停卡片 (3天, Day 25-27)

**业务价值**: 提升任务信息可读性,降低用户认知负担

#### 设计目标
- 显示更丰富的任务信息 (emoji、描述、进度)
- 优雅的动画效果 (淡入淡出、阴影)
- 智能定位 (避免遮挡、自适应空间)

#### 技术实现

**Day 25: 扩展数据结构**

1. **扩展 tasks.json 格式**
   - 新增字段: `emoji` (可选), `description` (可选), `progress` (0-100, 可选)
   - 向后兼容: 使用 `task.get('emoji', '')` 读取

2. **更新 data_loader.py**
   - 验证新字段的合法性
   - 提供默认值

**示例数据**:
```json
{
    "id": "d85b59052d950a357e5c72ecf9ff234708753b7d",
    "start": "00:00",
    "end": "06:00",
    "task": "深度睡眠",
    "emoji": "😴",
    "description": "保证充足睡眠,恢复精力",
    "progress": 100,
    "color": "#1976D2",
    "text_color": "#FFFFFF"
}
```

**Day 26: 创建 RichToolTip 组件**

**文件**: `gaiya/ui/components/rich_tooltip.py`

```python
class RichToolTip(QWidget):
    """富文本任务悬停卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 动画
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)

        # 内容布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)

        # 标题行 (emoji + 任务名称)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        # 时间信息
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 12px; color: #666;")

        # 描述文本
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("font-size: 11px; color: #888;")

        # 进度条 (可选)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.desc_label)
        self.layout.addWidget(self.progress_bar)

    def set_task(self, task: dict):
        """更新显示的任务信息"""
        emoji = task.get('emoji', '')
        task_name = task.get('task', '')
        self.title_label.setText(f"{emoji} {task_name}" if emoji else task_name)

        start = task.get('start', '')
        end = task.get('end', '')
        duration_minutes = self._calculate_duration(start, end)
        self.time_label.setText(f"⏰ {start} - {end} ({duration_minutes}分钟)")

        description = task.get('description', '')
        if description:
            self.desc_label.setText(description)
            self.desc_label.show()
        else:
            self.desc_label.hide()

        progress = task.get('progress', None)
        if progress is not None:
            self.progress_bar.setValue(progress)
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    def show_animated(self):
        """带淡入动画显示"""
        self.setWindowOpacity(0.0)
        self.show()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def hide_animated(self):
        """带淡出动画隐藏"""
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.hide)
        self.opacity_animation.start()
```

**Day 27: 集成到主窗口**

**修改文件**: `main.py`

1. **添加实例变量** (第92行附近)
```python
from gaiya.ui.components.rich_tooltip import RichToolTip

# 初始化
self.rich_tooltip = RichToolTip(self)
self.tooltip_timer = QTimer()
self.tooltip_timer.setSingleShot(True)
self.tooltip_timer.timeout.connect(self._show_rich_tooltip)
self.tooltip_hide_timer = QTimer()
self.tooltip_hide_timer.setSingleShot(True)
self.tooltip_hide_timer.timeout.connect(self._hide_rich_tooltip)
```

2. **修改 mouseMoveEvent()** (第2630行附近)
```python
# 原有逻辑
old_hovered_index = self.hovered_task_index
self.hovered_task_index = -1

if is_mouse_on_progress_bar:
    for i, pos in enumerate(self.task_positions):
        if pos['compact_start_pct'] <= mouse_percentage <= pos['compact_end_pct']:
            self.hovered_task_index = i
            break

# 新增: 悬停改变时的处理
if old_hovered_index != self.hovered_task_index:
    self.update()

    # 隐藏旧的提示框
    self.tooltip_timer.stop()
    self.tooltip_hide_timer.stop()
    if self.rich_tooltip.isVisible():
        self.rich_tooltip.hide_animated()

    # 延迟显示新的提示框 (避免快速移动时闪烁)
    if self.hovered_task_index != -1:
        self.tooltip_timer.start(300)  # 300ms 延迟
```

3. **添加显示/隐藏方法**
```python
def _show_rich_tooltip(self):
    """显示富文本提示框"""
    if self.hovered_task_index == -1:
        return

    task = self.task_positions[self.hovered_task_index]['task']
    self.rich_tooltip.set_task(task)

    # 计算显示位置 (任务块上方居中)
    pos = self.task_positions[self.hovered_task_index]
    bar_y_offset = self.height() - self.config.get('progress_bar_height', 60)

    task_center_x = self.width() * (pos['compact_start_pct'] + pos['compact_end_pct']) / 2
    tooltip_x = task_center_x - self.rich_tooltip.width() / 2
    tooltip_y = bar_y_offset - self.rich_tooltip.height() - 10  # 10px 间距

    # 边界检查
    tooltip_x = max(0, min(tooltip_x, self.width() - self.rich_tooltip.width()))

    self.rich_tooltip.move(int(tooltip_x), int(tooltip_y))
    self.rich_tooltip.show_animated()

def _hide_rich_tooltip(self):
    """隐藏富文本提示框"""
    if self.rich_tooltip.isVisible():
        self.rich_tooltip.hide_animated()
```

4. **修改 leaveEvent()** (第2664行)
```python
def leaveEvent(self, event):
    """鼠标离开窗口"""
    self.hovered_task_index = -1
    self.is_mouse_over_progress_bar = False
    self.update()

    # 隐藏提示框
    self.tooltip_timer.stop()
    self.tooltip_hide_timer.start(100)  # 100ms 后隐藏
```

#### 成功指标
- ✅ 提示框显示完整任务信息 (emoji、时间、描述、进度)
- ✅ 动画流畅 (200ms 淡入淡出)
- ✅ 定位准确 (不遮挡任务块,自适应空间)
- ✅ 无性能问题 (悬停响应 <50ms)

---

### P1-1.4: 编辑模式多种入口 (3天, Day 28-30)

**业务价值**: 提升编辑模式发现率,降低功能学习成本

#### 设计目标
- 双击进度条进入编辑模式
- 右键菜单提供编辑/退出选项
- 保留原有的快捷键入口 (空格键)

#### 技术实现

**Day 28: 实现双击进入编辑模式**

**修改文件**: `main.py`

1. **添加 mouseDoubleClickEvent()** (在 mouseMoveEvent 附近)
```python
def mouseDoubleClickEvent(self, event):
    """双击事件处理"""
    if event.button() == Qt.LeftButton:
        # 检测双击是否在进度条区域
        bar_height = self.config.get('progress_bar_height', 60)
        bar_y_offset = self.height() - bar_height

        if event.y() >= bar_y_offset:
            if not self.edit_mode:
                # 显示提示对话框
                msg = QMessageBox(self)
                msg.setWindowTitle("进入编辑模式")
                msg.setText("✏️ 进入编辑模式后,可以拖拽任务边缘调整时长")
                msg.setInformativeText("双击任务块可以快速编辑任务详情")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg.setDefaultButton(QMessageBox.Ok)

                if msg.exec() == QMessageBox.Ok:
                    self.enter_edit_mode()
```

**Day 29: 实现右键菜单**

**修改文件**: `main.py`

1. **添加 contextMenuEvent()** (在 mouseDoubleClickEvent 附近)
```python
def contextMenuEvent(self, event):
    """右键菜单"""
    menu = QMenu(self)

    # 编辑模式相关
    if not self.edit_mode:
        edit_action = menu.addAction("✏️ 进入编辑模式")
        edit_action.triggered.connect(self.enter_edit_mode)
    else:
        exit_action = menu.addAction("✅ 退出编辑模式")
        exit_action.triggered.connect(self.exit_edit_mode)

        menu.addSeparator()

        save_action = menu.addAction("💾 保存修改")
        save_action.triggered.connect(self._save_tasks)

        cancel_action = menu.addAction("❌ 取消修改")
        cancel_action.triggered.connect(self._cancel_edit)

    menu.addSeparator()

    # 配置相关
    config_action = menu.addAction("⚙️ 打开配置")
    config_action.triggered.connect(self.show_config_window)

    # 刷新
    refresh_action = menu.addAction("🔄 刷新")
    refresh_action.triggered.connect(self._reload_tasks)

    menu.exec(event.globalPos())
```

2. **添加辅助方法**
```python
def _save_tasks(self):
    """保存任务修改"""
    # 现有的保存逻辑
    self.save_tasks()

    # 显示成功提示
    QMessageBox.information(self, "保存成功", "任务已保存!")

def _cancel_edit(self):
    """取消编辑"""
    reply = QMessageBox.question(
        self,
        "取消编辑",
        "确定要取消编辑吗?未保存的修改将丢失。",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        self.exit_edit_mode()
        self._reload_tasks()

def _reload_tasks(self):
    """重新加载任务"""
    self.tasks = data_loader.load_tasks(self.app_dir, self.logger)
    self.calculate_time_range()
    self.update()
```

**Day 30: 优化编辑模式视觉提示**

**修改文件**: `main.py` (在 paintEvent 中)

1. **添加编辑模式指示器** (在进度条右上角)
```python
# 在 paintEvent() 中,绘制完任务块后添加
if self.edit_mode:
    # 绘制编辑模式指示器
    indicator_text = "✏️ 编辑模式 (双击任务编辑 | 拖拽边缘调整)"
    painter.setPen(QColor(255, 152, 0))  # 橙色
    painter.setFont(QFont("Arial", 12, QFont.Bold))
    painter.drawText(
        self.width() - 400,
        bar_y_offset - 30,
        indicator_text
    )
```

#### 成功指标
- ✅ 双击进度条可进入编辑模式
- ✅ 右键菜单显示正确的选项
- ✅ 编辑模式有明显的视觉提示
- ✅ 编辑模式使用率: 15% → 40% (目标 +166%)

---

### P1-1.5: AI功能前置化 (5天, Day 31-35)

**业务价值**: 提升 AI 功能发现率和使用频率

#### 设计目标
- 在配置窗口顶部显示 AI 配额卡片
- 卡片显示当前配额、使用情况、续费入口
- 一键跳转到 AI 任务生成功能

#### 技术实现

**Day 31-32: 创建 AIQuotaCard 组件**

**文件**: `gaiya/ui/components/ai_quota_card.py`

```python
class AIQuotaCard(QWidget):
    """AI配额卡片 (显示在配置窗口顶部)"""

    generate_clicked = Signal()  # 点击生成按钮的信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)

        # 样式
        self.setStyleSheet("""
            AIQuotaCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2
                );
                border-radius: 12px;
            }
        """)

        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        # 左侧: 图标 + 文字信息
        left_layout = QVBoxLayout()

        title_label = QLabel("🤖 AI 智能助手")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")

        self.quota_label = QLabel("加载中...")
        self.quota_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px;")

        left_layout.addWidget(title_label)
        left_layout.addWidget(self.quota_label)
        left_layout.addStretch()

        # 右侧: 操作按钮
        right_layout = QVBoxLayout()

        self.generate_btn = QPushButton("✨ 生成任务")
        self.generate_btn.setFixedSize(120, 36)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #667eea;
                border: none;
                border-radius: 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.9);
            }
        """)
        self.generate_btn.clicked.connect(self.generate_clicked.emit)

        self.renew_btn = QPushButton("续费")
        self.renew_btn.setFixedSize(80, 28)
        self.renew_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.5);
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)

        right_layout.addWidget(self.generate_btn)
        right_layout.addWidget(self.renew_btn, alignment=Qt.AlignRight)

        layout.addLayout(left_layout, stretch=1)
        layout.addLayout(right_layout)

    def update_quota(self, used: int, total: int, tier: str):
        """更新配额显示"""
        remaining = total - used
        percentage = (used / total * 100) if total > 0 else 0

        tier_text = {"free": "免费版", "pro": "专业版", "enterprise": "企业版"}.get(tier, tier)

        self.quota_label.setText(
            f"今日剩余: {remaining}/{total} 次 · {tier_text}"
        )

        # 配额不足时变红
        if remaining <= 0:
            self.quota_label.setStyleSheet("color: #ff6b6b; font-size: 13px;")
            self.generate_btn.setEnabled(False)
        else:
            self.quota_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px;")
            self.generate_btn.setEnabled(True)
```

**Day 33-34: 集成到配置窗口**

**修改文件**: `config_gui.py`

1. **在 __init__() 中添加 AI 卡片** (第一个组件)
```python
from gaiya.ui.components.ai_quota_card import AIQuotaCard

# 在布局顶部添加 AI 卡片
self.ai_quota_card = AIQuotaCard()
self.ai_quota_card.generate_clicked.connect(self._open_ai_generator)

main_layout = QVBoxLayout()
main_layout.addWidget(self.ai_quota_card)  # ← 前置显示
main_layout.addWidget(self.tab_widget)
self.setLayout(main_layout)
```

2. **添加配额查询方法**
```python
def _load_ai_quota(self):
    """加载 AI 配额信息"""
    if not hasattr(self, 'auth_client'):
        from gaiya.core.auth_client import AuthClient
        self.auth_client = AuthClient()

    quota_data = self.auth_client.get_quota_status()
    if quota_data.get("success"):
        self.ai_quota_card.update_quota(
            used=quota_data.get("used", 0),
            total=quota_data.get("total", 10),
            tier=quota_data.get("user_tier", "free")
        )

def _open_ai_generator(self):
    """打开 AI 任务生成对话框"""
    # 现有的 AI 生成逻辑
    if hasattr(self, 'ai_dialog'):
        self.ai_dialog.show()
    else:
        # 创建并显示 AI 对话框
        from gaiya.ui.onboarding.ai_generation_dialog import AIGenerationDialog
        self.ai_dialog = AIGenerationDialog(self)
        self.ai_dialog.show()
```

**Day 35: 测试与优化**

- 测试配额显示是否准确
- 测试按钮跳转是否正常
- 优化卡片动画效果

#### 成功指标
- ✅ AI 卡片在配置窗口顶部显示
- ✅ 配额信息准确无误
- ✅ 一键跳转到 AI 生成功能
- ✅ AI 功能使用率: 30% → 50% (目标 +66%)

---

### P1-1.6: 成就即时反馈 (5天, Day 36-40)

**业务价值**: 提升用户成就感,增强长期使用粘性

#### 设计目标
- Steam 风格的成就解锁通知
- 从屏幕右侧滑入,3秒后自动消失
- 显示成就图标、标题、描述

#### 技术实现

**Day 36-37: 创建 AchievementNotification 组件**

**文件**: `gaiya/ui/components/achievement_notification.py`

```python
class AchievementNotification(QWidget):
    """成就解锁通知 (Steam 风格)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 100)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # 动画
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(500)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)

        # 布局
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        # 背景容器
        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e
                );
                border: 2px solid #f39c12;
                border-radius: 10px;
            }
        """)
        container.setGeometry(0, 0, 320, 100)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)

        # 左侧: 成就图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(60, 60)
        self.icon_label.setScaledContents(True)

        # 右侧: 文字信息
        text_layout = QVBoxLayout()

        header_label = QLabel("🏆 成就解锁")
        header_label.setStyleSheet("color: #f39c12; font-size: 12px; font-weight: bold;")

        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
        self.desc_label.setWordWrap(True)

        text_layout.addWidget(header_label)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)
        text_layout.addStretch()

        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)

    def show_achievement(self, icon_path: str, title: str, description: str):
        """显示成就通知"""
        # 设置内容
        self.icon_label.setPixmap(QPixmap(icon_path))
        self.title_label.setText(title)
        self.desc_label.setText(description)

        # 计算起始和结束位置
        screen = QApplication.primaryScreen().geometry()
        start_x = screen.width()
        start_y = screen.height() - 120
        end_x = screen.width() - 340  # 320 + 20px 边距
        end_y = start_y

        # 滑入动画
        self.slide_animation.setStartValue(QPoint(start_x, start_y))
        self.slide_animation.setEndValue(QPoint(end_x, end_y))

        self.show()
        self.slide_animation.start()

        # 3秒后自动隐藏
        QTimer.singleShot(3000, self.hide_notification)

    def hide_notification(self):
        """隐藏通知 (滑出动画)"""
        screen = QApplication.primaryScreen().geometry()
        current_pos = self.pos()
        end_x = screen.width()
        end_y = current_pos.y()

        self.slide_animation.setStartValue(current_pos)
        self.slide_animation.setEndValue(QPoint(end_x, end_y))
        self.slide_animation.finished.connect(self.hide)
        self.slide_animation.start()
```

**Day 38-39: 集成成就系统**

**文件**: `gaiya/core/achievement_manager.py`

```python
class AchievementManager:
    """成就管理器"""

    ACHIEVEMENTS = {
        "first_task": {
            "title": "初出茅庐",
            "description": "完成第一个任务",
            "icon": "assets/achievements/first_task.png"
        },
        "task_streak_7": {
            "title": "坚持不懈",
            "description": "连续7天完成任务",
            "icon": "assets/achievements/streak_7.png"
        },
        "pomodoro_10": {
            "title": "番茄达人",
            "description": "累计完成10个番茄钟",
            "icon": "assets/achievements/pomodoro_10.png"
        },
        # ... 更多成就
    }

    def __init__(self, db_manager):
        self.db = db_manager
        self.unlocked_achievements = self._load_unlocked()

    def check_achievement(self, achievement_id: str) -> bool:
        """检查成就是否应该解锁"""
        if achievement_id in self.unlocked_achievements:
            return False

        # 检查解锁条件
        if achievement_id == "first_task":
            return self._check_first_task()
        elif achievement_id == "task_streak_7":
            return self._check_task_streak(7)
        # ... 其他成就条件

        return False

    def unlock_achievement(self, achievement_id: str):
        """解锁成就"""
        if achievement_id in self.unlocked_achievements:
            return

        self.unlocked_achievements.add(achievement_id)
        self.db.save_achievement(achievement_id)

        # 触发通知
        achievement = self.ACHIEVEMENTS.get(achievement_id)
        if achievement:
            self._show_notification(achievement)

    def _show_notification(self, achievement: dict):
        """显示成就通知"""
        from gaiya.ui.components.achievement_notification import AchievementNotification

        notification = AchievementNotification()
        notification.show_achievement(
            icon_path=achievement["icon"],
            title=achievement["title"],
            description=achievement["description"]
        )
```

**修改文件**: `main.py` (集成到主窗口)

```python
from gaiya.core.achievement_manager import AchievementManager

# 在 __init__() 中
self.achievement_manager = AchievementManager(self.db_manager)

# 在任务完成时检查成就
def mark_task_completed(self, task_id: str):
    """标记任务完成"""
    # 原有逻辑
    self.db_manager.mark_task_completed(task_id)

    # 检查成就
    for achievement_id in self.achievement_manager.ACHIEVEMENTS.keys():
        if self.achievement_manager.check_achievement(achievement_id):
            self.achievement_manager.unlock_achievement(achievement_id)
```

**Day 40: 创建成就图标资源**

- 设计 5-10 个成就图标 (64x64 PNG)
- 保存到 `assets/achievements/` 目录
- 更新 Gaiya.spec 打包配置

#### 成功指标
- ✅ 成就解锁时显示通知
- ✅ 通知滑入/滑出动画流畅
- ✅ 3秒后自动消失
- ✅ 用户满意度 (NPS): 4.0 → 4.5 (+12.5%)

---

## 📊 总体成功指标

| 指标 | 当前值 | 目标值 | 验收方法 |
|------|--------|--------|----------|
| **功能发现率** | ~60% | **80%** | 用户访谈 (10人) |
| **编辑模式使用率** | ~15% | **40%** | 数据埋点 (统计进入次数) |
| **AI 功能使用率** | ~30% | **50%** | API 调用日志 |
| **用户满意度 (NPS)** | 4.0 | **4.5** | 线上问卷调查 (50+ 样本) |

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| **PySide6.QtWidgets** | UI 组件基类 |
| **PySide6.QtCore** | 信号槽、定时器、动画 |
| **QPropertyAnimation** | 属性动画 (淡入淡出、滑动) |
| **QGraphicsDropShadowEffect** | 阴影效果 |
| **QPainter** | 自定义绘制 |

---

## 📁 文件结构

```
gaiya/
├── ui/
│   └── components/
│       ├── rich_tooltip.py          # P1-1.3: 富文本悬停卡片
│       ├── ai_quota_card.py         # P1-1.5: AI 配额卡片
│       └── achievement_notification.py  # P1-1.6: 成就通知
├── core/
│   └── achievement_manager.py       # P1-1.6: 成就管理器
└── data/
    └── achievements/                # 成就图标资源

main.py                              # 集成悬停卡片、右键菜单、成就
config_gui.py                        # 集成 AI 配额卡片
tasks.json                           # 扩展数据结构 (emoji, description, progress)
```

---

## 🔄 开发流程

### 每日工作流
1. **晨会**: 回顾前一天进度,确认当天目标
2. **开发**: 按照计划实施功能
3. **自测**: 运行应用,测试新功能
4. **提交**: 小步提交,确保每次提交都能编译运行
5. **文档**: 更新实施日志

### 测试要求
- **功能测试**: 每个功能完成后立即测试
- **集成测试**: 子任务完成后进行集成测试
- **回归测试**: 确保新功能不影响现有功能
- **用户测试**: P1-1 完成后邀请 3-5 名用户试用

### 提交规范
- `feat(ui): add rich tooltip component`
- `feat(interaction): add double-click to enter edit mode`
- `feat(ai): add AI quota card to config window`
- `feat(achievement): add achievement notification system`

---

## ⚠️ 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| **悬停延迟过长** | 用户体验差 | 调整延迟时间 (200-300ms),添加快速预览 |
| **提示框遮挡内容** | 影响可读性 | 智能定位算法,优先显示在上方 |
| **动画卡顿** | 性能问题 | 优化动画时长,使用硬件加速 |
| **数据结构不兼容** | 现有任务无法显示 | 向后兼容,提供默认值 |
| **成就系统复杂** | 开发周期延长 | 先实现 3-5 个核心成就,后续迭代 |

---

## 📝 验收标准

### P1-1.3: 富文本悬停卡片
- [ ] 悬停 300ms 后显示提示框
- [ ] 提示框显示 emoji、任务名称、时间、描述、进度
- [ ] 淡入淡出动画流畅 (200ms)
- [ ] 提示框不遮挡任务块
- [ ] 离开任务块 100ms 后隐藏

### P1-1.4: 编辑模式多种入口
- [ ] 双击进度条进入编辑模式
- [ ] 右键菜单显示编辑/退出选项
- [ ] 编辑模式有明显的视觉提示
- [ ] 保存/取消功能正常

### P1-1.5: AI功能前置化
- [ ] AI 卡片在配置窗口顶部显示
- [ ] 配额信息准确 (已用/总计/等级)
- [ ] 点击"生成任务"按钮跳转到 AI 生成对话框
- [ ] 配额不足时按钮禁用

### P1-1.6: 成就即时反馈
- [ ] 成就解锁时显示通知
- [ ] 通知从右侧滑入 (500ms)
- [ ] 3秒后自动滑出并隐藏
- [ ] 通知内容完整 (图标、标题、描述)
- [ ] 至少实现 5 个成就

---

**文档创建时间**: 2025-12-10
**计划版本**: v1.0
**负责人**: Claude AI Assistant
**下一步**: 开始执行 P1-1.3 (富文本悬停卡片)
