"""Internationalization (i18n) support using gettext."""

import os
import gettext
import logging
from pathlib import Path
from typing import Optional

from .config import DATA_DIR

logger = logging.getLogger(__name__)

# Default locale
DEFAULT_LOCALE = "es"

# Domain for gettext
DOMAIN = "lora-osmnotes"

# Locale directory (relative to this file)
LOCALE_DIR = Path(__file__).parent.parent.parent / "locale"

# Fallback to DATA_DIR if locale doesn't exist in project
if not LOCALE_DIR.exists():
    LOCALE_DIR = DATA_DIR / "locale"

# Also check if running from installed package location
if not LOCALE_DIR.exists():
    # Try common installation paths
    for possible_path in [
        Path("/home/angoca/LoRa-Meshtastic-OSM-notes-bot/locale"),
        Path("/opt/lora-osmnotes/locale"),
        DATA_DIR / "locale",
    ]:
        if possible_path.exists():
            LOCALE_DIR = possible_path
            break

# Get locale from environment variable (global default)
GLOBAL_LOCALE = os.getenv("LANGUAGE", DEFAULT_LOCALE).split(".")[0].split("_")[0]

# Cache for translations per locale
# Clear cache on import to ensure fresh translations are loaded
_translation_cache: dict[str, gettext.GNUTranslations] = {}


def _get_translation(locale: str) -> gettext.GNUTranslations:
    """Get or create translation for a locale."""
    if locale not in _translation_cache:
        try:
            logger.debug(f"Loading translation for locale: {locale} from {LOCALE_DIR}")
            translation = gettext.translation(
                DOMAIN,
                localedir=str(LOCALE_DIR),
                languages=[locale],
                fallback=True
            )
            _translation_cache[locale] = translation
            logger.info(f"Loaded translation for locale: {locale} from {LOCALE_DIR}")
        except Exception as e:
            logger.warning(f"Failed to load translation for locale {locale} from {LOCALE_DIR}: {e}")
            # Return NullTranslations as fallback
            _translation_cache[locale] = gettext.NullTranslations()
    return _translation_cache[locale]


def _(msgid: str, locale: Optional[str] = None) -> str:
    """
    Translate a message.
    
    Args:
        msgid: Message ID to translate
        locale: Optional locale override (if None, uses global default)
        
    Returns:
        Translated string
    """
    if locale is None:
        locale = GLOBAL_LOCALE
    translation = _get_translation(locale)
    result = translation.gettext(msgid)
    # Debug: log if translation didn't work (result == msgid and locale != 'es')
    if result == msgid and locale != "es" and locale is not None:
        logger.debug(f"Translation missing for locale {locale}: msgid='{msgid[:50]}...'")
    return result


def gettext_n(msgid: str, msgid_plural: str, n: int, locale: Optional[str] = None) -> str:
    """Get plural form of translated string."""
    if locale is None:
        locale = GLOBAL_LOCALE
    translation = _get_translation(locale)
    try:
        return translation.ngettext(msgid, msgid_plural, n)
    except Exception:
        return msgid if n == 1 else msgid_plural


def get_current_locale() -> str:
    """Get current global locale."""
    return GLOBAL_LOCALE


def set_locale(locale: str):
    """Set global locale (for testing or runtime changes)."""
    global GLOBAL_LOCALE
    GLOBAL_LOCALE = locale
    logger.info(f"Global locale changed to: {GLOBAL_LOCALE}")
