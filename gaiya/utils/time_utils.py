"""
时间处理工具函数
"""
import re


def validate_time_format(time_str):
    """验证时间格式 HH:MM

    允许 00:00-23:59 以及特殊的 24:00(表示午夜)

    Args:
        time_str: 时间字符串,格式为 HH:MM

    Returns:
        bool: 如果格式有效返回 True,否则返回 False
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


def time_str_to_seconds(time_str):
    """将 HH:MM 转换为秒数

    Args:
        time_str: 时间字符串,格式为 HH:MM

    Returns:
        int: 转换后的秒数,转换失败返回 0
    """
    try:
        hours, minutes = map(int, time_str.split(':'))
        # 特殊处理 24:00
        if hours == 24 and minutes == 0:
            return 86400
        return hours * 3600 + minutes * 60
    except (ValueError, AttributeError):
        return 0


def seconds_to_time_str(seconds):
    """将秒数转换为 HH:MM 格式

    Args:
        seconds: 秒数

    Returns:
        str: HH:MM 格式的时间字符串
    """
    if seconds >= 86400:
        return "24:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def time_to_percentage(time_str, time_range_start=0, time_range_end=86400, time_range_duration=86400):
    """将 HH:MM 格式转换为 0.0-1.0 之间的百分比(基于任务时间范围)

    Args:
        time_str: 时间字符串,格式为 HH:MM
        time_range_start: 时间范围起始秒数(默认0,即00:00)
        time_range_end: 时间范围结束秒数(默认86400,即24:00)
        time_range_duration: 时间范围持续时长(默认86400秒)

    Returns:
        float: 0.0-1.0 之间的百分比
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
