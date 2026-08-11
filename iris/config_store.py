# -*- coding: utf-8 -*-
"""Reading and writing ``config.ini``.

The file is looked up in several locations so that configurations written by
older versions keep working, and so the application still works when the
executable lives in a read-only folder.
"""

import base64
import configparser
import os
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from . import paths
from .i18n import DEFAULT_LANGUAGE, normalize_language, set_language, t

CONFIG_FILENAME = "config.ini"
SECTION = "EMAIL"

#: Prefix used for obfuscated passwords.
#: WARNING: this is obfuscation, not encryption. It only prevents the password
#: from being readable at a glance; ``config.ini`` must still be protected
#: (never share it, never commit it).
_OBFUSCATION_PREFIX = "b64:"

_ENCODINGS = ("utf-8", "utf-8-sig", "windows-1252", "iso-8859-1", "cp1252")


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
    attachment_path: str = ""
    language: str = DEFAULT_LANGUAGE

    def as_dict(self) -> dict:
        return asdict(self)


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
        attachment_path=section.get("attachment_path", ""),
        language=language,
    )
    return result


def save(config: AppConfig, path: Optional[str] = None) -> str:
    """Write the configuration as UTF-8 and return the path used."""
    config_path = path or default_save_path()
    directory = os.path.dirname(os.path.abspath(config_path))
    os.makedirs(directory, exist_ok=True)

    parser = configparser.ConfigParser(interpolation=None)
    values = config.as_dict()
    values["smtp_password"] = obfuscate(config.smtp_password)
    values["language"] = normalize_language(config.language)
    parser[SECTION] = values

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
