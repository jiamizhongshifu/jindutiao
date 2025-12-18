"""
自动推理引擎 (AutoInferenceEngine)

核心功能:
1. 后台自动运行,每5分钟执行一次推理
2. 基于应用使用记录,自动识别任务模式
3. 生成推理任务并保存到数据库
4. 实时更新UI显示

设计理念:
- 自动化优先: 用户无需手动触发
- 实时反馈: 数据实时更新
- 渐进式确认: AI先推理,用户可选择性调整
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger("gaiya.core.auto_inference_engine")


class AutoInferenceEngine(QObject):
    """自动推理引擎 - 方案A核心实现"""

    # 信号定义
    inference_completed = Signal(list)  # 推理完成,发送推理结果列表
    inference_failed = Signal(str)      # 推理失败,发送错误信息

    def __init__(self, db_manager, behavior_analyzer=None, interval_minutes=5):
        """
        初始化自动推理引擎

        Args:
            db_manager: 数据库管理器 (gaiya.data.db_manager.db)
            behavior_analyzer: 行为分析器 (可选,用于高级分析)
            interval_minutes: 推理间隔(分钟),默认5分钟
        """
        super().__init__()

        self.db = db_manager
        self.behavior_analyzer = behavior_analyzer
        self.interval_minutes = interval_minutes

        # 推理状态
        self.is_running = False
        self.last_inference_time = None
        self.inferred_tasks = []  # 存储推理结果

        # 定时器
        self.inference_timer = QTimer()
        self.inference_timer.timeout.connect(self.run_inference)

        # 内置规则库(从 inference_rules.py 导入)
        self.rules = self._load_inference_rules()

        logger.info(f"自动推理引擎已初始化 (间隔: {interval_minutes}分钟)")

    def start(self):
        """启动自动推理引擎"""
        if self.is_running:
            logger.warning("自动推理引擎已在运行")
            return

        self.is_running = True

        # 启动时立即执行一次推理
        self.run_inference()

        # 启动定时器
        self.inference_timer.start(self.interval_minutes * 60 * 1000)

        logger.info("自动推理引擎已启动")

    def stop(self):
        """停止自动推理引擎"""
        self.is_running = False
        self.inference_timer.stop()
        logger.info("自动推理引擎已停止")

    def run_inference(self):
        """执行推理任务 (核心方法)"""
        if not self.is_running:
            return

        try:
            start_time = datetime.now()
            logger.info(f"[自动推理] 开始执行推理...")

            # 1. 获取今日所有应用使用记录 (从0点到现在)
            now = datetime.now()
            minutes_since_midnight = now.hour * 60 + now.minute + 1
            recent_activities = self._get_recent_activities(minutes=minutes_since_midnight)

            if not recent_activities:
                logger.info("[自动推理] 无活动记录,跳过本次推理")
                return

            logger.info(f"[自动推理] 获取到 {len(recent_activities)} 条活动记录")

            # 2. 分析应用组合模式
            patterns = self._analyze_app_combinations(recent_activities)
            logger.info(f"[自动推理] 识别到 {len(patterns)} 个模式")

            # 3. 基于模式生成推理任务
            inferred_tasks = self._infer_tasks(patterns)
            logger.info(f"[自动推理] 生成 {len(inferred_tasks)} 个推理任务")

            # 4. 保存推理结果到内存 (不保存到数据库,仅展示)
            self.inferred_tasks = inferred_tasks

            # 5. 发射信号通知UI更新
            self.inference_completed.emit(inferred_tasks)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[自动推理] 推理完成,耗时: {elapsed:.2f}秒")

            self.last_inference_time = datetime.now()

        except Exception as e:
            logger.error(f"[自动推理] 执行失败: {e}", exc_info=True)
            self.inference_failed.emit(str(e))

    def _get_recent_activities(self, minutes=30) -> List[Dict]:
        """
        获取最近N分钟的应用使用记录

        Returns:
            活动记录列表,按时间排序
            [
                {
                    'app_name': str,
                    'window_title': str,
                    'timestamp': datetime,
                    'duration': int (秒)
                },
                ...
            ]
        """
        try:
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes)

            # 从数据库获取活动记录
            records = self.db.get_today_activity_records()

            # 过滤时间范围
            recent_records = []
            for record in records:
                # 数据库返回的timestamp可能是float或str
                timestamp_value = record['timestamp']
                if isinstance(timestamp_value, str):
                    timestamp = datetime.fromisoformat(timestamp_value)
                elif isinstance(timestamp_value, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp_value)
                else:
                    logger.warning(f"无效的时间戳类型: {type(timestamp_value)}, 跳过记录")
                    continue

                if start_time <= timestamp <= end_time:
                    recent_records.append({
                        'app_name': record['app_name'],
                        'window_title': record.get('window_title', ''),
                        'timestamp': timestamp,
                        'duration': record.get('duration', 0)
                    })

            # 按时间排序
            recent_records.sort(key=lambda x: x['timestamp'])

            return recent_records

        except Exception as e:
            logger.error(f"获取活动记录失败: {e}")
            return []

    def _analyze_app_combinations(self, activities: List[Dict]) -> List[Dict]:
        """
        分析应用组合模式

        算法:
        1. 时间窗口分析 (15分钟内的应用组合)
        2. 识别高频应用组合
        3. 匹配内置规则库

        Returns:
            模式列表
            [
                {
                    'type': 'coding',
                    'apps': ['vscode', 'chrome'],
                    'confidence': 0.9,
                    'start_time': datetime,
                    'end_time': datetime
                },
                ...
            ]
        """
        patterns = []
        time_window = 15 * 60  # 15分钟时间窗口

        # 按时间窗口分组活动
        windows = self._group_by_time_window(activities, time_window)

        for window_start, window_activities in windows.items():
            # 统计窗口内的应用使用情况
            app_usage = defaultdict(int)
            for activity in window_activities:
                app_name = activity['app_name'].lower()
                # 移除 .exe 后缀以便与规则库匹配
                if app_name.endswith('.exe'):
                    app_name = app_name[:-4]
                app_usage[app_name] += activity.get('duration', 60)

            # 匹配规则库
            matched_rule = self._match_rule(app_usage, window_activities)

            if matched_rule:
                pattern = {
                    'type': matched_rule['type'],
                    'task_name': matched_rule['task_name'],
                    'apps': list(app_usage.keys()),
                    'confidence': matched_rule['confidence'],
                    'start_time': window_start,
                    'end_time': window_start + timedelta(seconds=time_window),
                    'total_duration': sum(app_usage.values())
                }
                patterns.append(pattern)

        return patterns

    def _group_by_time_window(self, activities: List[Dict], window_seconds: int) -> Dict:
        """将活动按时间窗口分组"""
        windows = defaultdict(list)

        if not activities:
            return windows

        # 以第一个活动的时间为起点
        base_time = activities[0]['timestamp']

        for activity in activities:
            # 计算该活动属于哪个时间窗口
            time_diff = (activity['timestamp'] - base_time).total_seconds()
            window_index = int(time_diff // window_seconds)
            window_start = base_time + timedelta(seconds=window_index * window_seconds)

            windows[window_start].append(activity)

        return windows

    def _match_rule(self, app_usage: Dict, activities: List[Dict]) -> Optional[Dict]:
        """
        匹配内置规则库

        Args:
            app_usage: 应用使用时长统计 {'vscode': 600, 'chrome': 300}
            activities: 活动记录列表

        Returns:
            匹配的规则,或 None
        """
        # 遍历规则库
        for rule_name, rule in self.rules.items():
            # 检查是否有规则中的应用
            rule_apps = [app.lower() for app in rule.get('apps', [])]
            used_apps = set(app_usage.keys())

            # 匹配主应用
            if any(app in used_apps for app in rule_apps):
                # 检查并发应用 (可选)
                concurrent_apps = [app.lower() for app in rule.get('concurrent_apps', [])]

                # 如果有concurrent_apps要求,检查是否满足
                if concurrent_apps:
                    if any(app in used_apps for app in concurrent_apps):
                        return rule
                else:
                    return rule

        return None

    def _infer_tasks(self, patterns: List[Dict]) -> List[Dict]:
        """
        基于模式生成推理任务

        Returns:
            推理任务列表
            [
                {
                    'name': '代码开发',
                    'type': 'work',
                    'confidence': 0.9,
                    'start_time': '14:30',
                    'end_time': '15:00',
                    'duration_minutes': 30,
                    'apps': ['vscode', 'chrome'],
                    'auto_generated': True
                },
                ...
            ]
        """
        tasks = []

        for pattern in patterns:
            task = {
                'name': pattern['task_name'],
                'type': pattern['type'],
                'confidence': pattern['confidence'],
                'start_time': pattern['start_time'].strftime('%H:%M'),
                'end_time': pattern['end_time'].strftime('%H:%M'),
                'duration_minutes': int(pattern['total_duration'] / 60),
                'apps': pattern['apps'][:3],  # 最多显示3个应用
                'auto_generated': True,
                'timestamp': pattern['start_time'].isoformat()
            }
            tasks.append(task)

        # 合并相邻的相同任务
        tasks = self._merge_adjacent_tasks(tasks)

        return tasks

    def _merge_adjacent_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """合并相邻的相同类型任务"""
        if len(tasks) <= 1:
            return tasks

        merged = []
        current_task = tasks[0].copy()

        for next_task in tasks[1:]:
            # 如果任务类型相同且时间相邻(间隔<5分钟)
            if (current_task['name'] == next_task['name'] and
                self._is_adjacent(current_task['end_time'], next_task['start_time'])):
                # 合并任务
                current_task['end_time'] = next_task['end_time']
                current_task['duration_minutes'] += next_task['duration_minutes']
                current_task['apps'] = list(set(current_task['apps'] + next_task['apps']))[:3]
            else:
                merged.append(current_task)
                current_task = next_task.copy()

        merged.append(current_task)
        return merged

    def _is_adjacent(self, end_time_str: str, start_time_str: str) -> bool:
        """检查两个时间是否相邻(间隔<5分钟)"""
        try:
            end_time = datetime.strptime(end_time_str, '%H:%M')
            start_time = datetime.strptime(start_time_str, '%H:%M')
            diff = (start_time - end_time).total_seconds()
            return 0 <= diff <= 300  # 5分钟
        except ValueError:
            return False

    def _load_inference_rules(self) -> Dict:
        """
        加载内置推理规则库

        从 gaiya/core/inference_rules.py 导入
        如果文件不存在,使用默认规则
        """
        try:
            from gaiya.core.inference_rules import INFERENCE_RULES
            logger.info(f"成功加载推理规则库: {len(INFERENCE_RULES)} 条规则")
            return INFERENCE_RULES
        except ImportError:
            logger.warning("inference_rules.py 不存在,使用默认规则")
            return self._get_default_rules()

    def _get_default_rules(self) -> Dict:
        """获取默认推理规则(内置)"""
        return {
            'coding': {
                'apps': ['vscode', 'pycharm', 'visual studio', 'sublime text', 'idea'],
                'concurrent_apps': ['chrome', 'firefox', 'edge'],
                'task_name': '代码开发',
                'type': 'work',
                'confidence': 0.9
            },
            'writing': {
                'apps': ['word', 'powerpoint', 'excel', 'notion', 'typora', 'obsidian'],
                'task_name': '文档编写',
                'type': 'work',
                'confidence': 0.85
            },
            'design': {
                'apps': ['photoshop', 'figma', 'sketch', 'illustrator', 'xd'],
                'task_name': '设计创作',
                'type': 'work',
                'confidence': 0.9
            },
            'meeting': {
                'apps': ['zoom', 'teams', 'dingtalk', 'wechat', 'feishu'],
                'task_name': '会议/沟通',
                'type': 'work',
                'confidence': 0.95
            },
            'browsing': {
                'apps': ['chrome', 'firefox', 'edge', 'safari'],
                'task_name': '网页浏览',
                'type': 'neutral',
                'confidence': 0.7
            }
        }

    def get_today_inferred_tasks(self) -> List[Dict]:
        """获取今日推理任务列表"""
        return self.inferred_tasks

    def clear_inferred_tasks(self):
        """清空推理任务"""
        self.inferred_tasks = []
        logger.info("已清空推理任务")
