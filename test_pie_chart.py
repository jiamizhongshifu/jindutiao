"""Test script for Task Category Pie Chart"""

import sys
import io
import logging
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from statistics_manager import StatisticsManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_pie_chart")

def main():
    print("\n" + "="*60)
    print("🧪 测试任务分类饼图数据")
    print("="*60 + "\n")

    # Initialize statistics manager
    app_dir = Path(".")
    stats_manager = StatisticsManager(app_dir, logger)

    # Test get_task_categories() method
    print("📊 测试 get_task_categories() 方法...")
    categories = stats_manager.get_task_categories(days=7)

    if not categories:
        print("  ⚠️  没有任务分类数据")
        print("  💡 提示: 请确保 statistics.json 中有任务记录")
    else:
        print(f"  ✅ 成功获取 {len(categories)} 个分类\n")

        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category['name']}")
            print(f"     - 任务数: {category['count']}")
            print(f"     - 占比: {category['percentage']:.1f}%")
            print(f"     - 时长: {category['hours']:.1f} 小时")
            print()

    # Test get_category_distribution() method (原始方法)
    print("📊 测试 get_category_distribution() 方法...")
    category_dist = stats_manager.get_category_distribution(days=7)

    if not category_dist:
        print("  ⚠️  没有任务分类数据")
    else:
        print(f"  ✅ 成功获取 {len(category_dist)} 个分类\n")

        for category_name, stats in category_dist.items():
            print(f"  • {category_name}:")
            print(f"    - 总数: {stats['count']}")
            print(f"    - 完成: {stats['completed']}")
            print(f"    - 总时长: {stats['total_minutes']} 分钟")
            print()

    print("✅ 测试完成!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
