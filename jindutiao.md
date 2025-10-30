### 📅 项目：PyDayBar (桌面日历进度条)

**项目目标：** 创建一个常驻桌面的、可点击穿透的进度条，用于可视化显示全天的任务安排和当前时间进度。

**技术栈：**
* **语言：** Python 3.8+
* **GUI库：** PySide6 (Qt 6.x)
* **数据格式：** JSON (用于任务和配置)
* **可选依赖：** darkdetect (系统主题检测)

**核心特性：**
* ✅ 透明置顶窗口，不干扰其他应用
* ✅ 点击穿透，完全不影响桌面操作
* ✅ 实时显示时间进度和任务安排
* ✅ 支持热重载配置文件
* ✅ 系统托盘集成
* ✅ 低资源占用

---

### 阶段一：环境搭建与核心窗口 (MVP 基础)

**目标：** 创建一个可以运行的、透明的、置顶的、可点击穿透的空白窗口。

* [ ] **项目结构：**
    ```
    PyDayBar/
    ├── venv/              # 虚拟环境
    ├── main.py            # 主程序入口
    ├── config.json        # 配置文件（阶段四创建）
    ├── tasks.json         # 任务数据（阶段二创建）
    ├── resources/         # 资源文件夹（可选）
    │   └── icon.ico       # 托盘图标
    └── requirements.txt   # 依赖列表
    ```
    * 创建项目文件夹: `mkdir PyDayBar && cd PyDayBar`
    * 创建虚拟环境: `python -m venv venv`
    * 激活虚拟环境:
        * Windows: `venv\Scripts\activate`
        * Linux/Mac: `source venv/bin/activate`

* [ ] **安装依赖：**
    * 创建 `requirements.txt`:
    ```txt
    PySide6>=6.5.0
    ```
    * 安装: `pip install -r requirements.txt`

* [ ] **主程序 (`main.py`) - 基础框架：**
    ```python
    import sys
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtCore import Qt

    class TimeProgressBar(QWidget):
        def __init__(self):
            super().__init__()
            self.init_ui()

        def init_ui(self):
            # 窗口属性将在下一步设置
            self.setWindowTitle('PyDayBar')

    if __name__ == '__main__':
        app = QApplication(sys.argv)
        window = TimeProgressBar()
        window.show()
        sys.exit(app.exec())
    ```
* [ ] **窗口核心属性 (Window Flags) - 完整代码：**
    ```python
    def init_ui(self):
        # 窗口标志组合
        flags = (
            Qt.FramelessWindowHint |      # 无边框
            Qt.WindowStaysOnTopHint |     # 始终置顶
            Qt.Tool |                     # 不显示在任务栏
            Qt.WindowTransparentForInput  # 点击穿透
        )
        self.setWindowFlags(flags)

        # 设置背景透明（关键）
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置窗口布局
        self.setup_geometry()
    ```

* [ ] **窗口布局与定位：**
    ```python
    def setup_geometry(self):
        # 获取主屏幕信息
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        # 定义进度条尺寸
        BAR_HEIGHT = 20
        bar_width = screen_geometry.width()

        # 定位到屏幕底部（或顶部）
        position = 'bottom'  # 可改为 'top'
        if position == 'bottom':
            y_pos = screen_geometry.height() - BAR_HEIGHT
        else:
            y_pos = 0

        # 设置窗口几何
        self.setGeometry(0, y_pos, bar_width, BAR_HEIGHT)
    ```

* [ ] **多显示器支持（可选增强）：**
    * 如需在特定显示器上显示：
    ```python
    def setup_geometry(self):
        # 获取所有屏幕
        screens = QApplication.screens()
        # 选择主屏幕或指定索引
        target_screen = screens[0]  # 或从配置读取
        screen_geometry = target_screen.geometry()
        # ... 后续代码同上
    ```

** milestone (阶段一成果)：** 运行 `main.py` 后，屏幕底部 (或顶部) 会出现一个几乎看不见的空白区域，它置顶显示，但不会阻碍你点击它下面的任何东西。

---

### 阶段二：静态内容绘制 (绘制日程)

**目标：** 在空白窗口上绘制出背景条和所有已安排的任务色块。

