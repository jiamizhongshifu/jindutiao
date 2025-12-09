"""
专注时长追踪器
追踪连续使用同一应用 ≥25分钟 的会话,与碎片化的"生产力时长"区分
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger("gaiya.core.focus_tracker")


class FocusTracker:
    """专注时长追踪器

    用于区分"专注时长"和"生产力时长":
    - 生产力时长: 使用生产力应用的总时长(可以碎片化)
    - 专注时长: 连续使用同一应用 ≥25分钟 的时长总和(需要连续性)
    """

    FOCUS_THRESHOLD = 25 * 60  # 25分钟(秒)

    def __init__(self):
        self.current_app: Optional[str] = None
        self.session_start: Optional[float] = None
        self.focus_sessions: List[Dict] = []  # 存储所有专注时段

    def on_app_switch(self, new_app: str, timestamp: float, is_productive: bool = False):
        """应用切换时调用

        Args:
            new_app: 新应用名称
            timestamp: 切换时间戳
            is_productive: 是否为生产力应用
        """
        if self.current_app and self.session_start:
            duration = timestamp - self.session_start

            # 如果持续时长 ≥25分钟,记录为专注时段
            if duration >= self.FOCUS_THRESHOLD:
                self.focus_sessions.append({
                    'app': self.current_app,
                    'start': self.session_start,
                    'end': timestamp,
                    'duration': duration,
                    'is_productive': is_productive
                })
                logger.info(
                    f"检测到专注时段: {self.current_app}, "
                    f"时长 {duration/60:.1f}分钟"
                )

        # 开始新的会话
        self.current_app = new_app
        self.session_start = timestamp

    def end_current_session(self, timestamp: float, is_productive: bool = False):
        """结束当前会话(例如关机、程序关闭时)"""
        self.on_app_switch("", timestamp, is_productive)

    def get_total_focus_time(self) -> int:
        """获取总专注时长(秒)"""
        return sum(session['duration'] for session in self.focus_sessions)

    def get_productive_focus_time(self) -> int:
        """获取生产力应用的专注时长(秒)"""
        return sum(
            session['duration']
            for session in self.focus_sessions
            if session.get('is_productive', False)
        )

    def get_focus_sessions(self) -> List[Dict]:
        """获取所有专注时段"""
        return self.focus_sessions

    def get_focus_session_count(self) -> int:
        """获取专注时段数量"""
        return len(self.focus_sessions)

    def reset(self):
        """重置追踪器(用于新的一天开始时)"""
        self.current_app = None
        self.session_start = None
        self.focus_sessions = []
        logger.info("专注追踪器已重置")


def calculate_focus_from_activity_log(activity_records: List[Dict]) -> Dict:
    """从活动日志中计算专注时长

    Args:
        activity_records: 活动记录列表,每条记录包含:
            - app_name: 应用名称
            - timestamp: 时间戳
            - category: 应用分类 (PRODUCTIVE, LEISURE, NEUTRAL, UNKNOWN)

    Returns:
        Dict包含:
            - total_focus_time: 总专注时长(秒)
            - productive_focus_time: 生产力专注时长(秒)
            - focus_sessions: 专注时段列表
            - focus_session_count: 专注时段数量
    """
    tracker = FocusTracker()

    # 按时间排序
    sorted_records = sorted(activity_records, key=lambda x: x['timestamp'])

    for i, record in enumerate(sorted_records):
        app_name = record.get('app_name', '')
        timestamp = record.get('timestamp', 0)
        category = record.get('category', 'UNKNOWN')
        is_productive = (category == 'PRODUCTIVE')

        # 检测应用切换
        if i < len(sorted_records) - 1:
            next_app = sorted_records[i + 1].get('app_name', '')
            next_timestamp = sorted_records[i + 1].get('timestamp', 0)

            if next_app != app_name:
                # 应用切换,结束当前会话
                tracker.on_app_switch(next_app, next_timestamp, is_productive)

    # 结束最后一个会话
    if sorted_records:
        last_record = sorted_records[-1]
        tracker.end_current_session(
            datetime.now().timestamp(),
            last_record.get('category') == 'PRODUCTIVE'
        )

    return {
        'total_focus_time': tracker.get_total_focus_time(),
        'productive_focus_time': tracker.get_productive_focus_time(),
        'focus_sessions': tracker.get_focus_sessions(),
        'focus_session_count': tracker.get_focus_session_count()
    }
