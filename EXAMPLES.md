# Sheetwright — Examples

Three end-to-end use cases. Just talk to Claude in plain language.

## 1. Formatted budget comparison

> "Create a budget comparison in my Drive called 'Suppliers Q3'. Columns: Supplier, Amount, Delivery
> (days), Status. Add 3 suppliers, a colored header with white text, format Amount as currency, and
> highlight the cheapest row. Send me the link."

Sheetwright creates the spreadsheet, applies real formatting (header colors, currency), highlights
the cheapest supplier, verifies via API, and returns the link.

## 2. Native Table with dropdown and Drive links

> "Turn this range into a Google Sheets Table with a Status dropdown (Received / Pending / Rejected)
> and a 'Quote' column that links to each supplier's PDF in my Drive."

Sheetwright builds a native Table with proper column types, a dropdown on Status, and `HYPERLINK`
formulas that open the Drive files — using the correct formula separator for the sheet's locale.

## 3. Locale-aware editing (respects & flags)

> "In this sheet, add a Total column and format the amounts as currency."  *(the sheet's regional
> settings are on the wrong country, e.g. Spain/Euro, while you're elsewhere)*

Sheetwright detects the sheet's locale, **respects** it (never changes it silently), and **flags**
the mismatch — asking once whether to use your local currency, leave it as is, or fix the sheet's
regional settings (which it can do via the API, with your OK). It verifies the result silently via
the API, without opening a browser.
