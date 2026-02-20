#!/bin/bash
# Sync skills from submodules into skills/ directory
# Run this after updating submodules to keep skills/ in sync
#
# Usage:
#   git submodule update --remote
#   bash sync.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Syncing skills from submodules..."

for skill in hifi-download quark-download zlib-download; do
    src="${skill}-skill/skills/${skill}"
    dst="skills/${skill}"

    if [ ! -d "$src" ]; then
        echo "  SKIP $skill (submodule not initialized)"
        continue
    fi

    rm -rf "$dst"
    cp -R "$src" "$dst"
    echo "  OK   $skill"
done

echo "Done. Remember to commit the changes."
