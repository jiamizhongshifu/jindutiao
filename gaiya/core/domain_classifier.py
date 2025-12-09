"""
Domain Classifier - Classify web domains by category and content mode

Maps domains to categories (code/video/social/doc/shopping/etc.) and modes (production/consumption/neutral)

Author: GaiYa Team
Date: 2025-12-08
"""

import json
import os
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse


class DomainClassifier:
    """
    Domain Classifier - Classify web domains

    Categories:
    - code: GitHub, GitLab, Stack Overflow, etc.
    - doc: Notion, Google Docs, Confluence, etc.
    - video: Bilibili, YouTube, iQiyi, etc.
    - social: Weibo, Twitter, Xiaohongshu, etc.
    - shopping: JD, Taobao, Amazon, etc.
    - search: Google, Baidu, Bing
    - ai: Claude, ChatGPT, Poe
    - email: Gmail, Outlook, 163 Mail
    - other: Unknown domains

    Modes:
    - production: Creating content (coding, writing docs)
    - consumption: Consuming content (watching videos, browsing social media)
    - neutral: Neither (email, search)
    - unknown: Cannot determine
    """

    def __init__(self, rules_path: str = None, logger: Optional[logging.Logger] = None):
        """
        Initialize Domain Classifier

        Args:
            rules_path: Path to domain_rules.json
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Default rules path
        if rules_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            rules_path = os.path.join(data_dir, 'domain_rules.json')

        self.rules_path = rules_path
        self.domains: Dict[str, Dict] = {}
        self.wildcards: Dict[str, Dict] = {}

        self._load_rules()

    def _load_rules(self):
        """Load domain classification rules from JSON file"""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.domains = data.get('domains', {})
            self.wildcards = data.get('wildcards', {})

            total_domains = len(self.domains) + len(self.wildcards)
            self.logger.info(f"Loaded {total_domains} domain rules from {self.rules_path}")

        except FileNotFoundError:
            self.logger.error(f"Domain rules file not found: {self.rules_path}")
            self.domains = {}
            self.wildcards = {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse domain rules JSON: {e}")
            self.domains = {}
            self.wildcards = {}
        except Exception as e:
            self.logger.error(f"Failed to load domain rules: {e}")
            self.domains = {}
            self.wildcards = {}

    def extract_domain(self, url: str) -> Optional[str]:
        """
        Extract domain from URL

        Args:
            url: Full URL (e.g., "https://github.com/user/repo")

        Returns:
            Domain string (e.g., "github.com") or None
        """
        if not url:
            return None

        try:
            # Add scheme if missing
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'

            parsed = urlparse(url)
            domain = parsed.netloc

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain if domain else None

        except Exception as e:
            self.logger.debug(f"Failed to extract domain from URL '{url}': {e}")
            return None

    def classify(self, url: str) -> Tuple[str, str]:
        """
        Classify domain by URL

        Args:
            url: Full URL or domain

        Returns:
            Tuple of (category, mode)
            - category: code/video/social/doc/shopping/search/ai/email/other
            - mode: production/consumption/neutral/unknown
        """
        domain = self.extract_domain(url)
        if not domain:
            return ("other", "unknown")

        # Exact match
        if domain in self.domains:
            rule = self.domains[domain]
            return (rule['category'], rule['mode'])

        # Wildcard match
        for pattern, rule in self.wildcards.items():
            # Simple wildcard matching (*.example.com)
            if pattern.startswith('*.'):
                suffix = pattern[2:]  # Remove "*."
                if domain.endswith(suffix):
                    return (rule['category'], rule['mode'])

        # Unknown domain
        return ("other", "unknown")

    def get_category(self, url: str) -> str:
        """Get domain category"""
        category, _ = self.classify(url)
        return category

    def get_mode(self, url: str) -> str:
        """Get content mode"""
        _, mode = self.classify(url)
        return mode

    def add_domain(self, domain: str, category: str, mode: str, description: str = ""):
        """
        Add a new domain rule (runtime only, not persisted)

        Args:
            domain: Domain name
            category: Category
            mode: Content mode
            description: Description
        """
        self.domains[domain] = {
            'category': category,
            'mode': mode,
            'description': description
        }
        self.logger.debug(f"Added domain: {domain} -> {category}/{mode}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get classification statistics

        Returns:
            Dictionary with category counts
        """
        stats = {}
        for rule in self.domains.values():
            category = rule['category']
            stats[category] = stats.get(category, 0) + 1

        return stats
