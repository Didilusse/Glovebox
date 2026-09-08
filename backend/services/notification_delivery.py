"""Notification delivery with pinned public HTTPS endpoints and bounded workers."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from email.headerregistry import Address
from email.message import EmailMessage
import http.client
import ipaddress
import json
import re
import smtplib
import socket
import ssl
import threading
from urllib.parse import urlsplit

from backend.config import settings


_TIMEOUT = 10
_MAX_PAYLOAD = 64 * 1024
_WORKERS = ThreadPoolExecutor(max_workers=4, thread_name_prefix="notification")
_SLOTS = threading.BoundedSemaphore(4)
_FAILURE = "Notification delivery failed"


class DeliveryError(Exception):
    """A delivery failure that is safe to expose without endpoint credentials."""


def _public_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return (
        address.is_global
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
        and not address.is_loopback
        and not address.is_link_local
        and not getattr(address, "ipv4_mapped", None)
        and not getattr(address, "sixtofour", None)
        and not getattr(address, "teredo", None)
    )


def validate_destination(value: str, discord: bool = False) -> str:
    """Validate a webhook URL without DNS; return it unchanged or raise ValueError.

    DNS is intentionally checked again at delivery time, then pinned for connect.
    """
    try:
        if not isinstance(value, str) or not value or len(value) > 4096:
            raise ValueError
        if any(ord(char) <= 32 or ord(char) >= 127 for char in value):
            raise ValueError
        if "#" in value or "\\" in value:
            raise ValueError
        parsed = urlsplit(value)
        host = parsed.hostname
        if (parsed.scheme != "https" or not host or parsed.username is not None
                or parsed.password is not None or parsed.port not in (None, 443)):
            raise ValueError
        if parsed.netloc.endswith(":") or "%" in host:
            raise ValueError
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if (len(host) > 253 or host.endswith(".")
                    or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                           for label in host.split("."))
                    or host == "localhost" or host.endswith(".localhost")):
                raise ValueError
        else:
            if not _public_ip(host):
                raise ValueError
        if discord and (host not in {"discord.com", "discordapp.com"}
                        or not re.fullmatch(r"/api/webhooks/[0-9]+/[A-Za-z0-9_-]+", parsed.path)):
            raise ValueError
    except Exception:
        raise ValueError("Invalid notification destination") from None
    return value


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, family: int, address: tuple):
        super().__init__(host, port=443, timeout=_TIMEOUT, context=ssl.create_default_context())
        self._family = family
        self._address = address

    def connect(self):
        # Connect a numeric sockaddr directly: never resolve the hostname a second time.
        raw = socket.socket(self._family, socket.SOCK_STREAM)
        try:
            raw.settimeout(_TIMEOUT)
            raw.connect(self._address)
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def _webhook(destination: str, title: str, message: str, discord: bool):
    parsed = urlsplit(validate_destination(destination, discord=discord))
    records = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM,
                                 proto=socket.IPPROTO_TCP)
    if not records or any(family not in (socket.AF_INET, socket.AF_INET6)
                          or not _public_ip(address[0])
                          for family, _, _, _, address in records):
        raise ValueError("Unsafe endpoint")
    family, _, _, _, address = records[0]
    payload = ({"content": title + "\n" + message, "allowed_mentions": {"parse": []}}
               if discord else {"title": title, "message": message})
    body = json.dumps(payload).encode("utf-8")
    if len(body) > _MAX_PAYLOAD:
        raise ValueError("Payload too large")
    connection = _PinnedHTTPSConnection(parsed.hostname, family, address)
    try:
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        connection.request("POST", target, body=body,
                           headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        try:
            if not 200 <= response.status < 300:
                raise ValueError("Unsuccessful response")
        finally:
            # No response content is needed; never consume an unbounded remote body.
            response.close()
    finally:
        connection.close()


def _email(destination: str, title: str, message: str):
    sender = settings.smtp_from
    if not settings.smtp_host or not sender:
        raise ValueError("SMTP is not configured")
    for value in (destination, sender, title):
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("Invalid email header")
    for value in (destination, sender):
        address = Address(addr_spec=value)
        if not address.username or not address.domain:
            raise ValueError("Invalid mailbox")
    email = EmailMessage()
    email["From"] = sender
    email["To"] = destination
    email["Subject"] = title
    email.set_content(message)
    if len(email.as_bytes()) > _MAX_PAYLOAD:
        raise ValueError("Payload too large")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=_TIMEOUT) as smtp:
        if settings.smtp_starttls:
            smtp.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            password = settings.smtp_password
            smtp.login(settings.smtp_username, password.get_secret_value() if password else "")
        if smtp.send_message(email, from_addr=sender, to_addrs=[destination]):
            raise ValueError("Recipient rejected")


def _send(channel: str, destination: str, title: str, message: str):
    try:
        if len(title.encode("utf-8")) + len(message.encode("utf-8")) > _MAX_PAYLOAD:
            raise ValueError("Payload too large")
        if channel in ("webhook", "discord"):
            _webhook(destination, title, message, channel == "discord")
        elif channel == "email":
            _email(destination, title, message)
        else:
            raise ValueError("Unknown channel")
    except Exception:
        raise DeliveryError(_FAILURE) from None


async def deliver(channel: str, destination: str, title: str, message: str) -> None:
    """Deliver once, or raise DeliveryError; no redirects, retries, or secret logging.

    At most four jobs can run, with no unbounded queue. Socket operations have
    a 10-second timeout, but there is no total deadline and DNS may stall.
    Cancellation propagates without releasing a running worker's capacity until
    it actually finishes; otherwise await its result to avoid premature retries.
    """
    if not _SLOTS.acquire(blocking=False):
        raise DeliveryError(_FAILURE)
    try:
        future = _WORKERS.submit(_send, channel, destination, title, message)
    except Exception:
        _SLOTS.release()
        raise DeliveryError(_FAILURE) from None
    future.add_done_callback(lambda _: _SLOTS.release())
    try:
        await asyncio.wrap_future(future)
    except Exception:
        raise DeliveryError(_FAILURE) from None
