"""Builds the neofetch-style profile card (dark_mode.svg and light_mode.svg).

Runs daily on GitHub Actions. Only the standard library is used.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request
from html import escape
from pathlib import Path

USER = "hlspablo"
CODING_SINCE = dt.date(2016, 1, 6)
LINE_WIDTH = 63
ROOT = Path(__file__).parent

THEMES = {
    "dark_mode.svg": {
        "bg": "#161b22", "text": "#c9d1d9", "key": "#ffa657",
        "value": "#a5d6ff", "dots": "#616e7f", "art": "#c9d1d9",
    },
    "light_mode.svg": {
        "bg": "#f6f8fa", "text": "#24292f", "key": "#953800",
        "value": "#0a3069", "dots": "#c2cfde", "art": "#24292f",
    },
}


def graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch_stats() -> dict[str, int]:
    summary = graphql(
        """query($login: String!) {
          user(login: $login) {
            followers { totalCount }
            repositories(ownerAffiliations: OWNER) { totalCount }
            repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
            contributionsCollection { contributionCalendar { totalContributions } }
          }
        }""",
        {"login": USER},
    )["user"]

    stars, cursor = 0, None
    while True:
        page = graphql(
            """query($login: String!, $cursor: String) {
              user(login: $login) {
                repositories(ownerAffiliations: OWNER, first: 100, after: $cursor) {
                  nodes { stargazerCount }
                  pageInfo { hasNextPage endCursor }
                }
              }
            }""",
            {"login": USER, "cursor": cursor},
        )["user"]["repositories"]
        stars += sum(node["stargazerCount"] for node in page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    return {
        "repos": summary["repositories"]["totalCount"],
        "contributed": summary["repositoriesContributedTo"]["totalCount"],
        "stars": stars,
        "contributions": summary["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "followers": summary["followers"]["totalCount"],
    }


def uptime(today: dt.date) -> str:
    years = today.year - CODING_SINCE.year
    months = today.month - CODING_SINCE.month
    days = today.day - CODING_SINCE.day
    if days < 0:
        months -= 1
        previous_month_end = today.replace(day=1) - dt.timedelta(days=1)
        days += previous_month_end.day
    if months < 0:
        years -= 1
        months += 12

    def plural(amount: int, word: str) -> str:
        return f"{amount} {word}{'' if amount == 1 else 's'}"

    return f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"


def repos_label(stats: dict[str, int]) -> str:
    if stats["contributed"]:
        return f"{stats['repos']} {{Contributed: {stats['contributed']}}}"
    return str(stats["repos"])


def info_lines(stats: dict[str, int], today: dt.date) -> list[list[tuple[str, str]]]:
    """Each line is a list of (style, text) pieces."""

    def header(title: str) -> list[tuple[str, str]]:
        return [("text", title + " "), ("dots", "—" * (LINE_WIDTH - len(title) - 1))]

    def field(key: str, value: str) -> list[tuple[str, str]]:
        dots = LINE_WIDTH - len(key) - len(value) - 6
        return [("dots", ". "), ("key", key), ("text", ":"), ("dots", " " + "." * dots + " "), ("value", value)]

    def pair(key1: str, value1: str, key2: str, value2: str) -> list[tuple[str, str]]:
        left_width = 33
        dots1 = left_width - len(key1) - len(value1) - 6
        dots2 = LINE_WIDTH - left_width - len(key2) - len(value2) - 6
        return [
            ("dots", ". "), ("key", key1), ("text", ":"), ("dots", " " + "." * dots1 + " "), ("value", value1),
            ("text", " | "), ("key", key2), ("text", ":"), ("dots", " " + "." * dots2 + " "), ("value", value2),
        ]

    blank: list[tuple[str, str]] = [("dots", ".")]

    return [
        header("pablo@henrique"),
        field("OS", "macOS, iOS, Android, Linux"),
        field("Uptime", uptime(today)),
        field("Host", "DOC ADV (doc.adv.br)"),
        field("Kernel", "Full-Stack & Mobile Software Engineer"),
        field("IDE", "Neovim, Zed, IntelliJ IDEA"),
        blank,
        field("Languages.Programming", "TypeScript, PHP, Java, Kotlin, Swift"),
        field("Languages.Computer", "HTML, CSS, SQL, JSON, YAML"),
        field("Languages.Real", "Portuguese, English"),
        blank,
        field("Stack.Mobile", "React Native, Expo, iOS, Android"),
        field("Stack.Backend", "Laravel, Django, NestJS"),
        field("Stack.AI", "OpenAI API, LLMs, MCP"),
        blank,
        field("Maintainer", "expo-server-sdk-java (Expo docs)"),
        field("Hobbies", "Chess"),
        blank,
        header("- Contact"),
        field("Email", "pabllobeg@gmail.com"),
        field("LinkedIn", "hlspablo"),
        field("Site", "doc.adv.br"),
        blank,
        header("- GitHub Stats"),
        pair("Repos", repos_label(stats), "Stars", f"{stats['stars']:,}"),
        pair("Contributions (1y)", f"{stats['contributions']:,}", "Followers", f"{stats['followers']:,}"),
    ]


def render(theme: dict[str, str], art: list[str], lines: list[list[tuple[str, str]]]) -> str:
    line_height = 20
    top = 30
    rows = max(len(art), len(lines))
    height = top + rows * line_height + 20
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'SF Mono\',Menlo,monospace" '
        f'width="985px" height="{height}px" font-size="15px">',
        "<style>",
        f".text{{fill:{theme['text']}}} .key{{fill:{theme['key']}}} .value{{fill:{theme['value']}}} "
        f".dots{{fill:{theme['dots']}}} .art{{fill:{theme['art']}}}",
        "text,tspan{white-space:pre}",
        "</style>",
        f'<rect width="985px" height="{height}px" fill="{theme["bg"]}" rx="15"/>',
        f'<text x="15" y="{top}" class="art">',
    ]
    for index, row in enumerate(art):
        out.append(f'<tspan x="15" y="{top + index * line_height}">{escape(row)}</tspan>')
    out.append("</text>")
    out.append(f'<text x="390" y="{top}" class="text">')
    for index, pieces in enumerate(lines):
        spans = "".join(f'<tspan class="{style}">{escape(text)}</tspan>' for style, text in pieces)
        out.append(f'<tspan x="390" y="{top + index * line_height}">{spans}</tspan>')
    out.append("</text>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> None:
    art = (ROOT / "ascii.txt").read_text().rstrip("\n").split("\n")
    stats = fetch_stats()
    lines = info_lines(stats, dt.date.today())
    for filename, theme in THEMES.items():
        (ROOT / filename).write_text(render(theme, art, lines))
    print(stats)


if __name__ == "__main__":
    main()
