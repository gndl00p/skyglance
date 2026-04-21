import time

from state import load, save


class LongPressDetector:
    def __init__(self, display, button, threshold_s=2.0, now=time.time):
        self.display = display
        self.button = button
        self.threshold = threshold_s
        self._now = now
        self._press_start = None
        self._fired = False

    def poll(self):
        pressed = self.display.pressed(self.button)
        t = self._now()
        if pressed:
            if self._press_start is None:
                self._press_start = t
                self._fired = False
            elif not self._fired and (t - self._press_start) >= self.threshold:
                self._fired = True
                return True
        else:
            self._press_start = None
            self._fired = False
        return False


def transition(state_path):
    state = load(state_path)
    current = state.get("mode", "badge")
    new = "desk" if current == "badge" else "badge"
    state["mode"] = new
    save(state_path, state)
    return new
