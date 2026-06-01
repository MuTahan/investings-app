from __future__ import annotations

import httpx

from app.config import Settings
from app.notifications.notifier import (
    CompositeNotifier,
    Notification,
    NtfyNotifier,
    TelegramNotifier,
    build_notifier,
)


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return httpx.Response(200, request=httpx.Request("POST", url))


async def test_ntfy_posts_to_topic_with_headers():
    client = FakeClient()
    notifier = NtfyNotifier("https://ntfy.sh", "my-topic", client)  # type: ignore[arg-type]
    ok = await notifier.send(
        Notification(title="AAPL: BUY", body="hi", priority="high", tag="AAPL")
    )
    assert ok
    call = client.calls[0]
    assert call["url"] == "https://ntfy.sh/my-topic"
    assert call["headers"]["Title"] == "AAPL: BUY"
    assert call["headers"]["Priority"] == "4"
    assert call["headers"]["Tags"] == "AAPL"


async def test_telegram_posts_message():
    client = FakeClient()
    notifier = TelegramNotifier("BOTTOKEN", "12345", client)  # type: ignore[arg-type]
    ok = await notifier.send(Notification(title="AAPL: BUY", body="hi"))
    assert ok
    call = client.calls[0]
    assert "botBOTTOKEN/sendMessage" in call["url"]
    assert call["json"]["chat_id"] == "12345"
    assert "AAPL: BUY" in call["json"]["text"]


async def test_composite_fans_out_and_reports_any_success():
    class Ch:
        def __init__(self, name, ok):
            self.name = name
            self.ok = ok
            self.count = 0

        async def send(self, n):
            self.count += 1
            return self.ok

    a, b = Ch("a", False), Ch("b", True)
    composite = CompositeNotifier([a, b])
    assert await composite.send(Notification(title="t", body="b")) is True
    assert a.count == 1 and b.count == 1


def test_build_notifier_enables_configured_channels():
    client = FakeClient()
    none = build_notifier(Settings(environment="test"), client)  # type: ignore[arg-type]
    assert none.channels == []

    both = build_notifier(
        Settings(
            environment="test",
            ntfy_topic="t",
            telegram_bot_token="x",
            telegram_chat_id="y",
        ),
        client,  # type: ignore[arg-type]
    )
    assert set(both.channels) == {"ntfy", "telegram"}
