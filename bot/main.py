"""Telegram game commands and application construction."""

from __future__ import annotations

import logging
import os
from html import escape
from typing import Any

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    JobQueue,
)

from bot.game import create_draw_order, find_winners, format_card, generate_card
from bot.store import GameStore

logger = logging.getLogger("bongo")
GROUP_TYPES = {"group", "supergroup"}
DEFAULT_DRAW_INTERVAL = 12
MIN_DRAW_INTERVAL = 3
MAX_DRAW_INTERVAL = 600


class SecretRedactionFilter(logging.Filter):
    """Redact the bot token from library logs and exception traces."""

    def __init__(self, secret: str) -> None:
        super().__init__()
        self.secret = secret

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.secret:
            return True
        message = record.getMessage()
        if self.secret in message:
            record.msg = message.replace(self.secret, "[REDACTED]")
            record.args = ()
        if record.exc_info:
            formatted_exception = logging.Formatter().formatException(record.exc_info)
            if self.secret in formatted_exception:
                record.exc_text = formatted_exception.replace(self.secret, "[REDACTED]")
                record.exc_info = None
        return True


def _store(context: ContextTypes.DEFAULT_TYPE) -> GameStore:
    return context.application.bot_data["store"]


def _is_group(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type in GROUP_TYPES


async def _reply(update: Update, text: str) -> None:
    message = update.effective_message
    if message is not None:
        await message.reply_text(text)


async def _require_group(update: Update) -> bool:
    if _is_group(update):
        return True
    await _reply(update, "Use this command in the Telegram group where you are playing.")
    return False


async def _is_group_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
    except TelegramError:
        logger.exception("Could not check a group administrator.")
        await _reply(
            update,
            "I could not verify group permissions. Please try again or check that I can access group members.",
        )
        return False

    if member.status not in {"administrator", "creator"}:
        await _reply(update, "Only a Telegram group administrator can start the game.")
        return False
    return True


def _card_message(
    display_name: str,
    card: list[list[int | None]],
    called_numbers: list[int],
) -> str:
    return (
        f"Your Bongo card, {escape(display_name)}:\n"
        f"<pre>{format_card(card, called_numbers)}</pre>"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if _is_group(update):
        await _reply(
            update,
            "Welcome to free-play Traditional Ethiopian Bongo. "
            "Use /join to enter this group's next round. Use /help to see every command.",
        )
    else:
        await _reply(
            update,
            "Welcome to Traditional Ethiopian Bongo. Add me to a group, "
            "send /start here once so I can deliver your card privately, "
            "then use /join in the group. Free play only: no betting or cash prizes.",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        "Traditional Ethiopian Bongo — free play only\n\n"
        "/start — introduction and private-card setup\n"
        "/join — join this group's next round and receive a random card\n"
        "/card — send your card privately or view it here in a private chat\n"
        "/players — list players in this group\n"
        "/startgame — start the round (group administrators only)\n"
        "/numbers — show every number called so far\n"
        "/check — verify your card against called numbers\n"
        "/help — show this command list\n\n"
        "Numbers are drawn automatically one at a time. A completed row of "
        "five numbers wins; the bot checks every card after each draw. "
        "No betting, entry fees, or cash prizes.",
    )


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group(update):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return

    store = _store(context)
    game = store.get_or_create_waiting_game(chat.id)
    if game["status"] != "waiting":
        await _reply(update, "A round is already in progress. Join after it finishes.")
        return

    player_card = generate_card()
    added = store.add_player(
        chat.id,
        user.id,
        user.full_name,
        player_card,
    )
    if not added:
        await _reply(update, f"{user.full_name}, you are already in this round. Use /card to get your card.")
        return

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=_card_message(user.full_name, player_card, []),
            parse_mode="HTML",
        )
        await _reply(update, f"{user.full_name} joined. Your card was sent privately.")
    except TelegramError:
        await _reply(
            update,
            f"{user.full_name} joined. Open this bot in a private chat and send /start, "
            "then use /card here to receive your card privately.",
        )


async def card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        return

    store = _store(context)
    if chat.type in GROUP_TYPES:
        player = store.get_player(chat.id, user.id)
        if player is None:
            await _reply(update, "You have not joined this round yet. Use /join first.")
            return
        game = store.get_game(chat.id)
        called = game["called_numbers"] if game else []
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=_card_message(user.full_name, player["card"], called),
                parse_mode="HTML",
            )
            await _reply(update, f"{user.full_name}, I sent your card privately.")
        except TelegramError:
            await _reply(
                update,
                "I could not send a private message. Open this bot in a private chat, "
                "send /start, then use /card in the group again.",
            )
        return

    await _reply(
        update,
        "For a private card, use /card in the group where you joined. "
        "That tells me which group's card to send.",
    )


