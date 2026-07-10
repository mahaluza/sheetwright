# Gotchas — Google Sheets/Drive via API

Errors that were costly to discover. Read this before writing new code.

## Locale and formulas (argument separator)
In comma-decimal locales (es_AR, es_ES, pt_BR, de_DE, fr_FR, most of LatAm/Europe) the formula
argument separator is `;`, not `,`. Writing `=HYPERLINK("url","text")` in such a sheet returns
`#ERROR!`.
- Fix: detect the locale with `spreadsheets.get(fields='properties.locale')` and use `;` when it
  doesn't start with `en`. Already handled in `sheets_helpers.hyperlink()` / `write_hyperlink()`.
- Applies to any formula you write with `USER_ENTERED`, not just HYPERLINK.

## Writing formulas
For a formula (HYPERLINK, etc.) to evaluate when written via API, use
`valueInputOption='USER_ENTERED'`. With `RAW` it stays as text.

## Native Tables (addTable / updateTable)
- `tableId` is a **string**, not a number. Passing an int gives a 400 error.
- `updateTable` with `fields='columnProperties'` **replaces the whole column list**. Sending a
  single column loses the other columns' types (typically the DROPDOWN disappears). ALWAYS send the
  full column list (see `sheets_helpers.set_table_columns`).
- For a currency column, use `columnType='CURRENCY'` (it respects the locale, shows the local
  currency). The column type **overrides** any manual `numberFormat` you apply to those cells.
- The first row of the `addTable` range is the header; its values must match the `columnName`s.
- Don't overlap a table with merged cells or another table.

## Rotation (revoking kills the shared grant)
When the same user re-consents to the same client, Google usually groups the refresh tokens under
a **single consent grant**. Revoking ONE refresh token (the `/revoke` endpoint) **revokes the whole
grant** → both the old and the new die. So order matters:
1. To invalidate a leaked token, **revoke first** and **then** mint the new one (it lands in a new,
   live grant).
2. If you mint the new one first and then revoke the old, you take out the new one too — you'll have
   to re-mint once more.
Rotating the client secret does NOT invalidate a refresh token (the token is tied to the client_id,
not the secret); to kill a token you must revoke it (or have the user revoke access).

## Client secret
- Google no longer shows the client secret after creation. Capture it from the creation dialog
  (or from "Add secret") at that moment; it starts with `GOCSPX-`.
- To delete a secret you must **disable it first**. Limit of 2 secrets per client.

## Scopes
- `spreadsheets` is enough to read/write/create spreadsheets.
- To **move/organize existing files** in Drive you need `drive` (full); `drive.file` only sees
  files created/opened by the app.

## Refresh token / expiry
- The `refresh_token` is issued only if the flow carries `access_type=offline` AND `prompt=consent`.
- If the OAuth app stays in "Testing" publishing status (External user type), the refresh token
  **expires after 7 days**. Publish the app to Production (Google Auth Platform → Audience →
  Publish app). For Workspace accounts you administer, the "Internal" user type avoids this
  entirely (no verification warning, no expiry).

## Service account (alternative)
- A service account **cannot create** new files in a personal account's "My Drive" (no storage
  quota) — they fail with a quota error. It can edit files shared with it, or create inside a
  Shared Drive. To create spreadsheets in the user's Drive, use OAuth user credentials (not a
  service account), unless you use domain-wide delegation in a Workspace you administer.
