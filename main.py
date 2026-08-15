#!/usr/bin/env python
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

"""Entry point of Iris - Email Sender."""

import sys
import traceback


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


def main():
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
