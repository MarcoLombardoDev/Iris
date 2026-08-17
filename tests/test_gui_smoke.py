# -*- coding: utf-8 -*-
"""Smoke tests for the graphical interface.

They need a display (CI uses Xvfb); without one they are skipped.
"""

import gc
import os
import sys
import time

import pytest

tk = pytest.importorskip("tkinter")


def _display_available():
    if os.name == "nt" or sys.platform == "darwin":
        return True
    if not os.environ.get("DISPLAY"):
        return False
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _display_available(), reason="no display available")


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Start the application with configuration and folders isolated in tmp_path."""
    from iris import paths

    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    monkeypatch.setattr(paths, "writable_app_dir", lambda: str(tmp_path))
    monkeypatch.chdir(tmp_path)

    from iris import gui
    from iris.gui import IrisApp, create_root

    # No modal dialog during the tests.
    for name, value in (
        ("showinfo", None),
        ("showerror", None),
        ("showwarning", None),
        ("askyesno", True),
    ):
        monkeypatch.setattr(gui.messagebox, name, lambda *a, _v=value, **k: _v)

    root = create_root()
    instance = IrisApp(root)
    root.update()
    yield instance

    try:
        instance.shutdown()
        root.update()
    except Exception:
        pass

    # Every test creates and destroys a Tk window: ttkbootstrap's internal
    # images stay attached to the old interpreter and, if the garbage
    # collector claimed them inside a worker thread of a later test,
    # PhotoImage.__del__ would call Tk off the main thread and hang the suite.
    # Reset the style singleton and collect here, on the main thread.
    try:
        import ttkbootstrap as tb

        tb.Style.instance = None
    except Exception:
        pass
    gc.collect()


def pump(app, seconds=2.0):
    """Run the Tk loop until the background operation finishes."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.root.update()
        if not app.operation_in_progress:
            return True
        time.sleep(0.02)
    return not app.operation_in_progress


def test_application_starts(app):
    assert app.root.winfo_exists()
    assert app.status_label.cget("text") in ("Ready", "")


def test_analysis_fills_the_list(app, tmp_path):
    source = tmp_path / "recipients.txt"
    source.write_text("Acme Corp, info@acme.com\nGlobex Ltd; contact@globex.com\n", encoding="utf-8")

    app.analyze_file(str(source))
    assert pump(app), "analysis did not finish"

    values = [app.actions_tree.item(item, "values") for item in app.actions_tree.get_children()]
    assert values == [("Acme Corp", "info@acme.com"), ("Globex Ltd", "contact@globex.com")]


def test_validation_rejects_an_incomplete_configuration(app):
    assert app.validate_email_config() is False


def _configure(app):
    app.sender_email.set("sender@example.com")
    app.smtp_server.set("smtp.example.com")
    app.smtp_port.set("587")
    app.subject_template.set("Notice for {COMPANY}")
    app._set_body_text("Dear {COMPANY},\ngood morning.")


def test_validation_accepts_a_complete_configuration(app):
    _configure(app)
    assert app.validate_email_config() is True


def test_configuration_is_saved_and_reloaded(app, tmp_path):
    _configure(app)
    app.smtp_password.set("s3cret")
    app.smtp_user.set("user")
    app.save_config()

    config_file = tmp_path / "config.ini"
    assert config_file.exists()
    assert "s3cret" not in config_file.read_text(encoding="utf-8")

    app.sender_email.set("")
    app._set_body_text("")
    app.load_config()
    assert app.sender_email.get() == "sender@example.com"
    assert app.smtp_password.get() == "s3cret"
    assert app.body_template.get() == "Dear {COMPANY},\ngood morning."


def test_email_file_generation(app, tmp_path):
    _configure(app)
    source = tmp_path / "recipients.txt"
    source.write_text("Acme S.r.l.; acme@example.com\n", encoding="utf-8")
    app.analyze_file(str(source))
    assert pump(app)

    app.generate_email_files()
    assert pump(app, seconds=20.0), "generation did not finish"

    generated = sorted((tmp_path / "emails").iterdir())
    assert len(generated) == 1
    assert generated[0].suffix in (".eml", ".msg")


