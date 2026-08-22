# -*- coding: utf-8 -*-
"""Tests for reading and writing config.ini."""

import os

import pytest

from iris import config_store, i18n


def make_config(**kwargs):
    defaults = dict(
        sender_email="sender@example.com",
        smtp_server="smtp.example.com",
        smtp_port="587",
        smtp_user="user",
        smtp_password="s3cret",
        connection_type="starttls",
        email_subject="Notice for {COMPANY}",
        email_body="Dear {COMPANY},\ngood morning.",
        email_cc="",
        email_bcc="",
        attachments=[],
        language="en",
    )
    defaults.update(kwargs)
    return config_store.AppConfig(**defaults)


def test_save_and_reload(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(), path)
    result = config_store.load(path)

    assert result.found
    assert result.config == make_config()


def test_password_is_not_stored_in_clear(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(), path)
    content = (tmp_path / "config.ini").read_text(encoding="utf-8")
    assert "s3cret" not in content
    assert config_store.load(path).config.smtp_password == "s3cret"


def test_plain_password_stays_readable(tmp_path):
    """config.ini files written by earlier versions must keep working."""
    path = tmp_path / "config.ini"
    path.write_text(
        "[EMAIL]\n"
        "sender_email = sender@example.com\n"
        "smtp_password = oldPassword\n"
        "connection_type = ssl\n",
        encoding="utf-8",
    )
    result = config_store.load(str(path))
    assert result.config.smtp_password == "oldPassword"
    assert result.config.connection_type == "ssl"


def test_non_ascii_and_percent_sign(tmp_path):
    """A % in the body used to break configparser interpolation."""
    path = str(tmp_path / "config.ini")
    config = make_config(email_body="100% discount for the city of {COMPANY} — città")
    config_store.save(config, path)
    assert config_store.load(path).config.email_body == config.email_body


def test_windows_encoded_file(tmp_path):
    path = tmp_path / "config.ini"
    path.write_bytes(
        "[EMAIL]\nsender_email = sender@example.com\nemail_body = Società à\n".encode("cp1252")
    )
    result = config_store.load(str(path))
    assert result.found
    assert "Societ" in result.config.email_body


def test_missing_file(tmp_path):
    result = config_store.load(str(tmp_path / "missing.ini"))
    assert not result.found
    assert result.messages


