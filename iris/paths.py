# -*- coding: utf-8 -*-
#
# Iris - Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the
# GNU Affero General Public License in LICENSE for details.
#
# A commercial licence, without the AGPL obligations, is available for use in
# proprietary or closed-source products - see COMMERCIAL-LICENSE.md.
"""Application paths, both when running from source and as a PyInstaller build."""

import os
import sys

APP_DIR_NAME = "Iris"


def is_frozen() -> bool:
    """True when the application runs as a PyInstaller executable."""
    return bool(getattr(sys, "frozen", False))


def app_dir() -> str:
    """Directory of the executable, or of the source tree.

    This is where the user expects to find ``config.ini``, ``logs/`` and the
    ``emails/`` folder.
    """
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bundle_dir() -> str:
    """Directory holding the resources bundled with the executable.

    PyInstaller *onefile* builds unpack them into ``sys._MEIPASS``; running
    from source this is simply the project directory.
    """
    if is_frozen():
        return getattr(sys, "_MEIPASS", app_dir())
    return app_dir()


def resource_path(name: str) -> str:
    """Absolute path of an application resource.

    Looks inside the bundle first and next to the executable afterwards, so a
    user can replace a bundled asset without rebuilding.
    """
    candidates = [os.path.join(bundle_dir(), name), os.path.join(app_dir(), name)]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


def user_data_dir() -> str:
    """Writable per-user fallback directory."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_DIR_NAME)


def is_writable_dir(path: str) -> bool:
    """True when files can actually be written into ``path``."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("ok")
        os.remove(probe)
        return True
    except Exception:
        return False


def writable_app_dir() -> str:
    """Writable directory for application data (config, logs, generated emails).

    Prefers the application directory; falls back to the user profile when it
    is read-only (for example an executable installed in ``C:\\Program Files``).
    """
    candidate = app_dir()
    if is_writable_dir(candidate):
        return candidate
    fallback = user_data_dir()
    os.makedirs(fallback, exist_ok=True)
    return fallback
