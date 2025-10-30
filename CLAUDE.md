# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Language

**IMPORTANT: Always respond to the user in Chinese (中文).**

## Project Overview

**PyDayBar** (桌面日历进度条) - A desktop time progress bar application that visualizes daily task schedules and current time progress.

**Tech Stack:**
- Python 3
- PySide6 (Qt for Python)
- JSON for tasks and configuration

**Core Concept:** A transparent, always-on-top progress bar that spans the screen (top or bottom) displaying colored blocks for scheduled tasks and a moving time marker. Features hover tooltips for task details and a comprehensive GUI configuration manager.

## Project Structure

**Core Files:**
- `main.py` - Main application entry point with TimeProgressBar widget (1012 lines)
- `config_gui.py` - Visual configuration manager GUI (1123 lines)
- `config.json` - Runtime configuration file
- `tasks.json` - Current task schedule
- `requirements.txt` - Python dependencies (PySide6>=6.5.0)
- `PyDayBar.spec` - PyInstaller packaging configuration
- `PyDayBar-Config.spec` - PyInstaller config for config GUI

**Template Files (8 presets):**
- `tasks_template_24h.json` - 24小时完整作息
- `tasks_template_workday.json` - 工作日作息
- `tasks_template_student.json` - 学生作息
- `tasks_template_freelancer.json` - 自由职业
- `tasks_template_night_shift.json` - 夜班作息
- `tasks_template_creator.json` - 内容创作者
- `tasks_template_fitness.json` - 健身达人
- `tasks_template_entrepreneur.json` - 创业者

## Development Status

**✅ ALL PHASES COMPLETED - Project is Production Ready**

**Phase 1 (完成):** Environment setup and transparent window
- ✅ Frameless, transparent, always-on-top window
- ✅ Multi-monitor support with screen index selection
- ✅ Windows-specific topmost window implementation

**Phase 2 (完成):** Static content rendering
- ✅ Background bar with configurable opacity and color
- ✅ Task blocks from JSON with custom colors
- ✅ Compact mode: tasks display consecutively without gaps
- ✅ Configurable corner radius for visual effects

**Phase 3 (完成):** Dynamic time marker
- ✅ Real-time moving time marker
- ✅ Three marker types: line, static image, animated GIF
- ✅ Configurable marker size and Y-axis offset
- ✅ Marker positioning in compact mode

**Phase 4 (完成):** System tray & configuration
- ✅ System tray icon with context menu
- ✅ Full-featured GUI configuration manager (`config_gui.py`)
- ✅ Visual task editor with drag-free time editing
- ✅ 8 preset templates with one-click loading
- ✅ Custom template save/load functionality
- ✅ Mouse hover tooltips with task details (removed click-through for interactivity)

**Phase 5 (完成):** Hot-reload & error handling
- ✅ QFileSystemWatcher for auto-reload on file changes
- ✅ Comprehensive logging system (`pydaybar.log`)
- ✅ JSON validation and error recovery
- ✅ Task time overlap detection and warnings
- ✅ Window visibility monitoring and auto-recovery

**Phase 6 (完成):** Packaging & distribution
- ✅ PyInstaller configuration with template bundling
- ✅ Two executables: `PyDayBar.exe` (main app) and `PyDayBar-Config.exe` (config GUI)
- ✅ Resource path handling for both dev and packaged environments
- ✅ Template files properly embedded in exe

## Development Commands

