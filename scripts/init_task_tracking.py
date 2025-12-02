"""
任务完成追踪系统初始化脚本

用于:
1. 初始化数据库表结构
2. 创建用户行为模型文件
3. 验证数据迁移
4. (可选) 创建测试数据

使用方法:
    python scripts/init_task_tracking.py                    # 仅初始化
    python scripts/init_task_tracking.py --test-data        # 初始化 + 创建测试数据
    python scripts/init_task_tracking.py --validate         # 仅验证
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gaiya.data.db_manager import DatabaseManager
from gaiya.utils.data_migration import DataMigration
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    """获取数据目录路径"""
    import os

    if sys.platform == 'win32':
        data_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'GaiYa'
    elif sys.platform == 'darwin':
        data_dir = Path.home() / 'Library' / 'Application Support' / 'GaiYa'
    else:
        data_dir = Path.home() / '.gaiya'

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def main():
    parser = argparse.ArgumentParser(description='任务完成追踪系统初始化')
    parser.add_argument('--test-data', action='store_true', help='创建测试数据')
    parser.add_argument('--validate', action='store_true', help='仅验证数据迁移')
    parser.add_argument('--data-dir', type=str, help='指定数据目录 (默认使用系统数据目录)')

    args = parser.parse_args()

    # 获取数据目录
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = get_data_dir()

    logger.info(f"数据目录: {data_dir}")

    # 初始化数据库
    db_path = data_dir / "user_data.db"
    logger.info(f"数据库路径: {db_path}")

    try:
        db_manager = DatabaseManager(db_path)
        logger.info("数据库连接成功 ✓")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return 1

    # 创建迁移管理器
    migration = DataMigration(db_manager, data_dir)

    # 仅验证模式
    if args.validate:
        logger.info("=" * 60)
        logger.info("开始验证数据迁移...")
        logger.info("=" * 60)

        if migration.validate_migration():
            logger.info("✓ 验证通过")
            return 0
        else:
            logger.error("✗ 验证失败")
            return 1

    # 正常初始化模式
    logger.info("=" * 60)
    logger.info("开始初始化任务完成追踪系统...")
    logger.info("=" * 60)

    # 1. 运行数据迁移
    if not migration.check_and_run_migrations():
        logger.error("✗ 数据迁移失败")
        return 1

    logger.info("✓ 数据迁移完成")

    # 2. 验证迁移
    if not migration.validate_migration():
        logger.error("✗ 数据迁移验证失败")
        return 1

    logger.info("✓ 数据迁移验证通过")

    # 3. 创建测试数据 (可选)
    if args.test_data:
        logger.info("-" * 60)
        logger.info("创建测试数据...")
        try:
            migration.create_test_data()
            logger.info("✓ 测试数据创建完成")
        except Exception as e:
            logger.error(f"✗ 测试数据创建失败: {e}")
            return 1

    # 4. 显示摘要
    logger.info("=" * 60)
    logger.info("初始化完成摘要:")
    logger.info("=" * 60)
    logger.info(f"✓ 数据库: {db_path}")
    logger.info(f"✓ 用户行为模型: {data_dir / 'user_behavior_model.json'}")

    # 检查 task_completions 表
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM task_completions")
    count = cursor.fetchone()[0]
    conn.close()
    logger.info(f"✓ task_completions 表: {count} 条记录")

    logger.info("=" * 60)
    logger.info("🎉 初始化成功!")

    if not args.test_data:
        logger.info("\n提示: 使用 --test-data 参数可以创建测试数据")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"未预期的错误: {e}", exc_info=True)
        sys.exit(1)
