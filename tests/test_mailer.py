# -*- coding: utf-8 -*-
"""Tests for message composition, validation and delivery."""

import smtplib
import socket

import pytest

from iris import i18n, mailer
from iris.parsers import Recipient

RECIPIENT = Recipient("Acme Corp", "recipient@example.com")


def make_template(**kwargs):
    defaults = dict(
        sender="sender@example.com",
        subject="Notice for {COMPANY}",
        body="Dear {COMPANY},\nplease find the notice attached.",
    )
    defaults.update(kwargs)
    return mailer.EmailTemplate(**defaults)


def make_settings(**kwargs):
    defaults = dict(
        host="smtp.example.com", port=587, connection_type=mailer.CONNECTION_STARTTLS
    )
    defaults.update(kwargs)
    return mailer.SmtpSettings(**defaults)


# --------------------------------------------------------------------------
# Template
# --------------------------------------------------------------------------
def test_company_placeholder_is_replaced():
    template = make_template()
    assert template.render_subject("Alpha") == "Notice for Alpha"
    assert template.render_body("Alpha").startswith("Dear Alpha,")


def test_legacy_italian_placeholder_still_works():
    """Templates written for 1.x used {AZIENDA}."""
    template = make_template(subject="Avviso per {AZIENDA}", body="Gentile {AZIENDA},")
    assert template.render_subject("Alpha") == "Avviso per Alpha"
    assert template.render_body("Alpha") == "Gentile Alpha,"


def test_both_placeholders_in_the_same_text():
    template = make_template(subject="{COMPANY} / {AZIENDA}")
    assert template.render_subject("Alpha") == "Alpha / Alpha"


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def test_valid_configuration():
    assert mailer.validate_settings(make_settings(), make_template()) == []


def test_invalid_sender():
    errors = mailer.validate_settings(make_settings(), make_template(sender="not-an-address"))
    assert any("sender" in error.lower() for error in errors)


def test_missing_or_out_of_range_port():
    assert any(
        "port" in error.lower()
        for error in mailer.validate_settings(make_settings(port=0), make_template())
    )
    assert any(
        "65535" in error
        for error in mailer.validate_settings(make_settings(port=99999), make_template())
    )


def test_partial_credentials():
    errors = mailer.validate_settings(make_settings(username="user"), make_template())
    assert any("password" in error.lower() for error in errors)


def test_subject_and_body_are_required():
    errors = mailer.validate_settings(make_settings(), make_template(subject="", body=""))
    assert len(errors) == 2


def test_missing_attachment():
    errors = mailer.validate_settings(
        make_settings(), make_template(attachments=["/path/that/does/not/exist.pdf"])
    )
    assert any("attachment" in error.lower() for error in errors)


def test_validation_messages_follow_the_language():
    i18n.set_language("it")
    errors = mailer.validate_settings(make_settings(host=""), make_template())
    assert any("server SMTP" in error for error in errors)


@pytest.mark.parametrize(
    "value,expected", [("587", 587), (" 465 ", 465), ("", 0), ("abc", 0), (None, 0)]
)
def test_parse_port(value, expected):
    assert mailer.parse_port(value) == expected


def test_use_auth():
    assert not make_settings().use_auth
    assert make_settings(username="u", password="p").use_auth
    assert not make_settings(username="u").use_auth


