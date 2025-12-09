"""Test script for Insights Generator"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from statistics_manager import StatisticsManager
from gaiya.core.insights_generator import InsightsGenerator
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_insights")

def main():
    print("\n" + "="*60)
    print("🧪 测试个性化洞察报告生成器")
    print("="*60 + "\n")

    # Initialize statistics manager
    app_dir = Path(".")
    stats_manager = StatisticsManager(app_dir, logger)

    # Initialize insights generator
    insights_gen = InsightsGenerator(stats_manager, logger)

    # Generate weekly insights
    print("📊 正在生成本周洞察报告...\n")
    insights = insights_gen.generate_weekly_insights(days=7)

    # Display formatted report
    formatted_report = insights_gen.format_for_display(insights)
    print(formatted_report)

    # Display raw data (for debugging)
    print("\n\n" + "="*60)
    print("🔍 原始数据 (调试用)")
    print("="*60)
    print(f"生成时间: {insights['generated_at']}")
    print(f"分析周期: {insights['period']}")
    print(f"\n生产力趋势:")
    print(f"  状态: {insights['productivity_trend']['status']}")
    print(f"  变化: {insights['productivity_trend']['change']:.2f}%")
    print(f"\n专注分析:")
    print(f"  总任务数: {insights['focus_analysis']['total_tasks']}")
    print(f"  完成任务数: {insights['focus_analysis']['completed_tasks']}")
    print(f"  平均完成率: {insights['focus_analysis']['avg_completion_rate']:.1f}%")

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()
