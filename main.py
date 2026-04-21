try:
    import badger2040
except ImportError:
    badger2040 = None

from modes.badge import BadgeMode
from modes.desk import DeskMode
from badge_state import load as load_state


def _build_display():
    return badger2040.Badger2040()


def _load_config():
    import config
    return config


def run(state_path="/state.json"):
    state = load_state(state_path)
    mode = state.get("mode", "badge")
    display = _build_display()
    config = _load_config()

    if mode == "desk":
        DeskMode(display, config, state_path=state_path).cycle()
    else:
        BadgeMode(display, config).render_current()


if __name__ == "__main__":
    run()
