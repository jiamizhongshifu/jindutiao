import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
import uuid

# Setup logging
logger = logging.getLogger("gaiya.data.db")

class DatabaseManager:
    def __init__(self, db_path="user_data.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

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
            ("WINWORD.EXE", "PRODUCTIVE"),
            ("EXCEL.EXE", "PRODUCTIVE"),
            ("POWERPNT.EXE", "PRODUCTIVE"),
            ("Code.exe", "PRODUCTIVE"),
            ("idea64.exe", "PRODUCTIVE"),
            ("Figma.exe", "PRODUCTIVE"),
            ("WeChat.exe", "LEISURE"),
            ("QQ.exe", "LEISURE"),
            ("steam.exe", "LEISURE"),
            ("explorer.exe", "NEUTRAL"),
            ("chrome.exe", "UNKNOWN"),
            ("msedge.exe", "UNKNOWN")
        ]

        cursor.executemany(
            'INSERT INTO app_categories (process_name, category) VALUES (?, ?)',
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

    # --- Activity Tracking Methods ---

    def save_activity_session(self, process_name, window_title, start_time, end_time, duration_seconds):
        """Save an aggregated activity session."""
        session_id = str(uuid.uuid4())
        category = self.get_app_category(process_name)

        conn = self._get_connection()
        cursor = conn.cursor()
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

        # Total duration by category
        cursor.execute('''
            SELECT category, sum(duration_seconds)
            FROM activity_sessions
            WHERE start_time >= ?
            GROUP BY category
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

        # Top Apps
        cursor.execute('''
            SELECT process_name, category, sum(duration_seconds) as total_secs
            FROM activity_sessions
            WHERE start_time >= ?
            GROUP BY process_name
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
