# -*- coding: utf-8 -*-
#
# Iris - Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the
# GNU Affero General Public License in LICENSE for details.
#
# A commercial licence, without the AGPL obligations, is available for use in
# proprietary or closed-source products - see COMMERCIAL-LICENSE.md.
"""Message composition and SMTP delivery.

Like the rest of the package this module is independent from Tkinter, so the
sending logic can be tested and reused without a graphical interface.
"""

import mimetypes
import os
import smtplib
import socket
import time
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Callable, List, Optional, Sequence, Tuple

from .i18n import t
from .parsers import Recipient, is_valid_email

Logger = Optional[Callable[[str], None]]

#: Supported connection types.
CONNECTION_SSL = "ssl"
CONNECTION_STARTTLS = "starttls"
CONNECTION_NONE = "none"
CONNECTION_TYPES = (CONNECTION_SSL, CONNECTION_STARTTLS, CONNECTION_NONE)

#: Placeholder replaced with the recipient company name.
#: ``{AZIENDA}`` is the pre-2.0 Italian spelling, still accepted so existing
#: templates keep working.
COMPANY_PLACEHOLDERS = ("{COMPANY}", "{AZIENDA}")

DEFAULT_TIMEOUT = 30


class MailConfigError(ValueError):
    """The email configuration is incomplete or invalid."""


@dataclass
class SmtpSettings:
    """SMTP connection parameters."""

    host: str = ""
    port: int = 0
    connection_type: str = CONNECTION_STARTTLS
    username: str = ""
    password: str = ""
    timeout: int = DEFAULT_TIMEOUT
    #: Seconds to wait between one message and the next. Providers that rate
    #: limit a sender are much happier with a small pause than with a burst.
    #: A negative value marks input that could not be read as a number.
    send_delay: float = 0.0

    @property
    def use_auth(self) -> bool:
        """True when complete credentials were provided."""
        return bool(self.username.strip() and self.password.strip())


def render_template(text: str, company: str) -> str:
    """Replace every supported company placeholder in ``text``."""
    rendered = text or ""
    for placeholder in COMPANY_PLACEHOLDERS:
        rendered = rendered.replace(placeholder, company)
    return rendered


@dataclass
class EmailTemplate:
    """Email template, with the placeholders to substitute."""

    sender: str = ""
    subject: str = ""
    body: str = ""
    attachments: List[str] = field(default_factory=list)

    def render_subject(self, company: str) -> str:
        return render_template(self.subject, company)

    def render_body(self, company: str) -> str:
        return render_template(self.body, company)


def validate_settings(settings: SmtpSettings, template: EmailTemplate) -> List[str]:
    """Return the list of configuration errors (empty when valid)."""
    errors: List[str] = []

    if not template.sender.strip():
        errors.append(t("validate.sender_missing"))
    elif not is_valid_email(template.sender):
        errors.append(t("validate.sender_invalid", value=template.sender))

    if not settings.host.strip():
        errors.append(t("validate.host_missing"))

    if not settings.port:
        errors.append(t("validate.port_missing"))
    elif not 1 <= settings.port <= 65535:
        errors.append(t("validate.port_range", value=settings.port))

    if settings.connection_type not in CONNECTION_TYPES:
        errors.append(t("validate.connection_invalid", value=settings.connection_type))

    username = settings.username.strip()
    password = settings.password.strip()
    if bool(username) != bool(password):
        errors.append(t("validate.credentials"))

    if settings.send_delay < 0:
        errors.append(t("validate.delay_invalid"))

    if not template.subject.strip():
        errors.append(t("validate.subject_missing"))

    if not template.body.strip():
        errors.append(t("validate.body_missing"))

    for path in template.attachments:
        if path and not os.path.exists(path):
            errors.append(t("validate.attachment_missing", path=path))

    return errors


