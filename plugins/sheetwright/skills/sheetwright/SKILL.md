---
name: sheetwright
description: >-
  Create, edit and format Google Sheets NATIVELY via the official Google API (not as flat CSV):
  paint cells and headers, currency/number formats, HYPERLINK formulas that open Drive files,
  native Tables with dropdowns and filters, create new spreadsheets, and organize/move files in
  Google Drive. Locale-aware: adapts to each sheet's regional settings, respects them, and flags
  mismatches. USE THIS SKILL whenever the user wants to work on their Google Sheet with formatting
  or links — e.g. "fill in this budget comparison", "make an invoice list with links", "turn this
  column green", "build a native table", "create a spreadsheet in my Drive", "organize the files
  into that folder" — even if they don't say "API" or "connector". Also for quotes/invoices/
  budgets in gsheets, hyperlinks to Drive files, or first-time setup of Sheets access (credentials).
  Do NOT use for local .xlsx files (use the xlsx skill) or for Google Docs.
---

# Sheetwright — native Google Sheets (API bridge)

This skill gives Claude real programmatic access to the user's Google Sheets and Drive through
the official API. Unlike reading a sheet as flat CSV, it preserves and writes the full richness:
colors, number/currency formats, formulas, `HYPERLINK` to Drive files, native Tables (with column
types, dropdowns and filters), creating spreadsheets, and organizing files.

Access uses **per-account OAuth credentials** stored in a private folder owned by the user (never
inside this skill). One account = one `<account>.json` file.

## Workflow (every time)

1. **Pick the account.** If the user has several Google accounts configured, determine which one
   applies (from context: owner of the sheet, the Drive where the file lives, or ask if ambiguous).
   The credential file is usually named after the account alias, e.g. `mahaluza.json`, `work.json`.

2. **Get the credentials into the runtime.** The credentials live in a private local folder owned
   by the user (default: a folder named `Secrets` under `~/Claude`, i.e.
   `~/Claude/Secrets/credentials/<account>.json`).
   - In **Cowork (cloud)**: the skill runs remotely, so **stage** that file from the user's
     connected folder. If you don't know the exact path, list the connected folders
     (`device_list_dir`) to locate the secrets / `credentials` folder, then stage the `<account>.json`
     (`device_stage_files`). It appears under `/mnt/user-data/uploads/...`. That path is read-only,
     so copy the json somewhere writable (e.g. `/tmp/creds.json`) before use.
   - In a **local environment** (e.g. Claude Code): the file is already on disk — just point
     `gauth` at its path.
   - If NO credentials exist yet, go to **First-time setup** below.

3. **Install dependencies once** (if missing):
   `pip install --break-system-packages -q google-auth google-api-python-client`

4. **Use the helpers.** Put `scripts/` on the path and use `gauth` for the services and
   `sheets_helpers` for the common operations:
   ```python
   import sys; sys.path.insert(0, "<path-to-this-skill>/scripts")
   import gauth
   d = gauth.drive("/tmp/creds.json")      # Drive v3 service
   s = gauth.sheets("/tmp/creds.json")     # Sheets v4 service
   ```

5. **Verify via API, silently (by default).** Re-read the RENDERED values with
   `sheets_helpers.read_effective` / `cells_with_errors` and confirm there are no formula errors
   (`#ERROR!`, `#REF!`, etc.). This catches ~95% of issues — including the classic locale-separator
   one — **without opening anything**. For hyperlinks use `write_hyperlink`, which already
   self-heals the separator and verifies the result.
   Open the sheet in the browser (Claude in Chrome) for a **visual** check ONLY if the user asks,
   or if there's something about the formatting you cannot confirm via API — and in that case
   **tell them first** ("I'll open the sheet to review it"). **Never open a browser by surprise**:
   it's disconcerting for many users, and the skill must also work when Claude in Chrome isn't
   available.

## Common operations

`scripts/sheets_helpers.py` provides functions that already encapsulate the fiddly details:

