# Commercial Licence — Iris

**Iris — Email Sender**
Copyright © 2026 Marco Lombardo

Iris is dual-licensed. It is available under the
[GNU Affero General Public License v3.0](LICENSE) at no cost, and under the commercial
terms in this document for those who cannot accept the AGPL's obligations.

Both licences cover **the same software**. There is no crippled edition, no feature held
back behind a paywall, no licence key and no phone-home. What you buy is **permission**,
not functionality.

> **To buy, or to ask anything commercial — including whether you need this at all —
> email [marco.lombardo@gmail.com](mailto:marco.lombardo@gmail.com?subject=Iris%20commercial%20licence%20enquiry).**
> Email is the only commercial channel: quotes, contracts, invoicing and pre-sales
> questions all go there. GitHub Issues are for bugs and feature requests.

> This page is a **commercial offer and a summary of terms**, not the signed agreement.
> The binding contract is the licence certificate issued per customer. It is not legal
> advice; have your own counsel review it before signing.

The licensing structure, at a glance:

```
PRODUCT LICENSING
│
├── Community
│   └── AGPL-3.0
│
├── Commercial                    (internal use)
│   ├── Small       — 1–49 employees
│   ├── Medium      — 50–249 employees
│   ├── Large       — 250–999 employees
│   └── Enterprise  — 1,000+ employees / Corporate Group
│
└── Redistribution                (distributed to third parties)
    ├── Standard
    └── Enterprise
```

**Commercial** and **Redistribution** answer two different questions. Commercial answers
*"how big is the organisation using this internally?"* — Redistribution answers *"is any
part of this software reaching someone outside that organisation?"* An organisation that
only uses Iris itself never needs a Redistribution licence, however large it is; an
organisation of any size that ships Iris (or code derived from it) to third parties needs
one regardless of its Commercial tier.

---

## 1. Do you actually need this?

Most people do not. Read this before reading the price list.

| What you want to do | Licence you need |
|---|---|
| Use Iris inside your organisation, however many people, however many machines | **AGPL — free.** Nothing to buy, nothing to declare. |
| Modify it for your own internal use and keep the changes to yourself | **AGPL — free.** |
| Publish a fork, or ship a modified version to someone else | **AGPL — free**, provided you release your modified source under AGPL-3.0. |
| Ship Iris, or code derived from it, inside a **closed-source product for your own internal use** | **Commercial** — see §2, §5–§10 for the tier |
| Run a modified Iris as a **hosted or SaaS service**, without publishing your source | **Commercial** |
| Embed Iris in a product, or ship it under **your own name or branding**, to third parties | **Redistribution** — see §11–§13 |
| Distribute a derivative to customers, resell it, or run an OEM programme | **Redistribution** |
| Your organisation's policy forbids AGPL code, and you need it in writing | **Commercial** (or **Redistribution**, if the result also reaches third parties) |

**Internal use is free, permanently, for organisations of any size.** Anyone telling you
otherwise about an AGPL project is mistaken. Buy a commercial licence when the AGPL's
*distribution* terms are the problem — not simply because you are a company.

The dividing line is one rule: **AGPL-3.0 is free as long as the source stays open.**

---

## 2. What each licence grants

### 2a. Commercial (Small, Medium, Large, Enterprise)

Subject to payment and to the tier purchased, a non-exclusive, non-transferable licence
to use, copy and modify Iris, and to deploy it — including as a service reached by your
own employees, contractors or customers — without triggering AGPL §13, and with no
obligation to publish your modified source.

The licence covers:

- **one legal entity** — the licensee named in the certificate;
- **internal use** only;
- **authorised internal users**;
- **authorised internal installations**.

It does **not** automatically include:

- redistribution;
- OEM use;
- embedding in a product distributed to third parties;
- sublicensing;
- use by other companies in the same group (see §10, Corporate Group) — including at the
  Enterprise tier, unless the certificate expressly names those entities.

Any of the above requires a **Redistribution licence** (§11–§13) in addition to, or
instead of, the Commercial licence.

### 2b. Redistribution (Standard, Enterprise)

In addition to internal use, a Redistribution licence grants the right to:

1. incorporate Iris, in whole or in part, into your own products and services that reach
   third parties;
2. distribute it in binary or source form as part of your product, with no obligation to
   publish your own source;
3. sublicense these rights to your end users **solely as part of your product**, and not
   as a standalone competing tool.

You also receive the full source of the licensed version, and the right to modify it with
no obligation to contribute anything back.

Neither licence grants rights to the third-party components in §20.

---

