"""Generate the railway-crossing-at-sunset hero SVG as a grid of shaded cells (stdlib only)."""
import math
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "crossing.svg"
TITLE = ("A railway crossing at sunset drawn in cells: the lights blink, the barrier drops, "
         "a commuter train rolls past under a towering cloud while sakura petals drift by; a hanko seal reads Jacopo in katakana")
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
JP_FONT = "'Hiragino Mincho ProN','Yu Mincho','Noto Serif JP','MS Mincho',serif"

W, H = 960, 384
CELL, GAP = 8, 1
SIDE = CELL - GAP
COLS, ROWS = W // CELL, H // CELL

BG = "#1b1b1a"
SKY = ["#241e2b", "#2e2333", "#3d2838", "#552e3a", "#753838", "#9a4630", "#c25e2e", "#e07f3c", "#f4a95e", "#ffd49a"]
SUN = ["#ffd49a", "#ffe6bd", "#fff3dc"]
CLOUD = ["#2a2431", "#3a3040", "#504051", "#6e525c", "#966563", "#c27f68", "#e6a073", "#f7c493"]
STEEL, DARK, WIRE = "#3a3a37", "#232322", "#151514"
STEEL_LIT = "#55504a"
TRAIN = {"roof": "#6b4140", "body": "#2c2b30", "under": "#1f1f22", "wheel": "#141414",
         "stripe": "#c95f26", "lit": "#f2c879", "warm": "#e3a65a", "unlit": "#3c3b40",
         "door": "#24232a", "head": "#fff1c8", "tail": "#d8352a"}
YELLOW, BLACK = "#e0b83c", "#45433d"
LAMP_OFF, LAMP_ON, LAMP_GLOW = "#4a1d19", "#ff4a2e", "#5c241c"
PETAL = ["#f4c4cf", "#e8a1b0", "#c97a8c"]
GRASS = ["#1e2620", "#26302a", "#33402f"]
RAIL_GLINT = ["#4a4744", "#7a6a5c", "#c99a6a", "#f2c48c"]
BALLAST, BALLAST_INK = "#2b2a28", "#3d3b38"
STAR = "#8c8794"
SEAL = "#b8541f"
TEXT, MUTED = "#d9d4cb", "#6f6b64"

SUN_C, SUN_R = (92, 30.5), 6.5
HORIZON = 34  # rail row; the embankment hides everything below it
CYCLE = 16.0  # seconds: lights, barrier down, train, barrier up, pause
LIGHTS_ON, BARRIER_DOWN, TRAIN_IN, TRAIN_OUT, BARRIER_UP = 1.0, 2.2, 3.2, 9.6, 11.0
BARRIER_SWING = 0.35  # seconds the arm spends at 45 degrees on each leg
BLINK = 0.5
TRAIN_TOP = 25
CROSS_C = 22  # column of the crossing post
EPIGRAPH_COLS = 40  # grass tufts stay clear of the epigraph below this column
GLYPH_W = 7.8  # advance of one 13px monospace glyph


def noise(c, r, seed):
    """Deterministic per-cell hash in [0, 1)."""
    n = (c * 374761393 + r * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) / 2**32


def cell(c, r, fill, glyph="", ink=None):
    x, y = c * CELL, r * CELL
    out = f'<rect x="{x}" y="{y}" width="{SIDE}" height="{SIDE}" rx="1" fill="{fill}"/>'
    if glyph:
        out += f'<text x="{x + SIDE / 2}" y="{y + SIDE - 1.5}" fill="{ink}" text-anchor="middle">{glyph}</text>'
    return out


def ramp(colors, v):
    return colors[max(0, min(len(colors) - 1, int(v * len(colors))))]


def fmt_times(times):
    """keyTimes attribute value for event times given in seconds."""
    return ";".join(f"{t / CYCLE:.4f}" for t in times)


def windows_anim(windows):
    """Discrete opacity animation: visible inside the (start, end) windows, hidden elsewhere."""
    if not windows:
        raise ValueError("windows_anim needs at least one (start, end) window")
    events = [(0.0, 0)]
    for s, e in sorted(windows):
        events += [(s, 1), (e, 0)]
    events = [ev for ev in events if ev[0] < CYCLE]
    if events[1][0] == 0.0:
        events = events[1:]
    vals = ";".join(str(v) for _, v in events)
    times = fmt_times(t for t, _ in events)
    return (f'<animate attributeName="opacity" calcMode="discrete" values="{vals}" keyTimes="{times}" '
            f'dur="{CYCLE:g}s" repeatCount="indefinite"/>')


