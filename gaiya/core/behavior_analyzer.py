"""
Behavior Analyzer - Analyze user behavior and detect trends

Integrates ActivityCollector, AppClassifier, and DomainClassifier to provide
comprehensive behavior analysis including:
- Content mode detection (production/consumption/neutral/unknown)
- Activity duration tracking
- Behavior trend detection (focus_steady, moyu_start, moyu_steady, mode_switch, task_switch)

Author: GaiYa Team
Date: 2025-12-08
"""

import time
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

from .activity_collector import ActivitySnapshot
from .app_classifier import AppClassifier
from .domain_classifier import DomainClassifier


class ContentMode(Enum):
    """Content mode enumeration"""
    PRODUCTION = "production"      # Creating content (coding, writing)
    CONSUMPTION = "consumption"    # Consuming content (videos, social media)
    NEUTRAL = "neutral"            # Neither (email, chat)
    UNKNOWN = "unknown"            # Cannot determine


class BehaviorTrend(Enum):
    """Behavior trend enumeration"""
    FOCUS_STEADY = "focus_steady"      # Sustained production mode ≥20min
    MOYU_START = "moyu_start"          # Switched from production to consumption ≥3min
    MOYU_STEADY = "moyu_steady"        # Sustained consumption mode ≥15min
    MODE_SWITCH = "mode_switch"        # Switched between production/consumption
    TASK_SWITCH = "task_switch"        # Switched to different app
    NONE = "none"                      # No significant trend


@dataclass
class BehaviorInfo:
    """
    Comprehensive behavior information

    Attributes:
        app: Process name (e.g., "chrome.exe")
        app_type: App category (browser/ide/office/...)
        url: Browser URL (empty if not browser)
        domain: Extracted domain (e.g., "github.com")
        domain_category: Domain category (code/video/social/...)
        mode: Content mode (production/consumption/neutral/unknown)
        active_duration_sec: Duration in current state (seconds)
        trend: Detected behavior trend
        timestamp: Unix timestamp
    """
    app: str
    app_type: str
    url: str
    domain: str
    domain_category: str
    mode: str
    active_duration_sec: int
    trend: Optional[str]
    timestamp: int


