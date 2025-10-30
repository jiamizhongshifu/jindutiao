"""
PyDayBar - 桌面日历进度条
一个透明、置顶、可点击穿透的桌面时间进度条应用
"""

import sys
import json
import logging
import platform
from pathlib import Path
from datetime import datetime, date
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QToolTip
from PySide6.QtCore import Qt, QRectF, QTimer, QTime, QFileSystemWatcher, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QAction, QFont, QPixmap, QMovie

# Windows 特定导入
if platform.system() == 'Windows':
    import ctypes
    from ctypes import wintypes


class NotificationManager:
    """任务提醒通知管理器"""

    def __init__(self, config, tasks, tray_icon, logger):
        """初始化通知管理器

        Args:
            config: 配置字典
            tasks: 任务列表
            tray_icon: 系统托盘图标实例
            logger: 日志记录器
        """
        self.config = config
        self.tasks = tasks
        self.tray_icon = tray_icon
        self.logger = logger

        # 已发送通知记录 {任务名_类型_日期: True}
        self.sent_notifications = {}

        # 通知历史记录(最多保留10条)
        self.notification_history = []

        # 初始化定时器(每分钟检查一次)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_and_notify)

        # 如果通知已启用,启动定时器
        if self.is_enabled():
            self.check_timer.start(60000)  # 60秒检查一次
            self.logger.info("通知管理器已启动")

    def is_enabled(self):
        """检查通知功能是否启用"""
        return self.config.get('notification', {}).get('enabled', False)

    def reload_config(self, config, tasks):
        """重新加载配置和任务"""
        self.config = config
        self.tasks = tasks

        # 根据配置启动或停止定时器
        if self.is_enabled():
            if not self.check_timer.isActive():
                self.check_timer.start(60000)
                self.logger.info("通知管理器已启动")
        else:
            if self.check_timer.isActive():
                self.check_timer.stop()
                self.logger.info("通知管理器已停止")

    def is_in_quiet_hours(self, current_time):
        """检查当前是否在免打扰时段

        Args:
            current_time: QTime 对象

        Returns:
            bool: 如果在免打扰时段返回 True
        """
        quiet_config = self.config.get('notification', {}).get('quiet_hours', {})
        if not quiet_config.get('enabled', False):
            return False

        try:
            start_str = quiet_config.get('start', '22:00')
            end_str = quiet_config.get('end', '08:00')

            start_parts = start_str.split(':')
            end_parts = end_str.split(':')

            start_time = QTime(int(start_parts[0]), int(start_parts[1]))
            end_time = QTime(int(end_parts[0]), int(end_parts[1]))

            # 处理跨天的情况
            if end_time < start_time:
                # 例如: 22:00 - 08:00
                return current_time >= start_time or current_time <= end_time
            else:
                # 例如: 01:00 - 05:00
                return start_time <= current_time <= end_time

        except Exception as e:
            self.logger.error(f"免打扰时段配置错误: {e}")
            return False

    def check_and_notify(self):
        """检查并发送通知(每分钟调用一次)"""
        if not self.is_enabled():
            return

        current_time = QTime.currentTime()
        current_date = date.today().isoformat()

        # 检查是否在免打扰时段
        if self.is_in_quiet_hours(current_time):
            return

        # 清理昨天的通知记录
        self._clean_old_notifications(current_date)

        notification_config = self.config.get('notification', {})

        for task in self.tasks:
            task_name = task.get('task', '')
            start_str = task.get('start', '')
            end_str = task.get('end', '')

            try:
                start_parts = start_str.split(':')
                end_parts = end_str.split(':')

                start_time = QTime(int(start_parts[0]), int(start_parts[1]))

                # 处理 24:00 的情况
                if end_str == "24:00":
                    end_time = QTime(23, 59)
                else:
                    end_time = QTime(int(end_parts[0]), int(end_parts[1]))

                # 检查任务开始前的提醒
                before_start_minutes = notification_config.get('before_start_minutes', [])
                for minutes in before_start_minutes:
                    remind_time = start_time.addSecs(-minutes * 60)
                    if self._should_notify(current_time, remind_time):
                        notify_key = f"{task_name}_before_start_{minutes}_{current_date}"
                        if notify_key not in self.sent_notifications:
                            self._send_notification(
                                f"【提前{minutes}分钟】{task_name}",
                                f"将在 {start_str} 开始"
                            )
                            self.sent_notifications[notify_key] = True

                # 检查任务开始时的提醒
                if notification_config.get('on_start', False):
                    if self._should_notify(current_time, start_time):
                        notify_key = f"{task_name}_on_start_{current_date}"
                        if notify_key not in self.sent_notifications:
                            self._send_notification(
                                f"【现在】{task_name}",
                                f"已开始 ({start_str} - {end_str})"
                            )
                            self.sent_notifications[notify_key] = True

                # 检查任务结束前的提醒
                before_end_minutes = notification_config.get('before_end_minutes', [])
                for minutes in before_end_minutes:
                    remind_time = end_time.addSecs(-minutes * 60)
                    if self._should_notify(current_time, remind_time):
                        notify_key = f"{task_name}_before_end_{minutes}_{current_date}"
                        if notify_key not in self.sent_notifications:
                            self._send_notification(
                                f"【提前{minutes}分钟】{task_name}",
                                f"将在 {end_str} 结束"
                            )
                            self.sent_notifications[notify_key] = True

                # 检查任务结束时的提醒
                if notification_config.get('on_end', False):
                    if self._should_notify(current_time, end_time):
                        notify_key = f"{task_name}_on_end_{current_date}"
                        if notify_key not in self.sent_notifications:
                            # 查找下一个任务
                            next_task = self._get_next_task(end_str)
                            next_info = f", 下一项: {next_task}" if next_task else ""
                            self._send_notification(
                                f"【结束】{task_name}",
                                f"已结束{next_info}"
                            )
                            self.sent_notifications[notify_key] = True

            except Exception as e:
                self.logger.error(f"处理任务 {task_name} 的通知时出错: {e}")

    def _should_notify(self, current_time, target_time):
        """判断当前时间是否应该发送通知

        Args:
            current_time: 当前时间 (QTime)
            target_time: 目标时间 (QTime)

        Returns:
            bool: 如果时间匹配(相差在1分钟内)返回 True
        """
        # 计算时间差(秒)
        diff = abs(current_time.secsTo(target_time))
        # 如果在60秒内,认为匹配
        return diff < 60

    def _send_notification(self, title, message):
        """发送系统通知

        Args:
            title: 通知标题
            message: 通知内容
        """
        try:
            # 发送系统托盘通知
            self.tray_icon.showMessage(
                "PyDayBar 任务提醒",
                f"{title}\n{message}",
                QSystemTrayIcon.Information,
                5000  # 显示5秒
            )

            # 添加到历史记录
            self._add_to_history(title, message)

            # 记录日志
            self.logger.info(f"发送通知: {title} - {message}")

            # 播放提示音(如果启用)
            if self.config.get('notification', {}).get('sound_enabled', False):
                self._play_sound()

        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")

    def _play_sound(self):
        """播放提示音"""
        try:
            sound_file = self.config.get('notification', {}).get('sound_file', '')

            if sound_file:
                # TODO: 播放自定义音频文件
                # 可以使用 QSound 或其他音频库
                pass
            else:
                # 播放系统默认提示音
                QApplication.beep()

        except Exception as e:
            self.logger.error(f"播放提示音失败: {e}")

    def _add_to_history(self, title, message):
        """添加到通知历史记录

        Args:
            title: 通知标题
            message: 通知内容
        """
        timestamp = datetime.now().strftime("%H:%M")
        self.notification_history.append({
            'time': timestamp,
            'title': title,
            'message': message
        })

        # 只保留最近10条
        if len(self.notification_history) > 10:
            self.notification_history = self.notification_history[-10:]

    def _clean_old_notifications(self, current_date):
        """清理旧的通知记录

        Args:
            current_date: 当前日期字符串 (YYYY-MM-DD)
        """
        # 删除不是今天的记录
        keys_to_delete = [
            key for key in self.sent_notifications.keys()
            if not key.endswith(current_date)
        ]

        for key in keys_to_delete:
            del self.sent_notifications[key]

        if keys_to_delete:
            self.logger.info(f"清理了 {len(keys_to_delete)} 条过期通知记录")

    def _get_next_task(self, current_end_time):
        """获取下一个任务的名称

        Args:
            current_end_time: 当前任务结束时间字符串

        Returns:
            str: 下一个任务名称,如果没有返回 None
        """
        try:
            # 将时间字符串转换为分钟数
            def time_to_minutes(time_str):
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                if hours == 24:
                    return 24 * 60
                return hours * 60 + minutes

            current_minutes = time_to_minutes(current_end_time)

            # 查找紧接着开始的任务
            for task in self.tasks:
                start_minutes = time_to_minutes(task.get('start', '00:00'))
                if start_minutes >= current_minutes:
                    return task.get('task', '')

            return None

        except Exception as e:
            self.logger.error(f"获取下一个任务失败: {e}")
            return None

    def get_notification_history(self):
        """获取通知历史记录

        Returns:
            list: 通知历史列表
        """
        return self.notification_history

    def send_test_notification(self):
        """发送测试通知"""
        self._send_notification(
            "测试通知",
            "这是一条测试通知,如果您看到这条消息,说明通知功能正常工作!"
        )


