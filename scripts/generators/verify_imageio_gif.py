"""验证imageio生成的GIF文件"""
from PIL import Image
import os

def verify_gif(filepath):
    """验证GIF文件的帧延迟"""
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return False

    try:
        with Image.open(filepath) as img:
            print(f"文件: {filepath}")
            print(f"格式: {img.format}")
            print(f"尺寸: {img.size}")

            if not getattr(img, "is_animated", False):
                print("不是动画文件!")
                return False

            print(f"总帧数: {img.n_frames}")
            print("\n帧延迟信息:")
            print("-" * 50)

            total_duration = 0
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                duration = img.info.get('duration', 0)
                total_duration += duration
                print(f"帧 {frame_num + 1}: {duration}ms")

            print("-" * 50)
            print(f"总时长: {total_duration}ms ({total_duration/1000:.2f}秒)")
            print(f"平均帧延迟: {total_duration/img.n_frames:.1f}ms")

            loop = img.info.get('loop', None)
            print(f"循环次数: {loop if loop is not None else '无限循环'}")

            return total_duration > 0  # 如果总时长>0说明有帧延迟

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("验证imageio生成的GIF文件")
    print("="*60 + "\n")

    files = [
        "kun_imageio.gif",
        "kun_100x100_imageio.gif"
    ]

    success_count = 0
    for filepath in files:
        result = verify_gif(filepath)
        if result:
            success_count += 1
        print("\n")

    print("="*60)
    print(f"验证完成! 成功: {success_count}/{len(files)}")
    print("="*60)
