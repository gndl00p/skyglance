#!/usr/bin/env bash
set -euo pipefail

DEVICE="${DEVICE:-/dev/ttyACM0}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MP="mpremote connect $DEVICE"

echo "Flashing to $DEVICE from $HERE"

$MP mkdir :modes || true
$MP mkdir :screens || true
$MP mkdir :desk || true
$MP mkdir :assets || true

$MP cp "$HERE/main.py" :main.py
$MP cp "$HERE/badge_state.py" :badge_state.py
$MP cp "$HERE/mode_switch.py" :mode_switch.py

for f in "$HERE/modes"/*.py; do $MP cp "$f" ":modes/$(basename "$f")"; done
for f in "$HERE/screens"/*.py; do $MP cp "$f" ":screens/$(basename "$f")"; done
for f in "$HERE/desk"/*.py; do $MP cp "$f" ":desk/$(basename "$f")"; done
for f in "$HERE/assets"/*.bin; do $MP cp "$f" ":assets/$(basename "$f")"; done

if [ ! -f "$HERE/config.py" ]; then
  echo "!! $HERE/config.py missing — copy config.example.py and fill in secrets before flashing config."
else
  $MP cp "$HERE/config.py" :config.py
fi

# Only create /state.json on first flash — don't clobber persisted mode+last_data.
$MP exec 'import os
try:
    os.stat("/state.json")
    print("state.json exists, leaving alone")
except OSError:
    open("/state.json","w").write("{}")
    print("state.json created")'

echo "Done. Soft-reset:"
$MP soft-reset
