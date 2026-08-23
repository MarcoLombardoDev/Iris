# Iris — Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# Distributed WITHOUT ANY WARRANTY; see LICENSE for the full terms.
# A commercial licence, without the AGPL's obligations, is available for use
# in proprietary or closed-source products — see COMMERCIAL-LICENSE.md.

"""Reading and writing ``config.ini``.

The file is looked up in several locations so that configurations written by
older versions keep working, and so the application still works when the
executable lives in a read-only folder.
"""

import base64
import configparser
import os
from dataclasses import asdict, dataclass, field, replace
from typing import List, Optional

from . import paths
from .i18n import DEFAULT_LANGUAGE, normalize_language, set_language, t

CONFIG_FILENAME = "config.ini"
SECTION = "EMAIL"

#: Prefix of the sections holding a saved sender profile / email template.
#: Keeping them in their own sections leaves ``[EMAIL]`` — the settings
#: currently in use — exactly as earlier versions wrote it.
PROFILE_PREFIX = "PROFILE:"
TEMPLATE_PREFIX = "TEMPLATE:"

#: Characters that cannot appear in a profile or template name: they would
#: break the ``[SECTION]`` header the name is stored in.
_FORBIDDEN_NAME_CHARS = "[]"

#: Prefix used for obfuscated passwords.
#: WARNING: this is obfuscation, not encryption. It only prevents the password
#: from being readable at a glance; ``config.ini`` must still be protected
#: (never share it, never commit it).
_OBFUSCATION_PREFIX = "b64:"

#: Separator between attachment paths in the ``attachments`` key. A pipe is
#: illegal in Windows filenames, so it can never appear inside a real path.
_ATTACHMENT_SEP = "|"

_ENCODINGS = ("utf-8", "utf-8-sig", "windows-1252", "iso-8859-1", "cp1252")


def clean_name(value: str) -> str:
    """Return a profile/template name usable as a section header.

    Whitespace is collapsed (a newline would split the header in two) and the
    square brackets are dropped. An unusable name comes back empty, which the
    callers treat as "refuse to save".
    """
    name = " ".join(str(value or "").split())
    for char in _FORBIDDEN_NAME_CHARS:
        name = name.replace(char, "")
    return name.strip()


@dataclass
class SenderProfile:
    """A named set of sender and SMTP settings."""

    name: str = ""
    sender_email: str = ""
    smtp_server: str = ""
    smtp_port: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    connection_type: str = "starttls"


@dataclass
class MessageTemplate:
    """A named subject/body/Cc/Bcc/attachments set."""

    name: str = ""
    email_subject: str = ""
    email_body: str = ""
    email_cc: str = ""
    email_bcc: str = ""
    attachments: List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    """Contents of ``config.ini``."""

    sender_email: str = ""
    smtp_server: str = ""
    smtp_port: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    connection_type: str = "starttls"
    email_subject: str = ""
    email_body: str = ""
    email_cc: str = ""
    email_bcc: str = ""
    attachments: List[str] = field(default_factory=list)
    language: str = DEFAULT_LANGUAGE
    send_delay: str = "0"
    profiles: List[SenderProfile] = field(default_factory=list)
    templates: List[MessageTemplate] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def profile(self, name: str) -> Optional[SenderProfile]:
        """Return the saved profile called ``name`` (case-insensitive)."""
        wanted = clean_name(name).lower()
        return next((item for item in self.profiles if item.name.lower() == wanted), None)

    def template(self, name: str) -> Optional[MessageTemplate]:
        """Return the saved template called ``name`` (case-insensitive)."""
        wanted = clean_name(name).lower()
        return next((item for item in self.templates if item.name.lower() == wanted), None)


#: Fields of :class:`AppConfig` stored as plain keys in ``[EMAIL]``.
#: ``attachments`` is not here: it is a list, joined with ``_ATTACHMENT_SEP``
#: by :func:`save` like the profile/template sections are handled specially.
_SCALAR_FIELDS = (
    "sender_email",
    "smtp_server",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "connection_type",
    "email_subject",
    "email_body",
    "email_cc",
    "email_bcc",
    "language",
    "send_delay",
)


def _parse_attachments(value: str) -> List[str]:
    """Split the ``attachments`` key into individual paths."""
    return [item for item in (part.strip() for part in value.split(_ATTACHMENT_SEP)) if item]


def _format_attachments(paths: List[str]) -> str:
    """Join attachment paths for storage."""
    return _ATTACHMENT_SEP.join(path for path in paths if path)


def _read_attachments(section) -> List[str]:
    """Read ``attachments``, falling back to the pre-2.3 ``attachment_path``.

    Files written before multiple attachments existed have a single
    ``attachment_path`` key; ``attachments`` is only absent on those files,
    never merely empty, so ``None`` (not ``""``) is the right sentinel here.
    """
    raw = section.get("attachments")
    if raw is not None:
        return _parse_attachments(raw)
    legacy = section.get("attachment_path", "")
    return [legacy] if legacy else []


