import sys
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
import logging
import os
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

# Import database manager
# Assuming the project structure allows this import, otherwise we might need relative imports
try:
    from gaiya.data.db_manager import db
except ImportError:
    # Fallback for running as script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from gaiya.data.db_manager import db

logger = logging.getLogger("gaiya.services.tracker")

# --- Win32 API Definitions via ctypes ---

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

# Constants
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MAX_PATH = 260

# Types
LPSTR = ctypes.c_char_p
LPWSTR = ctypes.c_wchar_p
DWORD = ctypes.c_ulong
HANDLE = ctypes.c_void_p

# Function signatures
user32.GetForegroundWindow.restype = HANDLE
user32.GetWindowThreadProcessId.argtypes = [HANDLE, ctypes.POINTER(DWORD)]
user32.GetWindowThreadProcessId.restype = DWORD

user32.GetWindowTextW.argtypes = [HANDLE, LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int

kernel32.OpenProcess.argtypes = [DWORD, ctypes.c_int, DWORD]
kernel32.OpenProcess.restype = HANDLE

kernel32.CloseHandle.argtypes = [HANDLE]
kernel32.CloseHandle.restype = ctypes.c_int

psapi.GetModuleFileNameExW.argtypes = [HANDLE, HANDLE, LPWSTR, DWORD]
psapi.GetModuleFileNameExW.restype = DWORD

def get_active_window_info():
    """
    Retrieves the process name and window title of the currently active foreground window.
    Returns: (process_name, window_title) or (None, None) on failure.
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None

    # Get Process ID
    pid = DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    
    # Get Window Title
    title_buffer = ctypes.create_unicode_buffer(MAX_PATH)
    user32.GetWindowTextW(hwnd, title_buffer, MAX_PATH)
    window_title = title_buffer.value

    # Get Process Name
    process_handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    process_name = "Unknown"
    
    if process_handle:
        img_path_buffer = ctypes.create_unicode_buffer(MAX_PATH)
        try:
            length = psapi.GetModuleFileNameExW(process_handle, None, img_path_buffer, MAX_PATH)
            if length > 0:
                full_path = img_path_buffer.value
                process_name = os.path.basename(full_path)
        finally:
            kernel32.CloseHandle(process_handle)
    
    return process_name, window_title

class ActivityTracker(QThread):
    """
    Background thread that polls the active window and aggregates usage into sessions.
    """
    session_ended = Signal(str, str, int) # process_name, title, duration
    
    def __init__(self, parent=None, polling_interval=5, min_session_duration=5):
        super().__init__(parent)
        self.is_running = False
        self.polling_interval = max(1, int(polling_interval))  # seconds
        self.min_session_duration = max(1, int(min_session_duration))  # seconds
        
        # Current tracking state
        self.current_process = None
        self.current_title = None
        self.current_start_time = None
        
        # Thread safety
        self.mutex = QMutex()
        self.condition = QWaitCondition()

    def run(self):
        """Main loop."""
        self.is_running = True
        logger.info("Activity Tracker started.")
        
        while self.is_running:
            try:
                self._check_activity()
            except Exception as e:
                logger.error(f"Error in activity tracker: {e}")
            
            # Sleep for N seconds (interruptible)
            self.mutex.lock()
            self.condition.wait(self.mutex, self.polling_interval * 1000)
            self.mutex.unlock()
            
        self._flush_current_session()
        logger.info("Activity Tracker stopped.")

    def stop(self):
        """Stop the tracker safely."""
        self.is_running = False
        self.condition.wakeAll()
        self.wait()

    def _check_activity(self):
        """Polls current window and handles session logic."""
        process_name, window_title = get_active_window_info()
        
        if not process_name:
            return

        now = datetime.now()

        # If this is the very first check
        if self.current_process is None:
            self.current_process = process_name
            self.current_title = window_title
            self.current_start_time = now
            return

        # Check if context changed (different app or different window title)
        # Note: We treat different window titles of same app as same session 
        # ONLY IF the app is usually a single-task thing? 
        # For MVP, let's strictly separate if process name OR title changes significantly.
        # Actually, for "Activity Classification", usually Process Name is enough.
        # But the PRD says: "continuous samples if process_name AND window_title same".
        
        # Let's relax title matching slightly: ignore empty titles or minor changes?
        # For now, strict adherence to PRD: same process AND same title.
        
        has_changed = (process_name != self.current_process) or (window_title != self.current_title)
        
        if has_changed:
            # 1. End current session
            self._flush_current_session()
            
            # 2. Start new session
            self.current_process = process_name
            self.current_title = window_title
            self.current_start_time = now

    def _flush_current_session(self):
        """Saves the current session to DB."""
        if not self.current_process or not self.current_start_time:
            return
            
        end_time = datetime.now()
        duration_seconds = int((end_time - self.current_start_time).total_seconds())
        
        # Ignore very short sessions (noise)
        if duration_seconds < self.min_session_duration:
            return
            
        try:
            # Save to DB
            db.save_activity_session(
                self.current_process,
                self.current_title,
                self.current_start_time,
                end_time,
                duration_seconds
            )
            
            # Emit signal (optional, for UI updates)
            self.session_ended.emit(self.current_process, self.current_title, duration_seconds)
            
        except Exception as e:
            logger.error(f"Failed to save activity session: {e}")

# Test execution
if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    tracker = ActivityTracker()
    tracker.start()
    
    print("Tracker running... Switch windows to test. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tracker.stop()