async def players(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group(update):
        return
    chat = update.effective_chat
    if chat is None:
        return
    store = _store(context)
    roster = store.list_players(chat.id)
    game = store.get_game(chat.id)
    status = game["status"] if game else "waiting"
    if not roster:
        await _reply(update, f"No players have joined yet. Round status: {status}. Use /join.")
        return

    names = "\n".join(
        f"{index}. {player['display_name']}"
        for index, player in enumerate(roster, start=1)
    )
    await _reply(update, f"Players ({len(roster)}) — {status}:\n{names}")


def _job_name(chat_id: int) -> str:
    return f"bongo-draw-{chat_id}"


def _schedule_draw(job_queue: JobQueue, chat_id: int, interval: int) -> None:
    for existing_job in job_queue.get_jobs_by_name(_job_name(chat_id)):
        existing_job.schedule_removal()
    job_queue.run_repeating(
        draw_next_number,
        interval=interval,
        first=interval,
        chat_id=chat_id,
        name=_job_name(chat_id),
        job_kwargs={"max_instances": 1},
    )


async def start_game(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await _require_group(update):
        return
    if not await _is_group_admin(update, context):
        return

    chat = update.effective_chat
    if chat is None:
        return
    store = _store(context)
    game = store.get_game(chat.id)
    if game is None or game["status"] == "waiting":
        roster = store.list_players(chat.id)
    else:
        roster = []

    if game is None:
        await _reply(update, "No round is ready. Ask players to use /join first.")
        return
    if game["status"] == "active":
        await _reply(update, "This round has already started.")
        return
    if game["status"] == "finished":
        await _reply(update, "The previous round is over. Use /join to open the next round.")
        return
    if not roster:
        await _reply(update, "No players have joined. Ask players to use /join first.")
        return

    try:
        interval = int(os.getenv("DRAW_INTERVAL_SECONDS", str(DEFAULT_DRAW_INTERVAL)))
    except ValueError:
        interval = DEFAULT_DRAW_INTERVAL
    interval = max(MIN_DRAW_INTERVAL, min(interval, MAX_DRAW_INTERVAL))

    started = store.start_game(chat.id, create_draw_order(), interval)
    if not started:
        await _reply(update, "I could not start this round. Please try /startgame again.")
        return

    job_queue = context.application.job_queue
    if job_queue is None:
        store.finish_game(chat.id, [])
        await _reply(update, "Automatic number calling is unavailable. Please check the bot setup.")
        return
    _schedule_draw(job_queue, chat.id, interval)
    await _reply(
        update,
        f"The round has started with {len(roster)} player(s). "
        f"I will call one number every {interval} seconds and check every card automatically.",
    )


async def numbers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group(update):
        return
    chat = update.effective_chat
    if chat is None:
        return
    game = _store(context).get_game(chat.id)
    if game is None or not game["called_numbers"]:
        await _reply(update, "No numbers have been called yet.")
        return

    called = game["called_numbers"]
    history = ", ".join(str(number) for number in called)
    await _reply(
        update,
        f"Numbers called ({len(called)}):\n{history}\n"
        f"Round status: {game['status']}.",
    )


def _winner_announcement(winners: list[dict[str, Any]], number: int) -> str:
    names = "\n".join(f"- {player['display_name']}" for player in winners)
    label = "winner" if len(winners) == 1 else "winners"
    return (
        f"Number {number} called.\n"
        f"BONGO! Verified {label}:\n{names}\n"
        "A complete row of five was confirmed. This was a free-play round."
    )


async def draw_next_number(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    if job is None or job.chat_id is None:
        return
    chat_id = job.chat_id
    store: GameStore = context.application.bot_data["store"]
    game = store.get_game(chat_id)
    if game is None or game["status"] != "active":
        job.schedule_removal()
        return

    number = store.peek_next_number(chat_id)
    if number is None:
        await context.bot.send_message(
            chat_id=chat_id,
            text="The number board is complete. The round has ended.",
        )
        store.finish_game(chat_id, [])
        job.schedule_removal()
        return

    prospective_calls = [*game["called_numbers"], number]
    roster = store.list_players(chat_id)
    winners = find_winners(roster, prospective_calls)
    winner_ids = [player["user_id"] for player in winners]

    if winners:
        message = _winner_announcement(winners, number)
    else:
        message = f"Number called: {number}"

    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
    except TelegramError:
        logger.exception("Could not deliver a called number to a group.")
        return

    if not store.record_call(chat_id, number, winner_ids):
        logger.warning("A number could not be recorded for chat %s.", chat_id)
        return
    if winners:
        job.schedule_removal()


async def check_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group(update):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return

    store = _store(context)
    game = store.get_game(chat.id)
    if game is None or game["status"] == "waiting":
        await _reply(update, "There is no active round to check.")
        return
    player = store.get_player(chat.id, user.id)
    if player is None:
        await _reply(update, "You are not in this round. Use /join before the game starts.")
        return
    if game["status"] == "finished":
        if user.id in game["winner_user_ids"]:
            await _reply(update, f"{user.full_name}, your win has already been verified.")
        else:
            await _reply(update, "This round is already finished.")
        return

    winners = find_winners([player], game["called_numbers"])
    if not winners:
        marked = sum(
            number is not None and number in set(game["called_numbers"])
            for row in player["card"]
            for number in row
        )
        await _reply(
            update,
            f"Your card is not a winner yet. {marked} of 15 numbers have been called.",
        )
        return

    winner_ids = [player["user_id"]]
    store.finish_game(chat.id, winner_ids)
    job_queue = context.application.job_queue
    if job_queue is not None:
        for job in job_queue.get_jobs_by_name(_job_name(chat.id)):
            job.schedule_removal()
    await context.bot.send_message(
        chat_id=chat.id,
        text=_winner_announcement(winners, game["called_numbers"][-1]),
    )


async def _resume_active_games(application: Application) -> None:
    store: GameStore = application.bot_data["store"]
    job_queue = application.job_queue
    if job_queue is None:
        logger.error("Job queue is unavailable; active rounds cannot resume.")
        return
    for game in store.list_active_games():
        _schedule_draw(job_queue, game["chat_id"], game["draw_interval"])
        logger.info("Resumed an active Bongo round for chat %s.", game["chat_id"])


def create_application(token: str, store: GameStore) -> Application:
    """Build the bot and register all public Telegram commands."""
    application = Application.builder().token(token).build()
    application.bot_data["store"] = store

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("card", card))
    application.add_handler(CommandHandler("players", players))
    application.add_handler(CommandHandler("startgame", start_game))
    application.add_handler(CommandHandler("numbers", numbers))
    application.add_handler(CommandHandler("check", check_card))
    return application
