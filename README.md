# Badger 2040 W — Dual-Mode Badge + Aviation Weather Display

Pimoroni Badger 2040 W firmware that runs in two modes:

- **Badge mode** — portable conference name badge; five e-ink screens (name card, contact info with QR, bio, "what I'm working on", full-bleed logo), Wi-Fi off, `halt()` between refreshes for long battery life.
- **Desk mode** — USB-powered weather display; current **METAR** for a configured airport (default `KLBB`) with big-font temp, flight category (VFR / MVFR / IFR / LIFR), wind, visibility, cloud layers, and a last-updated clock.

A small FastAPI service on the workstation (`server/`) aggregates the METAR (plus optional Google Calendar, Zoho Desk tickets, and Zoho CRM tasks) and hands the badge a single token-gated JSON blob, so the device never talks to third-party APIs directly.

<img src="docs/layout.txt" alt="Desk-mode layout sketch" />

## Layout

```
 ┌─────────────────────────────────┐
 │ 72 F              VFR    16:13  │
 │ ─────────────────────────────── │
 │ KLBB  vis 10SM                  │
 │ 180 21kt G27                    │
 │ FEW021 FEW250                   │
 └─────────────────────────────────┘
```

## Repo layout

```
main.py                 device entry — dispatches to mode + runs idle loop
badge_state.py          read/write state.json (mode + last_data)
mode_switch.py          long-press B detector + mode transition
config.example.py       template for on-device config (WiFi, token, URL)
modes/                  BadgeMode + DeskMode controllers
screens/                badge-mode screen renderers + common drawing helpers
desk/                   desk-mode fetcher (Wi-Fi, urequests) + renderer
assets/                 1-bit packed .bin images (headshot, wordmark)
tools/                  host-side utilities
  dither_image.py         PNG/JPG → 1-bit .bin for display.image()
  make_placeholder_assets.py
  flash.sh                mpremote-based deploy
server/                 FastAPI aggregator (see server/README.md)
tests/                  host-side pytest suite (stubs in tests/stubs)
docs/superpowers/       implementation spec + plans
```

## Quick start

### Aggregator (workstation)

```bash
python3 -m venv server/.venv
server/.venv/bin/pip install -r server/requirements-dev.txt
cp server/.env.example server/.env          # fill in BADGE_TOKEN + METAR_STATION
server/.venv/bin/pytest server/tests -v     # host-side suite (~30 tests)
server/.venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8088 --env-file server/.env
```

Only `BADGE_TOKEN` and `METAR_STATION` are required for a weather-only
deployment — Zoho / Google fields are optional; missing creds produce
`stale: true` tiles and do not fail the endpoint.

### Firmware (Badger 2040 W)

```bash
python3 -m venv .venv
.venv/bin/pip install pytest Pillow numpy
.venv/bin/pytest tests -v                   # host-side firmware suite

cp config.example.py config.py              # fill in WIFI_SSID / WIFI_PSK / AGGREGATOR_URL / AGGREGATOR_TOKEN
python -m tools.make_placeholder_assets     # or replace with real art via tools/dither_image.py
bash tools/flash.sh                         # mpremote cp every file, soft-reset
```

`config.py` is git-ignored — it contains your Wi-Fi password and badge token
and must never be committed.

## Buttons (device)

| Button | Badge mode              | Desk mode                       |
| ------ | ----------------------- | ------------------------------- |
| A      | Previous screen         | Force refresh                   |
| B      | Redraw current          | (reserved)                      |
| B (2s) | Toggle mode → Desk      | Toggle mode → Badge             |
| C      | Next screen             | (reserved)                      |
| UP     | Toggle LED              | LED off                         |
| DOWN   | `halt()` (battery only) | `halt()` (battery only)         |

## Aviation weather

Desk mode pulls **METAR** directly from `aviationweather.gov` — no API key
required. The aggregator normalises the response into:

- `temp_f` — Celsius → Fahrenheit, rounded
- `wind` — formatted as `DDD SSkt G GG` (e.g. `190 21kt G27`), `CALM` when calm, `VRB SSkt` when variable
- `visibility_sm` — statute miles (strips `+` suffix, handles fractional reports)
- `ceiling_ft` — lowest `BKN` / `OVC` / `VV` layer, in feet
- `flight_category` — `VFR` / `MVFR` / `IFR` / `LIFR` per standard thresholds
- `summary` — up to three cloud layers in METAR short form (`FEW060 BKN080`)
- `raw` — the original METAR line for debugging

Default station is `KLBB` (Lubbock Preston Smith, TX). Change
`METAR_STATION` in `server/.env` to any ICAO identifier.

## Security notes

- `BADGE_TOKEN` is a shared secret between the workstation aggregator and
  the badge. Generate a long random value (`openssl rand -hex 32`) the
  first time you deploy; never commit the real value.
- The aggregator only listens on localhost + LAN (bind to `0.0.0.0` only
  if the device is on a separate subnet from the workstation). Put it on
  a trusted VLAN; do not expose port 8088 to the internet without fronting
  it with TLS + a reverse proxy.
- Zoho / Google OAuth refresh tokens, when configured, are held in
  `server/.env` only — the badge never sees them.

## License

MIT — see `LICENSE`.

## Acknowledgements

Built on the [Pimoroni Badger 2040 W](https://shop.pimoroni.com/products/badger-2040-w) MicroPython firmware and Pimoroni's `picographics` / `badger2040` libraries.
