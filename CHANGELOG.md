# Changelog — Iris

All notable changes to this project, most recent first.

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
