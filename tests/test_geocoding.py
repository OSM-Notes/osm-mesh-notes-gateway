"""Tests for reverse geocoding."""

import pytest
from unittest.mock import Mock, patch
from gateway.geocoding import GeocodingService


@pytest.fixture
def geocoding():
    """Create geocoding service."""
    return GeocodingService()


@patch('gateway.geocoding.requests.get')
def test_reverse_geocode_success(mock_get, geocoding):
    """Test successful reverse geocoding."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "address": {
            "neighbourhood": "Prado Veraniego",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "country": "Colombia"
        }
    }
    mock_get.return_value = mock_response
    
    result = geocoding.reverse_geocode(4.6097, -74.0817)
    
    assert result is not None
    assert "Prado Veraniego" in result
    assert "Bogotá" in result
    assert "Colombia" in result


@patch('gateway.geocoding.requests.get')
def test_reverse_geocode_no_address_components(mock_get, geocoding):
    """Test geocoding with no address components."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "address": {}
    }
    mock_get.return_value = mock_response
    
    result = geocoding.reverse_geocode(4.6097, -74.0817)
    
    assert result is None


@patch('gateway.geocoding.requests.get')
def test_reverse_geocode_api_error(mock_get, geocoding):
    """Test geocoding with API error."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response
    
    result = geocoding.reverse_geocode(4.6097, -74.0817)
    
    assert result is None


@patch('gateway.geocoding.requests.get')
def test_reverse_geocode_timeout(mock_get, geocoding):
    """Test geocoding with timeout."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout()
    
    result = geocoding.reverse_geocode(4.6097, -74.0817)
    
    assert result is None


@patch('gateway.geocoding.requests.get')
def test_reverse_geocode_connection_error(mock_get, geocoding):
    """Test geocoding with connection error."""
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError()
    
    result = geocoding.reverse_geocode(4.6097, -74.0817)
    
    assert result is None


@patch('gateway.geocoding.requests.get')
def test_reverse_geocode_rate_limiting(mock_get, geocoding):
    """Test that geocoding respects rate limiting."""
    import time
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "address": {
            "city": "Bogotá",
            "country": "Colombia"
        }
    }
    mock_get.return_value = mock_response
    
    # First call
    start_time = time.time()
    result1 = geocoding.reverse_geocode(4.6097, -74.0817)
    elapsed1 = time.time() - start_time
    
    # Second call immediately after should wait
    start_time = time.time()
    result2 = geocoding.reverse_geocode(4.6097, -74.0817)
    elapsed2 = time.time() - start_time
    
    assert result1 is not None
    assert result2 is not None
    # Second call should have waited at least 1 second (rate limit)
    assert elapsed2 >= 0.9  # Allow some margin for test execution time
