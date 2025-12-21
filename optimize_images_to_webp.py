#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片WebP格式转换工具
自动将PNG图片转换为WebP格式以优化网站性能
"""

import os
import sys
from pathlib import Path
from PIL import Image

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def optimize_image_to_webp(input_path: str, output_path: str, quality: int = 85) -> dict:
    """
    将图片转换为WebP格式

    Args:
        input_path: 输入图片路径
        output_path: 输出WebP图片路径
        quality: WebP质量 (1-100, 推荐85)

    Returns:
        包含优化统计信息的字典
    """
    # 打开原始图片
    img = Image.open(input_path)

    # 获取原始文件大小
    original_size = os.path.getsize(input_path)

    # 转换并保存为WebP
    img.save(
        output_path,
        'WEBP',
        quality=quality,
        method=6  # 使用最佳压缩方法
    )

    # 获取优化后文件大小
    optimized_size = os.path.getsize(output_path)

    # 计算压缩比例
    reduction = (1 - optimized_size / original_size) * 100

    return {
        'input': input_path,
        'output': output_path,
        'original_size_kb': original_size / 1024,
        'optimized_size_kb': optimized_size / 1024,
        'reduction_percent': reduction
    }

def main():
    """主函数 - 批量转换图片"""

    # 图片目录
    images_dir = Path(__file__).parent / 'public' / 'images'

    # 要转换的图片列表 (PNG路径, WebP路径, 质量)
    images_to_convert = [
        ('GaiYa1120.png', 'GaiYa1120.webp', 85),
        ('logo-large.png', 'logo-large.webp', 85),
        ('logo.png', 'logo.webp', 90),  # Logo使用更高质量
        ('og-image.png', 'og-image.webp', 85),
    ]

    print("=" * 70)
    print("🎨 GaiYa官网图片WebP格式转换工具")
    print("=" * 70)
    print()

    total_original = 0
    total_optimized = 0
    results = []

    for png_name, webp_name, quality in images_to_convert:
        input_path = images_dir / png_name
        output_path = images_dir / webp_name

        # 检查文件是否存在
        if not input_path.exists():
            print(f"⚠️  跳过: {png_name} (文件不存在)")
            continue

        # 如果WebP已存在，询问是否覆盖
        if output_path.exists():
            print(f"ℹ️  {webp_name} 已存在，将覆盖...")

        # 转换图片
        try:
            result = optimize_image_to_webp(
                str(input_path),
                str(output_path),
                quality=quality
            )
            results.append(result)

            total_original += result['original_size_kb']
            total_optimized += result['optimized_size_kb']

            print(f"✅ {png_name}")
            print(f"   {result['original_size_kb']:.1f}KB → {result['optimized_size_kb']:.1f}KB")
            print(f"   减少 {result['reduction_percent']:.1f}%")
            print()

        except Exception as e:
            print(f"❌ 转换失败: {png_name}")
            print(f"   错误: {str(e)}")
            print()

    # 打印总结
    print("=" * 70)
    print("📊 转换总结")
    print("=" * 70)
    print(f"转换成功: {len(results)}/{len(images_to_convert)} 张图片")
    print(f"原始总大小: {total_original:.1f}KB ({total_original/1024:.2f}MB)")
    print(f"优化后总大小: {total_optimized:.1f}KB ({total_optimized/1024:.2f}MB)")

    if total_original > 0:
        total_reduction = (1 - total_optimized / total_original) * 100
        print(f"总压缩比例: {total_reduction:.1f}%")
        print(f"节省空间: {(total_original - total_optimized):.1f}KB")

    print()
    print("=" * 70)
    print("✨ 下一步操作:")
    print("=" * 70)
    print("1. 检查 public/images/ 目录下的 .webp 文件")
    print("2. 更新HTML文件使用 <picture> 标签")
    print("3. 提交代码并部署到Vercel")
    print("4. 使用Google PageSpeed Insights验证性能提升")
    print()

if __name__ == '__main__':
    # 检查Pillow是否安装
    try:
        from PIL import Image
    except ImportError:
        print("❌ 错误: 缺少Pillow库")
        print()
        print("请先安装Pillow:")
        print("  pip install Pillow")
        print()
        exit(1)

    main()
