import math
import re
import sys
import urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "yooshuu"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist")

CELL, GAP = 11, 3
PITCH = CELL + GAP
LEFT, TOP = 16, 22
WALK, CHARGE = 70.0, 220.0
SCALE = 0.9
RUNUP = 30
REGROW = 2.5

PALETTES = {
    "light": {"levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]},
    "dark": {"levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]},
}
COAT = {"body": "#ede3d3", "line": "#2e2925", "shade": "#c9baa3"}


def fetch_cells(user):
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                                 headers={"User-Agent": "grass-pets"})
    html = urllib.request.urlopen(req).read().decode("utf-8")
    cells = []
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        m = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', tag)
        lv = re.search(r'data-level="(\d)"', tag)
        if m and lv:
            cells.append((int(m.group(2)), int(m.group(1)), int(lv.group(1))))
    return cells


def center(col, row):
    return LEFT + col * PITCH + CELL / 2, TOP + row * PITCH + CELL / 2


def tour(cells):
    green = [c for c in cells if c[2] > 0]
    if not green:
        return []
    cur = min(green, key=lambda c: (c[0], c[1]))
    order, left = [cur], set(green) - {cur}
    while left:
        cx, cy = center(cur[0], cur[1])
        cur = min(left, key=lambda c: math.dist((cx, cy), center(c[0], c[1])))
        order.append(cur)
        left.remove(cur)
    return order


def pct(t, total):
    return f"{max(0.0, min(100.0, t / total * 100)):.3f}%"


PIVOT = (7, -15)

LEGS_FAR = ["M-7.4 -9 L-8.4 -4.6 L-7.6 -0.6", "M6 -9 L6.4 -4.4 L6.2 -0.6"]
LEGS_NEAR = ["M-9.6 -9.4 L-10.6 -4.8 L-9.6 -0.6", "M3.8 -9 L3.6 -4.4 L3.8 -0.6"]
TAIL = "M-11.6 -14.6 q-1.6 -1.8 -1 -4.6 q1.4 1.6 1.9 3.8"
BODY = "M-11 -15 C-6 -17 2 -17 7 -15.5 C10 -14.5 10 -10 8 -8.5 C3 -7.2 -5 -7.2 -9 -8.5 C-12.5 -9.5 -13 -13 -11 -15 Z"
NECK = "M5 -15 C6 -18 8 -20 10 -21 L12.5 -19 C11 -17 10 -14 9 -12.5 Z"
EAR = "M10.5 -21 q-3 0.5 -4.2 -1.1 q2.2 -1.2 4.6 0"
HEAD = ("M9.5 -21.5 C11 -23 13.5 -22.5 15.5 -20 C17 -18.3 17 -17.4 16 -17 C14.5 -16.6 13 -17.5 11.5 -18 "
        "C10.2 -18.5 9.3 -20 9.5 -21.5 Z")


def shapes(paths, fill, stroke, width):
    return "".join(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"/>'
                   for d in paths)


def legs(paths, color, width):
    return "".join(f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round" '
                   f'stroke-linejoin="round"/>' for d in paths)


def goat(p):
    line, fill = p["line"], p["body"]
    torso_line = (legs(LEGS_FAR + LEGS_NEAR, line, 2.3) + shapes([TAIL, BODY], line, line, 2))
    torso_fill = (legs(LEGS_FAR + LEGS_NEAR, fill, 0.9) + shapes([TAIL, BODY], fill, "none", 0)
                  + f'<path d="M-8 -9.4 C-3 -8.4 2 -8.4 6.6 -9.4 C2 -9.8 -3 -9.8 -8 -9.4 Z" fill="{p["shade"]}"/>'
                  + f'<g stroke="{line}" stroke-width="0.45" fill="none" stroke-linecap="round" opacity=".75">'
                    f'<path d="M-6 -9.6 q4 0.9 9 0"/><path d="M-9.6 -10.4 q1.4 1.2 3.4 1.3"/>'
                    f'<path d="M-10.4 -12.6 q0.6 1.2 1.8 1.8"/><path d="M5.6 -11 q1.4 0.6 2.2 1.6"/></g>'
                  + "".join(f'<rect x="{x}" y="-1.2" width="1.8" height="1.2" rx="0.3" fill="{line}"/>'
                            for x in (-8.5, -10.5, 5.3, 2.9)))
    head_line = (f'<path d="M12.2 -22.6 C11.6 -26.5 8.5 -28.4 5.5 -27.6" stroke="{line}" stroke-width="1.5" fill="none" '
                 f'stroke-linecap="round" opacity=".8"/>' + shapes([NECK, EAR, HEAD], line, line, 2))
    head_fill = (shapes([NECK, EAR, HEAD], fill, "none", 0)
                 + f'<path d="M7 -15.6 q1.4 -1.6 2.6 -3.4" stroke="{line}" stroke-width="0.45" fill="none" opacity=".7"/>'
                 + f'<path d="M14 -16.9 l-0.3 3.2 l1.5 -3" fill="{line}" stroke="{line}" stroke-width="0.4" stroke-linejoin="round"/>'
                 + f'<path d="M11 -22.3 C10 -26 6.5 -27.5 3.5 -26" stroke="{line}" stroke-width="1.9" fill="none" stroke-linecap="round"/>'
                 + f'<g stroke="{fill}" stroke-width="0.4" stroke-linecap="round">'
                   f'<path d="M10.2 -24.4 l0.9 -0.3"/><path d="M8.9 -25.8 l0.6 -0.7"/><path d="M7.2 -26.5 l0.3 -0.9"/>'
                   f'<path d="M5.5 -26.6 l0 -0.9"/></g>'
                 + f'<ellipse cx="13.1" cy="-20.2" rx="0.85" ry="0.45" fill="{line}" transform="rotate(20 13.1 -20.2)"/>'
                 + f'<path d="M15.6 -17.6 q-0.6 0.3 -1.2 0" stroke="{line}" stroke-width="0.4" fill="none"/>')
    return torso_line, torso_fill, head_line, head_fill


def build(cells, theme):
    pal = PALETTES[theme]
    order = tour(cells)
    width = LEFT * 2 + 53 * PITCH - GAP
    height = TOP + 7 * PITCH + 14
    css, body = [], []

    pose, head, hits, dirs = [], [], [], []
    t = 0.6
    prev = None
    reach = CELL / 2 + 14.5 * SCALE
    for col, row, lv in order:
        cx, cy = center(col, row)
        facing = 1 if prev is None or cx >= prev[0] else -1
        contact = (cx - reach * facing, cy + 13 * SCALE)
        ready = (contact[0] - RUNUP * facing, contact[1])
        windup = (ready[0] - 5 * facing, ready[1])
        if prev is not None:
            t += math.dist(prev, ready) / WALK
        pose.append((t, ready, facing)); head.append((t, 0))
        t += 0.2
        pose.append((t, ready, facing)); head.append((t, 0))
        t += 0.3
        pose.append((t, windup, facing)); head.append((t, -22))
        t += 0.15
        pose.append((t, windup, facing)); head.append((t, -22))
        head.append((t + 0.08, 34))
        t += math.dist(windup, contact) / CHARGE
        pose.append((t, contact, facing)); head.append((t, 34))
        hits.append(t); dirs.append(facing)
        t += 0.3
        recoil = (contact[0] - 7 * facing, contact[1])
        pose.append((t, recoil, facing)); head.append((t, 0))
        t += 0.2
        pose.append((t, recoil, facing)); head.append((t, 0))
        prev = recoil
    total = t + REGROW

    frames, last_face, last_pose = [], None, None
    for tt, (x, y), f in pose:
        if last_face is not None and f != last_face:
            pt, (px, py) = last_pose
            frames.append(f"{pct(pt + 0.06, total)}{{transform:translate({px:.1f}px,{py:.1f}px) scale({f},1)}}")
        frames.append(f"{pct(tt, total)}{{transform:translate({x:.1f}px,{y:.1f}px) scale({f},1)}}")
        last_face, last_pose = f, (tt, (x, y))
    (x0, y0), f0 = pose[0][1], pose[0][2]
    frames.insert(0, f"0%{{transform:translate({x0:.1f}px,{y0:.1f}px) scale({f0},1)}}")
    css.append("@keyframes walk{" + "".join(frames) + "}")
    css.append(f".pet{{animation:walk {total:.2f}s linear infinite}}")
    hf = "".join(f"{pct(tt, total)}{{transform:rotate({a}deg)}}" for tt, a in head)
    css.append("@keyframes head{0%{transform:rotate(0deg)}" + hf + "100%{transform:rotate(0deg)}}")
    css.append(f".head{{animation:head {total:.2f}s linear infinite}}")

    hit_of = {(c[0], c[1]): (h, d) for c, h, d in zip(order, hits, dirs)}
    for i, (col, row, lv) in enumerate(cells):
        x, y = LEFT + col * PITCH, TOP + row * PITCH
        color = pal["levels"][lv]
        attrs = f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2"'
        if (col, row) not in hit_of:
            body.append(f'<rect {attrs} fill="{color}"/>')
            continue
        h, d = hit_of[(col, row)]
        body.append(f'<rect {attrs} fill="{pal["levels"][0]}"/>')
        kf = (f"0%{{transform:none;opacity:1}}{pct(h, total)}{{transform:none;opacity:1}}"
              f"{pct(h + 0.25, total)}{{transform:translate({16 * d}px,-16px) rotate({140 * d}deg);opacity:1}}"
              f"{pct(h + 0.6, total)}{{transform:translate({26 * d}px,-2px) rotate({260 * d}deg);opacity:0}}"
              f"{pct(total - REGROW, total)}{{transform:none;opacity:0}}100%{{transform:none;opacity:1}}")
        css.append(f"@keyframes c{i}{{{kf}}}.c{i}{{animation:c{i} {total:.2f}s ease-out infinite;"
                   f"transform-box:fill-box;transform-origin:center}}")
        body.append(f'<rect class="c{i}" {attrs} fill="{color}"/>')

    css.append("@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-1px)}}")
    css.append(".bob{animation:bob .4s ease-in-out infinite}")

    torso_line, torso_fill, head_line, head_fill = goat(COAT)

    def turning(inner):
        return (f'<g transform="translate({PIVOT[0]},{PIVOT[1]})"><g class="head">'
                f'<g transform="translate({-PIVOT[0]},{-PIVOT[1]})">{inner}</g></g></g>')

    art = f'<g class="bob">{torso_line}{turning(head_line)}{torso_fill}{turning(head_fill)}</g>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
            f"<style>{''.join(css)}</style>"
            f"{''.join(body)}"
            f'<g class="pet"><g transform="scale({SCALE})">{art}</g></g>'
            f"</svg>")


def main():
    cells = fetch_cells(USER)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in PALETTES:
        (OUT / f"goat-{theme}.svg").write_text(build(cells, theme), encoding="utf-8")


if __name__ == "__main__":
    main()
