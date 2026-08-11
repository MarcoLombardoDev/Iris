# -*- coding: utf-8 -*-
"""Message composition and SMTP delivery.

Like the rest of the package this module is independent from Tkinter, so the
sending logic can be tested and reused without a graphical interface.
"""

import mimetypes
import os
import smtplib
import socket
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


def send_bulk(
    settings: SmtpSettings,
    template: EmailTemplate,
    recipients: Sequence[Recipient],
    log: Logger = None,
    on_result: Optional[Callable[[Recipient, bool, str], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> BulkResult:
    """Send the message to every recipient reusing a single connection.

    ``on_result`` is called for each recipient with
    ``(recipient, success, message)``; ``should_stop`` allows the caller to
    interrupt the running batch.
    """
    log = log or (lambda message: None)
    result = BulkResult()

    with SmtpSession(settings, log=log) as session:
        for recipient in recipients:
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
    return result