def translate_anim(points, dur, key_times=None, begin=None):
    """Discrete translate animation over "x,y" points; dur and begin are preformatted strings."""
    key = f' keyTimes="{key_times}"' if key_times else ""
    start = f' begin="{begin}"' if begin else ""
    return (f'<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
            f'values="{";".join(points)}"{key} dur="{dur}"{start} repeatCount="indefinite"/>')


# --- sky ----------------------------------------------------------------------


def sky_glow(c, r):
    horizon = (r / HORIZON) ** 2.2 * (0.5 + 0.5 * math.exp(-abs(c - SUN_C[0]) / 45))
    sun = 1.15 * math.exp(-math.dist((c, r * 1.4), (SUN_C[0], SUN_C[1] * 1.4)) / 16)
    return min(1.0, max(horizon, sun))


def sky_cells():
    out = []
    for r in range(HORIZON):
        for c in range(COLS):
            if math.dist((c, r), SUN_C) < SUN_R:
                continue
            g = sky_glow(c, r)
            if noise(c, r, 1) > g * 1.35:
                continue
            glyph = ".:"[int(noise(c, r, 2) * 2)] if noise(c, r, 3) < 0.25 else ""
            out.append(cell(c, r, ramp(SKY, g), glyph, ramp(SKY, g - 0.12)))
    return out


def sun_cells():
    out = []
    for r in range(HORIZON):
        for c in range(COLS):
            d = math.dist((c, r), SUN_C)
            if d < SUN_R:
                out.append(cell(c, r, ramp(SUN, 1 - d / SUN_R)))
    return out


def stars():
    out = []
    for i in range(46):
        c, r = int(noise(i, 0, 20) * COLS), int(noise(i, 1, 20) ** 1.6 * 14)
        if sky_glow(c, r) > 0.15:
            continue
        x, y = c * CELL + SIDE / 2, r * CELL + SIDE - 1
        ch = "+" if noise(i, 2, 20) < 0.2 else "."
        twinkle = ""
        if noise(i, 3, 20) < 0.4:
            dur = 2 + noise(i, 4, 20) * 3
            twinkle = (f'<animate attributeName="opacity" values="1;.2;1" dur="{dur:.2f}s" '
                       f'begin="{noise(i, 5, 20) * dur:.2f}s" repeatCount="indefinite"/>')
        out.append(f'<text x="{x}" y="{y}" fill="{STAR}" text-anchor="middle" font-size="9">{ch}{twinkle}</text>')
    return out


# --- cumulonimbus -------------------------------------------------------------

# Overlapping puffs (col, row, radius); the base is flattened like a real cumulus.
PUFFS = [(36, 19, 5), (42, 15.5, 7), (50, 12, 8), (58, 9.5, 8.5), (66, 11.5, 7.5), (73, 14.5, 6.5),
         (79, 18, 5), (47, 18.5, 6.5), (61, 17, 7.5), (71, 19.5, 5), (54, 4.5, 5.5)]
CLOUD_BASE = 23.5


def cloud_cells():
    out = []
    lx, ly, lz = 0.78, 0.32, 0.53
    for r in range(HORIZON):
        for c in range(COLS):
            x, y = c + 0.5, r + 0.5
            if y > CLOUD_BASE:
                continue
            best = None
            for col, row, radius in PUFFS:
                d2 = (x - col) ** 2 + (y - row) ** 2
                if d2 < radius * radius:
                    h = math.sqrt(radius * radius - d2)
                    if best is None or h + row * 0.02 > best[0]:
                        best = (h, (x - col) / radius, (y - row) / radius, h / radius)
            if best is None:
                continue
            _, nx, ny, nz = best
            edge = 1 - nz
            if edge > 0.75 and noise(c, r, 7) < 0.5:
                continue  # wispy rim
            diffuse = max(0.0, nx * lx + ny * ly + nz * lz)
            base_shadow = max(0.0, (y - (CLOUD_BASE - 4)) / 4) * 0.35
            tone = 0.08 + 0.92 * diffuse ** 1.4 - base_shadow + (noise(c, r, 8) - 0.5) * 0.12
            glyph = ".:"[int(noise(c, r, 9) * 2)] if noise(c, r, 10) < 0.3 else ""
            out.append(cell(c, r, ramp(CLOUD, tone), glyph, ramp(CLOUD, tone - 0.15)))
    return out


