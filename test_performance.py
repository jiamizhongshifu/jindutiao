"""
性能测试脚本 - 测试配置管理器的启动和Tab切换性能
"""
import sys
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 设置UTF-8输出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config_gui import ConfigManager

def test_startup_performance():
    """测试启动性能"""
    print("=" * 60)
    print("配置管理器性能测试")
    print("=" * 60)

    app = QApplication(sys.argv)

    # 测试启动时间
    start_time = time.time()
    config_manager = ConfigManager()
    config_manager.show()
    startup_time = (time.time() - start_time) * 1000

    print(f"\n✓ 启动时间: {startup_time:.2f} ms")

    # 测试Tab初始化状态
    print("\n初始Tab状态:")
    for tab_name, initialized in config_manager._tab_initialized.items():
        status = "已初始化" if initialized else "未初始化(懒加载)"
        print(f"  - {tab_name}: {status}")

    # 模拟切换到主题Tab
    print("\n\n模拟切换到主题Tab...")
    tab_switch_start = time.time()

    def switch_to_theme_tab():
        config_manager.tabs.setCurrentIndex(2)  # 切换到主题Tab

        # 等待Tab创建完成
        QTimer.singleShot(100, check_theme_tab_loaded)

    def check_theme_tab_loaded():
        tab_switch_time = (time.time() - tab_switch_start) * 1000
        print(f"✓ 主题Tab首次加载时间: {tab_switch_time:.2f} ms")

        # 再次切换测试缓存效果
        print("\n再次切换到主题Tab(测试缓存)...")
        second_switch_start = time.time()
        config_manager.tabs.setCurrentIndex(0)  # 先切到其他Tab

        QTimer.singleShot(50, lambda: test_second_switch(second_switch_start))

    def test_second_switch(second_switch_start):
        config_manager.tabs.setCurrentIndex(2)  # 再切回主题Tab
        second_switch_time = (time.time() - second_switch_start) * 1000
        print(f"✓ 主题Tab再次切换时间: {second_switch_time:.2f} ms")

        # 显示最终Tab状态
        print("\n最终Tab状态:")
        for tab_name, initialized in config_manager._tab_initialized.items():
            status = "已初始化" if initialized else "未初始化"
            print(f"  - {tab_name}: {status}")

        print("\n" + "=" * 60)
        print("性能测试完成!")
        print("=" * 60)

        # 关闭应用
        QTimer.singleShot(1000, app.quit)

    # 延迟执行切换
    QTimer.singleShot(500, switch_to_theme_tab)

    sys.exit(app.exec())

if __name__ == "__main__":
    test_startup_performance()
