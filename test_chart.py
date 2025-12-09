"""快速测试折线图功能"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from statistics_manager import StatisticsManager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_chart")

# 创建统计管理器
app_dir = Path(".")
stats_manager = StatisticsManager(app_dir, logger)

# 测试 get_weekly_trend 方法
trend_data = stats_manager.get_weekly_trend(days=7)

print("=" * 60)
print("✅ get_weekly_trend() 测试结果:")
print("=" * 60)
for day in trend_data:
    print(f"日期: {day['date']}, 完成率: {day['completion_rate']:.1f}%, 总任务: {day['total_tasks']}, 已完成: {day['completed_tasks']}")

print("=" * 60)
print(f"✅ 测试通过! 获取到 {len(trend_data)} 天的数据")
print("=" * 60)

# 测试图表导入
try:
    from PySide6.QtCharts import QChart, QChartView, QLineSeries
    print("✅ PySide6.QtCharts 导入成功!")
except ImportError as e:
    print(f"❌ PySide6.QtCharts 导入失败: {e}")