def test_connection_type_combobox(app):
    from iris.i18n import t

    app.connection_display.set(t("connection.ssl"))
    app.on_connection_type_change()
    assert app.connection_type.get() == "ssl"

    app._set_connection_display("none")
    assert app.connection_display.get() == t("connection.none")

    # Unknown value: fall back to the default.
    app._set_connection_display("something-odd")
    assert app.connection_type.get() == "starttls"


def test_body_text_stays_in_sync(app):
    app.body_text.delete("1.0", tk.END)
    app.body_text.insert("1.0", "Hand written text")
    app.update_body_template()
    assert app.body_template.get() == "Hand written text"


def test_deleting_recipients(app, tmp_path):
    source = tmp_path / "recipients.txt"
    source.write_text("Alpha; alpha@example.com\nBeta; beta@example.com\n", encoding="utf-8")
    app.analyze_file(str(source))
    assert pump(app)

    app.actions_tree.selection_set(app.actions_tree.get_children()[0])
    app.delete_selected_action()
    assert len(app.actions_tree.get_children()) == 1


def test_an_analysis_error_unblocks_the_interface(app, tmp_path):
    """Regression: an unsupported format must end the operation.

    The error message used to be read inside a lambda referencing the
    ``except`` variable (which Python deletes when the block ends): the UI
    update failed and the buttons stayed disabled forever.
    """
    source = tmp_path / "document.rtf"
    source.write_text("content", encoding="utf-8")

    app.analyze_file(str(source))
    assert pump(app), "the operation was not closed after the error"

    assert app.operation_in_progress is False
    assert "Error" in app.status_label.cget("text")
    # The buttons must be usable again.
    assert all(str(button.cget("state")) == "normal" for button in app._action_buttons)


def test_a_missing_file_does_not_block(app, tmp_path):
    app.analyze_file(str(tmp_path / "missing.txt"))
    assert app.operation_in_progress is False


# --------------------------------------------------------------------------
# Language switching
# --------------------------------------------------------------------------
def test_interface_starts_in_english(app):
    from iris import i18n

    assert i18n.get_language() == "en"
    assert app.notebook.tab(0, "text") == "PROCESSING"


def test_switching_language_redraws_the_interface(app, tmp_path):
    from iris import i18n

    app.language_display.set("Italiano")
    app.on_language_change()

    assert i18n.get_language() == "it"
    assert app.notebook.tab(0, "text") == "ELABORAZIONE"
    assert app.status_label.cget("text") != ""
    # The preference is persisted right away.
    assert "language = it" in (tmp_path / "config.ini").read_text(encoding="utf-8")


def test_switching_language_keeps_the_content(app, tmp_path):
    _configure(app)
    source = tmp_path / "recipients.txt"
    source.write_text("Acme Corp; acme@example.com\n", encoding="utf-8")
    app.analyze_file(str(source))
    assert pump(app)

    app.language_display.set("Italiano")
    app.on_language_change()

    assert app.sender_email.get() == "sender@example.com"
    assert app.body_template.get() == "Dear {COMPANY},\ngood morning."
    values = [app.actions_tree.item(item, "values") for item in app.actions_tree.get_children()]
    assert values == [("Acme Corp", "acme@example.com")]
    assert app.actions_tree.heading("company")["text"] == "Nome Azienda"


def test_switching_back_to_english(app):
    app.language_display.set("Italiano")
    app.on_language_change()
    app.language_display.set("English")
    app.on_language_change()

    from iris import i18n

    assert i18n.get_language() == "en"
    assert app.notebook.tab(0, "text") == "PROCESSING"


