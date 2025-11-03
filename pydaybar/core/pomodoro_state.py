"""
番茄钟状态枚举
"""
from enum import Enum


class PomodoroState(Enum):
    """番茄钟状态枚举"""
    IDLE = 0          # 未启动
    WORK = 1          # 工作中
    SHORT_BREAK = 2   # 短休息
    LONG_BREAK = 3    # 长休息
    PAUSED = 4        # 已暂停
