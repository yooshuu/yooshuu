import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = sys.argv[1] if len(sys.argv) > 1 else "yooshuu"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist")
ART = Path(__file__).with_name("cat.txt")

FONT, LINE, CHAR = 14, 20, 8.4
ART_FONT, ART_LINE, ART_CHAR = 9, 12, 5.4
WIDTH = 46

THEMES = {
    "dark": {"bg": "#161b22", "text": "#c9d1d9", "key": "#ffa657", "value": "#a5d6ff", "dots": "#616e7f",
             "art": {"@": "#e6edf3", "#": "#c9d1d9", "+": "#8b949e", ":": "#6e7681", ".": "#484f58",
                     "*": "#e3b46a", "~": "#79b8ff", "o": "#f778ba"}},
    "light": {"bg": "#f6f8fa", "text": "#24292f", "key": "#953800", "value": "#0a3069", "dots": "#c2cfde",
              "art": {"@": "#1f2328", "#": "#24292f", "+": "#57606a", ":": "#afb8c1", ".": "#d0d7de",
                      "*": "#c48a2c", "~": "#4a90d9", "o": "#e5859b"}},
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


def span(text, color):
    return f'<tspan fill="{color}">{escape(text)}</tspan>'


def row(key, value, width, t):
    dots = max(2, width - len(key) - len(str(value)) - 4)
    return (span(". ", t["dots"]) + span(key, t["key"]) + span(": ", t["text"])
            + span("." * dots, t["dots"]) + span(" " + str(value), t["value"]))


def render(lines, t):
    out = []
    for item in lines:
        if item[0] == "title":
            rule = "—" * max(2, WIDTH - len(item[1]) - 1)
            out.append(span(item[1] + " ", t["text"]) + span(rule, t["dots"]))
        elif item[0] == "row":
            out.append(row(item[1], item[2], WIDTH, t))
        else:
            half = WIDTH // 2 - 1
            out.append(row(item[1][0], item[1][1], half, t) + span(" | ", t["text"])
                       + row(item[2][0], item[2][1], WIDTH - half - 3, t)[len(span(". ", t["dots"])):])
    return out


def build(s, theme):
    t = THEMES[theme]
    art = ART.read_text(encoding="utf-8").rstrip("\n").split("\n")
    art_w = max(len(a) for a in art) * ART_CHAR
    lines = render(info(s), t)
    height = max(len(art) * ART_LINE, len(lines) * LINE) + 60
    info_x = 30 + art_w + 40
    width = info_x + (WIDTH + 2) * CHAR + 30

    art_svg = []
    top = (height - len(art) * ART_LINE) / 2 + ART_FONT
    for i, text in enumerate(art):
        parts, cur, buf = [], None, ""
        for ch in text:
            color = t["art"].get(ch, t["text"])
            if ch == " ":
                buf += ch
                continue
            if color != cur and buf.strip():
                parts.append(span(buf, cur))
                buf = ""
            cur = color
            buf += ch
        if buf:
            parts.append(span(buf, cur or t["text"]))
        art_svg.append(f'<text x="30" y="{top + i * ART_LINE:.0f}" font-size="{ART_FONT}px">{"".join(parts)}</text>')

    top = (height - len(lines) * LINE) / 2 + FONT
    info_svg = [f'<text x="{info_x:.0f}" y="{top + i * LINE:.0f}">{l}</text>' for i, l in enumerate(lines)]

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height}" width="{width:.0f}" height="{height}" '
            f'font-family="ConsolasFallback,Consolas,\'SFMono-Regular\',Menlo,monospace" font-size="{FONT}px">'
            f'<style>text{{white-space:pre}}</style>'
            f'<rect width="100%" height="100%" rx="15" fill="{t["bg"]}"/>'
            f'{"".join(art_svg)}{"".join(info_svg)}</svg>')


def main():
    s = stats(USER)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"card-{theme}.svg").write_text(build(s, theme), encoding="utf-8")


if __name__ == "__main__":
    main()
