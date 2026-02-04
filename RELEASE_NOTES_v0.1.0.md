# Release v0.1.0 - Initial MVP Release

**Release Date**: February 3, 2026

This is the initial MVP release of the OSM Mesh Notes Gateway, enabling offline field reports via LoRa mesh (Meshtastic) to be converted into OpenStreetMap Notes.

## What's New

### Core Functionality

- **Meshtastic Integration**: USB serial communication with auto-reconnect
- **GPS Validation**: Position caching with recency checks (15s ideal, 60s max)
- **Command Processing**: Support for `#osmnote`, `#osmhelp`, `#osmstatus`, `#osmcount`, `#osmlist`, `#osmqueue`
- **Store-and-Forward**: SQLite-based queue for offline operation
- **OSM Notes API**: Integration with rate limiting (≥3s between sends)
- **Notifications**: DM-based acknowledgments with anti-spam protection

### Key Features

- **Deduplication**: Conservative deduplication to avoid losing real repeated events
- **Mobility-Aware**: GPS recency validation prevents misplaced notes during movement
- **Offline-First**: Reports are queued locally when Internet is unavailable
- **Privacy-Focused**: All messages include privacy warnings; no PII collection

### Documentation

- **Canonical Specification**: `docs/spec.md` - Complete MVP specification
- **Architecture Guide**: `docs/architecture.md` - System design and components
- **User Guide**: `README.md` - Non-technical introduction and quick start
- **Troubleshooting**: `docs/TROUBLESHOOTING.md` - Common issues and solutions
- **Security Guide**: `docs/SECURITY.md` - Security best practices
- **API Reference**: `docs/API.md` - Internal API documentation

### Installation & Deployment

- **Installation Script**: `scripts/install_pi.sh` - Automated setup for Raspberry Pi OS
- **Device Detection**: `scripts/detect_serial.sh` - Helper to find serial devices
- **Systemd Service**: Pre-configured service unit for 24/7 operation
- **Configuration**: Environment-based configuration with `.env` file

### Development

- **Test Suite**: Comprehensive pytest-based tests
- **Code Quality**: Black formatting + Ruff linting configured
- **Dependencies**: `pyproject.toml` as source of truth (PEP 621)

## Installation

```bash
git clone https://github.com/OSM-Notes/osm-mesh-notes-gateway.git
cd osm-mesh-notes-gateway
git checkout v0.1.0
sudo bash scripts/install_pi.sh
```

## Quick Start

1. Connect Meshtastic device via USB
2. Run `bash scripts/detect_serial.sh` to find your device
3. Configure `/var/lib/lora-osmnotes/.env` with `SERIAL_PORT`
4. Start service: `sudo systemctl start lora-osmnotes`
5. Check logs: `sudo journalctl -u lora-osmnotes -f`

## Usage

From Meshtastic app (connected to T-Echo via Bluetooth):

- `#osmnote <mensaje>` - Create OSM note
- `#osmhelp` - Show help
- `#osmstatus` - Check gateway status
- `#osmlist` - List your recent notes

## Important Notes

⚠️ **This is NOT an emergency response system** - Do not use for life-critical situations.

🔒 **Privacy**: 
- Messages travel over public LoRa channels
- OSM Notes are publicly visible
- Do not include personal data (PII)

## Credits

Developed by OSM-Notes Project Team with support from:
- **AC3** (Asociación de Cartografía Colaborativa de Colombia)
- **NASA Lifelines** (Speed Dating grant)

See [AUTHORS](AUTHORS) for full contributor list.

## Related Publications

- **OSM Diary** (English, high-level): https://www.openstreetmap.org/user/AngocA/diary/408194
- **osm.lat Blog** (Spanish, technical): https://www.osm.lat/reportes-en-terreno-sin-internet-lora-mesh-meshtastic-%e2%86%92-notas-osm-con-gateway-en-raspberry-pi/

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed change history.

## Documentation

- [README.md](README.md) - User guide and quick start
- [docs/spec.md](docs/spec.md) - Canonical specification
- [docs/architecture.md](docs/architecture.md) - System architecture
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Troubleshooting guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

## Support

- **Issues**: https://github.com/OSM-Notes/osm-mesh-notes-gateway/issues
- **Security**: https://github.com/OSM-Notes/osm-mesh-notes-gateway/security/advisories

## License

GPL-3.0 - See [LICENSE](LICENSE) file.
