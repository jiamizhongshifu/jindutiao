"""
Activity Collector - User Behavior Data Collection Module

Collects user activity data including:
- Active window process information
- Window titles
- Browser URLs (Chrome/Edge/Firefox)

Author: GaiYa Team
Date: 2025-12-08
"""

import time
import logging
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime
import sqlite3
import os

import psutil
import win32gui
import win32process


@dataclass
class ActivitySnapshot:
    """User activity snapshot data structure"""
    app: str                    # Process name (e.g., "chrome.exe")
    window_title: str          # Window title
    url: str                   # Browser URL (empty if not a browser)
    timestamp: int             # Unix timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class ActivityCollector:
    """
    Activity Collector - Continuously collects user activity data

    Features:
    - Monitor active window process
    - Collect window titles
    - Extract browser URLs (Chrome/Edge/Firefox)
    - Persist data to local SQLite database
    - Configurable collection frequency
    """

    def __init__(self,
                 db_path: str = None,
                 collection_interval: int = 5,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize Activity Collector

        Args:
            db_path: SQLite database path (default: gaiya/data/activity_log.db)
            collection_interval: Collection interval in seconds (default: 5)
            logger: Logger instance
        """
        self.collection_interval = collection_interval
        self.logger = logger or logging.getLogger(__name__)

        # Database path
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'activity_log.db')

        self.db_path = db_path
        self._init_database()

        # State
        self.last_snapshot: Optional[ActivitySnapshot] = None
        self.is_collecting = False

        self.logger.info(f"ActivityCollector initialized (interval={collection_interval}s, db={db_path})")

    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create activity_snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app TEXT NOT NULL,
                window_title TEXT,
                url TEXT,
                timestamp INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index on timestamp for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON activity_snapshots(timestamp)
        ''')

        conn.commit()
        conn.close()

        self.logger.info("Activity database initialized")

    def get_active_window_info(self) -> Optional[ActivitySnapshot]:
        """
        Get current active window information

        Returns:
            ActivitySnapshot or None if failed
        """
        start_time = time.time()
        try:
            # Get active window handle
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            # Get window title
            window_title = win32gui.GetWindowText(hwnd)

            # Get process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # Get process information
            try:
                process = psutil.Process(pid)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "unknown"

            # Extract URL if browser
            url = self._extract_browser_url(app_name, window_title, hwnd)

            # Create snapshot
            snapshot = ActivitySnapshot(
                app=app_name,
                window_title=window_title,
                url=url,
                timestamp=int(time.time())
            )

            # Performance monitoring
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            self.logger.debug(f"📸 Activity snapshot: app={app_name}, title={window_title[:30]}, url={url[:50] if url else 'N/A'}, collect_time={elapsed:.1f}ms")

            return snapshot

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            self.logger.error(f"Failed to get active window info: {e} (time={elapsed:.1f}ms)")
            return None

    def _extract_browser_url(self, app_name: str, window_title: str, hwnd: int) -> str:
        """
        Extract URL from browser window

        Args:
            app_name: Process name
            window_title: Window title
            hwnd: Window handle

        Returns:
            URL string (empty if not a browser or extraction failed)
        """
        # Normalize app name
        app_lower = app_name.lower()

        # Check if it's a supported browser
        supported_browsers = ['chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe']
        if app_lower not in supported_browsers:
            return ""

        # For now, we'll extract URL from window title
        # Chrome/Edge format: "Page Title - URL"
        # This is a simplified approach; full URL extraction requires UI Automation

        try:
            # Simple heuristic: look for common URL patterns in title
            if ' - ' in window_title:
                parts = window_title.split(' - ')
                for part in parts:
                    part = part.strip()
                    if any(part.lower().startswith(proto) for proto in ['http://', 'https://', 'www.']):
                        return part

            # If window title contains domain-like strings
            for part in window_title.split():
                if '.' in part and len(part) > 4:
                    # Looks like a domain
                    if not part.startswith('http'):
                        return f"https://{part}"
                    return part

        except Exception as e:
            self.logger.debug(f"URL extraction failed: {e}")

        return ""

    def save_snapshot(self, snapshot: ActivitySnapshot):
        """
        Save activity snapshot to database

        Args:
            snapshot: ActivitySnapshot instance
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO activity_snapshots (app, window_title, url, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (snapshot.app, snapshot.window_title, snapshot.url, snapshot.timestamp))

            conn.commit()
            conn.close()

            self.logger.debug(f"Saved snapshot: {snapshot.app} - {snapshot.window_title[:50]}")

        except Exception as e:
            self.logger.error(f"Failed to save snapshot: {e}")

    def collect_once(self) -> Optional[ActivitySnapshot]:
        """
        Collect activity data once

        Returns:
            ActivitySnapshot or None
        """
        snapshot = self.get_active_window_info()
        if snapshot:
            self.save_snapshot(snapshot)
            self.last_snapshot = snapshot
        return snapshot

    def get_recent_snapshots(self, limit: int = 100) -> List[ActivitySnapshot]:
        """
        Get recent activity snapshots

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of ActivitySnapshot
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT app, window_title, url, timestamp
                FROM activity_snapshots
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            snapshots = [
                ActivitySnapshot(
                    app=row[0],
                    window_title=row[1],
                    url=row[2],
                    timestamp=row[3]
                )
                for row in rows
            ]

            return snapshots

        except Exception as e:
            self.logger.error(f"Failed to get recent snapshots: {e}")
            return []

    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Clean up old activity data

        Args:
            days_to_keep: Number of days to keep (default: 30)
        """
        try:
            cutoff_timestamp = int(time.time()) - (days_to_keep * 24 * 60 * 60)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM activity_snapshots
                WHERE timestamp < ?
            ''', (cutoff_timestamp,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            self.logger.info(f"Cleaned up {deleted_count} old snapshots (older than {days_to_keep} days)")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")

    def get_database_stats(self) -> dict:
        """
        Get database statistics

        Returns:
            Dictionary with stats (total_records, oldest_timestamp, newest_timestamp)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total records
            cursor.execute('SELECT COUNT(*) FROM activity_snapshots')
            total_records = cursor.fetchone()[0]

            # Oldest and newest timestamps
            cursor.execute('''
                SELECT MIN(timestamp), MAX(timestamp)
                FROM activity_snapshots
            ''')
            oldest, newest = cursor.fetchone()

            conn.close()

            return {
                'total_records': total_records,
                'oldest_timestamp': oldest,
                'newest_timestamp': newest,
                'oldest_date': datetime.fromtimestamp(oldest).isoformat() if oldest else None,
                'newest_date': datetime.fromtimestamp(newest).isoformat() if newest else None,
            }

        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
