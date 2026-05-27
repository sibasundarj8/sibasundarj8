#!/usr/bin/env python3
"""Generate a contribution-grid arcade GIF from the real GitHub calendar.

GitHub profile READMEs cannot execute JavaScript or run a true browser game.
This script produces the closest GitHub-compatible version: a generated GIF
based on the current public contribution grid. It destroys every active cell,
restores the grid, and loops.
"""

from __future__ import annotations

import datetime as dt
import html
import random
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont


USERNAME = "sibasundarj8"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "gh-space-shooter.gif"

WIDTH = 1200
HEIGHT = 310
CELL = 12
GAP = 5
GRID_COLS = 53
GRID_ROWS = 7
GRID_W = GRID_COLS * CELL + (GRID_COLS - 1) * GAP
GRID_H = GRID_ROWS * CELL + (GRID_ROWS - 1) * GAP
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = 74
SHIP_Y = HEIGHT - 42

BG = (7, 12, 18)
PANEL = (10, 17, 25)
GRID_EMPTY = (12, 28, 34)
GRID_COLORS = [
    (12, 28, 34),
    (14, 92, 45),
    (16, 130, 58),
    (26, 175, 73),
    (56, 211, 88),
]
CYAN = (0, 229, 255)
BLUE = (47, 129, 247)
BLUE_DARK = (31, 111, 235)
GREEN = (45, 212, 191)
YELLOW = (244, 211, 45)
AMBER = (184, 135, 28)
WHITE = (231, 238, 247)
MUTED = (154, 168, 183)
DIM = (100, 116, 139)


@dataclass(frozen=True)
class Cell:
    row: int
    col: int
    level: int
    count: int
    date: str

    @property
    def x(self) -> int:
        return GRID_X + self.col * (CELL + GAP)

    @property
    def y(self) -> int:
        return GRID_Y + self.row * (CELL + GAP)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_12 = load_font(12)
FONT_14 = load_font(14)
FONT_16 = load_font(16, bold=True)
FONT_22 = load_font(22, bold=True)


def fetch_contribution_html() -> str:
    year = dt.datetime.now(dt.timezone.utc).year
    url = f"https://github.com/users/{USERNAME}/contributions?from={year}-01-01&to={year}-12-31"
    req = Request(url, headers={"User-Agent": "sibasundarj8-contribution-arcade"})
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_summary(markup: str) -> str:
    match = re.search(
        r'id="js-contribution-activity-description"[^>]*>\s*([\d,]+)\s+contributions?\s+in\s+(\d{4})',
        markup,
        re.S,
    )
    if not match:
        return "public contribution grid"
    return f"{match.group(1)} contributions in {match.group(2)}"


def parse_cells(markup: str) -> list[Cell]:
    cells: list[Cell] = []
    for match in re.finditer(r'<td\b(?=[^>]*class="ContributionCalendar-day")[^>]*>', markup):
        tag = match.group(0)
        date_match = re.search(r'data-date="([^"]+)"', tag)
        level_match = re.search(r'data-level="(\d+)"', tag)
        id_match = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', tag)
        if not (date_match and level_match and id_match):
            continue

        tooltip = re.search(r"<tool-tip[^>]*>(.*?)</tool-tip>", markup[match.end() : match.end() + 900], re.S)
        tooltip_text = html.unescape(re.sub(r"<[^>]+>", "", tooltip.group(1)).strip()) if tooltip else ""
        count_match = re.search(r"(\d+)\s+contributions?", tooltip_text)
        count = int(count_match.group(1)) if count_match else 0

        cells.append(
            Cell(
                row=int(id_match.group(1)),
                col=int(id_match.group(2)),
                level=int(level_match.group(1)),
                count=count,
                date=date_match.group(1),
            )
        )

    return cells


def cell_color(cell: Cell) -> tuple[int, int, int]:
    if cell.count <= 0 and cell.level == 0:
        return GRID_EMPTY
    return GRID_COLORS[min(max(cell.level, 1), 4)]


def rounded_cell(draw: ImageDraw.ImageDraw, cell: Cell, fill: tuple[int, int, int], scale: float = 1.0) -> None:
    size = max(2, int(CELL * scale))
    offset = (CELL - size) // 2
    draw.rounded_rectangle(
        [cell.x + offset, cell.y + offset, cell.x + offset + size, cell.y + offset + size],
        radius=3,
        fill=fill,
    )


def draw_header(
    draw: ImageDraw.ImageDraw,
    summary: str,
    active_count: int,
    total_cells: int,
    current_frame: int,
    total_frames: int,
) -> None:
    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    draw.text((GRID_X, 25), "GitHub Contribution Arcade", fill=WHITE, font=FONT_22)
    draw.text((GRID_X, 52), f"{USERNAME}  |  {summary}", fill=MUTED, font=FONT_14)

    status = f"cells: {active_count}/{total_cells} active  |  updated {updated}"
    draw.text((GRID_X + GRID_W, 31), status, fill=DIM, font=FONT_12, anchor="ra")

    progress = min(1.0, current_frame / max(1, total_frames))
    draw.rounded_rectangle([GRID_X, HEIGHT - 18, GRID_X + GRID_W, HEIGHT - 13], radius=2, fill=(24, 34, 48))
    draw.rounded_rectangle([GRID_X, HEIGHT - 18, GRID_X + int(GRID_W * progress), HEIGHT - 13], radius=2, fill=CYAN)


