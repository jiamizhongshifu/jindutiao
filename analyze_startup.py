"""
启动性能分析工具

使用cProfile分析应用启动时间,找出性能瓶颈
"""

import cProfile
import pstats
import io
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def profile_startup():
    """分析应用启动性能"""
    print("=" * 60)
    print("GaiYa 启动性能分析")
    print("=" * 60)

    # 创建profiler
    profiler = cProfile.Profile()

    # 记录开始时间
    start_time = time.time()

    # 开始profiling
    profiler.enable()

    try:
        # 导入主模块 (这会触发所有启动时导入)
        print("\n正在分析导入时间...")
        import main

        # 记录导入完成时间
        import_time = time.time() - start_time
        print(f"[OK] 模块导入完成: {import_time:.2f}秒")

        # 停止profiling
        profiler.disable()

    except Exception as e:
        profiler.disable()
        print(f"[ERROR] 分析失败: {e}")
        return

    # 生成统计报告
    print("\n" + "=" * 60)
    print("Top 30 最耗时的函数调用")
    print("=" * 60)

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.strip_dirs()
    ps.sort_stats('cumulative')
    ps.print_stats(30)

    print(s.getvalue())

    # 生成按调用次数排序的报告
    print("\n" + "=" * 60)
    print("Top 20 调用次数最多的函数")
    print("=" * 60)

    s2 = io.StringIO()
    ps2 = pstats.Stats(profiler, stream=s2)
    ps2.strip_dirs()
    ps2.sort_stats('calls')
    ps2.print_stats(20)

    print(s2.getvalue())

    # 分析特定模块的耗时
    print("\n" + "=" * 60)
    print("关键模块导入分析")
    print("=" * 60)

    key_modules = [
        'config_gui',
        'scene_editor',
        'statistics_manager',
        'ai_client',
        'gaiya.core',
        'gaiya.ui',
        'PySide6',
        'sqlite3',
        'httpx',
        'keyring'
    ]

    s3 = io.StringIO()
    ps3 = pstats.Stats(profiler, stream=s3)
    ps3.strip_dirs()
    ps3.sort_stats('cumulative')

    for module in key_modules:
        print(f"\n{module} 模块:")
        ps3.print_stats(module)

    # 保存完整报告到文件
    report_file = 'startup_profile_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("GaiYa 启动性能完整报告\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"总导入时间: {import_time:.2f}秒\n\n")
        f.write("=" * 60 + "\n")
        f.write("Top 100 最耗时的函数调用\n")
        f.write("=" * 60 + "\n\n")

        s_full = io.StringIO()
        ps_full = pstats.Stats(profiler, stream=s_full)
        ps_full.strip_dirs()
        ps_full.sort_stats('cumulative')
        ps_full.print_stats(100)
        f.write(s_full.getvalue())

    print("\n" + "=" * 60)
    print(f"[OK] 完整报告已保存到: {report_file}")
    print("=" * 60)

    # 总结
    print("\n" + "=" * 60)
    print("性能分析总结")
    print("=" * 60)
    print(f"- 总启动时间 (模块导入): {import_time:.2f}秒")
    print(f"- 目标启动时间: < 2秒")

    if import_time > 2:
        print(f"[WARNING] 当前启动时间超出目标 {import_time - 2:.2f}秒")
        print("\n建议优化方向:")
        print("1. 延迟加载 config_gui (预计减少1-2秒)")
        print("2. 延迟加载数据库连接 (预计减少0.3-0.5秒)")
        print("3. 异步加载场景资源 (预计减少0.5-0.8秒)")
    else:
        print("[OK] 启动时间符合目标!")

    print("=" * 60)


if __name__ == '__main__':
    profile_startup()