* [ ] **数据结构 (`tasks.json`) - 示例文件：**
    ```json
    [
        {
            "start": "09:00",
            "end": "12:00",
            "task": "上午工作",
            "color": "#4CAF50"
        },
        {
            "start": "13:00",
            "end": "14:00",
            "task": "午休",
            "color": "#FFC107"
        },
        {
            "start": "14:00",
            "end": "18:00",
            "task": "下午工作",
            "color": "#2196F3"
        },
        {
            "start": "19:00",
            "end": "20:00",
            "task": "健身",
            "color": "#FF5722"
        }
    ]
    ```

* [ ] **数据加载与验证：**
    ```python
    import json
    from pathlib import Path

    def load_tasks(self):
        """加载并验证任务数据"""
        tasks_file = Path(__file__).parent / 'tasks.json'

        # 如果文件不存在，创建默认任务
        if not tasks_file.exists():
            default_tasks = [
                {"start": "09:00", "end": "12:00", "task": "上午", "color": "#4CAF50"}
            ]
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(default_tasks, f, indent=4, ensure_ascii=False)
            return default_tasks

        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            # 验证数据格式
            validated_tasks = []
            for task in tasks:
                if all(key in task for key in ['start', 'end', 'task', 'color']):
                    validated_tasks.append(task)
                else:
                    print(f"警告: 跳过无效任务 {task}")

            return validated_tasks
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            return []
        except Exception as e:
            print(f"加载任务失败: {e}")
            return []
    ```

* [ ] **时间转换辅助函数：**
    ```python
    def time_to_percentage(self, time_str):
        """将 HH:MM 格式转换为 0.0-1.0 之间的百分比"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            total_seconds = hours * 3600 + minutes * 60
            return total_seconds / 86400  # 86400 = 24 * 60 * 60
        except (ValueError, AttributeError):
            print(f"警告: 无效的时间格式 '{time_str}'")
            return 0.0

    def percentage_to_time(self, percentage):
        """将百分比转换回 HH:MM 格式（用于调试）"""
        total_seconds = int(percentage * 86400)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    ```

* [ ] **在 `__init__` 中初始化任务数据：**
    ```python
    def __init__(self):
        super().__init__()
        self.tasks = self.load_tasks()  # 加载任务
        self.init_ui()
    ```
* [ ] **绘制 (`paintEvent`) - 完整实现：**
    ```python
    from PySide6.QtGui import QPainter, QColor, QPen
    from PySide6.QtCore import QRectF

    def paintEvent(self, event):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿

        width = self.width()
        height = self.height()

        # 1. 绘制半透明背景条
        bg_color = QColor(80, 80, 80, 180)  # RGBA
        painter.fillRect(0, 0, width, height, bg_color)

        # 2. 绘制任务色块
        for task in self.tasks:
            start_pct = self.time_to_percentage(task['start'])
            end_pct = self.time_to_percentage(task['end'])

            # 计算任务块的位置和宽度
            x = start_pct * width
            task_width = (end_pct - start_pct) * width

            # 解析颜色
            color = QColor(task['color'])

            # 绘制任务块（留出1px边距以区分相邻任务）
            rect = QRectF(x, 1, task_width, height - 2)
            painter.fillRect(rect, color)

        painter.end()
    ```

* [ ] **处理任务重叠问题（可选增强）：**
    * 如果任务时间重叠，可以采用以下策略：
    ```python
    def paint_overlapping_tasks(self, painter, width, height):
        """处理重叠任务的绘制"""
        # 按开始时间排序
        sorted_tasks = sorted(self.tasks, key=lambda t: t['start'])

        for i, task in enumerate(sorted_tasks):
            start_pct = self.time_to_percentage(task['start'])
            end_pct = self.time_to_percentage(task['end'])

            x = start_pct * width
            task_width = (end_pct - start_pct) * width

            # 检测重叠：如果与前一个任务重叠，降低高度显示
            y_offset = 0
            task_height = height - 2

            if i > 0:
                prev_end = self.time_to_percentage(sorted_tasks[i-1]['end'])
                if start_pct < prev_end:  # 检测重叠
                    y_offset = task_height // 2
                    task_height = task_height // 2

            color = QColor(task['color'])
            rect = QRectF(x, 1 + y_offset, task_width, task_height)
            painter.fillRect(rect, color)
    ```

** milestone (阶段二成果)：** 运行程序，进度条会显示半透明背景，以及 `tasks.json` 中定义的所有彩色任务块。

