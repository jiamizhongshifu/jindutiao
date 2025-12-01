import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
import uuid

# Setup logging
logger = logging.getLogger("gaiya.data.db")

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use Windows AppData directory for database
            # This ensures proper permissions and persistence across different working directories
            app_data_dir = Path.home() / "AppData" / "Local" / "GaiYa"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            db_path = app_data_dir / "user_data.db"

        self.db_path = str(db_path)
        logger.info(f"Database path: {self.db_path}")
        self._init_db()

    def _get_connection(self):
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.OperationalError as e:
            logger.error(f"Failed to open database at {self.db_path}: {e}")
            raise

    def _init_db(self):
        """Initialize the database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Focus Sessions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id TEXT PRIMARY KEY,
                time_block_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes INTEGER,
                status TEXT
            )
        ''')

        # Activity Sessions Table (Aggregated data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_sessions (
                id TEXT PRIMARY KEY,
                process_name TEXT,
                window_title TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER,
                category TEXT
            )
        ''')

        # App Categories Table (User rules)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_categories (
                process_name TEXT PRIMARY KEY,
                category TEXT,
                is_ignored BOOLEAN DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

        self._seed_defaults()

    def _seed_defaults(self):
        """Seed default categories if table is empty."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if empty
        cursor.execute('SELECT Count(*) FROM app_categories')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        defaults = [
            # Office productivity
            ("WINWORD.EXE", "PRODUCTIVE", False),
            ("EXCEL.EXE", "PRODUCTIVE", False),
            ("POWERPNT.EXE", "PRODUCTIVE", False),
            # Development tools
            ("CODE.EXE", "PRODUCTIVE", False),
            ("Cursor.exe", "PRODUCTIVE", False),
            ("IDEA64.EXE", "PRODUCTIVE", False),
            ("pycharm64.exe", "PRODUCTIVE", False),
            ("devenv.exe", "PRODUCTIVE", False),  # Visual Studio
            # Design tools
            ("FIGMA.EXE", "PRODUCTIVE", False),
            ("Photoshop.exe", "PRODUCTIVE", False),
            ("Illustrator.exe", "PRODUCTIVE", False),
            # Communication & Social
            ("Weixin.exe", "LEISURE", False),  # 微信正确的进程名
            ("WeChat.exe", "LEISURE", False),  # 兼容不同版本
            ("QQ.EXE", "LEISURE", False),
            ("TIM.exe", "LEISURE", False),
            ("DingTalk.exe", "LEISURE", False),  # 钉钉
            ("Feishu.exe", "LEISURE", False),  # 飞书
            # Entertainment
            ("STEAM.EXE", "LEISURE", False),
            ("WeGame.exe", "LEISURE", False),
            ("qqmusic.exe", "LEISURE", False),
            ("cloudmusic.exe", "LEISURE", False),  # 网易云音乐
            # Browsers (neutral - depends on usage)
            ("chrome.exe", "NEUTRAL", False),
            ("msedge.exe", "NEUTRAL", False),
            ("firefox.exe", "NEUTRAL", False),
            # System
            ("explorer.exe", "NEUTRAL", False),
            ("Taskmgr.exe", "NEUTRAL", False),
            # GaiYa app itself (ignore to avoid self-tracking)
            ("GaiYa-v1.6.exe", "NEUTRAL", True),
            ("GaiYa.exe", "NEUTRAL", True),
            ("main.exe", "NEUTRAL", True)  # For development builds
        ]

        cursor.executemany(
            'INSERT INTO app_categories (process_name, category, is_ignored) VALUES (?, ?, ?)',
            defaults
        )
        conn.commit()
        conn.close()

    # --- Focus Session Methods ---

    def create_focus_session(self, time_block_id: str) -> str:
        """Start a new focus session."""
        session_id = str(uuid.uuid4())
        start_time = datetime.now()

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO focus_sessions (id, time_block_id, start_time, status)
            VALUES (?, ?, ?, ?)
        ''', (session_id, time_block_id, start_time, "RUNNING"))
        conn.commit()
        conn.close()
        return session_id

    def complete_focus_session(self, session_id: str):
        """Mark a session as completed."""
        self._update_session_status(session_id, "COMPLETED")

    def interrupt_focus_session(self, session_id: str):
        """Mark a session as interrupted."""
        self._update_session_status(session_id, "INTERRUPTED")

    def _update_session_status(self, session_id: str, status: str):
        end_time = datetime.now()
        conn = self._get_connection()
        cursor = conn.cursor()

        # Calculate duration
        cursor.execute('SELECT start_time FROM focus_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row[0]) if isinstance(row[0], str) else row[0]
            # Handle implementation differences where sqlite might return string or datetime
            if isinstance(start_time, str):
                 start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')

            duration = int((end_time - start_time).total_seconds() / 60)

            cursor.execute('''
                UPDATE focus_sessions
                SET end_time = ?, status = ?, duration_minutes = ?
                WHERE id = ?
            ''', (end_time, status, duration, session_id))
            conn.commit()
        conn.close()

    def get_active_focus_sessions(self):
        """Get all currently running focus sessions.

        Returns:
            dict: {time_block_id: session_id} for all RUNNING sessions
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT time_block_id, id FROM focus_sessions
            WHERE status = 'RUNNING'
        ''')
        rows = cursor.fetchall()
        conn.close()

        # Return dict mapping time_block_id to session_id
        return {row[0]: row[1] for row in rows}

    def get_completed_focus_sessions_for_blocks(self, time_block_ids: list):
        """Check if any of the given time blocks have completed focus sessions today.

        Args:
            time_block_ids: List of time block IDs to check

        Returns:
            set: Set of time_block_ids that have completed sessions today
        """
        if not time_block_ids:
            return set()

        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        conn = self._get_connection()
        cursor = conn.cursor()

        # Use parameterized query with placeholders
        placeholders = ','.join('?' * len(time_block_ids))
        query = f'''
            SELECT DISTINCT time_block_id FROM focus_sessions
            WHERE time_block_id IN ({placeholders})
            AND start_time >= ?
            AND status = 'COMPLETED'
        '''

        cursor.execute(query, (*time_block_ids, start_of_day))
        rows = cursor.fetchall()
        conn.close()

        return {row[0] for row in rows}

    def get_completed_focus_sessions_with_time(self, time_block_ids: list):
        """Get completed focus sessions with their actual start times.

        Args:
            time_block_ids: List of time block IDs to check

        Returns:
            dict: {time_block_id: start_time (datetime)} for completed sessions today
        """
        if not time_block_ids:
            return {}

        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        conn = self._get_connection()
        cursor = conn.cursor()

        placeholders = ','.join('?' * len(time_block_ids))
        query = f'''
            SELECT time_block_id, start_time FROM focus_sessions
            WHERE time_block_id IN ({placeholders})
            AND start_time >= ?
            AND status = 'COMPLETED'
        '''

        cursor.execute(query, (*time_block_ids, start_of_day))
        rows = cursor.fetchall()
        conn.close()

        # Convert to dict, keeping the latest session if multiple exist
        result = {}
        for row in rows:
            time_block_id = row[0]
            start_time_str = row[1]
            # Parse datetime from string
            if isinstance(start_time_str, str):
                start_time = datetime.fromisoformat(start_time_str)
            else:
                start_time = start_time_str
            result[time_block_id] = start_time

        return result

    def get_all_completed_focus_sessions_today(self):
        """Get all completed focus sessions for today (global, not limited to specific time blocks).

        Returns:
            dict: {time_block_id: start_time (datetime)} for all completed sessions today
        """
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        conn = self._get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT time_block_id, start_time FROM focus_sessions
            WHERE start_time >= ?
            AND status = 'COMPLETED'
            ORDER BY start_time ASC
        '''

        cursor.execute(query, (start_of_day,))
        rows = cursor.fetchall()
        conn.close()

        # Convert to dict
        result = {}
        for row in rows:
            time_block_id = row[0]
            start_time_str = row[1]
            # Parse datetime from string
            if isinstance(start_time_str, str):
                start_time = datetime.fromisoformat(start_time_str)
            else:
                start_time = start_time_str
            # Keep all sessions (multiple sessions for same time_block_id are allowed)
            # Use a composite key to avoid overwriting
            result[f"{time_block_id}_{start_time.strftime('%H%M%S')}"] = start_time

        return result

    # --- Activity Tracking Methods ---

    def save_activity_session(self, process_name, window_title, start_time, end_time, duration_seconds):
        """Save an aggregated activity session."""
        # Check if app is ignored
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_ignored FROM app_categories WHERE process_name = ?', (process_name,))
        row = cursor.fetchone()

        # Skip saving if app is ignored
        if row and row[0] == 1:
            conn.close()
            return

        session_id = str(uuid.uuid4())
        category = self.get_app_category(process_name)

        cursor.execute('''
            INSERT INTO activity_sessions (id, process_name, window_title, start_time, end_time, duration_seconds, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, process_name, window_title, start_time, end_time, duration_seconds, category))
        conn.commit()
        conn.close()

    def get_app_category(self, process_name: str) -> str:
        """Get category for an app, return 'UNKNOWN' if not found."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT category FROM app_categories WHERE process_name = ?', (process_name,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "UNKNOWN"

    def get_all_app_categories(self) -> list:
        """Get all app categories."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT process_name, category, is_ignored FROM app_categories')
        rows = cursor.fetchall()
        conn.close()
        return rows

    def set_app_category(self, process_name: str, category: str, is_ignored: bool = False):
        """Set or update a category rule."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO app_categories (process_name, category, is_ignored)
            VALUES (?, ?, ?)
            ON CONFLICT(process_name) DO UPDATE SET category = ?, is_ignored = ?
        ''', (process_name, category, is_ignored, category, is_ignored))
        conn.commit()
        conn.close()

    def clear_activity_data(self):
        """Delete all recorded activity sessions."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM activity_sessions')
        conn.commit()
        conn.close()

    def cleanup_old_data(self, days: int = 90):
        """Remove focus/activity sessions older than N days."""
        cutoff = datetime.now() - timedelta(days=days)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM focus_sessions WHERE start_time < ?', (cutoff,))
        cursor.execute('DELETE FROM activity_sessions WHERE start_time < ?', (cutoff,))
        conn.commit()
        conn.close()

    # --- Reporting Methods ---

    def get_today_focus_stats(self):
        """Get focus sessions for today."""
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT time_block_id, sum(duration_minutes), count(*)
            FROM focus_sessions
            WHERE start_time >= ? AND status = 'COMPLETED'
            GROUP BY time_block_id
        ''', (start_of_day,))

        stats = {} # {block_id: (duration, count)}
        for row in cursor.fetchall():
            stats[row[0]] = {"duration": row[1], "count": row[2]}

        # Get total
        cursor.execute('''
            SELECT sum(duration_minutes) FROM focus_sessions
            WHERE start_time >= ? AND status = 'COMPLETED'
        ''', (start_of_day,))
        total = cursor.fetchone()[0] or 0

        conn.close()
        return {"by_block": stats, "total_minutes": total}

    def get_today_activity_stats(self):
        """Get aggregated stats for today."""
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total duration by category (exclude ignored apps)
        cursor.execute('''
            SELECT a.category, sum(a.duration_seconds)
            FROM activity_sessions a
            LEFT JOIN app_categories c ON a.process_name = c.process_name
            WHERE a.start_time >= ?
            AND (c.is_ignored IS NULL OR c.is_ignored = 0)
            GROUP BY a.category
        ''', (start_of_day,))

        category_totals = {
            "PRODUCTIVE": 0,
            "LEISURE": 0,
            "NEUTRAL": 0,
            "UNKNOWN": 0
        }
        total_seconds = 0

        for row in cursor.fetchall():
            cat = row[0]
            secs = row[1]
            if cat in category_totals:
                category_totals[cat] = secs
            else:
                category_totals["UNKNOWN"] += secs # Fallback
            total_seconds += secs

        # Top Apps (exclude ignored apps)
        cursor.execute('''
            SELECT a.process_name, a.category, sum(a.duration_seconds) as total_secs
            FROM activity_sessions a
            LEFT JOIN app_categories c ON a.process_name = c.process_name
            WHERE a.start_time >= ?
            AND (c.is_ignored IS NULL OR c.is_ignored = 0)
            GROUP BY a.process_name
            ORDER BY total_secs DESC
            LIMIT 10
        ''', (start_of_day,))

        top_apps = []
        for row in cursor.fetchall():
            top_apps.append({
                "name": row[0],
                "category": row[1],
                "duration": row[2]
            })

        conn.close()

        return {
            "total_seconds": total_seconds,
            "categories": category_totals,
            "top_apps": top_apps
        }

# Global instance
db = DatabaseManager()
