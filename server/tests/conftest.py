import os

import pytest

# Defaults so that `import server.app` (which calls build_app() → Settings())
# succeeds at pytest collection time. Real test values are injected per-test
# via monkeypatch and take precedence.
_COLLECTION_DEFAULTS = {
    "BADGE_TOKEN": "collection-time-placeholder",
    "WEATHER_LATITUDE": "0",
    "WEATHER_LONGITUDE": "0",
    "GOOGLE_SERVICE_ACCOUNT_JSON": "/tmp/sa.json",
    "GOOGLE_CALENDAR_ID": "x@example.com",
    "ZOHODESK_CLIENT_ID": "x",
    "ZOHODESK_CLIENT_SECRET": "x",
    "ZOHODESK_REFRESH_TOKEN": "x",
    "ZOHODESK_ORG_ID": "0",
    "ZOHOCRM_CLIENT_ID": "x",
    "ZOHOCRM_CLIENT_SECRET": "x",
    "ZOHOCRM_REFRESH_TOKEN": "x",
    "ZOHOCRM_USER_ID": "0",
}
for _k, _v in _COLLECTION_DEFAULTS.items():
    os.environ.setdefault(_k, _v)


@pytest.fixture
def fixtures_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures"
