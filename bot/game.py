"""Card generation and win detection for 90-ball Bongo."""

from __future__ import annotations

import random
from collections.abc import Iterable, Sequence
from typing import Any

ROWS = 3
COLUMNS = 9
NUMBERS_PER_ROW = 5
TOTAL_NUMBERS = 90


def _column_range(column: int) -> range:
    if column == 0:
        return range(1, 10)
    if column == COLUMNS - 1:
        return range(80, 91)
    start = column * 10
    return range(start, start + 10)


def generate_card(rng: Any | None = None) -> list[list[int | None]]:
    """Create a 3x9 ticket with five numbers on each row."""
    generator = rng or random.SystemRandom()
    occupied = [[False] * COLUMNS for _ in range(ROWS)]
    column_counts = [0] * COLUMNS

    for row in range(ROWS):
        available = [
            column
            for column, count in enumerate(column_counts)
            if count < ROWS
        ]
        chosen = sorted(generator.sample(available, NUMBERS_PER_ROW))
        for column in chosen:
            occupied[row][column] = True
            column_counts[column] += 1

    card: list[list[int | None]] = [[None] * COLUMNS for _ in range(ROWS)]
    for column, count in enumerate(column_counts):
        values = sorted(generator.sample(_column_range(column), count))
        row_indexes = [row for row in range(ROWS) if occupied[row][column]]
        for row, value in zip(row_indexes, values, strict=True):
            card[row][column] = value

    return card


def create_draw_order(rng: Any | None = None) -> list[int]:
    """Return every call number from 1 to 90 in a random order."""
    generator = rng or random.SystemRandom()
    numbers = list(range(1, TOTAL_NUMBERS + 1))
    generator.shuffle(numbers)
    return numbers


def find_winners(
    players: Iterable[dict[str, Any]],
    called_numbers: Sequence[int],
) -> list[dict[str, Any]]:
    """Find every player with a complete five-number horizontal row."""
    called = set(called_numbers)
    winners: list[dict[str, Any]] = []

    for player in players:
        card = player["card"]
        has_complete_row = any(
            all(number in called for number in row if number is not None)
            and sum(number is not None for number in row) == NUMBERS_PER_ROW
            for row in card
        )
        if has_complete_row:
            winners.append(player)

    return winners


def format_card(
    card: Sequence[Sequence[int | None]],
    called_numbers: Sequence[int] = (),
) -> str:
    """Format a ticket in a compact monospace-friendly text grid."""
    called = set(called_numbers)
    headings = ["01-09", "10-19", "20-29", "30-39", "40-49",
                "50-59", "60-69", "70-79", "80-90"]
    lines = [
        "BONGO CARD - 90 BALL",
        " ".join(f"{heading:>5}" for heading in headings),
        "-" * 54,
    ]

    for row in card:
        cells = []
        for number in row:
            if number is None:
                cells.append("  -- ")
            elif number in called:
                cells.append(f" [{number:02d}]")
            else:
                cells.append(f"  {number:02d} ")
        lines.append("".join(cells))

    lines.append("-" * 54)
    lines.append("Numbers in brackets have been called.")
    return "\n".join(lines)
