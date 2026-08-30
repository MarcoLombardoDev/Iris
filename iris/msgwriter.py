# Iris — Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# Distributed WITHOUT ANY WARRANTY; see LICENSE for the full terms.
# A commercial licence, without the AGPL's obligations, is available for use
# in proprietary or closed-source products — see COMMERCIAL-LICENSE.md.

"""Writing generated emails to disk (.msg through Outlook, .eml always).

``.msg`` support requires Windows with Outlook installed and the ``pywin32``
package. When that is unavailable the application falls back to the standard
``.eml`` format, which Outlook, Thunderbird and most mail clients can open.
"""

import contextlib
import os
import re
import sys
from collections.abc import Callable
from email.message import EmailMessage
from email.policy import SMTP as SMTP_POLICY

from .i18n import t

Logger = Callable[[str], None] | None

_INVALID_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._\- ]+")


def safe_filename(*parts: str, max_length: int = 80, extension: str = "") -> str:
    """Build a safe file name out of the given fragments."""
    cleaned = []
    for part in parts:
        value = _INVALID_FILENAME_CHARS.sub("_", (part or "").strip())
        value = re.sub(r"_{2,}", "_", value).strip("_ ")
        if value:
            cleaned.append(value[:max_length])
    name = "_".join(cleaned) or "email"
    return f"{name}{extension}"


def unique_path(path: str) -> str:
    """Return a path that does not exist yet, appending a counter if needed."""
    if not os.path.exists(path):
        return path
    base, extension = os.path.splitext(path)
    counter = 2
    while os.path.exists(f"{base}_{counter}{extension}"):
        counter += 1
    return f"{base}_{counter}{extension}"


def outlook_available() -> bool:
    """True when .msg files can be produced through Outlook."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import pythoncom  # noqa: F401
        import win32com.client  # noqa: F401
    except ImportError:
        return False
    return True


def save_eml(message: EmailMessage, filepath: str) -> str:
    """Save the message as .eml and return the path actually written."""
    filepath = unique_path(filepath)
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "wb") as handle:
        handle.write(message.as_bytes(policy=SMTP_POLICY))
    return filepath


def save_msg_via_outlook(
    to_email: str,
    subject: str,
    body: str,
    attachments,
    filepath: str,
    log: Logger = None,
) -> str:
    """Create a .msg file through Outlook COM automation.

    Raises when Outlook is unavailable: the caller decides whether to fall
    back to the .eml format.
    """
    import pythoncom
    import win32com.client

    filepath = unique_path(filepath)
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    pythoncom.CoInitialize()
    try:
        try:
            outlook = win32com.client.gencache.EnsureDispatch("Outlook.Application")
        except Exception:
            outlook = win32com.client.Dispatch("Outlook.Application")

        mail = outlook.CreateItem(0)  # olMailItem
        mail.To = to_email
        mail.Subject = subject
        mail.Body = body
        for attachment in attachments or []:
            if not attachment:
                continue
            try:
                mail.Attachments.Add(attachment)
            except Exception as exc:
                if log:
                    log(t("msgwriter.attachment_error", error=exc))
        mail.SaveAs(filepath, 3)  # 3 = olMSG (unicode)
        return filepath
    finally:
        with contextlib.suppress(Exception):
            pythoncom.CoUninitialize()


def save_message(
    message: EmailMessage,
    directory: str,
    company: str,
    email_address: str,
    attachments=None,
    prefer_msg: bool = True,
    log: Logger = None,
) -> tuple[str, str]:
    """Save the email using the best format available.

    Returns ``(path, format)`` where format is ``"msg"`` or ``"eml"``.
    """
    os.makedirs(directory, exist_ok=True)
    base_name = safe_filename(company, email_address)

    if prefer_msg and outlook_available():
        try:
            path = save_msg_via_outlook(
                to_email=email_address,
                subject=message.get("Subject", ""),
                body=_plain_body(message),
                attachments=attachments or [],
                filepath=os.path.join(directory, base_name + ".msg"),
                log=log,
            )
            return path, "msg"
        except Exception as exc:
            if log:
                log(t("msgwriter.outlook_error", error=exc))

    path = save_eml(message, os.path.join(directory, base_name + ".eml"))
    return path, "eml"


def _plain_body(message: EmailMessage) -> str:
    """Extract the plain text body from a message."""
    try:
        part = message.get_body(preferencelist=("plain",))
        if part is not None:
            return part.get_content()
    except Exception:
        pass
    payload = message.get_payload()
    return payload if isinstance(payload, str) else ""


def clean_output_directory(directory: str, log: Logger = None) -> int:
    """Remove previously generated emails (only .msg and .eml files).

    Returns how many files were removed. Unlike the pre-2.0 implementation it
    never touches other files that happen to live in the folder.
    """
    if not os.path.isdir(directory):
        return 0
    removed = 0
    for name in os.listdir(directory):
        if not name.lower().endswith((".msg", ".eml")):
            continue
        try:
            os.remove(os.path.join(directory, name))
            removed += 1
        except Exception as exc:
            if log:
                log(t("msgwriter.remove_error", name=name, error=exc))
    return removed
