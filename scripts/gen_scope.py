"""Generate the XY oscilloscope hero SVG (stdlib only)."""
import math
import random
from pathlib import Path

N = 600
DUR = 20.0
CX, CY = 420, 198
R = 110
VICENZA = (45.5455, 11.5354)  # (lat, lon) degrees
OUT = Path(__file__).resolve().parent.parent / "assets" / "scope.svg"
TITLE = "Oscilloscope that pulls a signal out of noise, maps the globe to Vicenza, and writes the name JACOPO"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SPLINES = {
    "hold": "0 0 1 1",
    "linear": "0 0 1 1",
    "ease": ".45 0 .55 1",
    "in": ".42 0 1 1",
    "out": "0 0 .58 1",
}
# (target frame, seconds, spline kind); the first value is NOISE_A
STEPS = [
    ("NOISE_A", 0.3, "hold"), ("NOISE_B", 0.4, "linear"), ("NOISE_A", 0.4, "linear"),
    ("NOISE_B", 0.4, "linear"), ("SINE", 1.5, "ease"), ("SINE", 1.0, "hold"),
    ("CIRCLE", 1.5, "ease"), ("CIRCLE", 0.5, "hold"), ("GLOBE_90", 1.2, "in"),
    ("GLOBE_60", 0.9, "linear"), ("GLOBE_30", 0.9, "linear"), ("GLOBE_0", 1.0, "out"),
    ("GLOBE_0", 2.0, "hold"), ("NAME", 2.0, "ease"), ("NAME", 5.0, "hold"),
    ("NOISE_A", 1.0, "ease"),
]
STATUS = [
    ("SEARCHING ...", [(0, 1.5), (19, 20)]),
    ("SIGNAL ACQUIRED", [(1.5, 4.0)]),
    ("XY MODE", [(4.0, 6.0)]),
    ("MAPPING", [(6.0, 10.0)]),
    ("TARGET LOCKED", [(10.0, 12.0)]),
    ("SIGNAL: JACOPO VENDRAMIN", [(12.0, 19.0)]),
]
VALUES = [
    ("-- -- --", [(0, 1.5), (19, 20)]),
    ("F 50.00 HZ", [(1.5, 4.0)]),
    ("PHASE 90.0 DEG", [(4.0, 6.0)]),
    ("LON 11.5354 E", [(6.0, 10.0)]),
    ("45.5455 N  11.5354 E", [(10.0, 12.0)]),
    ("FULL STACK // EKAR", [(12.0, 19.0)]),
]


def arc(cx, cy, rx, ry, start_deg, end_deg, n):
    angles = [math.radians(start_deg + (end_deg - start_deg) * i / (n - 1)) for i in range(n)]
    return [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in angles]


# Every glyph starts and ends on the baseline (y=0), so the beam's retrace between
# letters runs along a flat zero line instead of cutting through the letters.
# Strokes that double back over themselves are invisible overdraw.
_C_TOP = arc(0.5, 0.5, 0.5, 0.5, 270, 45, 20)
GLYPHS = {
    "J": arc(0.5, 0.3, 0.5, 0.3, 180, 360, 12) + [(1, 1), (1, 0)],
    "A": [(0, 0), (0.25, 0.5), (0.75, 0.5), (0.25, 0.5), (0.5, 1), (1, 0)],
    "C": _C_TOP + _C_TOP[::-1] + arc(0.5, 0.5, 0.5, 0.5, 270, 315, 5) + [(0.85, 0)],
    "O": arc(0.5, 0.5, 0.5, 0.5, -90, 270, 32),
    "P": [(0, 0), (0, 1), (0.55, 1)] + arc(0.55, 0.75, 0.45, 0.25, 90, -90, 12) + [(0, 0.5), (0, 0)],
}
LEAD = 0.6  # flat trace entering and leaving the word