def test_saved_language_is_restored_on_start(tmp_path, monkeypatch):
    """A new instance must open in the language stored in config.ini."""
    from iris import config_store, i18n, paths

    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    monkeypatch.setattr(paths, "writable_app_dir", lambda: str(tmp_path))
    monkeypatch.chdir(tmp_path)
    config_store.save(config_store.AppConfig(language="it"), str(tmp_path / "config.ini"))

    from iris import gui
    from iris.gui import IrisApp, create_root

    for name, value in (("showinfo", None), ("showerror", None), ("askyesno", True)):
        monkeypatch.setattr(gui.messagebox, name, lambda *a, _v=value, **k: _v)

    root = create_root()
    instance = IrisApp(root)
    root.update()
    try:
        assert i18n.get_language() == "it"
        assert instance.notebook.tab(0, "text") == "ELABORAZIONE"
        assert instance.language_display.get() == "Italiano"
    finally:
        instance.shutdown()
        root.update()
        try:
            import ttkbootstrap as tb

            tb.Style.instance = None
        except Exception:
            pass
        gc.collect()


# --------------------------------------------------------------------------
# End-to-end against a local SMTP server
# --------------------------------------------------------------------------
def _use_local_smtp(app, server):
    _configure(app)
    app.smtp_server.set("127.0.0.1")
    app.smtp_port.set(str(server.port))
    app._set_connection_display("none")


def test_end_to_end_send_from_the_gui(app, tmp_path):
    """Full path: analyse a document -> send -> list updated."""
    from test_smtp_integration import TinySMTPServer

    server = TinySMTPServer()
    server.start()
    try:
        _use_local_smtp(app, server)
        source = tmp_path / "recipients.txt"
        source.write_text(
            "Acme S.r.l.; acme@example.com\nSociété Beta; beta@example.com\n", encoding="utf-8"
        )
        app.analyze_file(str(source))
        assert pump(app), "analysis did not finish"
        assert len(app.actions_tree.get_children()) == 2

        app.send_all_emails()
        assert pump(app, seconds=30.0), "sending did not finish"

        assert len(server.messages) == 2
        # Successfully sent rows are removed from the list.
        assert app.actions_tree.get_children() == ()

        import email

        parsed = email.message_from_bytes(server.messages[0], policy=email.policy.default)
        assert parsed["To"] == "acme@example.com"
        assert parsed["Subject"] == "Notice for Acme S.r.l."
        assert "Dear Acme S.r.l.," in parsed.get_content()
    finally:
        server.stop()


def test_connection_test_from_the_gui(app):
    from test_smtp_integration import TinySMTPServer

    server = TinySMTPServer()
    server.start()
    try:
        _use_local_smtp(app, server)
        app.test_connection()
        assert pump(app, seconds=30.0), "the test did not finish"
        assert "successful" in app.status_label.cget("text").lower()
    finally:
        server.stop()


def test_failed_connection_test(app):
    _configure(app)
    app.smtp_server.set("127.0.0.1")
    app.smtp_port.set("1")  # nothing listening
    app._set_connection_display("none")

    app.test_connection()
    assert pump(app, seconds=30.0)
    assert "failed" in app.status_label.cget("text").lower()


# --------------------------------------------------------------------------
# Saved sender profiles and templates
# --------------------------------------------------------------------------
def _answer_name_prompt(monkeypatch, answer):
    """Make the "save as" dialog reply with ``answer`` (None = cancelled)."""
    from iris import gui

    monkeypatch.setattr(gui.simpledialog, "askstring", lambda *a, **k: answer)


def test_saving_and_reloading_a_sender_profile(app, tmp_path, monkeypatch):
    _configure(app)
    app.smtp_user.set("user")
    app.smtp_password.set("s3cret")
    _answer_name_prompt(monkeypatch, "Work")

    app.save_profile_as()

    assert app._profile_names() == ["Work"]
    stored = (tmp_path / "config.ini").read_text(encoding="utf-8")
    assert "[PROFILE:Work]" in stored
    assert "s3cret" not in stored

    # Overwrite every field, then bring the profile back.
    app.sender_email.set("other@example.com")
    app.smtp_server.set("other.example.com")
    app.smtp_password.set("")
    app.profile_display.set("Work")
    app.on_profile_selected()

    assert app.sender_email.get() == "sender@example.com"
    assert app.smtp_server.get() == "smtp.example.com"
    assert app.smtp_password.get() == "s3cret"


