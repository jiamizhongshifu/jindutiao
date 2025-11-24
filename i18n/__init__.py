"""
GaiYa Internationalization (i18n) Module

Usage:
    from i18n import tr, set_language, get_language

    # Translate a key
    text = tr("menu.config")

    # Translate with parameters
    text = tr("message.welcome", name="User")

    # Switch language
    set_language("en_US")

    # Get current language
    current = get_language()

    # Auto-detect system language
    from i18n import get_system_locale
    locale = get_system_locale()
    set_language(locale)
"""

from i18n.translator import (
    tr,
    set_language,
    get_language,
    get_available_languages,
    reload_translations
)

from i18n.locale_detector import (
    get_system_locale,
    get_locale_name,
    get_locale_native_name,
    get_all_locales
)

__all__ = [
    # Core translation functions
    'tr',
    'set_language',
    'get_language',
    'get_available_languages',
    'reload_translations',

    # Locale detection
    'get_system_locale',
    'get_locale_name',
    'get_locale_native_name',
    'get_all_locales'
]

__version__ = '1.0.0'
