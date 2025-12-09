"""
App Classifier - Classify applications by type

Maps process names to application types (browser, ide, office, etc.)

Author: GaiYa Team
Date: 2025-12-08
"""

import json
import os
import logging
from typing import Dict, List, Optional


class AppClassifier:
    """
    App Classifier - Classify applications by process name

    Supported app types:
    - browser: Chrome, Edge, Firefox, etc.
    - ide: VSCode, Cursor, PyCharm, etc.
    - office: Word, Excel, PowerPoint, etc.
    - im: WeChat, QQ, Slack, etc.
    - video: Bilibili, VLC, PotPlayer, etc.
    - player: CloudMusic, QQMusic, Spotify, etc.
    - game: Steam, League of Legends, etc.
    - tool: Everything, Snipaste, etc.
    - system: Explorer, Task Manager, etc.
    - other: Unknown apps
    """

    def __init__(self, rules_path: str = None, logger: Optional[logging.Logger] = None):
        """
        Initialize App Classifier

        Args:
            rules_path: Path to app_rules.json (default: gaiya/data/app_rules.json)
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Default rules path
        if rules_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            rules_path = os.path.join(data_dir, 'app_rules.json')

        self.rules_path = rules_path
        self.rules: Dict[str, List[str]] = {}
        self.app_to_type_map: Dict[str, str] = {}

        self._load_rules()

    def _load_rules(self):
        """Load app classification rules from JSON file"""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Remove metadata fields
            self.rules = {k: v for k, v in data.items() if isinstance(v, list)}

            # Build reverse mapping: app_name -> app_type
            self.app_to_type_map = {}
            for app_type, app_list in self.rules.items():
                for app_name in app_list:
                    # Normalize to lowercase for case-insensitive matching
                    self.app_to_type_map[app_name.lower()] = app_type

            self.logger.info(f"Loaded {len(self.app_to_type_map)} app rules from {self.rules_path}")

        except FileNotFoundError:
            self.logger.error(f"App rules file not found: {self.rules_path}")
            self.rules = {}
            self.app_to_type_map = {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse app rules JSON: {e}")
            self.rules = {}
            self.app_to_type_map = {}
        except Exception as e:
            self.logger.error(f"Failed to load app rules: {e}")
            self.rules = {}
            self.app_to_type_map = {}

    def classify(self, app_name: str) -> str:
        """
        Classify application by process name

        Args:
            app_name: Process name (e.g., "chrome.exe", "Code.exe")

        Returns:
            App type string (browser/ide/office/im/video/player/game/tool/system/other)
        """
        if not app_name:
            return "other"

        # Normalize to lowercase
        app_lower = app_name.lower()

        # Exact match
        if app_lower in self.app_to_type_map:
            return self.app_to_type_map[app_lower]

        # Partial match (e.g., "chrome" in "chrome.exe")
        for known_app, app_type in self.app_to_type_map.items():
            # Remove .exe for comparison
            known_base = known_app.replace('.exe', '')
            app_base = app_lower.replace('.exe', '')

            if known_base in app_base or app_base in known_base:
                return app_type

        # Unknown app
        return "other"

    def get_default_mode(self, app_type: str) -> str:
        """
        Get default content mode for app type

        Args:
            app_type: App type (browser/ide/office/...)

        Returns:
            Content mode (production/consumption/neutral/unknown)
        """
        production_types = ['ide', 'office']
        consumption_types = ['video', 'player', 'game']
        neutral_types = ['im', 'tool', 'system']

        if app_type in production_types:
            return "production"
        elif app_type in consumption_types:
            return "consumption"
        elif app_type in neutral_types:
            return "neutral"
        else:
            return "unknown"

    def add_app(self, app_name: str, app_type: str):
        """
        Add a new app to classification rules (runtime only, not persisted)

        Args:
            app_name: Process name
            app_type: App type
        """
        app_lower = app_name.lower()
        self.app_to_type_map[app_lower] = app_type
        self.logger.debug(f"Added app: {app_name} -> {app_type}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get classification statistics

        Returns:
            Dictionary with app type counts
        """
        stats = {}
        for app_type in self.rules.keys():
            count = len(self.rules[app_type])
            stats[app_type] = count

        return stats