---

### 阶段三：动态时间标记 (让进度条“动”起来)

**目标：** 添加一个随真实时间移动的垂直线标记。

* [ ] **定时器设置 - 在 `__init__` 中添加：**
    ```python
    from PySide6.QtCore import QTimer, QTime

    def __init__(self):
        super().__init__()
        self.tasks = self.load_tasks()
        self.current_time_percentage = 0.0  # 初始化时间百分比
        self.init_ui()
        self.init_timer()  # 初始化定时器

    def init_timer(self):
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_marker)
        self.timer.start(1000)  # 每秒更新一次

        # 立即更新一次，避免启动时等待1秒
        self.update_time_marker()
    ```

* [ ] **时间更新槽函数：**
    ```python
    def update_time_marker(self):
        """更新时间标记的位置"""
        current_time = QTime.currentTime()

        # 计算当前时间的秒数
        total_seconds = (
            current_time.hour() * 3600 +
            current_time.minute() * 60 +
            current_time.second()
        )

        # 转换为百分比
        self.current_time_percentage = total_seconds / 86400

        # 触发重绘
        self.update()
    ```

* [ ] **修改 `paintEvent` - 添加时间标记绘制：**
    ```python
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # 1. 绘制背景条
        bg_color = QColor(80, 80, 80, 180)
        painter.fillRect(0, 0, width, height, bg_color)

        # 2. 绘制任务色块
        for task in self.tasks:
            start_pct = self.time_to_percentage(task['start'])
            end_pct = self.time_to_percentage(task['end'])
            x = start_pct * width
            task_width = (end_pct - start_pct) * width
            color = QColor(task['color'])
            rect = QRectF(x, 1, task_width, height - 2)
            painter.fillRect(rect, color)

        # 3. 绘制时间标记线（最上层）
        marker_x = self.current_time_percentage * width

        # 绘制阴影效果（可选，增强可见性）
        shadow_pen = QPen(QColor(0, 0, 0, 100))
        shadow_pen.setWidth(3)
        painter.setPen(shadow_pen)
        painter.drawLine(int(marker_x + 1), 0, int(marker_x + 1), height)

        # 绘制主线
        marker_pen = QPen(QColor(255, 0, 0, 220))  # 红色，半透明
        marker_pen.setWidth(2)
        painter.setPen(marker_pen)
        painter.drawLine(int(marker_x), 0, int(marker_x), height)

        painter.end()
    ```

* [ ] **性能优化（可选）：**
    * 减少不必要的重绘：
    ```python
    def update_time_marker(self):
        """优化版本：仅在百分比变化时重绘"""
        current_time = QTime.currentTime()
        total_seconds = (
            current_time.hour() * 3600 +
            current_time.minute() * 60 +
            current_time.second()
        )

        new_percentage = total_seconds / 86400

        # 仅当百分比实际变化时才重绘（避免浮点误差）
        if abs(new_percentage - self.current_time_percentage) > 0.00001:
            self.current_time_percentage = new_percentage
            self.update()
    ```

** milestone (阶段三成果)：** 进度条上出现一条红线，并且该红线随着时钟时间从左到右平滑移动。

---

### 阶段四：功能增强 (交互与配置)

**目标：** 增加配置灵活性和基本的用户交互。

* [ ] **配置文件 (`config.json`) - 示例结构：**
    ```json
    {
        "bar_height": 20,
        "position": "bottom",
        "background_color": "#505050",
        "background_opacity": 180,
        "marker_color": "#FF0000",
        "marker_width": 2,
        "screen_index": 0,
        "update_interval": 1000,
        "enable_shadow": true,
        "corner_radius": 0
    }
    ```

* [ ] **配置加载函数：**
    ```python
    def load_config(self):
        """加载配置文件"""
        config_file = Path(__file__).parent / 'config.json'

        # 默认配置
        default_config = {
            "bar_height": 20,
            "position": "bottom",
            "background_color": "#505050",
            "background_opacity": 180,
            "marker_color": "#FF0000",
            "marker_width": 2,
            "screen_index": 0,
            "update_interval": 1000,
            "enable_shadow": True,
            "corner_radius": 0
        }

        if not config_file.exists():
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            return default_config

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 合并默认配置（防止缺失键）
            return {**default_config, **config}
        except Exception as e:
            print(f"加载配置失败: {e}")
            return default_config

    def __init__(self):
        super().__init__()
        self.config = self.load_config()  # 加载配置
        self.tasks = self.load_tasks()
        self.current_time_percentage = 0.0
        self.init_ui()
        self.init_timer()
        self.init_tray()  # 初始化托盘
    ```

