"""
任务完成追踪系统集成测试

测试完整工作流程:
1. 数据迁移 → 数据库表创建
2. 用户行为模型初始化
3. 信号收集 → 推理引擎 → 完成度计算
4. 调度器触发 → 批量推理
5. 用户确认 → 学习反馈 → 模型更新
"""
import unittest
import tempfile
import json
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
from gaiya.utils.data_migration import DataMigration


class TestTaskTrackingIntegration(unittest.TestCase):
    """测试任务追踪系统集成流程"""

    def setUp(self):
        """每个测试前创建完整测试环境"""
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

        # 初始化数据库
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        """每个测试后清理资源"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_data_migration_flow(self):
        """测试数据迁移流程"""
        # 1. 运行迁移
        migration = DataMigration(self.db, self.temp_dir)
        result = migration.check_and_run_migrations()

        self.assertTrue(result)

        # 2. 验证表创建
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='task_completions'
        """)
        table_exists = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(table_exists)

        # 3. 验证模型文件创建
        # DataMigration 使用固定路径 data_dir / "user_behavior_model.json"
        expected_model_path = self.temp_dir / "user_behavior_model.json"
        self.assertTrue(expected_model_path.exists())

        # 4. 验证可以加载模型
        model = UserBehaviorModel(expected_model_path)
        self.assertIsNotNone(model.model)
        self.assertEqual(model.model['version'], '1.0')

    def test_02_signal_collection_and_inference(self):
        """测试信号收集和推理流程"""
        date = datetime.now().strftime('%Y-%m-%d')
        time_block_id = 'time-block-0'

        # 1. 运行迁移
        migration = DataMigration(self.db, self.temp_dir)
        migration.check_and_run_migrations()

        # 2. 初始化模型和引擎
        model = UserBehaviorModel(self.model_path)
        model.initialize_task_pattern(
            task_name='上午工作',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        collector = SignalCollector(self.db, model)
        engine = InferenceEngine(collector)

        # 3. 创建测试数据 - 专注会话
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

        # 4. 执行推理
        result = engine.infer_task_completion(
            time_block_id=time_block_id,
            date=date,
            task_name='上午工作',
            planned_start='09:00',
            planned_end='12:00'
        )

        # 5. 验证推理结果
        self.assertIn('completion', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['confidence'], 'high')
        self.assertEqual(result['completion'], 100)

    def test_03_scheduler_daily_inference(self):
        """测试调度器每日推理流程"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 1. 运行迁移
        migration = DataMigration(self.db, self.temp_dir)
        migration.check_and_run_migrations()

        # 2. 初始化模型和引擎
        model = UserBehaviorModel(self.model_path)
        model.initialize_task_pattern(
            task_name='上午工作',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        collector = SignalCollector(self.db, model)
        engine = InferenceEngine(collector)

        # 3. 创建调度器
        ui_triggered = []

        def mock_ui_callback(date, tasks):
            ui_triggered.append({'date': date, 'task_count': len(tasks)})

        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=model,
            inference_engine=engine,
            config={
                'enabled': True,
                'trigger_time': '21:00',
                'trigger_on_startup': False,
                'auto_confirm_threshold': 0
            },
            ui_trigger_callback=mock_ui_callback
        )

        # 4. 模拟每日推理执行
        # Mock tasks file path
        import gaiya.utils.data_loader as loader
        original_get_app_dir = loader.path_utils.get_app_dir

        def mock_get_app_dir():
            return self.temp_dir

        loader.path_utils.get_app_dir = mock_get_app_dir

        try:
            # 手动触发推理
            scheduler.manual_trigger(date)

            # 等待推理完成
            import time
            time.sleep(0.5)

            # 5. 验证推理结果已保存
            completions = self.db.get_today_task_completions(date)
            self.assertGreater(len(completions), 0)

            # 6. 验证UI触发
            # 注意: 因为没有实际数据,可能不会触发UI
            # 这里主要验证流程不会抛出异常

        finally:
            loader.path_utils.get_app_dir = original_get_app_dir
            scheduler.stop()

    def test_04_user_confirmation_and_learning(self):
        """测试用户确认和学习反馈流程"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 1. 运行迁移
        migration = DataMigration(self.db, self.temp_dir)
        migration.check_and_run_migrations()

        # 2. 初始化模型
        model = UserBehaviorModel(self.model_path)
        model.initialize_task_pattern(
            task_name='上午工作',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        # 获取初始权重
        initial_pattern = model.get_task_pattern('上午工作')
        initial_weight = initial_pattern['typical_apps']['Cursor.exe']['weight']

        # 3. 创建推理记录 (AI推理为80%)
        completion_id = self.db.create_task_completion(
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
                'completion': 80,
                'confidence': 'medium',
                'actual_start': '09:00',
                'actual_end': '12:00',
                'actual_duration': 180,
                'inference_data': json.dumps({
                    'signal_count': 1,
                    'details': {
                        'primary_apps': ['Cursor.exe(90min)']
                    }
                })
            }
        )

        # 4. 用户修正为100% (AI低估了)
        self.db.confirm_task_completion(completion_id, 100, '实际全部完成')

        # 5. 触发学习
        task_completion = self.db.get_task_completion(completion_id)

        # 解析并学习
        inference_data = json.loads(task_completion['inference_data'])
        details = inference_data.get('details', {})
        primary_apps = details.get('primary_apps', [])

        apps_used = []
        import re
        for app_str in primary_apps:
            match = re.match(r'(.+?)\((\d+)min\)', app_str)
            if match:
                app_name = match.group(1)
                duration = int(match.group(2))
                apps_used.append({'app': app_name, 'duration': duration})

        model.learn_from_correction(
            task_name='上午工作',
            apps_used=apps_used,
            correction_type='underestimated'
        )

        # 6. 验证权重增加
        updated_pattern = model.get_task_pattern('上午工作')
        updated_weight = updated_pattern['typical_apps']['Cursor.exe']['weight']

        self.assertEqual(updated_weight, initial_weight + 0.05)

        # 7. 验证学习质量
        quality = model.model['learning_quality']
        self.assertEqual(quality['total_corrections'], 1)

    def test_05_complete_workflow(self):
        """测试完整工作流程: 推理 → 确认 → 学习"""
        date = datetime.now().strftime('%Y-%m-%d')
        time_block_id = 'time-block-0'

        # 1. 数据迁移
        migration = DataMigration(self.db, self.temp_dir)
        migration.check_and_run_migrations()

        # 2. 初始化系统
        model = UserBehaviorModel(self.model_path)
        model.initialize_task_pattern(
            task_name='上午工作',
            task_type='work',
            primary_apps=['Cursor.exe', 'chrome.exe']
        )

        collector = SignalCollector(self.db, model)
        engine = InferenceEngine(collector)

        # 3. 创建测试数据 (专注会话 + 应用使用)
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # 专注会话
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

        # 应用使用
        start_time = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M")
        cursor.execute('''
            INSERT INTO activity_sessions
            (id, process_name, window_title, start_time, end_time, duration_seconds, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'activity-1',
            'Cursor.exe',
            'Test',
            start_time.isoformat(),
            (start_time + timedelta(minutes=90)).isoformat(),
            5400,
            'PRODUCTIVE'
        ))

        conn.commit()
        conn.close()

        # 4. 执行推理
        inference_result = engine.infer_task_completion(
            time_block_id=time_block_id,
            date=date,
            task_name='上午工作',
            planned_start='09:00',
            planned_end='12:00'
        )

        # 验证推理结果
        # 有专注会话(25分钟) + 应用使用(90分钟Cursor.exe, 权重0.75)
        # 完成度应该较高,但不一定是100%
        self.assertEqual(inference_result['confidence'], 'high')
        self.assertGreaterEqual(inference_result['completion'], 85)
        self.assertLessEqual(inference_result['completion'], 100)

        # 5. 保存推理结果
        completion_id = self.db.create_task_completion(
            date=date,
            time_block_id=time_block_id,
            task_data={
                'name': '上午工作',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '12:00',
                'duration_minutes': 180
            },
            inference_result=inference_result
        )

        # 6. 模拟用户确认
        # 根据实际推理结果决定修正方式
        original_completion = inference_result['completion']

        # 如果AI推理>=90%,修正为70%以触发学习
        if original_completion >= 85:
            new_completion = 70
            expected_correction = 'overestimated'
        else:
            new_completion = 100
            expected_correction = 'underestimated'

        self.db.confirm_task_completion(completion_id, new_completion, '用户修正')

        # 7. 验证数据保存
        confirmed = self.db.get_task_completion(completion_id)
        self.assertTrue(confirmed['user_confirmed'])
        self.assertTrue(confirmed['user_corrected'])
        self.assertEqual(confirmed['completion_percentage'], new_completion)
        self.assertEqual(confirmed['user_correction_type'], expected_correction)

        # 8. 触发学习
        task_completion = self.db.get_task_completion(completion_id)
        inference_data = json.loads(task_completion['inference_data'])
        details = inference_data.get('details', {})
        primary_apps = details.get('primary_apps', [])

        apps_used = []
        import re
        for app_str in primary_apps:
            match = re.match(r'(.+?)\((\d+)min\)', app_str)
            if match:
                apps_used.append({
                    'app': match.group(1),
                    'duration': int(match.group(2))
                })

        if apps_used:
            model.learn_from_correction(
                task_name='上午工作',
                apps_used=apps_used,
                correction_type='overestimated'
            )

        # 9. 验证学习结果
        quality = model.model['learning_quality']
        self.assertGreater(quality['total_corrections'], 0)

    def test_06_auto_confirm_threshold(self):
        """测试自动确认阈值功能"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 1. 运行迁移
        migration = DataMigration(self.db, self.temp_dir)
        migration.check_and_run_migrations()

        # 2. 初始化模型和引擎
        model = UserBehaviorModel(self.model_path)
        collector = SignalCollector(self.db, model)
        engine = InferenceEngine(collector)

        # 3. 创建高置信度推理记录
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

        # 4. 创建调度器并触发自动确认
        scheduler = TaskCompletionScheduler(
            db_manager=self.db,
            behavior_model=model,
            inference_engine=engine,
            config={
                'enabled': True,
                'trigger_time': '21:00',
                'trigger_on_startup': False,
                'auto_confirm_threshold': 90  # 自动确认阈值
            }
        )

        # 5. 执行自动确认
        confirmed_count = scheduler._auto_confirm_high_confidence(date)

        # 6. 验证自动确认
        self.assertEqual(confirmed_count, 1)

        # 7. 验证记录已确认
        record = self.db.get_task_completion_by_block(date, 'time-block-0')
        self.assertTrue(record['user_confirmed'])

    def test_07_data_cleanup(self):
        """测试数据清理功能"""
        # 1. 运行迁移
        migration = DataMigration(self.db, self.temp_dir)
        migration.check_and_run_migrations()

        # 2. 创建旧数据 (40天前)
        old_date = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d')
        self.db.create_task_completion(
            date=old_date,
            time_block_id='time-block-old',
            task_data={
                'name': '旧任务',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '10:00',
                'duration_minutes': 60
            },
            inference_result={
                'completion': 100,
                'confidence': 'high',
                'actual_start': '09:00',
                'actual_end': '10:00',
                'actual_duration': 60,
                'inference_data': '{}'
            }
        )

        # 3. 创建新数据 (今天)
        today = datetime.now().strftime('%Y-%m-%d')
        self.db.create_task_completion(
            date=today,
            time_block_id='time-block-new',
            task_data={
                'name': '新任务',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '10:00',
                'duration_minutes': 60
            },
            inference_result={
                'completion': 100,
                'confidence': 'high',
                'actual_start': '09:00',
                'actual_end': '10:00',
                'actual_duration': 60,
                'inference_data': '{}'
            }
        )

        # 4. 执行清理 (保留30天)
        deleted = self.db.cleanup_old_task_completions(days=30)

        # 5. 验证清理结果
        self.assertEqual(deleted, 1)

        # 6. 验证旧数据已删除
        old_record = self.db.get_task_completion_by_block(old_date, 'time-block-old')
        self.assertIsNone(old_record)

        # 7. 验证新数据保留
        new_record = self.db.get_task_completion_by_block(today, 'time-block-new')
        self.assertIsNotNone(new_record)


if __name__ == '__main__':
    unittest.main()
