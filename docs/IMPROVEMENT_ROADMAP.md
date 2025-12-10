# GaiYa 应用改进详细计划

> **制定日期**: 2025-12-10
> **当前版本**: v1.6.13
> **目标版本**: v2.0.0
> **执行周期**: 2025-12 至 2026-06 (6 个月)

---

## 📋 优先级定义

| 优先级 | 标签 | 定义 | 执行时间 |
|--------|------|------|----------|
| **P0** | 🔥 紧急 | 严重影响用户体验,需立即修复 | 本周内 |
| **P1** | 🔴 高 | 重要功能/优化,需优先安排 | 1 个月内 |
| **P2** | 🟠 中 | 重要但不紧急,可分阶段完成 | 2-3 个月 |
| **P3** | 🟡 低 | 锦上添花,资源允许时执行 | 3-6 个月 |

---

## 🔥 P0 级任务 (紧急 - 本周完成)

### P0-1: 减少打包体积 (85MB → 50MB)

**问题描述**:
- 当前 EXE 体积 85 MB,影响下载转化率
- PySide6 占 50 MB (58%),是主要体积来源

**改进方案**:

#### 方案 A: UPX 压缩 (推荐,快速见效)
```bash
# 1. 下载 UPX 工具
# https://github.com/upx/upx/releases

# 2. 压缩 EXE (可减少 30-40%)
upx --best --lzma dist\GaiYa-v1.6.exe

# 3. 预期结果
# 85 MB → 50-60 MB
```

**优点**:
- ✅ 实施简单,立即生效
- ✅ 不影响功能
- ✅ 兼容性好

**缺点**:
- ⚠️ 启动速度可能略慢 (增加 0.5-1 秒)
- ⚠️ 某些杀毒软件误报率增加 (可通过签名解决)

#### 方案 B: 移除未使用的 PySide6 模块 (深度优化)
```python
# GaiYa.spec 修改
# 1. 排除未使用的 Qt 模块
excludes = [
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DExtras',
    'PySide6.QtBluetooth',
    'PySide6.QtLocation',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNfc',
    'PySide6.QtPositioning',
    'PySide6.QtQuick',
    'PySide6.QtQuickWidgets',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtSql',  # 如果不用 Qt SQL
    'PySide6.QtTest',
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineWidgets',
]

# 2. 修改 Analysis 配置
a = Analysis(
    ...,
    excludes=excludes,
    ...
)
```

**预期收益**:
- 减少 10-15 MB
- 配合 UPX 可达到 50 MB 目标

#### 方案 C: 图片资源压缩
```bash
# 1. 将 PNG 转为 WebP (减少 70-80%)
for file in assets/*.png; do
    cwebp -q 85 "$file" -o "${file%.png}.webp"
done

# 2. 压缩 GIF 动画
gifsicle -O3 --colors 256 marker.gif -o marker_optimized.gif
```

**实施步骤**:
1. **本周三前**: 实施 UPX 压缩
2. **本周五前**: 排除未使用模块
3. **下周一前**: 压缩图片资源
4. **验证**: 测试所有功能正常

**预期效果**:
- 体积: 85 MB → **45-50 MB** ✅
- 下载转化率: 提升 **30-40%** ✅

---

### P0-2: 修复会话管理不当 (安全问题)

**问题描述**:
- Refresh Token 未自动刷新
- Access Token 过期后需要重新登录
- 影响用户体验 (频繁掉线)

**改进方案**:

#### 实施步骤

**1. 修改 `gaiya/core/auth_client.py`**:
```python
class AuthClient:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None  # 新增: Token 过期时间

        # 新增: 定时器自动刷新 Token
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh_token)

    def _auto_refresh_token(self):
        """自动刷新 Token (在过期前 5 分钟刷新)"""
        if not self.refresh_token:
            return

        # 检查 Token 是否即将过期
        now = datetime.now()
        if self.token_expires_at and (self.token_expires_at - now).total_seconds() < 300:
            logger.info("Token 即将过期,自动刷新...")
            try:
                response = requests.post(
                    f"{VERCEL_URL}/api/auth-refresh",
                    json={"refresh_token": self.refresh_token}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data["access_token"]
                    self.token_expires_at = datetime.fromisoformat(data["expires_at"])

                    # 保存到 keyring
                    keyring.set_password("gaiya", "access_token", self.access_token)
                    logger.info("Token 刷新成功")
                else:
                    logger.error(f"Token 刷新失败: {response.status_code}")
            except Exception as e:
                logger.error(f"自动刷新 Token 异常: {e}")

    def start_auto_refresh(self):
        """启动自动刷新定时器 (每 5 分钟检查一次)"""
        self.refresh_timer.start(5 * 60 * 1000)  # 5 分钟
```

