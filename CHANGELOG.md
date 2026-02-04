# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-03

### Added
- Initial MVP implementation
- Meshtastic USB serial communication with auto-reconnect
- GPS position caching and validation (POS_GOOD=15s, POS_MAX=60s)
- Command processing (#osmnote, #osmhelp, #osmstatus, #osmcount, #osmlist, #osmqueue)
- Deduplication logic (intra-node, 4 decimal precision, 120s time bucket)
- SQLite store-and-forward queue
- OSM Notes API integration with rate limiting (≥3s between sends)
- DM notification system with anti-spam (max 3/min/node)
- Systemd service configuration
- Comprehensive test suite with pytest
- Installation script for Raspberry Pi OS (`scripts/install_pi.sh`)
- Serial device detection script (`scripts/detect_serial.sh`)
- Documentation structure:
  - README.md (user-friendly, non-technical)
  - docs/spec.md (canonical specification)
  - docs/architecture.md (system architecture)
  - docs/message-format.md (Meshtastic message formats)
  - docs/API.md (internal API reference)
  - docs/SECURITY.md (security best practices)
  - docs/TROUBLESHOOTING.md (troubleshooting guide)
  - CONTRIBUTING.md (contribution guidelines)
- Project metadata files:
  - CHANGELOG.md (Keep a Changelog format)
  - CITATION.cff (citation metadata)
  - AUTHORS (authors and contributors)

### Security
- Non-root execution by default (User=nobody in systemd template)
- Auto-detection of service user in install script
- Security documentation and best practices

### Fixed
- Word boundary bug in `#osmnote` extraction (prevented false positives like `#osmnotetest`)
- Systemd service user configuration (auto-detection and fix script)
- Circular import in database module
- Test environment setup (permissions, mocking)

### Changed
- Moved documentation files to `docs/` directory for better organization
- Updated repository references to `https://github.com/OSM-Notes/osm-mesh-notes-gateway`
- Improved code documentation and docstrings
- Enhanced README.md for non-technical readers
- Added code formatting and linting tools (Black + Ruff)
- Established `pyproject.toml` as source of truth for dependencies

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
