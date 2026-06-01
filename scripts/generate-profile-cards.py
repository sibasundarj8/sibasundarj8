#!/usr/bin/env python3
"""Generate local SVG cards for the GitHub profile README.

The public github-readme-stats deployment can be unavailable or paused. These
cards are generated from the GitHub REST API and committed as local assets so
the README always has visible analytics.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


USERNAME = "sibasundarj8"
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

BG = "#0D1117"
PANEL = "#0A0F16"
BORDER = "#243041"
TEXT = "#E6EDF3"
MUTED = "#9BA8B7"
DIM = "#64748B"
CYAN = "#00E5FF"
BLUE = "#1F6FEB"
GREEN = "#2DD4BF"
AMBER = "#FFB000"

UPDATED_FOOTER_RE = re.compile(r"Updated [A-Z][a-z]{2} \d{2}, \d{4} via GitHub API")


def request_json(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "sibasundarj8-profile-card-generator",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def xml(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt(num: int) -> str:
    return f"{num:,}"


def normalize_generated_svg(content: str) -> str:
    return UPDATED_FOOTER_RE.sub("Updated <date> via GitHub API", content)


def write_if_semantically_changed(path: Path, content: str) -> bool:
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if normalize_generated_svg(current) == normalize_generated_svg(content):
            print(f"No semantic changes in {path.relative_to(ROOT)}")
            return False

    path.write_text(content, encoding="utf-8")
    print(f"Updated {path.relative_to(ROOT)}")
    return True


def search_count(query: str, kind: str = "issues") -> int:
    if kind == "commits":
        url = f"https://api.github.com/search/commits?q={quote(query)}"
        headers = {
            "Accept": "application/vnd.github.cloak-preview+json",
            "User-Agent": "sibasundarj8-profile-card-generator",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as response:
            return int(json.load(response).get("total_count", 0))
    data = request_json(f"https://api.github.com/search/issues?q={quote(query)}")
    return int(data.get("total_count", 0))


def stat_item(x: int, y: int, label: str, value: object, color: str = CYAN) -> str:
    return f"""
    <g transform="translate({x} {y})">
      <text x="0" y="0" fill="{MUTED}" font-size="15" font-weight="600">{xml(label)}</text>
      <text x="0" y="38" fill="{TEXT}" font-size="31" font-weight="800">{xml(value)}</text>
      <rect x="0" y="52" width="152" height="3" rx="1.5" fill="{BORDER}"/>
      <rect x="0" y="52" width="88" height="3" rx="1.5" fill="{color}"/>
    </g>"""


def generate_github_stats(user: dict[str, Any], repos: list[dict[str, Any]]) -> str:
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    forks = sum(int(repo.get("forks_count", 0)) for repo in repos)
    commits = search_count(f"author:{USERNAME}", "commits")
    prs = search_count(f"author:{USERNAME} type:pr")
    issues = search_count(f"author:{USERNAME} type:issue")
    refreshed = dt.datetime.now(dt.timezone.utc).strftime("%b %d, %Y")

    return f"""<svg width="640" height="320" viewBox="0 0 640 320" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">GitHub stats for {xml(user.get("name") or USERNAME)}</title>
  <desc id="desc">Local GitHub statistics card generated from the public GitHub REST API.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="640" y2="320" gradientUnits="userSpaceOnUse">
      <stop stop-color="#05070D"/>
      <stop offset="0.55" stop-color="{BG}"/>
      <stop offset="1" stop-color="#071923"/>
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="640" height="320" rx="18" fill="url(#bg)"/>
  <rect x="1" y="1" width="638" height="318" rx="17" stroke="{BORDER}"/>
  <circle cx="552" cy="70" r="56" fill="{CYAN}" opacity="0.08"/>
  <circle cx="552" cy="70" r="35" fill="{CYAN}" opacity="0.12"/>
  <text x="34" y="52" fill="{TEXT}" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="26" font-weight="800">GitHub Analytics</text>
  <text x="34" y="78" fill="{MUTED}" font-family="JetBrains Mono, Consolas, monospace" font-size="13">github.com/{USERNAME}</text>
  <g filter="url(#glow)">
    <path d="M540 57h24v24h-24z" fill="{CYAN}" opacity="0.9"/>
    <path d="M552 45v48M528 69h48" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>
  </g>
  <g font-family="Inter, Segoe UI, Arial, sans-serif">
    {stat_item(36, 128, "Public Repos", fmt(int(user.get("public_repos", 0))), CYAN)}
    {stat_item(236, 128, "Public Commits", fmt(commits), BLUE)}
    {stat_item(436, 128, "Total Stars", fmt(stars), AMBER)}
    {stat_item(36, 226, "Followers", fmt(int(user.get("followers", 0))), GREEN)}
    {stat_item(236, 226, "Pull Requests", fmt(prs), CYAN)}
    {stat_item(436, 226, "Forks", fmt(forks), BLUE)}
  </g>
  <text x="34" y="302" fill="{DIM}" font-family="JetBrains Mono, Consolas, monospace" font-size="12">Updated {refreshed} via GitHub API</text>
