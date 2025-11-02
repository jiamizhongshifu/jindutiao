"""对比测试：原图 vs 不同速度设置"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt

class SpeedComparison(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Speed Comparison")
        self.resize(800, 300)

        layout = QVBoxLayout()

        # 标题
        title = QLabel("GIF Animation Speed Comparison")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # 对比区域
        compare_layout = QHBoxLayout()

        # 测试不同速度
        speeds = [70, 80, 90, 100, 110]

        for speed in speeds:
            container = QVBoxLayout()

            # 速度标签
            label = QLabel(f"{speed}% Speed")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 12pt; margin: 5px;")

            # 动画显示
            movie_label = QLabel()
            movie_label.setFixedSize(100, 100)
            movie_label.setAlignment(Qt.AlignCenter)
            movie_label.setStyleSheet("border: 1px solid #ccc;")

            movie = QMovie('kun.webp')
            movie.setSpeed(speed)
            movie.setCacheMode(QMovie.CacheAll)
            movie_label.setMovie(movie)
            movie.start()

            container.addWidget(label)
            container.addWidget(movie_label)

            compare_layout.addLayout(container)

        layout.addLayout(compare_layout)

        # 说明文字
        info = QLabel(
            "观察不同速度的动画效果，选择最接近原图的速度\n"
            "100% = 默认速度 (6.4 FPS)\n"
            "如果觉得快，可以在配置中设置为80%或70%"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(info)

        self.setLayout(layout)

app = QApplication(sys.argv)
window = SpeedComparison()
window.show()
sys.exit(app.exec())
