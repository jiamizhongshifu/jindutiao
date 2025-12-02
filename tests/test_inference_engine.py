"""
任务推理引擎单元测试

测试范围:
1. SignalCollector - 信号收集
2. InferenceEngine - 推理计算
3. 完成度计算 - 多维度信号加权
4. 置信度评估 - high/medium/low/unknown
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


class TestSignalCollector(unittest.TestCase):
    """测试信号收集器"""

    def setUp(self):
        """每个测试前创建临时数据库和模型"""
        import shutil
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / 'test.db'
        self.model_path = self.temp_dir / 'model.json'

        self.db = DatabaseManager(self.db_path)
        self.model = UserBehaviorModel(self.model_path)

        # 初始化任务模式
        self.model.initialize_task_pattern(
            task_name='编程开发',
            task_type='work',
            primary_apps=['Cursor.exe', 'chrome.exe']
        )

        self.collector = SignalCollector(self.db, self.model)

    def tearDown(self):
        """每个测试后删除临时文件"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_collect_focus_signal_with_session(self):
        """测试收集专注会话信号 - 有专注记录"""
        date = datetime.now().strftime('%Y-%m-%d')
        time_block_id = 'test-block-1'

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

        # 收集信号
        signal = self.collector.collect_focus_signal(time_block_id, date)

        self.assertTrue(signal['has_focus'])
        self.assertEqual(signal['focus_duration'], 25)
        self.assertEqual(signal['focus_sessions'], 1)
        self.assertEqual(signal['weight'], 1.0)

    def test_collect_focus_signal_without_session(self):
        """测试收集专注会话信号 - 无专注记录"""
        date = datetime.now().strftime('%Y-%m-%d')
        time_block_id = 'test-block-1'

        signal = self.collector.collect_focus_signal(time_block_id, date)

        self.assertFalse(signal['has_focus'])
        self.assertEqual(signal['focus_duration'], 0)
        self.assertEqual(signal['focus_sessions'], 0)

    def test_collect_activity_signal_with_apps(self):
        """测试收集活动追踪信号 - 有应用使用"""
        date = datetime.now().strftime('%Y-%m-%d')
        time_block_id = 'test-block-1'
        task_name = '编程开发'
        planned_start = '09:00'
        planned_end = '10:00'

        # 创建活动会话
        start_time = datetime.strptime(f"{date} {planned_start}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{date} {planned_end}", "%Y-%m-%d %H:%M")

        conn = self.db._get_connection()
        cursor = conn.cursor()

        # 插入 Cursor.exe 使用记录 (主要应用)
        cursor.execute('''
            INSERT INTO activity_sessions
            (id, process_name, window_title, start_time, end_time, duration_seconds, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'activity-1',
            'Cursor.exe',
            'Test',
            start_time.isoformat(),
            (start_time + timedelta(minutes=30)).isoformat(),
            1800,  # 30分钟
            'PRODUCTIVE'
        ))

        # 插入 chrome.exe 使用记录 (主要应用)
        cursor.execute('''
            INSERT INTO activity_sessions
            (id, process_name, window_title, start_time, end_time, duration_seconds, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'activity-2',
            'chrome.exe',
            'Test',
            (start_time + timedelta(minutes=30)).isoformat(),
            end_time.isoformat(),
            1800,  # 30分钟
            'NEUTRAL'
        ))

        conn.commit()
        conn.close()

        # 收集信号
        signal = self.collector.collect_activity_signal(
            time_block_id, date, task_name, planned_start, planned_end
        )

        self.assertGreater(len(signal['primary_apps']), 0)
        self.assertEqual(signal['total_active_time'], 3600)  # 60分钟

    def test_collect_time_match_signal(self):
        """测试收集时间匹配信号"""
        signal = self.collector.collect_time_match_signal(
            planned_start='09:00',
            planned_end='10:00',
            actual_start='09:10',
            actual_end='09:55'
        )

        self.assertGreater(signal['time_match_score'], 0)
        self.assertEqual(signal['planned_duration'], 60)
        self.assertEqual(signal['actual_duration'], 45)
        # 45/60 = 0.75
        self.assertAlmostEqual(signal['time_match_score'], 0.75, places=2)