* [ ] **系统托盘图标实现：**
    ```python
    from PySide6.QtWidgets import QSystemTrayIcon, QMenu
    from PySide6.QtGui import QIcon, QAction

    def init_tray(self):
        """初始化系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)

        # 设置图标（使用内置图标或自定义.ico文件）
        # 方案1：使用Qt内置图标
        icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon
        )
        # 方案2：使用自定义图标（推荐）
        # icon = QIcon('resources/icon.ico')

        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip('PyDayBar - 桌面日历进度条')

        # 创建右键菜单
        tray_menu = QMenu()

        # 重载配置动作
        reload_action = QAction('重载配置', self)
        reload_action.triggered.connect(self.reload_all)
        tray_menu.addAction(reload_action)

        # 切换位置动作
        toggle_position_action = QAction('切换位置 (顶部/底部)', self)
        toggle_position_action.triggered.connect(self.toggle_position)
        tray_menu.addAction(toggle_position_action)

        tray_menu.addSeparator()

        # 退出动作
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def reload_all(self):
        """重载配置和任务"""
        self.config = self.load_config()
        self.tasks = self.load_tasks()
        self.setup_geometry()  # 重新设置窗口位置
        self.update()

    def toggle_position(self):
        """切换进度条位置"""
        self.config['position'] = (
            'top' if self.config['position'] == 'bottom' else 'bottom'
        )
        # 保存到配置文件
        config_file = Path(__file__).parent / 'config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        self.setup_geometry()
    ```

* [ ] **使用配置更新 `setup_geometry`：**
    ```python
    def setup_geometry(self):
        """根据配置设置窗口位置"""
        screens = QApplication.screens()
        screen_index = min(self.config['screen_index'], len(screens) - 1)
        screen_geometry = screens[screen_index].geometry()

        bar_height = self.config['bar_height']
        bar_width = screen_geometry.width()

        if self.config['position'] == 'bottom':
            y_pos = screen_geometry.height() - bar_height
        else:
            y_pos = 0

        self.setGeometry(
            screen_geometry.x(),  # 多显示器支持
            y_pos,
            bar_width,
            bar_height
        )
    ```
* [ ] **(可选) 鼠标悬停提示 (Tooltip)：**
    * **注意：** 此功能与“点击穿透”(`WindowTransparentForInput`) **互斥**。你必须二选一。
    * *如果选择实现：*
        * [ ] 移除 `WindowTransparentForInput` 标志。
        * [ ] 重写 `mouseMoveEvent(event)`。
        * [ ] 检查 `event.pos().x()` 是否落在某个任务色块的 `QRectF` 内。
        * [ ] 如果是，使用 `QToolTip.showText()` 显示该任务的名称。

** milestone (阶段四成果)：** 程序可以通过托盘图标安全退出，并且外观（高度、位置）可以通过 `config.json` 轻松修改。

---

### 阶段五：健壮性 (Robustness)

**目标：** 让程序更稳定，易于维护。

* [ ] **动态重载 (Hot Reload) - 文件监视器：**
    ```python
    from PySide6.QtCore import QFileSystemWatcher

    def init_file_watcher(self):
        """初始化文件监视器"""
        self.file_watcher = QFileSystemWatcher(self)

        # 获取文件路径
        tasks_file = str(Path(__file__).parent / 'tasks.json')
        config_file = str(Path(__file__).parent / 'config.json')

        # 添加到监视列表
        self.file_watcher.addPath(tasks_file)
        self.file_watcher.addPath(config_file)

        # 连接信号
        self.file_watcher.fileChanged.connect(self.on_file_changed)

    def on_file_changed(self, path):
        """文件变化时的回调"""
        print(f"检测到文件变化: {path}")

        # 短暂延迟，确保文件写入完成
        QTimer.singleShot(100, self.reload_all)

    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.tasks = self.load_tasks()
        self.current_time_percentage = 0.0
        self.init_ui()
        self.init_timer()
        self.init_tray()
        self.init_file_watcher()  # 添加文件监视
    ```

