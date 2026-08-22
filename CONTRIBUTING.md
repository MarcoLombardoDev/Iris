# Contributing to Iris

Thanks for wanting to help. This file describes how the project works so a patch has a
good chance of being merged quickly.

## Ground rules

Iris is a **desktop application that sends the mail you already had a reason to
send**. Contributions that add address harvesting, list buying, open or click tracking,
telemetry, or anything else belonging to a marketing platform will not be merged,
regardless of how well they are written. The only server Iris contacts is the SMTP server
the user configured; keep it that way.

Never commit `config.ini`, real credentials, or real recipient lists. Samples and fixtures
use the reserved `example.com` / `.example` domains.

## The Contributor License Agreement

Iris is dual-licensed: AGPL-3.0 for everyone, and commercial terms for those who cannot
accept the AGPL's obligations. That is only possible if one party can license the whole
work both ways, so **every contributor must agree to the
[Contributor License Agreement](CLA.md)** before a pull request can be merged.

> **To agree:** include
> `I have read and agree to the Contributor License Agreement (CLA.md).`
> in your pull request description. Your first pull request constitutes your agreement.

You keep the copyright in your work, and you receive a perpetual, royalty-free commercial
licence to Iris for your own use — see
[COMMERCIAL-LICENSE.md §12](COMMERCIAL-LICENSE.md#12-contributors).

## Getting set up

```bash
git clone https://github.com/MarcoLombardoDev/Iris.git
cd Iris
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests -v
```

On Linux the GUI tests need a display:

```bash
xvfb-run -a python -m pytest tests
```

On Windows, `install_dependencies.bat`, `run.bat` and `test.bat` wrap the same commands.

## Before you write code

Read the *How it works* section of the README first. Two rules carry most of
the design:

1. **Only `iris/gui.py` may import Tkinter.** Everything else is plain logic, so it can be
   tested without a display, reused from a script, and debugged with a test rather than by
   clicking.
2. **Tkinter is not thread-safe.** Long operations — parsing, sending, file generation, the
   connection test — run on daemon threads, and every UI update is pushed through a queue
   drained by the main thread. Data read from widgets is collected on the main thread
   *before* a worker starts.

Two more, smaller but easy to get wrong:

- **User-facing strings go through `iris/i18n.py`, in both catalogues.** The test suite
  checks that every catalogue defines the same keys with the same placeholders.
- **`PIL._tkinter_finder` must stay in the PyInstaller hidden imports.** Without it
  `PIL.ImageTk` fails at runtime and the built executable will not start.

## Style

- Match the surrounding code: it is plain, unclever Python with no framework
  ceremony.
- Comments explain *why*, not *what*. If a line encodes a non-obvious fact about SMTP,
  Outlook or a document format, say so — the next person will not rediscover it.
- User-facing strings are sentences, not error codes, and they live in `iris/i18n.py`. A
  user must never see a Python traceback.

## Tests

New behaviour needs a test, and every bug fix arrives with a test that fails
without the fix.

- **No test ever sends a real email.** Delivery is verified against a minimal in-process
  SMTP server; anything else would be a bug in the test, not a shortcut.
- Parser, mailer and config tests need no display. GUI tests live in
  `tests/test_gui_smoke.py` and skip themselves where there is none.
- A new user-facing string needs an entry in both catalogues, or `tests/test_i18n.py`
  fails.

## Commits and pull requests

- One logical change per commit; a message that says what changed and why.
- Describe the user-visible effect in the pull request, and say how you tested it.
- Add an entry to `CHANGELOG.md` under *Unreleased*.
- If you changed anything documented in the README, update it in the same pull request.

## Reporting bugs

Include your operating system, your Python version, what you did, what you
expected and what happened. The *Log* tab and `logs/iris_YYYYMMDD.log` record every
operation in detail — attach the day's log file, **after checking it carries no real
addresses or credentials**. If a specific document fails to parse and you can share a
redacted version, that is usually the fastest route to a fix.
