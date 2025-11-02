"""使用imageio生成QMovie兼容的GIF文件"""
import imageio
from PIL import Image
import numpy as np

def create_gif_with_imageio(webp_path, gif_path, duration=150):
    """
    使用imageio创建GIF,确保帧延迟兼容QMovie

    Args:
        webp_path: 输入webp文件路径
        gif_path: 输出gif文件路径
        duration: 每帧延迟时间(毫秒),默认150ms
    """
    try:
        print(f"正在处理: {webp_path} -> {gif_path}")

        # 读取WebP文件
        with Image.open(webp_path) as img:
            if not getattr(img, "is_animated", False):
                print("  [WARNING] 不是动画文件,跳过")
                return False

            print(f"  原始信息:")
            print(f"    - 尺寸: {img.size}")
            print(f"    - 帧数: {img.n_frames}")

            # 提取所有帧为numpy数组
            frames = []
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                # 转换为RGB模式
                frame = img.copy()
                if frame.mode == 'RGBA':
                    # 创建白色背景
                    background = Image.new('RGB', frame.size, (255, 255, 255))
                    background.paste(frame, mask=frame.split()[3])
                    frame = background
                elif frame.mode != 'RGB':
                    frame = frame.convert('RGB')

                # 转换为numpy数组
                frames.append(np.array(frame))
                print(f"    - 提取帧 {frame_num + 1}")

        # 使用imageio保存GIF
        # duration单位是秒,需要转换
        duration_sec = duration / 1000.0
        print(f"  正在保存GIF文件 (每帧{duration}ms = {duration_sec}s)...")

        imageio.mimsave(
            gif_path,
            frames,
            duration=duration_sec,  # imageio使用秒为单位
            loop=0  # 无限循环
        )

        # 验证结果
        print(f"  验证结果:")
        reader = imageio.get_reader(gif_path)
        meta = reader.get_meta_data()
        print(f"    [OK] 帧数: {reader.count_frames()}")
        print(f"    [OK] 每帧延迟: {meta.get('duration', 'N/A') * 1000}ms")
        print(f"    [OK] 循环次数: {meta.get('loop', 'N/A')}")
        reader.close()

        print(f"  [SUCCESS] 成功创建GIF文件!\n")
        return True

    except Exception as e:
        print(f"  [ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 设置每帧延迟为150ms
    FRAME_DURATION = 150

    files_to_convert = [
        ("kun.webp", "kun_imageio.gif"),
        ("kun_100x100.webp", "kun_100x100_imageio.gif")
    ]

    print("="*60)
    print(f"使用imageio创建GIF (帧延迟: {FRAME_DURATION}ms/帧)")
    print("="*60 + "\n")

    success_count = 0
    for webp_path, gif_path in files_to_convert:
        import os
        if os.path.exists(webp_path):
            if create_gif_with_imageio(webp_path, gif_path, duration=FRAME_DURATION):
                success_count += 1
        else:
            print(f"[WARNING] 文件不存在: {webp_path}\n")

    print("="*60)
    print(f"转换完成! 成功: {success_count}/{len(files_to_convert)}")
    print("="*60)
