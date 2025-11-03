"""检查动画文件信息"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QMovie

app = QApplication(sys.argv)

movie = QMovie('kun.webp')

if movie.isValid():
    print("[OK] Animation file is valid")
    print(f"Frame count: {movie.frameCount()}")
    print(f"Current speed: {movie.speed()}%")

    # Check frame delays
    print(f"\nFrame delay info:")
    delays = []
    for i in range(min(movie.frameCount(), 10)):  # Only check first 10 frames
        movie.jumpToFrame(i)
        delay = movie.nextFrameDelay()
        delays.append(delay)
        print(f"  Frame {i}: {delay}ms")

    if delays:
        avg_delay = sum(delays) / len(delays)
        fps = 1000 / avg_delay if avg_delay > 0 else 0
        print(f"\nAverage frame delay: {avg_delay:.1f}ms")
        print(f"Theoretical FPS: {fps:.1f}")
else:
    print("[ERROR] Cannot load animation file")

app.quit()