def test_deleting_a_sender_profile(app, tmp_path, monkeypatch):
    _configure(app)
    _answer_name_prompt(monkeypatch, "Work")
    app.save_profile_as()

    app.profile_display.set("Work")
    app.delete_profile()

    assert app._profile_names() == []
    assert "[PROFILE:Work]" not in (tmp_path / "config.ini").read_text(encoding="utf-8")


def test_saving_and_reloading_a_template(app, monkeypatch):
    _configure(app)
    _answer_name_prompt(monkeypatch, "Reminder")

    app.save_template_as()
    assert app._template_names() == ["Reminder"]

    app.subject_template.set("Something else")
    app._set_body_text("Another body")
    app.template_display.set("Reminder")
    app.on_template_selected()

    assert app.subject_template.get() == "Notice for {COMPANY}"
    assert app.body_template.get() == "Dear {COMPANY},\ngood morning."


def test_a_cancelled_prompt_saves_nothing(app, monkeypatch):
    _configure(app)
    _answer_name_prompt(monkeypatch, None)

    app.save_profile_as()
    app.save_template_as()

    assert app._profile_names() == []
    assert app._template_names() == []


def test_saving_the_configuration_keeps_the_saved_profiles(app, tmp_path, monkeypatch):
    """Regression: SAVE CONFIGURATION rewrites config.ini in full."""
    from iris import config_store

    _configure(app)
    _answer_name_prompt(monkeypatch, "Work")
    app.save_profile_as()

    app.save_config()

    reloaded = config_store.load(str(tmp_path / "config.ini")).config
    assert [item.name for item in reloaded.profiles] == ["Work"]


def test_profiles_survive_a_language_switch(app, monkeypatch):
    _configure(app)
    _answer_name_prompt(monkeypatch, "Work")
    app.save_profile_as()

    app.language_display.set("Italiano")
    app.on_language_change()

    assert app._profile_names() == ["Work"]
    assert list(app.profile_combo.cget("values")) == ["Work"]


# --------------------------------------------------------------------------
# Pause between messages
# --------------------------------------------------------------------------
def test_the_pause_is_saved_and_read_back(app, tmp_path):
    _configure(app)
    app.send_delay.set("2")

    app.save_config()

    assert "send_delay = 2" in (tmp_path / "config.ini").read_text(encoding="utf-8")
    assert app.current_settings().send_delay == 2.0


def test_an_unreadable_pause_blocks_the_send(app):
    _configure(app)
    app.send_delay.set("now and then")
    assert app.validate_email_config() is False


# --------------------------------------------------------------------------
# Commercial licensing contact
# --------------------------------------------------------------------------
def test_the_footer_shows_the_licensing_address(app):
    from iris.version import CONTACT_EMAIL

    assert app.footer_email.cget("text") == CONTACT_EMAIL
    assert "AGPL-3.0" in app.footer_label.cget("text")


def test_clicking_the_address_opens_the_mail_client(app, monkeypatch):
    from iris import gui
    from iris.version import CONTACT_EMAIL

    opened = []
    monkeypatch.setattr(gui.webbrowser, "open", opened.append)

    app.open_licensing_email()

    assert len(opened) == 1
    assert opened[0].startswith(f"mailto:{CONTACT_EMAIL}?subject=")


def test_a_missing_mail_client_does_not_crash(app, monkeypatch):
    from iris import gui

    def explode(url):
        raise OSError("no mail client")

    monkeypatch.setattr(gui.webbrowser, "open", explode)

    app.open_licensing_email()  # must not raise: the address is on screen anyway

    assert app.root.winfo_exists()


def test_the_address_survives_a_language_switch(app):
    from iris.version import CONTACT_EMAIL

    app.language_display.set("Italiano")
    app.on_language_change()

    assert app.footer_email.cget("text") == CONTACT_EMAIL
    assert "Licenza commerciale" in app.footer_label.cget("text")


