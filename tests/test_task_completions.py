"""
任务完成追踪系统单元测试

测试范围:
1. DatabaseManager - task completions CRUD 操作
2. UserBehaviorModel - 模型加载/保存/学习
3. DataMigration - 数据迁移和初始化
"""
import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gaiya.data.db_manager import DatabaseManager
from gaiya.services.user_behavior_model import UserBehaviorModel
from gaiya.utils.data_migration import DataMigration


class TestTaskCompletions(unittest.TestCase):
    """测试任务完成记录的 CRUD 操作"""

    def setUp(self):
        """每个测试前创建临时数据库"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = Path(self.temp_db.name)
        self.temp_db.close()

        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        """每个测试后删除临时数据库"""
        if self.db_path.exists():
            self.db_path.unlink()

    def test_create_task_completion(self):
        """测试创建任务完成记录"""
        date = '2025-12-01'
        time_block_id = 'time-block-0'

        task_data = {
            'name': '上午工作',
            'task_type': 'work',
            'start_time': '09:00',
            'end_time': '12:00',
            'duration_minutes': 180
        }

        inference_result = {
            'actual_start': '09:10',
            'actual_end': '11:45',
            'actual_duration': 155,
            'completion': 86,
            'confidence': 'high',
            'inference_data': {'signal_strength': 0.92}
        }

        # 创建记录
        completion_id = self.db.create_task_completion(
            date, time_block_id, task_data, inference_result
        )

        self.assertIsNotNone(completion_id)
        self.assertIsInstance(completion_id, str)

    def test_get_task_completion(self):
        """测试获取任务完成记录"""
        # 先创建一条记录
        completion_id = self.db.create_task_completion(
            date='2025-12-01',
            time_block_id='time-block-0',
            task_data={
                'name': '测试任务',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '10:00',
                'duration_minutes': 60
            },
            inference_result={
                'actual_start': '09:05',
                'actual_end': '10:05',
                'actual_duration': 60,
                'completion': 100,
                'confidence': 'high',
                'inference_data': {}
            }
        )

        # 获取记录
        completion = self.db.get_task_completion(completion_id)

        self.assertIsNotNone(completion)
        self.assertEqual(completion['id'], completion_id)
        self.assertEqual(completion['task_name'], '测试任务')
        self.assertEqual(completion['completion_percentage'], 100)

    def test_get_today_task_completions(self):
        """测试获取今日所有任务完成记录"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 创建多条记录 (按时间逆序创建,测试排序)
        # 使用两位数小时以确保字符串排序正确
        start_times = ['09:00', '10:00', '11:00']
        end_times = ['10:00', '11:00', '12:00']

        for i in [2, 0, 1]:
            self.db.create_task_completion(
                date=date,
                time_block_id=f'time-block-{i}',
                task_data={
                    'name': f'任务 {i+1}',
                    'task_type': 'work',
                    'start_time': start_times[i],
                    'end_time': end_times[i],
                    'duration_minutes': 60
                },
                inference_result={
                    'actual_start': start_times[i],
                    'actual_end': end_times[i],
                    'actual_duration': 60,
                    'completion': 100,
                    'confidence': 'high',
                    'inference_data': {}
                }
            )

        # 获取今日记录 (应按 planned_start_time 排序)
        completions = self.db.get_today_task_completions(date)

        self.assertEqual(len(completions), 3)
        # 验证按时间排序: 09:00 (任务1), 10:00 (任务2), 11:00 (任务3)
        self.assertEqual(completions[0]['task_name'], '任务 1')
        self.assertEqual(completions[1]['task_name'], '任务 2')
        self.assertEqual(completions[2]['task_name'], '任务 3')

    def test_get_unconfirmed_task_completions(self):
        """测试获取未确认的任务完成记录"""
        date = datetime.now().strftime('%Y-%m-%d')

        # 创建已确认和未确认的记录
        id1 = self.db.create_task_completion(
            date=date,
            time_block_id='time-block-0',
            task_data={
                'name': '已确认任务',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '10:00',
                'duration_minutes': 60
            },
            inference_result={
                'actual_start': '09:05',
                'actual_end': '10:05',
                'actual_duration': 60,
                'completion': 100,
                'confidence': 'high',
                'inference_data': {}
            }
        )

        id2 = self.db.create_task_completion(
            date=date,
            time_block_id='time-block-1',
            task_data={
                'name': '未确认任务',
                'task_type': 'work',
                'start_time': '10:00',
                'end_time': '11:00',
                'duration_minutes': 60
            },
            inference_result={
                'actual_start': '10:05',
                'actual_end': '11:05',
                'actual_duration': 60,
                'completion': 100,
                'confidence': 'medium',
                'inference_data': {}
            }
        )

        # 确认第一条记录
        self.db.confirm_task_completion(id1, 100, '')

        # 获取未确认记录
        unconfirmed = self.db.get_unconfirmed_task_completions(date)

        self.assertEqual(len(unconfirmed), 1)
        self.assertEqual(unconfirmed[0]['task_name'], '未确认任务')

    def test_update_task_completion(self):
        """测试更新任务完成记录"""
        completion_id = self.db.create_task_completion(
            date='2025-12-01',
            time_block_id='time-block-0',
            task_data={
                'name': '测试任务',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '10:00',
                'duration_minutes': 60
            },
            inference_result={
                'actual_start': '09:05',
                'actual_end': '10:05',
                'actual_duration': 60,
                'completion': 80,
                'confidence': 'medium',
                'inference_data': {}
            }
        )

        # 更新记录
        self.db.update_task_completion(completion_id, {
            'completion_percentage': 100,
            'confidence_level': 'high',
            'user_note': '手动调整为100%'
        })

        # 验证更新
        updated = self.db.get_task_completion(completion_id)
        self.assertEqual(updated['completion_percentage'], 100)
        self.assertEqual(updated['confidence_level'], 'high')
        self.assertEqual(updated['user_note'], '手动调整为100%')

    def test_confirm_task_completion(self):
        """测试用户确认任务完成"""
        completion_id = self.db.create_task_completion(
            date='2025-12-01',
            time_block_id='time-block-0',
            task_data={
                'name': '测试任务',
                'task_type': 'work',
                'start_time': '09:00',
                'end_time': '10:00',
                'duration_minutes': 60
            },
            inference_result={
                'actual_start': '09:05',
                'actual_end': '10:05',
                'actual_duration': 60,
                'completion': 80,
                'confidence': 'medium',
                'inference_data': {}
            }
        )

        # 用户修正为60% (AI高估了>10%)
        self.db.confirm_task_completion(completion_id, 60, '实际只完成60%')

        # 验证确认
        confirmed = self.db.get_task_completion(completion_id)
        self.assertTrue(confirmed['user_confirmed'])
        self.assertTrue(confirmed['user_corrected'])
        self.assertEqual(confirmed['user_correction_type'], 'overestimated')
        self.assertEqual(confirmed['completion_percentage'], 60)


