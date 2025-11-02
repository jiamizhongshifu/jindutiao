"""检查WebP动画文件的帧延迟信息"""
from PIL import Image
import sys

def check_webp_frames(filepath):
    """检查WebP文件的每一帧延迟"""
    try:
        with Image.open(filepath) as img:
            print(f"文件: {filepath}")
            print(f"格式: {img.format}")
            print(f"尺寸: {img.size}")

            if not getattr(img, "is_animated", False):
                print("不是动画文件!")
                return

            print(f"总帧数: {img.n_frames}")
            print("\n帧延迟信息:")
            print("-" * 50)

            total_duration = 0
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                # 获取当前帧的延迟(毫秒)
                duration = img.info.get('duration', 0)
                total_duration += duration
                print(f"帧 {frame_num + 1}: {duration}ms")

            print("-" * 50)
            print(f"总时长: {total_duration}ms ({total_duration/1000:.2f}秒)")
            print(f"平均帧延迟: {total_duration/img.n_frames:.1f}ms")

            # 检查循环设置
            loop = img.info.get('loop', None)
            print(f"循环次数: {loop if loop is not None else '无限循环'}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 检查项目根目录的kun.webp
    check_webp_frames("kun.webp")
    print("\n" + "="*50 + "\n")
    # 如果存在,也检查kun_100x100.webp
    try:
        check_webp_frames("kun_100x100.webp")
    except:
        pass
