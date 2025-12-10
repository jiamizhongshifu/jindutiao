# GaiYa 应用改进路线图 v3.0 (最终版)

> **制定日期**: 2025-12-10
> **当前版本**: v1.6.13
> **目标版本**: v2.0.0
> **执行周期**: 2026-01 至 2026-08 (8 个月)
> **版本说明**: 基于实际代码实现 (92.5%完成度) 和三方专家评审的最终优化版

---

## 📋 v3.0 核心调整说明

### 🔄 相比 v2.0 的关键变化

**1. 新手引导策略调整** ✅
- **v2.0 方案**: 创建全新的 4 步交互式引导流程
- **v3.0 方案**: 优化现有引导系统 (WelcomeDialog + SetupWizard)
- **原因**: 代码审查发现已有完整实现 (welcome_dialog.py 130行 + setup_wizard.py 309行)

**2. 移除深色主题任务** ✅
- **移除任务**: P2-2 深色主题支持 (原计划 2 周)
- **原因**: 短期内不需要,优先其他高价值功能
- **释放资源**: 2 周开发时间 + ¥40,000 预算

**3. 基于实际功能完成度调整** ✅
- **已完全实现**: 行为追踪、AI推理、弹幕系统、激励系统、场景系统 (100%)
- **需要优化**: 高级编辑功能、数据分析、主题编辑器 (50-70%)
- **完全缺失**: 团队协作、移动端、插件系统 (0%)

---

## 🎯 优先级定义

| 优先级 | 标签 | 定义 | 执行时间 |
|--------|------|------|----------|
| **P0** | 🔥 紧急 | 严重影响用户体验,需立即修复 | 1-2 周 |
| **P1** | 🔴 高 | 重要功能/优化,需优先安排 | 1-2 个月 |
| **P2** | 🟠 中 | 重要但不紧急,可分阶段完成 | 2-4 个月 |
| **P3** | 🟡 低 | 锦上添花,资源允许时执行 | 4-8 个月 |

---

## 🔥 P0 级任务 (紧急 - 1-2 周完成)

### P0-1: 优化现有新手引导体验 ✨ 新增

**背景分析**:
- ✅ 已有 WelcomeDialog (130行) - 展示 4 个核心功能
- ✅ 已有 SetupWizard (309行) - 3 个预设模板 + AI 生成入口
- ✅ 已有 FirstRunDetector - 完成追踪机制
- ⚠️ 问题: 引导内容静态、缺少交互、AI 功能展示不足

**优化方案**:

#### 方案 A: 增强 WelcomeDialog 视觉设计 (推荐)

**现有代码位置**: `gaiya/ui/onboarding/welcome_dialog.py` 第 83-120 行

```python
# 现状: 简单的文本列表
features = [
    tr("welcome_dialog.features.task_progress"),
    tr("welcome_dialog.features.smart_reminder"),
    tr("welcome_dialog.features.rich_themes"),
    tr("welcome_dialog.features.ai_planning")
]

for feature in features:
    feature_label = QLabel(f"• {feature}")
    features_layout.addWidget(feature_label)
```

**优化后: 图标 + 动画卡片**

```python
class FeatureCard(QWidget):
    """功能卡片 - 带图标和动画效果"""

    def __init__(self, icon: str, title: str, description: str):
        super().__init__()
        self.setFixedSize(400, 80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 图标 (64x64)
        icon_label = QLabel()
        icon_pixmap = QPixmap(f"assets/icons/{icon}.png").scaled(
            48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        icon_label.setPixmap(icon_pixmap)

        # 文字区域
        text_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 12px; color: #888;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout)

        # 悬停动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

# 使用方式
features = [
    ("progress_bar", "时间可视化", "透明进度条让时间流逝清晰可见"),
    ("ai_brain", "AI 智能推理", "自动识别你的工作内容并生成任务"),
    ("palette", "50+ 主题风格", "商务/森林/赛博朋克等多种视觉风格"),
    ("trophy", "成就激励系统", "解锁成就,持续提升专注力")
]

for icon, title, desc in features:
    card = FeatureCard(icon, title, desc)
    features_layout.addWidget(card)
```

