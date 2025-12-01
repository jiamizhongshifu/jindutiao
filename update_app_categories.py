"""
更新应用分类配置
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
print("Updating App Categories")
print("=" * 60)

# New categories to add/update
new_categories = [
    ("Weixin.exe", "LEISURE", False),  # Correct WeChat process name
    ("chrome.exe", "NEUTRAL", False),  # Update from UNKNOWN
    ("msedge.exe", "NEUTRAL", False),  # Update from UNKNOWN
    ("Cursor.exe", "PRODUCTIVE", False),  # Add Cursor editor
    ("firefox.exe", "NEUTRAL", False),
    ("CODE.EXE", "PRODUCTIVE", False),
    ("pycharm64.exe", "PRODUCTIVE", False),
    ("DingTalk.exe", "LEISURE", False),
    ("Feishu.exe", "LEISURE", False),
    ("qqmusic.exe", "LEISURE", False),
    ("cloudmusic.exe", "LEISURE", False),
    # Ignore GaiYa itself
    ("GaiYa-v1.6.exe", "NEUTRAL", True),
    ("GaiYa.exe", "NEUTRAL", True),
    ("main.exe", "NEUTRAL", True),
]

print("\n[1] Updating categories...")
for process, category, is_ignored in new_categories:
    try:
        db.set_app_category(process, category, is_ignored)
        print(f"  OK: {process} -> {category}")
    except Exception as e:
        print(f"  ERROR: {process} -> {e}")

# Print current configuration
print("\n[2] Current app categories:")
categories = db.get_all_app_categories()
print(f"    Total: {len(categories)} apps configured\n")

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for process, category, is_ignored in categories:
    if not is_ignored:
        by_category[category].append(process)

for category in ["PRODUCTIVE", "LEISURE", "NEUTRAL", "UNKNOWN"]:
    apps = by_category.get(category, [])
    if apps:
        print(f"  {category} ({len(apps)} apps):")
        for app in sorted(apps):
            print(f"    - {app}")

print("\n" + "=" * 60)
print("Update completed!")
print("=" * 60)
print("\nPlease restart GaiYa app to apply changes.")
