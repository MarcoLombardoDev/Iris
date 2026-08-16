# Changelog — Iris

All notable changes to this project, most recent first.

## [Unreleased]

### Changed
- **The commercial offer is now identical across Iris, Argus and Proteus**, with only
  the price list, the scope wording and the third-party review differing per product.
  Same document (`COMMERCIAL-LICENSE.md`), same eleven sections, same tier ladder —
  Community / Internal / OEM / Enterprise, plus a perpetual option on Internal or OEM
  scope — and the same commitments at every paid tier:
  - **email support always included** (5 / 3 / 2 business days by tier), never sold
    separately to a paying customer;
  - **custom development never included and always quoted separately**, per project, at
    a fixed price agreed before work starts;
  - email as the only commercial channel, GitHub Issues for bugs and features;
  - perpetual fallback, no retroactive price rise, cancel any time, no licence key;
  - 50% off under 10 employees and €1M revenue; free licences for non-profits,
    academia and published research.
- README licensing section, badge and CLA contact line aligned to the same wording.
- Documented that PDF support depends on **PyMuPDF, itself AGPL-3.0**: a commercial
  Iris licence cannot relicense it, so a closed-source product shipping PDF support
  needs a commercial PyMuPDF licence from Artifex, or a build without the PDF reader.


## [2.1.0] - 2026-08-15

Everything a batch sender kept asking for, all of it in the free build. This
release adds no paid tier, no feature gate and no licence key: the commercial
licence covers redistribution rights, never features.

### Added
- **Sender profiles.** Several SMTP configurations — a work account, an
  internal relay, a client's server — can be saved under a name and recalled
  from a drop-down in the Configuration tab. `SAVE AS...` stores the fields on
  screen, `DELETE` removes the entry; selecting one copies it into the form,
  where it can still be edited before sending.
- **Template library.** Subject, message and attachment save and recall the
  same way, so switching between an annual notice and a payment reminder no
  longer means retyping the body.
- Both live in `config.ini`, one `[PROFILE:name]` / `[TEMPLATE:name]` section
  per entry, alongside the `[EMAIL]` section that still holds the settings in
  use. Saving an entry rewrites only that entry, leaving fields being edited
  elsewhere untouched. Profile passwords are obfuscated like the main one.
- New `config_store` API: `SenderProfile`, `MessageTemplate`, `save_profile()`,
  `delete_profile()`, `save_template()`, `delete_template()` and `clean_name()`.
- **Configurable pause between messages** (`send_delay`), for providers that
  rate limit a sender. Decimals are accepted, the pause never follows the last
  message of a batch, and it is interruptible — cancelling does not wait for
  the remaining seconds to elapse.
- `mailer.parse_delay()`, a `send_delay` field on `SmtpSettings`, and a `sleep`
  injection point on `send_bulk()` so the pause is testable without waiting.
- **AGPL-3.0 notice header** on every source file, as the licence itself
  recommends, each pointing at the commercial alternative.
- **Commercial licensing contact in the application itself.** The footer used
  to say "commercial licensing available" without saying how; it now shows the
  address, and clicking it opens the mail client on a pre-filled enquiry. The
  address lives in `version.CONTACT_EMAIL`, so the interface, the README and
  `COMMERCIAL-LICENSE.md` cannot drift apart.
- **`COMMERCIAL-LICENSE.md`** — scope of the commercial licence, what it does
  and does not include, and the price list. The README license section now
  carries the same list instead of only an email address.
- Commented profile and template examples in `config.ini.example`.

### Changed
- The Configuration tab is reorganised: the sender profile selector opens the
  SENDER frame, the template selector opens the EMAIL TEMPLATE frame, and a new
  OPTIONS frame collects the pause and the language selector (which used to sit
  among the sender fields, where it never belonged).
- The default window is 900x800 (was 900x750) to fit the reorganised tab.
- Test suite grown from 129 to 174 tests.

### Compatibility
- A `config.ini` written by 2.0.x loads unchanged: the new keys default to
  empty libraries and no pause, and files without them keep working.

## [2.0.0] - 2026-08-11

First public release, under the new name **Iris**. The application was
translated to English, the interface became bilingual, and the project was
prepared for open-source distribution.

### Added
- **New name**: the project is now *Iris — Email Sender*. The window title, the
  interface header and the executable use it; the Python package is `iris`, and
  the GUI moved to `iris/gui.py`.
- **English interface**, now the default, with an **Italian** translation
  selectable at runtime from the Configuration tab. The window is redrawn
  immediately, keeping settings, template and recipient list, and the choice is
  persisted in `config.ini`.
