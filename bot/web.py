"""FastAPI endpoints for receiving Telegram webhook updates."""

from __future__ import annotations

import hmac
import json
import logging
import os
import re
from collections.abc import Callable
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from telegram import Update
from telegram.ext import Application

from bot.main import (
    SecretRedactionFilter,
    _resume_active_games,
    create_application,
)
from bot.store import GameStore

logger = logging.getLogger("bongo.web")
WEBHOOK_PATH = "/telegram/webhook"
_WEBHOOK_SECRET_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,256}\Z")


def _configure_logging(bot_token: str) -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    redaction_filter = SecretRedactionFilter(bot_token)
    loggers = (
        logging.getLogger(),
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("uvicorn.access"),
        logging.getLogger("telegram"),
        logging.getLogger("httpx"),
        logging.getLogger("httpcore"),
    )
    for current_logger in loggers:
        for handler in current_logger.handlers:
            handler.addFilter(redaction_filter)


def create_app(
    *,
    application_factory: Callable[[str, GameStore], Any] | None = None,
    store_factory: Callable[[str], GameStore] = GameStore,
) -> FastAPI:
    """Create the webhook server; environment secrets are read at startup."""
    build_application = application_factory or create_application

    @asynccontextmanager
    async def lifespan(web_app: FastAPI):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is required. Add it to the service's secret settings."
            )

        webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        if webhook_secret and not _WEBHOOK_SECRET_PATTERN.fullmatch(webhook_secret):
            raise RuntimeError(
                "TELEGRAM_WEBHOOK_SECRET must use only letters, digits, underscores, "
                "or hyphens, and be at most 256 characters."
            )

        base_url = (
            os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or ""
        ).strip()
        if base_url and not webhook_secret:
            raise RuntimeError(
                "TELEGRAM_WEBHOOK_SECRET is required when configuring a public webhook."
            )

        database_path = os.getenv("BOT_DB_PATH", "data/bongo.sqlite3")
        store = store_factory(database_path)
        telegram_application = build_application(token, store)
        web_app.state.telegram_application = telegram_application
        web_app.state.webhook_secret = webhook_secret
        web_app.state.webhook_registered = False
        _configure_logging(token)

        initialized = False
        started = False
        try:
            await telegram_application.initialize()
            initialized = True
            await _resume_active_games(telegram_application)
            await telegram_application.start()
            started = True

            if base_url:
                parsed_url = urlsplit(base_url)
                if (
                    parsed_url.scheme != "https"
                    or not parsed_url.netloc
                    or parsed_url.path not in ("", "/")
                    or parsed_url.query
                    or parsed_url.fragment
                ):
                    raise RuntimeError(
                        "WEBHOOK_BASE_URL must be an HTTPS origin without a path."
                    )

                webhook_url = f"{base_url.rstrip('/')}{WEBHOOK_PATH}"
                registered = await telegram_application.bot.set_webhook(
                    url=webhook_url,
                    secret_token=webhook_secret,
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=False,
                )
                if not registered:
                    raise RuntimeError("Telegram did not accept the webhook URL.")
                web_app.state.webhook_registered = True
                logger.info("Telegram webhook registered at %s.", webhook_url)
            else:
                logger.warning(
                    "No public webhook URL is configured; webhook delivery is inactive."
                )

            yield
        finally:
            if started:
                await telegram_application.stop()
            if initialized:
                await telegram_application.shutdown()

    web_app = FastAPI(
        title="Traditional Ethiopian Bongo Telegram Bot",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    web_app.state.telegram_application = None
    web_app.state.webhook_secret = None
    web_app.state.webhook_registered = False

    @web_app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": "Traditional Ethiopian Bongo Telegram Bot",
            "health": "/health",
        }

    @web_app.get("/health")
    async def health(request: Request) -> dict[str, bool | str]:
        return {
            "status": "ok",
            "bot_initialized": request.app.state.telegram_application is not None,
            "webhook_registered": request.app.state.webhook_registered,
        }

    @web_app.post(WEBHOOK_PATH)
    async def telegram_webhook(request: Request) -> dict[str, bool]:
        expected_secret = request.app.state.webhook_secret
        if not expected_secret:
            raise HTTPException(
                status_code=503,
                detail="Webhook secret is not configured.",
            )

        provided_secret = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token", ""
        )
        if not hmac.compare_digest(provided_secret, expected_secret):
            raise HTTPException(status_code=403, detail="Invalid webhook secret.")

        telegram_application = request.app.state.telegram_application
        if telegram_application is None:
            raise HTTPException(status_code=503, detail="Bot is not initialized.")

        try:
            payload = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid JSON update.") from None
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Update must be a JSON object.")

        try:
            update = Update.de_json(payload, telegram_application.bot)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid Telegram update.") from None
        if update is None:
            raise HTTPException(status_code=400, detail="Invalid Telegram update.")

        await telegram_application.update_queue.put(update)
        return {"ok": True}

    return web_app


app = create_app()
