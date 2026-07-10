# First-time setup (create `<account>.json` for a Google account)

Goal: leave an `<account>.json` (client_id + client_secret + refresh_token) saved in the user's
private local folder, reusable forever. Takes ~15 min once per account.

You need: the target Google account, the user's logged-in browser (Claude in Chrome) or to guide
them step by step, and Python with internet access.

## Steps

1. **Project**: create one at `console.cloud.google.com/projectcreate`. If the account belongs to a
   Google Workspace, the project can be created under that organization (enables the "Internal"
   user type below).
2. **APIs**: enable "Google Sheets API" and "Google Drive API" (under `apis/library/...`).
3. **Consent** (Google Auth Platform → Overview → Get started): app name, support email, user type,
   contact email, accept the data policy.
   - **Personal account**: choose **External**.
   - **Workspace account you administer**: choose **Internal** — no "unverified app" warning, no
     publishing step, and the token doesn't expire. (Best path when available.)
4. **Publish to Production** (only for External / personal accounts): Audience → "Publish app" →
   Confirm. KEY: if it stays in "Testing", the refresh token expires after 7 days. (Internal apps
   don't need this.)
5. **Credential**: create an OAuth client of type **Desktop app** (`auth/clients/create`). Save the
   `client_id`. The `client_secret` (starts with `GOCSPX-`) is only shown at creation: capture it
   from the dialog, or generate one with "Add secret" and read it from the DOM (look for text
   containing `GOCSPX`).
6. **Authorization URL**:
   ```
   python scripts/oauth_setup.py url --client-id <ID> --client-secret <SECRET> --account <alias>
   ```
   Open that URL in the user's browser.
7. **Consent in the browser**: pick the account → for External/personal, pass the "Google hasn't
   verified this app" screen (Advanced → "Go to <app> (unsafe)"; it's normal — it's the user's own
   app) → grant the permissions (Sheets + Drive) → Continue. For Internal apps there's no warning.
8. **Read the code**: Google redirects to `http://localhost:8765/?code=...&state=...`. The page
   doesn't load (nothing listens on that port) but the `code` is in the tab URL. Read the URL and
   extract the `code` parameter.
9. **Exchange**:
   ```
   python scripts/oauth_setup.py exchange --code "<CODE>" --out /tmp/<alias>.json
   ```
10. **Save**: copy `/tmp/<alias>.json` into the user's private local folder
    (default `~/Claude/Secrets/credentials/<alias>.json`), permissions 600, **never** in
    Drive/iCloud/repos. Verify with `gauth.whoami("/tmp/<alias>.json")`.

## Hygiene / rotation (if a secret or token was exposed)
- Revoke the old refresh token: `python scripts/oauth_setup.py revoke --refresh-token <RT>`.
- Rotate the client secret in the console: disable and delete the old one, generate a new one, and
  re-run steps 6–10 with the new secret. (Revoke BEFORE minting the new token — see gotchas.md.)

## Where to store (privacy)
- Recommended: a local folder OUTSIDE Google Drive and iCloud (not "Documents" or "Desktop" if the
  user has iCloud "Desktop & Documents" on).
- For unattended use (without the user's computer open), the alternative is an environment variable
  `GOOGLE_SHEETS_CREDS` in the execution environment (not a synced file).

## Browser automation notes
Some Google account pages (consent) can be flaky under browser automation (frozen renderer). If a
click doesn't register, read elements via the accessibility tree, and hand the final "Allow"/"Go to
app" click to the user, then read the resulting localhost URL. Also, the console may block the
"Download JSON" of the client secret under automation — reading the `GOCSPX-` value from the DOM is
the reliable path.
