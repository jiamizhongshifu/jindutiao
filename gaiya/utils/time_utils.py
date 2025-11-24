"""
Time processing utility functions
"""
import re


def validate_time_format(time_str: str) -> bool:
    """Validate time string format HH:MM

    Accepts 00:00-23:59 and special 24:00 (midnight).

    Args:
        time_str: Time string in HH:MM format

    Returns:
        bool: True if format is valid, False otherwise
    """
    # 允许 0-23 小时,以及特殊的 24:00
    pattern = r'^([0-1]?[0-9]|2[0-4]):([0-5][0-9])$'
    if re.match(pattern, time_str):
        hours, minutes = map(int, time_str.split(':'))
        # 24:00 是唯一允许的 24 小时格式
        if hours == 24 and minutes != 0:
            return False
        return True
    return False


def time_str_to_seconds(time_str: str) -> int:
    """Convert HH:MM to seconds since midnight

    Args:
        time_str: Time string in HH:MM format

    Returns:
        int: Seconds since midnight, returns 0 on conversion failure
    """
    try:
        hours, minutes = map(int, time_str.split(':'))
        # 特殊处理 24:00
        if hours == 24 and minutes == 0:
            return 86400
        return hours * 3600 + minutes * 60
    except (ValueError, AttributeError):
        return 0


def seconds_to_time_str(seconds: int) -> str:
    """Convert seconds since midnight to HH:MM format

    Args:
        seconds: Seconds since midnight

    Returns:
        str: Time string in HH:MM format
    """
    if seconds >= 86400:
        return "24:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def time_to_percentage(
    time_str: str,
    time_range_start: int = 0,
    time_range_end: int = 86400,
    time_range_duration: int = 86400
) -> float:
    """Convert HH:MM to percentage (0.0-1.0) within time range

    Args:
        time_str: Time string in HH:MM format
        time_range_start: Range start in seconds (default 0, i.e., 00:00)
        time_range_end: Range end in seconds (default 86400, i.e., 24:00)
        time_range_duration: Range duration in seconds (default 86400)

    Returns:
        float: Percentage between 0.0-1.0
    """
    try:
        seconds = time_str_to_seconds(time_str)

        # 如果时间范围无效,使用全天计算
        if time_range_duration == 0:
            return seconds / 86400

        # 基于任务时间范围计算百分比
        if seconds < time_range_start:
            return 0.0
        elif seconds > time_range_end:
            return 1.0
        else:
            return (seconds - time_range_start) / time_range_duration
    except Exception:
        return 0.0