**预期效果**:
- ✅ 视觉吸引力提升 200%
- ✅ 信息传达效率提升 50%
- ✅ 用户继续使用意愿提升 40%

---

#### 方案 B: SetupWizard 增加实时预览 (推荐)

**现有代码位置**: `gaiya/ui/onboarding/setup_wizard.py` 第 83-202 行

**现状**: 用户选择模板后,需要完成向导才能看到效果

**优化: 所见即所得预览**

```python
class TemplateSelectionPage(QWizardPage):
    """模板选择页 - 增强版"""

    def __init__(self):
        super().__init__()

        # 左侧: 模板列表 (保持不变)
        self.setup_template_list()

        # 右侧: 实时预览 (新增)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        preview_label = QLabel("预览效果:")
        preview_label.setStyleSheet("font-weight: bold; margin-bottom: 8px;")

        # 迷你进度条预览 (300x40)
        self.mini_progress_bar = MiniProgressBarPreview()
        self.mini_progress_bar.setFixedSize(300, 40)

        # 任务列表预览
        self.task_list_preview = QListWidget()
        self.task_list_preview.setMaximumHeight(200)

        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.mini_progress_bar)
        preview_layout.addWidget(QLabel("今日任务:"))
        preview_layout.addWidget(self.task_list_preview)

        # 布局: 左右分栏
        main_layout = QHBoxLayout()
        main_layout.addWidget(template_list_widget, 1)
        main_layout.addWidget(preview_widget, 1)

    def on_template_selected(self, template_id: str):
        """模板选中时更新预览"""
        template = self.template_manager.get_template(template_id)

        # 更新迷你进度条
        self.mini_progress_bar.load_template(template)

        # 更新任务列表
        self.task_list_preview.clear()
        for task in template['tasks']:
            item = QListWidgetItem(
                f"{task['start_time']}-{task['end_time']} {task['name']}"
            )
            self.task_list_preview.addItem(item)

class MiniProgressBarPreview(QWidget):
    """迷你进度条预览组件"""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景渐变
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#4CAF50"))
        gradient.setColorAt(1, QColor("#81C784"))
        painter.fillRect(self.rect(), gradient)

        # 绘制当前时间标记 (模拟 40% 进度)
        marker_x = int(self.width() * 0.4)
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawLine(marker_x, 0, marker_x, self.height())

        painter.end()
```

**预期效果**:
- ✅ 用户理解模板内容的时间减少 60%
- ✅ 模板选择错误率降低 40%
- ✅ 用户满意度提升 35%

---

#### 方案 C: AI 生成流程优化 (高优先级)

**现有代码位置**: `gaiya/ui/onboarding/setup_wizard.py` 第 130-145 行

**现状**: AI 生成按钮存在,但缺少生成中的视觉反馈

**优化: 增加生成动画和进度提示**

```python
class AIGenerationDialog(QDialog):
    """AI 生成任务对话框 - 带动画"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 正在生成任务...")
        self.setFixedSize(400, 250)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 动画图标 (旋转的 AI 图标)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.load_icon = QPixmap("assets/icons/ai_brain.png").scaled(
            80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.icon_label.setPixmap(self.load_icon)

        # 旋转动画
        self.rotation_animation = QPropertyAnimation(self.icon_label, b"rotation")
        self.rotation_animation.setDuration(2000)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)  # 无限循环

        # 状态文本 (动态更新)
        self.status_label = QLabel("正在分析你的使用习惯...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #666;")

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度模式
        self.progress_bar.setTextVisible(False)

        # 提示文本
        tips = [
            "💡 提示: AI 会根据你的工作习惯生成个性化任务",
            "💡 提示: 生成后可以手动调整任务时间和名称",
            "💡 提示: AI 配额充足,放心使用"
        ]
        self.tip_label = QLabel(random.choice(tips))
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.setStyleSheet("font-size: 12px; color: #888; margin-top: 16px;")

        layout.addWidget(self.icon_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.tip_label)

        # 启动动画
        self.rotation_animation.start()

        # 状态文本轮播
        self.status_texts = [
            "正在分析你的使用习惯...",
            "正在生成任务计划...",
            "正在优化任务时间分配...",
            "即将完成..."
        ]
        self.status_index = 0
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(3000)  # 每 3 秒切换

    def update_status(self):
        """更新状态文本"""
        self.status_index = (self.status_index + 1) % len(self.status_texts)
        self.status_label.setText(self.status_texts[self.status_index])
```