def word_polyline(word, width=0.75, gap=0.33):
    pts = [(-LEAD, 0)]
    for i, ch in enumerate(word):
        off = i * (width + gap)
        pts += [(off + x * width, y) for x, y in GLYPHS[ch]]
    return pts + [(pts[-1][0] + LEAD, 0)]


def resample(pts, n):
    seg = [math.dist(p, q) for p, q in zip(pts, pts[1:])]
    total = sum(seg)
    out, k, acc = [], 0, 0.0
    for i in range(n):
        d = total * i / (n - 1)
        while k < len(seg) - 1 and acc + seg[k] < d:
            acc += seg[k]
            k += 1
        f = 0.0 if seg[k] == 0 else min(1.0, (d - acc) / seg[k])
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        out.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
    return out


def name_frame(word="JACOPO", box_w=700, box_h=100):
    pts = resample(word_polyline(word), N)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    s = min(box_w / w, box_h / h)
    mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return [(CX + (x - mx) * s, CY - (y - my) * s) for x, y in pts]


def noise_frame(seed):
    rng = random.Random(seed)
    pts = []
    for i in range(N):
        y = CY + max(-18, min(18, rng.gauss(0, 5)))
        if rng.random() < 0.015:
            y += rng.choice((-1, 1)) * rng.uniform(20, 40)
        pts.append((60 + 720 * i / (N - 1), y))
    return pts


def sine_frame():
    return [(60 + 720 * i / (N - 1), CY - 70 * math.sin(2 * math.pi * 3 * i / (N - 1))) for i in range(N)]


def circle_frame():
    angles = [2 * math.pi * i / N for i in range(N)]
    return [(CX + 110 * math.cos(a), CY - 110 * math.sin(a)) for a in angles]


def project(lat, lon, k):
    phi, lam = math.radians(lat), math.radians(lon - (VICENZA[1] + k))
    phi0 = math.radians(VICENZA[0])
    x, y, z = math.cos(phi) * math.sin(lam), math.sin(phi), math.cos(phi) * math.cos(lam)
    y2 = y * math.cos(phi0) - z * math.sin(phi0)
    z2 = y * math.sin(phi0) + z * math.cos(phi0)
    h = math.hypot(x, y2)
    if z2 < 0 and h > 0:
        x, y2 = x / h, y2 / h
    return CX + R * x, CY - R * y2


def sweep(lat0, lon0, lat1, lon1, n):
    return [(lat0 + (lat1 - lat0) * i / (n - 1), lon0 + (lon1 - lon0) * i / (n - 1)) for i in range(n)]


def meridian_circle(lon):
    return sweep(90, lon, -90, lon, 37) + sweep(-90, lon + 180, 90, lon + 180, 37)[1:]


def globe_sphere_path():
    pts = [(90, 0)]
    for lon in (0, 30, 60, 90, 120, 150):
        pts += meridian_circle(lon)[1:]
    prev = 90
    for lat in (60, 30, 0, -30, -60):
        pts += sweep(prev, 0, lat, 0, 13)[1:]
        pts += sweep(lat, 0, lat, 360, 73)[1:]
        prev = lat
    return pts + sweep(prev, 0, -90, 0, 13)[1:]


def globe_frame(k):
    return resample([project(lat, lon, k) for lat, lon in globe_sphere_path()], N)


def path_d(pts):
    return "M " + " ".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def frames():
    return {
        "NOISE_A": noise_frame(7), "NOISE_B": noise_frame(8), "SINE": sine_frame(),
        "CIRCLE": circle_frame(), "NAME": name_frame(),
        **{f"GLOBE_{k}": globe_frame(k) for k in (90, 60, 30, 0)},
    }


def timeline():
    """Return (frame names per value, keyTimes, keySplines)."""
    names, kt, splines, t = ["NOISE_A"], [0.0], [], 0.0
    for name, d, kind in STEPS:
        t += d
        names.append(name)
        kt.append(t / DUR)
        splines.append(SPLINES[kind])
    assert abs(t - DUR) < 1e-9, "durations must sum to DUR"
    return names, kt, splines