**2. 修改 `main.py` 初始化逻辑**:
```python
def __init__(self):
    ...
    # 初始化认证客户端
    self.auth_client = AuthClient()

    # 启动自动刷新 Token
    self.auth_client.start_auto_refresh()
```

**3. 添加测试用例**:
```python
# tests/unit/test_auth_client.py
def test_auto_refresh_token():
    """测试 Token 自动刷新"""
    client = AuthClient()
    client.access_token = "old_token"
    client.refresh_token = "refresh_token"
    client.token_expires_at = datetime.now() + timedelta(minutes=3)

    # 触发自动刷新
    client._auto_refresh_token()

    # 验证 Token 已更新
    assert client.access_token != "old_token"
```

**实施时间**: 本周四完成

**预期效果**:
- ✅ 用户无感知自动刷新
- ✅ 减少登录频率
- ✅ 提升用户体验

---

### P0-3: 优化首次启动速度 (3-5s → 1s)

**问题描述**:
- 冷启动耗时 3-5 秒
- 用户感知明显延迟

**性能分析**:
```python
# 启动耗时分析 (使用 cProfile)
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... 应用启动代码 ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)  # 打印前 20 个耗时操作
```

**优化方案**:

#### 方案 A: 延迟加载非核心模块
```python
# main.py 修改前
import config_gui  # 启动时立即加载
import scene_editor
import statistics_gui

# main.py 修改后
def __init__(self):
    ...
    # 延迟加载配置界面 (仅在用户点击时加载)
    self.config_window = None

def show_config(self):
    """显示配置界面 (延迟加载)"""
    if self.config_window is None:
        import config_gui  # 首次点击时才加载
        self.config_window = config_gui.ConfigWindow(self)

    self.config_window.show()
```

**预期收益**: 减少 1-2 秒

#### 方案 B: 数据库连接池预热
```python
# gaiya/data/db_manager.py
class DatabaseManager:
    def __init__(self):
        # 修改前: 启动时建立连接
        self.conn = sqlite3.connect(db_path)

        # 修改后: 首次使用时建立连接
        self._conn = None

    @property
    def conn(self):
        """懒加载数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn
```

**预期收益**: 减少 0.5 秒

#### 方案 C: 场景资源异步加载
```python
# gaiya/scene/loader.py
class SceneLoader:
    def load_scene_async(self, scene_id: str):
        """异步加载场景资源"""
        def _load():
            # 在后台线程中加载资源
            scene_data = self._load_scene_data(scene_id)
            # 加载完成后发送信号
            self.scene_loaded.emit(scene_data)

        # 启动后台线程
        thread = QThread()
        worker = AsyncWorker(_load)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        thread.start()
```

**预期收益**: 减少 1 秒

**实施步骤**:
1. **周一**: 延迟加载配置界面
2. **周二**: 数据库懒加载
3. **周三**: 场景资源异步加载
4. **周四**: 性能测试验证

**预期效果**:
- 启动时间: 3-5s → **1-1.5s** ✅
- 用户体验显著提升 ✅

---

## 🔴 P1 级任务 (高优先级 - 1 个月完成)

### P1-1: 代码重构 - 拆分大文件

**问题描述**:
- `main.py`: 3000+ 行 (圈复杂度过高)
- `config_gui.py`: 2500+ 行
- `statistics_gui.py`: 3000+ 行
- 难以维护,测试困难

**重构方案**:

#### 1. main.py 拆分 (3000 行 → 6 个文件)

**目标结构**:
```
gaiya/ui/progress_bar/
├── __init__.py
├── progress_bar_widget.py      # 进度条渲染 (500行)
├── task_manager.py              # 任务数据管理 (300行)
├── marker_renderer.py           # 时间标记渲染 (400行)
├── edit_mode_controller.py      # 编辑模式逻辑 (400行)
├── scene_integration.py         # 场景系统集成 (300行)
└── tray_manager.py              # 系统托盘管理 (200行)
```

**实施步骤**:

