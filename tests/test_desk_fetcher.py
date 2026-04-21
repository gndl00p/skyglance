from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from desk import fetcher


def _cfg():
    return SimpleNamespace(
        WIFI_SSID="net", WIFI_PSK="pw",
        AGGREGATOR_URL="http://h/badge.json",
        AGGREGATOR_TOKEN="tok",
    )


def test_connects_and_fetches(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.side_effect = [False, True]
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    response = MagicMock(status_code=200)
    response.json.return_value = {"weather": {"temp_f": 70}}
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: response)

    data, marker = fetcher.fetch(_cfg(), last_data=None)

    wlan.active.assert_called_with(True)
    wlan.connect.assert_called_with("net", "pw")
    assert data == {"weather": {"temp_f": 70}}
    assert marker is None


def test_wifi_timeout_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = False
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    monkeypatch.setattr(fetcher, "_WIFI_TIMEOUT_S", 0.01)

    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "offline"


def test_http_error_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    def boom(url, headers):
        raise OSError("conn reset")

    monkeypatch.setattr(fetcher, "_http_get", boom)
    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "offline"


def test_non_200_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=500)
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: response)

    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "offline"


def test_bad_payload_returns_last_with_marker(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    response.json.side_effect = ValueError("bad json")
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: response)

    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "bad payload"


def test_stale_marker_when_no_previous_data(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: (_ for _ in ()).throw(OSError("x")))

    data, marker = fetcher.fetch(_cfg(), last_data=None)
    assert data is None
    assert marker == "offline"
