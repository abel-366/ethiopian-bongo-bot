# Ethiopian Bongo Telegram Bot

A free-play Telegram group bot for Traditional Ethiopian Bongo. It creates 90-ball cards, calls numbers, tracks the round, and verifies a completed row automatically. No betting or cash prizes.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm --filter @workspace/bongo-bot run dev` — run the setup and command guide
- `uv run python -m bot.main` — run the Telegram polling bot
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required secret: `TELEGRAM_BOT_TOKEN`
- Optional environment: `DRAW_INTERVAL_SECONDS` (default 12), `BOT_DB_PATH` (default `data/bongo.sqlite3`)

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `bot/` — Python Telegram bot and Bongo game logic
- `README.md` — setup, commands, and deployment instructions
- `artifacts/bongo-bot/` — web setup guide
- `lib/api-spec/openapi.yaml` — shared API contract

## Architecture decisions

- A game uses a 90-ball, 3-by-9 card with 15 numbers and a horizontal five-number row as the winning pattern.
- Round state is stored in SQLite so active games and cards survive process restarts when the deployment provides persistent disk.
- The Telegram bot uses long polling; its process must run continuously and separately from the static web guide.
- The bot token is read only from the `TELEGRAM_BOT_TOKEN` environment secret.

## Product

Players join group rounds, receive their cards privately, and see numbers called one at a time. Group admins start rounds; the bot checks all cards after every call and announces the first verified row winner.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

_Populate as you build — sharp edges, "always run X before Y" rules._

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
