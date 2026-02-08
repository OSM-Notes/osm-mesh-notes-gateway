"""Tests for position cache."""

import pytest
import time
from pathlib import Path
from gateway.position_cache import PositionCache
from gateway.database import Database


@pytest.fixture
def db(tmp_path):
    """Create temporary database."""
    db_path = tmp_path / "test.db"
    return Database(db_path=db_path)


def test_update_and_get(db):
    """Test position update and retrieval."""
    cache = PositionCache(db=db)
    
    cache.update("node1", 1.0, 2.0)
    pos = cache.get("node1")
    
    assert pos is not None
    assert pos.lat == 1.0
    assert pos.lon == 2.0
    assert pos.seen_count == 1


def test_get_age(db):
    """Test position age calculation."""
    cache = PositionCache(db=db)
    
    cache.update("node1", 1.0, 2.0)
    age = cache.get_age("node1")
    
    assert age is not None
    assert age >= 0
    assert age < 1.0  # Should be very recent


def test_seen_count(db):
    """Test seen count increment."""
    cache = PositionCache(db=db)
    
    cache.update("node1", 1.0, 2.0)
    assert cache.get("node1").seen_count == 1
    
    cache.update("node1", 1.1, 2.1)
    assert cache.get("node1").seen_count == 2


def test_clear(db):
    """Test cache clearing (memory only, database persists)."""
    cache = PositionCache(db=db)
    
    cache.update("node1", 1.0, 2.0)
    assert cache.get("node1") is not None
    
    cache.clear()
    # Memory cache is cleared
    assert "node1" not in cache.positions
    # But database still has it, so get() will reload it
    pos = cache.get("node1")
    assert pos is not None  # Reloaded from database


def test_persistence_across_instances(tmp_path):
    """Test that positions persist across cache instances."""
    db_path = tmp_path / "test.db"
    db1 = Database(db_path=db_path)
    
    # Create cache and update position
    cache1 = PositionCache(db=db1)
    cache1.update("node1", 1.0, 2.0)
    
    # Create new cache instance (simulating restart)
    db2 = Database(db_path=db_path)
    cache2 = PositionCache(db=db2)
    
    # Position should be loaded from database
    pos = cache2.get("node1")
    assert pos is not None
    assert pos.lat == 1.0
    assert pos.lon == 2.0


def test_load_from_database(db):
    """Test loading positions from database on startup."""
    # Manually insert position in database
    db.save_position("node1", 1.0, 2.0, time.time(), 5)
    
    # Create cache - should load from database
    cache = PositionCache(db=db)
    
    pos = cache.get("node1")
    assert pos is not None
    assert pos.lat == 1.0
    assert pos.lon == 2.0
    assert pos.seen_count == 5
