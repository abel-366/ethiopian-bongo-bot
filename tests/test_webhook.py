from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from telegram import Bot

from bot.store import GameStore
from bot.web import create_app


class _FakeTelegramApplication:
    def __init__(self, token: str, store: GameStore) -> None:
        self.bot = Bot(token)
        self.bot_data = {"store": store}
        self.job_queue = SimpleNamespace()
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.initialize = AsyncMock()
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.shutdown = AsyncMock()


class WebhookServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.store = GameStore(
            str(Path(self.temp_directory.name) / "bongo.sqlite3")
        )
        self.telegram_applications: list[_FakeTelegramApplication] = []

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _create_test_app(self) -> FastAPI:
        def factory(token: str, store: GameStore) -> _FakeTelegramApplication:
            telegram_app = _FakeTelegramApplication(token, store)
            self.telegram_applications.append(telegram_app)
            return telegram_app

        return create_app(
            application_factory=factory,
            store_factory=lambda _path: self.store,
        )

    @asynccontextmanager
    async def _client(self, app: FastAPI):
        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                yield client

    def _environment(self, **overrides: str) -> dict[str, str]:
        values = {
            "TELEGRAM_BOT_TOKEN": "12345:test-token",
            "TELEGRAM_WEBHOOK_SECRET": "test_webhook_secret_123",
            "RENDER_EXTERNAL_URL": "https://bongo.example",
            "BOT_DB_PATH": str(Path(self.temp_directory.name) / "bongo.sqlite3"),
        }
        values.update(overrides)
        return values

    async def test_startup_registers_render_webhook_and_health_is_ready(self) -> None:
        with patch.dict(os.environ, self._environment(), clear=True):
            with patch.object(
                Bot,
                "set_webhook",
                new_callable=AsyncMock,
                return_value=True,
            ) as set_webhook:
                app = self._create_test_app()
                async with self._client(app) as client:
                    response = await client.get("/health")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {
                        "status": "ok",
                        "bot_initialized": True,
                        "webhook_registered": True,
                    },
                )
                set_webhook.assert_awaited_once()
                self.assertEqual(
                    set_webhook.await_args.kwargs["url"],
                    "https://bongo.example/telegram/webhook",
                )
                self.assertEqual(
                    set_webhook.await_args.kwargs["secret_token"],
                    "test_webhook_secret_123",
                )
                telegram_app = self.telegram_applications[0]
                telegram_app.initialize.assert_awaited_once()
                telegram_app.start.assert_awaited_once()
                telegram_app.stop.assert_awaited_once()
                telegram_app.shutdown.assert_awaited_once()

    async def test_webhook_rejects_wrong_secret_and_queues_valid_update(self) -> None:
        with patch.dict(os.environ, self._environment(), clear=True):
            with patch.object(
                Bot,
                "set_webhook",
                new_callable=AsyncMock,
                return_value=True,
            ):
                app = self._create_test_app()
                async with self._client(app) as client:
                    rejected = await client.post(
                        "/telegram/webhook",
                        headers={
                            "X-Telegram-Bot-Api-Secret-Token": "wrong-secret"
                        },
                        json={"update_id": 41},
                    )
                    accepted = await client.post(
                        "/telegram/webhook",
                        headers={
                            "X-Telegram-Bot-Api-Secret-Token": "test_webhook_secret_123"
                        },
                        json={"update_id": 42},
                    )

                self.assertEqual(rejected.status_code, 403)
                self.assertEqual(accepted.status_code, 200)
                self.assertEqual(accepted.json(), {"ok": True})
                queued_update = self.telegram_applications[0].update_queue.get_nowait()
                self.assertEqual(queued_update.update_id, 42)

    async def test_unconfigured_webhook_does_not_accept_updates(self) -> None:
        environment = self._environment()
        environment.pop("TELEGRAM_WEBHOOK_SECRET")
        environment.pop("RENDER_EXTERNAL_URL")
        with patch.dict(os.environ, environment, clear=True):
            app = self._create_test_app()
            async with self._client(app) as client:
                health = await client.get("/health")
                response = await client.post(
                    "/telegram/webhook",
                    json={"update_id": 43},
                )

        self.assertEqual(health.status_code, 200)
        self.assertFalse(health.json()["webhook_registered"])
        self.assertEqual(response.status_code, 503)

    async def test_public_webhook_requires_a_secret(self) -> None:
        environment = self._environment()
        environment.pop("TELEGRAM_WEBHOOK_SECRET")
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(RuntimeError, "TELEGRAM_WEBHOOK_SECRET"):
                async with self._client(self._create_test_app()):
                    pass

    async def test_bad_json_is_rejected(self) -> None:
        with patch.dict(os.environ, self._environment(), clear=True):
            with patch.object(
                Bot,
                "set_webhook",
                new_callable=AsyncMock,
                return_value=True,
            ):
                app = self._create_test_app()
                async with self._client(app) as client:
                    response = await client.post(
                        "/telegram/webhook",
                        headers={
                            "X-Telegram-Bot-Api-Secret-Token": "test_webhook_secret_123",
                            "content-type": "application/json",
                        },
                        content="{invalid",
                    )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