# --------------------------------------------------------------------------
# Message composition
# --------------------------------------------------------------------------
def test_message_headers():
    message = mailer.build_message(make_template(), RECIPIENT)
    assert message["From"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"
    assert message["Subject"] == "Notice for Acme Corp"
    assert message["Message-ID"]
    assert message["Date"]
    assert message.get_content().startswith("Dear Acme Corp,")


def test_non_ascii_text_is_serialisable():
    """Regression: with MIMEMultipart under the compat32 policy an accented
    subject could not be encoded and sending failed."""
    template = make_template(subject="Città di {COMPANY} – notice", body="Perché è così: àèìòù")
    message = mailer.build_message(template, RECIPIENT)

    # Serialisation must not raise, and the header must be RFC 2047 encoded.
    raw = message.as_bytes()
    assert b"=?utf-8?" in raw

    import email

    reparsed = email.message_from_bytes(raw, policy=email.policy.default)
    assert reparsed["Subject"] == "Città di Acme Corp – notice"
    assert "Perché è così: àèìòù" in reparsed.get_content()


def test_attachment_is_included(tmp_path):
    attachment = tmp_path / "notice.pdf"
    attachment.write_bytes(b"%PDF-1.4 content")
    message = mailer.build_message(make_template(attachments=[str(attachment)]), RECIPIENT)
    names = [part.get_filename() for part in message.iter_attachments()]
    assert names == ["notice.pdf"]


def test_missing_attachment_does_not_block_sending(tmp_path):
    messages = []
    message = mailer.build_message(
        make_template(attachments=[str(tmp_path / "missing.pdf")]), RECIPIENT, log=messages.append
    )
    assert list(message.iter_attachments()) == []
    assert any("not found" in text for text in messages)


def test_invalid_recipient():
    with pytest.raises(mailer.MailConfigError):
        mailer.build_message(make_template(), Recipient("Alpha", "not-an-address"))


# --------------------------------------------------------------------------
# Bulk sending (with a fake SMTP server)
# --------------------------------------------------------------------------
class FakeServer:
    """Minimal stand-in for smtplib.SMTP."""

    def __init__(self, fail_on=(), raise_type=None):
        self.fail_on = set(fail_on)
        self.raise_type = raise_type or smtplib.SMTPException
        self.sent = []
        self.closed = False

    def send_message(self, message):
        recipient = message["To"]
        if recipient in self.fail_on:
            raise self.raise_type(f"delivery refused for {recipient}")
        self.sent.append(recipient)

    def noop(self):
        return 250, b"OK"

    def quit(self):
        self.closed = True


@pytest.fixture
def fake_session(monkeypatch):
    """Replace the real connection with a fake server."""
    server = FakeServer()

    def fake_connect(self):
        self.server = server
        self.authenticated = self.settings.use_auth
        return server

    monkeypatch.setattr(mailer.SmtpSession, "connect", fake_connect)
    return server


def test_bulk_send_reuses_a_single_connection(fake_session, monkeypatch):
    connects = {"count": 0}
    original = mailer.SmtpSession.connect

    def counting_connect(self):
        connects["count"] += 1
        return original(self)

    monkeypatch.setattr(mailer.SmtpSession, "connect", counting_connect)

    recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(5)]
    result = mailer.send_bulk(make_settings(), make_template(), recipients)

    assert result.sent_count == 5
    assert result.error_count == 0
    assert connects["count"] == 1
    assert fake_session.closed is True


def test_bulk_send_records_failures(fake_session):
    recipients = [Recipient("Alpha", "a@example.com"), Recipient("Beta", "b@example.com")]
    fake_session.fail_on = {"b@example.com"}

    result = mailer.send_bulk(make_settings(), make_template(), recipients)

    assert [r.email for r in result.sent] == ["a@example.com"]
    assert result.error_count == 1
    assert result.failed[0][0].email == "b@example.com"


def test_a_blocking_error_aborts_the_batch(fake_session):
    recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(4)]

    def raise_auth(message):
        raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    fake_session.send_message = raise_auth
    result = mailer.send_bulk(make_settings(), make_template(), recipients)

    assert result.sent_count == 0
    assert result.error_count == 4  # the first failure plus the untried ones


def test_progress_callback(fake_session):
    recipients = [Recipient("Alpha", "a@example.com"), Recipient("Beta", "b@example.com")]
    seen = []
    mailer.send_bulk(
        make_settings(),
        make_template(),
        recipients,
        on_result=lambda r, ok, d: seen.append((r.email, ok)),
    )
    assert seen == [("a@example.com", True), ("b@example.com", True)]


def test_stop_requested(fake_session):
    recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(3)]
    stop = {"value": False}

    def on_result(recipient, success, detail):
        stop["value"] = True

    result = mailer.send_bulk(
        make_settings(),
        make_template(),
        recipients,
        on_result=on_result,
        should_stop=lambda: stop["value"],
    )
    assert result.sent_count == 1


def test_smtp_error_descriptions():
    assert "authentication" in mailer.describe_smtp_error(
        smtplib.SMTPAuthenticationError(535, b"nope")
    )
    assert "DNS" in mailer.describe_smtp_error(socket.gaierror("no host"))
    assert "refused" in mailer.describe_smtp_error(ConnectionRefusedError("refused"))


def test_smtp_error_descriptions_follow_the_language():
    i18n.set_language("it")
    assert "autenticazione" in mailer.describe_smtp_error(
        smtplib.SMTPAuthenticationError(535, b"nope")
    )


# --------------------------------------------------------------------------
# Pause between messages
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value,expected",
    [
        ("", 0.0),
        (None, 0.0),
        ("0", 0.0),
        ("2", 2.0),
        ("1.5", 1.5),
        ("1,5", 1.5),  # comma as the decimal separator
        ("  3  ", 3.0),
        ("abc", -1.0),  # unreadable: reported by validate_settings
    ],
)
def test_parse_delay(value, expected):
    assert mailer.parse_delay(value) == expected


def test_an_unreadable_delay_is_reported():
    errors = mailer.validate_settings(
        make_settings(send_delay=mailer.parse_delay("every now and then")), make_template()
    )
    assert any("pause" in error.lower() for error in errors)


def test_a_valid_delay_passes_validation():
    assert mailer.validate_settings(make_settings(send_delay=2.0), make_template()) == []


