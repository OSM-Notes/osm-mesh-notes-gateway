"""Notification system for DM messages."""

import time
import logging
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime

from .config import (
    DRY_RUN,
    NOTIFICATION_ANTI_SPAM_WINDOW,
    NOTIFICATION_ANTI_SPAM_MAX,
)
from .database import Database
from .commands import MSG_ACK_SUCCESS, MSG_ACK_QUEUED, MSG_Q_TO_NOTE, MSG_DUPLICATE
from .i18n import _
from .meshtastic_serial import MeshtasticSerial
from .geocoding import GeocodingService

logger = logging.getLogger(__name__)

# Meshtastic message size limit (bytes) - leave some margin for encoding overhead
MESHTASTIC_MAX_MESSAGE_SIZE = 220


def split_long_message(message: str, max_size: int = MESHTASTIC_MAX_MESSAGE_SIZE) -> List[str]:
    """
    Split a long message into smaller parts that fit within Meshtastic limits.

    Tries to split at line breaks or spaces to avoid breaking words.
    Adds part indicators (1/3, 2/3, etc.) to each part.

    Args:
        message: The message to split
        max_size: Maximum size per part in bytes (default: 220)

    Returns:
        List of message parts
    """
    message_bytes = message.encode('utf-8')
    if len(message_bytes) <= max_size:
        return [message]

    parts = []
    lines = message.split('\n')
    current_part = []
    current_size = 0

    # Estimate size for part indicator (e.g., "[1/3]\n")
    indicator_size = len("[1/X]\n".encode('utf-8'))

    for line in lines:
        line_bytes = line.encode('utf-8')
        line_size = len(line_bytes)

        # If single line is too long, split it by words
        if line_size > max_size - indicator_size:
            words = line.split(' ')
            for word in words:
                word_bytes = word.encode('utf-8')
                word_size = len(word_bytes)

                # If word itself is too long, split it (shouldn't happen, but handle it)
                if word_size > max_size - indicator_size:
                    # Split word character by character (last resort)
                    for char in word:
                        char_bytes = char.encode('utf-8')
                        if current_size + len(char_bytes) + indicator_size > max_size:
                            if current_part:
                                parts.append('\n'.join(current_part))
                                current_part = []
                                current_size = 0
                        current_part.append(char)
                        current_size += len(char_bytes)
                    # Add space after word
                    if current_part:
                        current_part[-1] += ' '
                        current_size += 1
                else:
                    # Check if adding this word would exceed limit
                    space_size = 1 if current_part else 0
                    if current_size + space_size + word_size + indicator_size > max_size:
                        if current_part:
                            parts.append('\n'.join(current_part))
                            current_part = []
                            current_size = 0

                    if current_part:
                        current_part[-1] += ' ' + word
                        current_size += space_size + word_size
                    else:
                        current_part.append(word)
                        current_size += word_size
        else:
            # Check if adding this line would exceed limit
            newline_size = 1 if current_part else 0
            if current_size + newline_size + line_size + indicator_size > max_size:
                if current_part:
                    parts.append('\n'.join(current_part))
                    current_part = []
                    current_size = 0

            current_part.append(line)
            current_size += newline_size + line_size

    # Add remaining part
    if current_part:
        parts.append('\n'.join(current_part))

    # Add part indicators
    total_parts = len(parts)
    if total_parts > 1:
        for i, part in enumerate(parts, 1):
            parts[i - 1] = f"[{i}/{total_parts}]\n{part}"

    return parts