def fmt_kt(kt):
    return ";".join(f"{k:.5f}".rstrip("0").rstrip(".") or "0" for k in kt)


def window_anim(windows):
    """Discrete opacity animate for visibility windows given in seconds."""
    ws = sorted(windows)
    events = [(0.0, 1 if ws[0][0] == 0 else 0)]
    for s, e in ws:
        if s > 0:
            events.append((s, 1))
        if e < DUR:
            events.append((e, 0))
    vals = ";".join(str(v) for _, v in events)
    return (f'<animate attributeName="opacity" calcMode="discrete" values="{vals}" '
            f'keyTimes="{fmt_kt([t / DUR for t, _ in events])}" dur="{DUR:g}s" repeatCount="indefinite"/>')


def readout(x, y, items, anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    out = []
    for text, ws in items:
        base = 1 if ws[0][0] == 0 else 0
        out.append(f'<text x="{x}" y="{y}"{a} xml:space="preserve" opacity="{base}">{text}{window_anim(ws)}</text>')
    return "\n".join(out)


def graticule():
    sx, sy, sw, sh = 40, 48, 760, 300
    v = [f"M {sx + i * 76} {sy} V {sy + sh}" for i in range(1, 10)]
    h = [f"M {sx} {sy + i * 37.5:g} H {sx + sw}" for i in range(1, 8)]
    grid = f'<path d="{" ".join(v + h)}" stroke="#0f2418" stroke-width="1" opacity=".6" fill="none"/>'
    ticks = [f"M {CX + i * 15.2:.1f} {CY - 3} v 6" for i in range(-24, 25) if i]
    ticks += [f"M {CX - 3} {CY + i * 7.5:g} h 6" for i in range(-19, 20) if i]
    axes = f"M {sx} {CY} H {sx + sw} M {CX} {sy} V {sy + sh} " + " ".join(ticks)
    return grid + f'\n<path d="{axes}" stroke="#163a26" stroke-width="1" fill="none"/>'


def label(x, y, text, anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return (f'<text x="{x}" y="{y}"{a} xml:space="preserve" font-family="{FONT}" font-size="10" '
            f'letter-spacing="2" fill="#2f4a3a">{text}</text>')


def marker():
    ln = 'stroke="#e6fff0" stroke-width="1.2"'
    cross = (f"M {CX} {CY - 9} V {CY - 16} M {CX} {CY + 9} V {CY + 16} "
             f"M {CX - 9} {CY} H {CX - 16} M {CX + 9} {CY} H {CX + 16}")
    return f'''<g opacity="0"><animate attributeName="opacity" calcMode="discrete" values="0;1;0" keyTimes="0;0.5;0.6" dur="20s" repeatCount="indefinite"/>
<circle cx="{CX}" cy="{CY}" r="5" {ln} fill="none"/>
<path d="{cross}" {ln} fill="none"/>
<circle cx="{CX}" cy="{CY}" r="6" stroke="#2df58a" stroke-width="1.2" fill="none" opacity="0.9"><animate attributeName="r" values="6;30" dur="1s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.9;0" dur="1s" repeatCount="indefinite"/></circle>
<text x="{CX + 22}" y="{CY - 14}" xml:space="preserve" font-family="{FONT}" font-size="10" letter-spacing="2" fill="#bfffd9">VICENZA</text>
</g>'''


def build_svg():
    fr = frames()
    names, kt, splines = timeline()
    values = ";".join(path_d(fr[n]) for n in names)

    def morph(begin=""):
        return (f'<animate attributeName="d" values="{values}" keyTimes="{fmt_kt(kt)}" calcMode="spline" '
                f'keySplines="{";".join(splines)}" dur="{DUR:g}s"{begin} repeatCount="indefinite"/>')

    d0 = path_d(fr["NOISE_A"])
    scr = 'x="40" y="48" width="760" height="300" rx="14"'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 420" width="100%" role="img" aria-label="{TITLE}">
<title>{TITLE}</title>
<style>@keyframes blink{{50%{{opacity:.15}}}}.led{{animation:blink 1.2s step-end infinite}}</style>
<defs>
<radialGradient id="crt" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#04140c"/><stop offset=".6" stop-color="#020a06"/><stop offset="1" stop-color="#000"/></radialGradient>
<radialGradient id="vig" cx="50%" cy="50%" r="70%"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".75"/></radialGradient>
<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="5"/></filter>
<filter id="glow2" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="1.5"/></filter>
<clipPath id="scr"><rect {scr}/></clipPath>
<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect y="2" width="4" height="1" fill="#000" opacity=".35"/></pattern>
<path id="beam" fill="none" pathLength="1000" d="{d0}">{morph()}</path>
</defs>
<rect width="840" height="420" rx="12" fill="#050505" stroke="#141414"/>
<rect {scr} fill="url(#crt)"/>
<g clip-path="url(#scr)">
{graticule()}
<path fill="none" d="{d0}" stroke="#2df58a" stroke-width="1.5" opacity=".22" filter="url(#glow2)">{morph(' begin="-0.14s"')}</path>
<use href="#beam" stroke="#12ff7a" stroke-width="8" opacity=".16" filter="url(#glow)"><animate attributeName="opacity" values=".16;.12;.17;.16" dur=".9s" repeatCount="indefinite"/></use>
<use href="#beam" stroke="#2df58a" stroke-width="1.5" opacity=".9" stroke-linejoin="round" stroke-linecap="round"/>
<use href="#beam" stroke="#e6fff0" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="18 982"><animate attributeName="stroke-dashoffset" values="1000;0" dur="1.1s" calcMode="linear" repeatCount="indefinite"/></use>
{marker()}
<rect {scr} fill="url(#scan)"/>
<rect {scr} fill="url(#vig)"/>
<rect {scr} fill="none" stroke="#12201a" stroke-width="1.5"/>
<g font-family="{FONT}" font-size="10" letter-spacing="2" fill="#2df58a" opacity=".75">
{readout(58, 70, STATUS)}
{readout(782, 70, VALUES, "end")}
</g>
</g>
{label(40, 32, "CH1 X  0.2V/div    CH2 Y  0.2V/div    XY")}
{label(782, 32, "TRIG LOCK", "end")}
<circle class="led" cx="792" cy="28.5" r="3.5" fill="#2df58a"/>
{label(40, 376, "JACOPO VENDRAMIN // FULL STACK ENGINEER @ EKAR")}
{label(800, 376, "VICENZA, IT", "end")}
</svg>
'''


def self_check(frs, kt, svg):
    for name, f in frs.items():
        assert len(f) == N, f"{name} point count"
        d = path_d(f)
        assert d.startswith("M "), f"{name} prefix"
        assert len(d[2:].split(" ")) == 2 * N, f"{name} number count"
    names, kt2, splines = timeline()
    assert kt[0] == 0 and kt[-1] == 1, "keyTimes ends"
    assert all(a < b for a, b in zip(kt, kt[1:])), "keyTimes increasing"
    assert len(kt) == len(names) and len(splines) == len(names) - 1, "values/keyTimes/splines count"
    x, y = project(*VICENZA, 0)
    assert abs(x - CX) < 1e-6 and abs(y - CY) < 1e-6, "Vicenza projection"
    assert svg.isascii(), "ascii only"
    size = len(svg.encode())
    assert size < 280000, f"size {size}"
    print(f"self_check ok: {len(frs)} frames x {N} pts, {len(kt)} keyTimes, {size} bytes")


def main():
    _, kt, _ = timeline()
    svg = build_svg()
    self_check(frames(), kt, svg)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