def test_missing_section(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text("[OTHER]\nkey = value\n", encoding="utf-8")
    result = config_store.load(str(path))
    assert result.found
    assert result.config == config_store.AppConfig()
    assert any("EMAIL" in message for message in result.messages)


@pytest.mark.parametrize("value", ["", "password", "pàssword with spaces and %"])
def test_obfuscation_round_trip(value):
    assert config_store.deobfuscate(config_store.obfuscate(value)) == value


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions")
def test_restricted_permissions(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(), path)
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"


def test_missing_file_message_lists_the_paths(tmp_path, monkeypatch):
    """The log must say where the file was searched and where it will be created."""
    from iris import paths

    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    monkeypatch.setattr(paths, "writable_app_dir", lambda: str(tmp_path))
    monkeypatch.chdir(tmp_path)

    result = config_store.load()

    assert not result.found
    assert len(result.messages) == 1
    assert str(tmp_path) in result.messages[0]
    assert "config.ini" in result.messages[0]


# --------------------------------------------------------------------------
# Language
# --------------------------------------------------------------------------
def test_language_defaults_to_english(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text("[EMAIL]\nsender_email = sender@example.com\n", encoding="utf-8")
    assert config_store.load(str(path)).config.language == "en"
    assert i18n.get_language() == "en"


def test_loading_applies_the_stored_language(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(language="it"), path)

    result = config_store.load(path)

    assert result.config.language == "it"
    assert i18n.get_language() == "it"


def test_unknown_language_falls_back(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text("[EMAIL]\nlanguage = klingon\n", encoding="utf-8")
    assert config_store.load(str(path)).config.language == "en"


def test_update_language_keeps_the_other_values(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(), path)

    config_store.update_language("it", path)

    reloaded = config_store.load(path).config
    assert reloaded.language == "it"
    assert reloaded.sender_email == "sender@example.com"
    assert reloaded.smtp_password == "s3cret"
    assert reloaded.email_body == make_config().email_body


def test_update_language_creates_the_file_when_missing(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.update_language("it", path)
    assert config_store.load(path).config.language == "it"


def test_update_language_does_not_reapply_the_old_one(tmp_path):
    """Regression: switching back used to be undone by the reload.

    ``update_language`` reloads the file to preserve the other values, and
    ``load`` applies the language it finds — which was still the previous one,
    silently reverting the user's choice.
    """
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(language="it"), path)
    i18n.set_language("en")

    config_store.update_language("en", path)

    assert i18n.get_language() == "en"
    assert config_store.load(path).config.language == "en"


def test_load_can_leave_the_language_untouched(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(language="it"), path)
    i18n.set_language("en")

    result = config_store.load(path, apply_language=False)

    assert result.config.language == "it"
    assert i18n.get_language() == "en"


# --------------------------------------------------------------------------
# Sender profiles and email templates
# --------------------------------------------------------------------------
def test_profiles_and_templates_round_trip(tmp_path):
    path = str(tmp_path / "config.ini")
    config = make_config(
        profiles=[
            config_store.SenderProfile(
                name="Work",
                sender_email="work@example.com",
                smtp_server="smtp.work.example",
                smtp_port="587",
                smtp_user="user",
                smtp_password="p4ss",
                connection_type="starttls",
            )
        ],
        templates=[
            config_store.MessageTemplate(
                name="Reminder",
                email_subject="Hello {COMPANY}",
                email_body="Body text",
                email_cc="accounting@example.com",
                email_bcc="archive@example.com",
                attachments=["/tmp/notice.pdf", "/tmp/terms.pdf"],
            )
        ],
    )
    config_store.save(config, path)
    reloaded = config_store.load(path).config

    assert [item.name for item in reloaded.profiles] == ["Work"]
    assert reloaded.profiles[0].smtp_server == "smtp.work.example"
    assert reloaded.profiles[0].smtp_password == "p4ss"
    assert [item.name for item in reloaded.templates] == ["Reminder"]
    assert reloaded.templates[0].email_subject == "Hello {COMPANY}"
    assert reloaded.templates[0].email_cc == "accounting@example.com"
    assert reloaded.templates[0].email_bcc == "archive@example.com"
    assert reloaded.templates[0].attachments == ["/tmp/notice.pdf", "/tmp/terms.pdf"]


def test_a_profile_password_is_not_stored_in_clear(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save_profile(
        config_store.SenderProfile(name="Work", smtp_password="topsecret"), path
    )
    assert "topsecret" not in (tmp_path / "config.ini").read_text(encoding="utf-8")
    assert config_store.load(path).config.profile("Work").smtp_password == "topsecret"


def test_saving_a_profile_keeps_the_other_values(tmp_path):
    """Adding a profile must not disturb the settings being edited."""
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(), path)

    config_store.save_profile(config_store.SenderProfile(name="Work"), path)

    reloaded = config_store.load(path).config
    assert reloaded.sender_email == "sender@example.com"
    assert reloaded.smtp_password == "s3cret"
    assert reloaded.email_body == make_config().email_body
    assert reloaded.profile("Work") is not None


def test_saving_the_same_name_replaces_the_entry(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save_profile(config_store.SenderProfile(name="Work", smtp_server="first"), path)
    config_store.save_profile(config_store.SenderProfile(name="work", smtp_server="second"), path)

    profiles = config_store.load(path).config.profiles
    assert len(profiles) == 1
    assert profiles[0].smtp_server == "second"


def test_delete_profile(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save_profile(config_store.SenderProfile(name="Work"), path)
    config_store.delete_profile("Work", path)
    assert config_store.load(path).config.profiles == []


def test_deleting_an_unknown_profile_is_harmless(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save_profile(config_store.SenderProfile(name="Work"), path)
    config_store.delete_profile("Missing", path)
    assert len(config_store.load(path).config.profiles) == 1


def test_templates_and_profiles_do_not_collide(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save_profile(config_store.SenderProfile(name="Work"), path)
    config_store.save_template(
        config_store.MessageTemplate(name="Work", email_subject="Subject"), path
    )

    config_store.delete_template("Work", path)

    config = config_store.load(path).config
    assert config.profile("Work") is not None
    assert config.templates == []


def test_profiles_come_back_sorted(tmp_path):
    path = str(tmp_path / "config.ini")
    for name in ("Zulu", "alpha", "Mike"):
        config_store.save_profile(config_store.SenderProfile(name=name), path)
    names = [item.name for item in config_store.load(path).config.profiles]
    assert names == ["alpha", "Mike", "Zulu"]


@pytest.mark.parametrize(
    "value,expected",
    [
        ("  Work  ", "Work"),
        ("Multi   space", "Multi space"),
        ("With[brackets]", "Withbrackets"),
        ("line\nbreak", "line break"),
        ("   ", ""),
        ("", ""),
    ],
)
def test_clean_name(value, expected):
    assert config_store.clean_name(value) == expected


def test_a_nameless_entry_is_refused(tmp_path):
    path = str(tmp_path / "config.ini")
    with pytest.raises(ValueError):
        config_store.save_profile(config_store.SenderProfile(name="  "), path)
    with pytest.raises(ValueError):
        config_store.save_template(config_store.MessageTemplate(name="[]"), path)


def test_a_name_with_brackets_is_stored_readable(tmp_path):
    """The name ends up in a section header, which brackets would break."""
    path = str(tmp_path / "config.ini")
    config_store.save_profile(config_store.SenderProfile(name="Acme [IT]"), path)
    assert [item.name for item in config_store.load(path).config.profiles] == ["Acme IT"]


# --------------------------------------------------------------------------
# Pause between messages
# --------------------------------------------------------------------------
def test_send_delay_round_trip(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(send_delay="2.5"), path)
    assert config_store.load(path).config.send_delay == "2.5"


def test_a_pre_2_1_file_loads_with_empty_libraries(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text("[EMAIL]\nsender_email = sender@example.com\n", encoding="utf-8")
    config = config_store.load(str(path)).config
    assert config.profiles == []
    assert config.templates == []
    assert config.send_delay == "0"


# --------------------------------------------------------------------------
# Multiple attachments and Cc/Bcc
# --------------------------------------------------------------------------
def test_multiple_attachments_round_trip(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(attachments=["/docs/a.pdf", "/docs/b.pdf"]), path)
    assert config_store.load(path).config.attachments == ["/docs/a.pdf", "/docs/b.pdf"]


def test_cc_and_bcc_round_trip(tmp_path):
    path = str(tmp_path / "config.ini")
    config_store.save(
        make_config(email_cc="a@example.com, b@example.com", email_bcc="c@example.com"), path
    )
    reloaded = config_store.load(path).config
    assert reloaded.email_cc == "a@example.com, b@example.com"
    assert reloaded.email_bcc == "c@example.com"


def test_a_pre_2_3_file_reads_the_single_attachment_path(tmp_path):
    """config.ini written before multiple attachments existed used one key."""
    path = tmp_path / "config.ini"
    path.write_text(
        "[EMAIL]\nsender_email = sender@example.com\nattachment_path = /docs/notice.pdf\n",
        encoding="utf-8",
    )
    config = config_store.load(str(path)).config
    assert config.attachments == ["/docs/notice.pdf"]


def test_an_empty_legacy_attachment_path_yields_no_attachments(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text(
        "[EMAIL]\nsender_email = sender@example.com\nattachment_path =\n", encoding="utf-8"
    )
    assert config_store.load(str(path)).config.attachments == []


def test_a_legacy_template_attachment_path_still_loads(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text(
        "[EMAIL]\nsender_email = sender@example.com\n\n"
        "[TEMPLATE:Old]\nemail_subject = Hi\nattachment_path = /docs/old.pdf\n",
        encoding="utf-8",
    )
    template = config_store.load(str(path)).config.template("Old")
    assert template.attachments == ["/docs/old.pdf"]


def test_saving_never_writes_the_legacy_key(tmp_path):
    """Once saved by this version, the file uses `attachments` only."""
    path = str(tmp_path / "config.ini")
    config_store.save(make_config(attachments=["/docs/a.pdf"]), path)
    content = (tmp_path / "config.ini").read_text(encoding="utf-8")
    assert "attachments = /docs/a.pdf" in content
    assert "attachment_path" not in content