- New `iris/i18n.py` module holding one catalogue per language; the test
  suite checks that all catalogues share the same keys and placeholders.
- `{COMPANY}` placeholder for templates. The Italian `{AZIENDA}` used by
  version 1.x is still accepted, so existing templates keep working.
- `language` entry in `config.ini`, plus `config_store.update_language()` which
  persists only that preference without touching fields being edited.
- AGPL-3.0 `LICENSE` with a dual-licensing model and a `CLA.md` for
  contributors.
- `docs/generate_screenshots.py`, which boots the real application under Xvfb
  with in-memory sample data and captures the README screenshots.
- Application icon generated from primitives by `assets/make_icon.py`.

### Changed
- Source code, comments, docstrings, tests and build scripts translated to
  English.
- Documentation condensed into a single exhaustive English `README.md`
  (the previous Italian guides under `docs/` were removed).
- Company branding removed: the tool is now generic, with a neutral icon.
- Test fixture `test.xls` replaced by a generated, data-free
  `tests/data/sample.xls` (`tests/data/make_sample_xls.py`).
- Version bumped to 2.0.0 to mark the interface language change.

### Fixed
- Switching the interface language back to a previous value was silently
  undone: `update_language()` reloaded the file and `load()` re-applied the
  language stored there. `load()` now takes `apply_language`, and the reload
  during an update no longer overrides the user's choice.

### Security
- The repository history was reset: earlier commits contained `config.ini`
  files with real SMTP credentials in clear text, along with build artefacts.
  Any credential ever committed must be considered compromised and rotated.

## [1.4.0] - 2026-08-05

Full product review: blocking bugs fixed, logic separated from the interface
and an automated test suite introduced.

### Fixed
- Start-up crash `TclError: unknown option "-bootstyle"`: the option was passed
  to standard `tkinter.ttk` widgets, which do not support it.
- Start-up crash on systems without `pywin32`/Outlook: the COM modules were
  imported at module level.
- `.xls` files were never read (handed to `openpyxl`, which does not support
  the binary format); `xlrd` is used now.
- Sending failed with non-ASCII subjects or bodies: messages now use
  `EmailMessage` with RFC 2047 compliant UTF-8 encoding.
- Tkinter widgets were accessed from worker threads during sending and file
  generation.
- Wrong email regular expression (`[A-Z|a-z]{2,}` accepted a pipe in the TLD).
- In PDFs the first occurrence of an address was always used, associating the
  wrong company name when several recipients were present.
- SMTP connections were not closed on error.
- `build.py` aborted when `config.ini` was missing, a file excluded from the
  repository because it holds credentials.
- `Iris.spec` contained an absolute path of the development machine and
  was overwritten at every build (now `--specpath build/`).
- The PyInstaller executable would not start: the `PIL._tkinter_finder` hidden
  import was missing, without which ttkbootstrap cannot build its theme.
- `after` callbacks were not cancelled on close ("invalid command name ...").
- An unsupported file left the interface blocked with disabled buttons: the
  error message was read inside a lambda referencing the `except` variable,
  which Python deletes when the block ends.
- Possible hang on close during an operation; the logo image is now released
  from the main thread.

### Added
- CSV and Excel `.xlsm` support.
- `TEST CONNECTION` button to validate server and credentials without sending.
- `.eml` generation when Outlook is unavailable (previously the operation just
  failed).
- Multiple selection in the recipient list.
- Automatic detection of the column order in spreadsheets.
- Send progress in the status bar and a final summary with error details.
- `config.ini` looked up in several locations, falling back to the per-user
  folder when the application directory is read-only.
- `config.ini.example` reference file.

### Changed
- Document analysis moved to a background thread: the interface no longer
  freezes on large files.
- Bulk sending reuses a single SMTP connection, with automatic reconnection and
  early abort on unrecoverable errors.
- Complete configuration validation with readable error messages.
- The password in `config.ini` is no longer stored in clear text (base64
  obfuscation, backward compatible on read); on POSIX the file is created with
  `600` permissions.
- The `emails/` folder cleanup only removes generated `.msg`/`.eml` files.
- Application logic extracted into a package independent from Tkinter, covered
  by a pytest suite and a GitHub Actions pipeline (Linux 3.10/3.11/3.12 with
  Xvfb, and Windows).

## [1.1.x] - 2025

Initial internal versions: graphical interface with Processing, Log and
Configuration tabs, support for PDF, Excel, Word and text files, templates with
a company placeholder, SMTP configuration with SSL/TLS and STARTTLS, logging
and persistent configuration.