class TestInferenceEngine(unittest.TestCase):
    """测试推理引擎"""

    def setUp(self):
        """每个测试前创建测试环境"""
        import shutil
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / 'test.db'
        self.model_path = self.temp_dir / 'model.json'

        self.db = DatabaseManager(self.db_path)
        self.model = UserBehaviorModel(self.model_path)

        # 初始化任务模式
        self.model.initialize_task_pattern(
            task_name='编程开发',
            task_type='work',
            primary_apps=['Cursor.exe']
        )

        self.collector = SignalCollector(self.db, self.model)
        self.engine = InferenceEngine(self.collector)

    def tearDown(self):
        """每个测试后删除临时文件"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_calculate_completion_with_focus_only(self):
        """测试仅有专注会话信号的完成度计算"""
        signals = {
            'focus': {
                'has_focus': True,
                'focus_duration': 25,
                'focus_sessions': 1,
                'weight': 1.0,
                'signal_type': 'focus'
            },
            'activity': {
                'primary_apps': [],
                'secondary_apps': [],
                'total_active_time': 0,
                'signal_type': 'activity'
            },
            'time_match': {
                'time_match_score': 0.0,
                'planned_duration': 60,
                'actual_duration': 0,
                'weight': 0.5,
                'signal_type': 'time_match'
            }
        }

        completion, confidence, inference_data = \
            self.engine.calculate_completion_percentage(signals)

        # 25分钟专注会话 = 100%完成度
        self.assertEqual(completion, 100)
        # 有专注会话 = high confidence
        self.assertEqual(confidence, 'high')
        self.assertEqual(inference_data['signal_count'], 1)

    def test_calculate_completion_with_primary_apps(self):
        """测试仅有主要应用使用信号的完成度计算"""
        signals = {
            'focus': {
                'has_focus': False,
                'focus_duration': 0,
                'focus_sessions': 0,
                'weight': 1.0,
                'signal_type': 'focus'
            },
            'activity': {
                'primary_apps': [
                    {'app': 'Cursor.exe', 'duration': 45, 'weight': 0.85}
                ],
                'secondary_apps': [],
                'total_active_time': 2700,
                'signal_type': 'activity'
            },
            'time_match': {
                'time_match_score': 0.0,
                'planned_duration': 60,
                'actual_duration': 0,
                'weight': 0.5,
                'signal_type': 'time_match'
            }
        }

        completion, confidence, inference_data = \
            self.engine.calculate_completion_percentage(signals)

        # 主要应用使用45分钟,权重0.85 -> 约85%完成度
        self.assertGreater(completion, 70)
        self.assertLess(completion, 100)
        # 有主要应用 + 总权重>=0.85 = high confidence
        self.assertEqual(confidence, 'high')

    def test_calculate_completion_with_multiple_signals(self):
        """测试多维度信号加权计算"""
        signals = {
            'focus': {
                'has_focus': True,
                'focus_duration': 15,
                'focus_sessions': 1,
                'weight': 1.0,
                'signal_type': 'focus'
            },
            'activity': {
                'primary_apps': [
                    {'app': 'Cursor.exe', 'duration': 30, 'weight': 0.85}
                ],
                'secondary_apps': [
                    {'app': 'explorer.exe', 'duration': 10, 'weight': 0.60}
                ],
                'total_active_time': 2400,
                'signal_type': 'activity'
            },
            'time_match': {
                'time_match_score': 0.75,
                'planned_duration': 60,
                'actual_duration': 45,
                'weight': 0.5,
                'signal_type': 'time_match'
            }
        }

        completion, confidence, inference_data = \
            self.engine.calculate_completion_percentage(signals)

        # 多维度信号应该给出合理的完成度
        self.assertGreater(completion, 50)
        self.assertLessEqual(completion, 100)
        # 有专注会话 = high confidence
        self.assertEqual(confidence, 'high')
        # 应该使用了4个信号 (focus + primary + secondary + time_match)
        self.assertEqual(inference_data['signal_count'], 4)

    def test_confidence_level_high(self):
        """测试high置信度判定"""
        # 情况1: 有专注会话
        signals = {
            'focus': {'has_focus': True, 'focus_duration': 25, 'focus_sessions': 1},
            'activity': {'primary_apps': [], 'secondary_apps': []},
            'time_match': {'time_match_score': 0.0}
        }

        _, confidence, _ = self.engine.calculate_completion_percentage(signals)
        self.assertEqual(confidence, 'high')

        # 情况2: 有主要应用 + 总权重>=0.85
        signals = {
            'focus': {'has_focus': False, 'focus_duration': 0, 'focus_sessions': 0},
            'activity': {
                'primary_apps': [{'app': 'Cursor.exe', 'duration': 40, 'weight': 0.85}],
                'secondary_apps': []
            },
            'time_match': {'time_match_score': 0.0}
        }

        _, confidence, _ = self.engine.calculate_completion_percentage(signals)
        self.assertEqual(confidence, 'high')

    def test_confidence_level_medium(self):
        """测试medium置信度判定"""
        signals = {
            'focus': {'has_focus': False, 'focus_duration': 0, 'focus_sessions': 0},
            'activity': {
                'primary_apps': [],
                'secondary_apps': [{'app': 'explorer.exe', 'duration': 20, 'weight': 0.60}]
            },
            'time_match': {'time_match_score': 0.0}
        }

        _, confidence, _ = self.engine.calculate_completion_percentage(signals)
        self.assertEqual(confidence, 'medium')

    def test_confidence_level_low(self):
        """测试low置信度判定"""
        signals = {
            'focus': {'has_focus': False, 'focus_duration': 0, 'focus_sessions': 0},
            'activity': {'primary_apps': [], 'secondary_apps': []},
            'time_match': {'time_match_score': 0.75}
        }

        _, confidence, _ = self.engine.calculate_completion_percentage(signals)
        self.assertEqual(confidence, 'low')

    def test_confidence_level_unknown(self):
        """测试unknown置信度判定"""
        signals = {
            'focus': {'has_focus': False, 'focus_duration': 0, 'focus_sessions': 0},
            'activity': {'primary_apps': [], 'secondary_apps': []},
            'time_match': {'time_match_score': 0.0}
        }

        _, confidence, _ = self.engine.calculate_completion_percentage(signals)
        self.assertEqual(confidence, 'unknown')

    def test_infer_task_completion_integration(self):
        """测试完整的任务完成推断流程"""
        date = datetime.now().strftime('%Y-%m-%d')
        time_block_id = 'test-block-1'
        task_name = '编程开发'
        planned_start = '09:00'
        planned_end = '10:00'

        # 创建测试数据
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # 添加专注会话
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

        # 执行推断
        result = self.engine.infer_task_completion(
            time_block_id, date, task_name, planned_start, planned_end
        )

        # 验证结果
        self.assertIn('completion', result)
        self.assertIn('confidence', result)
        self.assertIn('actual_start', result)
        self.assertIn('actual_end', result)
        self.assertIn('actual_duration', result)
        self.assertIn('inference_data', result)

        self.assertGreater(result['completion'], 0)
        self.assertLessEqual(result['completion'], 100)
        self.assertIn(result['confidence'], ['high', 'medium', 'low', 'unknown'])

        # 验证inference_data是合法的JSON
        import json
        data = json.loads(result['inference_data'])
        self.assertIn('signal_count', data)
        self.assertIn('details', data)


if __name__ == '__main__':
    unittest.main()