## 3. Price list

All prices in **EUR, excluding VAT**, per **licensed legal entity**. A Commercial licence
below Enterprise covers exactly that entity — subsidiaries and other group companies are
not automatically included, see §10. Seats are never counted: you are not billed per
developer, per user or per installation.

| Tier | Price | Scope |
|---|---:|---|
| **Community** | **Free** | Everything Iris does, under AGPL-3.0. Unlimited internal use. |
| **Commercial — Small** | **€1,500 / year** | 1–49 employees. Internal use, one legal entity. |
| **Commercial — Medium** | **€3,000 / year** | 50–249 employees. Internal use, one legal entity. |
| **Commercial — Large** | **€5,500 / year** | 250–999 employees. Internal use, one legal entity. |
| **Commercial — Enterprise** | **from €9,000 / year** | 1,000+ employees, or Corporate Group scope as defined in the certificate. |
| **Redistribution — Standard** | **€4,000 / year** | Ordinary commercial redistribution — see §12. |
| **Redistribution — Enterprise** | **from €15,000 / year** | Large-scale redistribution, scope set by the agreement — see §13. |
| **Perpetual — Commercial (Small or Medium)** | **€5,000** one-off | Bought once, covers the major version current at purchase. Large/Enterprise: quoted separately. |
| **Perpetual — Redistribution (Standard)** | **from €12,000** one-off | Bought once, covers the major version current at purchase. Enterprise: quoted separately. |

### What every paid licence includes

The same four things, at every tier above Community:

- **Email support** — see §15. Always included, never sold separately to a paying customer.
- **Updates for the whole term**, and a **perpetual fallback**: every version released while
  your subscription is active stays licensed to you forever. If the subscription lapses you
  keep running what you had, you simply stop receiving new versions under commercial terms.
- **No retroactive charge.** Renewals are priced at the rate in force when you first bought,
  for as long as you renew without a gap.
- **Cancel any time.** No notice period, no auto-renewal trap. An invoice is issued per
  term; not paying it ends the subscription.

### Discounts

| Who | What |
|---|---|
| Fewer than 10 employees **and** under €1M annual revenue | **50% off** any annual Commercial or Redistribution tier |
| Registered non-profits, accredited academic institutions, published research | **Free commercial licence** — ask |

---

## 4. Support

**Every paying customer gets support. It is included in the price, at every paid tier, and
it runs over email.** There is no support product to buy separately and no tier that leaves
you on your own. Response targets are detailed in §15.

---

## 5. Commercial — Small

**1–49 employees.**

For organisations of small size. As described in §2a, the licence covers one legal entity,
internal use, authorised internal users and authorised internal installations. It does not
automatically include redistribution, OEM, embedding in a distributed product, sublicensing,
or use by other companies in the same group.

## 6. Commercial — Medium

**50–249 employees.**

The same model as the Small tier (§2a, §5), applied to organisations with 50–249 employees.
The licence remains organisation-based, internal-use, single legal entity, and
non-redistributable.

## 7. Commercial — Large

**250–999 employees.**

The same model as the Small and Medium tiers, applied to organisations with 250–999
employees. The licence continues to be limited to the internal use of the licensed legal
entity.

## 8. Commercial — Enterprise

**1,000+ employees, OR Corporate Group.**

This tier covers at least one of the following:

1. an organisation with 1,000 or more employees;
2. an organisation that belongs to a Corporate Group (§10);
3. use that requires a group-wide perimeter;
4. use by more than one legal entity of the same group, where expressly authorised.

The Enterprise tier may be named **Enterprise / Group Commercial License** in the
certificate. The agreement must clearly state which legal entities are included.

Belonging to a corporate group does not by itself mean every company in that group is
authorised: the perimeter must be explicitly defined in the certificate (see §10).

## 9. Employee Count

The criterion used to determine the Commercial tier.

Default rule:

> Employee count refers to the total number of employees of the licensed legal entity,
> unless the applicable Enterprise / Group agreement defines a different scope.

The count does **not** automatically include:

- customers;
- end users;
- suppliers;
- partners;
- external consultants.

## 10. Corporate Group

A **Corporate Group** is a set of companies directly or indirectly controlled by the same
parent company, or otherwise belonging to the same corporate structure as defined by the
agreement.

A small company that belongs to a large group cannot use a Small (or Medium, or Large)
licence to automatically extend those rights to the rest of the group. A group-wide
perimeter must be expressly authorised — see §8, Commercial — Enterprise.

---

## 11. Redistribution

