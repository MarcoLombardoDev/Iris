# Iris — Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# Distributed WITHOUT ANY WARRANTY; see LICENSE for the full terms.
# A commercial licence, without the AGPL's obligations, is available for use
# in proprietary or closed-source products — see COMMERCIAL-LICENSE.md.

"""The check the release workflow runs against every bundle it builds.

``--version`` is not a smoke test. argparse prints the version and exits
during argument parsing, before Tk is imported and before a single one of the
product's own modules is loaded, so it proves the frozen interpreter and the
bundled standard library work and nothing else. A bundle whose Tcl/Tk
libraries were not collected passes it. So does one that cannot save a file.
Both then fail on the user's machine, after the release is published.

Two things are checked here instead, because these are the two ways a frozen
bundle actually breaks:

**The toolkit starts.** Creating a Tk root is what makes Tcl go looking for
its script library and Tk for its own, and both are data directories that
PyInstaller has to have collected. The windowing system is reported rather
than assumed — a Linux bundle must come up on ``x11``, and the workflow fails
the build if it does not, because "Tk started" under some fallback is exactly
the result that would hide a broken bundle.

**A file is written and read back.** This is where a frozen application
breaks: a data directory PyInstaller did not collect, a shared library it did
not find. Those failures happen the first time a user saves, not at startup,
and the test suite cannot see them either — it runs against an installed
package, where nothing is missing.

Nothing is left behind: everything is written inside a temporary directory
that goes away with it. A smoke test that litters the user's disk is its own
bug report.
"""

from __future__ import annotations

from iris.version import APP_NAME, __version__


def _toolkit() -> list[str]:
    """Start Tk for real and report what backend it came up on.

    Withdrawn immediately: the point is that the toolkit loaded, not that
    anything is shown, and a window flashing up on a build runner would be a
    nuisance at best. ``destroy`` runs whatever happens, so the process can
    still exit cleanly when the report is being written.
    """
    import tkinter

    root = tkinter.Tk()
    try:
        root.withdraw()
        return [
            f"windowing system: {root.tk.call('tk', 'windowingsystem')}",
            f"tk version: {root.tk.call('info', 'patchlevel')}",
        ]
    finally:
        root.destroy()


def _round_trip() -> str:
    """Read a recipient out of a spreadsheet, write a message, read it back.

    These are the two halves of what Iris does, and each exercises a part of
    the bundle that startup does not. openpyxl is read *and* written here on
    purpose: the write is how a spreadsheet gets made without a fixture, and
    the read is the code path the product actually uses. Saving the message
    goes through ``msgwriter.save_eml`` rather than around it, so the check
    covers the function a user's Send button reaches.
    """
    import tempfile
    from email import policy
    from email.message import EmailMessage
    from email.parser import BytesParser
    from pathlib import Path

    from openpyxl import Workbook

    from iris import msgwriter, parsers

    address = "self.check@example.invalid"
    company = "Self Check S.p.A."

    with tempfile.TemporaryDirectory(prefix="iris-self-check-") as directory:
        spreadsheet = Path(directory) / "recipients.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Company", "Email"])
        sheet.append([company, address])
        workbook.save(spreadsheet)

        recipients = parsers.extract_from_xlsx(str(spreadsheet))
        if [r.email for r in recipients] != [address]:
            raise RuntimeError(f"the recipient did not come back: {recipients}")

        message = EmailMessage()
        message["From"] = "noreply@example.invalid"
        message["To"] = address
        message["Subject"] = "Iris self-check"
        message.set_content("This message exists so a build can be checked.")
        message.add_attachment(
            spreadsheet.read_bytes(),
            maintype="application",
            subtype=("vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            filename=spreadsheet.name,
        )

        saved = msgwriter.save_eml(message, str(Path(directory) / "self-check.eml"))
        with open(saved, "rb") as handle:
            reloaded = BytesParser(policy=policy.default).parse(handle)

        if reloaded["To"] != address:
            raise RuntimeError("the recipient did not survive the round trip")
        attachments = list(reloaded.iter_attachments())
        if len(attachments) != 1:
            raise RuntimeError(f"expected one attachment, got {len(attachments)}")
        if attachments[0].get_content() != spreadsheet.read_bytes():
            raise RuntimeError("the attachment came back changed")
        size = Path(saved).stat().st_size

    return (
        f"read 1 recipient from a spreadsheet, wrote a {size}-byte message, "
        f"read back 1 attachment of {len(attachments[0].get_content())} bytes"
    )


def run(report_path: str | None = None) -> int:
    """Run the check, print the report, and return an exit code.

    The report is written to a file as well as printed because two of these
    three products are built ``--windowed`` on Windows, where the process has
    no stdout at all and ``print`` is a no-op. Parsing stdout would work on
    Linux and macOS and silently check nothing on Windows, which is the
    platform whose bundles are least like the machine they were built on.
    """
    lines = [f"{APP_NAME} {__version__}"]
    ok = True

    try:
        lines += _toolkit()
    except Exception as exc:  # noqa: BLE001 - the report is the error handler
        lines.append(f"windowing system: FAILED — {exc}")
        ok = False

    try:
        lines.append(f"round trip: {_round_trip()}")
    except Exception as exc:  # noqa: BLE001 - as above
        lines.append(f"round trip: FAILED — {exc}")
        ok = False

    report = "\n".join(lines)
    print(report)
    if report_path:
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
    return 0 if ok else 1