**预期效果**:
- ✅ 用户等待焦虑降低 50%
- ✅ AI 功能感知度提升 60%
- ✅ 完成引导率提升 25%

---

#### 方案 D: 完成页优化 (快速胜利)

**现有代码位置**: `gaiya/ui/onboarding/setup_wizard.py` 第 204-260 行

**优化: 增加成就感和下一步引导**

```python
class CompletionPage(QWizardPage):
    """完成页 - 增强版"""

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # 成功图标 (带动画)
        success_icon = QLabel()
        success_pixmap = QPixmap("assets/icons/success_checkmark.png").scaled(
            100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        success_icon.setPixmap(success_pixmap)
        success_icon.setAlignment(Qt.AlignCenter)

        # 缩放动画 (从小到大)
        self.scale_animation = QPropertyAnimation(success_icon, b"geometry")
        self.scale_animation.setDuration(500)
        self.scale_animation.setStartValue(QRect(150, 100, 0, 0))
        self.scale_animation.setEndValue(QRect(150, 100, 100, 100))
        self.scale_animation.setEasingCurve(QEasingCurve.OutElastic)

        # 祝贺文本
        congrats_label = QLabel("🎉 设置完成!")
        congrats_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        congrats_label.setAlignment(Qt.AlignCenter)

        # 下一步引导
        next_steps = QLabel(
            "接下来你可以:\n\n"
            "• 在屏幕顶部查看实时进度条\n"
            "• 右键进度条打开配置界面\n"
            "• 使用 AI 功能自动生成任务\n"
            "• 探索 50+ 种主题风格"
        )
        next_steps.setAlignment(Qt.AlignCenter)
        next_steps.setStyleSheet("font-size: 13px; color: #666; line-height: 1.8;")

        # 快速操作按钮
        action_layout = QHBoxLayout()

        open_config_btn = QPushButton("打开配置界面")
        open_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        open_config_btn.clicked.connect(self.open_config)

        try_ai_btn = QPushButton("体验 AI 功能")
        try_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        try_ai_btn.clicked.connect(self.try_ai)

        action_layout.addWidget(open_config_btn)
        action_layout.addWidget(try_ai_btn)

        layout.addWidget(success_icon)
        layout.addWidget(congrats_label)
        layout.addSpacing(20)
        layout.addWidget(next_steps)
        layout.addSpacing(20)
        layout.addLayout(action_layout)

        # 启动动画
        self.scale_animation.start()
```

**预期效果**:
- ✅ 用户成就感提升 80%
- ✅ 核心功能发现率提升 50%
- ✅ 7 日留存率提升 30%

---

### 实施计划

**第 1 周: 视觉增强**
- Day 1-2: 设计功能卡片图标 (4 个)
- Day 3-4: 实现 FeatureCard 组件
- Day 5: 集成到 WelcomeDialog

**第 2 周: 交互优化**
- Day 1-3: 实现 MiniProgressBarPreview 组件
- Day 4-5: 实现 AI 生成动画对话框
- Day 6-7: 完成页优化 + 测试

**验收标准**:
- [ ] 新用户完成引导率 > 85% (当前 ~70%)
- [ ] 引导完成后 7 日留存率 > 60% (当前 ~45%)
- [ ] AI 功能首次使用率 > 50% (当前 ~30%)
- [ ] 用户满意度评分 > 4.5/5.0

**预期效果**:
- ✅ 新用户留存率提升 **40%**
- ✅ AI 功能使用率提升 **60%**
- ✅ 核心功能发现率提升 **50%**

**预算**: ¥15,000 (1 名前端开发 2 周)

---

### P0-2: 减少打包体积 (85MB → 55MB)

**保持 v2.0 方案不变** (已经过工程师审核优化)

**实施步骤**:

#### 第 1 周: UPX 压缩

