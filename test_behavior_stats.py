"""
测试行为识别统计信息实时更新功能
"""
import sys
import logging
from PySide6.QtWidgets import QApplication
from config_gui import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别以看到更详细的日志
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_behavior_stats_timer():
    """测试行为识别统计信息定时器"""
    print("\n" + "="*60)
    print("测试行为识别统计信息实时更新功能")
    print("="*60 + "\n")

    app = QApplication(sys.argv)
    config_manager = ConfigManager()

    # 显示窗口
    config_manager.show()

    # 模拟切换到行为识别标签页 (index=4)
    print("1. 切换到行为识别标签页...")
    config_manager.tabs.setCurrentIndex(4)

    # 等待tab加载完成
    app.processEvents()

    # 检查定时器是否启动
    print("\n2. 检查定时器状态:")
    if config_manager.behavior_stats_timer:
        if config_manager.behavior_stats_timer.isActive():
            print("   ✅ 定时器已启动")
            print(f"   ⏰ 间隔: {config_manager.behavior_stats_timer.interval()}ms")
        else:
            print("   ❌ 定时器未激活")
    else:
        print("   ❌ 定时器未创建")

    # 检查统计标签是否存在
    print("\n3. 检查统计标签:")
    if config_manager.stats_labels:
        print(f"   ✅ 已创建 {len(config_manager.stats_labels)} 个统计标签")
        for category in config_manager.stats_labels.keys():
            print(f"      - {category}")
    else:
        print("   ❌ 未找到统计标签")

    # 手动触发一次更新
    print("\n4. 手动触发统计更新...")
    config_manager.update_behavior_stats()
    app.processEvents()

    print("\n5. 等待5秒观察定时器自动更新...")
    print("   (应该会在日志中看到 'DEBUG:行为识别统计信息已更新')")

    # 使用QTimer等待5秒后退出
    from PySide6.QtCore import QTimer
    QTimer.singleShot(5000, app.quit)

    # 运行应用
    app.exec()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_behavior_stats_timer()