* [ ] **增强错误处理 - 日志系统：**
    ```python
    import logging
    from datetime import datetime

    def setup_logging(self):
        """设置日志系统"""
        log_file = Path(__file__).parent / 'pydaybar.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_tasks(self):
        """加载任务（增强错误处理版本）"""
        tasks_file = Path(__file__).parent / 'tasks.json'

        if not tasks_file.exists():
            self.logger.info("tasks.json 不存在，创建默认任务")
            default_tasks = [
                {"start": "09:00", "end": "12:00", "task": "上午", "color": "#4CAF50"}
            ]
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(default_tasks, f, indent=4, ensure_ascii=False)
            return default_tasks

        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            validated_tasks = []
            for i, task in enumerate(tasks):
                if all(key in task for key in ['start', 'end', 'task', 'color']):
                    # 验证时间格式
                    if self.validate_time_format(task['start']) and \
                       self.validate_time_format(task['end']):
                        validated_tasks.append(task)
                    else:
                        self.logger.warning(f"任务 {i+1} 时间格式无效: {task}")
                else:
                    self.logger.warning(f"任务 {i+1} 缺少必要字段: {task}")

            self.logger.info(f"成功加载 {len(validated_tasks)} 个任务")
            return validated_tasks

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析错误: {e}")
            return []
        except Exception as e:
            self.logger.error(f"加载任务失败: {e}", exc_info=True)
            return []

    def validate_time_format(self, time_str):
        """验证时间格式 HH:MM"""
        import re
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        return bool(re.match(pattern, time_str))
    ```

* [ ] **代码重构 - 模块化绘制：**
    ```python
    def paintEvent(self, event):
        """主绘制事件（重构版）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # 模块化绘制
        self.draw_background(painter, width, height)
        self.draw_tasks(painter, width, height)
        self.draw_time_marker(painter, width, height)

        painter.end()

    def draw_background(self, painter, width, height):
        """绘制背景"""
        bg_color = QColor(self.config['background_color'])
        bg_color.setAlpha(self.config['background_opacity'])
        painter.fillRect(0, 0, width, height, bg_color)

    def draw_tasks(self, painter, width, height):
        """绘制任务块"""
        for task in self.tasks:
            start_pct = self.time_to_percentage(task['start'])
            end_pct = self.time_to_percentage(task['end'])

            x = start_pct * width
            task_width = (end_pct - start_pct) * width

            color = QColor(task['color'])
            rect = QRectF(x, 1, task_width, height - 2)

            # 可选圆角
            if self.config.get('corner_radius', 0) > 0:
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(
                    rect,
                    self.config['corner_radius'],
                    self.config['corner_radius']
                )
            else:
                painter.fillRect(rect, color)

    def draw_time_marker(self, painter, width, height):
        """绘制时间标记"""
        marker_x = self.current_time_percentage * width

        # 绘制阴影（可选）
        if self.config.get('enable_shadow', True):
            shadow_pen = QPen(QColor(0, 0, 0, 100))
            shadow_pen.setWidth(self.config['marker_width'] + 1)
            painter.setPen(shadow_pen)
            painter.drawLine(int(marker_x + 1), 0, int(marker_x + 1), height)

        # 绘制主线
        marker_color = QColor(self.config['marker_color'])
        marker_pen = QPen(marker_color)
        marker_pen.setWidth(self.config['marker_width'])
        painter.setPen(marker_pen)
        painter.drawLine(int(marker_x), 0, int(marker_x), height)
    ```

* [ ] **高DPI适配（Windows 10/11）：**
    ```python
    if __name__ == '__main__':
        # 启用高DPI支持
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        app = QApplication(sys.argv)
        window = TimeProgressBar()
        window.show()
        sys.exit(app.exec())
    ```

** milestone (阶段五成果)：** 你可以在不重启程序的情况下，直接修改 `tasks.json` 来更新你的日程，进度条会实时响应变化。

---

### 阶段六：打包与部署

**目标：** 将 `.py` 脚本打包成一个独立的可执行文件 (`.exe`)，并设置为开机自启动。

* [ ] **安装打包工具：**
    ```bash
    pip install pyinstaller
    ```

