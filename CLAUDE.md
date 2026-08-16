# CLAUDE.md — Iris

Working notes for anyone (human or agent) changing this repository. It records the
invariants that are easy to break and the reasons behind decisions that look arbitrary
from the outside. `README.md` documents the product; this documents the project.

## What it is

A Tkinter desktop application that extracts *(company, email)* pairs from a document
(PDF, Excel, CSV, Word, text) and sends a templated email to each one over a single SMTP
connection — or writes `.msg` / `.eml` files instead of sending.

```
main.py              entry point, start-up error handling
iris/
├── gui.py           Tkinter layer: widgets, events, threads
├── i18n.py          translation catalogues (en, it) and helpers
├── parsers.py       recipient extraction, one function per format
├── mailer.py        message building, validation, SMTP sessions
├── msgwriter.py     .msg (Outlook) / .eml writing
├── config_store.py  config.ini reading and writing
├── paths.py         paths for source and frozen builds
└── version.py       version, naming, CONTACT_EMAIL
```

## Invariants — break these and something silently rots

**Only `gui.py` imports Tkinter.** Everything else is plain logic so it can be tested
without a display and reused from a script. New logic goes in the other modules, with
tests; `gui.py` only wires it to widgets.

**Every user-facing string goes through `i18n.t()`, in *both* catalogues.** The test
suite enforces that `en` and `it` define exactly the same keys with exactly the same
`{placeholders}`, and that the translations actually differ. A string added to one
catalogue only will fail the build.

**Tkinter is not thread-safe.** The rule the whole app follows:

- long operations (parsing, sending, generating, connection test) run on daemon threads;
- every UI update is pushed through `self.ui_queue` and drained on the main thread every
  100 ms by `process_ui_queue()`;
- widget values are read on the main thread *before* the worker starts, never inside it.

**Never reference an `except` variable from inside a lambda.** Python deletes the name
when the block ends, so the lambda fails later, on the UI thread, leaving the interface
stuck with disabled buttons. Read the message into a local first:

```python
except UnsupportedFormatError as exc:
    detail = str(exc)                                   # read it here
    self.run_on_ui(lambda: self._analysis_failed(detail))
```

There is a regression test for exactly this (`test_an_analysis_error_unblocks_the_interface`).

**`config.ini` backward compatibility is a hard requirement.** Files written by older
versions must keep loading. The layout is:

- `[EMAIL]` — the settings currently in use (this is what 1.x/2.0 wrote);
- `[PROFILE:name]` — one per saved sender profile;
- `[TEMPLATE:name]` — one per saved email template.

Anything that edits one entry (`update_language`, `save_profile`, `delete_template`, …)
reloads the file, changes only its own entry and writes back, so it never clobbers fields
the user is editing elsewhere. `save_config()` in the GUI must pass `profiles=` and
`templates=` or a full save wipes the saved libraries — there is a regression test.

**Passwords are obfuscated, not encrypted.** Base64 with a `b64:` prefix, `0600` on
POSIX. Never describe it as encryption in docs or UI. Each sender profile carries its own
password, so a `config.ini` with several profiles is proportionally more sensitive.

**Every dependency is imported where it is used.** A missing library degrades one feature
with a clear message instead of preventing start-up. Keep it that way.

**Version lives only in `iris/version.py`.** So does `CONTACT_EMAIL`, which the interface,
the README and `COMMERCIAL-LICENSE.md` all quote — change it in one place.

## Dependency licence hygiene — now a commercial commitment

`COMMERCIAL-LICENSE.md` tells buyers that **no dependency imposes copyleft**. That
sentence has to stay true.

Before adding a dependency, check its licence. Permissive (MIT / BSD / Apache-2.0 / PSF /
HPND) is fine. Copyleft or "dual AGPL-or-pay" is not, because a commercial Iris licence
cannot relicense someone else's code and the buyer would need a second licence.

This is not hypothetical: PDF reading used to use **PyMuPDF**, dual-licensed by Artifex
under AGPL-3.0 or a paid commercial licence. It was replaced with `pypdf` (BSD-3-Clause)
in 2.2.0 for this reason alone. PyMuPDF was only ever used for one call — the page text —
so the swap changed nothing functionally. If you are tempted to bring it back for
rendering or OCR, that decision costs the commercial offer its clean bill of health.