# --------------------------------------------------------------------------
# Multiple attachments
# --------------------------------------------------------------------------
def _answer_file_dialog(monkeypatch, paths):
    from iris import gui

    monkeypatch.setattr(gui.filedialog, "askopenfilenames", lambda *a, **k: paths)


def test_adding_several_attachments_at_once(app, tmp_path, monkeypatch):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    first.write_bytes(b"%PDF-1.4 a")
    second.write_bytes(b"%PDF-1.4 b")
    _answer_file_dialog(monkeypatch, (str(first), str(second)))

    app.add_attachment_files()

    assert app.attachments == [str(first), str(second)]
    assert app.attachment_listbox.size() == 2
    assert app.attachment_listbox.get(0) == "a.pdf"


def test_adding_the_same_file_twice_is_a_no_op(app, tmp_path, monkeypatch):
    path = tmp_path / "a.pdf"
    path.write_bytes(b"%PDF-1.4 a")
    _answer_file_dialog(monkeypatch, (str(path),))

    app.add_attachment_files()
    app.add_attachment_files()

    assert app.attachments == [str(path)]


def test_removing_selected_attachments(app, tmp_path, monkeypatch):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    first.write_bytes(b"x")
    second.write_bytes(b"x")
    _answer_file_dialog(monkeypatch, (str(first), str(second)))
    app.add_attachment_files()

    app.attachment_listbox.selection_set(0)
    app.remove_selected_attachments()

    assert app.attachments == [str(second)]
    assert app.attachment_listbox.size() == 1


def test_removing_with_nothing_selected_shows_a_hint(app, monkeypatch):
    from iris import gui

    shown = []
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda *a, **k: shown.append(a))

    app.remove_selected_attachments()

    assert shown


def test_attachments_are_sent_and_survive_a_language_switch(app, tmp_path, monkeypatch):
    path = tmp_path / "a.pdf"
    path.write_bytes(b"x")
    _answer_file_dialog(monkeypatch, (str(path),))
    app.add_attachment_files()

    app.language_display.set("Italiano")
    app.on_language_change()

    assert app.attachments == [str(path)]
    assert app.attachment_listbox.size() == 1


def test_attachments_are_saved_and_reloaded(app, tmp_path, monkeypatch):
    _configure(app)
    path = tmp_path / "a.pdf"
    path.write_bytes(b"x")
    _answer_file_dialog(monkeypatch, (str(path),))
    app.add_attachment_files()

    app.save_config()
    app.attachments = []
    app._refresh_attachment_widget()
    app.load_config()

    assert app.attachments == [str(path)]


# --------------------------------------------------------------------------
# Cc / Bcc
# --------------------------------------------------------------------------
def test_cc_and_bcc_are_saved_and_reloaded(app, tmp_path):
    _configure(app)
    app.cc.set("cc@example.com")
    app.bcc.set("bcc@example.com")

    app.save_config()
    app.cc.set("")
    app.bcc.set("")
    app.load_config()

    assert app.cc.get() == "cc@example.com"
    assert app.bcc.get() == "bcc@example.com"


def test_an_invalid_cc_blocks_validation(app):
    _configure(app)
    app.cc.set("not-an-address")
    assert app.validate_email_config() is False


def test_saving_a_template_keeps_cc_bcc_and_attachments(app, tmp_path, monkeypatch):
    _configure(app)
    path = tmp_path / "a.pdf"
    path.write_bytes(b"x")
    _answer_file_dialog(monkeypatch, (str(path),))
    app.add_attachment_files()
    app.cc.set("cc@example.com")
    app.bcc.set("bcc@example.com")
    _answer_name_prompt(monkeypatch, "With extras")

    app.save_template_as()

    app.cc.set("")
    app.bcc.set("")
    app.attachments = []
    app._refresh_attachment_widget()
    app.template_display.set("With extras")
    app.on_template_selected()

    assert app.cc.get() == "cc@example.com"
    assert app.bcc.get() == "bcc@example.com"
    assert app.attachments == [str(path)]