```bash
# 下载 UPX 4.2.2
# https://github.com/upx/upx/releases

# 推荐配置 (平衡压缩率和兼容性)
upx --best \
    --compress-icons=0 \
    --compress-exports=0 \
    --exclude "*.pyd" \
    dist\GaiYa-v1.6.exe

# 预期结果: 85 MB → 58-62 MB
```

#### 第 2 周: 排除未使用模块

```python
# GaiYa.spec 修改
excludes = [
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DCore',
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtMultimedia',
    'PySide6.QtQuick',
]

a = Analysis(
    ...,
    excludes=excludes,
    ...
)
```

**预期效果**: 减少 10-15 MB

**预算**: ¥5,000 (DevOps 工程师 1 周兼职)

---

### P0-3: 修复会话管理不当 (Token 自动刷新)

**保持 v2.0 方案不变** (已经过工程师审核优化)

**关键改进**:
1. 指数退避重试机制
2. 提前刷新时间动态调整 (80% 有效期时刷新)
3. 线程安全的原子更新
4. 完整的单元测试

**预算**: ¥8,000 (1 名后端开发 3 天)

---

### P0-4: 优化首次启动速度 (3-5s → 1.5-2s)

**保持 v2.0 方案不变** (已经过工程师审核优化)

**三大优化**:
1. 延迟加载非核心模块 (config_gui, statistics_gui)
2. 数据库懒加载
3. 场景资源异步加载

**预期效果**: 3-5s → **1.5-2s**

**预算**: ¥20,000 (1 名前端开发 1.5 周)

---

## 🔴 P1 级任务 (高优先级 - 1-2 个月完成)

### P1-1: 核心交互优化 (UX 改进)

#### 1.1 富文本悬停卡片 (1 周)

**现有代码位置**: `main.py` 第 1420-1450 行

**现状**:
```python
# 简单的 tooltip
QToolTip.showText(
    event.globalPos(),
    f"{task['name']}\n{task['start_time']}-{task['end_time']}"
)
```

**优化: 信息丰富的悬停卡片**

```python
class RichToolTip(QWidget):
    """富文本悬停卡片"""

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # 任务名称 (大字体 + emoji)
        emoji_map = {
            "work": "💼", "study": "📚", "exercise": "🏃",
            "rest": "☕", "entertainment": "🎮"
        }
        emoji = emoji_map.get(task.get('category'), "📌")

        title = QLabel(f"{emoji} {task['name']}")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333333;
        """)

        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E0E0E0;")

        # 时间信息
        duration = self._calculate_duration(task)
        time_info = QLabel(
            f"⏰ {task['start_time']} - {task['end_time']} ({duration})"
        )
        time_info.setStyleSheet("font-size: 13px; color: #666;")

        # 进度信息
        progress = self._calculate_progress(task)
        progress_info = QLabel(
            f"📊 已完成 {progress['completed']} ({progress['percentage']:.0f}%)"
        )
        progress_info.setStyleSheet("font-size: 13px; color: #666;")

        # 类型标签
        category = QLabel(f"🎯 类型: {task.get('category', '未分类')}")
        category.setStyleSheet("font-size: 13px; color: #666;")

        # 操作提示
        hint = QLabel("💡 提示: 右键可编辑任务")
        hint.setStyleSheet("font-size: 12px; color: #999; margin-top: 8px;")

        # 添加到布局
        layout.addWidget(title)
        layout.addWidget(separator)
        layout.addWidget(time_info)
        layout.addWidget(progress_info)
        layout.addWidget(category)
        layout.addWidget(hint)

        # 卡片背景
        self.setStyleSheet("""
            RichToolTip {
                background-color: white;
                border: 1px solid #D0D0D0;
                border-radius: 8px;
            }
        """)
```

**预期效果**:
- ✅ 信息丰富度提升 300%
- ✅ 用户理解成本降低 50%

**预算**: ¥10,000 (1 周)

---

#### 1.2 编辑模式多种入口 (3 天)

**优化方案**:
1. 进度条双击进入编辑模式
2. 悬停时显示编辑图标
3. 右键菜单添加"编辑模式"选项

**预算**: ¥6,000