@dataclass
class LoadResult:
    """Outcome of a configuration load."""

    config: AppConfig = field(default_factory=AppConfig)
    path: Optional[str] = None
    encoding: Optional[str] = None
    messages: List[str] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.path is not None


def obfuscate(value: str) -> str:
    """Obfuscate the password before writing it to disk."""
    if not value:
        return ""
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    return _OBFUSCATION_PREFIX + encoded


def deobfuscate(value: str) -> str:
    """Read an obfuscated or plain password (backward compatibility)."""
    if not value:
        return ""
    if not value.startswith(_OBFUSCATION_PREFIX):
        return value
    try:
        return base64.b64decode(value[len(_OBFUSCATION_PREFIX):].encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def candidate_paths() -> List[str]:
    """Locations where ``config.ini`` is looked up, in priority order."""
    seen = []
    for directory in (paths.app_dir(), os.getcwd(), paths.user_data_dir()):
        candidate = os.path.join(directory, CONFIG_FILENAME)
        if candidate not in seen:
            seen.append(candidate)
    return seen


def default_save_path() -> str:
    """Path the configuration is written to."""
    for candidate in candidate_paths():
        if os.path.exists(candidate):
            directory = os.path.dirname(candidate)
            if paths.is_writable_dir(directory):
                return candidate
    return os.path.join(paths.writable_app_dir(), CONFIG_FILENAME)


def _read_profiles(parser: configparser.ConfigParser) -> List[SenderProfile]:
    """Read every ``[PROFILE:name]`` section, sorted by name."""
    profiles = []
    for header in parser.sections():
        if not header.startswith(PROFILE_PREFIX):
            continue
        name = clean_name(header[len(PROFILE_PREFIX):])
        if not name:
            continue
        section = parser[header]
        profiles.append(
            SenderProfile(
                name=name,
                sender_email=section.get("sender_email", ""),
                smtp_server=section.get("smtp_server", ""),
                smtp_port=section.get("smtp_port", ""),
                smtp_user=section.get("smtp_user", ""),
                smtp_password=deobfuscate(section.get("smtp_password", "")),
                connection_type=section.get("connection_type", "starttls").strip().lower(),
            )
        )
    return sorted(profiles, key=lambda item: item.name.lower())


def _read_templates(parser: configparser.ConfigParser) -> List[MessageTemplate]:
    """Read every ``[TEMPLATE:name]`` section, sorted by name."""
    templates = []
    for header in parser.sections():
        if not header.startswith(TEMPLATE_PREFIX):
            continue
        name = clean_name(header[len(TEMPLATE_PREFIX):])
        if not name:
            continue
        section = parser[header]
        templates.append(
            MessageTemplate(
                name=name,
                email_subject=section.get("email_subject", ""),
                email_body=section.get("email_body", ""),
                email_cc=section.get("email_cc", ""),
                email_bcc=section.get("email_bcc", ""),
                attachments=_read_attachments(section),
            )
        )
    return sorted(templates, key=lambda item: item.name.lower())


def load(path: Optional[str] = None, apply_language: bool = True) -> LoadResult:
    """Load the configuration from ``path`` or from the first location found.

    With ``apply_language`` (the default) the stored language preference is
    applied through :func:`iris.i18n.set_language` as soon as it is
    read, so the messages in :attr:`LoadResult.messages` come back already
    translated. Pass ``False`` when reloading the file must not change the
    language currently in use — see :func:`update_language`.
    """
    result = LoadResult()
    search = [path] if path else candidate_paths()

    config_path = next(
        (candidate for candidate in search if candidate and os.path.exists(candidate)), None
    )
    if config_path is None:
        searched = ", ".join(candidate for candidate in search if candidate)
        result.messages.append(
            t("configfile.not_found", searched=searched, path=default_save_path())
        )
        return result

    parser = configparser.ConfigParser(interpolation=None)
    last_error = None
    for encoding in _ENCODINGS:
        try:
            parser.read(config_path, encoding=encoding)
            result.encoding = encoding
            break
        except (UnicodeDecodeError, configparser.Error) as exc:
            last_error = exc
            parser = configparser.ConfigParser(interpolation=None)
            continue

    if result.encoding is None:
        result.messages.append(t("configfile.read_error", path=config_path, error=last_error))
        return result

    result.path = config_path
    if SECTION not in parser:
        result.messages.append(t("configfile.section_missing", section=SECTION, path=config_path))
        return result

    section = parser[SECTION]

    # Apply the language first: everything logged afterwards is translated.
    language = normalize_language(section.get("language", DEFAULT_LANGUAGE))
    if apply_language:
        set_language(language)

    result.config = AppConfig(
        sender_email=section.get("sender_email", ""),
        smtp_server=section.get("smtp_server", ""),
        smtp_port=section.get("smtp_port", ""),
        smtp_user=section.get("smtp_user", ""),
        smtp_password=deobfuscate(section.get("smtp_password", "")),
        connection_type=section.get("connection_type", "starttls").strip().lower(),
        email_subject=section.get("email_subject", ""),
        email_body=section.get("email_body", ""),
        email_cc=section.get("email_cc", ""),
        email_bcc=section.get("email_bcc", ""),
        attachments=_read_attachments(section),
        language=language,
        send_delay=section.get("send_delay", "0"),
        profiles=_read_profiles(parser),
        templates=_read_templates(parser),
    )
    return result


def save(config: AppConfig, path: Optional[str] = None) -> str:
    """Write the configuration as UTF-8 and return the path used."""
    config_path = path or default_save_path()
    directory = os.path.dirname(os.path.abspath(config_path))
    os.makedirs(directory, exist_ok=True)

    parser = configparser.ConfigParser(interpolation=None)
    values = {name: getattr(config, name) for name in _SCALAR_FIELDS}
    values["smtp_password"] = obfuscate(config.smtp_password)
    values["language"] = normalize_language(config.language)
    values["attachments"] = _format_attachments(config.attachments)
    parser[SECTION] = values

    for profile in sorted(config.profiles, key=lambda item: item.name.lower()):
        name = clean_name(profile.name)
        if not name:
            continue
        parser[PROFILE_PREFIX + name] = {
            "sender_email": profile.sender_email,
            "smtp_server": profile.smtp_server,
            "smtp_port": profile.smtp_port,
            "smtp_user": profile.smtp_user,
            "smtp_password": obfuscate(profile.smtp_password),
            "connection_type": profile.connection_type,
        }

    for template in sorted(config.templates, key=lambda item: item.name.lower()):
        name = clean_name(template.name)
        if not name:
            continue
        parser[TEMPLATE_PREFIX + name] = {
            "email_subject": template.email_subject,
            "email_body": template.email_body,
            "email_cc": template.email_cc,
            "email_bcc": template.email_bcc,
            "attachments": _format_attachments(template.attachments),
        }

    with open(config_path, "w", encoding="utf-8") as handle:
        parser.write(handle)

    # Restrict permissions on POSIX: the file holds credentials.
    if os.name == "posix":
        try:
            os.chmod(config_path, 0o600)
        except OSError:
            pass
    return config_path


def update_language(language: str, path: Optional[str] = None) -> str:
    """Persist only the language preference, keeping the rest untouched.

    Used by the language selector, which must not overwrite fields the user is
    still editing.
    """
    config_path = path or default_save_path()
    # apply_language=False: reloading the file must not undo the language the
    # caller just selected (the file still holds the previous value).
    existing = load(config_path, apply_language=False)
    config = existing.config
    config.language = normalize_language(language)
    return save(config, config_path)


# ---------------------------------------------------------------------------
# Saved profiles and templates
# ---------------------------------------------------------------------------
# Like update_language, these touch one entry and leave everything else in the
# file untouched: the user may well be editing other fields at the same time.
def _reload_for_edit(path: Optional[str]) -> "tuple[str, AppConfig]":
    config_path = path or default_save_path()
    return config_path, load(config_path, apply_language=False).config


def save_profile(profile: SenderProfile, path: Optional[str] = None) -> str:
    """Add or replace a sender profile, keeping the rest of the file intact."""
    name = clean_name(profile.name)
    if not name:
        raise ValueError(t("validate.name_required"))

    config_path, config = _reload_for_edit(path)
    config.profiles = [item for item in config.profiles if item.name.lower() != name.lower()]
    config.profiles.append(replace(profile, name=name))
    return save(config, config_path)


def delete_profile(name: str, path: Optional[str] = None) -> str:
    """Remove a sender profile; unknown names are a no-op."""
    wanted = clean_name(name).lower()
    config_path, config = _reload_for_edit(path)
    config.profiles = [item for item in config.profiles if item.name.lower() != wanted]
    return save(config, config_path)


def save_template(template: MessageTemplate, path: Optional[str] = None) -> str:
    """Add or replace an email template, keeping the rest of the file intact."""
    name = clean_name(template.name)
    if not name:
        raise ValueError(t("validate.name_required"))

    config_path, config = _reload_for_edit(path)
    config.templates = [item for item in config.templates if item.name.lower() != name.lower()]
    config.templates.append(replace(template, name=name))
    return save(config, config_path)


def delete_template(name: str, path: Optional[str] = None) -> str:
    """Remove an email template; unknown names are a no-op."""
    wanted = clean_name(name).lower()
    config_path, config = _reload_for_edit(path)
    config.templates = [item for item in config.templates if item.name.lower() != wanted]
    return save(config, config_path)
