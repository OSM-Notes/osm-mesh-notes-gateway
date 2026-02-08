"""Tests for message length validation."""

import pytest
from gateway.commands import CommandProcessor
from gateway.database import Database
from gateway.position_cache import PositionCache
from gateway.config import MESHTASTIC_MAX_MESSAGE_LENGTH


@pytest.fixture
def db(tmp_path):
    """Create temporary database."""
    db_path = tmp_path / "test.db"
    return Database(db_path=db_path)


@pytest.fixture
def position_cache(db):
    """Create position cache."""
    return PositionCache(db=db)


@pytest.fixture
def processor(db, position_cache):
    """Create command processor."""
    return CommandProcessor(db, position_cache)


def test_message_length_within_limit(processor, position_cache):
    """Test that messages within limit are accepted."""
    node_id = "test_node"
    position_cache.update(node_id, 4.6097, -74.0817)
    
    # Message at limit
    short_message = "a" * MESHTASTIC_MAX_MESSAGE_LENGTH
    cmd_type, response = processor.process_message(node_id, f"#osmnote {short_message}")
    assert cmd_type == "osmnote_queued"
    
    # Message under limit
    shorter_message = "a" * (MESHTASTIC_MAX_MESSAGE_LENGTH - 10)
    cmd_type, response = processor.process_message(node_id, f"#osmnote {shorter_message}")
    assert cmd_type == "osmnote_queued"


def test_message_length_over_limit(processor, position_cache):
    """Test that messages over limit are rejected."""
    node_id = "test_node"
    position_cache.update(node_id, 4.6097, -74.0817)
    
    # Message over limit
    long_message = "a" * (MESHTASTIC_MAX_MESSAGE_LENGTH + 1)
    cmd_type, response = processor.process_message(node_id, f"#osmnote {long_message}")
    assert cmd_type == "osmnote_reject"
    assert "demasiado largo" in response or "máximo" in response
    assert str(MESHTASTIC_MAX_MESSAGE_LENGTH) in response


def test_message_length_exact_limit(processor, position_cache):
    """Test message at exact limit."""
    node_id = "test_node"
    position_cache.update(node_id, 4.6097, -74.0817)
    
    # Message exactly at limit (after removing #osmnote prefix)
    message_text = "a" * MESHTASTIC_MAX_MESSAGE_LENGTH
    cmd_type, response = processor.process_message(node_id, f"#osmnote {message_text}")
    # Should be accepted (limit is on the text after #osmnote)
    assert cmd_type == "osmnote_queued"
