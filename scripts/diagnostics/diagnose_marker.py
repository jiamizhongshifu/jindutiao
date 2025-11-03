"""诊断进度条中GIF播放速度问题"""
import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QMovie

# 导入主程序
from main import ProgressBar
import json

# 加载配置
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 加载任务
with open('tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

app = QApplication(sys.argv)

# 创建进度条
bar = ProgressBar(config, tasks)
bar.show()

# 帧计数器
frame_count = 0
start_time = None
last_frame_time = None

def on_frame_changed(frame_num):
    global frame_count, start_time, last_frame_time

    current_time = time.time()

    if start_time is None:
        start_time = current_time
        print("\n=== 开始监控GIF动画帧率 ===")
        print(f"配置速度: {config.get('marker_speed', 100)}%")
        if bar.marker_movie:
            print(f"实际速度: {bar.marker_movie.speed()}%")
            print(f"循环次数: {bar.marker_movie.loopCount()}")
            print(f"总帧数: {bar.marker_movie.frameCount()}")

    frame_count += 1

    # 计算帧间隔
    if last_frame_time:
        interval = (current_time - last_frame_time) * 1000  # 转换为毫秒

        # 如果间隔异常短，输出警告
        if interval < 100:  # 正常应该是147ms左右
            print(f"[WARNING] 帧 {frame_num}: 间隔过短! {interval:.1f}ms (应该是147ms)")

    last_frame_time = current_time

    # 每完成一轮循环输出统计
    if frame_num == 0 and frame_count > 1:
        elapsed = current_time - start_time
        avg_fps = frame_count / elapsed
        print(f"\n循环完成 - 帧数: {frame_count}, 时间: {elapsed:.2f}s, 平均FPS: {avg_fps:.2f}")

        if avg_fps > 8.0:
            print(f"  [ERROR] FPS过高! ({avg_fps:.2f} > 8.0)")
        elif avg_fps > 7.0:
            print(f"  [WARNING] FPS偏高 ({avg_fps:.2f}, 预期6.8)")

# 连接信号
if bar.marker_movie:
    bar.marker_movie.frameChanged.connect(on_frame_changed)
    print(f"\n已连接frameChanged信号")
    print(f"marker_movie对象: {bar.marker_movie}")
    print(f"当前状态: {bar.marker_movie.state()}")
else:
    print("\n[ERROR] 没有找到marker_movie对象!")

# 10秒后输出总结
def show_summary():
    if start_time:
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed

        print(f"\n=== 诊断结果 ===")
        print(f"监控时长: {elapsed:.2f}s")
        print(f"总帧数: {frame_count}")
        print(f"平均FPS: {avg_fps:.2f}")
        print(f"预期FPS: ~6.8")

        if avg_fps > 8.0:
            print(f"\n[问题确认] 动画播放过快! (FPS {avg_fps:.2f} vs 预期 6.8)")
            print(f"可能原因:")
            print(f"  1. frameChanged信号被多次连接")
            print(f"  2. QMovie内部状态异常")
            print(f"  3. 定时器冲突")
        elif avg_fps > 7.2:
            print(f"\n[轻微异常] FPS略高于预期")
        else:
            print(f"\n[正常] FPS在正常范围内")

    app.quit()

QTimer.singleShot(10000, show_summary)

sys.exit(app.exec())