def draw_ship(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.polygon([(x, y - 20), (x - 12, y + 12), (x, y + 5), (x + 12, y + 12)], fill=BLUE)
    draw.rectangle([x - 20, y + 9, x - 11, y + 15], fill=BLUE_DARK)
    draw.rectangle([x + 11, y + 9, x + 20, y + 15], fill=BLUE_DARK)
    draw.rectangle([x - 3, y - 27, x + 3, y - 18], fill=CYAN)
    draw.point((x, y - 30), fill=WHITE)
    draw.point((x - 22, y + 13), fill=CYAN)
    draw.point((x + 22, y + 13), fill=CYAN)


def draw_stars(draw: ImageDraw.ImageDraw, stars: list[tuple[int, int, tuple[int, int, int]]], frame: int) -> None:
    for index, (x, y, color) in enumerate(stars):
        twinkle = (frame + index * 7) % 41
        star = WHITE if twinkle < 3 else color
        draw.point((x, y), fill=star)
        if index % 17 == 0 and twinkle < 4:
            draw.point((x + 1, y), fill=star)
            draw.point((x, y + 1), fill=star)


def target_order(active_cells: list[Cell]) -> list[Cell]:
    # Destroy nearby center targets first, then sweep outward for a readable game path.
    center_col = GRID_COLS / 2
    center_row = GRID_ROWS / 2
    return sorted(active_cells, key=lambda c: (abs(c.col - center_col) + abs(c.row - center_row), c.col, c.row))


def render_frames(cells: list[Cell], summary: str) -> list[Image.Image]:
    active_cells = [cell for cell in cells if cell.count > 0 or cell.level > 0]
    targets = target_order(active_cells)

    intro_frames = 14
    frames_per_target = 2
    impact_frames = 6
    restore_frames = 30
    hold_frames = 12
    hit_frame = {target: intro_frames + index * frames_per_target for index, target in enumerate(targets)}
    destroy_end = intro_frames + len(targets) * frames_per_target + impact_frames
    total_frames = destroy_end + restore_frames + hold_frames

    rng = random.Random(f"{USERNAME}-{summary}")
    stars = [
        (
            rng.randrange(18, WIDTH - 18),
            rng.randrange(10, HEIGHT - 26),
            rng.choice([WHITE, DIM, MUTED]),
        )
        for _ in range(92)
    ]

    frames: list[Image.Image] = []
    for frame in range(total_frames):
        image = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, HEIGHT - 4, WIDTH, HEIGHT], fill=PANEL)
        draw_stars(draw, stars, frame)
        draw_header(draw, summary, len(active_cells), len(cells), frame, total_frames)

        destroyed = {target for target, hit in hit_frame.items() if frame > hit + impact_frames and frame < destroy_end}
        restore_progress = max(0.0, min(1.0, (frame - destroy_end) / max(1, restore_frames)))

        for cell in cells:
            if cell in destroyed:
                if restore_progress <= 0:
                    continue
                scale = restore_progress
            else:
                scale = 1.0
            rounded_cell(draw, cell, cell_color(cell), scale=scale)

        current_index = min(max((frame - intro_frames) // frames_per_target, 0), max(0, len(targets) - 1))
        ship_target = targets[current_index] if targets else Cell(3, 26, 0, 0, "")
        wobble = int(10 * (1 if frame % 18 < 9 else -1))
        ship_x = min(max(ship_target.x + CELL // 2 + wobble, GRID_X + 20), GRID_X + GRID_W - 20)

        for target, hit in hit_frame.items():
            if hit - 8 <= frame <= hit:
                progress = (frame - (hit - 8)) / 8
                sx, sy = ship_x, SHIP_Y - 26
                tx, ty = target.x + CELL // 2, target.y + CELL // 2
                bx = int(sx + (tx - sx) * progress)
                by = int(sy + (ty - sy) * progress)
                draw.rounded_rectangle([bx - 2, by - 11, bx + 2, by + 11], radius=2, fill=YELLOW)
                draw.line([sx, sy, bx, by], fill=(98, 84, 20), width=1)

            if hit <= frame <= hit + impact_frames:
                cx, cy = target.x + CELL // 2, target.y + CELL // 2
                radius = 3 + (frame - hit) * 3
                draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=YELLOW, width=2)
                draw.rectangle([cx - 3, cy - 3, cx + 3, cy + 3], fill=WHITE)
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]:
                    draw.line([cx, cy, cx + dx * radius, cy + dy * radius], fill=AMBER, width=2)

        if frame >= destroy_end:
            text = "RESTORING GRID"
            draw.rounded_rectangle([WIDTH // 2 - 110, 200, WIDTH // 2 + 110, 230], radius=8, fill=(10, 17, 25))
            draw.text((WIDTH // 2, 206), text, fill=CYAN, font=FONT_16, anchor="ma")

        draw_ship(draw, ship_x, SHIP_Y)
        frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=48))

    return frames


def main() -> None:
    markup = fetch_contribution_html()
    summary = parse_summary(markup)
    cells = parse_cells(markup)
    if not cells:
        raise RuntimeError("Could not parse GitHub contribution cells.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames = render_frames(cells, summary)
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=42,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Generated {OUTPUT} with {len(frames)} frames from {len(cells)} contribution cells.")


if __name__ == "__main__":
    main()