* [ ] **准备资源文件：**
    * 创建 `.ico` 图标文件（推荐使用在线工具如 icoconvert.com）
    * 确保 `main.py` 中的资源路径使用相对路径

* [ ] **修改代码以支持打包后的路径：**
    ```python
    import sys
    from pathlib import Path

    def get_resource_path(relative_path):
        """获取资源文件的绝对路径（支持打包后）"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe路径
            base_path = Path(sys.executable).parent
        else:
            # 开发环境路径
            base_path = Path(__file__).parent
        return base_path / relative_path

    # 在所有文件操作中使用此函数
    def load_tasks(self):
        tasks_file = get_resource_path('tasks.json')
        # ... 后续代码
    ```

* [ ] **创建打包配置文件 `build.spec`（推荐方式）：**
    ```python
    # -*- mode: python ; coding: utf-8 -*-

    block_cipher = None

    a = Analysis(
        ['main.py'],
        pathex=[],
        binaries=[],
        datas=[
            ('resources/icon.ico', 'resources'),  # 如果有资源文件
        ],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )

    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='PyDayBar',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # 隐藏控制台
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='resources/icon.ico'  # 设置图标
    )
    ```

* [ ] **打包命令：**
    ```bash
    # 方法1：使用命令行（快速）
    pyinstaller --noconsole --onefile --icon=resources/icon.ico --name=PyDayBar main.py

    # 方法2：使用spec文件（推荐，可定制）
    pyinstaller build.spec

    # 打包完成后，exe文件位于 dist/ 目录
    ```

* [ ] **测试打包后的程序：**
    ```bash
    cd dist
    PyDayBar.exe
    ```
    * 检查是否正常显示
    * 确认配置文件自动创建
    * 测试托盘菜单功能

* [ ] **设置开机自启动 (Windows)：**

    **方法1：手动添加（简单）**
    ```bash
    # 1. 按 Win + R，输入 shell:startup
    # 2. 将 PyDayBar.exe 的快捷方式复制到启动文件夹
    ```

    **方法2：通过注册表（程序化）**
    ```python
    import winreg
    import sys

    def add_to_startup():
        """添加到Windows启动项"""
        if not getattr(sys, 'frozen', False):
            print("仅在打包后的exe中可用")
            return

        exe_path = sys.executable
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "PyDayBar", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            print("已添加到开机启动")
        except Exception as e:
            print(f"添加启动项失败: {e}")

    def remove_from_startup():
        """从启动项移除"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, "PyDayBar")
            winreg.CloseKey(key)
            print("已从开机启动移除")
        except FileNotFoundError:
            print("启动项不存在")
        except Exception as e:
            print(f"移除启动项失败: {e}")

    # 在托盘菜单中添加相关选项
    ```

* [ ] **优化打包体积（可选）：**
    ```bash
    # 使用 UPX 压缩（已在 spec 文件中启用）
    # 下载 UPX: https://github.com/upx/upx/releases
    # 将 upx.exe 放到系统 PATH 中

    # 排除不需要的模块
    pyinstaller --exclude-module matplotlib --exclude-module numpy ...
    ```

* [ ] **创建安装脚本（进阶）：**
    * 可选使用 Inno Setup 或 NSIS 创建专业的安装程序
    * 自动创建快捷方式、设置启动项、卸载功能

** milestone (阶段六成果)：** 一个可以分发给朋友的 `.exe` 文件，双击即可运行，并可以设置开机自启。

---

## 📋 常见问题与解决方案 (FAQ)

### 问题1：进度条不显示或位置不正确
**可能原因：**
- 多显示器配置问题
- 屏幕缩放设置（高DPI）

**解决方案：**
```python
# 调试：打印屏幕信息
def debug_screen_info(self):
    screens = QApplication.screens()
    for i, screen in enumerate(screens):
        geometry = screen.geometry()
        print(f"屏幕 {i}: {geometry.width()}x{geometry.height()} @ ({geometry.x()}, {geometry.y()})")
        print(f"  DPI: {screen.logicalDotsPerInch()}")
        print(f"  缩放比例: {screen.devicePixelRatio()}")
```

### 问题2：点击穿透不工作
**可能原因：**
- 某些应用（如全屏游戏）会覆盖置顶窗口
- Windows 10/11 的游戏模式冲突