**第 1 周: 提取进度条渲染逻辑**
```python
# gaiya/ui/progress_bar/progress_bar_widget.py
class ProgressBarWidget(QWidget):
    """进度条渲染组件 (仅负责绘制)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_percentage = 0.0
        self.theme_colors = {}

    def paintEvent(self, event):
        """绘制进度条"""
        painter = QPainter(self)
        self._draw_background(painter)
        self._draw_progress(painter)
        self._draw_tasks(painter)
        painter.end()

    def _draw_background(self, painter):
        """绘制背景 (渐变/纯色)"""
        ...

    def _draw_progress(self, painter):
        """绘制当前进度"""
        ...

    def _draw_tasks(self, painter):
        """绘制任务块"""
        ...
```

**第 2 周: 提取任务管理逻辑**
```python
# gaiya/ui/progress_bar/task_manager.py
class TaskManager(QObject):
    """任务数据管理器"""

    tasks_changed = Signal(list)  # 任务数据变化信号

    def __init__(self):
        super().__init__()
        self.tasks = []
        self.start_minutes = 0
        self.end_minutes = 0

    def load_tasks(self, file_path: str) -> bool:
        """加载任务数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = data.get('tasks', [])
                self._calculate_time_range()
                self.tasks_changed.emit(self.tasks)
                return True
        except Exception as e:
            logger.error(f"加载任务失败: {e}")
            return False

    def save_tasks(self, file_path: str) -> bool:
        """保存任务数据"""
        ...

    def get_current_task(self) -> Optional[dict]:
        """获取当前任务"""
        ...
```

**第 3 周: 提取编辑模式逻辑**
```python
# gaiya/ui/progress_bar/edit_mode_controller.py
class EditModeController(QObject):
    """编辑模式控制器"""

    task_updated = Signal(int, dict)  # (任务索引, 新数据)

    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager
        self.dragging = False
        self.drag_task_index = -1
        self.drag_edge = None  # 'left' or 'right'

    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        """处理鼠标按下 (开始拖拽)"""
        ...

    def handle_mouse_move(self, event: QMouseEvent):
        """处理鼠标移动 (拖拽中)"""
        ...

    def handle_mouse_release(self, event: QMouseEvent):
        """处理鼠标释放 (结束拖拽)"""
        ...
```

**第 4 周: 集成测试**
```python
# tests/unit/test_progress_bar_widget.py
def test_progress_bar_rendering():
    """测试进度条渲染"""
    widget = ProgressBarWidget()
    widget.current_percentage = 0.5
    widget.theme_colors = {"background": "#FFFFFF"}

    # 触发绘制
    widget.update()

    # 验证渲染结果 (使用 QTest 截图对比)
    ...
```

**预期效果**:
- ✅ 单文件行数 < 500 行
- ✅ 圈复杂度降低 50%
- ✅ 单元测试覆盖率 > 90%

---

#### 2. config_gui.py 拆分 (2500 行 → 7 个文件)

**目标结构**:
```
gaiya/ui/config/
├── __init__.py
├── config_window.py            # 主窗口框架 (200行)
├── basic_settings_tab.py       # 基础设置标签页 (400行)
├── task_editor_tab.py          # 任务编辑标签页 (500行)
├── ai_assistant_tab.py         # AI助手标签页 (400行)
├── theme_store_tab.py          # 主题商店标签页 (500行)
├── account_tab.py              # 账户管理标签页 (300行)
└── advanced_settings_tab.py    # 高级设置标签页 (300行)
```

**实施步骤**: 每周拆分 2 个标签页 (共 3-4 周完成)

---

#### 3. statistics_gui.py 拆分 (3000 行 → 8 个文件)

**目标结构**:
```
gaiya/ui/statistics/
├── __init__.py
├── statistics_window.py        # 主窗口框架 (200行)
├── overview_tab.py             # 概览标签页 (400行)
├── weekly_stats_tab.py         # 周统计标签页 (400行)
├── monthly_stats_tab.py        # 月统计标签页 (400行)
├── achievement_tab.py          # 成就系统标签页 (500行)
├── goal_manager_tab.py         # 目标管理标签页 (400行)
├── ai_inference_tab.py         # AI推理任务标签页 (400行)
└── time_replay_tab.py          # 时间回放标签页 (400行)
```

**实施步骤**: 每周拆分 2 个标签页 (共 4 周完成)

---

