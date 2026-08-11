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
        attachment_path="",
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
