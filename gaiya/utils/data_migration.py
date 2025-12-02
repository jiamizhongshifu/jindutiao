"""
数据迁移和初始化工具
用于初始化用户行为模型和数据库升级
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("gaiya.utils.data_migration")


class DataMigration:
    """数据迁移管理器"""

    def __init__(self, db_manager, data_dir: Path):
        """
        初始化数据迁移管理器

        Args:
            db_manager: 数据库管理器实例
            data_dir: 数据目录路径
        """
        self.db_manager = db_manager
        self.data_dir = data_dir
        self.model_path = data_dir / "user_behavior_model.json"

    def check_and_run_migrations(self) -> bool:
        """
        检查并运行所有必要的数据迁移

        Returns:
            是否成功完成所有迁移
        """
        try:
            logger.info("开始检查数据迁移...")

            # 1. 检查并创建 task_completions 表
            if not self._check_task_completions_table():
                logger.info("创建 task_completions 表...")
                self._create_task_completions_table()

            # 2. 检查并初始化用户行为模型
            if not self.model_path.exists():
                logger.info("初始化用户行为模型...")
                self._initialize_behavior_model()

            # 3. 检查数据库索引
            self._ensure_database_indexes()

            logger.info("数据迁移检查完成 ✓")
            return True

        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            return False

    def _check_task_completions_table(self) -> bool:
        """检查 task_completions 表是否存在"""
        try:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='task_completions'
            """)
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            logger.error(f"检查 task_completions 表失败: {e}")
            return False

    def _create_task_completions_table(self):
        """创建 task_completions 表 (用于数据库升级)"""
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_completions (
                id TEXT PRIMARY KEY,
                date DATE NOT NULL,
                time_block_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                task_type TEXT,

                planned_start_time TEXT,
                planned_end_time TEXT,
                planned_duration_minutes INTEGER,

                actual_start_time TEXT,
                actual_end_time TEXT,
                actual_duration_minutes INTEGER,

                completion_percentage INTEGER,
                confidence_level TEXT,
                inference_data TEXT,

                user_confirmed BOOLEAN DEFAULT 0,
                user_corrected BOOLEAN DEFAULT 0,
                user_correction_type TEXT,
                user_note TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_completions_date
            ON task_completions(date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_completions_time_block
            ON task_completions(time_block_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_completions_unconfirmed
            ON task_completions(user_confirmed, date)
        ''')

        conn.commit()
        conn.close()
        logger.info("task_completions 表创建成功")

    def _initialize_behavior_model(self):
        """初始化用户行为模型文件"""
        from gaiya.services.user_behavior_model import UserBehaviorModel

        try:
            # 创建默认模型
            model = UserBehaviorModel(self.model_path)

            # 模型文件会在初始化时自动创建
            logger.info(f"用户行为模型已初始化: {self.model_path}")

        except Exception as e:
            logger.error(f"初始化用户行为模型失败: {e}")
            raise

    def _ensure_database_indexes(self):
        """确保所有必要的数据库索引存在"""
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()

        # task_completions 表的索引
        indexes = [
            ("idx_task_completions_date", "task_completions", "date"),
            ("idx_task_completions_time_block", "task_completions", "time_block_id"),
            ("idx_task_completions_unconfirmed", "task_completions", "user_confirmed, date"),
        ]

        for index_name, table_name, columns in indexes:
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table_name}({columns})
                """)
            except Exception as e:
                logger.warning(f"创建索引 {index_name} 失败: {e}")

        conn.commit()
        conn.close()
        logger.info("数据库索引检查完成")

    def create_test_data(self, date: Optional[str] = None):
        """
        创建测试数据 (仅用于开发环境)

        Args:
            date: 测试日期,默认为今天
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"创建测试数据: {date}")

        # 示例任务完成记录
        test_completions = [
            {
                'time_block_id': 'time-block-0',
                'task_name': '深度睡眠',
                'task_type': 'rest',
                'planned_start_time': '00:00',
                'planned_end_time': '06:00',
                'planned_duration_minutes': 360,
                'actual_start_time': '00:15',
                'actual_end_time': '06:10',
                'actual_duration_minutes': 355,
                'completion_percentage': 99,
                'confidence_level': 'high',
                'inference_data': '{"signal_strength": 0.95, "primary_app": null, "focus_session": false}',
            },
            {
                'time_block_id': 'time-block-4',
                'task_name': '上午工作',
                'task_type': 'work',
                'planned_start_time': '09:00',
                'planned_end_time': '12:00',
                'planned_duration_minutes': 180,
                'actual_start_time': '09:10',
                'actual_end_time': '11:45',
                'actual_duration_minutes': 155,
                'completion_percentage': 86,
                'confidence_level': 'high',
                'inference_data': '{"signal_strength": 0.92, "primary_app": "Cursor.exe", "focus_session": true, "focus_minutes": 90}',
            },
            {
                'time_block_id': 'time-block-6',
                'task_name': '下午工作',
                'task_type': 'work',
                'planned_start_time': '14:00',
                'planned_end_time': '18:00',
                'planned_duration_minutes': 240,
                'actual_start_time': '14:20',
                'actual_end_time': '17:30',
                'actual_duration_minutes': 190,
                'completion_percentage': 79,
                'confidence_level': 'medium',
                'inference_data': '{"signal_strength": 0.75, "primary_app": "chrome.exe", "focus_session": false}',
            },
        ]

        # 插入测试数据
        for completion_data in test_completions:
            try:
                self.db_manager.create_task_completion(
                    date=date,
                    time_block_id=completion_data['time_block_id'],
                    task_data={
                        'name': completion_data['task_name'],
                        'task_type': completion_data['task_type'],
                        'start_time': completion_data['planned_start_time'],
                        'end_time': completion_data['planned_end_time'],
                        'duration_minutes': completion_data['planned_duration_minutes'],
                    },
                    inference_result={
                        'actual_start': completion_data['actual_start_time'],
                        'actual_end': completion_data['actual_end_time'],
                        'actual_duration': completion_data['actual_duration_minutes'],
                        'completion': completion_data['completion_percentage'],
                        'confidence': completion_data['confidence_level'],
                        'inference_data': completion_data['inference_data'],
                    }
                )
                logger.info(f"创建测试数据: {completion_data['task_name']}")
            except Exception as e:
                logger.error(f"创建测试数据失败 ({completion_data['task_name']}): {e}")

        logger.info("测试数据创建完成")

    def validate_migration(self) -> bool:
        """
        验证数据迁移是否成功

        Returns:
            验证是否通过
        """
        try:
            # 1. 检查 task_completions 表
            if not self._check_task_completions_table():
                logger.error("验证失败: task_completions 表不存在")
                return False

            # 2. 检查用户行为模型文件
            if not self.model_path.exists():
                logger.error(f"验证失败: 用户行为模型文件不存在 ({self.model_path})")
                return False

            # 3. 尝试读取模型文件
            from gaiya.services.user_behavior_model import UserBehaviorModel
            model = UserBehaviorModel(self.model_path)
            if model.model is None:
                logger.error("验证失败: 用户行为模型加载失败")
                return False

            # 4. 检查数据库索引
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='task_completions'
            """)
            indexes = cursor.fetchall()
            conn.close()
            if len(indexes) < 3:
                logger.warning(f"验证警告: task_completions 索引数量不足 ({len(indexes)}/3)")

            logger.info("数据迁移验证通过 ✓")
            return True

        except Exception as e:
            logger.error(f"数据迁移验证失败: {e}")
            return False


def run_migration(db_manager, data_dir: Path, create_test_data: bool = False):
    """
    运行数据迁移 (便捷函数)

    Args:
        db_manager: 数据库管理器实例
        data_dir: 数据目录路径
        create_test_data: 是否创建测试数据

    Returns:
        是否成功
    """
    migration = DataMigration(db_manager, data_dir)

    # 运行迁移
    if not migration.check_and_run_migrations():
        logger.error("数据迁移失败")
        return False

    # 验证迁移
    if not migration.validate_migration():
        logger.error("数据迁移验证失败")
        return False

    # 创建测试数据 (可选)
    if create_test_data:
        migration.create_test_data()

    return True