**总耗时**: 约 **4 周** (1 个月)

**预期效果**:
- ✅ 代码可读性提升 80%
- ✅ 维护成本降低 60%
- ✅ 单元测试覆盖率 > 85%

---

### P1-2: 添加完整类型注解

**问题描述**:
- 部分旧代码缺少 type hints
- 影响 IDE 代码提示
- 难以发现类型错误

**改进方案**:

#### 工具选择: mypy (静态类型检查)
```bash
# 1. 安装 mypy
pip install mypy

# 2. 运行类型检查
mypy gaiya/ --strict
```

#### 分阶段实施

**第 1 周: 工具类模块** (gaiya/utils/)
```python
# 修改前
def calculate_time_range(self):
    self.start_minutes = time_to_minutes(self.tasks[0]['start_time'])
    self.end_minutes = time_to_minutes(self.tasks[-1]['end_time'])

# 修改后
def calculate_time_range(self) -> None:
    """计算任务时间范围"""
    if not self.tasks:
        return

    self.start_minutes: int = time_to_minutes(self.tasks[0]['start_time'])
    self.end_minutes: int = time_to_minutes(self.tasks[-1]['end_time'])
```

**第 2 周: 核心业务模块** (gaiya/core/)
```python
# 修改前
def get_current_task(self):
    for task in self.tasks:
        if self._is_current_task(task):
            return task
    return None

# 修改后
def get_current_task(self) -> Optional[Dict[str, Any]]:
    """获取当前任务"""
    for task in self.tasks:
        if self._is_current_task(task):
            return task
    return None
```

**第 3 周: UI 模块** (gaiya/ui/)

**第 4 周: 数据模块** (gaiya/data/)

**实施工具**:
```bash
# 1. 自动添加类型注解 (使用 MonkeyType)
pip install MonkeyType

# 2. 运行程序收集类型信息
monkeytype run main.py

# 3. 生成类型注解
monkeytype apply gaiya.core.task_manager

# 4. 验证类型正确性
mypy gaiya/core/task_manager.py
```

**预期效果**:
- ✅ 类型注解覆盖率 > 90%
- ✅ mypy 检查通过
- ✅ IDE 代码提示完善

---

### P1-3: macOS 支持

**问题描述**:
- 当前仅支持 Windows
- 限制用户规模 (Mac 用户占比 ~30%)

**技术挑战**:
1. ⚠️ 窗口透明度设置 (Windows 使用 `SetWindowLong`, macOS 需要不同 API)
2. ⚠️ 系统托盘图标 (macOS 使用 `.png`, Windows 使用 `.ico`)
3. ⚠️ 开机自启动 (macOS 使用 LaunchAgent)
4. ⚠️ 打包工具 (macOS 使用 PyInstaller + .app bundle)

**解决方案**:

#### 1. 跨平台窗口工具封装
```python
# gaiya/utils/window_utils.py (已存在,需完善)
import platform
from PySide6.QtCore import Qt

def set_window_transparent(window):
    """设置窗口透明 (跨平台)"""
    if platform.system() == 'Windows':
        from ctypes import windll, c_int, byref
        hwnd = int(window.winId())
        # Windows API 调用
        windll.user32.SetWindowLongW(hwnd, -20, 0x00080000)
        windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x00000002)

    elif platform.system() == 'Darwin':  # macOS
        # macOS 原生 API 调用
        window.setAttribute(Qt.WA_TranslucentBackground)
        window.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

def set_click_through(window, enabled: bool):
    """设置鼠标穿透 (跨平台)"""
    if platform.system() == 'Windows':
        from ctypes import windll
        hwnd = int(window.winId())
        if enabled:
            windll.user32.SetWindowLongW(hwnd, -20, 0x00080020)
        else:
            windll.user32.SetWindowLongW(hwnd, -20, 0x00080000)

    elif platform.system() == 'Darwin':
        # macOS 使用 Qt 属性
        if enabled:
            window.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            window.setAttribute(Qt.WA_TransparentForMouseEvents, False)
```

#### 2. 开机自启动 (macOS)
```python
# autostart_manager.py 扩展
class AutoStartManager:
    def __init__(self):
        self.platform = platform.system()

    def enable_autostart_macos(self):
        """macOS 开机自启动 (使用 LaunchAgent)"""
        plist_path = os.path.expanduser(
            '~/Library/LaunchAgents/com.gaiya.plist'
        )

        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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

        # 加载 LaunchAgent
        os.system(f'launchctl load {plist_path}')
```

