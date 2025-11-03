"""将原始 GIF 预先缩放到目标尺寸，避免运行时缩放导致的性能问题"""
from PIL import Image
import sys

def scale_gif(input_path, output_path, target_size):
    """
    缩放 GIF 动画到指定尺寸

    Args:
        input_path: 原始 GIF 路径
        output_path: 输出 GIF 路径
        target_size: 目标尺寸 (width, height)
    """
    try:
        # 打开原始 GIF
        with Image.open(input_path) as img:
            frames = []
            durations = []

            print(f"原始 GIF 信息:")
            print(f"  尺寸: {img.size}")
            print(f"  帧数: {getattr(img, 'n_frames', 1)}")

            # 处理每一帧
            try:
                frame_index = 0
                while True:
                    img.seek(frame_index)

                    # 缩放当前帧
                    scaled_frame = img.copy()
                    scaled_frame.thumbnail(target_size, Image.Resampling.LANCZOS)

                    # 转换为 RGBA 模式（保持透明度）
                    if scaled_frame.mode != 'RGBA':
                        scaled_frame = scaled_frame.convert('RGBA')

                    frames.append(scaled_frame)

                    # 保存帧持续时间（毫秒）
                    duration = img.info.get('duration', 100)
                    durations.append(duration)

                    frame_index += 1

            except EOFError:
                # 所有帧处理完毕
                pass

            print(f"\n处理完成:")
            print(f"  总共处理 {len(frames)} 帧")
            print(f"  目标尺寸: {target_size}")
            print(f"  实际尺寸: {frames[0].size}")

            # 保存缩放后的 GIF
            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=0,  # 无限循环
                    optimize=False,  # 不优化，保持原始帧率
                    disposal=2  # 恢复到背景色
                )
                print(f"\n成功保存到: {output_path}")
            else:
                print("错误: 没有找到任何帧")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== GIF 缩放工具 ===\n")

    # 缩放到 100x100
    scale_gif('kun.webp', 'kun_100x100.webp', (100, 100))

    print("\n提示: 将 config.json 中的 marker_image_path 改为 'kun_100x100.webp'")
    print("并移除或注释掉 main.py 中的 setScaledSize 调用")
