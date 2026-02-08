"""GPS position cache with persistence."""

import time
import logging
from typing import Optional, Tuple, Dict
from dataclasses import dataclass

from .database import Database
from .config import DB_PATH

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """GPS position with metadata."""
    lat: float
    lon: float
    received_at: float
    seen_count: int = 1


class PositionCache:
    """
    GPS position cache with SQLite persistence.
    
    Stores the latest known position for each Meshtastic node, with both
    in-memory cache for fast access and SQLite persistence for survival
    across restarts and power loss.
    
    Attributes:
        positions: Dictionary mapping node_id to Position objects (in-memory cache)
        db: Database instance for persistence
        
    Note:
        Positions are automatically persisted to SQLite on update.
        Cache is loaded from database on initialization.
        Positions older than 24 hours are automatically cleaned up.
    """

    def __init__(self, db: Optional[Database] = None):
        self.positions: Dict[str, Position] = {}
        self.db = db or Database(db_path=DB_PATH)
        
        # Load positions from database on startup
        self._load_from_db()
        
        # Cleanup old positions (older than 24 hours)
        self.db.cleanup_old_positions(max_age_seconds=86400)

    def _load_from_db(self):
        """Load positions from database into memory cache."""
        try:
            db_positions = self.db.load_all_positions()
            for node_id, pos_data in db_positions.items():
                self.positions[node_id] = Position(
                    lat=pos_data["lat"],
                    lon=pos_data["lon"],
                    received_at=pos_data["received_at"],
                    seen_count=pos_data.get("seen_count", 1),
                )
            if db_positions:
                logger.info(f"Loaded {len(db_positions)} positions from database")
        except Exception as e:
            logger.warning(f"Failed to load positions from database: {e}")

    def update(self, node_id: str, lat: float, lon: float):
        """Update position for a node (both memory and database)."""
        now = time.time()
        
        # Update in-memory cache
        if node_id in self.positions:
            self.positions[node_id].lat = lat
            self.positions[node_id].lon = lon
            self.positions[node_id].received_at = now
            self.positions[node_id].seen_count += 1
            seen_count = self.positions[node_id].seen_count
        else:
            self.positions[node_id] = Position(
                lat=lat,
                lon=lon,
                received_at=now,
                seen_count=1,
            )
            seen_count = 1
        
        # Persist to database
        try:
            self.db.save_position(node_id, lat, lon, now, seen_count)
        except Exception as e:
            logger.warning(f"Failed to persist position for {node_id}: {e}")
        
        logger.debug(f"Updated position for {node_id}: ({lat}, {lon})")

    def get(self, node_id: str) -> Optional[Position]:
        """Get latest position for a node."""
        # First check in-memory cache
        if node_id in self.positions:
            return self.positions[node_id]
        
        # Fallback to database if not in memory
        try:
            db_pos = self.db.get_position(node_id)
            if db_pos:
                pos = Position(
                    lat=db_pos["lat"],
                    lon=db_pos["lon"],
                    received_at=db_pos["received_at"],
                    seen_count=db_pos.get("seen_count", 1),
                )
                # Add to memory cache for future access
                self.positions[node_id] = pos
                return pos
        except Exception as e:
            logger.debug(f"Failed to get position from database for {node_id}: {e}")
        
        return None

    def get_age(self, node_id: str) -> Optional[float]:
        """Get age of latest position in seconds."""
        pos = self.get(node_id)
        if pos:
            return time.time() - pos.received_at
        return None

    def clear(self):
        """Clear all positions (both memory and database)."""
        self.positions.clear()
        # Note: We don't clear database positions as they may be useful after restart