A Redistribution licence is distinct from a Commercial licence. It is needed whenever the
licensee wants to use the project in a scenario where the software, or part of it, is
distributed to third parties.

Examples:

- incorporation into another piece of software;
- embedding;
- distribution alongside a proprietary product;
- distribution to customers;
- distribution to end users;
- commercialisation of a derivative product;
- integration into a proprietary application;
- OEM scenarios;
- distribution as a component of a commercial solution.

The term **OEM** may be used as an example of a Redistribution scenario; it is not treated
as a separate category — see §14, Terminology.

## 12. Redistribution — Standard

For ordinary commercial distribution scenarios.

Examples:

- software houses;
- ISVs;
- integrators;
- commercial developers;
- companies embedding the project in a product;
- distribution to a non-exceptional number of customers or installations.

Depending on the specific terms of the agreement, the licence may allow: modification,
integration, embedding, distribution, and commercialisation of the resulting product.

It does not automatically grant: exclusivity, unlimited sublicensing, trademark rights,
rights over the dependencies (§20), or transfer of the licence.

## 13. Redistribution — Enterprise

For large-scale redistribution scenarios.

Examples:

- large software houses;
- large groups;
- worldwide distribution;
- products with large installation volumes;
- millions of users or installations;
- large-scale commercial platforms;
- large OEM programmes;
- widely distributed commercial products.

The precise scope is left to the commercial agreement, and the criterion is not
necessarily based on employee count. More relevant factors for Redistribution include:

- number of products;
- number of customers;
- number of installations;
- distribution volume;
- end users;
- territory;
- product revenue;
- number of legal entities;
- support required.

## 14. Terminology

Preferred terms: **Community**, **Commercial**, **Redistribution**.

**OEM** is avoided as a top-level category. It may still be used in documentation as an
example, worded along the lines of:

> OEM, embedded and other redistribution scenarios are covered by the Redistribution
> License.

This keeps the category general enough to apply to different commercial models rather than
locking it to one distribution pattern.

---

## 15. Support

| Tier | Support | Target first response |
|---|---|---|
| Community | GitHub Issues, best effort | — |
| Commercial — Small | Email | 5 business days |
| Commercial — Medium | Email | 4 business days |
| Commercial — Large | Email | 3 business days |
| Commercial — Enterprise | Email, private channel | 2 business days |
| Redistribution — Standard | Email | 3 business days |
| Redistribution — Enterprise | Email, private channel | 2 business days |

What "support" means here, stated plainly so nothing is inferred:

- **Included:** installation and configuration problems, questions about intended behaviour,
  diagnosis of suspected bugs, guidance on using Iris for your case, and licensing or
  compliance questions.
- **A response commitment, not a fix commitment.** The target above is how quickly you get a
  human reply, not how quickly a defect is resolved. Confirmed bugs are prioritised over
  new features, but no repair window is guaranteed at any tier.
- **Not included:** building your workflow for you, writing features, or operating the
  software on your behalf. That is custom development — see §16.

---

## 16. Custom development

Anything that changes the software for you — a new feature, an integration, a format, a
connector, a bespoke build — is **never included in a licence fee**, at any tier.

It is **available on request and quoted separately**, per project:

1. You describe what you need.
2. You get a written scope, a fixed price and a delivery window before any work starts.
3. Nothing is invoiced until you accept that quote.

The indicative day rate for Iris is **€600 / day**, used to size a quote; the quote
itself is fixed-price, not time-and-materials.

Two things worth knowing before you ask:

- **A commercial licence is not required to commission work.** AGPL users can pay for
  custom development too.
- **By default the result is merged into the public project** under AGPL-3.0, which is why
  the rate is what it is. If you need it kept private, say so at quoting time: exclusive or
  unpublished work is priced differently.

---

## 17. How to buy

1. **Ask.** Write to **[marco.lombardo@gmail.com](mailto:marco.lombardo@gmail.com?subject=Iris%20commercial%20licence%20enquiry)**.
   Say what you intend to build and roughly how big your organisation is. Use email rather
   than a public issue: what you are building is usually not something you want indexed.
2. **Confirm the tier.** You get a written statement of which tier applies and why, so
   there is no ambiguity later.
3. **Invoice.** Issued in EUR, payable by bank transfer within 30 days.
4. **Certificate.** On payment you receive a signed licence certificate naming your
   organisation, the tier, the term and the covered products. That certificate — not a key
   file — is the licence.

To get a concrete quote in one round instead of three, include: your **company** and the
legal entity that would hold the licence; the **intended use** (internal, embedded in a
product you sell, or operated as a service); **deployment scale**; the **tier** you think
fits; and whether you need **custom development**.