class TestUserBehaviorModel(unittest.TestCase):
    """测试用户行为模型"""

    def setUp(self):
        """每个测试前创建临时模型文件"""
        import shutil
        import uuid
        # 使用唯一目录名避免测试间冲突
        self.temp_dir = Path(tempfile.gettempdir()) / f'test_model_{uuid.uuid4().hex[:8]}'
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.temp_dir / 'user_behavior_model.json'

    def tearDown(self):
        """每个测试后删除临时文件"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_default_model(self):
        """测试创建默认模型"""
        model = UserBehaviorModel(self.model_path)

        self.assertTrue(self.model_path.exists())
        self.assertIsNotNone(model.model)
        self.assertEqual(model.model['version'], '1.0')

    def test_save_and_load_model(self):
        """测试模型保存和加载"""
        model = UserBehaviorModel(self.model_path)

        # 添加一些数据
        model.model['task_patterns']['测试任务'] = {
            'typical_apps': {'Cursor.exe': {'weight': 0.85}},
            'learning_samples': 5
        }
        model.save_model()

        # 重新加载
        model2 = UserBehaviorModel(self.model_path)

        self.assertIn('测试任务', model2.model['task_patterns'])
        self.assertEqual(
            model2.model['task_patterns']['测试任务']['learning_samples'],
            5
        )

    def test_initialize_task_pattern(self):
        """测试初始化任务模式"""
        model = UserBehaviorModel(self.model_path)

        model.initialize_task_pattern(
            task_name='编程开发',
            task_type='work',
            primary_apps=['Cursor.exe', 'chrome.exe']
        )

        pattern = model.get_task_pattern('编程开发')

        self.assertIn('Cursor.exe', pattern['typical_apps'])
        self.assertEqual(pattern['typical_apps']['Cursor.exe']['weight'], 0.75)
        self.assertEqual(pattern['learning_samples'], 0)

    def test_learn_from_correction_underestimated(self):
        """测试从修正中学习 - AI低估了"""
        # 使用独立的模型路径
        test_model_path = self.temp_dir / 'test_underestimated.json'
        model = UserBehaviorModel(test_model_path)

        # 初始化任务
        model.initialize_task_pattern(
            task_name='编程开发',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        # 重新加载模型以确保初始化数据已保存
        model = UserBehaviorModel(test_model_path)

        # 获取初始权重
        initial_pattern = model.get_task_pattern('编程开发')
        initial_weight = initial_pattern['typical_apps']['Cursor.exe']['weight']
        self.assertEqual(initial_weight, 0.75, f"初始权重应为0.75,实际为{initial_weight}")

        # AI低估了,用户实际完成更多
        model.learn_from_correction(
            task_name='编程开发',
            apps_used=[{'app': 'Cursor.exe', 'duration': 90}],
            correction_type='underestimated'
        )

        pattern = model.get_task_pattern('编程开发')

        # 权重应该提升 (0.75 + 0.05 = 0.80)
        self.assertEqual(pattern['typical_apps']['Cursor.exe']['weight'], 0.80)
        self.assertEqual(pattern['learning_samples'], 1)

    def test_learn_from_correction_overestimated(self):
        """测试从修正中学习 - AI高估了"""
        model = UserBehaviorModel(self.model_path)

        model.initialize_task_pattern(
            task_name='编程开发',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        # AI高估了,用户实际完成更少
        model.learn_from_correction(
            task_name='编程开发',
            apps_used=[{'app': 'Cursor.exe', 'duration': 90}],
            correction_type='overestimated'
        )

        pattern = model.get_task_pattern('编程开发')

        # 权重应该降低 (0.75 - 0.05 = 0.70)
        self.assertEqual(pattern['typical_apps']['Cursor.exe']['weight'], 0.70)

    def test_learning_quality_tracking(self):
        """测试学习质量追踪"""
        # 使用独立的模型路径
        test_model_path = self.temp_dir / 'test_quality.json'
        model = UserBehaviorModel(test_model_path)

        # 初始化时不应该影响学习质量计数
        model.initialize_task_pattern(
            task_name='编程开发',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        # 验证初始学习质量
        initial_quality = model.model['learning_quality']
        self.assertEqual(initial_quality['total_corrections'], 0,
                        f"初始质量计数应为0,实际为{initial_quality['total_corrections']}")

        # 多次修正
        for _ in range(3):
            model.learn_from_correction(
                task_name='编程开发',
                apps_used=[{'app': 'Cursor.exe', 'duration': 90}],
                correction_type='accurate'
            )

        for _ in range(2):
            model.learn_from_correction(
                task_name='编程开发',
                apps_used=[{'app': 'Cursor.exe', 'duration': 90}],
                correction_type='underestimated'
            )

        # 验证学习质量 (只有 learn_from_correction 会增加计数)
        quality = model.model['learning_quality']
        self.assertEqual(quality['total_corrections'], 5)
        self.assertEqual(quality['accurate_predictions'], 3)
        self.assertAlmostEqual(quality['accuracy_rate'], 0.6, places=2)

    def test_cleanup_old_data(self):
        """测试清理旧数据"""
        model = UserBehaviorModel(self.model_path)

        # 添加低质量应用记录
        model.model['task_patterns']['测试任务'] = {
            'typical_apps': {
                'GoodApp.exe': {'weight': 0.85, 'sample_count': 10},
                'BadApp.exe': {'weight': 0.3, 'sample_count': 2},  # 应该被清理
                'AnotherBadApp.exe': {'weight': 0.2, 'sample_count': 1}  # 应该被清理
            },
            'learning_samples': 10
        }

        model.save_model()
        model.cleanup_old_data()

        # 验证清理结果
        apps = model.model['task_patterns']['测试任务']['typical_apps']
        self.assertIn('GoodApp.exe', apps)
        self.assertNotIn('BadApp.exe', apps)
        self.assertNotIn('AnotherBadApp.exe', apps)


class TestDataMigration(unittest.TestCase):
    """测试数据迁移"""

    def setUp(self):
        """每个测试前创建临时环境"""
        import shutil
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / 'test.db'
        self.model_path = self.temp_dir / 'user_behavior_model.json'

        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        """每个测试后删除临时文件"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_and_run_migrations(self):
        """测试运行数据迁移"""
        migration = DataMigration(self.db, self.temp_dir)

        result = migration.check_and_run_migrations()

        self.assertTrue(result)
        self.assertTrue(self.model_path.exists())

    def test_validate_migration(self):
        """测试验证数据迁移"""
        migration = DataMigration(self.db, self.temp_dir)

        # 运行迁移
        migration.check_and_run_migrations()

        # 验证迁移
        result = migration.validate_migration()

        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