---

#### 1.3 AI 功能前置化 (1 周)

**优化方案**:
1. 配置界面顶部显示 AI 配额卡片
2. 进度条右键菜单添加"AI 生成今日任务"
3. 首次使用时展示 AI 能力

**预算**: ¥10,000

---

#### 1.4 成就即时反馈 (1 周)

**实现: Steam 风格成就通知**

```python
class AchievementNotification(QWidget):
    """成就解锁通知 (类似 Steam)"""

    def show_notification(self):
        """从右侧滑入动画"""
        screen = QApplication.primaryScreen().geometry()

        # 起始位置 (屏幕外)
        start_pos = QPoint(screen.width(), screen.height() - 120)
        # 结束位置 (屏幕右下角)
        end_pos = QPoint(screen.width() - 320, screen.height() - 120)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)

        self.show()
        self.animation.start()

        # 3 秒后自动隐藏
        QTimer.singleShot(3000, self.hide_notification)
```

**预算**: ¥10,000

---

**P1-1 总预算**: ¥36,000 (约 3.5 周)

---

### P1-2: 代码重构 - 拆分大文件

**保持 v2.0 方案不变** (已经过工程师审核优化)

**关键调整**:
- 时间估算: 4 周 → **6-7 周** (更现实)
- 采用 Strangler Fig Pattern (渐进式重构)
- 每周独立交付可工作版本

**预算**: ¥120,000 (2 名前端开发 6 周)

---

### P1-3: 添加完整类型注解

**保持 v2.0 方案不变**

**预算**: ¥30,000 (1 名开发 3 周)

---

### P1-4: macOS 支持

**保持 v2.0 方案不变**

**预算**: ¥100,000 (1 名开发 6 周 + Mac Mini 设备)

---

## 🟠 P2 级任务 (中优先级 - 2-4 个月完成)

### P2-1: 信息架构重组

#### 2.1.1 统计报告标签页重组 (2 周)

**现状**: 8 个标签页 (信息过载)

**优化**: 5 个标签页

```
1. 📊 概览 (Dashboard)
   ├─ 今日进度环形图
   ├─ 本周趋势折线图
   ├─ 关键指标卡片
   └─ AI 洞察 (3 条)

2. 📈 深度分析 (合并周/月/分类)
   └─ 下拉菜单切换视图

3. 🎯 成就与目标 (左右分栏)
   ├─ 成就系统 (左)
   └─ 目标管理 (右)

4. 🤖 AI 智能 (上下分栏)
   ├─ 推理任务 (上)
   └─ 时间回放 (下)

5. 📅 历史记录
   ├─ 日历视图
   └─ 详细记录列表
```

**预期效果**:
- ✅ 认知负担降低 40%
- ✅ 任务完成效率提升 25%

**预算**: ¥30,000

---

#### 2.1.2 配置界面侧边栏导航 (2 周)

**现状**: 7 个标签页 (水平排列)

**优化**: 侧边栏导航

```
┌────────────────────────────────────┐
│ GaiYa 配置                          │
├───────┬────────────────────────────┤
│ 侧边栏│ 主内容区                    │
│       │                            │
│ 🏠 概览│ 当前设置概览                │
│ 📝 任务│                            │
│ 🎨 外观│                            │
│ 🤖 AI │                            │
│ 👤 账户│                            │
│ ⚙️ 高级│                            │
└───────┴────────────────────────────┘
```

**预算**: ¥30,000

---

### P2-2: UI 自动化测试

**保持 v2.0 方案不变**

**预算**: ¥100,000 (1 名测试工程师 8 周)

---

### P2-3: 性能监控与优化

**保持 v2.0 方案不变**

**预算**: ¥60,000 (2 个月)

---

### P2-4: 插件系统

**保持 v2.0 方案不变**

**预算**: ¥180,000 (4-5 个月)

---

## 🟡 P3 级任务 (低优先级 - 4-8 个月完成)

### P3-1: 移动端应用 (React Native)

**保持 v2.0 方案不变**

**预算**: ¥240,000 (6 个月)

---

### P3-2: 团队协作功能

**保持 v2.0 方案不变**

