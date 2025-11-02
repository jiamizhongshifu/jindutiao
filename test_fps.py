"""测试GIF动画实际播放帧率"""
import sys
import time
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QMovie
from PySide6.QtCore import QTimer

class FPSTest(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF FPS Test")
        self.resize(200, 200)

        # 加载动画
        self.movie = QMovie('kun.webp')
        self.setMovie(self.movie)

        # 记录帧数和时间
        self.frame_count = 0
        self.start_time = None

        # 设置不同速度测试
        test_speed = 100  # 测试100%速度
        self.movie.setSpeed(test_speed)
        self.movie.setCacheMode(QMovie.CacheAll)

        print(f"=== GIF Animation FPS Test ===")
        print(f"File: kun.webp")
        print(f"Total frames: {self.movie.frameCount()}")
        print(f"Speed setting: {test_speed}%")
        print(f"Loop count: {self.movie.loopCount()}")

        # 连接信号
        self.movie.frameChanged.connect(self.on_frame_changed)

        # 启动动画
        self.movie.start()
        self.show()

        # 10秒后停止测试
        QTimer.singleShot(10000, self.stop_test)

    def on_frame_changed(self, frame_num):
        if self.start_time is None:
            self.start_time = time.time()
            print(f"\nStarting frame counting...")

        self.frame_count += 1

        # 每完成一轮循环输出一次
        if frame_num == 0 and self.frame_count > 1:
            elapsed = time.time() - self.start_time
            avg_fps = self.frame_count / elapsed
            print(f"Loop completed. Frames: {self.frame_count}, Time: {elapsed:.2f}s, Avg FPS: {avg_fps:.2f}")

    def stop_test(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            avg_fps = self.frame_count / elapsed

            print(f"\n=== Test Results ===")
            print(f"Total frames rendered: {self.frame_count}")
            print(f"Total time: {elapsed:.2f}s")
            print(f"Average FPS: {avg_fps:.2f}")
            print(f"Expected FPS: ~6.8")

            if avg_fps > 7.5:
                print(f"\n[WARNING] Animation is playing TOO FAST!")
                print(f"Actual FPS ({avg_fps:.2f}) is significantly higher than expected (6.8)")
            elif avg_fps < 6.0:
                print(f"\n[WARNING] Animation is playing too slow")
            else:
                print(f"\n[OK] Animation speed is normal")

        QApplication.quit()

app = QApplication(sys.argv)
test = FPSTest()
sys.exit(app.exec())
