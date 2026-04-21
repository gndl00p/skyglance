import time

try:
    import network
    import urequests
except ImportError:
    network = None
    urequests = None

_WIFI_TIMEOUT_S = 15.0


def _make_wlan():
    w = network.WLAN(network.STA_IF)
    return w


def _http_get(url, headers):
    return urequests.get(url, headers=headers, timeout=3)


def _connect_wifi(cfg):
    w = _make_wlan()
    w.active(True)
    if not w.isconnected():
        w.connect(cfg.WIFI_SSID, cfg.WIFI_PSK)
    deadline = time.time() + _WIFI_TIMEOUT_S
    while not w.isconnected():
        if time.time() > deadline:
            return False
        time.sleep(0.25)
    return True


def fetch(cfg, last_data):
    if not _connect_wifi(cfg):
        return last_data, "offline"

    try:
        r = _http_get(cfg.AGGREGATOR_URL, headers={"X-Badge-Token": cfg.AGGREGATOR_TOKEN})
        if r.status_code != 200:
            return last_data, "offline"
        try:
            return r.json(), None
        except (ValueError, Exception):
            return last_data, "bad payload"
    except Exception:
        return last_data, "offline"
