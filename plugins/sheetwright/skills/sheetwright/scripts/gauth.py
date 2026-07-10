"""Auth for the Sheetwright native Google Sheets/Drive bridge.

Loads a per-account OAuth credential (client_id + client_secret + refresh_token) and returns
authorized Sheets v4 and Drive v3 services. Credentials do NOT live in the skill: they are a
private <account>.json file owned by the user.

Credential resolution (in order):
  1. Explicit path passed as an argument.
  2. Environment variable GOOGLE_SHEETS_CREDS (path to a json, or the json text inline).
  3. Search under /mnt/user-data/uploads/**/credentials/<account>.json (files staged from the
     user's device in Cowork). Also matches a 'credenciales' folder for backwards compatibility.
"""
import os
import glob
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _resolve(path=None, account=None):
    # 1) explicit path
    if path and os.path.exists(path):
        return path
    # 2) environment variable (path or inline json)
    env = os.environ.get("GOOGLE_SHEETS_CREDS")
    if env:
        if os.path.exists(env):
            return env
        try:
            json.loads(env)
            tmp = "/tmp/_sheetwright_creds_env.json"
            with open(tmp, "w") as f:
                f.write(env)
            return tmp
        except Exception:
            pass
    # 3) credentials staged from the device
    pats = [
        "/mnt/user-data/uploads/**/credentials/*.json",
        "/mnt/user-data/uploads/**/credenciales/*.json",
        "/mnt/user-data/uploads/**/*.json",
    ]
    found = []
    for p in pats:
        found += glob.glob(p, recursive=True)
    # de-dup while keeping order
    seen = set()
    found = [f for f in found if not (f in seen or seen.add(f))]
    if account:
        for f in found:
            if account.lower() in os.path.basename(f).lower():
                return f
    if len(found) == 1:
        return found[0]
    if found:
        raise RuntimeError(
            "Multiple credential files found; specify the account or the path. "
            f"Candidates: {found}")
    raise FileNotFoundError(
        "No credentials found. Stage <account>.json from the user's private folder "
        "(default ~/Claude/Secrets/credentials/) or pass the path. If none exist, run the "
        "first-time setup (references/setup.md).")


def load_creds(path=None, account=None):
    with open(_resolve(path, account)) as f:
        c = json.load(f)
    return Credentials(
        token=None,
        refresh_token=c["refresh_token"],
        client_id=c["client_id"],
        client_secret=c["client_secret"],
        token_uri=c.get("token_uri", "https://oauth2.googleapis.com/token"),
        scopes=c.get("scopes", [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]),
    )


def drive(path=None, account=None):
    return build("drive", "v3", credentials=load_creds(path, account),
                 cache_discovery=False)


def sheets(path=None, account=None):
    return build("sheets", "v4", credentials=load_creds(path, account),
                 cache_discovery=False)


def whoami(path=None, account=None):
    """Return the authorized account's email (handy to verify)."""
    return drive(path, account).about().get(fields="user").execute()["user"]["emailAddress"]
