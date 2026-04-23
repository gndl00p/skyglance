from desk.fetcher import fetch
from desk.render import render
from badge_state import load as load_state
from badge_state import save as save_state


class DeskMode:
    def __init__(self, display, config, state_path="/state.json"):
        self.display = display
        self.config = config
        self.state_path = state_path

    def cycle(self):
        state = load_state(self.state_path)
        last = state.get("last_data")
        data, marker = fetch(self.config, last)
        render(self.display, data if data is not None else last, marker)
        if data is not None and marker is None:
            save_state(self.state_path, {"mode": "desk", "last_data": data})

    def handle_button(self, btn):
        if btn == "A":
            self.cycle()
        elif btn == "UP":
            self.display.led(0)
        elif btn == "DOWN":
            self.display.halt()
