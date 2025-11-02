"""检查 GIF 原始尺寸"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QMovie

app = QApplication(sys.argv)

movie = QMovie('kun.webp')
if movie.isValid():
    # 获取第一帧来查看原始尺寸
    movie.jumpToFrame(0)
    pixmap = movie.currentPixmap()

    print("=== GIF 原始信息 ===")
    print(f"原始尺寸: {pixmap.width()} x {pixmap.height()}")
    print(f"总帧数: {movie.frameCount()}")
    print(f"缩放尺寸: {movie.scaledSize().width()} x {movie.scaledSize().height()}")

    # 测试设置缩放
    from PySide6.QtCore import QSize
    movie.setScaledSize(QSize(100, 100))
    print(f"\n设置缩放到 100x100 后:")
    print(f"缩放尺寸: {movie.scaledSize().width()} x {movie.scaledSize().height()}")

    print(f"\n如果原始尺寸远大于目标尺寸，实时缩放可能导致性能问题和视觉速度异常")
else:
    print("无法加载 GIF 文件")

app.quit()