#### 3. macOS 打包配置
```bash
# 1. 安装依赖
pip install pyinstaller

# 2. 创建 macOS 打包配置
# GaiYa-macOS.spec
# -*- mode: python ; coding: utf-8 -*-

app = BUNDLE(
    exe,
    name='GaiYa.app',
    icon='assets/icon.icns',  # macOS 图标格式
    bundle_identifier='com.gaiya.app',
    info_plist={
        'CFBundleName': 'GaiYa',
        'CFBundleDisplayName': 'GaiYa 每日进度条',
        'CFBundleVersion': '1.6.13',
        'NSHighResolutionCapable': 'True',
    },
)

# 3. 打包命令
pyinstaller GaiYa-macOS.spec
```

#### 4. 测试环境搭建
```bash
# macOS 虚拟机 (使用 VMware/Parallels)
# 或租用 MacStadium 云 Mac
# 或使用 GitHub Actions macOS runner
```

**实施步骤**:
1. **第 1 周**: 完善跨平台工具类
2. **第 2 周**: macOS 打包测试
3. **第 3 周**: 功能适配 (托盘/自启动)
4. **第 4 周**: 测试验证 + 发布

**预期效果**:
- ✅ 支持 macOS 10.15+
- ✅ 功能与 Windows 版本一致
- ✅ 用户规模扩展 **50%** ✅

---

## 🟠 P2 级任务 (中优先级 - 2-3 个月完成)

### P2-1: UI 自动化测试

**问题描述**:
- 当前仅有单元测试
- UI 功能缺少自动化测试
- 回归测试依赖手工操作

**改进方案**:

#### 工具选择: pytest-qt
```bash
# 1. 安装 pytest-qt
pip install pytest-qt

# 2. 编写 UI 测试用例
# tests/ui/test_main_window.py
import pytest
from PySide6.QtCore import Qt
from main import TimeProgressBar

def test_progress_bar_visible(qtbot):
    """测试进度条可见性"""
    window = TimeProgressBar()
    qtbot.addWidget(window)

    # 显示窗口
    window.show()

    # 验证窗口可见
    assert window.isVisible()

    # 验证进度条宽度
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

def test_edit_mode_drag(qtbot):
    """测试编辑模式拖拽"""
    window = TimeProgressBar()
    qtbot.addWidget(window)
    window.edit_mode = True
    window.show()

    # 模拟拖拽任务边缘
    qtbot.mousePress(window, Qt.LeftButton, pos=QPoint(100, 5))
    qtbot.mouseMove(window, pos=QPoint(150, 5))
    qtbot.mouseRelease(window, Qt.LeftButton)

    # 验证任务时长已修改
    assert window.temp_tasks is not None
```

**测试覆盖目标**:
- [ ] 主窗口显示/隐藏
- [ ] 进度条渲染
- [ ] 任务悬停
- [ ] 编辑模式拖拽
- [ ] 系统托盘菜单
- [ ] 配置界面交互
- [ ] 统计报告展示

**实施计划**: 每周增加 10 个测试用例,共 8 周

**预期效果**:
- ✅ UI 测试覆盖率 > 50%
- ✅ 自动化回归测试
- ✅ 减少手工测试时间 70%

---

### P2-2: 性能监控与优化

**问题描述**:
- 缺少性能监控指标
- 无法及时发现性能退化

**改进方案**:

#### 1. 集成应用性能监控 (APM)
```python
# gaiya/utils/performance_monitor.py
import time
from functools import wraps
from typing import Callable
import logging

logger = logging.getLogger("gaiya.performance")

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {}

    def measure(self, name: str):
        """装饰器: 测量函数执行时间"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time

                # 记录性能指标
                self.metrics[name] = elapsed

                # 慢查询告警 (超过 100ms)
                if elapsed > 0.1:
                    logger.warning(
                        f"性能告警: {name} 耗时 {elapsed:.2f}s"
                    )

                return result
            return wrapper
        return decorator

    def get_metrics(self) -> dict:
        """获取性能指标"""
        return self.metrics

# 使用示例
monitor = PerformanceMonitor()

@monitor.measure("load_tasks")
def load_tasks(self, file_path: str):
    """加载任务数据"""
    ...
```

