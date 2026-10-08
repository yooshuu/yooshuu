import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = sys.argv[1] if len(sys.argv) > 1 else "yooshuu"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist")
ART = Path(__file__).with_name("charmeleon.art")

LEVELS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'."

FONT, LINE, CHAR = 14, 20, 8.4
ART_FONT, ART_LINE, ART_CHAR = 6.5, 7.8, 3.9
WIDTH = 46

THEMES = {
    "dark": {"bg": "#161b22", "art": "#c9d1d9", "user": "#ff7b72", "title": "#e6edf3", "key": "#ffa657",
             "dots": "#3d444d", "value": "#a5d6ff", "rule": "#3d444d", "bright_dense": True},
    "light": {"bg": "#f6f8fa", "art": "#1f2328", "user": "#cf222e", "title": "#1f2328", "key": "#bc4c00",
              "dots": "#d1d9e0", "value": "#0a3069", "rule": "#d1d9e0", "bright_dense": False},
}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json",
                                                                          "User-Agent": "profile-card"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    return json.load(urllib.request.urlopen(req))


def stats(user):
    profile = api(f"/users/{user}")
    repos = api(f"/users/{user}/repos?per_page=100")
    commits = api(f"/search/commits?q=author:{user}&per_page=1")["total_count"]
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions", headers={"User-Agent": "profile-card"})
    page = urllib.request.urlopen(req).read().decode("utf-8")
    m = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
    return {
        "repos": profile["public_repos"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "followers": profile["followers"],
        "commits": commits,
        "contributions": m.group(1) if m else "-",
    }


def info(s):
    return [
        ("title", f"{USER}@github"),
        ("row", "Role", "Backend Developer"),
        ("row", "Languages.Programming", "Java, JavaScript"),
        ("row", "Frameworks", "Spring Boot, MyBatis"),
        ("row", "Database", "MariaDB, Oracle"),
        ("row", "Learning", "Spring AI"),
        ("row", "Project", "MOVE:ON (Team Lead)"),
        ("title", "- Contact"),
        ("row", "GitHub", f"github.com/{USER}"),
        ("title", "- GitHub Stats"),
        ("pair", ("Repos", s["repos"]), ("Stars", s["stars"])),
        ("pair", ("Commits", s["commits"]), ("Followers", s["followers"])),
        ("row", "Contributions (1y)", s["contributions"]),
    ]


def ascii_art(t):
    out = []
    n = len(RAMP)
    for line in ART.read_text(encoding="utf-8").rstrip("\n").split("\n"):
        chars = []
        for c in line:
            if c == " ":
                chars.append(" ")
                continue
            level = LEVELS.index(c) / 63
            i = (1 - level) if t["bright_dense"] else level
            chars.append(RAMP[min(n - 1, round(i * (n - 1)))])
        out.append("".join(chars))
    return out


def span(text, color, bold=False):
    weight = ' font-weight="700"' if bold else ""
    return f'<tspan fill="{color}"{weight}>{escape(text)}</tspan>'


def row(key, value, width, t):
    dots = max(2, width - len(key) - len(str(value)) - 4)
    return (span(". ", t["dots"]) + span(key, t["key"]) + span(": ", t["key"])
            + span("." * dots, t["dots"]) + span(" " + str(value), t["value"]))


def render(items, t):
    out = []
    for item in items:
        if item[0] == "title":
            bold = "@" in item[1]
            rule = "-" * max(2, WIDTH - len(item[1]) - 1)
            out.append(span(item[1] + " ", t["user"] if bold else t["title"], bold) + span(rule, t["rule"]))
        elif item[0] == "row":
            out.append(row(item[1], item[2], WIDTH, t))
        else:
            half = WIDTH // 2 - 1
            right = row(item[2][0], item[2][1], WIDTH - half - 3, t)
            out.append(row(item[1][0], item[1][1], half, t) + span(" | ", t["dots"])
                       + right[len(span(". ", t["dots"])):])
    out.append(span("-" * (WIDTH + 2), t["rule"]))
    return out


def build(s, theme):
    t = THEMES[theme]
    art = ascii_art(t)
    lines = render(info(s), t)
    art_w = max(len(a) for a in art) * ART_CHAR
    height = max(len(art) * ART_LINE, len(lines) * LINE) + 50
    info_x = 30 + art_w + 50
    width = info_x + (WIDTH + 2) * CHAR + 30

    top = (height - len(art) * ART_LINE) / 2 + ART_FONT
    art_svg = "".join(f'<text x="30" y="{top + i * ART_LINE:.0f}" font-size="{ART_FONT}px" fill="{t["art"]}">{escape(a)}</text>'
                      for i, a in enumerate(art))
    top = (height - len(lines) * LINE) / 2 + FONT
    info_svg = "".join(f'<text x="{info_x:.0f}" y="{top + i * LINE:.0f}">{l}</text>' for i, l in enumerate(lines))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height}" width="{width:.0f}" height="{height}" '
            f'font-family="ConsolasFallback,Consolas,\'SFMono-Regular\',Menlo,monospace" font-size="{FONT}px">'
            f'<style>text{{white-space:pre}}</style>'
            f'<rect width="100%" height="100%" rx="12" fill="{t["bg"]}"/>{art_svg}{info_svg}</svg>')


def main():
    s = stats(USER)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"card-{theme}.svg").write_text(build(s, theme), encoding="utf-8")


if __name__ == "__main__":
    main()
