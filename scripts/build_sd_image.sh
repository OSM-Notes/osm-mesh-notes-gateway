#!/bin/bash
# Build a compressed microSD disk image from a golden card, with checksum,
# and optionally upload it to a GitHub Release.
#
# Run on a Linux PC (NOT on the Pi), with the microSD inserted as a block device.
#
# DANGER: --device must be the SD card (e.g. /dev/sdb), NEVER your system disk.
#
# Usage:
#   sudo bash scripts/build_sd_image.sh --device /dev/sdb --version v0.2.0
#   sudo bash scripts/build_sd_image.sh --device /dev/sdb --version v0.2.0 \
#        --upload --repo OSM-Notes/osm-mesh-notes-gateway
#
# Requires: dd, xz, sha256sum; for --upload: gh (GitHub CLI) authenticated.
# Output dir default: ./dist/

set -euo pipefail

DEVICE=""
VERSION=""
OUT_DIR=""
UPLOAD=0
REPO="${GITHUB_REPOSITORY:-OSM-Notes/osm-mesh-notes-gateway}"
SKIP_CONFIRM=0
BS="4M"

while [ $# -gt 0 ]; do
  case "$1" in
    --device|-d)
      DEVICE="${2:-}"
      shift 2
      ;;
    --version|-v)
      VERSION="${2:-}"
      shift 2
      ;;
    --out)
      OUT_DIR="${2:-}"
      shift 2
      ;;
    --upload)
      UPLOAD=1
      shift
      ;;
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --yes)
      SKIP_CONFIRM=1
      shift
      ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if [ -z "$DEVICE" ] || [ -z "$VERSION" ]; then
  echo "Usage: sudo $0 --device /dev/sdX --version v0.2.0 [--upload] [--repo owner/name]" >&2
  exit 2
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (needed for dd of block devices): sudo bash $0 ..." >&2
  exit 1
fi

if [ ! -b "$DEVICE" ]; then
  echo "ERROR: $DEVICE is not a block device" >&2
  exit 1
fi

# Refuse obvious system disks
case "$DEVICE" in
  /dev/sda|/dev/nvme0n1|/dev/mmcblk0)
    # mmcblk0 might BE the SD on some hosts — still warn hard
    ;;
esac

SIZE_BYTES=$(blockdev --getsize64 "$DEVICE" 2>/dev/null || echo 0)
SIZE_GB=$(awk -v b="$SIZE_BYTES" 'BEGIN { printf "%.1f", b/1024/1024/1024 }')

echo "=== SD image build ==="
echo "Device:  $DEVICE ($SIZE_GB GB)"
echo "Version: $VERSION"
echo "Repo:    $REPO"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL "$DEVICE" || true
echo ""

if [ "$SKIP_CONFIRM" -ne 1 ]; then
  echo "WARNING: This will READ the entire device $DEVICE."
  echo "Confirm this is the golden microSD (not your laptop disk)."
  read -r -p "Type the device path again to continue: " confirm
  if [ "$confirm" != "$DEVICE" ]; then
    echo "Aborted."
    exit 1
  fi
fi

# Unmount partitions if mounted
for part in ${DEVICE}*? ${DEVICE}p*; do
  if [ -e "$part" ] && findmnt "$part" >/dev/null 2>&1; then
    echo "Unmounting $part"
    umount "$part" || umount -l "$part" || true
  fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/dist}"
mkdir -p "$OUT_DIR"

SAFE_VER=$(echo "$VERSION" | tr '/' '-')
RAW="$OUT_DIR/osm-mesh-notes-gateway-${SAFE_VER}-pi.img"
XZ="$RAW.xz"
SUM="$XZ.sha256"

echo ">>> Imaging $DEVICE → $RAW (this can take a long time)"
dd if="$DEVICE" of="$RAW" bs="$BS" status=progress conv=fsync

echo ">>> Compressing with xz ..."
xz -T0 -f -v "$RAW"
# xz removes .img and leaves .img.xz

echo ">>> Checksum"
sha256sum "$XZ" | tee "$SUM"

echo ""
echo "Artifacts:"
ls -lh "$XZ" "$SUM"
echo ""

if [ "$UPLOAD" -eq 1 ]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: gh CLI not found. Install GitHub CLI and run: gh auth login" >&2
    exit 1
  fi
  # gh may need to run as the invoking user, not root
  GH_USER="${SUDO_USER:-$USER}"
  echo ">>> Uploading to GitHub Release $VERSION on $REPO (as $GH_USER)"
  if ! sudo -u "$GH_USER" gh release view "$VERSION" --repo "$REPO" >/dev/null 2>&1; then
    echo "Release $VERSION does not exist yet — creating it"
    sudo -u "$GH_USER" gh release create "$VERSION" \
      --repo "$REPO" \
      --title "OSM Mesh Notes Gateway $VERSION" \
      --notes "Raspberry Pi microSD image for this release.

## SD image
Flash \`$XZ\` with [Raspberry Pi Imager](https://www.raspberrypi.com/software/) (Use custom image).

Verify: \`sha256sum -c $(basename "$SUM")\`

After first boot see \`/var/lib/lora-osmnotes/IMAGE_INFO.txt\`.

## Install without image
\`git checkout $VERSION && sudo bash scripts/install_pi.sh\`
"
  fi
  sudo -u "$GH_USER" gh release upload "$VERSION" "$XZ" "$SUM" --repo "$REPO" --clobber
  echo "Uploaded."
  sudo -u "$GH_USER" gh release view "$VERSION" --repo "$REPO" --web 2>/dev/null || \
    echo "View: https://github.com/$REPO/releases/tag/$VERSION"
else
  echo "Skipped upload. To publish later:"
  echo "  gh release upload $VERSION $XZ $SUM --repo $REPO"
fi

echo "Done."
