"""Tests for coordinate validation."""

import pytest
from gateway.commands import CommandProcessor
from gateway.database import Database
from gateway.position_cache import PositionCache


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


def test_validate_coordinates_valid(processor):
    """Test validation of valid coordinates."""
    # Valid coordinates
    is_valid, msg = processor._validate_coordinates(4.6097, -74.0817)
    assert is_valid is True
    assert msg is None
    
    # (0,0) is invalid
    is_valid, msg = processor._validate_coordinates(0.0, 0.0)
    assert is_valid is False
    assert msg is not None
    
    is_valid, msg = processor._validate_coordinates(90.0, 180.0)
    assert is_valid is True
    assert msg is None
    
    is_valid, msg = processor._validate_coordinates(-90.0, -180.0)
    assert is_valid is True
    assert msg is None


def test_validate_coordinates_invalid(processor):
    """Test validation of invalid coordinates."""
    # Invalid latitude
    assert processor._validate_coordinates(91.0, 0.0)[0] == False
    assert processor._validate_coordinates(-91.0, 0.0)[0] == False
    
    # Invalid longitude
    assert processor._validate_coordinates(0.0, 181.0)[0] == False
    assert processor._validate_coordinates(0.0, -181.0)[0] == False
    
    # (0,0) is invalid (default/error value)
    assert processor._validate_coordinates(0.0, 0.0)[0] == False


def test_osmnote_rejects_invalid_coordinates(processor, position_cache):
    """Test that osmnote rejects invalid coordinates."""
    node_id = "test_node"
    
    # Test with (0,0) coordinates
    position_cache.update(node_id, 0.0, 0.0)
    cmd_type, response = processor.process_message(node_id, "#osmnote test")
    assert cmd_type == "osmnote_reject"
    assert "coordenadas GPS" in response or "inválidas" in response
    
    # Test with invalid latitude
    position_cache.update(node_id, 91.0, 0.0)
    cmd_type, response = processor.process_message(node_id, "#osmnote test")
    assert cmd_type == "osmnote_reject"
    
    # Test with invalid longitude
    position_cache.update(node_id, 0.0, 181.0)
    cmd_type, response = processor.process_message(node_id, "#osmnote test")
    assert cmd_type == "osmnote_reject"


def test_osmnote_accepts_valid_coordinates(processor, position_cache):
    """Test that osmnote accepts valid coordinates."""
    import time
    node_id = "test_node"
    
    # Valid coordinates for Bogotá
    position_cache.update(node_id, 4.6097, -74.0817)
    
    cmd_type, response = processor.process_message(node_id, "#osmnote test message")
    assert cmd_type == "osmnote_queued"
    assert response is not None  # Should return queue_id
