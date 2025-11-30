"""
时间块标识工具
为时间块生成稳定的 ID，确保数据库、UI 与统计模块之间一致。
"""

from __future__ import annotations

import hashlib
from typing import Dict, Any, List


def generate_time_block_id(task: Dict[str, Any], fallback_suffix: int | None = None) -> str:
    """根据任务信息生成稳定 ID。

    Args:
        task: 时间块字典
        fallback_suffix: 当缺少关键信息时附加的索引值
    """
    if not isinstance(task, dict):
        return "time-block-unknown"

    # 优先使用显式 ID 字段
    for key in ("time_block_id", "id", "task_id"):
        value = task.get(key)
        if value:
            return str(value)

    parts: List[str] = []
    for key in ("task", "name", "start", "end"):
        value = task.get(key)
        if value:
            parts.append(str(value).strip())

    if fallback_suffix is not None:
        parts.append(str(fallback_suffix))

    base = "|".join(parts)
    if not base:
        base = f"default|{fallback_suffix if fallback_suffix is not None else '0'}|{id(task)}"

    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def legacy_time_block_keys(task: Dict[str, Any]) -> List[str]:
    """返回旧版本中可能被用作标识符的字段组合，便于兼容历史数据。"""
    if not isinstance(task, dict):
        return []

    keys: List[str] = []
    for key in ("task", "name"):
        value = task.get(key)
        if value:
            value_str = str(value)
            if value_str not in keys:
                keys.append(value_str)
    return keys
