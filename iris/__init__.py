# Iris — Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# Distributed WITHOUT ANY WARRANTY; see LICENSE for the full terms.
# A commercial licence, without the AGPL's obligations, is available for use
# in proprietary or closed-source products — see COMMERCIAL-LICENSE.md.

"""Support library for Iris - Email Sender.

Holds the application logic (document parsing, message composition and
sending, configuration handling, translations) separated from the graphical
interface, so it can be tested without a display.
"""

from .version import APP_NAME, APP_TITLE, __version__

__all__ = ["APP_NAME", "APP_TITLE", "__version__"]
