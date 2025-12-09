"""
测试DEBUG级别日志增强效果
"""
import sys
import logging

# 配置DEBUG级别日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_debug_logs():
    """测试所有增强的DEBUG日志"""
    print("\n" + "="*80)
    print("测试行为识别和弹幕系统DEBUG日志增强")
    print("="*80 + "\n")

    print("📝 此测试将运行GaiYa主程序,请等待30秒观察DEBUG日志输出...")
    print("=" *80)
    print("\n预期会看到以下DEBUG日志:")
    print("  1. 🎯 Mode determined - ContentMode判断逻辑")
    print("  2. 🔍 Trend detected - 行为趋势检测")
    print("  3. ❄️ Cooldown activated - 冷却系统状态")
    print("  4. 🎲 Probability check - 概率调度决策")
    print("  5. 📸 Activity snapshot - 活动采集快照")
    print("  6. ⏱️ Collection loop cycle - 采集循环性能\n")
    print("="*80)

    # 导入主程序
    from main import main

    # 运行主程序
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("测试已手动停止")
        print("="*80)

if __name__ == "__main__":
    test_debug_logs()
