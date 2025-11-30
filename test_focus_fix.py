"""
测试红温专注仓修复
验证:
1. Logger调用不再报错
2. UI正确显示红温专注仓样式(火焰图标+红色背景)
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from gaiya.ui.pomodoro_panel import PomodoroPanel
import logging

# 简单的配置和logger
config = {
    'pomodoro': {
        'work_duration': 1500,  # 25分钟
        'short_break': 300,
        'long_break': 900,
        'long_break_interval': 4
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

def test_focus_mode():
    """测试红温专注仓模式"""
    app = QApplication(sys.argv)

    # 创建一个mock tray icon
    class MockTrayIcon:
        def showMessage(self, *args, **kwargs):
            logger.info(f"Tray message: {args}")

    tray = MockTrayIcon()

    # 测试1: 普通番茄钟(无time_block_id)
    logger.info("=== 测试普通番茄钟 ===")
    panel_normal = PomodoroPanel(config, tray, logger, parent=None, time_block_id=None)
    panel_normal.show()
    logger.info(f"窗口标题: {panel_normal.windowTitle()}")
    logger.info(f"time_block_id: {panel_normal.time_block_id}")

    # 测试2: 红温专注仓(有time_block_id)
    logger.info("\n=== 测试红温专注仓 ===")
    panel_focus = PomodoroPanel(config, tray, logger, parent=None, time_block_id="test_block_001")
    panel_focus.move(100, 100)  # 错开位置
    panel_focus.show()
    logger.info(f"窗口标题: {panel_focus.windowTitle()}")
    logger.info(f"time_block_id: {panel_focus.time_block_id}")

    # 测试3: 启动工作模式(触发logger调用)
    logger.info("\n=== 测试启动工作模式 ===")
    try:
        panel_focus.start_work()
        logger.info("✅ start_work()成功,没有报错!")
    except Exception as e:
        logger.error(f"❌ start_work()失败: {e}")
        return 1

    logger.info("\n=== 测试完成 ===")
    logger.info("请检查两个窗口的视觉差异:")
    logger.info("- 普通番茄钟: 番茄图标🍅 + 灰色背景")
    logger.info("- 红温专注仓: 火焰图标🔥 + 红色背景")

    sys.exit(app.exec())

if __name__ == '__main__':
    test_focus_mode()
