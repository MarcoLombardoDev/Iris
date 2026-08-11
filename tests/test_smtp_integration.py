# -*- coding: utf-8 -*-
"""Integration tests against a minimal in-process SMTP server.

They exercise the real SMTP dialogue (EHLO/MAIL/RCPT/DATA), connection reuse
and automatic reconnection, with no external dependency and without ever
sending a real email.
"""

import email
import socket
import threading

import pytest

from iris import mailer
from iris.parsers import Recipient


class TinySMTPServer(threading.Thread):
    """Bare-bones SMTP server: accepts messages and keeps them in memory."""

    def __init__(self, drop_after=None):
        super().__init__(daemon=True)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(5)
        self.port = self.socket.getsockname()[1]
        self.messages = []
        self.sessions = 0
        #: Abruptly close the connection after N messages (reconnection test).
        self.drop_after = drop_after
        self._running = True

    def run(self):
        while self._running:
            try:
                connection, _ = self.socket.accept()
            except OSError:
                break
            self.sessions += 1
            threading.Thread(target=self._handle, args=(connection,), daemon=True).start()

    def _handle(self, connection):
        delivered = 0
        with connection:
            stream = connection.makefile("rwb")
            stream.write(b"220 tiny.test ESMTP\r\n")
            stream.flush()
            envelope = {}
            while True:
                line = stream.readline()
                if not line:
                    return
                command = line.decode("utf-8", "replace").strip()
                upper = command.upper()

                if upper.startswith(("EHLO", "HELO")):
                    stream.write(b"250-tiny.test\r\n250 SIZE 10240000\r\n")
                elif upper.startswith("MAIL FROM"):
                    envelope["from"] = command
                    stream.write(b"250 OK\r\n")
                elif upper.startswith("RCPT TO"):
                    envelope.setdefault("to", []).append(command)
                    stream.write(b"250 OK\r\n")
                elif upper == "DATA":
                    stream.write(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                    stream.flush()
                    payload = bytearray()
                    while True:
                        data_line = stream.readline()
                        if not data_line or data_line in (b".\r\n", b".\n"):
                            break
                        payload.extend(data_line)
                    self.messages.append(bytes(payload))
                    delivered += 1
                    stream.write(b"250 Message accepted\r\n")
                    stream.flush()
                    if self.drop_after is not None and delivered >= self.drop_after:
                        return  # abrupt close: the client must reconnect
                    continue
                elif upper == "NOOP":
                    stream.write(b"250 OK\r\n")
                elif upper == "RSET":
                    envelope = {}
                    stream.write(b"250 OK\r\n")
                elif upper == "QUIT":
                    stream.write(b"221 Bye\r\n")
                    stream.flush()
                    return
                else:
                    stream.write(b"502 Command not implemented\r\n")
                stream.flush()

    def stop(self):
        self._running = False
        try:
            self.socket.close()
        except OSError:
            pass


@pytest.fixture
def smtp_server():
    server = TinySMTPServer()
    server.start()
    yield server
    server.stop()


def make_settings(port):
    return mailer.SmtpSettings(
        host="127.0.0.1", port=port, connection_type=mailer.CONNECTION_NONE, timeout=10
    )


TEMPLATE = mailer.EmailTemplate(
    sender="sender@example.com",
    subject="Notice for {COMPANY}",
    body="Dear {COMPANY}, accented text: àèìòù",
)


def test_end_to_end_send(smtp_server):
    recipients = [
        Recipient("Acme S.r.l.", "acme@example.com"),
        Recipient("Globex", "globex@example.com"),
    ]

    result = mailer.send_bulk(make_settings(smtp_server.port), TEMPLATE, recipients)

    assert result.sent_count == 2
    assert result.error_count == 0
    assert len(smtp_server.messages) == 2
    # A single TCP session for the whole batch.
    assert smtp_server.sessions == 1

    parsed = email.message_from_bytes(smtp_server.messages[0], policy=email.policy.default)
    assert parsed["To"] == "acme@example.com"
    assert parsed["Subject"] == "Notice for Acme S.r.l."
    assert "accented text: àèìòù" in parsed.get_content()


def test_send_with_attachment(smtp_server, tmp_path):
    attachment = tmp_path / "notice.pdf"
    attachment.write_bytes(b"%PDF-1.4 sample content")
    template = mailer.EmailTemplate(
        sender=TEMPLATE.sender,
        subject=TEMPLATE.subject,
        body=TEMPLATE.body,
        attachments=[str(attachment)],
    )

    result = mailer.send_bulk(
        make_settings(smtp_server.port), template, [Recipient("Acme", "acme@example.com")]
    )

    assert result.sent_count == 1
    parsed = email.message_from_bytes(smtp_server.messages[0], policy=email.policy.default)
    assert [part.get_filename() for part in parsed.iter_attachments()] == ["notice.pdf"]


def test_reconnection_after_a_dropped_connection():
    """Sending must continue when the server closes the connection."""
    server = TinySMTPServer(drop_after=1)
    server.start()
    try:
        recipients = [Recipient(f"Company {i}", f"a{i}@example.com") for i in range(3)]
        result = mailer.send_bulk(make_settings(server.port), TEMPLATE, recipients)
    finally:
        server.stop()

    assert result.sent_count == 3
    assert server.sessions > 1


def test_unreachable_server():
    settings = mailer.SmtpSettings(
        host="127.0.0.1", port=1, connection_type=mailer.CONNECTION_NONE, timeout=2
    )
    result = mailer.send_bulk(settings, TEMPLATE, [Recipient("Acme", "acme@example.com")])
    assert result.sent_count == 0
    assert result.error_count == 1
