"""
任务完成推理调度器

负责:
1. 每日定时执行任务完成推理
2. 批量处理所有时间块
3. 保存推理结果到数据库
4. 触发批量确认UI
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path
import threading
import time

logger = logging.getLogger("gaiya.services.task_completion_scheduler")


class TaskCompletionScheduler:
    """任务完成推理调度器"""

    def __init__(self, db_manager, behavior_model, inference_engine, config: Dict,
                 ui_trigger_callback: Optional[callable] = None):
        """
        初始化调度器

        Args:
            db_manager: 数据库管理器
            behavior_model: 用户行为模型
            inference_engine: 推理引擎
            config: 调度配置
                {
                    'enabled': bool,              # 是否启用自动推理
                    'trigger_time': str,          # 触发时间 (HH:MM)
                    'trigger_on_startup': bool,   # 启动时是否推理昨日数据
                    'auto_confirm_threshold': int # 自动确认阈值 (置信度high且完成度>threshold)
                }
            ui_trigger_callback: UI触发回调函数 (date, unconfirmed_tasks)
        """
        self.db = db_manager
        self.model = behavior_model
        self.engine = inference_engine
        self.config = config
        self.ui_trigger_callback = ui_trigger_callback

        # 调度状态
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.last_run_date: Optional[str] = None

        logger.info(f"任务完成推理调度器已初始化: {config}")

    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行,跳过启动")
            return

        if not self.config.get('enabled', True):
            logger.info("任务完成推理调度器已禁用")
            return

        self.is_running = True

        # 启动时推理昨日数据 (可选)
        if self.config.get('trigger_on_startup', False):
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            logger.info(f"启动时推理昨日数据: {yesterday}")
            threading.Thread(
                target=self._run_daily_inference,
                args=(yesterday,),
                daemon=True
            ).start()

        # 启动定时调度线程
        self.scheduler_thread = threading.Thread(
            target=self._schedule_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        logger.info("任务完成推理调度器已启动")

    def stop(self):
        """停止调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("任务完成推理调度器已停止")

    def reload_config(self, new_config: Dict):
        """
        重新加载配置

        Args:
            new_config: 新的调度配置
        """
        self.config = new_config
        logger.info(f"任务完成推理调度器配置已更新: {new_config}")

    def _schedule_loop(self):
        """调度循环 - 每分钟检查是否到达触发时间"""
        trigger_time = self.config.get('trigger_time', '21:00')

        while self.is_running:
            try:
                current_time = datetime.now()
                current_time_str = current_time.strftime('%H:%M')
                current_date = current_time.strftime('%Y-%m-%d')

                # 检查是否到达触发时间
                if current_time_str == trigger_time:
                    # 检查今天是否已运行
                    if self.last_run_date != current_date:
                        logger.info(f"到达触发时间 {trigger_time},开始执行每日推理")
                        self._run_daily_inference(current_date)
                        self.last_run_date = current_date

                # 每分钟检查一次
                time.sleep(60)

            except Exception as e:
                logger.error(f"调度循环异常: {e}", exc_info=True)
                time.sleep(60)

    def _run_daily_inference(self, date: str):
        """
        执行每日推理

        Args:
            date: 日期 (YYYY-MM-DD)
        """
        try:
            logger.info(f"开始执行每日推理: {date}")

            # 1. 获取当日所有任务计划
            tasks = self._get_daily_tasks(date)

            if not tasks:
                logger.info(f"日期 {date} 没有任务计划,跳过推理")
                return

            logger.info(f"找到 {len(tasks)} 个任务,开始推理...")

            # 2. 批量推理所有任务
            inference_results = []
            for task in tasks:
                try:
                    result = self._infer_single_task(date, task)
                    if result:
                        inference_results.append(result)
                except Exception as e:
                    logger.error(f"推理任务失败 ({task['name']}): {e}", exc_info=True)

            logger.info(f"推理完成: {len(inference_results)}/{len(tasks)} 个任务")

            # 3. 保存推理结果到数据库
            saved_count = self._save_inference_results(date, inference_results)
            logger.info(f"保存推理结果: {saved_count} 条记录")

            # 4. 检查是否需要自动确认
            auto_confirmed_count = self._auto_confirm_high_confidence(date)
            if auto_confirmed_count > 0:
                logger.info(f"自动确认: {auto_confirmed_count} 个高置信度任务")

            # 5. 触发批量确认UI (如果有未确认的任务)
            # 🔥 如果启用了完全自动确认,则永远不触发UI弹窗
            auto_confirm_all = self.config.get('auto_confirm_all', False)
            if auto_confirm_all:
                logger.info("✅ 完全自动确认模式已启用,所有任务已自动处理,不触发确认弹窗")
                return  # 直接返回,不触发UI

            # 否则,检查是否有未确认的任务需要人工确认
            unconfirmed_count = self._get_unconfirmed_count(date)
            if unconfirmed_count > 0:
                logger.info(f"待确认任务: {unconfirmed_count} 个,触发批量确认UI")
                self._trigger_batch_confirmation_ui(date)
            else:
                logger.info("所有任务已确认,无需触发UI")

        except Exception as e:
            logger.error(f"每日推理执行失败: {e}", exc_info=True)

    def _get_daily_tasks(self, date: str) -> List[Dict]:
        """
        获取指定日期的所有任务计划

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            [{'time_block_id': str, 'name': str, 'task_type': str,
              'start_time': str, 'end_time': str, 'duration_minutes': int}]
        """
        # TODO: 从配置文件或数据库读取任务计划
        # 这里需要集成现有的任务管理系统
        # 临时实现:从 tasks.json 读取

        from gaiya.utils.data_loader import load_daily_tasks

        try:
            # 加载任务配置
            tasks_data = load_daily_tasks()

            if not tasks_data:
                return []

            # 转换为统一格式
            daily_tasks = []
            for time_block_id, task_info in tasks_data.items():
                # 解析任务信息
                task = {
                    'time_block_id': time_block_id,
                    'name': task_info.get('name', '未命名任务'),
                    'task_type': task_info.get('task_type', 'other'),
                    'start_time': task_info.get('start_time', '00:00'),
                    'end_time': task_info.get('end_time', '00:00'),
                    'duration_minutes': task_info.get('duration_minutes', 0)
                }
                daily_tasks.append(task)

            return daily_tasks

        except Exception as e:
            logger.error(f"读取任务计划失败: {e}", exc_info=True)
            return []

    def _infer_single_task(self, date: str, task: Dict) -> Optional[Dict]:
        """
        推理单个任务的完成情况

        Args:
            date: 日期
            task: 任务信息

        Returns:
            推理结果或None
        """
        try:
            # 调用推理引擎
            result = self.engine.infer_task_completion(
                time_block_id=task['time_block_id'],
                date=date,
                task_name=task['name'],
                planned_start=task['start_time'],
                planned_end=task['end_time']
            )

            # 附加任务信息
            result['task'] = task

            logger.debug(
                f"推理任务 {task['name']}: "
                f"完成度={result['completion']}%, "
                f"置信度={result['confidence']}"
            )

            return result

        except Exception as e:
            logger.error(f"推理任务失败 ({task['name']}): {e}", exc_info=True)
            return None

    def _save_inference_results(self, date: str, results: List[Dict]) -> int:
        """
        批量保存推理结果到数据库

        Args:
            date: 日期
            results: 推理结果列表

        Returns:
            保存成功的记录数
        """
        saved_count = 0

        for result in results:
            try:
                task = result['task']

                # 检查是否已存在记录
                existing = self.db.get_task_completion_by_block(
                    date, task['time_block_id']
                )

                if existing:
                    logger.debug(f"任务 {task['name']} 已存在推理记录,跳过")
                    continue

                # 创建新记录
                self.db.create_task_completion(
                    date=date,
                    time_block_id=task['time_block_id'],
                    task_data={
                        'name': task['name'],
                        'task_type': task.get('task_type'),
                        'start_time': task['start_time'],
                        'end_time': task['end_time'],
                        'duration_minutes': task['duration_minutes']
                    },
                    inference_result=result
                )

                saved_count += 1

            except Exception as e:
                logger.error(f"保存推理结果失败 ({result.get('task', {}).get('name')}): {e}")

        return saved_count

    def _auto_confirm_high_confidence(self, date: str) -> int:
        """
        自动确认任务

        支持两种模式:
        1. auto_confirm_all=True: 完全自动确认所有任务，不弹窗
        2. auto_confirm_threshold>0: 仅自动确认高置信度任务

        Args:
            date: 日期

        Returns:
            自动确认的任务数量
        """
        # 完全自动确认模式: 所有任务自动确认，不弹窗
        auto_confirm_all = self.config.get('auto_confirm_all', False)
        logger.info(f"[自动确认] auto_confirm_all={auto_confirm_all}, 配置={self.config}")
        if auto_confirm_all:
            try:
                unconfirmed = self.db.get_unconfirmed_task_completions(date)
                for task_completion in unconfirmed:
                    self.db.update_task_completion_confirmation(
                        completion_id=task_completion['id'],
                        user_confirmed=True,
                        user_corrected=False,
                        user_note='完全自动确认'
                    )
                if unconfirmed:
                    logger.info(f"完全自动确认: {len(unconfirmed)} 个任务")
                return len(unconfirmed)
            except Exception as e:
                logger.error(f"完全自动确认失败: {e}", exc_info=True)
                return 0

        # 原有逻辑: 仅自动确认高置信度任务
        threshold = self.config.get('auto_confirm_threshold', 0)

        # 如果阈值为0,则不自动确认
        if threshold <= 0:
            return 0

        try:
            # 查询所有未确认的高置信度任务
            unconfirmed = self.db.get_unconfirmed_task_completions(date)

            auto_confirmed_count = 0
            for task_completion in unconfirmed:
                # 检查是否满足自动确认条件
                if (task_completion.get('confidence_level') == 'high' and
                    task_completion.get('completion_percentage', 0) >= threshold):

                    # 自动确认
                    self.db.update_task_completion_confirmation(
                        completion_id=task_completion['id'],
                        user_confirmed=True,
                        user_corrected=False,
                        user_note='自动确认(高置信度)'
                    )

                    auto_confirmed_count += 1
                    logger.debug(
                        f"自动确认任务: {task_completion['task_name']} "
                        f"(完成度={task_completion['completion_percentage']}%)"
                    )

            return auto_confirmed_count

        except Exception as e:
            logger.error(f"自动确认失败: {e}", exc_info=True)
            return 0

    def _get_unconfirmed_count(self, date: str) -> int:
        """
        获取未确认的任务数量

        Args:
            date: 日期

        Returns:
            未确认任务数量
        """
        try:
            unconfirmed = self.db.get_unconfirmed_task_completions(date)
            return len(unconfirmed)
        except Exception as e:
            logger.error(f"查询未确认任务失败: {e}", exc_info=True)
            return 0

    def _trigger_batch_confirmation_ui(self, date: str):
        """
        触发批量确认UI

        Args:
            date: 日期
        """
        # 获取未确认的任务
        unconfirmed_tasks = self.db.get_unconfirmed_task_completions(date)

        if not unconfirmed_tasks:
            logger.info(f"日期 {date} 没有未确认任务,跳过UI触发")
            return

        # 调用UI回调
        if self.ui_trigger_callback:
            try:
                logger.info(f"触发批量确认UI: {date}, {len(unconfirmed_tasks)} 个未确认任务")
                self.ui_trigger_callback(date, unconfirmed_tasks)
            except Exception as e:
                logger.error(f"触发UI回调失败: {e}", exc_info=True)
        else:
            logger.warning("UI触发回调未设置,无法显示批量确认窗口")

    def manual_trigger(self, date: Optional[str] = None):
        """
        手动触发推理 (用于托盘菜单或调试)

        Args:
            date: 日期,默认为今天
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"手动触发每日推理: {date}")
        threading.Thread(
            target=self._run_daily_inference,
            args=(date,),
            daemon=True
        ).start()

    def get_status(self) -> Dict:
        """
        获取调度器状态

        Returns:
            {'is_running': bool, 'last_run_date': str, 'config': dict}
        """
        return {
            'is_running': self.is_running,
            'last_run_date': self.last_run_date,
            'config': self.config
        }
