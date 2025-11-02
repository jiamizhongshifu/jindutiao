"""检查WebP文件的真实帧延迟"""
from PIL import Image
import os

def check_webp_delays(filepath):
    """检查WebP文件的帧延迟"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return

    try:
        with Image.open(filepath) as img:
            print(f"\n{'='*60}")
            print(f"文件: {filepath}")
            print(f"格式: {img.format}")
            print(f"尺寸: {img.size}")

            if not getattr(img, "is_animated", False):
                print("❌ 不是动画文件")
                return

            print(f"总帧数: {img.n_frames}")
            print(f"\n帧延迟信息:")
            print("-" * 60)

            delays = []
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                duration = img.info.get('duration', 0)
                delays.append(duration)
                print(f"帧 {frame_num + 1}: {duration}ms")

            print("-" * 60)
            total_duration = sum(delays)
            avg_delay = total_duration / len(delays) if delays else 0

            print(f"总时长: {total_duration}ms ({total_duration/1000:.2f}秒)")
            print(f"平均帧延迟: {avg_delay:.1f}ms")

            loop = img.info.get('loop', None)
            print(f"循环设置: {loop if loop is not None else '无限循环 (默认)'}")

            # 判断是否需要手动控制
            if all(d == 0 for d in delays):
                print(f"\n⚠️  所有帧延迟都是0ms - 需要手动控制")
            elif avg_delay > 0:
                print(f"\n✅ 帧延迟正常 ({avg_delay:.1f}ms) - QMovie应该可以正常播放")

            print("="*60)
            return delays

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n检查WebP文件的帧延迟设置\n")

    files = [
        "kun.webp",
        "kun_100x100.webp"
    ]

    for filepath in files:
        if os.path.exists(filepath):
            check_webp_delays(filepath)
        else:
            print(f"\n⚠️  文件不存在: {filepath}")
