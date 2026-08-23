# Changelog

All notable changes to Iris are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Real builds for Windows, macOS and Linux.** `.github/workflows/release.yml`
  builds each platform on its own GitHub runner — PyInstaller does not
  cross-compile, so this is the only way each binary can be genuine — and
  attaches one archive per platform to the release.
- Every bundle is **smoke-tested on its own platform** before it is offered for
  download: it has to answer `--version` cleanly, or the asset is not published.
- `.github/release-body.md`, so the description a downloader reads lives in the
  repository and can be edited without touching a workflow.
- `tests/test_release_workflow.py`, which parses the workflow and the release
  body so a download table can never again promise a platform that is not built.
- **`--version`** on the command line. It is what the release workflow uses to
  smoke-test each bundle, and it is parsed before the GUI is imported, so it
  answers without needing a display.

### Changed
- **Every Python source file carries the same seven-line licence header**, in
  the same place: the product name, the copyright line, an
  `SPDX-License-Identifier: AGPL-3.0-or-later` a tool can read, a pointer to
  LICENSE for the warranty disclaimer, and a pointer to COMMERCIAL-LICENSE.md
  for the commercial option.
  Ten of Iris's 24 files carried a longer, differently worded notice; it was
  replaced rather than left alongside.
  The `# -*- coding: utf-8 -*-` declarations went with it: they have meant
  nothing since Python 3, and Orion's ruff configuration flags them as UP009.
  Nothing but comments changed — the parsed syntax tree of all 152 files is
  identical before and after, which is how that was checked rather than
  assumed.
- **`LICENSE` is now the verbatim FSF text of the AGPL-3.0.** The previous copy
  was reflowed to long lines, which the licence's own header does not permit
  ("changing it is not allowed") and which stops GitHub recognising it.
- **`COMMERCIAL-LICENSE.md` was restructured into the 14-section layout shared
  by Orion, Iris, Proteus and Argus**, so the same clause sits at the same
  number in every product. Annual prices are unchanged. The
  **Perpetual option** is now a per-tier price at three times the annual rate,
  replacing the single "Small or Medium" figure and the two tiers that were
  previously quoted separately.
- `CLA.md` was aligned with the same three products, keeping the representation
  that is specific to this one.
- `README.md` follows the section skeleton shared by the four products.
- Release assets are now archives named `Iris-<version>-<platform>.zip` /
  `.tar.gz`.


### Changed
- **The commercial licensing structure was rebuilt around two independent questions**
  instead of one flat tier ladder: *how big is the organisation using Iris internally*
  (**Commercial** — Small / Medium / Large / Enterprise, by employee count or Corporate
  Group scope) and *does the software reach third parties at all* (**Redistribution** —
  Standard / Enterprise, replacing the old "OEM / Redistribution" tier). A Commercial
  licence below Enterprise no longer implies any redistribution, OEM, embedding or
  sublicensing right, and no longer extends to other companies in the same group —
  those need a Redistribution licence and/or the Enterprise/Group scope, both now
  explicitly defined (`COMMERCIAL-LICENSE.md` §2, §9–§10).
  `COMMERCIAL-LICENSE.md` grew from 11 to 22 sections; **OEM** is kept only as an example
  of a Redistribution scenario, not as a category (§14). README's licensing section and
  `CLAUDE.md`'s cross-product alignment note were updated to match; Argus and Proteus have
  not been migrated to this structure yet.

### Fixed
- **The GitHub Release published for a version tag had no title or notes.**
  `.github/workflows/build.yml` never set them, so a release showed up with
  only the bare tag name and an empty body. It now sets a fixed, readable
  title (`Iris vX.Y.Z`) and fixed notes pointing at `CHANGELOG.md`, plus a
  `gh release edit` step that runs unconditionally after the release step —
  belt and braces for a release that already exists with a stale title
  (created by hand, or by a run of the workflow from before this fix), which
  `softprops/action-gh-release` alone does not reliably correct.
- Adds `tests/test_build.py`, which parses the workflow YAML itself (GitHub
  Actions is the only thing that can run it) and checks for exactly these two
  regressions — verified to fail against the previous version of the file.
- Test suite grown from 211 to 216 tests.

## [2.3.0] - 2026-08-17

### Added
- **Cc and Bcc fields**, on the same row in the Configuration tab. Comma or semicolon
  separated for more than one address, validated like any other address, and identical
  on every message of the batch — since Iris sends one message per recipient, a
  recipient's message is never Cc'd or Bcc'd to another recipient in the same batch.
  Bcc uses the standard mechanism: `smtplib.SMTP.send_message()` reads the `Bcc` header
  to compute the SMTP envelope recipients, then strips it before transmitting, so the
  address is delivered but never appears in the message itself — verified with an
  integration test that inspects both the raw SMTP envelope and the bytes on the wire.
- **Multiple attachments.** The single-file field became a list: `ADD FILES...` opens a
  multi-select dialog, `REMOVE` drops the highlighted entries. `mailer.EmailTemplate`
  already supported a list of attachments; only the interface was limited to one.
- Both are part of the saved template library: `MessageTemplate` gained `email_cc`,
  `email_bcc`, and `attachments` replaces the old `attachment_path`.
- `mailer.parse_address_list()`, a small comma/semicolon splitter shared by validation
  and message building.

### Changed
- The default window grew to 900x900 (minimum 820x800) to fit the new Cc/Bcc row and the
  taller, multi-line attachment list without clipping the Save button — verified by
  measuring the tab's required height against the window, not just by eye.
- `config.ini`'s `[EMAIL]` section and `[TEMPLATE:name]` sections now store `attachments`
  (paths joined with `|`, which cannot appear in a Windows filename) instead of a single
  `attachment_path`, plus `email_cc` / `email_bcc`.
- Test suite grown from 180 to 211 tests.

### Compatibility
- A `config.ini` (or a saved template) written before this version has `attachment_path`
  instead of `attachments`; it is still read as a single-item attachment list. Newly
  saved files use only the new key.

## [2.2.0] - 2026-08-16

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
- Test suite grown from 174 to 180 tests.
- **The PDF reader moved from PyMuPDF to `pypdf`.** PyMuPDF is dual-licensed by
  Artifex under AGPL-3.0 or a paid commercial licence: a commercial Iris licence
  removed Iris's copyleft obligation but could never remove PyMuPDF's, so a
  closed-source product shipping PDF support would have needed a second licence
  from Artifex. `pypdf` is BSD-3-Clause, and **nothing in the dependency tree now
  restricts commercial sale**.
  - No functional change. PyMuPDF was used for exactly one call — the page text —
    and all the recognition already happened in `extract_from_pdf_text()`, which
    works on a plain string. Both engines were compared on inline, stacked,
    two-column and dense-table layouts, and on a file produced by a different
    toolchain with accented company names: identical results, identical speed.
  - The install shrinks from ~64 MB to ~3.5 MB, and the dependency is now pure
    Python with no C library to build.
- New tests covering `extract_from_pdf()` against a real PDF file — the previous
  suite only exercised the text parser, never the file reader.


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
