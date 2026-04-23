# Badger 2040 W — Dual-Mode Badge + Aviation Weather Display

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![MicroPython (Pimoroni)](https://img.shields.io/badge/MicroPython-Pimoroni%20Badger2040-green.svg)](https://github.com/pimoroni/pimoroni-pico)
[![METAR: aviationweather.gov](https://img.shields.io/badge/METAR-aviationweather.gov-lightgrey.svg)](https://aviationweather.gov)

MicroPython firmware for the Pimoroni [Badger 2040 W](https://shop.pimoroni.com/products/badger-2040-w)
that runs as two devices in one:

- **Badge mode** — five-screen e-ink name-card deck for conferences and meetings. Wi-Fi off, battery powered, hibernates between redraws.
- **Desk mode** — USB-powered ambient display showing the current **METAR** for any ICAO airport: temperature, wind, cloud layers, visibility, and the standard **VFR / MVFR / IFR / LIFR** flight category, with an auto-refreshing 24-hour timestamp.

A small FastAPI aggregator on a workstation does the API talking; the badge only sees one token-gated JSON blob.

---

## Contents

- [Desk-mode layout](#desk-mode-layout)
- [Architecture](#architecture)
- [Hardware](#hardware)
- [Quick start](#quick-start)
- [Configuration reference](#configuration-reference)
- [Button reference](#button-reference)
- [Aviation weather fields](#aviation-weather-fields)
- [Flight category thresholds](#flight-category-thresholds)
- [Development](#development)
- [Repository layout](#repository-layout)
- [Troubleshooting](#troubleshooting)
- [Design document](#design-document)
- [Security](#security)
- [Roadmap](#roadmap)
- [License](#license)

---

## Desk-mode layout

```
 +-----------------------------------------------+
 |                                               |
 |   72 F                    VFR         16:13  |
 |                                               |
 |  ---------------------------------------------|
 |   KLBB    vis 10SM                            |
 |   180 21kt G27                                |
 |   FEW021 FEW250                               |
 +-----------------------------------------------+
```

Top-right is the **last-updated** clock (24h local). Bottom shows the
cloud summary in standard METAR short form (`FEW060`, `BKN080`, etc.).

## Architecture

```
  +-----------------------+          HTTPS           +-----------------------+
  |  aviationweather.gov  |<-------------------------|                       |
  +-----------------------+                          |                       |
                                                     |   FastAPI aggregator  |
  +-----------------------+        HTTPS             |   (endevour or any    |
  |  Google Calendar API  |<-------------------------|    trusted host)      |
  +-----------------------+                          |                       |
                                                     |   /badge.json         |
  +-----------------------+        HTTPS             |   GET, token-gated    |
  |  Zoho Desk / CRM APIs |<-------------------------|                       |
  +-----------------------+                          +-----------+-----------+
                                                                 ^
                                                     LAN HTTP    | X-Badge-Token
                                                                 |
                                                     +-----------+-----------+
                                                     |  Badger 2040 W        |
                                                     |  MicroPython firmware |
                                                     |  Wi-Fi + e-ink panel  |
                                                     +-----------------------+
```

- **Device** never holds third-party credentials — only the aggregator does.
- **Aggregator** normalises every upstream into a single fixed JSON shape with per-tile `stale: true` fallbacks, so the device renders gracefully even when upstreams are down.
- **LAN-only** by design: the aggregator expects to live on a trusted VLAN and binds to `0.0.0.0:8088`. If you want remote access, front it with a reverse proxy that adds TLS.

## Hardware

- Pimoroni [Badger 2040 W](https://shop.pimoroni.com/products/badger-2040-w) (RP2040 + Pico W, 296 × 128 mono e-ink, five buttons, JST-PH LiPo header, USB-C)
- Pimoroni MicroPython build (any stable release that ships the `badger2040` module with `Badger2040`, `pressed_to_wake`, `woken_by_button`)
- Optional: a ≥400 mAh LiPo cell for badge mode

The host tooling (pytest, Pillow, numpy, FastAPI, httpx, uvicorn, google-api-python-client) runs on any modern Linux/macOS workstation with Python 3.11+.

## Quick start

### 1. Clone + install host dependencies

```bash
git clone https://github.com/gndl00p/badger.git
cd badger

# Firmware host-side venv (pytest + dither tool + placeholder generator)
python3 -m venv .venv
.venv/bin/pip install pytest==8.3.3 Pillow==11.0.0 numpy==2.1.3

# Aggregator venv (FastAPI + all upstream clients + test deps)
python3 -m venv server/.venv
server/.venv/bin/pip install -r server/requirements-dev.txt
```

### 2. Run the test suites

```bash
# Firmware (host-side, stubs Pimoroni libraries)
.venv/bin/pytest tests -v

# Aggregator
server/.venv/bin/pytest server/tests -v
```

Both suites together are ~90 tests. Nothing touches real hardware or
external networks — all upstream calls are mocked via `respx` and
`unittest.mock`.

### 3. Configure the aggregator

```bash
cp server/.env.example server/.env
# edit server/.env:
#   BADGE_TOKEN       = openssl rand -hex 32
#   METAR_STATION     = ICAO id, e.g. KLBB, KAUS, EGLL
#   (optional) Zoho + Google fields for calendar / ticket / task tiles
```

Launch it:

```bash
server/.venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8088 --env-file server/.env
```

Smoke-test:

```bash
TOKEN=$(grep ^BADGE_TOKEN server/.env | cut -d= -f2)
curl -sS -H "X-Badge-Token: $TOKEN" http://127.0.0.1:8088/badge.json | python3 -m json.tool
```

Deploy under `systemd` (user-scope, no root):

```bash
mkdir -p ~/.config/systemd/user
ln -sf ~/code/badger/server/badger.service ~/.config/systemd/user/badger.service
systemctl --user daemon-reload
systemctl --user enable --now badger
systemctl --user status badger
```

### 4. Configure the firmware

```bash
cp config.example.py config.py
# edit config.py:
#   NAME, TITLE, ORG, URL, CONTACT, BIO, BIO_SKILLS, NOW  (badge-mode fields)
#   WIFI_SSID, WIFI_PSK                                   (2.4 GHz network)
#   AGGREGATOR_URL    = http://<workstation-ip>:8088/badge.json
#   AGGREGATOR_TOKEN  = same value as BADGE_TOKEN in server/.env
#   REFRESH_MINUTES   = how often desk mode auto-refreshes
```

### 5. Generate placeholder assets (or supply real ones)

```bash
.venv/bin/python -m tools.make_placeholder_assets
```

Or bring your own:

```bash
.venv/bin/python -m tools.dither_image \
    --in  /path/to/headshot.png   --out assets/headshot.bin          --width 128 --height 128
.venv/bin/python -m tools.dither_image \
    --in  /path/to/wordmark.png   --out assets/robbtech_wordmark.bin --width 296 --height 128
```

### 6. Flash the device

```bash
bash tools/flash.sh
```

The script `mpremote cp`-s every file, creates `/state.json` only on first
flash (so it doesn't clobber persisted mode + last fetched data), and
triggers a soft-reset.

## Configuration reference

### `server/.env`

| Variable                      | Required | Default                         | Notes                                               |
| ----------------------------- | -------- | ------------------------------- | --------------------------------------------------- |
| `BADGE_TOKEN`                 | yes      |                                 | Shared secret between device and aggregator         |
| `METAR_STATION`               | no       | `KLBB`                          | ICAO identifier, e.g. `KAUS`, `EGLL`, `YSSY`        |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | no*      |                                 | Path to SA credentials JSON for Calendar            |
| `GOOGLE_CALENDAR_ID`          | no*      |                                 | Calendar the SA has read access to                  |
| `ZOHODESK_CLIENT_ID`          | no*      |                                 | OAuth client for Desk `/api/v1/ticketsCount`        |
| `ZOHODESK_CLIENT_SECRET`      | no*      |                                 | ″                                                   |
| `ZOHODESK_REFRESH_TOKEN`      | no*      |                                 | ″                                                   |
| `ZOHODESK_ORG_ID`             | no*      |                                 | Zoho organisation ID                                |
| `ZOHOCRM_CLIENT_ID`           | no*      |                                 | OAuth client for CRM COQL                           |
| `ZOHOCRM_CLIENT_SECRET`       | no*      |                                 | ″                                                   |
| `ZOHOCRM_REFRESH_TOKEN`       | no*      |                                 | ″                                                   |
| `ZOHOCRM_USER_ID`             | no*      |                                 | Task owner filter                                   |
| `ZOHO_ACCOUNTS_HOST`          | no       | `https://accounts.zoho.com`     | `.eu` / `.in` for non-US Zoho accounts              |
| `ZOHODESK_API_HOST`           | no       | `https://desk.zoho.com`         |                                                     |
| `ZOHOCRM_API_HOST`            | no       | `https://www.zohoapis.com`      |                                                     |

\* Each tile degrades gracefully with `stale: true` if its credentials
are missing or wrong. The weather tile alone will still work.

### `config.py` (device)

| Field              | Purpose                                                                 |
| ------------------ | ----------------------------------------------------------------------- |
| `NAME`             | Badge-mode name card                                                    |
| `TITLE`            | Badge-mode name card                                                    |
| `ORG`              | Badge-mode name card                                                    |
| `URL`              | Primary QR target on the name-card screen                               |
| `CONTACT`          | dict of `{label: value}` — rendered as a QR per field on screen 2       |
| `BIO`              | 1–2 sentence bio on screen 3                                            |
| `BIO_SKILLS`       | Skills keywords on screen 3                                             |
| `NOW`              | "What I'm working on" text, screen 4                                    |
| `WIFI_SSID`        | 2.4 GHz network the Pico W joins                                        |
| `WIFI_PSK`         | Pre-shared key                                                          |
| `AGGREGATOR_URL`   | HTTP URL to `/badge.json`, typically `http://<workstation-ip>:8088/...` |
| `AGGREGATOR_TOKEN` | Must match the aggregator's `BADGE_TOKEN`                               |
| `REFRESH_MINUTES`  | Desk-mode auto-refresh interval                                         |

## Button reference

| Button | Badge mode              | Desk mode                      |
| ------ | ----------------------- | ------------------------------ |
| A      | Previous screen         | Force refresh                  |
| B      | Redraw current          | (reserved)                     |
| B (≥2s long press) | **Toggle → Desk mode** | **Toggle → Badge mode**        |
| C      | Next screen             | (reserved)                     |
| UP     | Toggle backlight LED    | LED off                        |
| DOWN   | `halt()` (LiPo only)    | `halt()` (LiPo only)           |

Long-press B writes the new mode to `state.json` and issues
`machine.reset()`, so the device re-enters the new mode cleanly.

## Aviation weather fields

The aggregator normalises a METAR into this JSON shape:

```json
{
  "weather": {
    "temp_f": 81,
    "summary": "FEW060 BKN080",
    "icon": "cloud",
    "flight_category": "VFR",
    "station": "KLBB",
    "wind": "190 21kt G27",
    "visibility_sm": 10.0,
    "ceiling_ft": 8000,
    "raw": "KLBB 212013Z 19021G27KT 10SM FEW060 BKN080 27/14 A3002",
    "stale": false
  }
}
```

- `temp_f`          — METAR temperature in Celsius converted and rounded to Fahrenheit
- `wind`            — `DDD SSkt G GG`, `CALM`, or `VRB SSkt`
- `visibility_sm`   — statute miles; `+` stripped, fractions expanded
- `ceiling_ft`      — lowest `BKN` / `OVC` / `VV` base, feet AGL
- `summary`         — up to three cloud layers in METAR short form
- `raw`             — untouched METAR line for debugging

## Flight category thresholds

| Category | Ceiling        | Visibility (SM) |
| -------- | -------------- | --------------- |
| **LIFR** | < 500 ft       | < 1             |
| **IFR**  | < 1 000 ft     | < 3             |
| **MVFR** | ≤ 3 000 ft     | ≤ 5             |
| **VFR**  | > 3 000 ft     | > 5             |

Conditions are evaluated top-to-bottom; whichever tier matches first wins,
so a 700 ft ceiling beats a 10 SM visibility.

## Development

### Run everything

```bash
.venv/bin/pytest tests -v                 # 56 firmware tests
server/.venv/bin/pytest server/tests -v   # 34 aggregator tests
```

### Add a screen (badge mode)

1. Create `screens/<name>.py` exporting `render(display, config)` that uses the `display` protocol from `screens/common.py`.
2. Append `"<name>"` to `modes/badge.py`'s `_SCREEN_NAMES` tuple.
3. Add a `tests/test_screens_<name>.py` using `FakeDisplay` (see `tests/test_screens_name_card.py` for the template).

### Add an upstream (aggregator)

1. Create `server/upstreams/<source>.py` that exposes `async def get(client, settings) -> dict` plus a module-level `_cache = TTLCache(...)`.
2. Wire it into `server/app.py`'s `asyncio.gather` call.
3. Add a Pydantic model for the tile in `server/schemas.py` and stitch it into `BadgePayload`.
4. Add a `server/tests/test_<source>.py` with the standard happy-path / cached-within-ttl / stale-fallback / default-when-never-succeeded triplet.

### Dither your own images

```bash
.venv/bin/python -m tools.dither_image \
    --in photo.jpg --out assets/headshot.bin --width 128 --height 128
```

The tool resizes with Lanczos, Floyd-Steinberg dithers to 1-bit, and packs
MSB-first with `bit=1` meaning "drawn in current pen colour" — the
convention Pimoroni's `picographics.image()` expects.

## Repository layout

```
main.py                    device entry — dispatch + idle loop
badge_state.py             read/write /state.json (mode + last_data)
mode_switch.py             long-press detector + persisted mode flip
config.example.py          device config template (git-ignored once copied)

modes/
  badge.py                 BadgeMode: five-screen deck controller
  desk.py                  DeskMode: fetch / render / save cycle

screens/
  common.py                shared drawing helpers (clear, QR, wrap)
  name_card.py             screen 1 — headshot + name + QR
  contact.py               screen 2 — per-field QR
  bio.py                   screen 3 — wrapped bio + skills
  now.py                   screen 4 — "what I'm working on"
  logo.py                  screen 5 — full-bleed wordmark

desk/
  fetcher.py               Wi-Fi connect + HTTP GET + stale fallback
  render.py                four-tile (weather-dominant) layout

assets/
  headshot.bin             1-bit packed, 128x128
  robbtech_wordmark.bin    1-bit packed, 296x128

tools/
  dither_image.py          PNG/JPG -> 1-bit .bin
  make_placeholder_assets  silhouette + text wordmark generator
  flash.sh                 mpremote-based deploy (mkdir + cp + soft-reset)

server/
  app.py                   FastAPI app, /badge.json endpoint
  config.py                pydantic-settings model
  auth.py                  X-Badge-Token header dependency
  cache.py                 TTLCache helper
  schemas.py               Pydantic response models
  upstreams/
    weather.py             METAR via aviationweather.gov
    calendar.py            Google Calendar next event
    zoho_desk.py           Open-ticket count (/api/v1/ticketsCount)
    zoho_crm.py            COQL for tasks due today
  badger.service           user systemd unit

tests/                     host-side firmware pytest suite
  conftest.py              adds tests/stubs to sys.path
  stubs/                   fake Pimoroni / MicroPython modules
  fakes/                   FakeDisplay that records draw calls

docs/superpowers/          original design spec + implementation plans
```

## Troubleshooting

### The e-ink shows solid black blocks where images should be

Pimoroni's `picographics.image()` draws a set bit (`1`) in the current
pen colour; PIL's "1" mode uses the opposite convention. Pack black pixels
as `1` (`tools/dither_image.py` already does this — don't revert that).

### `ImportError: no module named 'state.load'` on device

The factory Pimoroni filesystem ships a `state/` directory for the stock
launcher; MicroPython resolves `import state` to that package and shadows
a `state.py`. That's why this repo's module is called `badge_state.py`.

### `AttributeError: 'NoneType' object has no attribute 'Badger2040W'`

The current Pimoroni firmware exposes `badger2040.Badger2040` (no `W`
suffix). If you're following older docs, rename accordingly.

### Buttons don't respond after the first render

`display.halt()` on the Badger 2040 W only actually cuts power when the
device is running on LiPo — on USB, VBUS keeps 3V3_EN high and `halt()`
returns immediately. The firmware sits in a polling idle loop instead
so buttons remain responsive under USB.

### Device stuck on "switching to desk..."

`machine.reset()` fires before the Wi-Fi supplicant finishes the first
associate. The desk-mode cycle returns with `"offline"` and the renderer
overwrites the splash frame once the 15-s Wi-Fi timeout or the HTTP
fetch completes. If the SSID or PSK is wrong it stays stuck — verify
with `mpremote exec 'import network; w=network.WLAN(network.STA_IF); w.active(True); print(w.scan()[:3])'`.

### Dashboard never auto-refreshes

Every `mpremote exec` sends a Ctrl-C that kills the firmware's idle loop.
After diagnostics, `mpremote connect /dev/ttyACM0 soft-reset` restarts
`main.py` cleanly and re-arms the refresh timer.

## Design document

The complete design spec lives at
[`docs/superpowers/specs/2026-04-20-name-badge-design.md`](docs/superpowers/specs/2026-04-20-name-badge-design.md).
Per-subsystem implementation plans are alongside it in
[`docs/superpowers/plans/`](docs/superpowers/plans/) — one for the
aggregator, one for the firmware, each with TDD-sized tasks and the
real bugs that surfaced during the rollout.

## Security

- `BADGE_TOKEN` is the only shared secret; keep it out of version control (`config.py` and `server/.env` are git-ignored).
- The aggregator is intended to live on a trusted LAN; do not expose port 8088 to the public internet without fronting it with TLS and at minimum a rate-limited reverse proxy.
- Zoho / Google credentials, when configured, are stored in `server/.env` only — they never reach the badge.
- Placeholder assets are regenerated deterministically; no face likeness is committed until you run `tools/dither_image.py` with your own source image.

## Roadmap

- Battery-powered desk mode with a power-source detection pass so `machine.deepsleep()` can be used instead of the polling idle loop
- Optional second METAR tile (home / destination pair)
- Per-tile refresh cadence so Zoho tiles (30 s) don't hit the same rhythm as weather (5 min)
- Alerting when flight category degrades by two tiers in one cycle

## License

Released under the [MIT License](./LICENSE). Contributions welcome via
pull request — please run both test suites locally before submitting.

## Acknowledgements

Built on the [Pimoroni Badger 2040 W](https://shop.pimoroni.com/products/badger-2040-w) hardware and the Pimoroni MicroPython build that ships `badger2040` + `picographics`. METAR data from [aviationweather.gov](https://aviationweather.gov). Test suite driven by [pytest](https://pytest.org), HTTP mocks via [respx](https://lundberg.github.io/respx/).
