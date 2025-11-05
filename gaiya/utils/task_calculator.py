"""
任务计算工具
"""
from . import time_utils


def calculate_task_positions(tasks, logger):
    """计算任务的紧凑排列映射

    将任务按时间顺序排列,计算每个任务在进度条上的位置
    忽略任务之间的时间间隔,所有任务紧密排列

    Args:
        tasks: 任务列表
        logger: 日志记录器

    Returns:
        dict: 包含以下键的字典
            - task_positions: 任务位置映射列表
            - time_range_start: 第一个任务的开始时间（秒）
            - time_range_end: 最后一个任务的结束时间（秒）
            - time_range_duration: 所有任务的总时长（秒）
    """
    if not tasks:
        # 如果没有任务,使用全天范围
        return {
            'task_positions': [],
            'time_range_start': 0,
            'time_range_end': 86400,
            'time_range_duration': 86400
        }

    # 按任务开始时间排序
    sorted_tasks = sorted(tasks, key=lambda t: time_utils.time_str_to_seconds(t['start']))

    # 计算总的任务持续时间(只计算任务本身,不包括间隔)
    total_task_duration = 0
    for task in sorted_tasks:
        start_seconds = time_utils.time_str_to_seconds(task['start'])
        end_seconds = time_utils.time_str_to_seconds(task['end'])
        duration = end_seconds - start_seconds
        total_task_duration += duration

    # 构建任务位置映射表
    # 每个任务记录:原始时间区间 -> 紧凑排列后的百分比区间
    task_positions = []
    cumulative_duration = 0

    for task in sorted_tasks:
        start_seconds = time_utils.time_str_to_seconds(task['start'])
        end_seconds = time_utils.time_str_to_seconds(task['end'])
        duration = end_seconds - start_seconds

        # 计算该任务在紧凑排列中的百分比位置
        start_percentage = cumulative_duration / total_task_duration if total_task_duration > 0 else 0
        end_percentage = (cumulative_duration + duration) / total_task_duration if total_task_duration > 0 else 0

        task_positions.append({
            'task': task,
            'original_start': start_seconds,
            'original_end': end_seconds,
            'compact_start_pct': start_percentage,
            'compact_end_pct': end_percentage
        })

        cumulative_duration += duration

    # 保存时间范围信息(用于日志)
    time_range_start = time_utils.time_str_to_seconds(sorted_tasks[0]['start'])
    time_range_end = time_utils.time_str_to_seconds(sorted_tasks[-1]['end'])

    logger.info(f"紧凑模式: {len(sorted_tasks)}个任务, 总时长{total_task_duration//3600}小时{(total_task_duration%3600)//60}分钟")

    return {
        'task_positions': task_positions,
        'time_range_start': time_range_start,
        'time_range_end': time_range_end,
        'time_range_duration': total_task_duration
    }
