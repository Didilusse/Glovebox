import asyncio
import json
import socket
import ssl
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr

from backend.services import notification_delivery as delivery


@pytest.mark.parametrize("url", [
    "https://example.com/hook?token=secret", "https://example.com:443/",
    "https://8.8.8.8/", "https://[2606:4700:4700::1111]/",
])
def test_valid_destination(url):
    assert delivery.validate_destination(url) == url


@pytest.mark.parametrize("url", [
    "http://example.com", "https://user:secret@example.com", "https://example.com/#",
    "https://example.com:444/", "https://example.com:/", "https://localhost/",
    "https://foo.localhost/", "https://127.0.0.1", "https://10.1.2.3",
    "https://169.254.169.254", "https://192.168.1.1", "https://100.64.0.1",
    "https://192.0.2.1", "https://224.0.0.1", "https://240.0.0.1",
    "https://[::1]", "https://[::]", "https://[fc00::1]", "https://[fe80::1]",
    "https://[::ffff:8.8.8.8]", "https://[2001:db8::1]", "https://[ff02::1]",
    "https://[fe80::1%25en0]", "https://example.com\r\nX: secret",
    "https://example.com\\@evil.com", "https://example.com./", "https://%65xample.com",
])
def test_invalid_destination(url):
    with pytest.raises(ValueError, match="^Invalid notification destination$"):
        delivery.validate_destination(url)


@pytest.mark.parametrize("host", ["discord.com", "discordapp.com"])
def test_discord_destination(host):
    delivery.validate_destination(f"https://{host}/api/webhooks/123/secret_token", discord=True)


@pytest.mark.parametrize("url", [
    "https://evil.com/api/webhooks/123/token", "https://discord.com.evil.com/api/webhooks/123/token",
    "https://discord.com/api/other", "https://discord.com/api/webhooks/",
    "https://discord.com/api/webhooks/123/token/../other",
])
def test_discord_restricts_endpoint(url):
    with pytest.raises(ValueError):
        delivery.validate_destination(url, discord=True)


def record(ip):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    address = (ip, 443, 0, 0) if family == socket.AF_INET6 else (ip, 443)
    return family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", address


@pytest.fixture
def https(monkeypatch):
    resolver = MagicMock()
    resolver.answers = ["8.8.8.8"]

    def resolve(_host, record_type, **_kwargs):
        if record_type == "A":
            return resolver.answers
        raise delivery.dns.resolver.NoAnswer

    resolver.resolve.side_effect = resolve
    monkeypatch.setattr(delivery.dns.resolver, "Resolver", MagicMock(return_value=resolver))
    connection = MagicMock()
    connection.getresponse.return_value.status = 204
    factory = MagicMock(return_value=connection)
    monkeypatch.setattr(delivery, "_PinnedHTTPSConnection", factory)
    return resolver.resolve, factory, connection


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.1", "100.64.0.1", "::1", "fc00::1", "192.0.2.1"])
def test_all_dns_results_must_be_public(https, ip):
    dns, factory, _ = https

    def resolve(_host, record_type, **_kwargs):
        if record_type == ("AAAA" if ":" in ip else "A"):
            return [ip]
        if record_type == "A":
            return ["8.8.8.8"]
        raise delivery.dns.resolver.NoAnswer

    dns.side_effect = resolve
    with pytest.raises(delivery.DeliveryError):
        asyncio.run(delivery.deliver("webhook", "https://example.com/secret", "Title", "Body"))
    factory.assert_not_called()


@pytest.mark.parametrize("channel", ["webhook", "discord"])
def test_post_payload_and_no_body_read(https, channel):
    dns, factory, connection = https
    url = "https://discord.com/api/webhooks/123/secret?wait=true"
    asyncio.run(delivery.deliver(channel, url, "Title", "@everyone Body"))
    factory.assert_called_once_with("discord.com", socket.AF_INET, ("8.8.8.8", 443))
    assert dns.call_count == 2
    assert all(0 < call.kwargs["lifetime"] <= delivery._DNS_TIMEOUT for call in dns.call_args_list)
    assert all(call.kwargs["search"] is False for call in dns.call_args_list)
    args, kwargs = connection.request.call_args
    assert args == ("POST", "/api/webhooks/123/secret?wait=true")
    payload = json.loads(kwargs["body"])
    assert payload == ({"title": "Title", "message": "@everyone Body"} if channel == "webhook"
                       else {"content": "Title\n@everyone Body", "allowed_mentions": {"parse": []}})
    connection.getresponse.return_value.read.assert_not_called()
    connection.getresponse.return_value.close.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.parametrize("status", [301, 302, 307, 308, 400, 500])
def test_redirects_and_errors_rejected(https, status):
    _, _, connection = https
    connection.getresponse.return_value.status = status
    with pytest.raises(delivery.DeliveryError, match="^Notification delivery failed$"):
        asyncio.run(delivery.deliver("webhook", "https://example.com/secret", "T", "M"))
    connection.request.assert_called_once()
    connection.close.assert_called_once()


def test_pinned_socket_preserves_tls_identity_and_host(monkeypatch):
    context = ssl.create_default_context()
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    tls = MagicMock(wrap_socket=MagicMock(return_value=MagicMock()))
    monkeypatch.setattr(delivery.ssl, "create_default_context", lambda: tls)
    raw = MagicMock()
    monkeypatch.setattr(delivery.socket, "socket", MagicMock(return_value=raw))
    dns = MagicMock(side_effect=AssertionError("Must not resolve during connect"))
    monkeypatch.setattr(delivery.socket, "getaddrinfo", dns)
    connection = delivery._PinnedHTTPSConnection("example.com", socket.AF_INET, ("8.8.8.8", 443))
    connection.request("POST", "/secret", body=b"{}")
    raw.connect.assert_called_once_with(("8.8.8.8", 443))
    raw.settimeout.assert_called_once_with(10)
    tls.wrap_socket.assert_called_once_with(raw, server_hostname="example.com")
    sent = b"".join(call.args[0] for call in connection.sock.sendall.call_args_list)
    assert b"Host: example.com\r\n" in sent
    dns.assert_not_called()


