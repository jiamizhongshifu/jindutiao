# GaiYa v3.0 开发计划 - 按优先级排序

> **基于**: IMPROVEMENT_ROADMAP_V3_FINAL.md
> **制定日期**: 2025-12-10
> **执行周期**: 2026-01 至 2026-08 (8 个月)

---

## 🎯 优先级体系说明

| 优先级 | 标签 | 业务价值 | 技术难度 | 执行时间 | ROI |
|--------|------|----------|----------|----------|-----|
| **P0** | 🔥 | 极高 | 低-中 | 1-2 周 | 800%+ |
| **P1** | 🔴 | 高 | 中-高 | 1-2 月 | 400-600% |
| **P2** | 🟠 | 中 | 中-高 | 2-4 月 | 200-300% |
| **P3** | 🟡 | 低-中 | 高 | 4-8 月 | 100-200% |

---

## 🔥 P0 级任务 - 立即执行 (第 1 个月)

### 执行顺序: P0-1 → P0-2 → P0-3 → P0-4

---

### 📌 P0-1: 优化现有新手引导体验 ⭐⭐⭐⭐⭐

**业务价值**: 直接影响新用户留存率 (+40%)

**执行周期**: 第 1-2 周

**负责人**: 前端开发 × 1

**预算**: ¥15,000

#### 📅 详细排期

**第 1 周 (Day 1-7): 视觉增强**

| 日期 | 任务 | 产出 | 验收标准 |
|------|------|------|----------|
| Day 1-2 | 设计功能卡片图标 | 4 个 PNG 图标 (64x64) | 符合 MacOS 设计规范 |
| Day 3-4 | 实现 FeatureCard 组件 | `feature_card.py` (150行) | 支持悬停动画 |
| Day 5 | 集成到 WelcomeDialog | 修改 `welcome_dialog.py` | 视觉测试通过 |
| Day 6-7 | 测试 + Bug 修复 | 测试报告 | 无阻塞性 Bug |

**第 2 周 (Day 8-14): 交互优化**

| 日期 | 任务 | 产出 | 验收标准 |
|------|------|------|----------|
| Day 8-10 | 实现 MiniProgressBarPreview | `mini_progress_bar_preview.py` | 实时预览功能 |
| Day 11-12 | 实现 AI 生成动画对话框 | `ai_generation_dialog.py` (200行) | 旋转动画 + 状态轮播 |
| Day 13 | 优化完成页 | 修改 `setup_wizard.py` 完成页 | 成功动画 + 快速操作按钮 |
| Day 14 | 集成测试 + 发布 | v1.6.14-beta | 完成引导率 > 85% |

#### 🔧 技术实现要点

**1. FeatureCard 组件**

```python
# 文件: gaiya/ui/onboarding/feature_card.py
class FeatureCard(QWidget):
    """功能卡片 - 带图标和动画效果"""

    def __init__(self, icon: str, title: str, description: str):
        super().__init__()
        self.setFixedSize(400, 80)
        # 悬停动画实现
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
```

**2. MiniProgressBarPreview 组件**

```python
# 文件: gaiya/ui/onboarding/mini_progress_bar_preview.py
class MiniProgressBarPreview(QWidget):
    """迷你进度条预览组件"""

    def load_template(self, template: dict):
        """加载模板并渲染预览"""
        self.tasks = template['tasks']
        self.update()  # 触发重绘
```

**3. AI 生成动画对话框**