**预算**: ¥160,000 (4 个月)

---

### P3-3: API 开放平台

**保持 v2.0 方案不变**

**预算**: ¥120,000 (3 个月)

---

## 📅 总体时间表 (8 个月)

### 第 1 个月 (2026-01)
- 🔥 P0-1: 优化现有新手引导 (2 周)
- 🔥 P0-2: 减少打包体积 (1 周)
- 🔥 P0-3: Token 自动刷新 (3 天)
- 🔥 P0-4: 优化启动速度 (1.5 周)

### 第 2-3 个月 (2026-02 至 2026-03)
- 🔴 P1-1: 核心交互优化 (3.5 周)
- 🔴 P1-2: main.py 拆分 (6-7 周)

### 第 4 个月 (2026-04)
- 🔴 P1-3: 添加类型注解 (3 周)
- 🔴 P1-4: macOS 支持启动 (1 周)

### 第 5-6 个月 (2026-05 至 2026-06)
- 🔴 P1-4: macOS 支持完成 (5 周)
- 🟠 P2-1: 信息架构重组 (4 周)
- 🟠 P2-2: UI 自动化测试启动

### 第 7-8 个月 (2026-07 至 2026-08)
- 🟠 P2-2: UI 自动化测试完成
- 🟠 P2-3: 性能监控与优化
- 🟠 P2-4: 插件系统设计

---

## 📊 资源分配

### 人员配置 (优化后)

| 角色 | 人数 | 职责 | 月薪 (CNY) |
|------|------|------|-----------|
| **前端开发** | 2 | UI 重构 + 新手引导优化 | ¥25,000 × 2 |
| **后端开发** | 1 | API 优化 + Token 刷新 | ¥28,000 |
| **测试工程师** | 1 | UI 自动化测试 + 回归测试 | ¥18,000 |
| **UX 设计师** | 1 | 界面设计 + 用户研究 | ¥22,000 |
| **DevOps** | 0.5 | CI/CD + 打包优化 | ¥15,000 |
| **产品经理** | 1 | 需求管理 + 用户反馈 | ¥30,000 |
| **总计** | **6.5 人** | | **¥163,000/月** |

---

### 预算估算 (8 个月)

| 项目 | 原 v2.0 预算 | v3.0 预算 | 说明 |
|------|------------|----------|------|
| **人力成本** | ¥1,200,000 | **¥1,304,000** | 8 个月 × ¥163,000 |
| **云服务** | ¥40,000 | **¥30,000** | Vercel Pro + Sentry (减少 2 个月) |
| **测试设备** | ¥30,000 | **¥30,000** | Mac Mini + iPhone |
| **开发者账号** | ¥4,000 | **¥4,000** | Apple Developer + 代码签名 |
| **用户研究** | ¥120,000 | **¥120,000** | 3 轮用户研究 |
| **设计资源** | ¥80,000 | **¥80,000** | UI 图标 + 插画 |
| **应急储备** | ¥265,000 | **¥232,000** | 15% 应急储备 |
| **总计** | **¥1,739,000** | **¥1,800,000** | 8 个月 |

**相比 v2.0 增加**: ¥61,000 (+3.5%)

**主要调整**:
- ✅ 减少 2 个月云服务费用 (移除深色主题开发)
- ✅ 新手引导优化预算 (¥15,000)
- ✅ 应急储备调整

---

## 🎯 成功指标 (KPI)

### 技术指标

| 指标 | 当前 | v1.7 目标 | v2.0 目标 |
|------|------|----------|----------|
| 打包体积 | 85 MB | **55-60 MB** ✅ | < 50 MB |
| 启动时间 | 3-5s | **1.5-2s** ✅ | < 1s |
| 测试覆盖率 | 80% | **85%** ✅ | > 90% |
| 单文件行数 | 3000+ | **< 1000 行** ✅ | < 500 行 |
| macOS 版本 | 无 | 无 | **已发布** ✅ |

### 用户指标

