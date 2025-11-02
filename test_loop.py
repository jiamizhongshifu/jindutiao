"""测试GIF动画循环设置"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QMovie

app = QApplication(sys.argv)

# 测试原始文件的循环设置
movie = QMovie('kun.webp')

if movie.isValid():
    print("=== Original GIF File Info ===")
    print(f"Valid: {movie.isValid()}")
    print(f"Frame count: {movie.frameCount()}")
    print(f"Loop count: {movie.loopCount()}")
    print(f"  -1 = Infinite loop")
    print(f"   0 = No loop (play once)")
    print(f"  >0 = Specific number of loops")

    # 设置缓存模式
    movie.setCacheMode(QMovie.CacheAll)

    print(f"\n=== After Setting Cache Mode ===")
    print(f"Cache mode: {movie.cacheMode()}")

    if movie.loopCount() == -1:
        print("\n[OK] GIF is set to infinite loop")
    elif movie.loopCount() == 0:
        print("\n[WARNING] GIF will play only once!")
    else:
        print(f"\n[INFO] GIF will loop {movie.loopCount()} times")
else:
    print("[ERROR] Cannot load animation file")

app.quit()
