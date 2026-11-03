from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from bot.game import create_draw_order, find_winners, generate_card
from bot.main import (
    card as card_command,
    check_card,
    create_application,
    draw_next_number,
    help_command,
    join,
    numbers,
    players,
    start,
    start_game,
)
from bot.store import GameStore


class BongoCardTests(unittest.TestCase):
    def test_generated_cards_follow_90_ball_ticket_shape(self) -> None:
        column_ranges = [
            range(1, 10),
            range(10, 20),
            range(20, 30),
            range(30, 40),
            range(40, 50),
            range(50, 60),
            range(60, 70),
            range(70, 80),
            range(80, 91),
        ]

        for seed in range(100):
            card = generate_card(random.Random(seed))
            self.assertEqual(len(card), 3)
            self.assertTrue(all(len(row) == 9 for row in card))
            self.assertTrue(
                all(sum(value is not None for value in row) == 5 for row in card)
            )

            values = [
                value
                for row in card
                for value in row
                if value is not None
            ]
            self.assertEqual(len(values), 15)
            self.assertEqual(len(values), len(set(values)))

            for column, number_range in enumerate(column_ranges):
                column_values = [
                    card[row][column]
                    for row in range(3)
                    if card[row][column] is not None
                ]
                self.assertLessEqual(len(column_values), 3)
                self.assertEqual(column_values, sorted(column_values))
                self.assertTrue(all(value in number_range for value in column_values))

    def test_draw_order_contains_each_number_once(self) -> None:
        draw_order = create_draw_order(random.Random(41))
        self.assertEqual(len(draw_order), 90)
        self.assertEqual(sorted(draw_order), list(range(1, 91)))

    def test_completed_row_wins_but_incomplete_row_does_not(self) -> None:
        card = generate_card(random.Random(12))
        player = {"user_id": 4, "card": card}
        row_numbers = [value for value in card[1] if value is not None]

        self.assertEqual(find_winners([player], row_numbers[:-1]), [])
        self.assertEqual(find_winners([player], row_numbers), [player])

    def test_simultaneous_winners_are_all_returned(self) -> None:
        card = generate_card(random.Random(19))
        players = [
            {"user_id": 10, "card": card},
            {"user_id": 20, "card": card},
        ]
        called = [value for value in card[0] if value is not None]

        self.assertEqual(find_winners(players, called), players)


class GameStoreTests(unittest.TestCase):
    def test_round_and_cards_survive_reopening_the_database(self) -> None:
        card = generate_card(random.Random(22))
        draw_order = [13, 7, *[number for number in range(1, 91) if number not in {7, 13}]]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bongo.sqlite3"
            first_store = GameStore(str(path))
            game = first_store.get_or_create_waiting_game(-100123)
            self.assertEqual(game["status"], "waiting")
            self.assertTrue(first_store.add_player(-100123, 8, "Aster", card))
            self.assertFalse(first_store.add_player(-100123, 8, "Aster", card))
            self.assertTrue(first_store.start_game(-100123, draw_order, 12))
            self.assertEqual(first_store.peek_next_number(-100123), 13)
            self.assertFalse(first_store.record_call(-100123, 7))
            self.assertTrue(first_store.record_call(-100123, 13))

            reopened_store = GameStore(str(path))
            restored_game = reopened_store.get_game(-100123)
            restored_player = reopened_store.get_player(-100123, 8)

            self.assertIsNotNone(restored_game)
            self.assertEqual(restored_game["called_numbers"], [13])
            self.assertEqual(restored_game["status"], "active")
            self.assertEqual(restored_player["card"], card)
            self.assertEqual(len(reopened_store.list_active_games()), 1)

    def test_finished_round_can_start_cleanly_with_new_players(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = GameStore(str(Path(directory) / "bongo.sqlite3"))
            card = generate_card(random.Random(7))
            store.get_or_create_waiting_game(-100555)
            store.add_player(-100555, 9, "Mekdes", card)
            store.start_game(-100555, list(range(1, 91)), 12)
            self.assertTrue(store.record_call(-100555, 1, [9]))
            self.assertEqual(store.get_game(-100555)["status"], "finished")

            new_game = store.get_or_create_waiting_game(-100555)
            self.assertEqual(new_game["status"], "waiting")
            self.assertEqual(new_game["called_numbers"], [])
            self.assertEqual(store.list_players(-100555), [])


class _FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


def _fake_update(message: _FakeMessage | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=-100123, type="supergroup"),
        effective_user=SimpleNamespace(id=8, full_name="Aster Bekele"),
        effective_message=message or _FakeMessage(),
    )


def _fake_context(
    store: GameStore,
    bot: SimpleNamespace | None = None,
    job_queue: SimpleNamespace | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        application=SimpleNamespace(
            bot_data={"store": store},
            job_queue=job_queue,
        ),
        bot=bot or SimpleNamespace(send_message=AsyncMock()),
    )


class TelegramCommandTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.store = GameStore(
            str(Path(self.temp_directory.name) / "bongo.sqlite3")
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_application_registers_all_requested_commands(self) -> None:
        application = create_application("12345:test-token", self.store)
        registered: set[str] = set()
        for group in application.handlers.values():
            for handler in group:
                registered.update(getattr(handler, "commands", set()))

        self.assertEqual(
            registered,
            {
                "start",
                "join",
                "card",
                "players",
                "startgame",
                "numbers",
                "check",
                "help",
            },
        )

    async def test_start_and_help_return_useful_instructions(self) -> None:
        update = _fake_update()
        context = _fake_context(self.store)

        await start(update, context)
        await help_command(update, context)

        self.assertIn("/join", update.effective_message.replies[0])
        help_text = update.effective_message.replies[1]
        for command in (
            "/start",
            "/join",
            "/card",
            "/players",
            "/startgame",
            "/numbers",
            "/check",
            "/help",
        ):
            self.assertIn(command, help_text)

    async def test_join_creates_a_card_and_sends_it_privately(self) -> None:
        update = _fake_update()
        bot = SimpleNamespace(send_message=AsyncMock())

        await join(update, _fake_context(self.store, bot=bot))

        player = self.store.get_player(-100123, 8)
        self.assertIsNotNone(player)
        bot.send_message.assert_awaited_once()
        self.assertEqual(bot.send_message.await_args.kwargs["chat_id"], 8)
        self.assertIn("BONGO CARD", bot.send_message.await_args.kwargs["text"])
        self.assertIn("joined", update.effective_message.replies[0])

    async def test_card_players_numbers_and_check_commands(self) -> None:
        card_values = generate_card(random.Random(32))
        self.store.get_or_create_waiting_game(-100123)
        self.store.add_player(-100123, 8, "Aster Bekele", card_values)
        self.store.start_game(-100123, list(range(1, 91)), 12)
        self.store.record_call(-100123, 1)

        update = _fake_update()
        bot = SimpleNamespace(send_message=AsyncMock())
        context = _fake_context(self.store, bot=bot)
        await card_command(update, context)
        await players(update, context)
        await numbers(update, context)
        await check_card(update, context)

        self.assertEqual(bot.send_message.await_args.kwargs["chat_id"], 8)
        self.assertIn("Aster Bekele", update.effective_message.replies[1])
        self.assertIn("Numbers called (1):\n1", update.effective_message.replies[2])
        self.assertIn("not a winner yet", update.effective_message.replies[3])

    async def test_only_group_admin_can_start_and_schedule_a_round(self) -> None:
        self.store.get_or_create_waiting_game(-100123)
        self.store.add_player(
            -100123,
            8,
            "Aster Bekele",
            generate_card(random.Random(5)),
        )
        job_queue = SimpleNamespace(
            get_jobs_by_name=Mock(return_value=[]),
            run_repeating=Mock(),
        )
        bot = SimpleNamespace(
            get_chat_member=AsyncMock(
                return_value=SimpleNamespace(status="administrator")
            ),
            send_message=AsyncMock(),
        )
        update = _fake_update()

        await start_game(
            update,
            _fake_context(self.store, bot=bot, job_queue=job_queue),
        )

        self.assertEqual(self.store.get_game(-100123)["status"], "active")
        job_queue.run_repeating.assert_called_once()
        self.assertIn("round has started", update.effective_message.replies[0])

    async def test_non_admin_is_denied_startgame(self) -> None:
        bot = SimpleNamespace(
            get_chat_member=AsyncMock(
                return_value=SimpleNamespace(status="member")
            ),
            send_message=AsyncMock(),
        )
        update = _fake_update()

        await start_game(update, _fake_context(self.store, bot=bot))

        self.assertIn("Only a Telegram group administrator", update.effective_message.replies[0])

    async def test_automatic_draw_announces_verified_winner(self) -> None:
        ticket = generate_card(random.Random(65))
        winning_row = [value for value in ticket[0] if value is not None]
        draw_order = winning_row + [
            value for value in range(1, 91) if value not in winning_row
        ]
        self.store.get_or_create_waiting_game(-100123)
        self.store.add_player(-100123, 8, "Aster Bekele", ticket)
        self.store.start_game(-100123, draw_order, 12)

        job = SimpleNamespace(chat_id=-100123, schedule_removal=Mock())
        bot = SimpleNamespace(send_message=AsyncMock())
        context = SimpleNamespace(
            application=SimpleNamespace(bot_data={"store": self.store}),
            bot=bot,
            job=job,
        )

        for _ in winning_row:
            await draw_next_number(context)

        self.assertEqual(self.store.get_game(-100123)["status"], "finished")
        self.assertEqual(self.store.get_game(-100123)["winner_user_ids"], [8])
        self.assertIn("BONGO! Verified winner", bot.send_message.await_args.kwargs["text"])
        job.schedule_removal.assert_called_once()

    async def test_check_command_announces_a_verified_card(self) -> None:
        ticket = generate_card(random.Random(13))
        winning_row = [value for value in ticket[0] if value is not None]
        draw_order = winning_row + [
            value for value in range(1, 91) if value not in winning_row
        ]
        self.store.get_or_create_waiting_game(-100123)
        self.store.add_player(-100123, 8, "Aster Bekele", ticket)
        self.store.start_game(-100123, draw_order, 12)
        for number in winning_row:
            self.store.record_call(-100123, number)

        job = SimpleNamespace(schedule_removal=Mock())
        job_queue = SimpleNamespace(get_jobs_by_name=Mock(return_value=[job]))
        bot = SimpleNamespace(send_message=AsyncMock())
        update = _fake_update()

        await check_card(
            update,
            _fake_context(self.store, bot=bot, job_queue=job_queue),
        )

        self.assertEqual(self.store.get_game(-100123)["status"], "finished")
        bot.send_message.assert_awaited_once()
        self.assertIn("Verified winner", bot.send_message.await_args.kwargs["text"])
        job.schedule_removal.assert_called_once()


if __name__ == "__main__":
    unittest.main()