@pytest.fixture
def smtp(monkeypatch):
    monkeypatch.setattr(delivery, "settings", SimpleNamespace(
        smtp_host="smtp.example.com", smtp_port=587, smtp_username="user",
        smtp_password=SecretStr("super-secret"), smtp_from="sender@example.com", smtp_starttls=True,
    ))
    factory = MagicMock()
    client = factory.return_value.__enter__.return_value
    client.send_message.return_value = {}
    monkeypatch.setattr(delivery.smtplib, "SMTP", factory)
    return factory, client


def test_smtp_tls_and_credentials(smtp):
    factory, client = smtp
    asyncio.run(delivery.deliver("email", "user@example.com", "Title", "Message"))
    factory.assert_called_once_with("smtp.example.com", 587, timeout=10)
    context = client.starttls.call_args.kwargs["context"]
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    client.login.assert_called_once_with("user", "super-secret")
    email = client.send_message.call_args.args[0]
    assert email["Subject"] == "Title"
    assert email.get_content() == "Message\n"


@pytest.mark.parametrize("destination,title", [
    ("user@example.com\r\nBcc: other@example.com", "T"),
    ("user@example.com", "T\r\nBcc: other@example.com"),
    ("user@example.com,other@example.com", "T"),
])
def test_email_header_injection_rejected(smtp, destination, title):
    with pytest.raises(delivery.DeliveryError):
        asyncio.run(delivery.deliver("email", destination, title, "M"))
    smtp[0].assert_not_called()


def test_smtp_secret_failure_is_safe(smtp, caplog):
    smtp[1].login.side_effect = RuntimeError("super-secret")
    with pytest.raises(delivery.DeliveryError) as error:
        asyncio.run(delivery.deliver("email", "user@example.com", "T", "M"))
    assert str(error.value) == "Notification delivery failed"
    assert error.value.__suppress_context__
    assert "super-secret" not in caplog.text


def test_webhook_secret_failure_is_safe(https, caplog):
    https[2].request.side_effect = RuntimeError("https://example.com/secret-token")
    with pytest.raises(delivery.DeliveryError) as error:
        asyncio.run(delivery.deliver("webhook", "https://example.com/secret-token", "T", "M"))
    assert str(error.value) == "Notification delivery failed"
    assert "secret-token" not in caplog.text


def test_resource_limit(monkeypatch):
    monkeypatch.setattr(delivery, "_SLOTS", threading.BoundedSemaphore(0))
    with pytest.raises(delivery.DeliveryError):
        asyncio.run(delivery.deliver("webhook", "https://example.com", "T", "M"))


def test_unknown_channel():
    with pytest.raises(delivery.DeliveryError):
        asyncio.run(delivery.deliver("unknown", "destination", "T", "M"))


@pytest.mark.parametrize("cancel", [False, True])
def test_delayed_success_and_cancellation_keep_worker_slot(monkeypatch, cancel):
    slots = threading.BoundedSemaphore(1)
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    monkeypatch.setattr(delivery, "_SLOTS", slots)
    monkeypatch.setattr(delivery, "_TIMEOUT", 0.05)

    def blocked(*args):
        started.set()
        release.wait(2)
        finished.set()

    monkeypatch.setattr(delivery, "_send", blocked)

    async def exercise():
        task = asyncio.create_task(delivery.deliver("webhook", "https://example.com", "T", "M"))
        while not started.is_set():
            await asyncio.sleep(0.001)
        if cancel:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=1)
        else:
            # Exceed the socket timeout without reporting a still-running send as failed.
            await asyncio.sleep(0.15)
            assert not task.done()
        assert not slots.acquire(blocking=False)
        with pytest.raises(delivery.DeliveryError):
            await delivery.deliver("webhook", "https://example.com", "T", "M")
        release.set()
        if not cancel:
            assert await asyncio.wait_for(task, timeout=1) is None

    try:
        asyncio.run(exercise())
    finally:
        release.set()
        assert finished.wait(2)
        assert slots.acquire(timeout=2)
        slots.release()


def test_smtp_recipient_rejection(smtp):
    smtp[1].send_message.return_value = {"user@example.com": (550, b"Rejected")}
    with pytest.raises(delivery.DeliveryError):
        asyncio.run(delivery.deliver("email", "user@example.com", "T", "M"))


def test_unconfigured_smtp(smtp):
    delivery.settings.smtp_host = None
    with pytest.raises(delivery.DeliveryError):
        asyncio.run(delivery.deliver("email", "user@example.com", "T", "M"))
    smtp[0].assert_not_called()


def test_dns_failure_is_safe(https):
    https[0].side_effect = socket.gaierror("secret hostname")
    with pytest.raises(delivery.DeliveryError, match="^Notification delivery failed$"):
        asyncio.run(delivery.deliver("webhook", "https://example.com/secret", "T", "M"))
    https[1].assert_not_called()


def test_oversize_payload_rejected(https):
    with pytest.raises(delivery.DeliveryError):
        asyncio.run(delivery.deliver("webhook", "https://example.com", "T", "M" * 65537))
    https[0].assert_not_called()
