"""
测试行为识别功能是否正常工作
"""
import sys
import io
import time

# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from gaiya.services.activity_tracker import get_active_window_info

print("=" * 60)
print("Activity Tracking Test")
print("=" * 60)

# Test 1: Check current active window
print("\n[Test 1] Getting current active window...")
try:
    process_name, window_title = get_active_window_info()
    if process_name:
        print(f"SUCCESS: Got window info")
        print(f"   Process: {process_name}")
        print(f"   Title: {window_title}")
    else:
        print(f"FAILED: Cannot get window info (may need admin permission)")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Monitor for 5 times
print("\n[Test 2] Monitoring active window (5 times, 3s interval)...")
print("Please switch between different apps in the next 15 seconds...")

for i in range(5):
    time.sleep(3)
    try:
        process_name, window_title = get_active_window_info()
        if process_name:
            title_preview = window_title[:50] if window_title else ""
            print(f"  #{i+1} - {process_name}: {title_preview}...")
        else:
            print(f"  #{i+1} - Cannot get window info")
    except Exception as e:
        print(f"  #{i+1} - ERROR: {e}")

# Test 3: Check database connection
print("\n[Test 3] Checking database connection...")
try:
    from gaiya.data.db_manager import DatabaseManager
    from pathlib import Path
    import os

    app_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "GaiYa"
    db = DatabaseManager(app_dir / "user_data.db")

    # Try to save a test record
    from datetime import datetime, timedelta
    now = datetime.now()
    start_time = now - timedelta(seconds=10)

    db.save_activity_session(
        process_name="TEST.EXE",
        window_title="Test Window",
        start_time=start_time,
        end_time=now,
        duration_seconds=10
    )
    print("SUCCESS: Database connected, test record saved")

    # Query today's activity records
    sessions = db.get_activity_sessions_for_date(now.date())
    print(f"SUCCESS: Today's activity records: {len(sessions)}")

    if sessions:
        print("\nLast 5 records:")
        for session in sessions[-5:]:
            print(f"  - {session['process_name']}: {session['duration_seconds']}s")

except Exception as e:
    print(f"FAILED: Database test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
