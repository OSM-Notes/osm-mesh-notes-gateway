"""Tests for internationalization (i18n) functionality."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from gateway import i18n


@pytest.fixture
def temp_locale_dir(tmp_path):
    """Create a temporary locale directory structure."""
    locale_dir = tmp_path / "locale"
    es_dir = locale_dir / "es" / "LC_MESSAGES"
    en_dir = locale_dir / "en" / "LC_MESSAGES"
    es_dir.mkdir(parents=True)
    en_dir.mkdir(parents=True)
    
    # Create minimal .po files (compiled to .mo would be better, but gettext handles .po in fallback)
    # For testing, we'll mock the translation loading
    return locale_dir


def test_default_locale():
    """Test that default locale is Spanish."""
    assert i18n.DEFAULT_LOCALE == "es"


def test_get_current_locale():
    """Test getting current locale."""
    locale = i18n.get_current_locale()
    assert isinstance(locale, str)
    assert len(locale) > 0


def test_set_locale():
    """Test setting locale."""
    original_locale = i18n.get_current_locale()
    
    # Set to English
    i18n.set_locale("en")
    assert i18n.get_current_locale() == "en"
    
    # Restore original
    i18n.set_locale(original_locale)
    assert i18n.get_current_locale() == original_locale


def test_translate_with_default_locale():
    """Test translation function with default locale."""
    # Should return the message ID if no translation exists (fallback)
    result = i18n._("Test message")
    assert isinstance(result, str)
    assert len(result) > 0


def test_translate_with_explicit_locale():
    """Test translation function with explicit locale."""
    # Test with Spanish
    result_es = i18n._("Test message", locale="es")
    assert isinstance(result_es, str)
    
    # Test with English
    result_en = i18n._("Test message", locale="en")
    assert isinstance(result_en, str)
    
    # Both should return strings
    assert len(result_es) > 0
    assert len(result_en) > 0


def test_translate_with_none_locale():
    """Test translation function with None locale (should use default)."""
    result = i18n._("Test message", locale=None)
    assert isinstance(result, str)
    assert len(result) > 0


def test_gettext_n_singular():
    """Test plural translation with singular form."""
    result = i18n.gettext_n("One item", "Many items", 1, locale="es")
    assert isinstance(result, str)
    # Should return singular form
    assert "One" in result or result == "One item"


def test_gettext_n_plural():
    """Test plural translation with plural form."""
    result = i18n.gettext_n("One item", "Many items", 5, locale="es")
    assert isinstance(result, str)
    # Should return plural form
    assert "Many" in result or result == "Many items"


def test_gettext_n_with_none_locale():
    """Test plural translation with None locale."""
    result = i18n.gettext_n("One item", "Many items", 1, locale=None)
    assert isinstance(result, str)
    assert len(result) > 0


@patch('gateway.i18n.gettext.translation')
def test_get_translation_caching(mock_translation):
    """Test that translations are cached."""
    # Clear cache
    i18n._translation_cache.clear()
    
    # Mock translation object
    mock_trans = MagicMock()
    mock_translation.return_value = mock_trans
    
    # First call should create translation
    trans1 = i18n._get_translation("es")
    assert mock_translation.call_count == 1
    
    # Second call should use cache
    trans2 = i18n._get_translation("es")
    assert mock_translation.call_count == 1
    assert trans1 is trans2
    
    # Clear cache
    i18n._translation_cache.clear()


@patch('gateway.i18n.gettext.translation')
def test_get_translation_different_locales(mock_translation):
    """Test that different locales create different translations."""
    # Clear cache
    i18n._translation_cache.clear()
    
    # Mock translation objects
    mock_trans_es = MagicMock()
    mock_trans_en = MagicMock()
    mock_translation.side_effect = [mock_trans_es, mock_trans_en]
    
    # Get translations for different locales
    trans_es = i18n._get_translation("es")
    trans_en = i18n._get_translation("en")
    
    # Should have called translation twice
    assert mock_translation.call_count == 2
    assert trans_es is mock_trans_es
    assert trans_en is mock_trans_en
    
    # Clear cache
    i18n._translation_cache.clear()


@patch('gateway.i18n.gettext.translation')
def test_get_translation_fallback_on_error(mock_translation):
    """Test that translation falls back to NullTranslations on error."""
    # Clear cache
    i18n._translation_cache.clear()
    
    # Mock translation to raise exception
    mock_translation.side_effect = Exception("Translation error")
    
    # Should return NullTranslations
    import gettext
    trans = i18n._get_translation("fr")
    assert isinstance(trans, gettext.NullTranslations)
    
    # Clear cache
    i18n._translation_cache.clear()


def test_translate_known_spanish_message():
    """Test translation with a known Spanish message."""
    # Use a message that should exist in Spanish translations
    result = i18n._("📊 Notas creadas:\n", locale="es")
    assert isinstance(result, str)
    assert len(result) > 0


def test_translate_known_english_message():
    """Test translation with a known English message."""
    # Use a message that should exist in English translations
    result = i18n._("📊 Notas creadas:\n", locale="en")
    assert isinstance(result, str)
    assert len(result) > 0


def test_translate_with_formatting():
    """Test translation with formatting placeholders."""
    # Test that formatting works with translated strings
    result = i18n._("Hoy: {today}\n", locale="es")
    formatted = result.format(today=5)
    assert isinstance(formatted, str)
    assert "5" in formatted or "today" in formatted.lower()


def test_locale_dir_exists():
    """Test that locale directory path is set."""
    assert hasattr(i18n, 'LOCALE_DIR')
    assert isinstance(i18n.LOCALE_DIR, Path)


def test_domain_constant():
    """Test that domain constant is set correctly."""
    assert i18n.DOMAIN == "lora-osmnotes"


def test_translation_cache_structure():
    """Test that translation cache is a dictionary."""
    assert isinstance(i18n._translation_cache, dict)


@patch.dict(os.environ, {'LANGUAGE': 'en'})
def test_global_locale_from_environment():
    """Test that global locale can be set from environment."""
    # Reload module to pick up environment variable
    import importlib
    importlib.reload(i18n)
    
    # Should use environment variable
    locale = i18n.get_current_locale()
    assert locale == "en" or locale.startswith("en")
    
    # Restore default
    importlib.reload(i18n)
