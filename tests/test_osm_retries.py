"""Tests for OSM API retry logic."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
import sys

# Mock requests if not available
try:
    import requests
except ImportError:
    sys.modules['requests'] = MagicMock()

from gateway.osm_worker import OSMWorker
from gateway.database import Database
from gateway.config import OSM_MAX_RETRIES, OSM_RETRY_DELAY_SECONDS


@pytest.fixture
def db(tmp_path):
    """Create temporary database."""
    db_path = tmp_path / "test.db"
    return Database(db_path=db_path)


@pytest.fixture
def worker(db):
    """Create OSM worker."""
    return OSMWorker(db)


def test_parse_osm_error_400(worker):
    """Test parsing of 400 error."""
    error_msg = worker._parse_osm_error(400, "Bad Request")
    assert "inválida" in error_msg or "incorrectos" in error_msg


def test_parse_osm_error_403(worker):
    """Test parsing of 403 error."""
    error_msg = worker._parse_osm_error(403, "Forbidden")
    assert "denegado" in error_msg or "rate limiting" in error_msg


def test_parse_osm_error_429(worker):
    """Test parsing of 429 error."""
    error_msg = worker._parse_osm_error(429, "Too Many Requests")
    assert "Demasiadas solicitudes" in error_msg or "rate limiting" in error_msg


def test_parse_osm_error_500(worker):
    """Test parsing of 500 error."""
    error_msg = worker._parse_osm_error(500, "Internal Server Error")
    assert "servidor" in error_msg or "Error del servidor" in error_msg


def test_parse_osm_error_503(worker):
    """Test parsing of 503 error."""
    error_msg = worker._parse_osm_error(503, "Service Unavailable")
    assert "no disponible" in error_msg or "temporalmente" in error_msg


def test_parse_osm_error_unknown(worker):
    """Test parsing of unknown error."""
    error_msg = worker._parse_osm_error(999, "Unknown Error")
    assert "Unknown Error" in error_msg or "Error desconocido" in error_msg


@patch('gateway.osm_worker.requests.post')
def test_process_pending_retries_on_failure(mock_post, worker, db, monkeypatch):
    """Test that process_pending retries failed notes."""
    import time
    
    # Mock sleep to not actually wait
    sleep_calls = []
    original_sleep = time.sleep
    def mock_sleep(seconds):
        sleep_calls.append(seconds)
    monkeypatch.setattr(time, "sleep", mock_sleep)
    
    # Create a pending note
    queue_id = db.create_note(
        node_id="test_node",
        lat=4.6097,
        lon=-74.0817,
        text_original="test",
        text_normalized="test"
    )
    
    # Mock API to fail first time, succeed second time
    mock_response_fail = Mock()
    mock_response_fail.status_code = 500
    mock_response_fail.text = "Internal Server Error"
    
    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {
        "properties": {"id": 12345}
    }
    
    # First call: fail
    mock_post.return_value = mock_response_fail
    
    # First attempt - should fail and increment retry count
    sent_count = worker.process_pending(limit=10)
    assert sent_count == 0
    assert queue_id in worker.retry_counts
    assert worker.retry_counts[queue_id] == 1
    
    # Second call: succeed
    mock_post.return_value = mock_response_success
    
    # Second attempt - should succeed
    sent_count = worker.process_pending(limit=10)
    assert sent_count == 1
    assert queue_id not in worker.retry_counts  # Should be removed after success


@patch('gateway.osm_worker.requests.post')
def test_process_pending_max_retries_exceeded(mock_post, worker, db):
    """Test that process_pending stops retrying after max retries."""
    # Create a pending note
    queue_id = db.create_note(
        node_id="test_node",
        lat=4.6097,
        lon=-74.0817,
        text_original="test",
        text_normalized="test"
    )
    
    # Mock API to always fail
    mock_response_fail = Mock()
    mock_response_fail.status_code = 500
    mock_response_fail.text = "Internal Server Error"
    mock_post.return_value = mock_response_fail
    
    # Set retry count to max
    worker.retry_counts[queue_id] = OSM_MAX_RETRIES
    
    # Should not retry anymore (should skip and mark error)
    sent_count = worker.process_pending(limit=10)
    assert sent_count == 0
    
    # Retry count should be removed after max retries exceeded
    assert queue_id not in worker.retry_counts
    
    # Note should have error message
    note = db.get_note_by_queue_id(queue_id)
    assert note["last_error"] is not None
    assert str(OSM_MAX_RETRIES) in note["last_error"]


@patch('gateway.osm_worker.requests.post')
def test_process_pending_retry_delay(mock_post, worker, db, monkeypatch):
    """Test that retries have delay between attempts."""
    import time
    
    # Track sleep calls
    sleep_calls = []
    def mock_sleep(seconds):
        sleep_calls.append(seconds)
    
    monkeypatch.setattr(time, "sleep", mock_sleep)
    
    # Create a pending note
    queue_id = db.create_note(
        node_id="test_node",
        lat=4.6097,
        lon=-74.0817,
        text_original="test",
        text_normalized="test"
    )
    
    # Mock API to fail
    mock_response_fail = Mock()
    mock_response_fail.status_code = 500
    mock_post.return_value = mock_response_fail
    
    # First attempt - should fail and increment retry count
    worker.process_pending(limit=10)
    assert queue_id in worker.retry_counts
    assert worker.retry_counts[queue_id] == 1
    
    # Second attempt - should have delay before retrying
    worker.process_pending(limit=10)
    
    # Should have called sleep with retry delay (after first failure)
    assert OSM_RETRY_DELAY_SECONDS in sleep_calls
