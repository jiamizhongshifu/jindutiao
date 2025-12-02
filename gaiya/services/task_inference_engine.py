"""
任务完成推理引擎

负责收集多维度信号并推断任务完成情况:
1. 信号收集: 专注会话、活动追踪、应用使用、时间匹配
2. 加权计算: 多维度信号加权融合
3. 完成度推断: 基于信号强度计算完成百分比
4. 置信度评估: high/medium/low/unknown
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger("gaiya.services.task_inference_engine")


class SignalCollector:
    """信号收集器 - 从多个数据源收集任务相关信号"""

    def __init__(self, db_manager, behavior_model):
        """
        初始化信号收集器

        Args:
            db_manager: 数据库管理器
            behavior_model: 用户行为模型
        """
        self.db = db_manager
        self.model = behavior_model

    def collect_focus_signal(self, time_block_id: str, date: str) -> Dict:
        """
        收集专注会话信号 (最强信号, 权重 1.0)

        Args:
            time_block_id: 时间块ID
            date: 日期 (YYYY-MM-DD)

        Returns:
            {
                'has_focus': bool,
                'focus_duration': int (分钟),
                'focus_sessions': int,
                'weight': float
            }
        """
        # 查询该时间块的所有完成的专注会话
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as session_count,
                SUM(duration_minutes) as total_duration
            FROM focus_sessions
            WHERE time_block_id = ?
            AND DATE(start_time) = ?
            AND status = 'COMPLETED'
        ''', (time_block_id, date))

        row = cursor.fetchone()
        conn.close()

        if row and row[0] > 0:
            return {
                'has_focus': True,
                'focus_duration': row[1] or 0,
                'focus_sessions': row[0],
                'weight': 1.0,
                'signal_type': 'focus'
            }
        else:
            return {
                'has_focus': False,
                'focus_duration': 0,
                'focus_sessions': 0,
                'weight': 1.0,
                'signal_type': 'focus'
            }

    def collect_activity_signal(self, time_block_id: str, date: str,
                                task_name: str, planned_start: str,
                                planned_end: str) -> Dict:
        """
        收集活动追踪信号 (应用使用情况)

        Args:
            time_block_id: 时间块ID
            date: 日期
            task_name: 任务名称
            planned_start: 计划开始时间 (HH:MM)
            planned_end: 计划结束时间 (HH:MM)

        Returns:
            {
                'primary_apps': [{'app': str, 'duration': int, 'weight': float}],
                'secondary_apps': [{'app': str, 'duration': int, 'weight': float}],
                'total_active_time': int (秒),
                'signal_type': 'activity'
            }
        """
        # 计算时间范围
        start_datetime = datetime.strptime(f"{date} {planned_start}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{date} {planned_end}", "%Y-%m-%d %H:%M")

        # 查询该时间范围内的活动会话
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                process_name,
                SUM(duration_seconds) as total_seconds
            FROM activity_sessions
            WHERE start_time >= ? AND start_time < ?
            GROUP BY process_name
            ORDER BY total_seconds DESC
        ''', (start_datetime.isoformat(), end_datetime.isoformat()))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {
                'primary_apps': [],
                'secondary_apps': [],
                'total_active_time': 0,
                'signal_type': 'activity'
            }

        # 获取任务模式
        task_pattern = self.model.get_task_pattern(task_name)
        typical_apps = task_pattern.get('typical_apps', {})

        primary_apps = []
        secondary_apps = []
        total_active_time = 0

        for process_name, duration_seconds in rows:
            total_active_time += duration_seconds
            duration_minutes = duration_seconds / 60

            # 跳过时间太短的应用 (<1分钟)
            if duration_minutes < 1:
                continue

            # 检查是否为已学习的应用
            if process_name in typical_apps:
                app_weight = typical_apps[process_name].get('weight', 0.5)

                # 高权重应用视为主要应用
                if app_weight >= 0.7:
                    primary_apps.append({
                        'app': process_name,
                        'duration': int(duration_minutes),
                        'weight': app_weight
                    })
                else:
                    secondary_apps.append({
                        'app': process_name,
                        'duration': int(duration_minutes),
                        'weight': app_weight
                    })
            else:
                # 未学习的应用,根据使用时长判断重要性
                if duration_minutes > 10:
                    secondary_apps.append({
                        'app': process_name,
                        'duration': int(duration_minutes),
                        'weight': 0.5  # 默认权重
                    })

        return {
            'primary_apps': primary_apps,
            'secondary_apps': secondary_apps,
            'total_active_time': total_active_time,
            'signal_type': 'activity'
        }

    def collect_time_match_signal(self, planned_start: str, planned_end: str,
                                  actual_start: Optional[str],
                                  actual_end: Optional[str]) -> Dict:
        """
        收集时间匹配度信号

        Args:
            planned_start: 计划开始时间 (HH:MM)
            planned_end: 计划结束时间 (HH:MM)
            actual_start: 实际开始时间 (HH:MM, 可选)
            actual_end: 实际结束时间 (HH:MM, 可选)

        Returns:
            {
                'time_match_score': float (0-1),
                'planned_duration': int (分钟),
                'actual_duration': int (分钟),
                'weight': float,
                'signal_type': 'time_match'
            }
        """
        # 计算计划时长
        planned_start_time = datetime.strptime(planned_start, "%H:%M")
        planned_end_time = datetime.strptime(planned_end, "%H:%M")
        planned_duration = (planned_end_time - planned_start_time).seconds / 60

        if not actual_start or not actual_end:
            # 没有实际时间数据,无法计算匹配度
            return {
                'time_match_score': 0.0,
                'planned_duration': int(planned_duration),
                'actual_duration': 0,
                'weight': 0.5,
                'signal_type': 'time_match'
            }

        # 计算实际时长
        actual_start_time = datetime.strptime(actual_start, "%H:%M")
        actual_end_time = datetime.strptime(actual_end, "%H:%M")
        actual_duration = (actual_end_time - actual_start_time).seconds / 60

        # 计算时间匹配度 (实际/计划,限制在0-1范围)
        if planned_duration > 0:
            time_match_score = min(1.0, actual_duration / planned_duration)
        else:
            time_match_score = 0.0

        return {
            'time_match_score': time_match_score,
            'planned_duration': int(planned_duration),
            'actual_duration': int(actual_duration),
            'weight': 0.5,
            'signal_type': 'time_match'
        }

    def collect_all_signals(self, time_block_id: str, date: str,
                           task_name: str, planned_start: str,
                           planned_end: str) -> Dict:
        """
        收集所有信号

        Args:
            time_block_id: 时间块ID
            date: 日期
            task_name: 任务名称
            planned_start: 计划开始时间
            planned_end: 计划结束时间

        Returns:
            {
                'focus': Dict,
                'activity': Dict,
                'time_match': Dict
            }
        """
        focus_signal = self.collect_focus_signal(time_block_id, date)

        activity_signal = self.collect_activity_signal(
            time_block_id, date, task_name, planned_start, planned_end
        )

        # 时间匹配信号需要实际时间,这里先用None
        time_signal = self.collect_time_match_signal(
            planned_start, planned_end, None, None
        )

        return {
            'focus': focus_signal,
            'activity': activity_signal,
            'time_match': time_signal
        }


class InferenceEngine:
    """推理引擎 - 基于信号计算任务完成度和置信度"""

    # 信号权重配置
    SIGNAL_WEIGHTS = {
        'focus': 1.0,           # 专注会话 - 最强信号
        'primary_app': 0.85,    # 主要应用使用
        'secondary_app': 0.60,  # 次要应用使用
        'time_match': 0.50      # 时间匹配度
    }

    def __init__(self, signal_collector: SignalCollector):
        """
        初始化推理引擎

        Args:
            signal_collector: 信号收集器实例
        """
        self.collector = signal_collector

    def calculate_completion_percentage(self, signals: Dict) -> Tuple[int, str, Dict]:
        """
        计算任务完成百分比

        Args:
            signals: 收集的所有信号

        Returns:
            (completion_percentage, confidence_level, inference_data)
            - completion_percentage: 0-100
            - confidence_level: 'high', 'medium', 'low', 'unknown'
            - inference_data: 推理详情
        """
        focus_signal = signals['focus']
        activity_signal = signals['activity']
        time_signal = signals['time_match']

        # 计算各维度得分
        scores = []
        weights = []
        details = {}

        # 1. 专注会话信号
        if focus_signal['has_focus']:
            focus_score = min(100, focus_signal['focus_duration'] / 25 * 100)  # 25分钟为基准
            scores.append(focus_score)
            weights.append(self.SIGNAL_WEIGHTS['focus'])
            details['focus_score'] = focus_score
            details['focus_duration'] = focus_signal['focus_duration']
        else:
            details['focus_score'] = 0
            details['focus_duration'] = 0

        # 2. 主要应用使用信号
        primary_apps = activity_signal['primary_apps']
        if primary_apps:
            # 计算主要应用使用时长加权得分
            primary_total_duration = sum(app['duration'] for app in primary_apps)
            primary_weighted_score = sum(
                app['duration'] * app['weight'] for app in primary_apps
            ) / primary_total_duration if primary_total_duration > 0 else 0

            primary_score = min(100, primary_weighted_score * 100)
            scores.append(primary_score)
            weights.append(self.SIGNAL_WEIGHTS['primary_app'])
            details['primary_app_score'] = primary_score
            details['primary_apps'] = [
                f"{app['app']}({app['duration']}min)" for app in primary_apps
            ]
        else:
            details['primary_app_score'] = 0
            details['primary_apps'] = []

        # 3. 次要应用使用信号
        secondary_apps = activity_signal['secondary_apps']
        if secondary_apps:
            secondary_total_duration = sum(app['duration'] for app in secondary_apps)
            secondary_weighted_score = sum(
                app['duration'] * app['weight'] for app in secondary_apps
            ) / secondary_total_duration if secondary_total_duration > 0 else 0

            secondary_score = min(100, secondary_weighted_score * 100)
            scores.append(secondary_score)
            weights.append(self.SIGNAL_WEIGHTS['secondary_app'])
            details['secondary_app_score'] = secondary_score
        else:
            details['secondary_app_score'] = 0

        # 4. 时间匹配信号
        if time_signal['time_match_score'] > 0:
            time_score = time_signal['time_match_score'] * 100
            scores.append(time_score)
            weights.append(self.SIGNAL_WEIGHTS['time_match'])
            details['time_match_score'] = time_score
        else:
            details['time_match_score'] = 0

        # 加权平均计算最终完成度
        if scores:
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            weight_sum = sum(weights)
            completion_percentage = int(weighted_sum / weight_sum)
        else:
            completion_percentage = 0

        # 计算置信度
        confidence_level = self._calculate_confidence(signals, scores, weights)

        # 保存推理数据
        inference_data = {
            'signal_count': len(scores),
            'total_weight': sum(weights),
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(
            f"推理完成: {completion_percentage}% (置信度: {confidence_level}, "
            f"信号数: {len(scores)})"
        )

        return completion_percentage, confidence_level, inference_data

    def _calculate_confidence(self, signals: Dict, scores: List[float],
                             weights: List[float]) -> str:
        """
        计算推理置信度

        Args:
            signals: 原始信号
            scores: 各维度得分
            weights: 各维度权重

        Returns:
            'high', 'medium', 'low', 'unknown'
        """
        # 无信号 -> unknown
        if not scores:
            return 'unknown'

        # 有专注会话 -> high
        if signals['focus']['has_focus']:
            return 'high'

        # 有主要应用使用且总权重 >= 0.85 -> high
        total_weight = sum(weights)
        if signals['activity']['primary_apps'] and total_weight >= 0.85:
            return 'high'

        # 有主要或次要应用使用 -> medium
        if signals['activity']['primary_apps'] or signals['activity']['secondary_apps']:
            return 'medium'

        # 仅有时间匹配信号 -> low
        if signals['time_match']['time_match_score'] > 0:
            return 'low'

        # 其他情况 -> unknown
        return 'unknown'

    def infer_task_completion(self, time_block_id: str, date: str,
                             task_name: str, planned_start: str,
                             planned_end: str) -> Dict:
        """
        推断任务完成情况

        Args:
            time_block_id: 时间块ID
            date: 日期
            task_name: 任务名称
            planned_start: 计划开始时间
            planned_end: 计划结束时间

        Returns:
            {
                'completion': int (0-100),
                'confidence': str,
                'actual_start': str,
                'actual_end': str,
                'actual_duration': int,
                'inference_data': str (JSON)
            }
        """
        # 收集所有信号
        signals = self.collector.collect_all_signals(
            time_block_id, date, task_name, planned_start, planned_end
        )

        # 计算完成度和置信度
        completion, confidence, inference_data = self.calculate_completion_percentage(signals)

        # 估算实际开始/结束时间
        actual_start = planned_start  # 简化处理,使用计划时间
        actual_end = planned_end

        # 根据活动信号调整实际时间
        if signals['activity']['total_active_time'] > 0:
            actual_duration = int(signals['activity']['total_active_time'] / 60)
        else:
            # 根据完成度估算实际时长
            planned_duration = (
                datetime.strptime(planned_end, "%H:%M") -
                datetime.strptime(planned_start, "%H:%M")
            ).seconds / 60
            actual_duration = int(planned_duration * completion / 100)

        import json
        return {
            'completion': completion,
            'confidence': confidence,
            'actual_start': actual_start,
            'actual_end': actual_end,
            'actual_duration': actual_duration,
            'inference_data': json.dumps(inference_data, ensure_ascii=False)
        }