- `hyperlink(s, sid, url, label)` → a `=HYPERLINK(...)` formula with the **right separator for the
  sheet's locale** (in comma-decimal locales it's `;`, not `,`; otherwise you get `#ERROR!`).
- `drive_file_link(s, sid, file_id, label)` → a hyperlink to a Drive file by its ID.
- `write_hyperlink(s, sid, cell, url, label)` → writes a hyperlink, **self-healing** the separator
  and verifying the effective value (no `#ERROR!`).
- `create_table(s, sid, gid, name, first_row, last_row, columns)` → creates a **native Table**,
  handling the gotchas (tableId as string; full column list).
- `set_table_columns(s, sid, table_id, columns)` → rewrites table column types **always sending the
  full list** (sending a single column deletes the rest).

For everything else (merges, borders, conditional formatting, charts, moving Drive files) use the
raw API with the `gauth` services. Before writing new code, **read `references/gotchas.md`** — it
collects the errors that were costly to discover and saves you time.

## Locale & languages (important — context awareness)

The skill adapts to the **document's locale**, which is the ONLY source of truth. Read
`sheet_locale(s, sid)` → (locale, timeZone). From it come the formula separator and the
currency/date formats. **Ignore** the language of Chrome, the account, and the Sheets UI: those are
display layers that don't affect data or formulas. Function names via the API are ALWAYS English
(HYPERLINK, not the localized name); only the separator follows the locale. Full detail in
`references/locale.md`.

Expected behavior:

- **Always respect the locale you receive** on an existing sheet. NEVER change it silently.
- **When creating** a spreadsheet, state in your reply which locale and timezone it ended up with
  (e.g. "it's in es_AR / Buenos Aires"). The account default can be "stuck" on another country
  (a common trap: born in Spain/Euro/Madrid without the user knowing). If it looks inconsistent
  with the user's context, offer to adjust it.
- **If you detect a strange or inconsistent locale/timezone** on an existing sheet (e.g. the user
  is in Argentina but the sheet is es_ES / Euro / Europe/Madrid), **raise a friendly flag and ask
  ONCE** (don't repeat the same question). Offer these paths:
    1. Use the user's local currency/format (e.g. Pesos) without touching the document's locale.
    2. Leave everything as is (respect the document's locale).
    3. **Fix the sheet's configuration**: if the user agrees, change this sheet's locale/timeZone
       via `updateSpreadsheetProperties` (never silently, always with an OK). Offer to do it now or
       "later".
  Always make clear that, until they decide, you respected what was there and touched nothing.
  Key note: if the user finds that **ALL their new sheets are born with the odd locale**, that's
  the **Google account default**, which the API CANNOT change. Point them to the official setting:
  https://support.google.com/docs/answer/58515 (and per-sheet: File → Settings). Many people don't
  know these settings exist.
- When in doubt about locale: **respect what you receive and flag it**, rather than "guessing".

## First-time setup (once per account)

If there are no credentials for the target account, you must create a Google Cloud project and
authorize access once. The full step-by-step — including the OAuth flow, how to read the `code`
from the localhost redirect, and (for personal accounts) publishing the app so the token doesn't
expire — is in **`references/setup.md`**. The code-for-token exchange is implemented in
**`scripts/oauth_setup.py`**. When done, save the `<account>.json` **only** in the user's private
local folder (never in Drive, iCloud, or a repo).

## Limitations & feedback

The universe of locale / language / timezone combinations is huge and can't be tested exhaustively.
The skill relies on the document's locale (robust) and on verifying rendered values (catches
`#ERROR!`), but edge cases may exist. If something doesn't work as expected, that's valuable data:
report it through the feedback channel listed by whoever shared this skill (or the marketplace you
installed it from). The skill prioritizes respecting what it receives and flagging, over breaking or
guessing.

## Security

- The `<account>.json` file (client_id + client_secret + refresh_token) is equivalent to a
  password: never write it to Drive, a synced folder, or the chat.
- Store credentials only in the user's private local folder.
- The user can revoke access anytime at https://myaccount.google.com/permissions
