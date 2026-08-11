# -*- coding: utf-8 -*-
"""Support library for Iris - Email Sender.

Holds the application logic (document parsing, message composition and
sending, configuration handling, translations) separated from the graphical
interface, so it can be tested without a display.
"""

from .version import APP_NAME, APP_TITLE, __version__

__all__ = ["APP_NAME", "APP_TITLE", "__version__"]