```python
# 文件: gaiya/ui/onboarding/ai_generation_dialog.py
class AIGenerationDialog(QDialog):
    """AI 生成任务对话框 - 带旋转动画"""

    def __init__(self):
        # 旋转动画
        self.rotation_animation = QPropertyAnimation(self.icon_label, b"rotation")
        self.rotation_animation.setLoopCount(-1)  # 无限循环

        # 状态文本轮播
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(3000)  # 每 3 秒切换
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| 新用户完成引导率 | ~70% | **85%** | Google Analytics 埋点 |
| 引导完成后 7 日留存 | ~45% | **60%** | 数据库查询 |
| AI 功能首次使用率 | ~30% | **50%** | API 调用日志 |
| 用户满意度评分 | ~4.0 | **4.5/5.0** | 应用内弹窗调查 |

#### 🎯 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 动画性能问题 | 中 | 中 | 在低端设备上禁用动画 |
| AI 生成超时 | 高 | 高 | 增加超时提示 + 重试按钮 |
| 图标设计延期 | 低 | 低 | 使用 Emoji 作为备选方案 |

---

### 📌 P0-2: 减少打包体积 (85MB → 55MB)

**业务价值**: 提升下载转化率 (+30%)

**执行周期**: 第 3 周

**负责人**: DevOps 工程师 × 0.5

**预算**: ¥5,000

#### 📅 详细排期

| 日期 | 任务 | 命令/操作 | 验收标准 |
|------|------|----------|----------|
| Day 15-16 | UPX 压缩测试 | `upx --best dist\GaiYa-v1.6.exe` | 体积减少 25-30 MB |
| Day 17-18 | 排除未使用模块 | 修改 `GaiYa.spec` excludes 列表 | 体积再减少 10-15 MB |
| Day 19 | 图片资源压缩 | PNG → WebP 转换 | 体积再减少 3-7 MB |
| Day 20-21 | 完整测试 | 测试所有功能 | 功能无回归 Bug |

#### 🔧 技术实现

**1. UPX 压缩配置**

```bash
# 推荐配置 (平衡压缩率和兼容性)
upx --best \
    --compress-icons=0 \
    --compress-exports=0 \
    --exclude "*.pyd" \
    dist\GaiYa-v1.6.exe