# --- poles and wires ----------------------------------------------------------

POLES = [8, 108]
ARM_ROW, ARM_HALF = 9, 4  # crossarm row and half width


def poles():
    out = []
    for pc in POLES:
        for r in range(7, HORIZON + 1):
            out.append(cell(pc, r, DARK))
        for dc in range(-ARM_HALF, ARM_HALF + 1):
            out.append(cell(pc + dc, ARM_ROW, DARK))
        out.append(cell(pc + 1, 15, DARK) + cell(pc + 2, 15, DARK) + cell(pc + 1, 16, DARK))  # transformer
    return out


def wires():
    out = []
    spans = [(-30, POLES[0]), (POLES[0], POLES[1]), (POLES[1], COLS + 30)]
    for dc in (-ARM_HALF, ARM_HALF):
        for a, b in spans:
            sag = 0.045 * (b - a)
            seen = set()
            for i in range(int((b - a) * 3) + 1):
                x = a + (b - a) * i / ((b - a) * 3)
                t = (x - a) / (b - a)
                y = ARM_ROW + sag * 4 * t * (1 - t)
                c, r = int(x + dc + 0.5), int(y + 0.5)
                if 0 <= c < COLS and (c, r) not in seen:
                    seen.add((c, r))
                    out.append(cell(c, r, WIRE))
    return out


# --- train --------------------------------------------------------------------

CAR_W, CARS = 20, 4
TRAIN_LEN = CARS * (CAR_W + 1)
DOOR_COLS = (7, 8, 13, 14)


def car_fill(k, dc, dr, c):
    """Fill of cell (dc, dr) in car k, or None when the cell is empty."""
    if k == CARS - 1 and dc >= CAR_W - 2 and dr <= 1:
        return None  # notched nose on the leading car
    if dr == 0:
        return TRAIN["roof"]
    if dr in (2, 3) and 1 <= dc <= CAR_W - 2:
        if dc in DOOR_COLS:
            return TRAIN["door"]
        if dc % 3 == 0:
            return TRAIN["body"]
        if noise(c, dr, 30) >= 0.82:
            return TRAIN["unlit"]
        return TRAIN["lit"] if noise(c, dr, 31) < 0.6 else TRAIN["warm"]
    if dr == 5:
        return TRAIN["stripe"]
    if dr == 7:
        return TRAIN["under"]
    if dr == 8:
        return TRAIN["wheel"] if dc in (2, 4, CAR_W - 5, CAR_W - 3) else None
    if dc in DOOR_COLS and dr in (1, 4, 6):
        return TRAIN["door"]
    return TRAIN["body"]


def train_cells():
    """Cells relative to the train's left edge, leading car on the right."""
    out = []
    for k in range(CARS):
        x0 = k * (CAR_W + 1)
        lead, tail = k == CARS - 1, k == 0
        for dc in range(CAR_W):
            for dr in range(9):
                fill = car_fill(k, dc, dr, x0 + dc)
                if fill:
                    out.append(cell(x0 + dc, TRAIN_TOP + dr, fill))
        if lead:
            out.append(cell(x0 + CAR_W - 1, TRAIN_TOP + 6, TRAIN["head"]))
            out.append(cell(x0 + CAR_W - 1, TRAIN_TOP + 3, TRAIN["lit"]))
        if tail:
            out.append(cell(x0, TRAIN_TOP + 6, TRAIN["tail"]))
        if k in (1, 3):
            for dc, dr in ((8, -1), (10, -1), (9, -2), (7, -3), (8, -3), (9, -3), (10, -3), (11, -3)):
                out.append(cell(x0 + dc, TRAIN_TOP + dr, DARK))
        if k < CARS - 1:
            out.append(cell(x0 + CAR_W, TRAIN_TOP + 6, TRAIN["under"]))
    return out


def train():
    start, end = -TRAIN_LEN - 2, COLS + 2
    steps = end - start
    pts = [f"{(start + i) * CELL},0" for i in range(steps + 1)]
    times = [TRAIN_IN + (TRAIN_OUT - TRAIN_IN) * i / steps for i in range(steps + 1)]
    # Hidden off-frame on the left before it arrives and on the right after it leaves.
    anim = translate_anim([pts[0]] + pts + [pts[-1]], f"{CYCLE:g}s", fmt_times([0.0] + times + [CYCLE]))
    return f'<g transform="translate({pts[0]})">{anim}{"".join(train_cells())}</g>'


