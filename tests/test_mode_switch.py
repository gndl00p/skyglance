from tests.fakes.display import FakeDisplay

import mode_switch


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_long_press_detected_after_threshold():
    clock = Clock()
    d = FakeDisplay()
    d.press("B")
    detector = mode_switch.LongPressDetector(d, button="B", threshold_s=2.0, now=clock)

    clock.t = 0.0
    assert detector.poll() is False
    clock.t = 1.5
    assert detector.poll() is False
    clock.t = 2.5
    assert detector.poll() is True


def test_short_press_does_not_trigger():
    clock = Clock()
    d = FakeDisplay()
    detector = mode_switch.LongPressDetector(d, button="B", threshold_s=2.0, now=clock)

    d.press("B")
    clock.t = 0.5
    assert detector.poll() is False
    d.release("B")
    clock.t = 0.6
    assert detector.poll() is False


def test_detector_only_fires_once_per_press():
    clock = Clock()
    d = FakeDisplay()
    d.press("B")
    detector = mode_switch.LongPressDetector(d, button="B", threshold_s=2.0, now=clock)

    # First poll records the press start at t=0; threshold hasn't elapsed yet.
    clock.t = 0.0
    assert detector.poll() is False
    clock.t = 2.5
    assert detector.poll() is True
    clock.t = 3.0
    assert detector.poll() is False


def test_transition_flips_mode_and_persists(tmp_path):
    p = tmp_path / "state.json"
    p.write_text('{"mode": "badge", "last_data": null}')
    new = mode_switch.transition(str(p))
    assert new == "desk"
    import json
    assert json.loads(p.read_text())["mode"] == "desk"

    new = mode_switch.transition(str(p))
    assert new == "badge"


def test_transition_preserves_last_data(tmp_path):
    import json

    p = tmp_path / "state.json"
    p.write_text(json.dumps({"mode": "desk", "last_data": {"x": 1}}))
    mode_switch.transition(str(p))
    assert json.loads(p.read_text())["last_data"] == {"x": 1}
