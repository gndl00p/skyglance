try:
    import badger2040
except ImportError:
    badger2040 = None

import time

from fetcher import fetch
from render import render
from store import load as load_state
from store import save as save_state


_POLL_INTERVAL = 0.05


def _pressed_a(display):
    if badger2040 is None:
        return False
    btn = getattr(badger2040, "BUTTON_A", None)
    if btn is None:
        return False
    return display.pressed(btn)


def _wait_release_a(display):
    if badger2040 is None:
        return
    btn = getattr(badger2040, "BUTTON_A", None)
    if btn is None:
        return
    while display.pressed(btn):
        time.sleep(_POLL_INTERVAL)


def _build_display():
    return badger2040.Badger2040()


def _load_config():
    import config
    return config


def _cycle(display, cfg, state_path):
    state = load_state(state_path)
    last = state.get("last_data")
    data, marker = fetch(cfg, last)
    render(display, data if data is not None else last, marker)
    if data is not None and marker is None:
        save_state(state_path, {"last_data": data})


def run(state_path="/state.json"):
    display = _build_display()
    cfg = _load_config()

    _cycle(display, cfg, state_path)

    refresh_s = getattr(cfg, "REFRESH_MINUTES", 15) * 60
    last_tick = time.time()
    while True:
        if _pressed_a(display):
            _cycle(display, cfg, state_path)
            last_tick = time.time()
            _wait_release_a(display)
            continue
        if time.time() - last_tick >= refresh_s:
            _cycle(display, cfg, state_path)
            last_tick = time.time()
        time.sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    run()