class NotificationManager:
    """Manage DM notifications with anti-spam."""

    def __init__(self, serial: MeshtasticSerial, db: Database):
        self.serial = serial
        self.db = db
        self.node_notification_times: Dict[str, List[float]] = defaultdict(list)
        self.geocoding = GeocodingService()

    def send_ack(
        self,
        node_id: str,
        status: str,
        local_queue_id: Optional[str] = None,
        osm_note_id: Optional[int] = None,
        osm_note_url: Optional[str] = None,
    ):
        # Get user's preferred language
        user_lang = self.db.get_user_language(node_id)
        """
        Send acknowledgment DM to a node.

        Sends different messages based on status. Implements anti-spam
        to prevent flooding nodes with notifications.

        Args:
            node_id: Target Meshtastic node ID
            status: ACK status - one of:
                - 'success': Note created in OSM (requires osm_note_id and osm_note_url)
                - 'queued': Note queued for sending (requires local_queue_id)
                - 'duplicate': Duplicate note detected
            local_queue_id: Queue ID for queued status (e.g., "Q-0001")
            osm_note_id: OSM note ID for success status
            osm_note_url: OSM note URL for success status

        Note:
            Respects anti-spam limits (max 3 notifications per minute per node).
            In DRY_RUN mode, logs instead of sending.
        """
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would send ACK to {node_id}: {status}")
            return

        # Determine if we should show the warning (every 5 notes)
        # Get total notes count for this user to decide if we show warning
        node_stats = self.db.get_node_stats(node_id)
        total_notes = node_stats.get("total", 0)
        # Show warning every 5 notes (on notes 5, 10, 15, 20, etc.)
        show_warning = (total_notes > 0 and total_notes % 5 == 0)

        if status == "success" and osm_note_id and osm_note_url:
            # Get note location for geocoding
            location_str = ""
            if local_queue_id:
                note_data = self.db.get_note_by_queue_id(local_queue_id)
                if note_data:
                    lat = note_data.get("lat")
                    lon = note_data.get("lon")
                    if lat and lon:
                        address = self.geocoding.reverse_geocode(lat, lon)
                        if address:
                            location_str = _("📍 Ubicación: {address}\n", user_lang).format(address=address)

            message = MSG_ACK_SUCCESS(
                id=osm_note_id,
                url=osm_note_url,
                location=location_str,
                locale=user_lang,
                show_warning=show_warning
            )
        elif status == "queued" and local_queue_id:
            message = MSG_ACK_QUEUED(queue_id=local_queue_id, locale=user_lang, show_warning=show_warning)
        elif status == "reject":
            # Message should be passed separately
            return
        elif status == "duplicate":
            message = MSG_DUPLICATE(locale=user_lang, show_warning=show_warning)
        else:
            logger.warning(f"Unknown ACK status: {status}")
            return

        if message:
            # Split message if too long
            parts = split_long_message(message)

            # Check anti-spam once before sending all parts
            if self._check_antispam(node_id):
                logger.debug(f"Anti-spam: skipping ACK to {node_id}")
                return

            # Send all parts with delays
            for i, part in enumerate(parts):
                if i > 0:
                    # Wait between parts to avoid overwhelming the node
                    # Increased delay to 3 seconds for better reliability
                    logger.debug(f"Waiting before sending ACK part {i+1}/{len(parts)}")
                    time.sleep(3.0)
                success = self.serial.send_dm(node_id, part)
                if success:
                    logger.info(f"Successfully sent ACK part {i+1}/{len(parts)} to {node_id} ({len(part.encode('utf-8'))} bytes)")
                    # Only record notification for the first part
                    if i == 0:
                        self._record_notification(node_id)
                else:
                    logger.error(f"Failed to send ACK part {i+1}/{len(parts)} to {node_id}")
                    break

    def send_reject(self, node_id: str, message: str):
        """Send rejection message."""
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would send reject to {node_id}: {message[:50]}...")
            return

        self._send_dm_with_antispam(node_id, message)

    def send_command_response(self, node_id: str, message: str):
        """Send command response, splitting long messages if necessary."""
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would send command response to {node_id}: {message[:50]}...")
            return

        # Split message if too long
        parts = split_long_message(message)

        # Check anti-spam once before sending all parts
        if self._check_antispam(node_id):
            logger.debug(f"Anti-spam: skipping command response to {node_id}")
            return

        # Send all parts (they're part of the same response)
        # Only record one notification to avoid triggering anti-spam for parts
        logger.info(f"Sending {len(parts)} parts to {node_id}")
        for i, part in enumerate(parts):
            if i > 0:
                # Longer delay between parts to ensure mesh network can handle them
                # Meshtastic mesh networks may need more time to propagate messages
                # Increased delay to 3.5 seconds to reduce packet loss (especially for osmhelp/osmmorehelp)
                logger.debug(f"Waiting before sending part {i+1}/{len(parts)}")
                time.sleep(3.5)
            success = self.serial.send_dm(node_id, part)
            if success:
                logger.info(f"Successfully sent part {i+1}/{len(parts)} to {node_id} ({len(part.encode('utf-8'))} bytes)")
                # Only record notification for the first part
                if i == 0:
                    self._record_notification(node_id)
            else:
                logger.error(f"Failed to send part {i+1}/{len(parts)} to {node_id}")

    def process_sent_notifications(self):
        """Process pending sent notifications (Q→Note)."""
        pending = self.db.get_pending_for_notification()
        if not pending:
            return

        # Group by node_id for anti-spam
        node_notes: Dict[str, List[Dict]] = defaultdict(list)
        for note in pending:
            node_notes[note["node_id"]].append(note)

        for node_id, notes in node_notes.items():
            # Get user's preferred language
            user_lang = self.db.get_user_language(node_id)

            # Check anti-spam
            if self._check_antispam(node_id):
                # Send summary instead
                self._send_summary(node_id, len(notes))
            else:
                # Send individual notifications
                for note in notes[:NOTIFICATION_ANTI_SPAM_MAX]:
                    # Get location for geocoding
                    location_str = ""
                    lat = note.get("lat")
                    lon = note.get("lon")
                    if lat and lon:
                        address = self.geocoding.reverse_geocode(lat, lon)
                        if address:
                            location_str = _("\n📍 Ubicación: {address}", user_lang).format(address=address)

                    message = MSG_Q_TO_NOTE(
                        queue_id=note["local_queue_id"],
                        note_id=note["osm_note_id"],
                        url=note["osm_note_url"],
                        locale=user_lang
                    ) + location_str

                    if self.serial.send_dm(node_id, message):
                        self.db.mark_notified_sent(note["local_queue_id"])
                        self._record_notification(node_id)

    def process_failed_notifications(self):
        """Process notifications for notes that failed after max retries."""
        failed = self.db.get_failed_notes_for_notification()
        if not failed:
            return

        # Group by node_id
        node_notes: Dict[str, List[Dict]] = defaultdict(list)
        for note in failed:
            node_notes[note["node_id"]].append(note)

        for node_id, notes in node_notes.items():
            # Get user's preferred language
            user_lang = self.db.get_user_language(node_id)
            # Send error notification
            error_msg = (
                _("❌ {count} reporte(s) fallaron después de múltiples intentos.\n", user_lang).format(count=len(notes))
                + _("Error: {error}\n", user_lang).format(error=notes[0].get('last_error', _('Error desconocido', user_lang))[:100])
                + _("Usa #osmlist para ver detalles.\n", user_lang)
                + _("⚠️ No envíes datos personales ni emergencias médicas.", user_lang)
            )
            if self.serial.send_dm(node_id, error_msg):
                # Mark as notified
                for note in notes:
                    self.db.mark_notified_sent(note["local_queue_id"])
                self._record_notification(node_id)

    def _send_dm_with_antispam(self, node_id: str, message: str):
        """Send DM with anti-spam check."""
        if self._check_antispam(node_id):
            logger.debug(f"Anti-spam: skipping DM to {node_id}")
            return

        if self.serial.send_dm(node_id, message):
            self._record_notification(node_id)

    def _check_antispam(self, node_id: str) -> bool:
        """Check if node has exceeded anti-spam limit."""
        now = time.time()
        times = self.node_notification_times[node_id]

        # Remove old entries
        cutoff = now - NOTIFICATION_ANTI_SPAM_WINDOW
        times[:] = [t for t in times if t > cutoff]

        return len(times) >= NOTIFICATION_ANTI_SPAM_MAX

    def _record_notification(self, node_id: str):
        """Record notification timestamp."""
        self.node_notification_times[node_id].append(time.time())

    def _send_summary(self, node_id: str, count: int):
        """Send summary message when anti-spam triggered."""
        message = (
            f"✅ Se enviaron {count} reportes en cola. "
            "Usa #osmlist para ver detalles."
        )
        if self.serial.send_dm(node_id, message):
            # Mark all as notified
            pending = self.db.get_pending_for_notification()
            for note in pending:
                if note["node_id"] == node_id:
                    self.db.mark_notified_sent(note["local_queue_id"])
