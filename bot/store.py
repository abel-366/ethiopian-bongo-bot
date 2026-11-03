"""Small SQLite store for Telegram group rounds."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any


class GameStore:
    def __init__(self, path: str) -> None:
        self.path = path
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS games (
                    chat_id INTEGER PRIMARY KEY,
                    status TEXT NOT NULL,
                    draw_order TEXT NOT NULL DEFAULT '[]',
                    called_numbers TEXT NOT NULL DEFAULT '[]',
                    draw_interval INTEGER NOT NULL DEFAULT 12,
                    winner_user_ids TEXT NOT NULL DEFAULT '[]',
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS players (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    display_name TEXT NOT NULL,
                    card TEXT NOT NULL,
                    joined_at REAL NOT NULL,
                    PRIMARY KEY (chat_id, user_id)
                );
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _decode_game(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "chat_id": row["chat_id"],
            "status": row["status"],
            "draw_order": json.loads(row["draw_order"]),
            "called_numbers": json.loads(row["called_numbers"]),
            "draw_interval": row["draw_interval"],
            "winner_user_ids": json.loads(row["winner_user_ids"]),
            "created_at": row["created_at"],
        }

    def get_game(self, chat_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM games WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
        return self._decode_game(row)

    def get_or_create_waiting_game(self, chat_id: int) -> dict[str, Any]:
        with self._connect() as connection:
            with connection:
                row = connection.execute(
                    "SELECT status FROM games WHERE chat_id = ?",
                    (chat_id,),
                ).fetchone()
                if row is None:
                    connection.execute(
                        """
                        INSERT INTO games (chat_id, status, created_at)
                        VALUES (?, 'waiting', ?)
                        """,
                        (chat_id, time.time()),
                    )
                elif row["status"] == "finished":
                    connection.execute(
                        "DELETE FROM players WHERE chat_id = ?",
                        (chat_id,),
                    )
                    connection.execute(
                        """
                        UPDATE games
                        SET status = 'waiting', draw_order = '[]',
                            called_numbers = '[]', winner_user_ids = '[]',
                            created_at = ?
                        WHERE chat_id = ?
                        """,
                        (time.time(), chat_id),
                    )
        game = self.get_game(chat_id)
        if game is None:
            raise RuntimeError("Failed to create a waiting game.")
        return game

    def add_player(
        self,
        chat_id: int,
        user_id: int,
        display_name: str,
        card: list[list[int | None]],
    ) -> bool:
        with self._connect() as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO players
                        (chat_id, user_id, display_name, card, joined_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chat_id,
                        user_id,
                        display_name,
                        json.dumps(card),
                        time.time(),
                    ),
                )
        return cursor.rowcount == 1

    def get_player(self, chat_id: int, user_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT user_id, display_name, card, joined_at
                FROM players WHERE chat_id = ? AND user_id = ?
                """,
                (chat_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return {
            "user_id": row["user_id"],
            "display_name": row["display_name"],
            "card": json.loads(row["card"]),
            "joined_at": row["joined_at"],
        }

    def list_players(self, chat_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT user_id, display_name, card, joined_at
                FROM players WHERE chat_id = ?
                ORDER BY joined_at, user_id
                """,
                (chat_id,),
            ).fetchall()
        return [
            {
                "user_id": row["user_id"],
                "display_name": row["display_name"],
                "card": json.loads(row["card"]),
                "joined_at": row["joined_at"],
            }
            for row in rows
        ]

    def start_game(
        self,
        chat_id: int,
        draw_order: list[int],
        draw_interval: int,
    ) -> bool:
        with self._connect() as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE games
                    SET status = 'active', draw_order = ?,
                        called_numbers = '[]', draw_interval = ?,
                        winner_user_ids = '[]'
                    WHERE chat_id = ? AND status = 'waiting'
                    """,
                    (json.dumps(draw_order), draw_interval, chat_id),
                )
        return cursor.rowcount == 1

    def peek_next_number(self, chat_id: int) -> int | None:
        game = self.get_game(chat_id)
        if game is None or game["status"] != "active":
            return None
        index = len(game["called_numbers"])
        if index >= len(game["draw_order"]):
            return None
        return game["draw_order"][index]

    def record_call(
        self,
        chat_id: int,
        number: int,
        winner_user_ids: list[int] | None = None,
    ) -> bool:
        game = self.get_game(chat_id)
        if game is None or game["status"] != "active":
            return False
        index = len(game["called_numbers"])
        if index >= len(game["draw_order"]) or game["draw_order"][index] != number:
            return False

        called_numbers = [*game["called_numbers"], number]
        winners = winner_user_ids or []
        status = "finished" if winners else "active"

        with self._connect() as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE games
                    SET called_numbers = ?, status = ?, winner_user_ids = ?
                    WHERE chat_id = ? AND status = 'active'
                    """,
                    (
                        json.dumps(called_numbers),
                        status,
                        json.dumps(winners),
                        chat_id,
                    ),
                )
        return cursor.rowcount == 1

    def finish_game(self, chat_id: int, winner_user_ids: list[int]) -> bool:
        with self._connect() as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE games
                    SET status = 'finished', winner_user_ids = ?
                    WHERE chat_id = ? AND status = 'active'
                    """,
                    (json.dumps(winner_user_ids), chat_id),
                )
        return cursor.rowcount == 1

    def list_active_games(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM games WHERE status = 'active'"
            ).fetchall()
        return [self._decode_game(row) for row in rows if row is not None]
