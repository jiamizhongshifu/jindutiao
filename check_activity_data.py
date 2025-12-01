"""
检查行为识别数据
"""
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup database
from gaiya.data.db_manager import DatabaseManager
import os

app_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "GaiYa"
db = DatabaseManager(app_dir / "user_data.db")

print("=" * 60)
print("Activity Data Check")
print("=" * 60)

# Check 1: Database file exists
print(f"\n[1] Database path: {app_dir / 'user_data.db'}")
print(f"    Exists: {(app_dir / 'user_data.db').exists()}")

# Check 2: Raw SQL query for today's data
print("\n[2] Querying activity_sessions table...")
start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
conn = db._get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT COUNT(*) FROM activity_sessions
    WHERE start_time >= ?
''', (start_of_day,))
total_records = cursor.fetchone()[0]
print(f"    Total records today: {total_records}")

if total_records > 0:
    cursor.execute('''
        SELECT process_name, window_title, duration_seconds, category, start_time
        FROM activity_sessions
        WHERE start_time >= ?
        ORDER BY start_time DESC
        LIMIT 10
    ''', (start_of_day,))

    print("\n    Last 10 records:")
    for row in cursor.fetchall():
        process, title, duration, category, start_time = row
        title_preview = title[:40] if title else ""
        print(f"      - {process} ({category}): {duration}s")
        print(f"        Title: {title_preview}...")
        print(f"        Time: {start_time}")

# Check 3: App categories
print("\n[3] App categories configuration...")
cursor.execute('SELECT COUNT(*) FROM app_categories')
total_categories = cursor.fetchone()[0]
print(f"    Total configured apps: {total_categories}")

if total_categories > 0:
    cursor.execute('SELECT process_name, category, is_ignored FROM app_categories LIMIT 10')
    print("\n    Sample categories:")
    for row in cursor.fetchall():
        process, category, is_ignored = row
        ignored_str = " (IGNORED)" if is_ignored else ""
        print(f"      - {process}: {category}{ignored_str}")

conn.close()

# Check 4: Activity stats
print("\n[4] Today's activity statistics...")
try:
    stats = db.get_today_activity_stats()
    if stats:
        print(f"    Total time: {stats['total_seconds']}s ({stats['total_seconds']//60}min)")
        print(f"    Categories:")
        for cat, seconds in stats['categories'].items():
            print(f"      - {cat}: {seconds}s ({seconds//60}min)")

        if stats['top_apps']:
            print(f"\n    Top apps:")
            for app in stats['top_apps'][:5]:
                print(f"      - {app['process']}: {app['duration']}s")
    else:
        print("    No stats available")
except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 60)
print("Check completed!")
print("=" * 60)
