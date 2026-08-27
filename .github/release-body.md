**Iris — Email Sender.** Turns a document full of company names and email addresses into a
batch of personalised emails, and sends them over a single SMTP connection — or writes
them to disk for review first.

- **Reads** PDF, Excel (`.xlsx` / `.xlsm` / `.xls`), CSV, Word (`.docx`) and plain text,
  detecting the company and address columns by content rather than position.
- **Personalises** — `{COMPANY}` in the subject and body is replaced per recipient, with a
  named template library for subject, message, Cc/Bcc and attachments.
- **Sends or drafts** — one SMTP connection for the whole batch, or standard `.eml` files
  (`.msg` through Outlook on Windows) written to disk without sending anything.
- **Bilingual** — English and Italian, switchable at runtime.

## Download

| Platform | File |
|---|---|
| Windows (x64) | `Iris-{{VERSION}}-windows-x64.zip` |
| macOS (Apple silicon) | `Iris-{{VERSION}}-macos-arm64.zip` |
| Linux (x64) | `Iris-{{VERSION}}-linux-x64.tar.gz` |

Each archive is built on that platform's own runner — no cross-compilation, no emulation.
Unpack and run: no installation, and no Python needed.

### Windows will say the publisher is unknown

It is meant to. These builds carry **no code-signing certificate**, so Microsoft Defender
SmartScreen shows *"Windows protected your PC"* and offers only **Don't run**. Click
**More info**, then **Run anyway**. Nothing is wrong with the download; SmartScreen is
reporting that it has never seen this publisher, which is true.

Because that warning asks you to trust a file you cannot check by looking at it, every
archive ships with a `.sha256` beside it. In PowerShell:

```powershell
Get-FileHash .\Iris-{{VERSION}}-windows-x64.zip -Algorithm SHA256
```

The hash it prints must match the one inside `Iris-{{VERSION}}-windows-x64.zip.sha256`.
If it does, the file is byte for byte what the build produced.

On **macOS**, Gatekeeper refuses an unidentified developer the same way: right-click the
application and choose **Open**, or run `xattr -dr com.apple.quarantine Iris`.

Each archive unpacks to a folder holding the executable and a `licenses/` directory: the
terms of everything Iris is built on, plus an inventory of every native library in the
build and where each licence determination came from. That inventory is generated on the
machine that produced the archive, so it describes what you actually downloaded.

Running from source instead is described in the
[README](https://github.com/MarcoLombardoDev/Iris/blob/{{TAG}}/README.md).

## Changes

See [CHANGELOG.md](https://github.com/MarcoLombardoDev/Iris/blob/{{TAG}}/CHANGELOG.md).

## Licence

Licensed **AGPL-3.0-or-later** — see
[LICENSE](https://github.com/MarcoLombardoDev/Iris/blob/{{TAG}}/LICENSE). A commercial
licence, without the AGPL's obligations, is available for closed-source and redistribution
use: see
[COMMERCIAL-LICENSE.md](https://github.com/MarcoLombardoDev/Iris/blob/{{TAG}}/COMMERCIAL-LICENSE.md).