# 预期结果: 85 MB → 58-62 MB
```

**2. PyInstaller 排除配置**

```python
# GaiYa.spec 修改
excludes = [
    'PySide6.Qt3DAnimation',      # 3D 动画 (未使用)
    'PySide6.Qt3DCore',           # 3D 核心 (未使用)
    'PySide6.QtWebEngine',        # Web 引擎 (~30 MB)
    'PySide6.QtWebEngineWidgets', # Web 组件
    'PySide6.QtMultimedia',       # 音视频 (~10 MB)
    'PySide6.QtQuick',            # QML (~15 MB)
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,  # ← 关键
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
```

**3. 图片资源压缩**

```bash
# PNG → WebP (85% 质量)
for file in assets/*.png; do
    cwebp -q 85 "$file" -o "${file%.png}.webp"
done

# 预期收益: 3-7 MB
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| EXE 体积 | 85 MB | **55-60 MB** | 文件属性检查 |
| 下载转化率 | ~2% | **3%** | 下载统计 |
| 启动时间 | 3-5s | 不增加 | 性能测试 |
| 功能完整性 | 100% | 100% | 回归测试 |

---

### 📌 P0-3: 修复会话管理不当 (Token 自动刷新)

**业务价值**: 减少用户掉线频率,提升用户体验

**执行周期**: 第 3 周 (Day 22-24)

**负责人**: 后端开发 × 1

**预算**: ¥8,000

#### 📅 详细排期

| 日期 | 任务 | 文件 | 验收标准 |
|------|------|------|----------|
| Day 22 | 实现指数退避重试 | `gaiya/core/auth_client.py` | 自动重试 3 次 |
| Day 23 | 实现动态刷新时间 | `auth_client.py` | 80% 有效期时刷新 |
| Day 24 | 添加单元测试 | `tests/unit/test_auth_client.py` | 测试覆盖率 > 90% |

#### 🔧 技术实现

**1. 指数退避重试机制**

```python
# gaiya/core/auth_client.py
class AuthClient:
    def __init__(self):
        self.refresh_retry_count = 0
        self.max_retries = 3
        self.token_lock = threading.Lock()  # 线程安全

    def _auto_refresh_token(self):
        """自动刷新 Token (带重试)"""
        try:
            response = httpx.post(
                f"{VERCEL_URL}/api/auth-refresh",
                json={"refresh_token": self.refresh_token},
                timeout=10.0
            )

            if response.status_code == 200:
                with self.token_lock:  # 原子更新
                    self._update_tokens(response.json())
                self.refresh_retry_count = 0  # 重置计数器
            elif response.status_code == 401:
                # Refresh Token 过期
                self.token_expired.emit()

        except httpx.TimeoutException:
            self.refresh_retry_count += 1

            if self.refresh_retry_count < self.max_retries:
                # 指数退避: 2^n 秒后重试
                retry_delay = 2 ** self.refresh_retry_count
                logger.warning(f"Token 刷新超时,{retry_delay}秒后重试")
                QTimer.singleShot(retry_delay * 1000, self._auto_refresh_token)
            else:
                logger.error("Token 刷新失败次数过多,停止重试")
                self.token_expired.emit()
```

**2. 动态刷新时间**

```python
def _calculate_refresh_time(self, token_expires_at: datetime) -> int:
    """计算刷新时间 (80% 有效期时刷新)"""
    total_seconds = (token_expires_at - datetime.now()).total_seconds()
    return int(total_seconds * 0.8)

def start_auto_refresh(self):
    """启动自动刷新定时器"""
    refresh_time = self._calculate_refresh_time(self.token_expires_at)
    self.refresh_timer.start(refresh_time * 1000)
```

**3. 单元测试**

```python
# tests/unit/test_auth_client.py
@pytest.mark.asyncio
async def test_token_refresh_retry():
    """测试 Token 刷新重试机制"""
    client = AuthClient()
    client.refresh_token = "valid_refresh_token"

    # Mock API 超时
    with patch('httpx.post') as mock_post:
        mock_post.side_effect = httpx.TimeoutException()

        client._auto_refresh_token()

        # 验证重试次数
        assert client.refresh_retry_count == 1
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| Token 刷新成功率 | ~85% | **95%** | API 日志统计 |
| 用户掉线次数 | 频繁 | 几乎无 | 用户反馈 |
| 单元测试覆盖率 | 0% | **90%** | pytest coverage |

---

### 📌 P0-4: 优化首次启动速度 (3-5s → 1.5-2s)

**业务价值**: 提升用户首次体验

**执行周期**: 第 4 周 + 第 5 周前半段 (Day 25-32)

**负责人**: 前端开发 × 1

**预算**: ¥20,000

#### 📅 详细排期

| 日期 | 任务 | 优化方案 | 预期收益 |
|------|------|----------|----------|
| Day 25-27 | 延迟加载配置界面 | 懒加载 `config_gui.py` | 减少 1-2s |
| Day 28-29 | 数据库懒加载 | 懒加载 `db_manager.py` | 减少 0.3-0.5s |
| Day 30-31 | 场景资源异步加载 | 异步加载场景 JSON | 减少 0.5-0.8s |
| Day 32 | 性能测试验证 | cProfile 分析 | 启动时间 < 2s |

#### 🔧 技术实现

**1. 延迟加载配置界面**

```python
# main.py 修改
class TimeProgressBar(QWidget):
    def __init__(self):
        super().__init__()
        self.config_window = None  # 延迟初始化
        self.config_loading = False

    def show_config(self):
        """显示配置界面 (延迟加载)"""
        if self.config_window is not None:
            self.config_window.show()
            return

        if self.config_loading:
            QMessageBox.information(self, "提示", "配置界面正在加载...")
            return

        # 显示加载提示
        loading_dialog = QProgressDialog("加载配置界面...", None, 0, 0, self)
        loading_dialog.setWindowModality(Qt.WindowModal)
        loading_dialog.show()

        # 在后台线程加载
        def _load_config():
            import config_gui  # ← 首次点击时才加载
            self.config_window = config_gui.ConfigWindow(self)

        worker = AsyncWorker(_load_config)
        worker.finished.connect(lambda: self._on_config_loaded(loading_dialog))
        worker.start()

        self.config_loading = True
```

**2. 数据库懒加载**

```python
# gaiya/data/db_manager.py
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None
        self._lock = threading.Lock()

    @property
    def conn(self):
        """懒加载数据库连接 (线程安全)"""
        if self._conn is None:
            with self._lock:
                if self._conn is None:  # 双重检查锁定
                    self._conn = sqlite3.connect(
                        self.db_path,
                        check_same_thread=False,
                        timeout=10.0
                    )
                    self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn
```

**3. 场景资源异步加载**

```python
# gaiya/scene/loader.py
class SceneLoader:
    def load_scene_async(self, scene_id: str):
        """异步加载场景资源"""
        def _load():
            try:
                scene_data = self._load_scene_data(scene_id)
                self.scene_loaded.emit(scene_data)
            except Exception as e:
                logger.error(f"场景加载异常: {e}")
                self.scene_load_failed.emit(str(e))

        worker = QThread()
        loader = AsyncWorker(_load)
        loader.moveToThread(worker)
        worker.started.connect(loader.run)
        worker.start()
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| 冷启动时间 | 3-5s | **1.5-2s** | cProfile 性能测试 |
| 内存占用 | 80-120 MB | 不增加 | 任务管理器 |
| 功能完整性 | 100% | 100% | 回归测试 |

---

## 🔴 P1 级任务 - 高优先级 (第 2-6 个月)

### 执行顺序: P1-1 → P1-2 → P1-3 → P1-4

---

### 📌 P1-1: 核心交互优化 (UX 改进)

**业务价值**: 提升日活跃用户体验

**执行周期**: 第 5 周后半段 + 第 6-8 周 (3.5 周)

**负责人**: 前端开发 × 1

**预算**: ¥36,000

#### 📅 详细排期

| 周次 | 任务 | 产出 | 工作量 |
|------|------|------|--------|
| 第 5 周后半 | 富文本悬停卡片 | `rich_tooltip.py` | 3 天 |
| 第 6 周 | 编辑模式多种入口 | 修改 `main.py` | 3 天 |
| 第 7 周 | AI 功能前置化 | 修改 `config_gui.py` | 5 天 |
| 第 8 周 | 成就即时反馈 | `achievement_notification.py` | 5 天 |

#### 🔧 技术实现

**1. 富文本悬停卡片**

```python
# gaiya/ui/components/rich_tooltip.py
class RichToolTip(QWidget):
    """富文本悬停卡片"""

    def __init__(self, task: dict):
        super().__init__()
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)

        # 任务名称 (大字体 + emoji)
        title = QLabel(f"{self._get_emoji(task)} {task['name']}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        # 进度信息
        progress = self._calculate_progress(task)
        progress_info = QLabel(
            f"📊 已完成 {progress['completed']} ({progress['percentage']:.0f}%)"
        )
```

**2. 编辑模式多种入口**

```python
# main.py 修改
def mouseDoubleClickEvent(self, event):
    """双击进入编辑模式"""
    if not self.edit_mode:
        msg = QMessageBox(self)
        msg.setText("✏️ 进入编辑模式后,可以拖拽任务边缘调整时长")
        if msg.exec() == QMessageBox.Ok:
            self.enter_edit_mode()

def contextMenuEvent(self, event):
    """右键菜单"""
    menu = QMenu(self)

    if not self.edit_mode:
        edit_action = menu.addAction("✏️ 编辑模式")
        edit_action.triggered.connect(self.enter_edit_mode)
    else:
        exit_action = menu.addAction("✅ 退出编辑模式")
        exit_action.triggered.connect(self.exit_edit_mode)

    menu.exec(event.globalPos())
```

**3. AI 功能前置化**

```python
# config_gui.py 修改
class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 顶部 AI 配额卡片
        quota_card = AIQuotaCard()
        quota_card.setFixedHeight(80)

        layout = QVBoxLayout()
        layout.addWidget(quota_card)  # ← 前置显示
        layout.addWidget(self.tab_widget)
```

**4. 成就即时反馈**

```python
# gaiya/ui/components/achievement_notification.py
class AchievementNotification(QWidget):
    """成就解锁通知 (Steam 风格)"""

    def show_notification(self):
        """从右侧滑入动画"""
        screen = QApplication.primaryScreen().geometry()

        # 滑入动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setStartValue(QPoint(screen.width(), screen.height() - 120))
        self.animation.setEndValue(QPoint(screen.width() - 320, screen.height() - 120))

        self.show()
        self.animation.start()

        # 3 秒后自动隐藏
        QTimer.singleShot(3000, self.hide_notification)
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| 功能发现率 | ~60% | **80%** | 用户访谈 |
| 编辑模式使用率 | ~15% | **40%** | 数据埋点 |
| AI 功能使用率 | ~30% | **50%** | API 调用日志 |
| 用户满意度 | 4.0 | **4.5** | NPS 调查 |

---

### 📌 P1-2: 代码重构 - 拆分大文件

**业务价值**: 提升代码可维护性,降低 Bug 率

**执行周期**: 第 9-15 周 (6-7 周)

**负责人**: 前端开发 × 2

**预算**: ¥120,000

#### 📅 详细排期

| 阶段 | 周次 | 任务 | 产出 | 负责人 |
|------|------|------|------|--------|
| Phase 1 | 第 9-10 周 | 提取工具函数 | `time_utils.py`, `color_utils.py` | 开发 A |
| Phase 2 | 第 11-13 周 | 提取业务逻辑类 | `TaskManager`, `ThemeManager` | 开发 A + B |
| Phase 3 | 第 14 周 | 提取 UI 组件 | `ProgressBarWidget`, `TaskBlockWidget` | 开发 B |
| Phase 4 | 第 15 周 | 集成测试 + 回归测试 | 测试报告 | 测试工程师 |

#### 🔧 技术实现 (Strangler Fig Pattern)

**第 1 阶段: 提取工具函数 (无状态)**

```python
# gaiya/ui/progress_bar/time_utils.py
def time_to_minutes(time_str: str) -> int:
    """时间字符串转分钟数"""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def minutes_to_time(minutes: int) -> str:
    """分钟数转时间字符串"""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
```

**第 2 阶段: 提取业务逻辑类 (有状态)**

```python
# gaiya/ui/progress_bar/task_manager.py
class TaskManager(QObject):
    """任务数据管理器"""

    tasks_changed = Signal(list)  # 任务数据变化信号

    def __init__(self):
        super().__init__()
        self.tasks = []

    def load_tasks(self, file_path: str) -> bool:
        """加载任务数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = data.get('tasks', [])
                self.tasks_changed.emit(self.tasks)
                return True
        except Exception as e:
            logger.error(f"加载任务失败: {e}")
            return False
```

**第 3 阶段: 提取 UI 组件 (Qt Widget)**

```python
# gaiya/ui/progress_bar/progress_bar_widget.py
class ProgressBarWidget(QWidget):
    """进度条渲染组件 (仅负责绘制)"""

    def __init__(self):
        super().__init__()
        self.current_percentage = 0.0
        self.theme_colors = {}

    def paintEvent(self, event):
        """绘制进度条"""
        painter = QPainter(self)
        self._draw_background(painter)
        self._draw_progress(painter)
        self._draw_tasks(painter)
        painter.end()
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| main.py 行数 | 3000+ | **< 1000** | 代码统计 |
| 单文件行数 | 3000+ | **< 500** | 代码审查 |
| 圈复杂度 | ~50-80 | **< 20** | Radon 分析 |
| 单元测试覆盖率 | ~80% | **> 90%** | pytest coverage |

---

### 📌 P1-3: 添加完整类型注解

**业务价值**: 提升代码可读性,减少类型错误

**执行周期**: 第 16-18 周 (3 周)

**负责人**: 后端开发 × 1

**预算**: ¥30,000

#### 📅 详细排期

| 周次 | 模块 | 预期文件数 | 工具 |
|------|------|-----------|------|
| 第 16 周 | gaiya/utils/ | 11 个文件 | MonkeyType |
| 第 17 周 | gaiya/core/ | 30+ 个文件 | MonkeyType + 手工 |
| 第 18 周 | gaiya/ui/ | 15+ 个文件 | mypy 验证 |

#### 🔧 技术实现

```bash
# Step 1: 运行程序收集类型信息
monkeytype run main.py

# Step 2: 生成类型注解
monkeytype apply gaiya.core.task_manager

# Step 3: 验证类型正确性
mypy gaiya/core/task_manager.py --strict
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| 类型注解覆盖率 | ~60% | **> 90%** | mypy coverage |
| mypy 检查通过率 | ~70% | **100%** | mypy --strict |

---

### 📌 P1-4: macOS 支持

**业务价值**: 扩展用户规模 (+50%)

**执行周期**: 第 19-24 周 (6 周)

**负责人**: 前端开发 × 1

**预算**: ¥100,000 (包含 Mac Mini 设备)

#### 📅 详细排期

| 周次 | 任务 | 产出 | 验收标准 |
|------|------|------|----------|
| 第 19 周 | 完善跨平台工具类 | `window_utils.py` | 支持 macOS API |
| 第 20-21 周 | macOS 打包测试 | `GaiYa-macOS.spec` | 生成 .app bundle |
| 第 22-23 周 | 功能适配 (托盘/自启动) | `autostart_manager.py` | 使用 LaunchAgent |
| 第 24 周 | 测试验证 + 发布 | GaiYa v1.7.0 macOS | App Store 提交 |

#### 🔧 技术实现

**1. 跨平台窗口工具**

```python
# gaiya/utils/window_utils.py
import platform

def set_window_transparent(window):
    """设置窗口透明 (跨平台)"""
    if platform.system() == 'Windows':
        # Windows API 调用
        from ctypes import windll
        hwnd = int(window.winId())
        windll.user32.SetWindowLongW(hwnd, -20, 0x00080000)

    elif platform.system() == 'Darwin':  # macOS
        # macOS 原生 API 调用
        window.setAttribute(Qt.WA_TranslucentBackground)
        window.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
```

**2. macOS 开机自启动**

```python
# autostart_manager.py
class AutoStartManager:
    def enable_autostart_macos(self):
        """macOS 开机自启动 (LaunchAgent)"""
        plist_path = os.path.expanduser(
            '~/Library/LaunchAgents/com.gaiya.plist'
        )

        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gaiya</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''

        with open(plist_path, 'w') as f:
            f.write(plist_content)

        os.system(f'launchctl load {plist_path}')
```

**3. macOS 打包配置**

```python
# GaiYa-macOS.spec
app = BUNDLE(
    exe,
    name='GaiYa.app',
    icon='assets/icon.icns',
    bundle_identifier='com.gaiya.app',
    info_plist={
        'CFBundleName': 'GaiYa',
        'CFBundleDisplayName': 'GaiYa 每日进度条',
        'CFBundleVersion': '1.7.0',
        'NSHighResolutionCapable': 'True',
    },
)
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| macOS 兼容性 | 0% | **100%** | macOS 10.15+ 测试 |
| 功能一致性 | - | **100%** | 与 Windows 版对比 |
| 用户规模扩展 | - | **+50%** | 下载统计 |

---

## 🟠 P2 级任务 - 中优先级 (第 6-8 个月)

### 执行顺序: P2-1 → P2-2 → P2-3 → P2-4

---

### 📌 P2-1: 信息架构重组

**业务价值**: 降低认知负担,提升任务完成效率

**执行周期**: 第 25-28 周 (4 周)

**负责人**: 前端开发 × 1 + UX 设计师 × 1

**预算**: ¥60,000

#### 📅 详细排期

| 周次 | 任务 | 产出 | 负责人 |
|------|------|------|--------|
| 第 25-26 周 | 统计报告标签页重组 (8→5) | 修改 `statistics_gui.py` | 前端开发 |
| 第 27-28 周 | 配置界面侧边栏导航 | 修改 `config_gui.py` | 前端开发 |

#### 🔧 技术实现

**1. 统计报告标签页重组**

```
旧结构 (8 个标签页):
概览 / 周统计 / 月统计 / 任务分类 / 成就 / 目标 / AI推理 / 时间回放

新结构 (5 个标签页):
1. 📊 概览 (Dashboard)
2. 📈 深度分析 (合并周/月/分类)
3. 🎯 成就与目标 (左右分栏)
4. 🤖 AI 智能 (上下分栏)
5. 📅 历史记录
```

**2. 配置界面侧边栏导航**

```python
# config_gui.py 重构
class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 侧边栏导航
        self.sidebar = QListWidget()
        self.sidebar.addItem("🏠 概览")
        self.sidebar.addItem("📝 任务")
        self.sidebar.addItem("🎨 外观")
        self.sidebar.addItem("🤖 AI")
        self.sidebar.addItem("👤 账户")
        self.sidebar.addItem("⚙️ 高级")

        # 堆叠式内容区
        self.content_stack = QStackedWidget()

        # 左右分栏布局
        layout = QHBoxLayout()
        layout.addWidget(self.sidebar, 1)
        layout.addWidget(self.content_stack, 3)
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| 认知负担 | 100% | **60%** | 可用性测试 |
| 任务完成效率 | 100% | **125%** | 时间测量 |
| 界面复杂度 | 100% | **60%** | 专家评审 |

---

### 📌 P2-2: UI 自动化测试

**业务价值**: 减少手工测试时间 70%

**执行周期**: 第 25-32 周 (8 周)

**负责人**: 测试工程师 × 1

**预算**: ¥100,000

#### 📅 详细排期

| 周次 | 测试模块 | 用例数 | 覆盖率目标 |
|------|---------|--------|-----------|
| 第 25-26 周 | 主窗口显示/隐藏 | 10 个 | 20% |
| 第 27-28 周 | 进度条渲染 + 任务悬停 | 20 个 | 40% |
| 第 29-30 周 | 编辑模式拖拽 | 15 个 | 60% |
| 第 31-32 周 | 配置界面 + 统计报告 | 25 个 | 80% |

#### 🔧 技术实现

```python
# tests/ui/test_main_window.py
import pytest
from PySide6.QtCore import Qt, QPoint
from main import TimeProgressBar

def test_progress_bar_visible(qtbot):
    """测试进度条可见性"""
    window = TimeProgressBar()
    qtbot.addWidget(window)

    window.show()
    assert window.isVisible()
    assert window.width() > 0

def test_task_hover(qtbot):
    """测试任务悬停效果"""
    window = TimeProgressBar()
    qtbot.addWidget(window)
    window.show()

    # 模拟鼠标移动到任务块
    qtbot.mouseMove(window, pos=QPoint(100, 5))

    # 验证悬停任务索引更新
    assert window.hovered_task_index >= 0
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| UI 测试覆盖率 | 0% | **> 50%** | pytest coverage |
| 手工测试时间 | 100% | **30%** | 时间统计 |
| 回归测试自动化率 | 0% | **80%** | CI/CD 报告 |

---

### 📌 P2-3: 性能监控与优化

**业务价值**: 提升应用稳定性和性能

**执行周期**: 第 25-32 周 (8 周)

**负责人**: 后端开发 × 1

**预算**: ¥60,000

#### 📅 详细排期

| 周次 | 任务 | 产出 |
|------|------|------|
| 第 25-26 周 | 集成 APM (Sentry) | 性能监控仪表盘 |
| 第 27-28 周 | 关键路径性能优化 | 进度条刷新优化 |
| 第 29-30 周 | 内存泄漏检测 | 修复内存泄漏 |
| 第 31-32 周 | 数据库查询优化 | 索引优化 |

#### 🔧 技术实现

**1. 集成 Sentry APM**

```python
# gaiya/__init__.py
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project",
    traces_sample_rate=0.1,  # 10% 采样率
    profiles_sample_rate=0.1,
    environment="production"
)
```

**2. 性能监控装饰器**

```python
# gaiya/utils/performance_monitor.py
class PerformanceMonitor:
    def measure(self, name: str):
        """装饰器: 测量函数执行时间"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time

                if elapsed > 0.1:  # 慢查询告警
                    logger.warning(f"性能告警: {name} 耗时 {elapsed:.2f}s")

                return result
            return wrapper
        return decorator
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| 进度条刷新性能 | 60fps | **60fps** | 性能分析器 |
| 内存占用 | 80-120 MB | **< 80 MB** | 任务管理器 |
| CPU 占用 (空闲) | 1-2% | **< 1%** | 任务管理器 |

---

### 📌 P2-4: 插件系统

**业务价值**: 社区生态建设,扩展性

**执行周期**: 第 29-48 周 (4-5 个月)

**负责人**: 前端开发 × 1 + 后端开发 × 1

**预算**: ¥180,000

#### 📅 详细排期

| 阶段 | 周次 | 任务 | 产出 |
|------|------|------|------|
| 设计阶段 | 第 29-32 周 | 插件架构设计 | 设计文档 |
| 开发阶段 | 第 33-40 周 | 插件加载器 + API | `plugin_manager.py` |
| 测试阶段 | 第 41-44 周 | 示例插件开发 | 3 个示例插件 |
| 发布阶段 | 第 45-48 周 | 插件市场 | Web 界面 |

#### 🔧 技术实现

```python
# gaiya/plugins/plugin_manager.py
class PluginManager:
    """插件管理器"""

    def load_plugin(self, plugin_path: str):
        """加载插件"""
        spec = importlib.util.spec_from_file_location("plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin = module.Plugin()
        plugin.on_load(self.api)
```

#### 📊 成功指标

| 指标 | 当前 | 目标 | 验收方法 |
|------|------|------|----------|
| 插件市场上线 | 无 | **已上线** | Web 访问 |
| 示例插件数量 | 0 | **> 3** | 插件列表 |
| 社区活跃度 | 0 | **> 100 星标** | GitHub |

---

## 🟡 P3 级任务 - 低优先级 (第 8 个月后)

### 执行顺序: P3-1 → P3-2 → P3-3

---

### 📌 P3-1: 移动端应用 (React Native)

**业务价值**: 扩展使用场景 (+100% 用户)

**执行周期**: 6 个月

**预算**: ¥240,000

---

### 📌 P3-2: 团队协作功能

**业务价值**: 进入企业市场

**执行周期**: 4 个月

**预算**: ¥160,000

---

### 📌 P3-3: API 开放平台

**业务价值**: 生态系统建设

**执行周期**: 3 个月

**预算**: ¥120,000

---

## 📅 总体甘特图 (前 8 个月)

```
月份     │ 2026-01 │ 2026-02 │ 2026-03 │ 2026-04 │ 2026-05 │ 2026-06 │ 2026-07 │ 2026-08 │
─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
P0-1     │ ████    │         │         │         │         │         │         │         │
P0-2     │   ██    │         │         │         │         │         │         │         │
P0-3     │   ██    │         │         │         │         │         │         │         │
P0-4     │    ███  │         │         │         │         │         │         │         │
P1-1     │     ████│████     │         │         │         │         │         │         │
P1-2     │         │  ██████ │████████ │██       │         │         │         │         │
P1-3     │         │         │         │  ██████ │         │         │         │         │
P1-4     │         │         │         │    █████│████████ │         │         │         │
P2-1     │         │         │         │         │         │ ████████│         │         │
P2-2     │         │         │         │         │         │ ████████│████████ │         │
P2-3     │         │         │         │         │         │ ████████│████████ │         │
P2-4     │         │         │         │         │         │         │ ████████│████████ │
```

---

## 🎯 里程碑节点

| 里程碑 | 日期 | 交付物 | 关键指标 |
|--------|------|--------|----------|
| **M1: 性能优化版** | 2026-02-07 | v1.6.14 | 体积 < 60MB, 启动 < 2s |
| **M2: UX 增强版** | 2026-03-14 | v1.7.0 | 新用户留存率 > 60% |
| **M3: 代码重构版** | 2026-05-02 | v1.8.0 | 单文件 < 1000 行 |
| **M4: 跨平台版** | 2026-06-20 | v1.9.0 | macOS 版本发布 |
| **M5: 质量提升版** | 2026-08-15 | v1.10.0 | 测试覆盖率 > 85% |
| **M6: 可扩展版** | 2026-10-31 | v2.0.0 | 插件系统上线 |

---

## 📊 资源分配表

| 角色 | Q1 (1-3月) | Q2 (4-6月) | Q3 (7-8月) | 总工作量 |
|------|-----------|-----------|-----------|----------|
| **前端开发 A** | P0-1, P0-4, P1-1 | P1-2 (50%) | - | 5.5 月 |
| **前端开发 B** | - | P1-2 (50%), P1-4 | P2-1 | 4 月 |
| **后端开发** | P0-3, P1-3 | - | P2-3 | 4 月 |
| **测试工程师** | 回归测试 | P1-2 测试 | P2-2 | 3 月 |
| **UX 设计师** | P0-1 设计 | 用户研究 | P2-1 设计 | 2 月 |
| **DevOps** | P0-2 | - | - | 0.5 月 |
| **产品经理** | 需求管理 | 需求管理 | 需求管理 | 8 月 |

---

## 💰 预算分配表

| 优先级 | 任务数 | 预算 (CNY) | 占比 | 关键产出 |
|--------|--------|-----------|------|----------|
| **P0** | 4 | ¥48,000 | 2.7% | 性能优化 + 新手引导 |
| **P1** | 4 | ¥286,000 | 15.9% | 代码重构 + macOS 支持 |
| **P2** | 4 | ¥400,000 | 22.2% | UI 测试 + 插件系统 |
| **P3** | 3 | ¥520,000 | 28.9% | 移动端 + 团队协作 |
| **人力** | - | ¥1,304,000 | 72.4% | 6.5 人 × 8 个月 |
| **其他** | - | ¥342,000 | 19.0% | 云服务 + 设备 + 研究 |
| **总计** | **15** | **¥1,800,000** | **100%** | - |

---

## 🚨 风险矩阵

| 风险 | 概率 | 影响 | 优先级 | 应对策略 |
|------|------|------|--------|----------|
| 代码重构延期 | 高 | 高 | P1 | 分阶段交付,每周可工作版本 |
| macOS 测试环境不足 | 中 | 中 | P1 | 提前采购 Mac Mini |
| UPX 压缩兼容性问题 | 中 | 低 | P0 | 保留未压缩版本作为备选 |
| 插件系统安全漏洞 | 低 | 高 | P2 | 代码审计 + 沙箱隔离 |
| 人力不足导致延期 | 中 | 高 | P1 | 预留 15% 应急预算 |

---

## 📝 总结

### v3.0 开发计划核心特点

1. ✅ **渐进式交付**: 每月有可见里程碑
2. ✅ **优先级清晰**: P0 → P1 → P2 → P3 严格执行
3. ✅ **资源优化**: 6.5 人团队,¥180 万预算
4. ✅ **风险可控**: 每个任务都有应对策略

### 立即行动 (本周)

- [ ] 启动 P0-1: 优化新手引导
- [ ] 设计功能卡片图标 (4 个)
- [ ] 准备 UPX 压缩工具
- [ ] 配置开发环境

---

**计划完成** | 版本: v3.0 | 日期: 2025-12-10
