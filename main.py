#!/usr/bin/env python
# Iris — Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# Distributed WITHOUT ANY WARRANTY; see LICENSE for the full terms.
# A commercial licence, without the AGPL's obligations, is available for use
# in proprietary or closed-source products — see COMMERCIAL-LICENSE.md.

"""Entry point of Iris - Email Sender."""

import argparse
import sys
import traceback

from iris.version import APP_NAME, APP_TITLE, __version__


def _show_startup_error(exc):
    """Show a start-up error in a window, falling back to the console."""
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"FATAL START-UP ERROR:\n{details}", file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Fatal error",
            f"The application could not start:\n\n{exc}\n\nIt will now close.",
        )
        root.destroy()
    except Exception:
        pass


def _parse_args():
    """Handle ``--version``, ``--self-check`` and ``--help``.

    Returns an exit code when one of them was asked for, or None to carry on
    and open the window.

    Iris is a GUI application, but the release workflow runs every bundle
    it builds before offering it for download. ``--version`` is the cheap half
    of that — a binary that cannot report its own version is broken — and
    ``--self-check`` is the half that means something: it starts Tk and writes
    a file, which is where a frozen bundle actually breaks. Both are parsed
    here, before the GUI is imported, so ``--version`` stays instant.
    """
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=APP_TITLE,
        epilog="Run without arguments to open the interface.",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help="print the version and exit",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help=(
            "check a built bundle can start Tk and write and read back a message, then exit"
        ),
    )
    parser.add_argument(
        "--self-check-report",
        metavar="FILE",
        help="also write the self-check report here; a --windowed build has "
             "no stdout to read it from",
    )
    args, unknown = parser.parse_known_args()
    if unknown:
        parser.error(f"unrecognised arguments: {' '.join(unknown)}")
    if args.self_check:
        from iris import selfcheck

        return selfcheck.run(args.self_check_report)
    if args.version:
        # Deliberately not argparse's own "version" action: that one writes to
        # sys.stdout unconditionally, and a windowed PyInstaller build on
        # Windows may not have one. print() is a no-op when sys.stdout is
        # None, so the exit code stays 0 either way — which is what the
        # workflow's smoke test actually checks.
        print(f"{APP_NAME} {__version__}")
        return 0
    return None


def main():
    exit_code = _parse_args()
    if exit_code is not None:
        return exit_code

    try:
        from iris.gui import IrisApp, create_root
    except ImportError as exc:
        _show_startup_error(
            ImportError(
                f"{exc}\n\nMissing dependency: install the required packages with\n"
                "    pip install -r requirements.txt"
            )
        )
        return 1

    try:
        root = create_root()
        IrisApp(root)
        root.mainloop()
    except Exception as exc:
        _show_startup_error(exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