**解决方案：**
```python
# 尝试更强的置顶设置
from PySide6.QtCore import Qt

def force_stay_on_top(self):
    """强制保持置顶"""
    self.setWindowFlags(
        self.windowFlags() |
        Qt.WindowStaysOnTopHint |
        Qt.BypassWindowManagerHint  # 绕过窗口管理器
    )
    self.show()

# 或者使用定时器定期检查
def check_window_state(self):
    if not self.isActiveWindow():
        self.raise_()
        self.activateWindow()
```

### 问题3：程序占用CPU过高
**原因：**
- 每秒重绘导致

**优化方案：**
```python
# 1. 仅在需要时重绘
def update_time_marker(self):
    current_time = QTime.currentTime()
    # 仅在分钟改变时更新（而非每秒）
    if current_time.minute() != getattr(self, '_last_minute', -1):
        self._last_minute = current_time.minute()
        total_seconds = (
            current_time.hour() * 3600 +
            current_time.minute() * 60
        )
        self.current_time_percentage = total_seconds / 86400
        self.update()

# 2. 使用定时器减少更新频率
self.timer.start(60000)  # 改为每分钟更新一次
```

### 问题4：任务颜色显示不正确
**原因：**
- 颜色格式错误
- Alpha通道设置

**解决方案：**
```python
def parse_color(self, color_str):
    """安全解析颜色"""
    try:
        # 支持 #RRGGBB 和 #RRGGBBAA
        color = QColor(color_str)
        if not color.isValid():
            print(f"警告: 无效颜色 {color_str}，使用默认灰色")
            return QColor(128, 128, 128)
        return color
    except Exception as e:
        print(f"解析颜色失败: {e}")
        return QColor(128, 128, 128)
```

### 问题5：Windows Defender 误报病毒
**原因：**
- PyInstaller 打包的程序可能被误报

**解决方案：**
1. 添加代码签名证书（推荐但需付费）
2. 提交文件到 Microsoft 白名单
3. 打包时使用 `--debug=all` 查看详细信息
4. 使用虚拟环境减少依赖

### 问题6：配置文件修改后不生效
**检查：**
```python
# 确保文件监视器正常工作
def on_file_changed(self, path):
    print(f"文件变化: {path}")  # 添加日志

    # Windows 某些编辑器会先删除再创建文件
    # 需要重新添加到监视列表
    if not self.file_watcher.files():
        self.file_watcher.addPath(str(get_resource_path('tasks.json')))
        self.file_watcher.addPath(str(get_resource_path('config.json')))

    QTimer.singleShot(100, self.reload_all)
```

---

## 🚀 进阶功能建议

### 功能1：任务提醒通知
```python
def check_task_notifications(self):
    """检查是否有任务即将开始"""
    current_time = QTime.currentTime()
    current_str = current_time.toString("HH:mm")

    for task in self.tasks:
        # 提前5分钟提醒
        task_time = QTime.fromString(task['start'], "HH:mm")
        reminder_time = task_time.addSecs(-300)  # 5分钟 = 300秒

        if current_str == reminder_time.toString("HH:mm"):
            self.show_notification(f"即将开始: {task['task']}", task['start'])

def show_notification(self, title, message):
    """显示系统托盘通知"""
    self.tray_icon.showMessage(
        title,
        message,
        QSystemTrayIcon.Information,
        3000  # 显示3秒
    )
```

### 功能2：任务统计
```python
def calculate_task_stats(self):
    """计算任务统计信息"""
    total_minutes = 0
    task_categories = {}

    for task in self.tasks:
        start_pct = self.time_to_percentage(task['start'])
        end_pct = self.time_to_percentage(task['end'])
        duration_minutes = (end_pct - start_pct) * 24 * 60

        total_minutes += duration_minutes

        # 按任务名称分类统计
        task_name = task['task']
        task_categories[task_name] = task_categories.get(task_name, 0) + duration_minutes

    return {
        'total_hours': total_minutes / 60,
        'categories': task_categories,
        'utilization': (total_minutes / (24 * 60)) * 100  # 时间利用率
    }
```