| 指标 | 当前估算 | v1.7 目标 | v2.0 目标 |
|------|---------|----------|----------|
| **新用户完成引导率** | ~70% | **85%** ✅ | > 90% |
| **7 日留存率** | ~45% | **60%** ✅ | > 70% |
| **AI 功能首次使用率** | ~30% | **50%** ✅ | > 60% |
| **核心功能发现率** | ~60% | **80%** ✅ | > 90% |
| **用户满意度 (CSAT)** | ~4.0/5.0 | **4.5/5.0** ✅ | > 4.7/5.0 |
| **NPS 评分** | 未统计 | **> 40** | > 60 |

### 商业指标

| 指标 | 当前估算 | v1.7 目标 | v2.0 目标 |
|------|---------|----------|----------|
| 下载转化率 | ~2% | **3%** ✅ | > 4% |
| 付费用户增长 | - | **100%** ✅ | 200% |
| 月收入增长 | - | **2 倍** | 5 倍 |
| 企业客户 | 0 | 0 | > 10 家 |

---

## 🔬 用户研究计划

### 第 1 轮: 用户访谈 (2026-02)

**目标**: 验证新手引导优化方向

**方法**: 1 对 1 访谈 (每人 30-60 分钟)

**样本**: 10-15 名新用户

**访谈问题**:
1. 你第一次打开 GaiYa 时的感受?
2. 新手引导是否帮助你理解核心功能?
3. 你最喜欢/讨厌 GaiYa 的什么?
4. 有哪些功能你不知道怎么用?
5. 你希望 GaiYa 增加什么功能?

---

### 第 2 轮: 可用性测试 (2026-04)

**目标**: 发现交互卡点

**方法**: 任务测试 + 录屏分析

**样本**: 5-8 名新用户

**测试任务**:
1. 完成新手引导流程
2. 使用 AI 生成任务
3. 切换主题
4. 查看统计报告
5. 使用编辑模式调整任务

**成功指标**:
- 任务完成率 > 80%
- 平均完成时间 < 5 分钟
- 错误率 < 20%

---

### 第 3 轮: NPS 调查 (2026-07)

**目标**: 衡量用户满意度

**方法**: 在线问卷 (所有用户)

**核心问题**:
1. 你会向朋友推荐 GaiYa 吗? (0-10 分)
2. 推荐/不推荐的原因?
3. 你最常使用的 3 个功能?
4. 你最希望改进的 3 个问题?

---

## 💡 战略建议

### 产品定位 (保持不变)

**核心价值主张**:
> GaiYa = 时间可视化 + AI 智能推理 + 游戏化激励

**目标用户**:
- 自由职业者 (需要自律管理时间)
- 知识工作者 (程序员、设计师、作家)
- 学生群体 (考研、备考、学习规划)

---

### 商业化路径 (保持不变)

**免费版** (引流):
- 核心功能: 进度条 + 任务管理
- 基础主题: 10 种预设主题
- 本地数据存储

**会员版** (变现):
- AI 功能: 300-5000 次/月配额
- 高级主题: 50+ 主题 + AI 生成
- 云端同步: 数据无限期保存
- 价格: ¥19/月, ¥199/年, ¥499/终身

**企业版** (扩展):
- 团队协作: 多人任务同步
- SSO 集成: 企业账号登录
- API 开放: 第三方系统集成
- 价格: ¥99/用户/月

---

## 📝 总结

### v3.0 核心变化

1. ✅ **新手引导策略调整**: 优化现有系统,而非重建
2. ✅ **移除深色主题**: 短期不需要,节省 2 周 + ¥40,000
3. ✅ **基于实际实现**: 避免重复开发 (92.5% 已完成)

### 资源优化

| 指标 | v2.0 | v3.0 | 变化 |
|------|------|------|------|
| 时间 | 8 个月 | 8 个月 | 持平 |
| 预算 | ¥1,739,000 | ¥1,800,000 | +3.5% |
| 团队 | 6.5-8.5 人 | 6.5 人 | 优化 |

### 核心原则

1. **用户优先**: 35% 资源投入 UX 改进
2. **渐进式交付**: 每月可见进展
3. **质量保障**: 每个改进都有测试验证
4. **数据驱动**: 3 轮用户研究支撑决策

---

**路线图完成** | 版本: v3.0 Final | 日期: 2025-12-10