class BehaviorAnalyzer:
    """
    Behavior Analyzer - Comprehensive user behavior analysis

    Features:
    - Classify apps and domains
    - Determine content mode with priority logic
    - Track activity duration
    - Detect behavior trends
    - Generate BehaviorInfo for danmaku engine
    """

    def __init__(self,
                 app_classifier: Optional[AppClassifier] = None,
                 domain_classifier: Optional[DomainClassifier] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize Behavior Analyzer

        Args:
            app_classifier: AppClassifier instance (creates new if None)
            domain_classifier: DomainClassifier instance (creates new if None)
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Classifiers
        self.app_classifier = app_classifier or AppClassifier(logger=logger)
        self.domain_classifier = domain_classifier or DomainClassifier(logger=logger)

        # State tracking
        self.current_app: Optional[str] = None
        self.current_mode: Optional[str] = None
        self.state_start_time: int = 0
        self.last_snapshot: Optional[ActivitySnapshot] = None

        # Thresholds (seconds)
        self.focus_steady_threshold = 20 * 60     # 20 minutes
        self.moyu_start_threshold = 3 * 60        # 3 minutes
        self.moyu_steady_threshold = 15 * 60      # 15 minutes

        self.logger.info("BehaviorAnalyzer initialized")

    def analyze(self, snapshot: ActivitySnapshot) -> BehaviorInfo:
        """
        Analyze activity snapshot and generate behavior info

        Args:
            snapshot: ActivitySnapshot from ActivityCollector

        Returns:
            BehaviorInfo with comprehensive analysis
        """
        # Classify app
        app_type = self.app_classifier.classify(snapshot.app)

        # Extract and classify domain
        domain = ""
        domain_category = "other"
        domain_mode = "unknown"

        if snapshot.url:
            domain = self.domain_classifier.extract_domain(snapshot.url) or ""
            if domain:
                domain_category, domain_mode = self.domain_classifier.classify(snapshot.url)

        # Determine content mode
        mode = self._determine_content_mode(
            app_type=app_type,
            domain=domain,
            domain_mode=domain_mode,
            window_title=snapshot.window_title
        )

        # Track duration and detect trends
        duration_sec = self._update_duration(snapshot.app, mode, snapshot.timestamp)
        trend = self._detect_trend(mode, duration_sec)

        # Build BehaviorInfo
        behavior_info = BehaviorInfo(
            app=snapshot.app,
            app_type=app_type,
            url=snapshot.url,
            domain=domain,
            domain_category=domain_category,
            mode=mode,
            active_duration_sec=duration_sec,
            trend=trend,
            timestamp=snapshot.timestamp
        )

        # Update state
        self.last_snapshot = snapshot

        return behavior_info

    def _determine_content_mode(self,
                                 app_type: str,
                                 domain: str,
                                 domain_mode: str,
                                 window_title: str) -> str:
        """
        Determine content mode with priority logic

        Priority:
        1. Domain rules (if browser with known domain)
        2. Window title keywords
        3. AppType default mode
        4. Unknown

        Args:
            app_type: App type from AppClassifier
            domain: Extracted domain
            domain_mode: Mode from DomainClassifier
            window_title: Window title

        Returns:
            Content mode string
        """
        # Priority 1: Domain rules
        if domain and domain_mode != "unknown":
            self.logger.debug(f"🎯 Mode determined: {domain_mode} (priority=1:domain, domain={domain})")
            return domain_mode

        # Priority 2: Window title keywords
        title_lower = window_title.lower()

        production_keywords = ['edit', 'write', 'code', 'develop', '编辑', '写', '开发', '代码']
        consumption_keywords = ['watch', 'video', 'browse', '视频', '看', '浏览']

        if any(kw in title_lower for kw in production_keywords):
            self.logger.debug(f"🎯 Mode determined: production (priority=2:title_keywords, title={window_title[:50]})")
            return ContentMode.PRODUCTION.value
        if any(kw in title_lower for kw in consumption_keywords):
            self.logger.debug(f"🎯 Mode determined: consumption (priority=2:title_keywords, title={window_title[:50]})")
            return ContentMode.CONSUMPTION.value

        # Priority 3: AppType default mode
        default_mode = self.app_classifier.get_default_mode(app_type)
        if default_mode != "unknown":
            self.logger.debug(f"🎯 Mode determined: {default_mode} (priority=3:app_type, type={app_type})")
            return default_mode

        # Priority 4: Unknown
        self.logger.debug(f"🎯 Mode determined: unknown (priority=4:fallback)")
        return ContentMode.UNKNOWN.value

    def _update_duration(self, app: str, mode: str, timestamp: int) -> int:
        """
        Update activity duration tracking

        Args:
            app: Current app name
            mode: Current content mode
            timestamp: Current timestamp

        Returns:
            Duration in current state (seconds)
        """
        # First time or state changed
        if (self.current_app != app or self.current_mode != mode):
            self.current_app = app
            self.current_mode = mode
            self.state_start_time = timestamp
            return 0

        # Calculate duration
        duration = timestamp - self.state_start_time
        return max(0, duration)

    def _detect_trend(self, mode: str, duration_sec: int) -> Optional[str]:
        """
        Detect behavior trend based on mode and duration

        Args:
            mode: Current content mode
            duration_sec: Duration in current state

        Returns:
            Behavior trend string or None
        """
        previous_mode = self.current_mode if self.last_snapshot else None

        # Focus steady: sustained production ≥20min
        if mode == ContentMode.PRODUCTION.value and duration_sec >= self.focus_steady_threshold:
            self.logger.debug(f"🔍 Trend detected: focus_steady (mode={mode}, duration={duration_sec}s)")
            return BehaviorTrend.FOCUS_STEADY.value

        # Moyu start: in consumption mode for ≥3min (context: was working)
        if mode == ContentMode.CONSUMPTION.value and duration_sec >= self.moyu_start_threshold:
            # Check if previously was in production mode
            if self.last_snapshot and self.current_mode != mode:
                self.logger.debug(f"🔍 Trend detected: moyu_start (mode={mode}, duration={duration_sec}s, prev_mode={previous_mode})")
                return BehaviorTrend.MOYU_START.value

        # Moyu steady: sustained consumption ≥15min
        if mode == ContentMode.CONSUMPTION.value and duration_sec >= self.moyu_steady_threshold:
            self.logger.debug(f"🔍 Trend detected: moyu_steady (mode={mode}, duration={duration_sec}s)")
            return BehaviorTrend.MOYU_STEADY.value

        # Mode switch (recent switch)
        if self.last_snapshot and duration_sec < 60:  # Within 1 minute of switch
            if mode != self.current_mode:
                self.logger.debug(f"🔍 Trend detected: mode_switch (transition: {previous_mode} → {mode})")
                return BehaviorTrend.MODE_SWITCH.value

        # Task switch
        if self.last_snapshot and duration_sec < 30:  # Within 30 seconds of switch
            if self.current_app != self.last_snapshot.app:
                self.logger.debug(f"🔍 Trend detected: task_switch (app: {self.last_snapshot.app} → {self.current_app})")
                return BehaviorTrend.TASK_SWITCH.value

        return BehaviorTrend.NONE.value

    def get_current_state(self) -> Dict:
        """
        Get current behavior state

        Returns:
            Dictionary with current state info
        """
        return {
            'current_app': self.current_app,
            'current_mode': self.current_mode,
            'state_start_time': self.state_start_time,
            'duration_sec': int(time.time()) - self.state_start_time if self.state_start_time else 0
        }

    def reset_state(self):
        """Reset behavior tracking state"""
        self.current_app = None
        self.current_mode = None
        self.state_start_time = 0
        self.last_snapshot = None
        self.logger.info("Behavior state reset")
