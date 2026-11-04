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
4. Deploy or start the FastAPI webhook service using the instructions below.
5. In the group, players use `/join`. A random card is sent privately; use `/card` in the group to request it again.
6. A Telegram group administrator starts the game with `/startgame`.

Telegram sends updates to `POST /telegram/webhook`. The service registers this endpoint with Telegram when it starts with a public HTTPS URL. It also checks Telegram's `X-Telegram-Bot-Api-Secret-Token` header before accepting updates.

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
uv run uvicorn bot.web:app --host 0.0.0.0 --port ${PORT:-8000}
```

The workflow serves `/health`. To receive Telegram updates, the service also needs a public HTTPS URL in `WEBHOOK_BASE_URL` and `TELEGRAM_WEBHOOK_SECRET`. Publishing the separate web guide does not deploy this webhook service.

## Deploy a free Render Web Service

The included `render.yaml` defines a Python Web Service, the `/health` check, and the Uvicorn start command.

1. Push the repository to GitHub and create a Render Blueprint from it, or create a Python Web Service using `render.yaml`.
2. In Render's environment settings, enter the existing bot token as `TELEGRAM_BOT_TOKEN`. Do not put it in the repository or share it in chat.
3. Add `TELEGRAM_WEBHOOK_SECRET`. Generate a Telegram-compatible value with `python -c "import secrets; print(secrets.token_urlsafe(32))"` and paste it directly into Render's secret settings.
4. Render supplies `RENDER_EXTERNAL_URL`; the service uses it to register `https://<your-service>/telegram/webhook` automatically. The `/health` endpoint is the configured health check.
5. Keep one web-service instance for this bot token. Do not run long polling at the same time as the webhook.
6. Optionally set `DRAW_INTERVAL_SECONDS` to a whole number from 3 through 600. The default is 12 seconds.

### Free Render limitations

Render Free Web Services can sleep after 15 minutes without inbound traffic and take about a minute to wake. Their local filesystem is temporary, so SQLite game state is lost on sleep, restart, or redeploy. This is suitable for testing and hobby play, but not uninterrupted rounds or durable game history.

## Local setup

```bash
uv sync
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_WEBHOOK_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
# Set this to a public HTTPS origin when testing real Telegram deliveries.
export WEBHOOK_BASE_URL="https://your-public-host.example"
uv run uvicorn bot.web:app --host 0.0.0.0 --port "${PORT:-8000}"
```

Keep both values in a secret manager or environment variables. Do not put either in a committed `.env` file.

The health endpoint is `GET /health`; Telegram posts JSON updates to `POST /telegram/webhook`.

## Run the tests

```bash
uv run python -m unittest discover -s tests -v
```

## Project files

- `bot/main.py` — Telegram commands, group permissions, automatic draws, and announcements
- `bot/web.py` — FastAPI health and secured Telegram webhook endpoints
- `bot/game.py` — card generation, number draw order, and win verification
- `bot/store.py` — SQLite storage for groups, players, cards, and rounds
- `render.yaml` — Free Render Web Service blueprint
- `artifacts/bongo-bot/` — web-based setup and command guide
