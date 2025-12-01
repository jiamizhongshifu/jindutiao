"""
测试行为统计数据
"""
import sys
import io
from pathlib import Path
import os

# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from gaiya.data.db_manager import DatabaseManager

app_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "GaiYa"
db = DatabaseManager(app_dir / "user_data.db")

print("=" * 60)
print("Activity Stats Test")
print("=" * 60)

# Test get_today_activity_stats()
print("\n[Test] Calling get_today_activity_stats()...")
try:
    stats = db.get_today_activity_stats()

    print("\nReturned data structure:")
    print(f"  Keys: {list(stats.keys())}")
    print(f"\n  total_seconds: {stats['total_seconds']} ({stats['total_seconds']//60} minutes)")

    print(f"\n  categories:")
    for cat, secs in stats['categories'].items():
        minutes = secs // 60
        print(f"    - {cat}: {secs}s ({minutes}min)")

    print(f"\n  top_apps: {len(stats['top_apps'])} apps")
    if stats['top_apps']:
        print("\n  Top 5 apps:")
        for i, app in enumerate(stats['top_apps'][:5], 1):
            name = app.get('name', 'Unknown')
            category = app.get('category', 'UNKNOWN')
            duration = app.get('duration', 0)
            minutes = duration // 60
            print(f"    #{i} {name} ({category}): {duration}s ({minutes}min)")
    else:
        print("    No apps data!")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
