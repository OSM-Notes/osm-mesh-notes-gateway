#!/bin/bash
# Compile translation files (.po to .mo)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCALE_DIR="$PROJECT_ROOT/locale"

echo "Compiling translations..."

for lang_dir in "$LOCALE_DIR"/*/LC_MESSAGES; do
    if [ -d "$lang_dir" ]; then
        po_file="$lang_dir/lora-osmnotes.po"
        mo_file="$lang_dir/lora-osmnotes.mo"
        
        if [ -f "$po_file" ]; then
            echo "Compiling $po_file -> $mo_file"
            msgfmt -o "$mo_file" "$po_file"
        fi
    fi
done

echo "Translations compiled successfully!"
