# Contributing to SkyGlance

Small, testable pull requests welcome.

## Before submitting

1. The host suite passes:
   ```bash
   .venv/bin/pytest tests -v
   ```
2. Any new module that imports a MicroPython-only library
   (`badger2040`, `network`, `requests`, `machine`) does so inside a
   `try / except ImportError` guard — the suite must stay runnable on
   CPython with no device attached.
3. Commit messages follow `type(scope): summary` (`feat(fetcher): …`,
   `fix(render): …`, `docs: …`).

## Reporting issues

Please include:

- Pimoroni MicroPython build string:
  ```
  mpremote connect /dev/ttyACM0 exec 'import sys; print(sys.implementation)'
  ```
- The ICAO station you configured and, ideally, the raw METAR:
  ```
  curl 'https://aviationweather.gov/api/data/metar?ids=<station>&format=raw'
  ```
- A photo of the e-ink display if the bug is visual.

## Code style

- Python 3.11+ on the host, MicroPython-compatible syntax on the
  device (dict-unpacking `{**x, ...}` spreads are not universally
  supported — use `dict(x); out[k]=v` instead).
- Keep the device codebase dependency-free beyond what Pimoroni ships.
- Tests use `pytest` + `unittest.mock` only. No `requests_mock` /
  `respx` — intercept `fetcher._http_get_metar` directly and have it
  return a `MagicMock` with the fields your test cares about.
