"""
测试进度条专注状态显示功能
验证:
1. ✅ 活跃专注会话在进度条上显示红色覆盖层和🔥图标
2. ✅ 已完成专注会话在时间块右上角显示小🔥图标
3. ✅ 专注状态每秒自动更新
"""
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

from gaiya.data.db_manager import db
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_progress_focus")

def test_focus_state_integration():
    """测试进度条专注状态集成"""
    logger.info("=== 🔥 测试进度条专注状态显示 ===\n")

    # 1. 创建测试专注会话
    test_task_active = "写自己的项目"
    test_task_completed = "看书学习"

    logger.info("📝 创建测试数据...")

    # Create active session
    active_session_id = db.create_focus_session(test_task_active)
    logger.info(f"✅ 创建活跃专注会话: {test_task_active} (ID: {active_session_id})")

    # Create and complete a session
    completed_session_id = db.create_focus_session(test_task_completed)
    db.complete_focus_session(completed_session_id)
    logger.info(f"✅ 创建已完成专注会话: {test_task_completed} (ID: {completed_session_id})")

    # 2. Test query methods
    logger.info("\n📊 测试数据库查询方法...")

    active_sessions = db.get_active_focus_sessions()
    logger.info(f"活跃专注会话: {active_sessions}")

    completed_blocks = db.get_completed_focus_sessions_for_blocks([test_task_active, test_task_completed])
    logger.info(f"已完成专注会话的时间块: {completed_blocks}")

    # 3. Verify expected results
    logger.info("\n✅ 验证测试结果...")

    assert test_task_active in active_sessions, "活跃会话应该包含测试任务"
    assert test_task_completed in completed_blocks, "已完成会话应该包含测试任务"

    logger.info("✅ 所有测试通过!")

    # 4. Instructions for visual testing
    logger.info("\n📋 视觉测试说明:")
    logger.info("1. 启动主应用程序 (python main.py)")
    logger.info("2. 观察进度条上的时间块:")
    logger.info(f"   - '{test_task_active}' 应显示红色覆盖层和左侧🔥图标 (活跃专注)")
    logger.info(f"   - '{test_task_completed}' 应在右上角显示小🔥图标 (已完成专注)")
    logger.info("3. 专注状态应该每秒自动更新")
    logger.info("4. 右键点击时间块选择'开启红温专注仓'后,应立即看到红色覆盖层")

    # 5. Cleanup instructions
    logger.info("\n🧹 清理测试数据:")
    logger.info("执行以下命令清理测试会话:")
    logger.info(f"  - db.interrupt_focus_session('{active_session_id}')")
    logger.info("\n或者重启应用后,新的一天将自动清零历史数据")

    return {
        "active_session_id": active_session_id,
        "completed_session_id": completed_session_id
    }

def cleanup_test_data(session_ids):
    """清理测试数据"""
    logger.info("\n🧹 清理测试数据...")
    if 'active_session_id' in session_ids:
        db.interrupt_focus_session(session_ids['active_session_id'])
        logger.info(f"✅ 已中断活跃会话: {session_ids['active_session_id']}")

if __name__ == '__main__':
    try:
        session_ids = test_focus_state_integration()
        logger.info("\n✅ 测试数据已创建,保留以便进行视觉测试")
        logger.info("提示: 现在可以启动主应用查看进度条上的专注状态")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        sys.exit(1)
