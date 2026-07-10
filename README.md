# Sheetwright

**Native Google Sheets for Claude.** Sheetwright lets Claude create, edit and *format* your Google
Sheets through Google's official API — real colors, currency and number formats, native Tables with
dropdowns and filters, `HYPERLINK` formulas that open your Drive files, and locale-aware behavior.
Not a flat CSV dump.

> Talk to Claude in plain language — *"fill in this budget comparison and highlight the cheapest
> supplier"*, *"make an invoice list with links to each PDF"*, *"turn this range into a table with a
> Status dropdown"* — and Sheetwright does it natively in your spreadsheet.

## Why it exists

Until now, when an AI assistant read a Google Sheet it saw a flat CSV: colors, visual order and
links were lost. The existing Google Sheets integrations are read/write of values — no formatting,
no native Tables, no `HYPERLINK`, no locale awareness. Sheetwright fills that gap: it works the
sheet the way a person does, preserving and writing the full richness. Built with first-class care
for the international details (locale, currency, timezone, formula separators) that quietly break
spreadsheets around the world — a sensitivity born from real-life "regional-settings stew" in
Argentina.

## What it does

- **Real formatting** — cell/header colors, bold, number and currency formats.
- **Links to Drive** — `HYPERLINK` formulas that open invoices, receipts, any Drive file, from a cell.
- **Native Tables** — Google Sheets Tables with column types, dropdowns and filters.
- **Create spreadsheets** — new sheets in your Drive, already formatted.
- **Organize files** — move and tidy your Drive files into folders.
- **Locale-aware** — adapts to each sheet's regional settings, **respects** them, and **flags**
  inconsistencies (e.g. a sheet stuck on the wrong country's currency), offering to fix them.

Works with **personal Gmail and Google Workspace** accounts, and supports **multiple accounts**.

## How it works

Sheetwright is the *know-how*; your *access* stays yours. The skill contains no secrets. Each user
runs a one-time setup that creates their own Google OAuth credentials, which live in a **private,
local folder on their own machine** — never in this repo, never sent anywhere. Claude loads them to
act on your behalf via Google's APIs. You can revoke access anytime at
[myaccount.google.com/permissions](https://myaccount.google.com/permissions).

## Install

Add this repo as a marketplace and install the plugin:

```
/plugin marketplace add mahaluza/sheetwright
/plugin install sheetwright@haluza
```

Or install from the official Claude plugin directory (once approved).

## First-time setup (once per Google account)

Sheetwright needs a small one-time setup (~15 min) to create your own API access: a Google Cloud
project with the Sheets + Drive APIs and an OAuth credential. Claude can guide you through it
step by step — just ask it to "set up Sheets access". The full runbook is in
[`skills/sheetwright/references/setup.md`](plugins/sheetwright/skills/sheetwright/references/setup.md).

## User manual

A full illustrated user manual (why it exists, how it works, step-by-step setup with screenshots,
day-to-day use, locale & languages, security) is available in two languages, each as PDF and Word:

- **English** — [`docs/Sheetwright_User_Manual_EN.pdf`](docs/Sheetwright_User_Manual_EN.pdf) ([.docx](docs/Sheetwright_User_Manual_EN.docx))
- **Español** — [`docs/Sheetwright_Manual_Usuario_ES.pdf`](docs/Sheetwright_Manual_Usuario_ES.pdf) ([.docx](docs/Sheetwright_Manual_Usuario_ES.docx))

## Security & privacy

Your credentials are equivalent to a password and stay in a private local folder you control.
Sheetwright collects no data and has no servers. See [PRIVACY.md](PRIVACY.md).

## Examples

See [EXAMPLES.md](EXAMPLES.md) for three end-to-end use cases.

## Author & support

Created by **Miguel Angel Haluza** ([@mahaluza](https://github.com/mahaluza)).
Questions, bugs or feedback: please open an issue at
[github.com/mahaluza/sheetwright/issues](https://github.com/mahaluza/sheetwright/issues).

## License

[MIT](LICENSE).
