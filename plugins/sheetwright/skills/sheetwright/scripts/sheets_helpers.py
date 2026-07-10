"""Helpers for common Google Sheets operations that encapsulate the gotchas.

Every function takes `s` = a Sheets v4 service (from gauth.sheets()).
"""
import functools


# ---------- Locale / formulas ----------

@functools.lru_cache(maxsize=128)
def locale_sep(s, spreadsheet_id):
    """Formula argument separator based on the document locale.

    In comma-decimal locales (es_*, pt_BR, de_*, fr_*, most of LatAm/Europe) Google uses ';';
    in period-decimal locales (en_*) it uses ','. Writing HYPERLINK with a comma in a comma-decimal
    sheet yields #ERROR!, so we always detect the locale.
    """
    loc = s.spreadsheets().get(
        spreadsheetId=spreadsheet_id, fields="properties.locale"
    ).execute()["properties"].get("locale", "en_US")
    return ";" if not loc.startswith("en") else ","


def hyperlink(s, spreadsheet_id, url, label):
    sep = locale_sep(s, spreadsheet_id)
    return f'=HYPERLINK("{url}"{sep}"{label}")'


def drive_file_link(s, spreadsheet_id, file_id, label):
    return hyperlink(s, spreadsheet_id,
                     f"https://drive.google.com/file/d/{file_id}/view", label)


def write_values(s, spreadsheet_id, a1_range, values):
    """Write values with USER_ENTERED (so formulas like HYPERLINK are evaluated)."""
    return s.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=a1_range,
        valueInputOption="USER_ENTERED", body={"values": values}).execute()


# ---------- Native Tables ----------
#
# Encapsulated gotchas:
#  - tableId is a STRING (not a number) in updateTable.
#  - updateTable with fields='columnProperties' REPLACES the whole list: sending a single column
#    deletes the rest (e.g. you lose a DROPDOWN type). So set_table_columns requires the full list.
#  - For currency use columnType 'CURRENCY' (it respects the locale); the column type overrides any
#    manual number format.

def create_table(s, spreadsheet_id, sheet_id, name, first_row, last_row, columns):
    """Create a native Table over [first_row, last_row) x [0, len(columns)).

    `columns` is a list of dicts, each:
      {"name": "Supplier", "type": "TEXT"}
      {"name": "Status", "type": "DROPDOWN", "values": ["Received", "Pending"]}
    Useful types: TEXT, DOUBLE, CURRENCY, PERCENT, DATE, DROPDOWN.
    The first row of the range is the header (must contain the column names).
    """
    col_props = []
    for i, c in enumerate(columns):
        cp = {"columnIndex": i, "columnName": c["name"], "columnType": c["type"]}
        if c["type"] == "DROPDOWN" and c.get("values"):
            cp["dataValidationRule"] = {"condition": {"type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in c["values"]]}}
        col_props.append(cp)
    req = {"addTable": {"table": {
        "name": name,
        "range": {"sheetId": sheet_id, "startRowIndex": first_row, "endRowIndex": last_row,
                  "startColumnIndex": 0, "endColumnIndex": len(columns)},
        "columnProperties": col_props,
    }}}
    s.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": [req]}).execute()
    # return the tableId (string) for later updates
    meta = s.spreadsheets().get(spreadsheetId=spreadsheet_id,
                                fields="sheets(properties.sheetId,tables)").execute()
    for sh in meta["sheets"]:
        if sh["properties"]["sheetId"] == sheet_id:
            for t in sh.get("tables", []):
                if t.get("name") == name:
                    return t["tableId"]
    return None


def set_table_columns(s, spreadsheet_id, table_id, columns):
    """Rewrite ALL the table columns (you MUST send the full list).

    `columns` uses the same format as create_table. `table_id` goes as a string.
    """
    col_props = []
    for i, c in enumerate(columns):
        cp = {"columnIndex": i, "columnName": c["name"], "columnType": c["type"]}
        if c["type"] == "DROPDOWN" and c.get("values"):
            cp["dataValidationRule"] = {"condition": {"type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in c["values"]]}}
        col_props.append(cp)
    return s.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [
        {"updateTable": {"table": {"tableId": str(table_id), "columnProperties": col_props},
                         "fields": "columnProperties"}}]}).execute()


# ---------- Basic formatting ----------

def repeat_format(sheet_id, r0, r1, c0, c1, fmt, fields):
    """Return a repeatCell request (to pass to batchUpdate)."""
    return {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "cell": {"userEnteredFormat": fmt}, "fields": fields}}


def cell_format(bg=None, fg=None, bold=False, size=None, halign=None, numfmt=None):
    """Build a userEnteredFormat. Colors as (r,g,b) in 0..1."""
    cf = {}
    if bg:
        cf["backgroundColor"] = {"red": bg[0], "green": bg[1], "blue": bg[2]}
    tf = {}
    if fg:
        tf["foregroundColor"] = {"red": fg[0], "green": fg[1], "blue": fg[2]}
    if bold:
        tf["bold"] = True
    if size:
        tf["fontSize"] = size
    if tf:
        cf["textFormat"] = tf
    if halign:
        cf["horizontalAlignment"] = halign
    if numfmt:
        cf["numberFormat"] = {"type": "NUMBER", "pattern": numfmt}
    return cf


# ---------- Locale + silent verification (no browser) ----------

ERROR_TOKENS = ("#ERROR!", "#REF!", "#NAME?", "#N/A", "#VALUE!", "#DIV/0!",
                "#NUM!", "#NULL!")


def sheet_locale(s, spreadsheet_id):
    """Return (locale, timeZone) of the document — the ONLY source of truth for formatting and
    formulas. Independent of the Chrome / account / UI language."""
    p = s.spreadsheets().get(spreadsheetId=spreadsheet_id,
        fields="properties(locale,timeZone)").execute()["properties"]
    return p.get("locale", "en_US"), p.get("timeZone", "")


def read_effective(s, spreadsheet_id, a1_range):
    """Read the RENDERED values (what shows on screen). Used to detect formula errors
    (#ERROR! etc.) WITHOUT opening a browser."""
    return s.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=a1_range,
        valueRenderOption="FORMATTED_VALUE").execute().get("values", [])


def cells_with_errors(s, spreadsheet_id, a1_range):
    """Return the effective values that are formula errors in the range (empty = OK)."""
    bad = []
    for row in read_effective(s, spreadsheet_id, a1_range):
        for c in row:
            if isinstance(c, str) and c.strip() in ERROR_TOKENS:
                bad.append(c.strip())
    return bad


def write_hyperlink(s, spreadsheet_id, a1_cell, url, label):
    """Write a HYPERLINK SELF-HEALING the separator based on the locale, and verify the result via
    API. If the first attempt renders #ERROR!, flip the separator. Returns
    {'ok': bool, 'sep': separator_that_worked}."""
    loc, _ = sheet_locale(s, spreadsheet_id)
    order = [";", ","] if not loc.startswith("en") else [",", ";"]
    for sep in order:
        write_values(s, spreadsheet_id, a1_cell, [[f'=HYPERLINK("{url}"{sep}"{label}")']])
        eff = read_effective(s, spreadsheet_id, a1_cell)
        val = eff[0][0].strip() if (eff and eff[0]) else ""
        if val not in ERROR_TOKENS:
            return {"ok": True, "sep": sep}
    return {"ok": False, "sep": None}