def parse_port(value, default: int = 0) -> int:
    """Convert a port to an integer without raising."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_delay(value) -> float:
    """Convert the pause between messages to seconds, without raising.

    An empty field means "no pause"; text that is not a number comes back as
    ``-1.0`` so :func:`validate_settings` can report it instead of silently
    sending a batch at full speed.
    """
    text = str(value if value is not None else "").strip().replace(",", ".")
    if not text:
        return 0.0
    try:
        return float(text)
    except (TypeError, ValueError):
        return -1.0


def format_delay(seconds: float) -> str:
    """Format a delay for the log: ``1.0`` becomes ``1``, ``0.5`` stays ``0.5``."""
    return f"{seconds:g}"


def attach_file(message: EmailMessage, path: str) -> None:
    """Attach a file to the message, guessing its MIME type."""
    filename = os.path.basename(path)
    content_type, encoding = mimetypes.guess_type(path)
    if content_type is None or encoding is not None:
        content_type = "application/octet-stream"
    maintype, subtype = content_type.split("/", 1)
    with open(path, "rb") as handle:
        data = handle.read()
    message.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)


def build_message(
    template: EmailTemplate,
    recipient: Recipient,
    log: Logger = None,
) -> EmailMessage:
    """Build the MIME message for one recipient.

    Uses :class:`email.message.EmailMessage`, which encodes both headers
    (RFC 2047) and body as UTF-8 — required for any non-ASCII text.
    """
    if not template.sender.strip():
        raise MailConfigError(t("validate.sender_required"))
    if not is_valid_email(recipient.email):
        raise MailConfigError(t("validate.recipient_invalid", value=recipient.email))

    message = EmailMessage()
    message["From"] = template.sender.strip()
    message["To"] = recipient.email
    message["Subject"] = template.render_subject(recipient.company)
    message["Date"] = formatdate(localtime=True)
    try:
        domain = template.sender.split("@", 1)[1]
    except IndexError:  # pragma: no cover - already validated above
        domain = None
    message["Message-ID"] = make_msgid(domain=domain)
    message.set_content(template.render_body(recipient.company), subtype="plain", charset="utf-8")

    for path in template.attachments:
        if not path:
            continue
        try:
            attach_file(message, path)
            if log:
                log(t("mailer.attachment_added", name=os.path.basename(path)))
        except FileNotFoundError:
            if log:
                log(t("mailer.attachment_missing", path=path))
        except Exception as exc:
            if log:
                log(t("mailer.attachment_error", path=path, error=exc))
    return message


def ssl_error_types():
    """TLS error types (imported lazily so the cost is only paid when needed)."""
    import ssl

    return (ssl.SSLError,)


def describe_smtp_error(exc: Exception) -> str:
    """Translate common SMTP/socket exceptions into readable messages."""
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return t("smtp.auth", error=exc)
    if isinstance(exc, smtplib.SMTPNotSupportedError):
        return t("smtp.not_supported", error=exc)
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        return t("smtp.recipients_refused", value=exc.recipients)
    if isinstance(exc, smtplib.SMTPSenderRefused):
        return t("smtp.sender_refused", value=exc.sender, error=exc)
    if isinstance(exc, smtplib.SMTPConnectError):
        return t("smtp.connect", error=exc)
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return t("smtp.disconnected", error=exc)
    if isinstance(exc, socket.gaierror):
        return t("smtp.dns", error=exc)
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return t("smtp.timeout", error=exc)
    if isinstance(exc, ConnectionRefusedError):
        return t("smtp.refused", error=exc)
    if isinstance(exc, ssl_error_types()):
        return t("smtp.tls", error=exc)
    if isinstance(exc, smtplib.SMTPException):
        return t("smtp.generic", error=exc)
    return t("smtp.unknown", error=exc)


class SmtpSession:
    """Reusable SMTP session able to deliver several messages.

    Keeping a single connection for a whole batch is much faster and less
    likely to hit provider rate limits. The session reconnects by itself when
    the server drops the connection.
    """

    def __init__(self, settings: SmtpSettings, log: Logger = None):
        self.settings = settings
        self.log = log or (lambda message: None)
        self.server: Optional[smtplib.SMTP] = None
        self.authenticated = False

    # -- connection handling --------------------------------------------------
    def connect(self) -> smtplib.SMTP:
        """Open the connection (and authenticate, when required)."""
        settings = self.settings
        self.log(
            t(
                "mailer.connecting",
                host=settings.host,
                port=settings.port,
                mode=settings.connection_type,
            )
        )

        if settings.connection_type == CONNECTION_SSL:
            server = smtplib.SMTP_SSL(settings.host, settings.port, timeout=settings.timeout)
            server.ehlo()
        else:
            server = smtplib.SMTP(timeout=settings.timeout)
            server.connect(settings.host, settings.port)
            server.ehlo()
            wants_tls = settings.connection_type == CONNECTION_STARTTLS
            if wants_tls or server.has_extn("STARTTLS"):
                self.log(t("mailer.starttls"))
                server.starttls()
                server.ehlo()  # a second EHLO after STARTTLS is mandatory
            else:
                self.log(t("mailer.insecure"))

        self.server = server
        self.authenticated = False

        if settings.use_auth:
            if not server.has_extn("AUTH"):
                self.log(t("mailer.no_auth_ext"))
            else:
                self.log(t("mailer.authenticating", user=settings.username.strip()))
                server.login(settings.username.strip(), settings.password)
                self.authenticated = True
        else:
            self.log(t("mailer.no_auth"))
        return server

    def ensure_connected(self) -> smtplib.SMTP:
        """Return a live connection, reconnecting when needed."""
        if self.server is not None:
            try:
                status, _ = self.server.noop()
                if status == 250:
                    return self.server
            except Exception:
                pass
            self.close()
        return self.connect()

    def close(self) -> None:
        """Close the connection, ignoring any error."""
        if self.server is None:
            return
        try:
            self.server.quit()
        except Exception:
            try:
                self.server.close()
            except Exception:
                pass
        finally:
            self.server = None
            self.authenticated = False

    # -- sending --------------------------------------------------------------
    def send(self, message: EmailMessage) -> None:
        """Send one message, retrying once when the connection drops."""
        try:
            server = self.ensure_connected()
            server.send_message(message)
        except (smtplib.SMTPServerDisconnected, ConnectionResetError, BrokenPipeError):
            self.log(t("mailer.reconnecting"))
            self.close()
            server = self.connect()
            server.send_message(message)

    def __enter__(self) -> "SmtpSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


@dataclass
class BulkResult:
    """Outcome of a bulk send."""

    sent: List[Recipient] = field(default_factory=list)
    failed: List[Tuple[Recipient, str]] = field(default_factory=list)

    @property
    def sent_count(self) -> int:
        return len(self.sent)

    @property
    def error_count(self) -> int:
        return len(self.failed)


def _pause(
    seconds: float,
    should_stop: Optional[Callable[[], bool]],
    sleep: Callable[[float], None],
) -> None:
    """Wait ``seconds`` in short steps, so a cancel request is honoured at once.

    Sleeping the whole delay in one call would leave the user waiting for it to
    elapse before the batch reacts to ``Stop``.
    """
    remaining = seconds
    while remaining > 0:
        if should_stop and should_stop():
            return
        step = min(0.2, remaining)
        sleep(step)
        remaining -= step


def send_bulk(
    settings: SmtpSettings,
    template: EmailTemplate,
    recipients: Sequence[Recipient],
    log: Logger = None,
    on_result: Optional[Callable[[Recipient, bool, str], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> BulkResult:
    """Send the message to every recipient reusing a single connection.

    ``on_result`` is called for each recipient with
    ``(recipient, success, message)``; ``should_stop`` allows the caller to
    interrupt the running batch. When ``settings.send_delay`` is set, the
    batch pauses for that many seconds between one message and the next.
    """
    log = log or (lambda message: None)
    result = BulkResult()
    delay = max(0.0, settings.send_delay)
    last_index = len(recipients) - 1
    if delay and last_index > 0:
        log(t("mailer.delay_active", seconds=format_delay(delay)))

    with SmtpSession(settings, log=log) as session:
        for index, recipient in enumerate(recipients):
            if should_stop and should_stop():
                log(t("mailer.stopped"))
                break
            try:
                message = build_message(template, recipient, log=log)
                session.send(message)
                result.sent.append(recipient)
                log(t("mailer.sent", company=recipient.company, email=recipient.email))
                if on_result:
                    on_result(recipient, True, "")
            except Exception as exc:
                detail = describe_smtp_error(exc)
                result.failed.append((recipient, detail))
                log(
                    t(
                        "mailer.send_error",
                        company=recipient.company,
                        email=recipient.email,
                        error=detail,
                    )
                )
                if on_result:
                    on_result(recipient, False, detail)
                if isinstance(
                    exc,
                    (smtplib.SMTPAuthenticationError, socket.gaierror, ConnectionRefusedError),
                ):
                    # Unrecoverable: insisting on the remaining recipients is
                    # pointless and may get the sender rate limited.
                    log(t("mailer.aborted"))
                    processed = len(result.sent) + len(result.failed)
                    for remaining in recipients[processed:]:
                        result.failed.append((remaining, t("mailer.not_attempted")))
                    break

            # Reached after a delivery and after a recoverable failure alike —
            # the abort path above leaves the loop before getting here.
            if delay and index < last_index:
                _pause(delay, should_stop, sleep)
    return result
