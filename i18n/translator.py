"""
Multi-language translation engine for GaiYa
Supports nested key access (e.g., "menu.file.open")
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Translator:
    """Core translation engine"""

    def __init__(self, locale: str = "zh_CN"):
        self.locale = locale
        self.translations: Dict[str, Dict] = {}
        self.fallback_locale = "zh_CN"
        self.load_translations()

    def load_translations(self):
        """Load all translation files from i18n directory"""
        import sys

        # Support for PyInstaller packaging
        if getattr(sys, 'frozen', False):
            # Running as packaged exe - use _MEIPASS
            i18n_dir = Path(sys._MEIPASS) / 'i18n'
        else:
            # Running in development - use __file__
            i18n_dir = Path(__file__).parent

        logger.info(f"Loading translations from: {i18n_dir}")

        for locale_file in i18n_dir.glob("*.json"):
            locale_name = locale_file.stem
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations[locale_name] = json.load(f)
                logger.debug(f"Loaded translations for {locale_name}")
            except Exception as e:
                logger.error(f"Failed to load {locale_file}: {e}")

        logger.info(f"Loaded {len(self.translations)} translation files")

    def tr(self, key: str, fallback: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the current locale

        Args:
            key: Translation key (supports dot notation, e.g., "menu.file.open")
            fallback: Default value if translation not found
            **kwargs: Format parameters (e.g., {name}, {count})

        Returns:
            Translated text
        """
        # Get current locale translations
        trans_dict = self.translations.get(self.locale, {})

        # Try literal key first (for flat keys like "appearance.basic_settings")
        if key in trans_dict:
            trans = trans_dict[key]
        else:
            # Support nested key access
            trans = trans_dict
            keys = key.split('.')
            for k in keys:
                if isinstance(trans, dict):
                    trans = trans.get(k)
                else:
                    trans = None
                    break

        # Fallback to default locale if not found
        if trans is None and self.locale != self.fallback_locale:
            trans = self._get_fallback_translation(key)

        # Still not found, use fallback or return key itself
        if trans is None:
            trans = fallback or key

        # Format parameter replacement
        if kwargs and isinstance(trans, str):
            try:
                trans = trans.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format parameter for {key}: {e}")

        return trans

    def _get_fallback_translation(self, key: str) -> Optional[str]:
        """Get translation from fallback locale"""
        trans_dict = self.translations.get(self.fallback_locale, {})

        # Try literal key first (for flat keys)
        if key in trans_dict:
            return trans_dict[key]

        # Try nested key access
        trans = trans_dict
        keys = key.split('.')
        for k in keys:
            if isinstance(trans, dict):
                trans = trans.get(k)
            else:
                return None
        return trans

    def set_language(self, locale: str) -> bool:
        """
        Switch language

        Args:
            locale: Locale code (e.g., "zh_CN", "en_US")

        Returns:
            True if successful, False if locale not available
        """
        if locale in self.translations:
            self.locale = locale
            logger.info(f"Language switched to {locale}")
            return True

        logger.warning(f"Locale {locale} not available")
        return False

    def get_language(self) -> str:
        """Get current language"""
        return self.locale

    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return list(self.translations.keys())

    def reload(self):
        """Reload all translation files (for development)"""
        self.translations.clear()
        self.load_translations()
        logger.info("Translation files reloaded")


# Global singleton instance
_translator = Translator()


def tr(key: str, fallback: Optional[str] = None, **kwargs) -> str:
    """
    Global translation function

    Usage:
        from i18n import tr
        text = tr("menu.config")
        text = tr("message.welcome", name="User")
    """
    return _translator.tr(key, fallback, **kwargs)


def set_language(locale: str) -> bool:
    """Global language switch"""
    return _translator.set_language(locale)


def get_language() -> str:
    """Get current language"""
    return _translator.get_language()


def get_available_languages() -> list:
    """Get list of available languages"""
    return _translator.get_available_languages()


def reload_translations():
    """Reload translation files (for development)"""
    _translator.reload()