### 功能3：双击编辑任务
```python
# 注意：需要移除 WindowTransparentForInput 标志

def mousePressEvent(self, event):
    """鼠标点击事件"""
    if event.button() == Qt.LeftButton:
        # 检测点击位置对应的任务
        click_x = event.pos().x()
        width = self.width()
        click_percentage = click_x / width

        for task in self.tasks:
            start_pct = self.time_to_percentage(task['start'])
            end_pct = self.time_to_percentage(task['end'])

            if start_pct <= click_percentage <= end_pct:
                self.edit_task_dialog(task)
                break

def edit_task_dialog(self, task):
    """打开任务编辑对话框"""
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton

    dialog = QDialog()
    dialog.setWindowTitle(f"编辑任务: {task['task']}")
    layout = QVBoxLayout()

    # 添加编辑控件
    name_edit = QLineEdit(task['task'])
    start_edit = QLineEdit(task['start'])
    end_edit = QLineEdit(task['end'])

    layout.addWidget(name_edit)
    layout.addWidget(start_edit)
    layout.addWidget(end_edit)

    # 保存按钮
    save_btn = QPushButton("保存")
    save_btn.clicked.connect(lambda: self.save_task_edit(task, name_edit.text(), start_edit.text(), end_edit.text(), dialog))
    layout.addWidget(save_btn)

    dialog.setLayout(layout)
    dialog.exec()

def save_task_edit(self, task, new_name, new_start, new_end, dialog):
    """保存任务编辑"""
    task['task'] = new_name
    task['start'] = new_start
    task['end'] = new_end

    # 保存到文件
    tasks_file = get_resource_path('tasks.json')
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(self.tasks, f, indent=4, ensure_ascii=False)

    self.update()
    dialog.close()
```

### 功能4：主题支持（深色/浅色）
```python
def detect_system_theme(self):
    """检测系统主题"""
    try:
        # Windows 10/11
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value == 1 else "dark"
    except:
        return "dark"  # 默认深色

def apply_theme(self, theme):
    """应用主题"""
    if theme == "dark":
        self.config['background_color'] = "#202020"
        self.config['marker_color'] = "#FF4444"
    else:
        self.config['background_color'] = "#E0E0E0"
        self.config['marker_color'] = "#CC0000"

    self.update()
```

### 功能5：导出日程为图片
```python
def export_to_image(self, filename):
    """导出当前进度条为图片"""
    from PySide6.QtGui import QPixmap

    pixmap = QPixmap(self.size())
    self.render(pixmap)
    pixmap.save(filename, "PNG")
    print(f"已导出到: {filename}")
```

### 功能6：周视图/月视图
```python
def load_weekly_tasks(self, date):
    """加载一周的任务"""
    # tasks.json 格式扩展：
    # {"date": "2024-01-15", "tasks": [...]}
    pass

def switch_to_week_view(self):
    """切换到周视图"""
    # 显示7天的任务分布
    pass
```

---

## 🔧 调试技巧

### 显示调试信息
```python
def paintEvent(self, event):
    painter = QPainter(self)
    # ... 正常绘制代码

    # 添加调试文本
    if self.config.get('debug_mode', False):
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(10, 15, f"Time: {self.percentage_to_time(self.current_time_percentage)}")
        painter.drawText(10, 30, f"Tasks: {len(self.tasks)}")
        painter.drawText(10, 45, f"FPS: {self.fps}")
```

### 性能监控
```python
import time

def paintEvent(self, event):
    start_time = time.perf_counter()

    # ... 绘制代码

    elapsed = (time.perf_counter() - start_time) * 1000
    if elapsed > 16:  # 超过16ms（60fps）
        print(f"警告: 绘制耗时 {elapsed:.2f}ms")
```

---

## 📝 开发建议

1. **版本控制：** 使用 Git 管理代码，建议添加 `.gitignore`：
   ```
   venv/
   __pycache__/
   *.pyc
   build/
   dist/
   *.spec
   *.log
   ```

2. **代码风格：** 遵循 PEP 8，使用 `black` 或 `autopep8` 格式化

3. **类型提示：** 添加类型注解提高代码可读性
   ```python
   def time_to_percentage(self, time_str: str) -> float:
       ...
   ```

4. **单元测试：** 为关键函数编写测试
   ```python
   import unittest

   class TestTimeConversion(unittest.TestCase):
       def test_time_to_percentage(self):
           bar = TimeProgressBar()
           self.assertAlmostEqual(bar.time_to_percentage("12:00"), 0.5)
   ```

5. **文档字符串：** 使用 docstring 记录函数用途

---