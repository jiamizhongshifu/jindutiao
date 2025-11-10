"""测试欢迎对话框"""

import sys
from PySide6.QtWidgets import QApplication
from gaiya.ui.onboarding import WelcomeDialog


def main():
    app = QApplication(sys.argv)

    # 创建并显示欢迎对话框
    dialog = WelcomeDialog()
    result = dialog.exec()

    if result == WelcomeDialog.DialogCode.Accepted:
        print("用户选择：开始配置")
    else:
        print("用户选择：暂时跳过")

    return 0


if __name__ == "__main__":
    sys.exit(main())