PyInstaller is GPL-2.0 **with the bootloader exception**, which exists precisely to allow
proprietary frozen applications — that one is fine.

## Testing

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests -v          # GUI tests need a display
xvfb-run -a python -m pytest tests # on a headless Linux box
```

On Debian/Ubuntu `tkinter` ships separately: `sudo apt-get install python3-tk`. Without a
display the GUI tests skip themselves and the rest still runs — **do not treat a skipped
GUI suite as a passing one**, it hides real breakage in `gui.py`.

**No test ever sends a real email.** Delivery is verified against a minimal in-process
SMTP server (`tests/test_smtp_integration.py::TinySMTPServer`).

Conventions that keep the suite honest:

- every bug fix arrives with a test that fails without the fix;
- PDF tests build a real PDF **byte by byte** (`_minimal_pdf` in `test_parsers.py`) rather
  than pulling in a PDF-writing dependency;
- the pause between messages is tested by injecting `sleep=` into `send_bulk()`, so no
  test ever actually waits;
- `tests/conftest.py` resets the language before and after each test — `config_store.load()`
  applies the stored language globally and would otherwise leak between tests.

## Screenshots

`docs/screenshots/*.png` are generated, not hand-taken. After any UI change:

```bash
xvfb-run -a python docs/generate_screenshots.py                 # English
LANG_CODE=it xvfb-run -a python docs/generate_screenshots.py    # Italian
```

It boots the real application with in-memory sample data — no config written, no network.
All sample data must stay fictitious: reserved `.example` domains, fake servers, a
placeholder password. Check the result: the configuration tab is dense and a too-long
label gets silently truncated rather than raising.

## Building the executable

```bash
python build.py            # or: pyinstaller Iris.spec
```

`PIL._tkinter_finder` must stay in the hidden imports: without it `PIL.ImageTk` fails at
runtime, ttkbootstrap cannot build its theme, every themed widget raises, and the
executable will not start. When a dependency changes, update the hidden imports in **both**
`build.py` and `Iris.spec`.

Do not run `pyinstaller --name=Iris main.py` from the project root — it overwrites
`Iris.spec` with absolute paths from the build machine.

## Commercial model — keep it aligned with Argus and Proteus

Iris is one of three dual-licensed products (with **Argus** and **Proteus**) that
deliberately share **the same commercial offer**, differing only in price, scope wording
and the third-party review. Changing the shape of the offer here means changing it in all
three, or the alignment is lost.

The parts that must stay identical:

- **`COMMERCIAL-LICENSE.md`, same eleven sections**, same tier ladder: Community /
  Internal / OEM & Redistribution / Enterprise, plus a perpetual option on Internal or
  OEM scope.
- **Email is the only commercial channel.** GitHub Issues are for bugs and features.
- **Email support is included at every paid tier** (5 / 3 / 2 business days), never sold
  separately to a paying customer.
- **Custom development is never included**, at any tier, and is always quoted separately
  per project at a fixed price agreed before work starts.
- Perpetual fallback, no retroactive price rise, cancel any time, **no licence key and no
  phone-home**, 50% discount under 10 employees and €1M revenue, free licences for
  non-profits, academia and published research.

And the principle underneath all of it: **the free AGPL build is the whole product.** No
paid edition, no feature gate, no seat limit. A commercial licence buys *permission*, not
functionality. Never add a feature that is unlocked by paying.

The address in the application footer is deliberate: whoever is running the software is
exactly the person who might need a licence, and "available on request" tells them
nothing.

## House style

- Source, comments, docstrings and tests are **in English**; the interface is bilingual.
- Comments explain *why*, especially where the code looks odd — most of the strange-looking
  lines here are scar tissue from a real bug.
- Add a `CHANGELOG.md` entry for anything user-visible, and bump `iris/version.py` when
  users need to reinstall (a dependency change counts).
- **Never commit `config.ini`**, real credentials, or real recipient lists. The repository
  history was already reset once for exactly that. Use `.example` domains in samples.
