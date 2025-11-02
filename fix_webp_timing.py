"""修复WebP动画的帧延迟问题"""
from PIL import Image
import os

def fix_webp_timing(input_path, output_path=None, frame_duration=150):
    """
    修复WebP动画的帧延迟

    Args:
        input_path: 输入webp文件路径
        output_path: 输出webp文件路径(默认覆盖原文件)
        frame_duration: 每帧延迟时间(毫秒),默认150ms
    """
    if output_path is None:
        output_path = input_path

    try:
        print(f"正在处理: {input_path}")

        # 读取原始文件
        with Image.open(input_path) as img:
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
                # 复制当前帧
                frame = img.copy().convert("RGBA")
                frames.append(frame)

                # 显示原始延迟
                original_duration = img.info.get('duration', 0)
                print(f"    - 帧 {frame_num + 1}: {original_duration}ms → {frame_duration}ms")

        # 保存新文件,设置正确的帧延迟
        print(f"  正在保存修复后的文件...")
        frames[0].save(
            output_path,
            format='WEBP',
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,  # 每帧延迟(毫秒)
            loop=0,  # 无限循环
            lossless=True,  # 无损压缩
            quality=100,
            method=6  # 最佳压缩
        )

        # 验证修复结果
        print(f"  验证修复结果:")
        with Image.open(output_path) as img:
            total_duration = 0
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                duration = img.info.get('duration', 0)
                total_duration += duration

            print(f"    [OK] 总时长: {total_duration}ms ({total_duration/1000:.2f}秒)")
            print(f"    [OK] 平均帧延迟: {total_duration/img.n_frames:.1f}ms")

        print(f"  [SUCCESS] 成功修复: {output_path}\n")
        return True

    except Exception as e:
        print(f"  [ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 设置每帧延迟为150ms (8帧总共1.2秒)
    FRAME_DURATION = 150

    files_to_fix = [
        "kun.webp",
        "kun_100x100.webp"
    ]

    print("="*60)
    print(f"开始修复WebP动画帧延迟 (设置为 {FRAME_DURATION}ms/帧)")
    print("="*60 + "\n")

    success_count = 0
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_webp_timing(filepath, frame_duration=FRAME_DURATION):
                success_count += 1
        else:
            print(f"[WARNING] 文件不存在: {filepath}\n")

    print("="*60)
    print(f"修复完成! 成功: {success_count}/{len(files_to_fix)}")
    print("="*60)
