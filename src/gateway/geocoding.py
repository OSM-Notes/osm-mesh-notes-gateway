"""Reverse geocoding using OSM Nominatim API."""

import time
import logging
import requests
from typing import Optional, Dict, Any

from .config import NOMINATIM_API_URL, NOMINATIM_RATE_LIMIT_SECONDS, NOMINATIM_TIMEOUT

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for reverse geocoding coordinates to addresses."""

    def __init__(self):
        self.last_request_time = 0.0

    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Reverse geocode coordinates to a human-readable address.
        
        Uses OSM Nominatim API to get address information. Returns a formatted
        string like "Prado Veraniego, Suba, Bogotá, Colombia" or None on error.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Formatted address string or None if geocoding fails
            
        Note:
            Respects Nominatim rate limiting (max 1 request per second).
            Returns None on errors (does not raise exceptions).
        """
        # Rate limiting
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < NOMINATIM_RATE_LIMIT_SECONDS:
            sleep_time = NOMINATIM_RATE_LIMIT_SECONDS - time_since_last
            logger.debug(f"Geocoding rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)

        try:
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1,
                "accept-language": "es",  # Spanish for Colombia
            }

            logger.debug(f"Reverse geocoding: ({lat}, {lon})")

            response = requests.get(
                NOMINATIM_API_URL,
                params=params,
                timeout=NOMINATIM_TIMEOUT,
                headers={"User-Agent": "OSM-Mesh-Notes-Gateway/1.0"},  # Required by Nominatim
            )

            self.last_request_time = time.time()

            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})
                
                # Build address string from components
                # Priority: neighbourhood/suburb > city > state > country
                parts = []
                
                # Try different address component names
                neighbourhood = (
                    address.get("neighbourhood") or
                    address.get("suburb") or
                    address.get("quarter") or
                    address.get("village")
                )
                if neighbourhood:
                    parts.append(neighbourhood)
                
                city = (
                    address.get("city") or
                    address.get("town") or
                    address.get("municipality")
                )
                if city and city != neighbourhood:
                    parts.append(city)
                
                state = address.get("state") or address.get("region")
                if state:
                    parts.append(state)
                
                country = address.get("country")
                if country:
                    parts.append(country)
                
                if parts:
                    address_str = ", ".join(parts)
                    logger.debug(f"Geocoded address: {address_str}")
                    return address_str
                else:
                    logger.debug("No address components found")
                    return None
            else:
                logger.debug(f"Geocoding API error {response.status_code}: {response.text[:100]}")
                return None

        except requests.exceptions.Timeout:
            logger.debug("Geocoding API timeout")
            return None
        except requests.exceptions.ConnectionError:
            logger.debug("Geocoding API connection error")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error in geocoding: {e}")
            return None