def test_the_batch_pauses_between_messages(fake_session):
    waited = []
    recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(3)]

    result = mailer.send_bulk(
        make_settings(send_delay=1.0), make_template(), recipients, sleep=waited.append
    )

    assert result.sent_count == 3
    # Two pauses for three messages: never after the last one.
    assert round(sum(waited), 3) == 2.0


def test_no_pause_without_a_delay(fake_session):
    waited = []
    recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(3)]

    mailer.send_bulk(make_settings(), make_template(), recipients, sleep=waited.append)

    assert waited == []


def test_a_single_recipient_is_never_delayed(fake_session):
    waited = []
    mailer.send_bulk(
        make_settings(send_delay=5.0), make_template(), [RECIPIENT], sleep=waited.append
    )
    assert waited == []


def test_the_pause_reacts_to_a_stop_request(fake_session):
    """Cancelling must not wait for the whole delay to elapse."""
    waited = []
    stopped = {"value": False}
    recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(4)]

    def should_stop():
        # Ask to stop as soon as the first message has gone out.
        return stopped["value"]

    def sleep(seconds):
        waited.append(seconds)
        stopped["value"] = True

    result = mailer.send_bulk(
        make_settings(send_delay=30.0),
        make_template(),
        recipients,
        should_stop=should_stop,
        sleep=sleep,
    )

    assert result.sent_count == 1
    # A single short step, not the full 30 seconds.
    assert waited == [0.2]


def test_the_delay_is_announced_once(fake_session):
    messages = []
    recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(3)]

    mailer.send_bulk(
        make_settings(send_delay=1.5),
        make_template(),
        recipients,
        log=messages.append,
        sleep=lambda seconds: None,
    )

    announcements = [text for text in messages if "1.5" in text and "Pausing" in text]
    assert len(announcements) == 1


# --------------------------------------------------------------------------
# Address lists (Cc/Bcc)
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value,expected",
    [
        ("", []),
        ("a@example.com", ["a@example.com"]),
        ("a@example.com, b@example.com", ["a@example.com", "b@example.com"]),
        ("a@example.com; b@example.com", ["a@example.com", "b@example.com"]),
        (" a@example.com ,  b@example.com ", ["a@example.com", "b@example.com"]),
        ("a@example.com,,b@example.com", ["a@example.com", "b@example.com"]),
    ],
)
def test_parse_address_list(value, expected):
    assert mailer.parse_address_list(value) == expected


def test_valid_cc_and_bcc_pass_validation():
    template = make_template(cc="a@example.com, b@example.com", bcc="c@example.com")
    assert mailer.validate_settings(make_settings(), template) == []


def test_invalid_cc_is_reported():
    errors = mailer.validate_settings(make_settings(), make_template(cc="not-an-address"))
    assert any("cc" in error.lower() for error in errors)


def test_invalid_bcc_is_reported():
    errors = mailer.validate_settings(make_settings(), make_template(bcc="not-an-address"))
    assert any("bcc" in error.lower() for error in errors)


def test_one_bad_address_among_several_is_still_caught():
    errors = mailer.validate_settings(
        make_settings(), make_template(cc="ok@example.com, not-an-address")
    )
    assert any("not-an-address" in error for error in errors)


def test_message_carries_cc_header():
    template = make_template(cc="cc1@example.com, cc2@example.com")
    message = mailer.build_message(template, RECIPIENT)
    assert message["Cc"] == "cc1@example.com, cc2@example.com"


def test_message_carries_bcc_header():
    """Bcc is set on the built message; send_message() strips it before the wire."""
    template = make_template(bcc="hidden@example.com")
    message = mailer.build_message(template, RECIPIENT)
    assert message["Bcc"] == "hidden@example.com"


def test_no_cc_bcc_header_when_not_set():
    message = mailer.build_message(make_template(), RECIPIENT)
    assert message["Cc"] is None
    assert message["Bcc"] is None


# --------------------------------------------------------------------------
# Multiple attachments
# --------------------------------------------------------------------------
def test_several_attachments_are_all_included(tmp_path):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    first.write_bytes(b"%PDF-1.4 a")
    second.write_bytes(b"%PDF-1.4 b")
    message = mailer.build_message(
        make_template(attachments=[str(first), str(second)]), RECIPIENT
    )
    names = sorted(part.get_filename() for part in message.iter_attachments())
    assert names == ["a.pdf", "b.pdf"]


def test_one_missing_attachment_does_not_block_the_others(tmp_path):
    present = tmp_path / "present.pdf"
    present.write_bytes(b"%PDF-1.4 content")
    messages = []
    message = mailer.build_message(
        make_template(attachments=[str(present), str(tmp_path / "missing.pdf")]),
        RECIPIENT,
        log=messages.append,
    )
    names = [part.get_filename() for part in message.iter_attachments()]
    assert names == ["present.pdf"]
    assert any("not found" in text for text in messages)