</svg>
"""


def generate_language_card(languages: dict[str, int]) -> str:
    total = sum(languages.values()) or 1
    ordered = sorted(languages.items(), key=lambda item: item[1], reverse=True)
    colors = [CYAN, BLUE, GREEN, AMBER, "#A78BFA", "#F472B6"]
    segments = []
    cursor = 34.0
    bar_width = 572.0
    rows = []
    for index, (lang, amount) in enumerate(ordered[:6]):
        pct = amount / total * 100
        width = bar_width * pct / 100
        color = colors[index % len(colors)]
        segments.append(f'<rect x="{cursor:.2f}" y="116" width="{width:.2f}" height="14" rx="7" fill="{color}"/>')
        cursor += width
        y = 172 + index * 32
        rows.append(
            f"""
    <g transform="translate(38 {y})">
      <circle cx="0" cy="-5" r="5" fill="{color}"/>
      <text x="18" y="0" fill="{TEXT}" font-size="16" font-weight="700">{xml(lang)}</text>
      <text x="526" y="0" fill="{MUTED}" font-size="15" font-weight="700" text-anchor="end">{pct:.1f}%</text>
      <rect x="112" y="-12" width="344" height="8" rx="4" fill="{BORDER}"/>
      <rect x="112" y="-12" width="{344 * pct / 100:.2f}" height="8" rx="4" fill="{color}"/>
    </g>"""
        )

    refreshed = dt.datetime.now(dt.timezone.utc).strftime("%b %d, %Y")
    return f"""<svg width="640" height="320" viewBox="0 0 640 320" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Most used languages for {USERNAME}</title>
  <desc id="desc">Local top languages card generated from public GitHub repository language data.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="640" y2="320" gradientUnits="userSpaceOnUse">
      <stop stop-color="#05070D"/>
      <stop offset="0.55" stop-color="{BG}"/>
      <stop offset="1" stop-color="#061D20"/>
    </linearGradient>
  </defs>
  <rect width="640" height="320" rx="18" fill="url(#bg)"/>
  <rect x="1" y="1" width="638" height="318" rx="17" stroke="{BORDER}"/>
  <text x="34" y="52" fill="{TEXT}" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="26" font-weight="800">Most Used Languages</text>
  <text x="34" y="78" fill="{MUTED}" font-family="JetBrains Mono, Consolas, monospace" font-size="13">public repository language breakdown</text>
  <rect x="34" y="116" width="572" height="14" rx="7" fill="{BORDER}"/>
  {''.join(segments)}
  <g font-family="Inter, Segoe UI, Arial, sans-serif">
    {''.join(rows)}
  </g>
  <text x="34" y="302" fill="{DIM}" font-family="JetBrains Mono, Consolas, monospace" font-size="12">Updated {refreshed} via GitHub API</text>
</svg>
"""


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    user = request_json(f"https://api.github.com/users/{USERNAME}")
    repos = request_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated")

    languages: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        data = request_json(repo["languages_url"])
        for lang, amount in data.items():
            languages[lang] = languages.get(lang, 0) + int(amount)

    write_if_semantically_changed(ASSETS / "github-stats-card.svg", generate_github_stats(user, repos))
    write_if_semantically_changed(ASSETS / "top-langs-card.svg", generate_language_card(languages))


if __name__ == "__main__":
    main()
