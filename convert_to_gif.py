"""将WebP转换为GIF格式,并设置正确的帧延迟"""
from PIL import Image
import os

def webp_to_gif(webp_path, gif_path=None, frame_duration=150):
    """
    将WebP转换为GIF,设置正确的帧延迟

    Args:
        webp_path: 输入webp文件路径
        gif_path: 输出gif文件路径(默认同名.gif)
        frame_duration: 每帧延迟时间(毫秒),默认150ms
    """
    if gif_path is None:
        gif_path = os.path.splitext(webp_path)[0] + ".gif"

    try:
        print(f"正在转换: {webp_path} -> {gif_path}")

        # 读取WebP文件
        with Image.open(webp_path) as img:
            if not getattr(img, "is_animated", False):
                print("  [WARNING] 不是动画文件,跳过")
                return False

            print(f"  原始信息:")
            print(f"    - 尺寸: {img.size}")
            print(f"    - 帧数: {img.n_frames}")

            # 提取所有帧
            frames = []
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                # 转换为RGB模式(GIF不支持RGBA,需要处理透明度)
                frame = img.copy()
                if frame.mode == 'RGBA':
                    # 创建白色背景
                    background = Image.new('RGB', frame.size, (255, 255, 255))
                    background.paste(frame, mask=frame.split()[3])  # 使用alpha通道作为mask
                    frame = background
                elif frame.mode != 'RGB':
                    frame = frame.convert('RGB')

                frames.append(frame)
                print(f"    - 提取帧 {frame_num + 1}")

        # 保存为GIF
        print(f"  正在保存GIF文件...")
        frames[0].save(
            gif_path,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,  # 每帧延迟(毫秒)
            loop=0,  # 无限循环
            optimize=False  # 不优化,保持原始质量
        )

        # 验证结果
        print(f"  验证结果:")
        with Image.open(gif_path) as gif:
            print(f"    [OK] 帧数: {gif.n_frames}")
            total_duration = 0
            for frame_num in range(gif.n_frames):
                gif.seek(frame_num)
                duration = gif.info.get('duration', 0)
                total_duration += duration
                print(f"    [OK] 帧 {frame_num + 1}: {duration}ms")

            print(f"    [OK] 总时长: {total_duration}ms ({total_duration/1000:.2f}秒)")

        file_size = os.path.getsize(gif_path)
        print(f"  [SUCCESS] 成功转换! 文件大小: {file_size/1024:.1f}KB\n")
        return True

    except Exception as e:
        print(f"  [ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 设置每帧延迟为150ms (8帧总共1.2秒)
    FRAME_DURATION = 150

    files_to_convert = [
        ("kun.webp", "kun.gif"),
        ("kun_100x100.webp", "kun_100x100.gif")
    ]

    print("="*60)
    print(f"开始转换WebP为GIF (帧延迟: {FRAME_DURATION}ms/帧)")
    print("="*60 + "\n")

    success_count = 0
    for webp_path, gif_path in files_to_convert:
        if os.path.exists(webp_path):
            if webp_to_gif(webp_path, gif_path, frame_duration=FRAME_DURATION):
                success_count += 1
        else:
            print(f"[WARNING] 文件不存在: {webp_path}\n")

    print("="*60)
    print(f"转换完成! 成功: {success_count}/{len(files_to_convert)}")
    print("="*60)
