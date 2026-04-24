WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128

_WRAP_CHARS = 24
_LINE_H = 18


def _clear_white(display):
    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)


def _wrap(text, max_chars):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur = cur + " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(display, raw_text):
    _clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("Raw METAR", 8, 4, scale=2)
    display.text("B back", WIDTH - 60, 8, scale=1)
    display.line(0, 24, WIDTH, 24)

    if not raw_text:
        display.text("no data", 8, 40, scale=2)
        display.update()
        return

    lines = _wrap(raw_text, _WRAP_CHARS)
    y = 30
    for line in lines[:5]:
        display.text(line, 8, y, scale=2)
        y += _LINE_H

    if len(lines) > 5:
        display.text("(+{0} more)".format(len(lines) - 5), WIDTH - 80, HEIGHT - 10, scale=1)

    display.update()
