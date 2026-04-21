try:
    import qrcode
except ImportError:
    qrcode = None


WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128


def clear_white(display):
    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)


def draw_header_rule(display, y=20):
    display.line(0, y, WIDTH, y)


def draw_qr(display, text, x, y, size_px):
    if qrcode is None:
        return
    code = qrcode.QRCode()
    code.set_text(text)
    w, h = code.get_size()
    cell = max(1, size_px // max(w, h))
    for cy in range(h):
        for cx in range(w):
            if code.get_module(cx, cy):
                display.rectangle(x + cx * cell, y + cy * cell, cell, cell)


def wrap(text, max_chars):
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