#### 2. 关键路径性能优化
```python
# 优化前: 每秒刷新进度条 (可能阻塞 UI)
def update_progress(self):
    # 计算当前进度 (耗时操作)
    self.current_time_percentage = self.calculate_current_percentage()
    # 立即重绘 (阻塞 UI 线程)
    self.update()

# 优化后: 使用节流 (throttle)
from gaiya.utils.throttle import Throttle

class TimeProgressBar(QWidget):
    def __init__(self):
        ...
        # 节流: 最多每 100ms 刷新一次
        self.throttled_update = Throttle(self.update, delay_ms=100)

    def update_progress(self):
        self.current_time_percentage = self.calculate_current_percentage()
        # 使用节流更新 (避免过度刷新)
        self.throttled_update()
```

#### 3. 内存泄漏检测
```python
# tests/performance/test_memory_leak.py
import tracemalloc
import gc

def test_no_memory_leak():
    """测试长时间运行无内存泄漏"""
    tracemalloc.start()

    # 模拟运行 1 小时
    window = TimeProgressBar()
    for _ in range(3600):  # 3600 秒
        window.update_progress()
        QApplication.processEvents()

    # 获取内存快照
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 验证内存增长 < 10 MB
    assert (peak - current) / 1024 / 1024 < 10  # MB
```

**实施计划**: 2 个月 (每周优化 1 个关键路径)

**预期效果**:
- ✅ 进度条刷新性能提升 20%
- ✅ 内存占用减少 15%
- ✅ 无内存泄漏

---

### P2-3: 插件系统 (可扩展性)

**问题描述**:
- 功能扩展需要修改核心代码
- 第三方开发者无法贡献插件

**设计目标**:
- 用户可安装/卸载插件
- 插件可访问核心 API
- 插件沙箱隔离 (安全性)

**架构设计**:
```
gaiya/plugins/
├── __init__.py
├── plugin_manager.py           # 插件管理器
├── plugin_api.py               # 插件 API 接口
├── plugin_loader.py            # 插件加载器
└── marketplace/                # 插件市场 (可选)
```

**示例插件**:
```python
# ~/.gaiya/plugins/weather_widget/plugin.py
from gaiya.plugins import Plugin, PluginAPI

class WeatherWidget(Plugin):
    """天气插件 (在进度条上显示天气)"""

    name = "天气小部件"
    version = "1.0.0"
    author = "张三"

    def on_load(self, api: PluginAPI):
        """插件加载时调用"""
        # 注册进度条绘制回调
        api.register_paint_callback(self.draw_weather)

    def draw_weather(self, painter, rect):
        """在进度条上绘制天气"""
        weather = self.fetch_weather()  # 获取天气数据
        painter.drawText(rect.topRight(), f"🌤️ {weather}")

    def fetch_weather(self) -> str:
        """获取天气数据 (调用第三方 API)"""
        response = requests.get("https://api.weather.com/...")
        return response.json()["weather"]
```

**实施计划**: 3 个月

**预期效果**:
- ✅ 支持第三方插件开发
- ✅ 插件市场 (20+ 插件)
- ✅ 社区活跃度提升

---

## 🟡 P3 级任务 (低优先级 - 3-6 个月完成)

### P3-1: 移动端应用 (React Native)

**技术选型**:
- React Native (跨平台)
- Expo (开发框架)
- React Navigation (路由)

**功能范围**:
- [ ] 查看今日任务进度
- [ ] 完成任务打卡
- [ ] 查看统计报告
- [ ] 成就系统
- [ ] 推送通知 (任务提醒)

**实施计划**: 6 个月
- 第 1-2 月: 基础框架 + UI 设计
- 第 3-4 月: 功能开发
- 第 5 月: 测试 + 优化
- 第 6 月: 上架 App Store / Google Play

**预期效果**:
- ✅ iOS / Android 双平台
- ✅ 用户规模扩展 100%
- ✅ 使用场景扩展 (移动办公)

---

### P3-2: 团队协作功能

**功能设计**:
- [ ] 创建团队工作区
- [ ] 邀请成员加入
- [ ] 共享任务模板
- [ ] 团队统计报告
- [ ] 排行榜 (游戏化)

**技术架构**:
```
后端:
- FastAPI (Python)
- PostgreSQL (数据库)
- Redis (缓存)
- WebSocket (实时推送)

前端:
- 沿用现有 PySide6
- 新增团队管理界面
```

