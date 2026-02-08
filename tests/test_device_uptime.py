"""Tests for device uptime detection and handling."""

import pytest
import time
from gateway.commands import CommandProcessor
from gateway.database import Database
from gateway.position_cache import PositionCache
from gateway.config import DEVICE_UPTIME_RECENT, DEVICE_UPTIME_GPS_WAIT


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


def test_recent_device_start_no_position(processor):
    """Test that recent device start without position gives helpful message."""
    node_id = "test_node"
    
    # Device started recently (less than DEVICE_UPTIME_RECENT seconds ago)
    device_uptime = DEVICE_UPTIME_RECENT - 10  # 10 seconds ago
    
    cmd_type, response = processor.process_message(
        node_id,
        "#osmnote test message",
        device_uptime=device_uptime
    )
    
    assert cmd_type == "osmnote_reject"
    # Should mention device was recently started or GPS issue
    assert ("se prendió hace poco" in response or 
            "GPS" in response or 
            "no hay GPS" in response)
    # If it's the recent start message, should include wait time
    if "se prendió hace poco" in response:
        wait_time = int(DEVICE_UPTIME_GPS_WAIT - device_uptime)
        assert str(wait_time) in response


def test_recent_device_start_with_stale_position(processor, position_cache):
    """Test that recent device start with stale position gives helpful message."""
    node_id = "test_node"
    position_cache.update(node_id, 4.6097, -74.0817)
    
    # Make position stale
    position_cache.positions[node_id].received_at = time.time() - 150
    
    # Device started recently
    device_uptime = DEVICE_UPTIME_RECENT - 10
    
    cmd_type, response = processor.process_message(
        node_id,
        "#osmnote test message",
        device_uptime=device_uptime
    )
    
    assert cmd_type == "osmnote_reject"
    assert "se prendió hace poco" in response or "GPS" in response


def test_old_device_start_works_normal(processor, position_cache):
    """Test that old device start works normally."""
    node_id = "test_node"
    position_cache.update(node_id, 4.6097, -74.0817)
    
    # Device started a while ago (more than DEVICE_UPTIME_RECENT seconds)
    device_uptime = DEVICE_UPTIME_RECENT + 100
    
    cmd_type, response = processor.process_message(
        node_id,
        "#osmnote test message",
        device_uptime=device_uptime
    )
    
    # Should work normally (not reject due to uptime)
    assert cmd_type == "osmnote_queued"


def test_no_uptime_info_works_normal(processor, position_cache):
    """Test that missing uptime info works normally."""
    node_id = "test_node"
    position_cache.update(node_id, 4.6097, -74.0817)
    
    # No uptime info (None)
    cmd_type, response = processor.process_message(
        node_id,
        "#osmnote test message",
        device_uptime=None
    )
    
    # Should work normally
    assert cmd_type == "osmnote_queued"


def test_recent_device_with_fresh_position(processor, position_cache):
    """Test that recent device with fresh position works."""
    node_id = "test_node"
    position_cache.update(node_id, 4.6097, -74.0817)
    
    # Device started recently but position is fresh
    device_uptime = DEVICE_UPTIME_RECENT - 10
    
    cmd_type, response = processor.process_message(
        node_id,
        "#osmnote test message",
        device_uptime=device_uptime
    )
    
    # Should work if position is fresh
    assert cmd_type == "osmnote_queued"
