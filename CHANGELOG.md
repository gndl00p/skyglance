# Changelog

## [0.2.0] — 2026-04-23

Major pivot: SkyGlance is now a single-purpose aviation weather display.

### Removed
- **Badge mode**: all five name-card screens, mode-switch detector,
  placeholder-asset generator, dither tool, asset files. The device is
  no longer a dual-mode badge.
- **FastAPI aggregator**: `server/` directory removed in full. The
  device calls `aviationweather.gov` directly over HTTPS — no server,
  no API key, no shared secret.
- **Zoho Desk / Zoho CRM / Google Calendar upstreams**: no longer part
  of the project.
- `tools/dither_image.py`, `tools/make_placeholder_assets.py`, and
  `assets/*.bin`.

### Changed
- Project renamed **badger** → **SkyGlance**.
- Firmware tree flattened: no more `modes/`, `screens/`, `desk/`
  subdirectories — just `main.py`, `fetcher.py`, `render.py`,
  `store.py` at the repository root.
- `badge_state.py` renamed to `store.py`; state.json now stores just
  `{"last_data": {...}}` (no mode field).
- Weather payload is now a flat dict (no `payload.weather.*` nesting)
  since the aggregator envelope is gone.
- Observation time is rendered with a `Z` suffix to flag UTC.
- `tools/flash.sh` trimmed to four firmware files plus `config.py`.
- `config.example.py` reduced to four fields: `WIFI_SSID`, `WIFI_PSK`,
  `METAR_STATION`, `REFRESH_MINUTES`.
- `pyproject.toml` `name` bumped to `skyglance`, version `0.2.0`.

### Added
- `fetcher.py` now contains the full METAR parser (ported from the
  retired aggregator's `weather.py`).
- Host test suite trimmed to the four firmware modules; 24 tests cover
  fetcher / render / store / main.

### Fixed
- Swapped `{**dict, "stale": True}` spread (not supported by some
  MicroPython builds) for an explicit `_stale_copy` helper.

## [0.1.0] — 2026-04-20

Initial release under the `badger` name — dual-mode firmware (badge
+ desk), FastAPI aggregator, per-tile stale fallback, 84 tests.

[0.2.0]: https://github.com/gndl00p/skyglance/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/gndl00p/skyglance/releases/tag/v0.1.0
