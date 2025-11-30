"""
测试红温专注仓增强功能
验证:
1. ✅ Logger调用不再报错
2. ✅ UI正确显示红温专注仓样式(火焰图标+红色背景)
3. 🆕 呼吸动画效果
4. 🆕 专注会话完成处理
5. 🆕 任务名称显示
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from gaiya.ui.pomodoro_panel import PomodoroPanel
import logging

# 简单的配置和logger
config = {
    'pomodoro': {
        'work_duration': 10,  # 10秒用于快速测试
        'short_break': 5,
        'long_break': 10,
        'long_break_interval': 4
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_enhanced")

def test_focus_mode_enhanced():
    """测试红温专注仓增强功能"""
    app = QApplication(sys.argv)

    # 创建一个mock tray icon
    class MockTrayIcon:
        def showMessage(self, title, msg, icon, duration):
            logger.info(f"📢 托盘通知: {title}")
            logger.info(f"   内容: {msg}")

    tray = MockTrayIcon()

    # 测试红温专注仓(完整流程)
    logger.info("=== 🔥 测试红温专注仓完整流程 ===")
    task_name = "编写AI助手代码"
    panel_focus = PomodoroPanel(
        config,
        tray,
        logger,
        parent=None,
        time_block_id=task_name
    )
    panel_focus.show()

    logger.info(f"✅ 窗口标题: {panel_focus.windowTitle()}")
    logger.info(f"✅ 任务名称: {panel_focus.time_block_id}")
    logger.info(f"✅ 窗口大小: {panel_focus.width()}x{panel_focus.height()}")

    # 启动工作模式
    logger.info("\n=== 🚀 启动专注工作模式 ===")
    try:
        panel_focus.start_work()
        logger.info("✅ start_work()成功!")
        logger.info(f"✅ 专注会话ID: {panel_focus.current_focus_session_id}")
        logger.info(f"✅ 呼吸动画定时器: {'运行中' if panel_focus.breathing_timer.isActive() else '未启动'}")
    except Exception as e:
        logger.error(f"❌ start_work()失败: {e}")
        return 1

    # 检查呼吸动画
    logger.info("\n=== 🫁 监控呼吸动画 ===")
    def check_breathing():
        intensity = panel_focus.focus_intensity
        direction = "增强" if panel_focus.breathing_direction > 0 else "减弱"
        logger.info(f"呼吸强度: {intensity:.2f} ({direction})")

    # 每秒检查一次呼吸动画
    breathing_check_timer = QTimer()
    breathing_check_timer.timeout.connect(check_breathing)
    breathing_check_timer.start(1000)

    # 5秒后停止检查
    def stop_breathing_check():
        breathing_check_timer.stop()
        logger.info("\n=== ⏱️ 等待倒计时完成 ===")
        logger.info("(10秒后会自动完成专注会话)")

    QTimer.singleShot(5000, stop_breathing_check)

    # 测试说明
    logger.info("\n=== 📋 测试检查清单 ===")
    logger.info("请观察以下内容:")
    logger.info("1. 🔥 窗口左侧显示火焰图标(不是番茄)")
    logger.info("2. 🎨 背景为深红色(不是灰色)")
    logger.info("3. 🫁 背景红色有呼吸效果(渐变明暗)")
    logger.info("4. 📌 底部显示任务名称: 编写AI助手代码")
    logger.info("5. ⏱️ 倒计时从00:10开始")
    logger.info("6. 💾 10秒后自动完成并保存专注会话")
    logger.info("\n⏳ 测试进行中,请观察窗口变化...")

    sys.exit(app.exec())

if __name__ == '__main__':
    test_focus_mode_enhanced()
