"""
System locale detection module for GaiYa
"""
import locale
import platform
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def get_system_locale() -> str:
    """
    Detect system language and return locale code

    Returns:
        Locale code: "zh_CN" or "en_US"
    """
    try:
        # Method 1: locale.getdefaultlocale()
        system_locale, _ = locale.getdefaultlocale()

        if system_locale:
            normalized = _normalize_locale(system_locale)
            if normalized:
                logger.debug(f"Detected system locale: {normalized}")
                return normalized

        # Method 2: Windows-specific detection
        if platform.system() == 'Windows':
            try:
                import ctypes
                windll = ctypes.windll.kernel32
                lang_id = windll.GetUserDefaultUILanguage()

                # Language ID mapping
                # 0x0804 = Simplified Chinese
                # 0x0404 = Traditional Chinese
                # 0x0409 = English (US)
                # 0x0809 = English (UK)
                if lang_id in (0x0804, 0x0404):
                    logger.debug(f"Windows lang_id {hex(lang_id)} -> zh_CN")
                    return "zh_CN"
                elif lang_id in (0x0409, 0x0809):
                    logger.debug(f"Windows lang_id {hex(lang_id)} -> en_US")
                    return "en_US"
            except Exception as e:
                logger.debug(f"Windows language detection failed: {e}")

        # Method 3: Environment variables
        import os
        for var in ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES']:
            env_locale = os.environ.get(var, '')
            if env_locale:
                normalized = _normalize_locale(env_locale)
                if normalized:
                    logger.debug(f"Detected from {var}: {normalized}")
                    return normalized

    except Exception as e:
        logger.error(f"Locale detection failed: {e}")

    # Default to Chinese
    logger.debug("Falling back to default locale: zh_CN")
    return "zh_CN"


def _normalize_locale(locale_str: str) -> str:
    """
    Normalize locale string to supported format

    Args:
        locale_str: Raw locale string (e.g., "zh_CN.UTF-8", "en-US")

    Returns:
        Normalized locale code or empty string if not recognized
    """
    if not locale_str:
        return ""

    # Convert to lowercase for comparison
    lower = locale_str.lower()

    # Chinese variants
    if any(x in lower for x in ['zh_cn', 'zh-cn', 'chinese', 'zh_hans']):
        return "zh_CN"
    elif any(x in lower for x in ['zh_tw', 'zh-tw', 'zh_hk', 'zh-hk', 'zh_hant']):
        return "zh_CN"  # Map Traditional Chinese to Simplified for now
    elif lower.startswith('zh'):
        return "zh_CN"

    # English variants
    elif any(x in lower for x in ['en_us', 'en-us', 'en_gb', 'en-gb', 'english']):
        return "en_US"
    elif lower.startswith('en'):
        return "en_US"

    return ""


def get_locale_name(locale_code: str) -> str:
    """
    Get localized display name for a locale

    Args:
        locale_code: e.g., "zh_CN"

    Returns:
        Display name, e.g., "简体中文"
    """
    names = {
        "zh_CN": "简体中文",
        "en_US": "English"
    }
    return names.get(locale_code, locale_code)


def get_locale_native_name(locale_code: str) -> str:
    """
    Get native name for a locale (always in that language)

    Args:
        locale_code: e.g., "zh_CN"

    Returns:
        Native name, e.g., "简体中文"
    """
    names = {
        "zh_CN": "简体中文",
        "en_US": "English"
    }
    return names.get(locale_code, locale_code)


def get_all_locales() -> list:
    """
    Get list of all supported locales with metadata

    Returns:
        List of dicts with locale info
    """
    return [
        {
            "code": "zh_CN",
            "name": "简体中文",
            "native_name": "简体中文",
            "flag": "🇨🇳"
        },
        {
            "code": "en_US",
            "name": "English",
            "native_name": "English",
            "flag": "🇺🇸"
        }
    ]
