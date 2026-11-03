# Traditional Ethiopian Bongo Telegram Bot

A free-play Telegram group bot for 90-ball Bongo. Players join a group round, receive a private randomized card, and follow automatic number calls. The bot checks every card after each call and announces a verified completed row.

**Free play only.** There are no bets, entry fees, cash prizes, or payment features.

## Game rules

- Each card has 3 rows and 9 columns, with 5 numbers per row (15 numbers total).
- Numbers range from 1 to 90. Numbers are unique on each card and ordered by column.
- The group administrator starts the round with `/startgame`.
- The bot calls one number at a time, every 12 seconds by default.
- A complete horizontal row of five called numbers wins. All cards are checked after each call; tied wins on the same call are announced together.
- Game cards, called numbers, and round status are stored in SQLite. Active rounds resume after a process restart if the database file is on persistent storage.

## Telegram setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.
2. Save the token as a secret named `TELEGRAM_BOT_TOKEN`. In Replit, use **Tools → Secrets**. Never paste the token into source code or commit it.
3. Add the bot to your Telegram group. Players should open the bot privately and send `/start` once so Telegram allows the bot to deliver private cards.
4. Start the bot process using the instructions below.
5. In the group, players use `/join`. A random card is sent privately; use `/card` in the group to request it again.
6. A Telegram group administrator starts the game with `/startgame`.

The bot uses long polling, so no public webhook URL is needed. It must remain running as a background process.

## Commands

| Command | What it does |
| --- | --- |
| `/start` | Introduces the bot and explains private-card setup |
| `/join` | Joins the group's waiting round and creates a random card |
| `/card` | Sends your group's card privately |
| `/players` | Lists players and round status |
| `/startgame` | Starts number calls; Telegram group administrators only |
| `/numbers` | Shows the complete call history |
| `/check` | Checks your card against the numbers already called |
| `/help` | Shows the command list and rules |

## Run in Replit

The project includes a workflow named **Ethiopian Bongo Telegram Bot**. Start it from the Workflows panel. It runs:

```bash
uv run python -m bot.main
```

The web guide and Telegram bot are separate processes. Publishing the web guide alone does not keep the bot online.

## Deploy the bot as a worker

Use a host that supports an always-on Python background worker:

1. Deploy this repository as a Python worker, not just as a static website.
2. Set the worker's start command to `uv run python -m bot.main` (or install `requirements.txt` and run `python -m bot.main`).
3. Add `TELEGRAM_BOT_TOKEN` in the host's secret/environment settings.
4. Set `BOT_DB_PATH` to a file path on persistent storage if rounds should survive redeploys. It defaults to `data/bongo.sqlite3`.
5. Keep one worker instance running. Telegram long polling should not be started by multiple replicas using the same bot token.
6. Optionally set `DRAW_INTERVAL_SECONDS` to a whole number from 3 through 600. The default is 12 seconds.

## Local setup

```bash
python -m pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your-token"
python -m bot.main
```

Keep the token in a secret manager or environment variable. Do not put it in a committed `.env` file.

## Project files

- `bot/main.py` — Telegram commands, group permissions, automatic draws, and announcements
- `bot/game.py` — card generation, number draw order, and win verification
- `bot/store.py` — SQLite storage for groups, players, cards, and rounds
- `artifacts/bongo-bot/` — web-based setup and command guide
