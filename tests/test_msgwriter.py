# -*- coding: utf-8 -*-
"""Tests for writing the generated emails to disk."""

import os

from iris import mailer, msgwriter
from iris.parsers import Recipient

RECIPIENT = Recipient("Acme Corp", "recipient@example.com")
TEMPLATE = mailer.EmailTemplate(
    sender="sender@example.com",
    subject="Notice for {COMPANY}",
    body="Dear {COMPANY}, accented text: àèìòù",
)


def test_safe_filename():
    assert msgwriter.safe_filename("Acme Corp", "info@acme.com", extension=".eml") == (
        "Acme Corp_info_acme.com.eml"
    )
    assert msgwriter.safe_filename("", "", extension=".eml") == "email.eml"


def test_unique_path(tmp_path):
    first = tmp_path / "email.eml"
    first.write_text("x", encoding="utf-8")
    assert msgwriter.unique_path(str(first)).endswith("email_2.eml")


def test_save_eml(tmp_path):
    message = mailer.build_message(TEMPLATE, RECIPIENT)
    path, kind = msgwriter.save_message(
        message, str(tmp_path), RECIPIENT.company, RECIPIENT.email, prefer_msg=False
    )
    assert kind == "eml"
    assert os.path.exists(path)

    raw = open(path, "rb").read()
    assert b"To: recipient@example.com" in raw
    assert b"Message-ID:" in raw

    # The file must be a re-readable MIME message.
    import email

    parsed = email.message_from_bytes(raw)
    assert parsed["Subject"] == "Notice for Acme Corp"


def test_save_eml_with_attachment(tmp_path):
    attachment = tmp_path / "notice.pdf"
    attachment.write_bytes(b"%PDF-1.4 test")
    template = mailer.EmailTemplate(
        sender=TEMPLATE.sender,
        subject=TEMPLATE.subject,
        body=TEMPLATE.body,
        attachments=[str(attachment)],
    )
    message = mailer.build_message(template, RECIPIENT)
    path, _ = msgwriter.save_message(
        message, str(tmp_path / "out"), RECIPIENT.company, RECIPIENT.email, prefer_msg=False
    )
    assert b"notice.pdf" in open(path, "rb").read()


def test_fallback_to_eml_without_outlook(tmp_path, monkeypatch):
    """Without Outlook the generation must produce an .eml, not fail."""
    monkeypatch.setattr(msgwriter, "outlook_available", lambda: False)
    message = mailer.build_message(TEMPLATE, RECIPIENT)
    path, kind = msgwriter.save_message(
        message, str(tmp_path), RECIPIENT.company, RECIPIENT.email, prefer_msg=True
    )
    assert kind == "eml"
    assert os.path.exists(path)


def test_cleanup_only_touches_email_files(tmp_path):
    (tmp_path / "old.eml").write_text("x", encoding="utf-8")
    (tmp_path / "old.msg").write_text("x", encoding="utf-8")
    (tmp_path / "important.pdf").write_text("x", encoding="utf-8")

    removed = msgwriter.clean_output_directory(str(tmp_path))

    assert removed == 2
    assert (tmp_path / "important.pdf").exists()


def test_cleanup_of_a_missing_directory(tmp_path):
    assert msgwriter.clean_output_directory(str(tmp_path / "missing")) == 0