**Setup environment:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install PySide6
```

**Run application:**
```bash
python main.py
```

**Run configuration GUI:**
```bash
python config_gui.py
```

**Package for distribution:**
```bash
pip install pyinstaller
# Package main application
pyinstaller PyDayBar.spec
# Package configuration GUI (optional, can also be run via main app's tray menu)
pyinstaller PyDayBar-Config.spec
```

**⚠️ IMPORTANT: Packaging with Template Files**

When packaging the application, you MUST ensure all template files are included in the `.spec` file. This is a recurring issue that needs attention:

**Problem:** By default, PyInstaller only packages Python code and dependencies. Data files like JSON templates are NOT automatically included, causing "template not found" errors in the packaged exe.

**Solution:** After running `pyinstaller` for the first time, edit the generated `PyDayBar.spec` file:

```python
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # ADD ALL TEMPLATE FILES HERE:
        ('tasks_template_24h.json', '.'),
        ('tasks_template_workday.json', '.'),
        ('tasks_template_student.json', '.'),
        ('tasks_template_freelancer.json', '.'),
        ('tasks_template_night_shift.json', '.'),
        ('tasks_template_creator.json', '.'),
        ('tasks_template_fitness.json', '.'),
        ('tasks_template_entrepreneur.json', '.'),
        # Add any new template files here
    ],
    # ... rest of config
)
```

**Packaging Checklist:**
1. ✅ Run initial `pyinstaller` command to generate `.spec` file
2. ✅ Edit `PyDayBar.spec` to add all template files in `datas=[]` section
3. ✅ Verify all `.json` template files are listed
4. ✅ Run `pyinstaller PyDayBar.spec` to rebuild with templates included
5. ✅ Test the packaged exe to ensure templates load correctly

**When adding new templates:**
- Create the `tasks_template_*.json` file
- Add it to `PyDayBar.spec` in the `datas=[]` list
- Add corresponding button in `config_gui.py` template section
- Rebuild the package

## Key Technical Details

**Window Properties (Qt Flags):**
- `Qt.FramelessWindowHint` - No window borders
- `Qt.WindowStaysOnTopHint` - Always on top
- `Qt.WindowDoesNotAcceptFocus` - Doesn't steal focus from other apps
- `Qt.BypassWindowManagerHint` - Prevents being hidden by window manager
- `WA_TranslucentBackground` - Transparent background
- `WA_X11DoNotAcceptFocus` - X11-specific focus prevention
- **Note:** `WindowTransparentForInput` was removed to enable mouse interaction for hover tooltips

**Data Files:**
- `tasks.json` - Task definitions: `[{"start": "HH:MM", "end": "HH:MM", "task": "name", "color": "#RRGGBB"}, ...]`
  - Supports "24:00" as midnight/end of day
  - Tasks can be non-contiguous (gaps are handled)
- `config.json` - Configuration settings:
  ```json
  {
    "bar_height": 20,
    "position": "bottom",
    "background_color": "#505050",
    "background_opacity": 180,
    "marker_color": "#FF0000",
    "marker_width": 2,
    "marker_type": "line",  // "line", "image", "gif"
    "marker_image_path": "",
    "marker_size": 50,
    "marker_y_offset": 0,
    "screen_index": 0,
    "update_interval": 1000,
    "enable_shadow": true,
    "corner_radius": 0
  }
  ```

**Core Components:**
- `main.py` - Entry point with QApplication
- `TimeProgressBar(QWidget)` - Main window class with:
  - `paintEvent()` - Custom rendering for background, tasks, and time marker
  - `mouseMoveEvent()` - Handles hover detection for task tooltips
  - `eventFilter()` - Prevents window from being hidden
  - `force_show()` - Ensures window stays visible
  - `set_windows_topmost()` - Windows-specific always-on-top enforcement
- `QTimer` - Updates time marker every second + visibility monitoring
- `QSystemTrayIcon` - System tray with config/reload/quit menu
- `QFileSystemWatcher` - Hot-reload config/tasks without restart
- `config_gui.py` - Full GUI configuration manager with:
  - Visual task table editor with QTimeEdit widgets
  - Color picker integration
  - Template management (load/save)
  - Real-time validation
  - Two-way config.json/tasks.json editing

**Time Calculation (Compact Mode):**
- Compact mode displays tasks consecutively without gaps
- `calculate_time_range()` builds a position mapping from real time to compact percentage
- `task_positions[]` stores both original time ranges and compact percentages
- Current time percentage calculated by finding which task contains current time
- Helper functions:
  - `time_str_to_seconds(time_str)` converts "HH:MM" to seconds (handles 24:00)
  - `seconds_to_time_str(seconds)` converts back to "HH:MM"
- Time marker positioning:
  - If current time is within a task: interpolate position within that task block
  - If current time is between tasks: snap to next task's start
  - If current time is after all tasks: position at end (100%)

## Architecture Notes

**Click-Through vs Interaction Trade-off:**
The `WindowTransparentForInput` flag was **removed** to enable mouse interaction. The window now accepts mouse events for hover tooltips, but users can still click through to underlying windows in empty areas. This is achieved by:
- Removing `WindowTransparentForInput` flag
- Implementing `mouseMoveEvent()` to detect which task is hovered
- Implementing `leaveEvent()` to clear hover state
- Using `setMouseTracking(True)` to receive move events without clicks

**Rendering Order (paintEvent):**
1. Draw semi-transparent background bar at the bottom of the window
2. Draw all task blocks in compact mode (consecutive, no gaps)
   - Normal state: draw colored blocks in progress bar area
   - Hover state: draw expanded tooltip above progress bar with task details
   - Completed tasks: rendered in grayscale with reduced opacity
3. Draw time marker on top (three rendering modes):
   - Line mode: vertical line with optional shadow
   - Image mode: static PNG/JPG centered at marker position
   - GIF mode: animated GIF with frame-by-frame updates

**Hot-Reload Implementation:**
`QFileSystemWatcher` monitors both `config.json` and `tasks.json`. On file change:
1. Debounce with 300ms timer to avoid multiple rapid triggers
2. Re-add file to watch list (Windows editors may delete+recreate)
3. Call `reload_all()` which:
   - Reloads config and tasks from disk
   - Re-initializes marker image if path changed
   - Recalculates time ranges
   - Updates geometry if height/position/screen changed
   - Triggers `self.update()` to repaint

**Window Visibility Protection:**
Multiple layers ensure the window stays visible:
1. `eventFilter()` intercepts Hide events and blocks them
2. `visibility_timer` checks visibility every second
3. `force_show()` re-applies all show/raise/topmost settings
4. Windows-specific: `set_windows_topmost()` uses Win32 API to enforce HWND_TOPMOST

**Resource Path Handling:**
Two path systems for dev vs packaged environments:
- `app_dir` = directory containing exe/script (for user data: config.json, tasks.json, logs)
- `get_resource_path()` = PyInstaller's `_MEIPASS` temp dir (for bundled templates)
- This allows:
  - Templates bundled in exe (read from _MEIPASS)
  - User configs saved next to exe (written to app_dir)
  - Clean separation of read-only resources vs user data

**Configuration GUI Features:**
- **Preset buttons:** Quick-select common values (bar height: 细/标准/粗, marker size: 小/中/大)
- **Smart task addition:** New tasks auto-start at previous task's end time
- **Color palette cycling:** New tasks use Material Design colors in sequence
- **Template system:**
  - 8 built-in presets (24h, workday, student, freelancer, etc.)
  - Save custom templates as `tasks_custom_*.json`
  - Load custom templates from dropdown
- **Validation:**
  - End time must be > start time
  - Overlap detection with warning (allows saving with confirmation)
  - Time format validation (00:00-24:00)
- **Live preview:** Changes saved to disk, main app auto-reloads via file watcher

## Common Tasks & Solutions

**Adding a new template:**
1. Create `tasks_template_<name>.json` with task array
2. Add entry to `PyDayBar.spec` in `datas=[]` list
3. Add button in `config_gui.py` around line 366-418 (template section)
4. Rebuild package: `pyinstaller PyDayBar.spec`

**Troubleshooting template not found in packaged exe:**
- Verify template is listed in `PyDayBar.spec` `datas=[]` section
- Rebuild using `pyinstaller PyDayBar.spec` (not the command line)
- Check that `get_resource_path()` is used to load templates, not direct file paths

**Adjusting window position:**
- Change `position` in config.json: "top" or "bottom"
- For multi-monitor: set `screen_index` (0 = primary, 1+ = secondary monitors)
- Position is relative to available geometry (excludes taskbar space)

**Customizing time marker:**
- **Line mode:** Set `marker_type: "line"`, adjust `marker_color` and `marker_width`
- **Image mode:** Set `marker_type: "image"`, provide `marker_image_path` (PNG/JPG)
- **GIF mode:** Set `marker_type: "gif"`, provide path to animated GIF/WebP
- Adjust `marker_y_offset` to move marker up (positive) or down (negative)

**Debugging:**
- Check `pydaybar.log` in same directory as exe/script
- Log includes: startup, config loading, file changes, errors
- Use `logging.INFO` level for normal operation

**Performance optimization:**
- Increase `update_interval` (default 1000ms = 1 second) to reduce CPU usage
- Disable `enable_shadow` if not needed
- Use line marker instead of GIF for lower CPU usage

## Known Limitations

1. **Windows-only topmost enforcement:** `set_windows_topmost()` uses Win32 API, may need adaptation for Linux/Mac
2. **No drag-to-reorder:** Task order is determined by start time, edit via config GUI
3. **Single instance:** No built-in check, can run multiple instances (not recommended)
4. **No auto-startup:** User must manually add to Windows startup folder or Task Scheduler
5. **Compact mode only:** No option to display tasks with real-time gaps (by design)

## Future Enhancement Ideas

- [ ] Task completion tracking with statistics
- [ ] Color themes/presets (dark mode, light mode, etc.)
- [ ] Task categories/tags with filtering
- [ ] Export/import task schedules
- [ ] Notification/reminder system for upcoming tasks
- [ ] Multi-language support (currently Chinese/English mixed)
- [ ] Auto-startup installer option
- [ ] Backup/restore configuration
- [ ] Task recurrence patterns (daily, weekly, etc.)
