# Release v0.2.0 — Field-ready stable

Date: 2026-08-12

Second numbered release after the MVP (`v0.1.0`). Suitable for real deployments while leaving room for fixes found in field testing before calling it 1.0.0.

## Highlights

- Spec and docs aligned with the running code (`POS_MAX=120s`, Meshtastic protobuf, full command set)
- Critical GPS age / double-ACK / OSM retry fixes
- Rich `#osmstatus` (no SSH needed for day-to-day health)
- Default LoRa region **ANZ** (Colombia per Meshtastic region-by-country)
- Adoption pack: FIELD_CARD, ADOPTION, health/mission/export/backup scripts
- Optional SD image build/upload tooling (image asset not required for this release)

## Install

```bash
git clone https://github.com/OSM-Notes/osm-mesh-notes-gateway.git
cd osm-mesh-notes-gateway
git checkout v0.2.0
sudo bash scripts/install_pi.sh
```

Configure `/var/lib/lora-osmnotes/.env` (`SERIAL_PORT`, `TZ`, `LORA_REGION=ANZ`), start the service, then from Meshtastic: `#osmstatus`.

Field nodes (T-Echo): LoRa region **ANZ**, same channel as the gateway.

## Not in this release

- Pre-built `.img.xz` on GitHub Releases (optional; see `docs/SD_IMAGE_RELEASE.md`)

## Full changelog

See [CHANGELOG.md](CHANGELOG.md) section `[0.2.0]`.
