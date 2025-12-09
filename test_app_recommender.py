"""Test script for App Recommender"""

import sys
import io
import logging
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from gaiya.core.app_recommender import AppRecommender

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_app_recommender")

def main():
    print("\n" + "="*60)
    print("🧪 测试智能应用分类推荐引擎")
    print("="*60 + "\n")

    # Initialize recommender
    recommender = AppRecommender(logger=logger)

    # Get stats
    stats = recommender.get_recommendation_stats()
    print(f"📊 推荐引擎统计:")
    print(f"  总应用数: {stats['total_known_apps']}")
    print(f"  规则数: {stats['total_rules']}")
    print(f"  PRODUCTIVE应用: {stats['productive_apps']}")
    print(f"  LEISURE应用: {stats['leisure_apps']}")
    print(f"  NEUTRAL应用: {stats['neutral_apps']}")
    print()

    # Test cases
    test_apps = [
        'code.exe',           # 精确匹配 - PRODUCTIVE
        'pycharm64.exe',      # 精确匹配 - PRODUCTIVE
        'wechat.exe',         # 精确匹配 - LEISURE
        'bilibili.exe',       # 精确匹配 - LEISURE
        'chrome.exe',         # 精确匹配 - NEUTRAL
        'vscode-insider.exe', # 关键词匹配 - PRODUCTIVE
        'my-game.exe',        # 关键词匹配 - LEISURE
        'unknown-app.exe',    # 未知 - NEUTRAL
    ]

    print("🔍 测试推荐:")
    print("-" * 60)

    for app_name in test_apps:
        rec = recommender.recommend_category(app_name)
        confidence_pct = int(rec['confidence'] * 100)

        print(f"\n📱 {app_name}")
        print(f"  {rec['emoji']} 推荐分类: {rec['category']}")
        print(f"  📊 置信度: {confidence_pct}%")
        print(f"  💭 理由: {rec['reason']}")
        print(f"  📝 说明: {rec['description']}")

    # Batch recommend
    print("\n" + "="*60)
    print("🚀 批量推荐测试")
    print("="*60 + "\n")

    batch_apps = ['notion.exe', 'steam.exe', 'cursor.exe']
    recommendations = recommender.batch_recommend(batch_apps)

    for app_name, rec in recommendations.items():
        print(f"✅ {app_name} -> {rec['emoji']} {rec['category']} ({int(rec['confidence']*100)}%)")

    print("\n✅ 测试完成!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