**实施计划**: 4 个月

**预期效果**:
- ✅ 进入企业市场
- ✅ 团队版定价: ¥99/用户/月
- ✅ 年收入增长 3-5 倍

---

### P3-3: API 开放平台

**设计目标**:
- 第三方应用可调用 GaiYa API
- 支持 OAuth 2.0 认证
- API 按调用次数计费

**API 端点示例**:
```
GET /api/v1/tasks                 # 获取任务列表
POST /api/v1/tasks                # 创建任务
PUT /api/v1/tasks/{id}            # 更新任务
GET /api/v1/statistics/daily      # 获取每日统计
POST /api/v1/ai/plan-tasks        # AI 任务规划
```

**实施计划**: 3 个月

**预期效果**:
- ✅ 第三方集成 (Notion, Trello, 飞书)
- ✅ API 收入: ¥0.01/调用
- ✅ 生态系统建设

---

## 📅 总体时间表

### 第 1 个月 (2025-12)
- 🔥 P0-1: 减少打包体积 (本周完成)
- 🔥 P0-2: 修复会话管理 (本周完成)
- 🔥 P0-3: 优化启动速度 (本周完成)
- 🔴 P1-1: 开始代码重构 (main.py 拆分)

### 第 2 个月 (2026-01)
- 🔴 P1-1: 继续代码重构 (config_gui.py 拆分)
- 🔴 P1-2: 添加类型注解 (工具类 + 核心模块)
- 🔴 P1-3: macOS 支持开发

### 第 3 个月 (2026-02)
- 🔴 P1-1: 完成代码重构 (statistics_gui.py 拆分)
- 🔴 P1-2: 完成类型注解 (UI + 数据模块)
- 🟠 P2-1: 开始 UI 自动化测试

### 第 4 个月 (2026-03)
- 🟠 P2-1: 继续 UI 自动化测试
- 🟠 P2-2: 性能监控与优化
- 🟠 P2-3: 插件系统设计

### 第 5-6 个月 (2026-04 至 2026-05)
- 🟠 P2-3: 插件系统开发
- 🟡 P3-1: 移动端应用启动
- 🟡 P3-2: 团队协作功能调研

---

## 📊 资源分配建议

### 人员配置
| 角色 | 人数 | 职责 |
|------|------|------|
| 前端开发 | 1-2 | UI 重构 + 移动端 |
| 后端开发 | 1 | API 优化 + 团队协作 |
| 测试工程师 | 1 | UI 自动化测试 + 性能测试 |
| 产品经理 | 1 | 需求管理 + 用户反馈 |

### 预算估算 (6 个月)
| 项目 | 金额 (CNY) |
|------|-----------|
| 人力成本 | ¥200,000 |
| 云服务 (Vercel Pro) | ¥2,000 |
| 测试设备 (Mac) | ¥15,000 |
| 移动端开发者账号 | ¥1,500 |
| 总计 | **¥218,500** |

---

## 🎯 成功指标 (KPI)

### 技术指标
- [ ] 打包体积 < 50 MB ✅
- [ ] 启动时间 < 1.5s ✅
- [ ] 测试覆盖率 > 85% ✅
- [ ] 单文件行数 < 500 行 ✅
- [ ] macOS 版本发布 ✅

### 用户指标
- [ ] 下载转化率提升 30%
- [ ] 用户留存率提升 20%
- [ ] 日活跃用户增长 50%
- [ ] App Store 评分 > 4.5 ⭐

### 商业指标
- [ ] 付费用户增长 100%
- [ ] 月收入增长 3 倍
- [ ] 企业客户获取 > 10 家

---

## 📝 总结

这份改进计划涵盖了从**紧急修复到长期愿景**的完整路径:

1. **P0 任务** (本周完成): 解决用户体验最痛点 (体积/启动/安全)
2. **P1 任务** (1 个月): 提升代码质量和跨平台能力
3. **P2 任务** (2-3 个月): 增强测试和性能,支持扩展
4. **P3 任务** (3-6 个月): 移动端和团队协作,生态建设

**核心原则**:
- ✅ 小步快跑: 每周可见进展
- ✅ 用户优先: 优先解决影响体验的问题
- ✅ 质量保障: 每个改进都有测试验证
- ✅ 商业闭环: 技术改进支撑商业增长

祝 GaiYa 产品越来越好! 🚀
