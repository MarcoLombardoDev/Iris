#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the README screenshots.

Boots the real application with sample data kept entirely in memory (no
config.ini is written, no email is sent, no network call is made) and captures
one PNG per tab.

Usage (from the repository root, with the dev environment installed)::

    xvfb-run -a python docs/generate_screenshots.py

Optional environment variables:

    SHOTDIR   output folder (default: docs/screenshots)
    LANG_CODE interface language to capture (default: en)
"""

import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

OUT = Path(os.environ.get("SHOTDIR", REPO_ROOT / "docs" / "screenshots"))
LANGUAGE = os.environ.get("LANG_CODE", "en")
OUT.mkdir(parents=True, exist_ok=True)

from PIL import ImageGrab  # noqa: E402

from iris import config_store, i18n, paths  # noqa: E402
from iris.parsers import Recipient  # noqa: E402

# Sample data: fictitious companies on reserved example domains.
SAMPLE_RECIPIENTS = [
    Recipient("Acme Corporation", "purchasing@acme.example"),
    Recipient("Globex Ltd", "info@globex.example"),
    Recipient("Initech S.r.l.", "sales@initech.example"),
    Recipient("Umbrella Group", "contact@umbrella.example"),
    Recipient("Soylent Industries", "office@soylent.example"),
    Recipient("Stark Trading", "admin@stark.example"),
]

SAMPLE_CONFIG = config_store.AppConfig(
    sender_email="notices@example.com",
    smtp_server="smtp.example.com",
    smtp_port="587",
    smtp_user="notices@example.com",
    smtp_password="not-a-real-password",
    connection_type="starttls",
    email_subject="Annual notice for {COMPANY}",
    email_body=(
        "Dear {COMPANY},\n\n"
        "please find attached the annual notice for your company.\n"
        "Should you need any clarification, simply reply to this message.\n\n"
        "Kind regards,\n"
        "Customer Office"
    ),
    email_cc="accounting@example.com",
    attachments=["annual_notice.pdf", "terms_and_conditions.pdf"],
    language=LANGUAGE,
    send_delay="1",
    profiles=[
        config_store.SenderProfile(
            name="Customer Office",
            sender_email="notices@example.com",
            smtp_server="smtp.example.com",
            smtp_port="587",
            smtp_user="notices@example.com",
            smtp_password="not-a-real-password",
            connection_type="starttls",
        ),
        config_store.SenderProfile(
            name="Internal relay",
            sender_email="no-reply@example.com",
            smtp_server="relay.internal.example",
            smtp_port="25",
            connection_type="none",
        ),
    ],
    templates=[
        config_store.MessageTemplate(
            name="Annual notice",
            email_subject="Annual notice for {COMPANY}",
            email_body="Dear {COMPANY},\n\nplease find attached the annual notice.",
            email_cc="accounting@example.com",
            attachments=["annual_notice.pdf", "terms_and_conditions.pdf"],
        ),
        config_store.MessageTemplate(
            name="Payment reminder",
            email_subject="Payment reminder — {COMPANY}",
            email_body="Dear {COMPANY},\n\nour records show an outstanding invoice.",
        ),
    ],
)

SAMPLE_LOG = [
    "Logging system initialized. Log file: logs/iris_20260811.log",
    "Configuration loaded from config.ini (encoding utf-8)",
    "File selected: recipients.xlsx",
    "Starting analysis of file: recipients.xlsx",
    "Analysis complete: 6 recipients found",
    "Connecting to smtp.example.com:587 (mode starttls)...",
    "Enabling secure connection (STARTTLS)...",
    "Authenticating user notices@example.com...",
    "Email sent to Acme Corporation <purchasing@acme.example>",
    "Email sent to Globex Ltd <info@globex.example>",
    "All 2 emails were sent successfully.",
]


def capture(root, filename):
    """Capture the application window into ``filename``."""
    root.update_idletasks()
    root.update()
    time.sleep(0.4)
    root.update()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    image = ImageGrab.grab(
        bbox=(x, y, x + root.winfo_width(), y + root.winfo_height()),
        xdisplay=os.environ.get("DISPLAY"),
    )
    target = OUT / filename
    image.save(target, "PNG")
    print(f"Written: {target} ({image.width}x{image.height})")


def main():
    # Never touch the real user configuration.
    config_store.default_save_path = lambda: str(REPO_ROOT / "docs" / "_screenshot_config.ini")
    paths.writable_app_dir = lambda: str(REPO_ROOT / "docs" / "_screenshot_data")
    i18n.set_language(LANGUAGE)

    from iris import gui
    from iris.gui import IrisApp, create_root

    root = create_root()
    app = IrisApp(root)

    # Sample configuration, straight into the widgets.
    app._loaded_config = config_store.LoadResult(config=SAMPLE_CONFIG, path="config.ini",
                                                 encoding="utf-8")
    # The saved libraries and attachments normally arrive through
    # load_config(); apply_config_to_widgets() alone only handles the
    # scalar fields, so they are set here the way load_config() would.
    app.profiles = list(SAMPLE_CONFIG.profiles)
    app.templates = list(SAMPLE_CONFIG.templates)
    app.attachments = list(SAMPLE_CONFIG.attachments)
    app.apply_config_to_widgets()
    app._refresh_library_choices()
    app.profile_display.set(SAMPLE_CONFIG.profiles[0].name)
    app.template_display.set(SAMPLE_CONFIG.templates[0].name)

    app._update_actions_list(SAMPLE_RECIPIENTS)

    app.log_text.config(state="normal")
    app.log_text.delete("1.0", "end")
    for line in SAMPLE_LOG:
        app.log_text.insert("end", f"[2026-08-11 09:41:12] {line}\n")
    app.log_text.see("end")
    app.log_text.config(state="disabled")

    app.update_status_bar(i18n.t("status.analysis_done", count=len(SAMPLE_RECIPIENTS)))

    tabs = [
        (0, f"01_processing_{LANGUAGE}.png"),
        (2, f"02_configuration_{LANGUAGE}.png"),
        (1, f"03_log_{LANGUAGE}.png"),
    ]
    for index, filename in tabs:
        app.notebook.select(index)
        capture(root, filename)

    app.shutdown()
    print("Done.")


if __name__ == "__main__":
    main()
