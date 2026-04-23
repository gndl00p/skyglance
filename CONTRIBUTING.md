# Contributing

Thanks for considering a contribution — keep it small and testable.

## Before you submit a pull request

1. Both suites pass:
   ```bash
   .venv/bin/pytest tests -v
   server/.venv/bin/pytest server/tests -v
   ```
2. No new file imports real hardware (`badger2040`, `machine`, `network`) outside a `try / except ImportError` guard — the test suite must stay runnable on CPython with no device attached.
3. If you touched the METAR parser, include a new fixture under `server/tests/fixtures/` covering the edge case.
4. Commit messages follow the existing conventional format (`feat(scope): …`, `fix(server): …`, etc.).

## Adding a screen

See the [Development section](./README.md#development) of the root README.

## Adding an aggregator upstream

See the [Development section](./README.md#development) of the root README.
Test pattern: happy path, cached-within-ttl, stale-fallback-on-error, default-when-never-succeeded.

## Reporting issues

Please include:
- Pimoroni MicroPython build string (`mpremote connect /dev/ttyACM0 exec 'import sys; print(sys.implementation)'`).
- The aggregator response that's being fed to the badge (`curl -H "X-Badge-Token: <token>" http://<host>:8088/badge.json`).
- A photo of the e-ink display if the bug is visual.

## Code style

- Python 3.11+ type hints where they aid clarity.
- Keep the device codebase dependency-free beyond what Pimoroni ships.
- Tests use `pytest`, `respx` (HTTP), `unittest.mock` (sync libs), `freezegun` where time matters.
