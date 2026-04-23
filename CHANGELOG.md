# Changelog

All notable changes are recorded here. Dates follow `YYYY-MM-DD`.

## [Unreleased]

### Added
- HH:MM last-updated clock (24-hour) rendered in the top-right of the desk display.
- Scheduled auto-refresh of the desk cycle every `REFRESH_MINUTES`, independent of the button poll.
- Wake-button dispatch + long-press B detection in `main.py`, so buttons can navigate screens and toggle modes after a halt.

### Changed
- Desk display is weather-first. Big-font temperature and flight category top, station + visibility + wind + cloud layers below. Non-weather tiles removed from the render (server still provides them for API compatibility).
- Weather upstream swapped from `open-meteo` (generic forecast) to `aviationweather.gov` (METAR). Flight category (`VFR` / `MVFR` / `IFR` / `LIFR`) computed from ceiling + visibility.
- `display.halt()` is no longer relied upon on USB power — firmware runs a polling idle loop instead.
- `flash.sh` leaves `/state.json` on the device alone after the first flash, so persisted mode + last fetched data survive subsequent firmware updates.
- `state.py` renamed to `badge_state.py` to dodge the factory Pimoroni filesystem's `state/` directory.
- Host stub renamed `badger2040w` → `badger2040` with class `Badger2040`, matching the current Pimoroni MicroPython build.

### Fixed
- Dither bit polarity — `picographics.image()` draws set bits in the current pen, so black pixels must map to `1`. Placeholder assets regenerated.
- Desk mode `test_desk_stale_fallback` and equivalent CRM test: token cache outlives the data cache, so the stale path must be triggered by the downstream endpoint failing, not the token refresh.

## [0.1.0] — 2026-04-20

### Added
- Initial design spec and per-subsystem implementation plans.
- Five badge-mode screens (name card, contact, bio, now, logo).
- Desk-mode 4-tile dashboard, mode-switch state, button handling.
- FastAPI aggregator with weather, Google Calendar, Zoho Desk, Zoho CRM upstreams; TTL caching and stale fallback.
- Host test suite for both firmware and aggregator (~84 tests at release).
- `tools/dither_image.py` host-side 1-bit packer for custom assets.
- `tools/flash.sh` mpremote-based deployment wrapper.
- `server/badger.service` user systemd unit.

[Unreleased]: https://github.com/gndl00p/badger/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gndl00p/badger/releases/tag/v0.1.0