# --- crossing -----------------------------------------------------------------


def crossing():
    """Foreground crossing: striped crossbuck, twin blinking lamps, barrier arm in three poses."""
    out = []
    for r in range(11, HORIZON + 3):
        out.append(cell(CROSS_C, r, STEEL) + cell(CROSS_C + 1, r, STEEL_LIT))  # right side catches the sun
    for i in range(-5, 6):
        color = YELLOW if (i + 5) % 2 == 0 else BLACK
        out.append(cell(CROSS_C + i, 6 + i, color) + cell(CROSS_C + 1 + i, 6 + i, color))
        out.append(cell(CROSS_C + i, 6 - i, color) + cell(CROSS_C + 1 + i, 6 - i, color))
    for dc in range(-5, 7):
        out.append(cell(CROSS_C + dc, 15, STEEL))
    slots = int((BARRIER_UP - LIGHTS_ON) / BLINK)
    for idx, dc0 in enumerate((-5, 5)):
        off = "".join(cell(CROSS_C + dc0 + dx, 16 + dy, LAMP_OFF) for dx in (0, 1) for dy in (0, 1))
        glow = "".join(
            cell(CROSS_C + dc0 + dx, 16 + dy, LAMP_GLOW)
            for dx in range(-1, 3) for dy in range(0, 3)
            if not (0 <= dx <= 1 and 0 <= dy <= 1)
        )
        lit = glow + "".join(cell(CROSS_C + dc0 + dx, 16 + dy, LAMP_ON) for dx in (0, 1) for dy in (0, 1))
        windows = [(LIGHTS_ON + s * BLINK, LIGHTS_ON + (s + 1) * BLINK) for s in range(slots) if s % 2 == idx]
        out.append(off)
        out.append(f'<g opacity="0">{lit}{windows_anim(windows)}</g>')
    px, py = CROSS_C + 3, 32
    for dc in (0, 1):
        for dr in (-1, 0, 1):
            out.append(cell(px + dc, py + dr, STEEL))
    down = "".join(cell(c, py, YELLOW if ((c - px) // 2) % 2 else BLACK) for c in range(px + 2, px + 30))
    up = "".join(cell(px, r, YELLOW if ((py - r) // 2) % 2 else BLACK) for r in range(py - 21, py - 1))
    mid = "".join(cell(px + 1 + i, py - 1 - i, YELLOW if ((i + 1) // 2) % 2 else BLACK) for i in range(1, 21))
    swing_in = (BARRIER_DOWN - BARRIER_SWING, BARRIER_DOWN)
    swing_out = (BARRIER_UP, BARRIER_UP + BARRIER_SWING)
    out.append(f'<g opacity="0">{down}{windows_anim([(BARRIER_DOWN, BARRIER_UP)])}</g>')
    out.append(f'<g opacity="0">{mid}{windows_anim([swing_in, swing_out])}</g>')
    out.append(f'<g>{up}{windows_anim([(0, swing_in[0]), (swing_out[1], CYCLE)])}</g>')
    return out


# --- ground -------------------------------------------------------------------


def ground():
    out = []
    for c in range(COLS):
        glint = math.exp(-abs(c - SUN_C[0]) / 12)
        out.append(cell(c, HORIZON, ramp(RAIL_GLINT, glint)))
        out.append(cell(c, HORIZON + 1, BALLAST, ":" if noise(c, 1, 40) < 0.4 else "", BALLAST_INK))
        if noise(c, 2, 40) < 0.85:
            out.append(cell(c, HORIZON + 2, GRASS[int(noise(c, 3, 40) * 3)]))
        tuft = int(noise(c, 4, 40) * 3)
        for dr in range(tuft):
            if c < EPIGRAPH_COLS and dr > 0:
                continue
            out.append(cell(c, HORIZON + 3 + dr, GRASS[0]))
    return out


# --- petals -------------------------------------------------------------------


def petal(i):
    rng = [noise(i, k, 60) for k in range(8)]
    x0, y0 = -4 - rng[0] * 30, -2 + rng[1] * 22
    x1, y1 = COLS + 4, y0 + 14 + rng[2] * 18
    sway, dur = 1.5 + rng[3] * 3, 10 + rng[4] * 8
    steps = int(math.dist((x0, y0), (x1, y1)) * 1.3)
    pts = []
    for s in range(steps + 1):
        t = s / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sway * math.sin(t * math.tau * (1.5 + rng[5]))
        pts.append(f"{round(x) * CELL},{round(y) * CELL}")
    color = PETAL[int(rng[6] * 3)]
    wide = cell(0, 0, color) + cell(1, 0, PETAL[min(2, int(rng[6] * 3) + 1)])
    narrow = cell(0, 0, color)
    flip = 0.4 + rng[7] * 0.4
    anim = translate_anim(pts, f"{dur:.2f}s", begin=f"-{rng[0] * dur:.2f}s")
    return (
        f'<g transform="translate({pts[0]})">{anim}'
        f'<g>{wide}<animate attributeName="opacity" values="1;0" dur="{flip * 2:.2f}s" calcMode="discrete" repeatCount="indefinite"/></g>'
        f'<g opacity="0">{narrow}<animate attributeName="opacity" values="0;1" dur="{flip * 2:.2f}s" calcMode="discrete" repeatCount="indefinite"/></g>'
        "</g>"
    )


# --- text ---------------------------------------------------------------------


def overlay():
    x, y = 24, HORIZON * CELL + 52
    lines = ("every summer ends", "at a railway crossing")
    sw, sh = 24, 58
    sx, sy = W - 24 - sw, H - 16 - sh
    seal = "".join(
        f'<text x="{sx + sw / 2}" y="{sy + 19 + i * 16}" fill="{BG}" text-anchor="middle" '
        f'font-family="{JP_FONT}" font-size="13" font-weight="700">{ch}</text>'
        for i, ch in enumerate("ヤコポ")
    )
    return [
        f'<g font-size="11" fill="{MUTED}" text-anchor="end">'
        f'<text x="{W - 24}" y="24">45.5455 N</text>'
        f'<text x="{W - 24}" y="40">11.5354 E</text></g>',
        f'<g font-size="13" fill="{MUTED}">'
        f'<text x="{x}" y="{y}">{lines[0]}</text>'
        f'<text x="{x}" y="{y + 20}">{lines[1]}</text></g>',
        f'<rect x="{x + GLYPH_W * len(lines[1]) + 2}" y="{y + 9}" width="7.5" height="14" fill="{TEXT}">'
        '<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" repeatCount="indefinite"/></rect>',
        f'<g transform="rotate(-4 {sx + sw / 2} {sy + sh / 2})" opacity=".92">'
        f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="2.5" fill="{SEAL}"/>'
        f'<rect x="{sx + 2.5}" y="{sy + 2.5}" width="{sw - 5}" height="{sh - 5}" rx="1.5" fill="none" '
        f'stroke="{BG}" stroke-width="1"/>{seal}</g>',
    ]


def build():
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-labelledby="t" font-family="{FONT}" font-size="5.5">',
            f'<title id="t">{TITLE}</title>',
            f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
            *stars(),
            *sky_cells(),
            *sun_cells(),
            *cloud_cells(),
            *wires(),
            *poles(),
            train(),
            *crossing(),
            *ground(),
            *(petal(i) for i in range(14)),
            *overlay(),
            "</svg>",
        ]
    )


def self_check(svg):
    """Assert keyTimes are well formed against their values, then print a one-line summary."""
    pairs = re.findall(r'values="([^"]*)" keyTimes="([^"]*)"', svg)
    assert pairs, "no keyTimes found"
    for values, key_times in pairs:
        kt = [float(t) for t in key_times.split(";")]
        assert kt[0] == 0, "keyTimes must start at 0"
        assert all(a <= b for a, b in zip(kt, kt[1:])), "keyTimes must be non-decreasing"
        assert len(kt) == len(values.split(";")), "keyTimes/values count mismatch"
    train_kt = re.search(r'<animateTransform[^>]*keyTimes="([^"]*)"', svg)
    assert train_kt, "train animation missing"
    kt = [float(t) for t in train_kt.group(1).split(";")]
    assert all(a < b for a, b in zip(kt, kt[1:])), "train keyTimes must be strictly increasing"
    print(f"self_check ok: {len(pairs)} keyTimes animations, {len(svg.encode()) / 1024:.0f} KiB")


def main():
    svg = build()
    self_check(svg)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