There is **no licence key, no activation, no phone-home.** The software behaves identically
whether or not you have paid. Compliance is contractual and self-declared; there is no
audit clause.

---

## 18. Term, warranty and liability

- **Term.** Annual from the invoice date, unless the tier says otherwise.
- **Updates.** Included for the duration of the term.
- **Warranty.** Iris is provided **as is**. No warranty of merchantability, fitness for a
  particular purpose, or non-infringement. Iris sends real email to real recipients: read the [Disclaimer](README.md#disclaimer).
- **Liability.** Total aggregate liability under a commercial licence is limited to **the
  fees paid in the twelve months preceding the claim**. Liability is not excluded where it
  cannot lawfully be excluded — death or personal injury caused by negligence, fraud, or
  wilful misconduct.
- **Indemnity.** No IP indemnity at Commercial Small/Medium/Large, or at Redistribution
  Standard. Commercial Enterprise, Redistribution Enterprise, and perpetual licences may
  include one; ask, and it will be stated in the certificate.
- **Governing law.** Italian law, courts of Milan, unless the certificate names otherwise.

---

## 19. What is *not* included

Stated plainly, so nobody discovers it after paying:

- **No SLA on the software itself.** Response targets are commitments about replying to
  you, not about fixing anything within a window.
- **No custom development.** Quoted separately — see §16.
- **No guarantee of future features.** The roadmap is not a contract.
- **No exclusivity.** The same licence is available to your competitors.
- **No rights to third-party components.** See §20.
- **No responsibility for what you send.** Recipient consent, content and compliance with the rules on electronic communications and personal data —
  including the GDPR — remain entirely yours.

---

## 20. Third-party components

A commercial licence covers Iris's own code. Its dependencies are separately licensed and
a commercial licence cannot and does not relicense them.

| Component | Licence | Commercial redistribution |
|---|---|---|
| pypdf | BSD-3-Clause | ✅ Permissive |
| openpyxl | MIT | ✅ Permissive |
| xlrd | BSD-3-Clause | ✅ Permissive |
| python-docx | MIT | ✅ Permissive |
| Pillow | MIT-CMU (HPND) | ✅ Permissive |
| ttkbootstrap | MIT | ✅ Permissive, optional |
| pywin32 | PSF-style | ✅ Permissive, Windows only |
| PyInstaller | GPL-2.0 **with bootloader exception** | ✅ The exception exists to allow proprietary frozen applications |

**Every dependency is permissively licensed and safe to redistribute in a commercial
product.** No dependency imposes copyleft, field-of-use or anti-commercial conditions.

> **Resolved: the PyMuPDF problem.** PDF reading used to depend on `PyMuPDF`, dual-licensed
> by Artifex under **AGPL-3.0 or a paid commercial licence** — the same model as Iris
> itself. A commercial Iris licence removes *Iris's* copyleft obligation but could never
> remove PyMuPDF's, so a closed-source product shipping PDF support would have needed a
> second commercial licence from Artifex. The reader now uses
> [`pypdf`](https://github.com/py-pdf/pypdf) (BSD-3-Clause), which extracts the same page
> text with no copyleft attached. Nothing in the dependency tree now restricts commercial
> sale.

Verify these against the versions you actually ship. They are listed in good faith, current
as at the version of this document, and are not a legal opinion.

---

## 21. Contributors

Contributions are accepted under the [Contributor License Agreement](CLA.md), which grants
the Project Owner the right to license contributed code under both AGPL-3.0 and commercial
terms. That grant is what makes dual licensing possible: without it, a single contributed
patch would block commercial licensing for everyone.

Contributors keep the copyright in their work, and receive a perpetual, royalty-free
commercial licence to Iris for their own use, as thanks.

---

## 22. Contact

**Commercial licensing, quotes and support for paying customers:
[marco.lombardo@gmail.com](mailto:marco.lombardo@gmail.com?subject=Iris%20commercial%20licence%20enquiry)**

For anything that is *not* a purchase — a bug, a feature request, a question about which
row of §1 you fall into — the [issue tracker](https://github.com/MarcoLombardoDev/Iris/issues) is the better channel, and the
answer helps whoever asks next.

---

*This document is a commercial offer, not legal advice. Prices and terms may change for new
purchases; a licence already issued is governed by the certificate you hold, not by later
revisions of this file.*

*Copyright © 2026 Marco Lombardo. Iris is licensed under AGPL-3.0; commercial licensing is
available under the terms above.*
