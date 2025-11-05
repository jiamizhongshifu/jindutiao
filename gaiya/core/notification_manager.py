"""
任务提醒通知管理器
"""
from datetime import datetime, date
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtCore import QTimer, QTime


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