class TimeProgressBar(QWidget):
    """时间进度条主窗口"""

    def __init__(self):
        super().__init__()
        self.app_dir = self.get_app_dir()  # 获取应用目录
        self.setup_logging()  # 设置日志
        self.config = self.load_config()  # 加载配置
        self.tasks = self.load_tasks()  # 加载任务数据
        self.calculate_time_range()  # 计算任务的时间范围
        self.current_time_percentage = 0.0  # 初始化时间百分比
        self.hovered_task_index = -1  # 当前悬停的任务索引(-1表示没有悬停)

        # 初始化时间标记相关变量
        self.marker_pixmap = None  # 静态图片
        self.marker_movie = None   # GIF 动画
        self.init_marker_image()   # 加载时间标记图片

        self.init_ui()
        self.init_timer()  # 初始化定时器
        self.init_tray()  # 初始化托盘
        self.init_notification_manager()  # 初始化通知管理器
        self.init_file_watcher()  # 初始化文件监视器
        self.installEventFilter(self)  # 安装事件过滤器
        self.setMouseTracking(True)  # 启用鼠标追踪

    def get_app_dir(self):
        """获取应用程序目录(支持打包后的 exe)"""
        if getattr(sys, 'frozen', False):
            # 打包后的 exe,使用 exe 所在目录
            return Path(sys.executable).parent
        else:
            # 开发环境,使用脚本所在目录
            return Path(__file__).parent

    def get_resource_path(self, relative_path):
        """获取资源文件路径(支持打包后的 exe)

        PyInstaller 打包后,资源文件会被解压到 _MEIPASS 临时目录
        """
        if getattr(sys, 'frozen', False):
            # 打包后的 exe,资源文件在临时目录
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境,资源文件在脚本目录
            base_path = Path(__file__).parent

        return base_path / relative_path

    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题(虽然无边框窗口看不到)
        self.setWindowTitle('PyDayBar - 桌面日历进度条')

        # 窗口标志组合
        # 移除 WindowTransparentForInput 以支持鼠标交互
        flags = (
            Qt.FramelessWindowHint |           # 无边框
            Qt.WindowStaysOnTopHint |          # 始终置顶
            Qt.WindowDoesNotAcceptFocus |      # 不接受焦点(避免影响其他窗口)
            Qt.BypassWindowManagerHint         # 绕过窗口管理器(防止被隐藏)
        )
        self.setWindowFlags(flags)

        # 设置背景透明(关键属性)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置为不在任务栏显示,但保持始终可见
        self.setAttribute(Qt.WA_X11DoNotAcceptFocus)

        # 设置窗口布局和位置
        self.setup_geometry()

        # 初始化时显示窗口
        self.show()
        self.raise_()
        self.setVisible(True)

        # Windows 特定:设置窗口始终在最顶层
        if platform.system() == 'Windows':
            self.set_windows_topmost()

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        self.logger.info("窗口显示事件触发")

    def hideEvent(self, event):
        """窗口隐藏事件"""
        super().hideEvent(event)
        self.logger.warning("窗口隐藏事件触发! 这不应该发生")

    def changeEvent(self, event):
        """窗口状态变化事件"""
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            self.logger.info(f"窗口状态变化: {self.windowState()}")

    def eventFilter(self, obj, event):
        """事件过滤器:防止窗口被意外隐藏"""
        from PySide6.QtCore import QEvent

        # 拦截隐藏事件并阻止
        if obj == self and event.type() == QEvent.Hide:
            self.logger.warning("检测到窗口隐藏事件,阻止并强制显示")
            # 阻止隐藏事件
            event.ignore()
            # 使用 QTimer 延迟强制显示,避免事件循环冲突
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.force_show)
            return True  # 事件已处理,不继续传播

        return super().eventFilter(obj, event)

    def force_show(self):
        """强制显示窗口"""
        self.setVisible(True)
        self.show()
        self.raise_()
        self.activateWindow()

        # Windows 特定:设置窗口始终在最顶层
        if platform.system() == 'Windows':
            self.set_windows_topmost()

        self.logger.info("强制显示窗口")

    def set_windows_topmost(self):
        """Windows 特定:设置窗口始终置顶,在任务栏之上"""
        try:
            hwnd = int(self.winId())

            # Windows API 常量
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040

            # 获取 Windows API 函数
            user32 = ctypes.windll.user32

            # 设置窗口为 TOPMOST
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )

            # 获取扩展窗口样式
            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000

            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ex_style |= (WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

            self.logger.info("已设置 Windows TOPMOST 属性")
        except Exception as e:
            self.logger.error(f"设置 Windows TOPMOST 失败: {e}")

    def setup_geometry(self):
        """设置窗口几何属性(位置和大小)"""
        # 获取所有屏幕
        screens = QApplication.screens()
        screen_index = min(self.config['screen_index'], len(screens) - 1)
        screen = screens[screen_index]
        screen_geometry = screen.geometry()

        # 从配置读取参数
        bar_height = self.config['bar_height']
        bar_width = screen_geometry.width()

        # 悬停时需要额外的空间来显示扩展色块
        # 固定50像素的额外空间用于悬停效果,确保文本有足够空间
        hover_extra_space = 50

        # 计算标记图片需要的额外空间
        marker_extra_space = 0
        if self.config.get('marker_type') in ['image', 'gif']:
            marker_size = self.config.get('marker_size', 50)
            marker_y_offset = self.config.get('marker_y_offset', 0)
            # 标记图片可能超出进度条高度,需要预留额外空间
            # 如果图片底对齐,可能需要的高度 = 图片高度 - 进度条高度 + Y轴偏移
            marker_extra_space = max(0, marker_size - bar_height + abs(marker_y_offset))

        # 取悬停空间和标记空间的最大值
        hover_extra_space = max(hover_extra_space, marker_extra_space)

        # 根据配置定位到屏幕顶部或任务栏上方
        if self.config['position'] == 'bottom':
            # 使用可用几何(available geometry)而不是完整屏幕几何
            # 可用几何会排除任务栏、Dock等系统UI的空间
            available_geometry = screen.availableGeometry()
            # 定位到可用区域的底部(任务栏上方),留出悬停空间
            y_pos = available_geometry.y() + available_geometry.height() - bar_height - hover_extra_space
            # 增加窗口高度以容纳悬停效果
            total_height = bar_height + hover_extra_space
        else:
            # 顶部位置:使用可用区域的顶部
            available_geometry = screen.availableGeometry()
            y_pos = available_geometry.y()
            total_height = bar_height + hover_extra_space

        # 设置窗口几何属性
        self.setGeometry(
            screen_geometry.x(),  # 多显示器支持 x 坐标
            y_pos,                # 修正后的 y 坐标
            bar_width,
            total_height          # 增加高度以容纳悬停效果
        )

        self.logger.info(f"窗口位置设置: x={screen_geometry.x()}, y={y_pos}, w={bar_width}, h={total_height} (bar_h={bar_height}), position={self.config['position']}")

    def setup_logging(self):
        """设置日志系统"""
        log_file = self.app_dir / 'pydaybar.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("PyDayBar 启动")

    def load_config(self):
        """加载配置文件"""
        config_file = self.app_dir / 'config.json'

        # 默认配置
        default_config = {
            "bar_height": 20,
            "position": "bottom",
            "background_color": "#505050",
            "background_opacity": 180,
            "marker_color": "#FF0000",
            "marker_width": 2,
            "marker_type": "line",  # "line", "image", "gif"
            "marker_image_path": "",  # 自定义图片路径
            "marker_size": 50,  # 标记图片大小(像素)
            "marker_y_offset": 0,  # 标记图片 Y 轴偏移(像素,正值向上,负值向下)
            "screen_index": 0,
            "update_interval": 1000,
            "enable_shadow": True,
            "corner_radius": 0,
            # 通知配置
            "notification": {
                "enabled": True,                    # 通知总开关
                "before_start_minutes": [10, 5],   # 任务开始前N分钟提醒
                "on_start": True,                   # 任务开始时提醒
                "before_end_minutes": [5],          # 任务结束前N分钟提醒
                "on_end": False,                    # 任务结束时提醒
                "sound_enabled": True,              # 声音开关
                "sound_file": "",                   # 自定义提示音路径
                "quiet_hours": {                    # 免打扰时段
                    "enabled": False,
                    "start": "22:00",
                    "end": "08:00"
                }
            }
        }

        if not config_file.exists():
            self.logger.info("config.json 不存在,创建默认配置")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            return default_config

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 合并默认配置(防止缺失键)
            merged_config = {**default_config, **config}
            self.logger.info("配置文件加载成功")
            return merged_config
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析错误: {e}")
            return default_config
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}", exc_info=True)
            return default_config

    def load_tasks(self):
        """加载并验证任务数据"""
        tasks_file = self.app_dir / 'tasks.json'

        # 如果文件不存在,尝试加载24小时模板
        if not tasks_file.exists():
            self.logger.info("tasks.json 不存在,尝试加载24小时模板")
            # 使用 get_resource_path 获取打包资源路径
            template_file = self.get_resource_path('tasks_template_24h.json')

            if template_file.exists():
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        default_tasks = json.load(f)
                    # 保存为 tasks.json(保存到 exe 所在目录)
                    with open(tasks_file, 'w', encoding='utf-8') as f:
                        json.dump(default_tasks, f, indent=4, ensure_ascii=False)
                    self.logger.info(f"已从模板加载 {len(default_tasks)} 个任务")
                    return default_tasks
                except Exception as e:
                    self.logger.error(f"加载模板失败: {e}")

            # 如果模板也不存在,创建简单的默认任务
            self.logger.info("模板不存在,创建默认任务")
            default_tasks = [
                {"start": "09:00", "end": "12:00", "task": "上午工作", "color": "#4CAF50"}
            ]
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(default_tasks, f, indent=4, ensure_ascii=False)
            return default_tasks

        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            # 验证数据格式
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
        """验证时间格式 HH:MM

        允许 00:00-23:59 以及特殊的 24:00(表示午夜)
        """
        import re
        # 允许 0-23 小时,以及特殊的 24:00
        pattern = r'^([0-1]?[0-9]|2[0-4]):([0-5][0-9])$'
        if re.match(pattern, time_str):
            hours, minutes = map(int, time_str.split(':'))
            # 24:00 是唯一允许的 24 小时格式
            if hours == 24 and minutes != 0:
                return False
            return True
        return False

    def init_marker_image(self):
        """初始化时间标记图片"""
        marker_type = self.config.get('marker_type', 'line')

        # 清理旧的资源
        self.marker_pixmap = None
        if self.marker_movie:
            self.marker_movie.stop()
            self.marker_movie = None

        if marker_type == 'line':
            # 线条模式,不需要加载图片
            return

        # 获取图片路径
        image_path = self.config.get('marker_image_path', '')

        if not image_path:
            self.logger.info("未配置时间标记图片,使用线条模式")
            self.config['marker_type'] = 'line'
            return

        # 支持相对路径和绝对路径
        image_file = Path(image_path)
        if not image_file.is_absolute():
            # 相对路径:相对于应用目录
            image_file = self.app_dir / image_path

        if not image_file.exists():
            self.logger.error(f"时间标记图片不存在: {image_file}")
            self.config['marker_type'] = 'line'
            return

        # 根据文件扩展名判断类型
        ext = image_file.suffix.lower()

        try:
            if ext in ['.gif', '.webp']:
                # GIF 或 WebP 动画
                self.marker_movie = QMovie(str(image_file))
                if not self.marker_movie.isValid():
                    self.logger.error(f"无效的动画文件: {image_file}")
                    self.marker_movie = None
                    self.config['marker_type'] = 'line'
                    return

                # 缩放到配置的大小
                marker_size = self.config.get('marker_size', 50)
                self.marker_movie.setScaledSize(QPixmap(marker_size, marker_size).size())

                # 启动动画
                self.marker_movie.start()

                # 连接帧更新信号,触发重绘
                self.marker_movie.frameChanged.connect(self.update)

                self.logger.info(f"加载动画时间标记 ({ext}): {image_file}")

            elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                # 静态图片(包括静态的 WebP)
                self.marker_pixmap = QPixmap(str(image_file))
                if self.marker_pixmap.isNull():
                    self.logger.error(f"无法加载图片: {image_file}")
                    self.marker_pixmap = None
                    self.config['marker_type'] = 'line'
                    return

                # 缩放到配置的大小,保持宽高比
                marker_size = self.config.get('marker_size', 50)
                self.marker_pixmap = self.marker_pixmap.scaled(
                    marker_size,
                    marker_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                self.logger.info(f"加载静态图片时间标记 ({ext}): {image_file}")
            else:
                self.logger.error(f"不支持的图片格式: {ext}")
                self.config['marker_type'] = 'line'

        except Exception as e:
            self.logger.error(f"加载时间标记图片失败: {e}", exc_info=True)
            self.config['marker_type'] = 'line'

    def calculate_time_range(self):
        """计算任务的紧凑排列映射

        将任务按时间顺序排列,计算每个任务在进度条上的位置
        忽略任务之间的时间间隔,所有任务紧密排列
        """
        if not self.tasks:
            # 如果没有任务,使用全天范围
            self.time_range_start = 0
            self.time_range_end = 86400
            self.time_range_duration = 86400
            self.task_positions = []
            return

        # 按任务开始时间排序
        sorted_tasks = sorted(self.tasks, key=lambda t: self.time_str_to_seconds(t['start']))

        # 计算总的任务持续时间(只计算任务本身,不包括间隔)
        total_task_duration = 0
        for task in sorted_tasks:
            start_seconds = self.time_str_to_seconds(task['start'])
            end_seconds = self.time_str_to_seconds(task['end'])
            duration = end_seconds - start_seconds
            total_task_duration += duration

        # 构建任务位置映射表
        # 每个任务记录:原始时间区间 -> 紧凑排列后的百分比区间
        self.task_positions = []
        cumulative_duration = 0

        for task in sorted_tasks:
            start_seconds = self.time_str_to_seconds(task['start'])
            end_seconds = self.time_str_to_seconds(task['end'])
            duration = end_seconds - start_seconds

            # 计算该任务在紧凑排列中的百分比位置
            start_percentage = cumulative_duration / total_task_duration if total_task_duration > 0 else 0
            end_percentage = (cumulative_duration + duration) / total_task_duration if total_task_duration > 0 else 0

            self.task_positions.append({
                'task': task,
                'original_start': start_seconds,
                'original_end': end_seconds,
                'compact_start_pct': start_percentage,
                'compact_end_pct': end_percentage
            })

            cumulative_duration += duration

        # 保存时间范围信息(用于日志)
        self.time_range_start = self.time_str_to_seconds(sorted_tasks[0]['start'])
        self.time_range_end = self.time_str_to_seconds(sorted_tasks[-1]['end'])
        self.time_range_duration = total_task_duration

        self.logger.info(f"紧凑模式: {len(sorted_tasks)}个任务, 总时长{total_task_duration//3600}小时{(total_task_duration%3600)//60}分钟")

    def time_str_to_seconds(self, time_str):
        """将 HH:MM 转换为秒数"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            # 特殊处理 24:00
            if hours == 24 and minutes == 0:
                return 86400
            return hours * 3600 + minutes * 60
        except (ValueError, AttributeError):
            return 0

    def seconds_to_time_str(self, seconds):
        """将秒数转换为 HH:MM 格式"""
        if seconds >= 86400:
            return "24:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    def time_to_percentage(self, time_str):
        """将 HH:MM 格式转换为 0.0-1.0 之间的百分比(基于任务时间范围)"""
        try:
            seconds = self.time_str_to_seconds(time_str)

            # 如果时间范围无效,使用全天计算
            if self.time_range_duration == 0:
                return seconds / 86400

            # 基于任务时间范围计算百分比
            if seconds < self.time_range_start:
                return 0.0
            elif seconds > self.time_range_end:
                return 1.0
            else:
                return (seconds - self.time_range_start) / self.time_range_duration
        except (ValueError, AttributeError):
            self.logger.warning(f"无效的时间格式 '{time_str}'")
            return 0.0

    def init_timer(self):
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_marker)
        # 使用配置文件中的更新间隔
        self.timer.start(self.config['update_interval'])

        # 立即更新一次,避免启动时等待
        self.update_time_marker()

        # 添加窗口可见性监控定时器(每秒检查一次)
        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.visibility_timer.start(1000)

    def check_visibility(self):
        """检查并确保窗口始终可见"""
        if not self.isVisible():
            self.logger.warning("检测到窗口不可见,强制显示")
            self.force_show()

    def init_tray(self):
        """初始化系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)

        # 使用Qt内置图标(因为我们还没有自定义图标文件)
        icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon
        )
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip('PyDayBar - 桌面日历进度条')

        # 创建右键菜单
        tray_menu = QMenu()

        # 打开配置界面动作
        config_action = QAction('⚙️ 打开配置', self)
        config_action.triggered.connect(self.open_config_gui)
        tray_menu.addAction(config_action)

        tray_menu.addSeparator()

        # 通知功能子菜单
        notification_menu = QMenu('🔔 通知功能', self)

        # 发送测试通知
        test_notify_action = QAction('📢 发送测试通知', self)
        test_notify_action.triggered.connect(self.send_test_notification)
        notification_menu.addAction(test_notify_action)

        # 查看通知历史
        history_action = QAction('📜 查看通知历史', self)
        history_action.triggered.connect(self.show_notification_history)
        notification_menu.addAction(history_action)

        tray_menu.addMenu(notification_menu)

        # 重载配置动作
        reload_action = QAction('🔄 重载配置', self)
        reload_action.triggered.connect(self.reload_all)
        tray_menu.addAction(reload_action)

        # 切换位置动作
        toggle_position_action = QAction('↕️ 切换位置', self)
        toggle_position_action.triggered.connect(self.toggle_position)
        tray_menu.addAction(toggle_position_action)

        tray_menu.addSeparator()

        # 退出动作
        quit_action = QAction('❌ 退出', self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def init_notification_manager(self):
        """初始化通知管理器"""
        self.notification_manager = NotificationManager(
            self.config,
            self.tasks,
            self.tray_icon,
            self.logger
        )
        self.logger.info("通知管理器初始化完成")

    def send_test_notification(self):
        """发送测试通知"""
        if hasattr(self, 'notification_manager'):
            self.notification_manager.send_test_notification()
        else:
            self.logger.warning("通知管理器未初始化")

    def show_notification_history(self):
        """显示通知历史"""
        if not hasattr(self, 'notification_manager'):
            self.tray_icon.showMessage(
                "PyDayBar",
                "通知管理器未初始化",
                QSystemTrayIcon.Information,
                3000
            )
            return

        history = self.notification_manager.get_notification_history()

        if not history:
            self.tray_icon.showMessage(
                "PyDayBar 通知历史",
                "暂无通知记录",
                QSystemTrayIcon.Information,
                3000
            )
            return

        # 格式化历史记录
        history_text = "\n".join([
            f"[{item['time']}] {item['title']}"
            for item in history[-5:]  # 只显示最近5条
        ])

        self.tray_icon.showMessage(
            "PyDayBar 通知历史",
            f"最近的通知:\n{history_text}",
            QSystemTrayIcon.Information,
            5000
        )

    def open_config_gui(self):
        """打开配置界面"""
        try:
            # 动态导入配置界面
            from config_gui import ConfigManager

            # 如果已经打开,则显示现有窗口
            if hasattr(self, 'config_window') and self.config_window.isVisible():
                self.config_window.activateWindow()
                self.config_window.raise_()
                return

            # 创建新窗口
            self.config_window = ConfigManager()
            self.config_window.config_saved.connect(self.reload_all)
            self.config_window.show()
            self.logger.info("配置界面已打开")

        except Exception as e:
            self.logger.error(f"打开配置界面失败: {e}", exc_info=True)
            # 如果导入失败,显示错误消息
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                None,
                "错误",
                f"无法打开配置界面:\n{str(e)}\n\n请确保 config_gui.py 文件存在。"
            )

    def reload_all(self):
        """重载配置和任务"""
        self.logger.info("开始重载配置和任务...")
        old_height = self.config.get('bar_height', 20)
        old_position = self.config.get('position', 'bottom')
        old_screen_index = self.config.get('screen_index', 0)

        # 重新加载配置和任务
        self.config = self.load_config()
        self.tasks = self.load_tasks()

        # 重新加载时间标记图片
        self.init_marker_image()

        # 重新计算时间范围
        self.calculate_time_range()

        # 重新加载通知管理器配置
        if hasattr(self, 'notification_manager'):
            self.notification_manager.reload_config(self.config, self.tasks)

        # 如果高度、位置或屏幕索引改变,需要重新设置窗口几何
        new_height = self.config.get('bar_height', 20)
        new_position = self.config.get('position', 'bottom')
        new_screen_index = self.config.get('screen_index', 0)

        if (old_height != new_height or
            old_position != new_position or
            old_screen_index != new_screen_index):
            self.logger.info(f"检测到几何变化: 高度 {old_height}->{new_height}, 位置 {old_position}->{new_position}, 屏幕 {old_screen_index}->{new_screen_index}")
            # 重新设置窗口几何
            self.setup_geometry()

        # 更新定时器间隔
        self.timer.setInterval(self.config['update_interval'])

        # 触发重绘
        self.update()
        self.logger.info("配置和任务重载完成")

    def toggle_position(self):
        """切换进度条位置"""
        self.config['position'] = (
            'top' if self.config['position'] == 'bottom' else 'bottom'
        )
        # 保存到配置文件
        config_file = self.app_dir / 'config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        self.setup_geometry()

    def init_file_watcher(self):
        """初始化文件监视器"""
        self.file_watcher = QFileSystemWatcher(self)

        # 获取文件路径
        tasks_file = str(self.app_dir / 'tasks.json')
        config_file = str(self.app_dir / 'config.json')

        # 添加到监视列表
        self.file_watcher.addPath(tasks_file)
        self.file_watcher.addPath(config_file)

        # 连接信号
        self.file_watcher.fileChanged.connect(self.on_file_changed)
        self.logger.info("文件监视器已启动")

    def on_file_changed(self, path):
        """文件变化时的回调"""
        self.logger.info(f"检测到文件变化: {path}")

        # 防止重复触发: 使用定时器去抖
        if hasattr(self, '_reload_timer') and self._reload_timer.isActive():
            self._reload_timer.stop()

        # Windows 某些编辑器会先删除再创建文件
        # 需要重新添加到监视列表
        tasks_file = str(self.app_dir / 'tasks.json')
        config_file = str(self.app_dir / 'config.json')

        # 检查并重新添加监视
        current_files = self.file_watcher.files()
        if tasks_file not in current_files:
            self.file_watcher.addPath(tasks_file)
            self.logger.info(f"重新监视文件: {tasks_file}")
        if config_file not in current_files:
            self.file_watcher.addPath(config_file)
            self.logger.info(f"重新监视文件: {config_file}")

        # 延迟重载,避免频繁触发
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self.reload_all)
        self._reload_timer.start(300)  # 300毫秒延迟

    def update_time_marker(self):
        """更新时间标记的位置(紧凑模式)"""
        current_time = QTime.currentTime()

        # 计算当前时间的秒数
        total_seconds = (
            current_time.hour() * 3600 +
            current_time.minute() * 60 +
            current_time.second()
        )

        # 在紧凑模式下,找到当前时间所在的任务
        new_percentage = 0.0

        if not self.task_positions:
            # 没有任务时使用全天计算
            new_percentage = total_seconds / 86400
        else:
            # 查找当前时间所在的任务
            found = False
            cumulative_duration = 0

            for pos in self.task_positions:
                task_start = pos['original_start']
                task_end = pos['original_end']
                task_duration = task_end - task_start

                if task_start <= total_seconds <= task_end:
                    # 当前时间在这个任务内
                    # 计算在任务内的进度
                    progress_in_task = (total_seconds - task_start) / task_duration if task_duration > 0 else 0
                    # 计算在整个进度条上的位置
                    new_percentage = pos['compact_start_pct'] + (pos['compact_end_pct'] - pos['compact_start_pct']) * progress_in_task
                    found = True
                    break
                elif total_seconds < task_start:
                    # 当前时间在这个任务之前(处于间隔中)
                    # 显示在这个任务的起始位置
                    new_percentage = pos['compact_start_pct']
                    found = True
                    break

                cumulative_duration += task_duration

            # 如果当前时间在所有任务之后
            if not found:
                new_percentage = 1.0

        # 仅当百分比实际变化时才重绘(避免浮点误差)
        if abs(new_percentage - self.current_time_percentage) > 0.00001:
            self.current_time_percentage = new_percentage
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 检测悬停在哪个任务上(紧凑模式)"""
        mouse_x = event.position().x()
        width = self.width()

        # 计算鼠标位置对应的百分比
        mouse_percentage = mouse_x / width if width > 0 else 0

        # 查找鼠标所在的任务(使用紧凑位置)
        old_hovered_index = self.hovered_task_index
        self.hovered_task_index = -1

        for i, pos in enumerate(self.task_positions):
            if pos['compact_start_pct'] <= mouse_percentage <= pos['compact_end_pct']:
                self.hovered_task_index = i
                break

        # 如果悬停任务改变,触发重绘
        if old_hovered_index != self.hovered_task_index:
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口事件"""
        if self.hovered_task_index != -1:
            self.hovered_task_index = -1
            self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿

        width = self.width()
        height = self.height()
        bar_height = self.config['bar_height']

        # 计算进度条的实际位置(在窗口底部)
        bar_y_offset = height - bar_height

        # 1. 绘制半透明背景条(只在进度条区域)
        bg_color = QColor(self.config['background_color'])
        bg_color.setAlpha(self.config['background_opacity'])
        painter.fillRect(0, bar_y_offset, width, bar_height, bg_color)

        # 2. 绘制任务色块(使用紧凑模式位置)
        for i, pos in enumerate(self.task_positions):
            task = pos['task']

            # 使用紧凑模式的百分比位置
            start_pct = pos['compact_start_pct']
            end_pct = pos['compact_end_pct']

            # 判断任务状态(比较任务的原始时间和当前时间)
            current_time = QTime.currentTime()
            current_seconds = current_time.hour() * 3600 + current_time.minute() * 60 + current_time.second()

            # 三种状态:未开始、进行中、已完成
            is_completed = pos['original_end'] <= current_seconds  # 已完成
            is_in_progress = pos['original_start'] <= current_seconds < pos['original_end']  # 进行中
            is_not_started = current_seconds < pos['original_start']  # 未开始

            # 计算任务块的位置和宽度
            x = start_pct * width
            task_width = (end_pct - start_pct) * width

            # 解析颜色
            color = QColor(task['color'])

            # 未开始的任务置灰处理
            if is_not_started:
                # 转换为灰度并降低饱和度
                gray_value = int(color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114)
                color = QColor(gray_value, gray_value, gray_value, 120)  # 半透明灰色
            # 进行中和已完成的任务保持原色(点亮状态)

            # 绘制任务块
            if i == self.hovered_task_index:
                # 悬停状态:根据文字大小动态调整色块尺寸

                # 设置文字字体
                font = QFont()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)

                # 任务信息 - 单行显示
                task_text = f"{task['task']} ({task['start']}-{task['end']})"

                # 计算文字的实际尺寸
                font_metrics = painter.fontMetrics()
                text_width = font_metrics.horizontalAdvance(task_text)
                text_height = font_metrics.height()

                # 添加内边距(增加以确保文字不被截断)
                padding_horizontal = 30  # 左右各15像素
                padding_vertical = 14    # 上下各7像素

                # 计算悬停色块的实际尺寸
                hover_width = max(task_width, text_width + padding_horizontal)  # 取任务块宽度和文字宽度的较大值
                hover_height = text_height + padding_vertical

                # 计算悬停色块的位置(居中对齐任务块)
                hover_x = x + (task_width - hover_width) / 2
                hover_y = bar_y_offset - hover_height - 5  # 向上偏移5像素,避免与进度条重叠

                # 确保悬停色块不超出窗口边界
                if hover_x < 0:
                    hover_x = 0
                elif hover_x + hover_width > width:
                    hover_x = width - hover_width

                # 确保 y 坐标不会超出窗口顶部
                if hover_y < 0:
                    hover_y = 0

                hover_rect = QRectF(hover_x, hover_y, hover_width, hover_height)

                # 绘制悬停的扩展色块
                hover_color = QColor(color)
                hover_color.setAlpha(240)  # 稍微透明
                painter.setBrush(hover_color)
                painter.setPen(QPen(QColor(255, 255, 255, 255), 2))  # 白色边框

                if self.config.get('corner_radius', 0) > 0:
                    painter.drawRoundedRect(
                        hover_rect,
                        self.config['corner_radius'],
                        self.config['corner_radius']
                    )
                else:
                    painter.drawRect(hover_rect)

                # 绘制任务文本
                painter.setPen(QColor(255, 255, 255))  # 白色文字
                painter.drawText(hover_rect, Qt.AlignCenter, task_text)

                # 在进度条位置也绘制正常的色块
                base_rect = QRectF(x, bar_y_offset + 1, task_width, bar_height - 2)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                if self.config.get('corner_radius', 0) > 0:
                    painter.drawRoundedRect(
                        base_rect,
                        self.config['corner_radius'],
                        self.config['corner_radius']
                    )
                else:
                    painter.fillRect(base_rect, color)
            else:
                # 普通状态 - 在进度条位置绘制
                rect = QRectF(x, bar_y_offset + 1, task_width, bar_height - 2)

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

        # 3. 绘制时间标记(最上层,在进度条区域)
        marker_x = self.current_time_percentage * width
        marker_type = self.config.get('marker_type', 'line')

        if marker_type == 'gif' and self.marker_movie and self.marker_movie.isValid():
            # GIF 动画标记
            current_pixmap = self.marker_movie.currentPixmap()
            if not current_pixmap.isNull():
                # 计算绘制位置(水平居中,底部对齐到进度条底部 + Y轴偏移)
                pixmap_width = current_pixmap.width()
                pixmap_height = current_pixmap.height()
                draw_x = int(marker_x - pixmap_width / 2)
                # Y 轴位置 = 窗口底部 - 图片高度 - Y轴偏移(正值向上,负值向下)
                marker_y_offset = self.config.get('marker_y_offset', 0)
                draw_y = height - pixmap_height - marker_y_offset

                # 绘制 GIF 当前帧
                painter.drawPixmap(draw_x, draw_y, current_pixmap)

        elif marker_type == 'image' and self.marker_pixmap and not self.marker_pixmap.isNull():
            # 静态图片标记
            pixmap_width = self.marker_pixmap.width()
            pixmap_height = self.marker_pixmap.height()
            draw_x = int(marker_x - pixmap_width / 2)
            # Y 轴位置 = 窗口底部 - 图片高度 - Y轴偏移(正值向上,负值向下)
            marker_y_offset = self.config.get('marker_y_offset', 0)
            draw_y = height - pixmap_height - marker_y_offset

            # 绘制图片
            painter.drawPixmap(draw_x, draw_y, self.marker_pixmap)

        else:
            # 默认线条标记
            # 绘制阴影效果(可选)
            if self.config.get('enable_shadow', True):
                shadow_pen = QPen(QColor(0, 0, 0, 100))
                shadow_pen.setWidth(self.config['marker_width'] + 1)
                painter.setPen(shadow_pen)
                painter.drawLine(int(marker_x + 1), bar_y_offset, int(marker_x + 1), height)

            # 绘制主线
            marker_color = QColor(self.config['marker_color'])
            marker_pen = QPen(marker_color)
            marker_pen.setWidth(self.config['marker_width'])
            painter.setPen(marker_pen)
            painter.drawLine(int(marker_x), bar_y_offset, int(marker_x), height)

        painter.end()


def main():
    """主程序入口"""
    # 启用高DPI支持(Windows 10/11)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 创建应用实例
    app = QApplication(sys.argv)

    # 创建并显示主窗口
    window = TimeProgressBar()
    window.show()

    # 进入事件循环
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
