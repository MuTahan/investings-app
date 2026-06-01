"""Notification channels. Fans out to every configured channel (ntfy + Telegram).

A channel is only active when its env config is present, so you can enable either,
both, or neither. The in-app feed (notification_log) is handled separately and is
always recorded regardless of external channels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger("notifications")


@dataclass
class Notification:
    title: str
    body: str
    priority: str = "normal"  # low | normal | high | critical
    tag: str | None = None  # e.g. the symbol
    click_url: str | None = None


class Notifier(Protocol):
    name: str

    async def send(self, n: Notification) -> bool: ...


# ntfy priority is 1 (min) .. 5 (max)
_NTFY_PRIORITY = {"low": "2", "normal": "3", "high": "4", "critical": "5"}


class NtfyNotifier:
    name = "ntfy"

    def __init__(self, server: str, topic: str, client: httpx.AsyncClient) -> None:
        self._url = f"{server.rstrip('/')}/{topic}"
        self._client = client

    async def send(self, n: Notification) -> bool:
        headers = {
            "Title": n.title,
            "Priority": _NTFY_PRIORITY.get(n.priority, "3"),
        }
        if n.tag:
            headers["Tags"] = n.tag
        if n.click_url:
            headers["Click"] = n.click_url
        try:
            resp = await self._client.post(
                self._url, content=n.body.encode("utf-8"), headers=headers, timeout=10.0
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.info("ntfy_send_failed", extra={"error": str(exc)})
            return False


class TelegramNotifier:
    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str, client: httpx.AsyncClient) -> None:
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._chat_id = chat_id
        self._client = client

    async def send(self, n: Notification) -> bool:
        text = f"*{n.title}*\n{n.body}"
        if n.click_url:
            text += f"\n{n.click_url}"
        try:
            resp = await self._client.post(
                self._url,
                json={"chat_id": self._chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.info("telegram_send_failed", extra={"error": str(exc)})
            return False


class CompositeNotifier:
    name = "composite"

    def __init__(self, channels: list[Notifier]) -> None:
        self._channels = channels

    @property
    def channels(self) -> list[str]:
        return [c.name for c in self._channels]

    async def send(self, n: Notification) -> bool:
        results = [await c.send(n) for c in self._channels]
        return any(results)


def build_notifier(settings: Settings, client: httpx.AsyncClient) -> CompositeNotifier:
    channels: list[Notifier] = []
    if settings.ntfy_topic:
        channels.append(NtfyNotifier(settings.ntfy_server, settings.ntfy_topic, client))
    if settings.telegram_bot_token and settings.telegram_chat_id:
        channels.append(
            TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, client)
        )
    return CompositeNotifier(channels)
