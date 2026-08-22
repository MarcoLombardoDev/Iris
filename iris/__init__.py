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
"""Support library for Iris - Email Sender.

Holds the application logic (document parsing, message composition and
sending, configuration handling, translations) separated from the graphical
interface, so it can be tested without a display.
"""

from .version import APP_NAME, APP_TITLE, __version__

__all__ = ["APP_NAME", "APP_TITLE", "__version__"]
