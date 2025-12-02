"""
任务完成推理调度器单元测试

测试范围:
1. 调度器初始化和配置
2. 任务加载和推理触发
3. 自动确认高置信度任务
4. 手动触发推理
"""
import unittest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gaiya.data.db_manager import DatabaseManager
from gaiya.services.user_behavior_model import UserBehaviorModel
from gaiya.services.task_inference_engine import SignalCollector, InferenceEngine
from gaiya.services.task_completion_scheduler import TaskCompletionScheduler


class TestTaskCompletionScheduler(unittest.TestCase):
    """测试任务完成推理调度器"""

    def setUp(self):
        """每个测试前创建测试环境"""
        import shutil
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / 'test.db'
        self.model_path = self.temp_dir / 'model.json'

        # 创建测试任务文件
        self.tasks_file = self.temp_dir / 'tasks.json'
        test_tasks = [
            {"start": "09:00", "end": "12:00", "task": "上午工作", "color": "#4CAF50"},
            {"start": "14:00", "end": "18:00", "task": "下午工作", "color": "#2196F3"}
        ]
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(test_tasks, f)

        # 初始化数据库和模型
        self.db = DatabaseManager(self.db_path)
        self.model = UserBehaviorModel(self.model_path)

        # 初始化任务模式
        self.model.initialize_task_pattern(
            task_name='上午工作',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        # 初始化推理引擎
        collector = SignalCollector(self.db, self.model)
        self.engine = InferenceEngine(collector)

        # 调度器配置
        self.scheduler_config = {
            'enabled': True,
            'trigger_time': '21:00',
            'trigger_on_startup': False,
            'auto_confirm_threshold': 0
        }

    def tearDown(self):
        """每个测试后清理资源"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        self.assertFalse(scheduler.is_running)
        self.assertIsNone(scheduler.last_run_date)
        self.assertEqual(scheduler.config['trigger_time'], '21:00')

    def test_scheduler_start_stop(self):
        """测试调度器启动和停止"""
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # 启动
        scheduler.start()
        self.assertTrue(scheduler.is_running)
        self.assertIsNotNone(scheduler.scheduler_thread)

        # 停止
        scheduler.stop()
        self.assertFalse(scheduler.is_running)

    def test_get_daily_tasks(self):
        """测试获取每日任务"""
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # Mock tasks file path
        import gaiya.utils.data_loader as loader
        original_get_app_dir = loader.path_utils.get_app_dir

        def mock_get_app_dir():
            return self.temp_dir

        loader.path_utils.get_app_dir = mock_get_app_dir

        try:
            tasks = scheduler._get_daily_tasks('2024-01-01')

            # 验证任务数量
            self.assertEqual(len(tasks), 2)

            # 验证第一个任务
            task1 = tasks[0]
            self.assertEqual(task1['name'], '上午工作')
            self.assertEqual(task1['start_time'], '09:00')
            self.assertEqual(task1['end_time'], '12:00')
            self.assertEqual(task1['duration_minutes'], 180)

        finally:
            loader.path_utils.get_app_dir = original_get_app_dir

    def test_infer_single_task_with_focus(self):
        """测试推理单个任务 - 有专注会话"""
        date = datetime.now().strftime('%Y-%m-%d')
        time_block_id = 'time-block-0'

        # 创建专注会话
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO focus_sessions
            (id, time_block_id, start_time, end_time, duration_minutes, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'session-1',
            time_block_id,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(minutes=25)).isoformat(),
            25,
            'COMPLETED'
        ))
        conn.commit()
        conn.close()

        # 创建调度器
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # 推理任务
        task = {
            'time_block_id': time_block_id,
            'name': '上午工作',
            'task_type': 'work',
            'start_time': '09:00',
            'end_time': '12:00',
            'duration_minutes': 180
        }

        result = scheduler._infer_single_task(date, task)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result['completion'], 100)
        self.assertEqual(result['confidence'], 'high')
        self.assertIn('task', result)

    def test_save_inference_results(self):
        """测试保存推理结果"""
        date = datetime.now().strftime('%Y-%m-%d')

        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # 构造推理结果
        results = [
            {
                'task': {
                    'time_block_id': 'time-block-0',
                    'name': '上午工作',
                    'task_type': 'work',
                    'start_time': '09:00',
                    'end_time': '12:00',
                    'duration_minutes': 180
                },
                'completion': 85,
                'confidence': 'high',
                'actual_start': '09:10',
                'actual_end': '11:50',
                'actual_duration': 160,
                'inference_data': '{"signal_count": 2}'
            }
        ]

        # 保存
        saved_count = scheduler._save_inference_results(date, results)

        # 验证
        self.assertEqual(saved_count, 1)

        # 查询数据库验证
        saved_record = self.db.get_task_completion_by_block(date, 'time-block-0')
        self.assertIsNotNone(saved_record)
        self.assertEqual(saved_record['task_name'], '上午工作')
        self.assertEqual(saved_record['completion_percentage'], 85)

    def test_auto_confirm_high_confidence(self):
        """测试自动确认高置信度任务"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 创建测试数据 - 高置信度任务
        self.db.create_task_completion(
            date=date,
            time_block_id='time-block-0',
            task_data={
                'name': '上午工作',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '12:00',
                'duration_minutes': 180
            },
            inference_result={
                'completion': 95,
                'confidence': 'high',
                'actual_start': '09:00',
                'actual_end': '12:00',
                'actual_duration': 180,
                'inference_data': '{}'
            }
        )

        # 配置自动确认阈值
        config_with_threshold = self.scheduler_config.copy()
        config_with_threshold['auto_confirm_threshold'] = 90

        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=config_with_threshold
        )

        # 执行自动确认
        confirmed_count = scheduler._auto_confirm_high_confidence(date)

        # 验证
        self.assertEqual(confirmed_count, 1)

        # 查询数据库验证
        record = self.db.get_task_completion_by_block(date, 'time-block-0')
        self.assertTrue(record['user_confirmed'])

    def test_auto_confirm_disabled_when_threshold_is_zero(self):
        """测试阈值为0时不自动确认"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 创建测试数据
        self.db.create_task_completion(
            date=date,
            time_block_id='time-block-0',
            task_data={
                'name': '上午工作',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '12:00',
                'duration_minutes': 180
            },
            inference_result={
                'completion': 95,
                'confidence': 'high',
                'actual_start': '09:00',
                'actual_end': '12:00',
                'actual_duration': 180,
                'inference_data': '{}'
            }
        )

        # 阈值为0
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # 执行自动确认
        confirmed_count = scheduler._auto_confirm_high_confidence(date)

        # 验证: 阈值为0时不应自动确认
        self.assertEqual(confirmed_count, 0)

        # 查询数据库验证
        record = self.db.get_task_completion_by_block(date, 'time-block-0')
        self.assertFalse(record['user_confirmed'])

    def test_get_unconfirmed_count(self):
        """测试获取未确认任务数量"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 创建2个未确认任务
        for i in range(2):
            self.db.create_task_completion(
                date=date,
                time_block_id=f'time-block-{i}',
                task_data={
                    'name': f'任务{i}',
                    'task_type': 'work',
                    'start_time': '09:00',
                    'end_time': '10:00',
                    'duration_minutes': 60
                },
                inference_result={
                    'completion': 80,
                    'confidence': 'medium',
                    'actual_start': '09:00',
                    'actual_end': '10:00',
                    'actual_duration': 60,
                    'inference_data': '{}'
                }
            )

        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # 获取未确认数量
        count = scheduler._get_unconfirmed_count(date)

        # 验证
        self.assertEqual(count, 2)

    def test_manual_trigger(self):
        """测试手动触发推理"""
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # 手动触发 (不会阻塞,因为是异步执行)
        date = datetime.now().strftime('%Y-%m-%d')
        scheduler.manual_trigger(date)

        # 等待一小段时间让线程开始执行
        time.sleep(0.1)

        # 验证:由于没有实际数据,不会创建推理记录,但不应该抛出异常
        # 这个测试主要验证方法可以正常调用
        self.assertTrue(True)

    def test_get_status(self):
        """测试获取调度器状态"""
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=self.model,
            inference_engine=self.engine,
            config=self.scheduler_config
        )

        # 启动前
        status = scheduler.get_status()
        self.assertFalse(status['is_running'])
        self.assertIsNone(status['last_run_date'])
        self.assertEqual(status['config']['trigger_time'], '21:00')

        # 启动后
        scheduler.start()
        status = scheduler.get_status()
        self.assertTrue(status['is_running'])

        # 停止
        scheduler.stop()


if __name__ == '__main__':
    unittest.main()
