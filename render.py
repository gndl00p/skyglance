WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128

_CAT_CHAR_W = 30  # bitmap8 char at scale 5


def render(display, weather, stale_marker=None, invert=None):
    try:
        display.set_update_speed(0)
    except Exception:
        pass

    w = weather or {}
    if invert is None:
        invert = False
    bg = BLACK if invert else WHITE
    fg = WHITE if invert else BLACK

    display.set_pen(bg)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(fg)
    display.set_font("bitmap8")

    # ─── Header strip ────────────────────────────────────────
    station = w.get("station") or "----"
    name = w.get("station_name") or ""
    updated = w.get("updated_z")

    head = "{0} {1}".format(station, name).strip()
    display.text(head, 4, 2, scale=1)
    if updated is not None:
        right = "{0}Z".format(updated)
        display.text(right, WIDTH - len(right) * 6 - 4, 2, scale=1)
    display.line(0, 12, WIDTH, 12)

    # ─── Hero ────────────────────────────────────────────────
    temp = w.get("temp_f")
    cat = w.get("flight_category") or "--"
    temp_str = "{0}F".format(int(temp)) if temp is not None else "--F"
    display.text(temp_str, 12, 22, scale=5)

    cat_w = len(cat) * _CAT_CHAR_W
    cat_x = WIDTH - cat_w - 12
    if cat in ("IFR", "LIFR") and not invert:
        display.set_pen(fg)
        display.rectangle(cat_x - 8, 18, cat_w + 16, 50)
        display.set_pen(bg)
        display.text(cat, cat_x, 22, scale=5)
        display.set_pen(fg)
    else:
        display.text(cat, cat_x, 22, scale=5)

    display.line(0, 72, WIDTH, 72)

    # ─── Data grid (5 rows × 2 cols at scale 1) ──────────────
    wind = w.get("wind") or "--"
    vis = w.get("visibility_sm")
    da = w.get("density_altitude_ft")
    dewp = w.get("dewpoint_f")
    sky = w.get("summary") or "--"
    ceiling = w.get("ceiling_ft")
    sr = w.get("sunrise_local")
    ss = w.get("sunset_local")
    rwy_hdg = w.get("runway_heading_deg")
    hw = w.get("headwind_kt")
    xw = w.get("crosswind_kt")
    xw_side = w.get("crosswind_side") or ""

    L_X = 4
    R_X = WIDTH // 2 + 6
    Y0 = 78
    ROW = 10

    # Row 1: Wind | Vis
    display.text("WIND  {0}".format(wind), L_X, Y0, scale=1)
    if vis is not None:
        v = int(vis) if vis == int(vis) else vis
        display.text("VIS   {0} SM".format(v), R_X, Y0, scale=1)

    # Row 2: T/Td | DA
    if temp is not None and dewp is not None:
        display.text("T/Td  {0}/{1} F".format(int(temp), int(dewp)),
                     L_X, Y0 + ROW, scale=1)
    if da is not None:
        display.text("DA    {0} ft".format(da), R_X, Y0 + ROW, scale=1)

    # Row 3: Clouds | Ceiling
    display.text("CLD   {0}".format(sky), L_X, Y0 + 2 * ROW, scale=1)
    ceil_str = "{0} ft".format(ceiling) if ceiling is not None else "---"
    display.text("CEIL  {0}".format(ceil_str), R_X, Y0 + 2 * ROW, scale=1)

    # Row 4: RWY left, free right (or stale marker)
    if rwy_hdg is not None and hw is not None and xw is not None:
        rwy_num = int(round(rwy_hdg / 10.0)) % 36
        if rwy_num == 0:
            rwy_num = 36
        display.text("RWY{0:02d}  HW {1}  XW {2}{3}".format(
            rwy_num, hw, xw, xw_side), L_X, Y0 + 3 * ROW, scale=1)

    # Row 5: SR / SS right-aligned, stale marker left
    if sr is not None or ss is not None:
        parts = []
        if sr:
            parts.append("SR {0}".format(sr))
        if ss:
            parts.append("SS {0}".format(ss))
        line = "   ".join(parts)
        display.text(line, WIDTH - len(line) * 6 - 4, Y0 + 4 * ROW, scale=1)

    if stale_marker:
        display.text(stale_marker, L_X, Y0 + 4 * ROW, scale=1)

    display.update()
