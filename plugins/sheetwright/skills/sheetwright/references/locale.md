# Locale, languages and timezone — how Sheetwright stays "context aware"

## The core idea
A Google Sheet has its own **regional settings** (locale) and **timezone**, stored INSIDE the
document. They are the only thing that determines:
- how **formulas are parsed** (argument separator: `,` vs `;`),
- how currency, numbers and dates are **formatted** by default.

The skill reads these two fields via API and adapts to them:
```python
loc, tz = sheet_locale(s, spreadsheet_id)   # e.g. ('es_AR', 'America/Buenos_Aires')
```
`properties.locale` and `properties.timeZone` are the **source of truth**.

## The layers that do NOT matter (the "stew")
These are *display* layers and do NOT affect data or formulas. The skill ignores them on purpose:
- Operating system language (Windows/Mac in English, Spanish, etc.).
- Google account language.
- Google Sheets UI language (the menus).
- Browser (Chrome) language.

You can have Chrome in English, the account in English, the Sheets UI in Latin-American Spanish and
the document in Spain: it doesn't matter. The API reports the **document's locale** and the skill
acts on THAT. That's why it's robust to any bizarre combination.

## Argument separator
- Locale with **comma decimal** (es_AR, es_ES, pt_BR, de_DE, fr_FR, most of LatAm/Europe)
  → argument separator **`;`**.
- Locale with **period decimal** (en_US, en_GB, en_*) → separator **`,`**.

Heuristic used: `';' if not locale.startswith('en') else ','`. Covers the vast majority.
As a safety net, `write_hyperlink` **self-heals**: it writes, reads the rendered value, and if it's
`#ERROR!` it flips the separator and retries. So it doesn't depend on the heuristic alone.

## Function names: always English via the API
When writing via API (`USER_ENTERED`), **function names are English** — `HYPERLINK`, `SUM`, `IF` —
regardless of:
- the UI language, or
- the document's "Always use English function names" toggle.

That toggle and the translated names are a UI thing. Via API, English always. The ONLY thing the
locale changes is the separator. (Verified in practice: an English `HYPERLINK` works in an es_ES
sheet by only changing `,` to `;`.)

## When creating a new spreadsheet
`spreadsheets.create` without specifying a locale inherits the **account default**. That default is
sometimes "stuck" on an unexpected country (a frequent real case: born in Spain, Euro, Madrid).
The skill CANNOT unstick the user's account default, but it MUST:
- report which locale/timeZone the new sheet got, and
- if it looks inconsistent with the context, offer to set it explicitly:
```python
s.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests":[
  {"updateSpreadsheetProperties":{
     "properties":{"locale":"es_AR","timeZone":"America/Argentina/Buenos_Aires"},
     "fields":"locale,timeZone"}}]}).execute()
```

## Against existing sheets with an "odd" locale
1. **Respect**: never change an existing sheet's locale silently.
2. **Detect and flag, asking ONCE** (don't repeat the same question). Offer:
   1. use the user's local currency/format without touching the document's locale,
   2. leave everything as is,
   3. fix THIS sheet's configuration (with the user's OK), now or "later".
3. **Fix this sheet** (only with consent):
```python
s.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests":[
  {"updateSpreadsheetProperties":{
     "properties":{"locale":"es_AR","timeZone":"America/Argentina/Buenos_Aires"},
     "fields":"locale,timeZone"}}]}).execute()
```
4. **The recurring default is NOT API**: if ALL the user's new sheets are born with the odd locale,
   that's a **Google account** setting (the API can't change it). Point them to the official docs:
   https://support.google.com/docs/answer/58515 (and per sheet: File → Settings → Locale / Time
   zone).

## How the skill "raises flags"
There is no separate alert system: the mechanism is that Claude, following these instructions,
**mentions it in its reply to the user** in natural language (respecting what's there and offering
help). That message IS the flag, and it's the reasonable way to warn without breaking anything.
