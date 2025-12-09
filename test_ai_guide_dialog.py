"""测试AI引导对话框"""

import sys
from PySide6.QtWidgets import QApplication
from statistics_gui import AIGuideDialog

def main():
    app = QApplication(sys.argv)

    # 创建对话框
    dialog = AIGuideDialog()

    # 连接信号
    dialog.config_requested.connect(lambda: print("用户点击了'立即配置'按钮"))

    # 显示对话框
    dialog.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
