"""Helpers for the first-time OAuth setup (create <account>.json).

Usage (two steps, with browser interaction in between — see references/setup.md):

  1) Authorization URL:
       python oauth_setup.py url --client-id ID --client-secret SECRET
     Prints the URL (open it in the user's browser) and saves state to /tmp/oauth_pending.json.

  2) Exchange the code (read from the http://localhost:8765/?code=... redirect):
       python oauth_setup.py exchange --code "4/0A..." --out /tmp/account.json
     Writes <account>.json with client_id + client_secret + refresh_token.
     Save that file ONLY in the user's private local folder.
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request

TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
REDIRECT = "http://localhost:8765"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
PENDING = "/tmp/oauth_pending.json"


def make_url(client_id, client_secret, account=None):
    verifier = base64.urlsafe_b64encode(os.urandom(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = base64.urlsafe_b64encode(os.urandom(9)).rstrip(b"=").decode()
    params = {
        "client_id": client_id, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent",
        "include_granted_scopes": "true", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    }
    json.dump({"client_id": client_id, "client_secret": client_secret,
               "verifier": verifier, "state": state, "account": account},
              open(PENDING, "w"))
    return AUTH_URI + "?" + urllib.parse.urlencode(params)


def exchange(code, out, retries=5):
    p = json.load(open(PENDING))
    data = urllib.parse.urlencode({
        "code": code, "client_id": p["client_id"], "client_secret": p["client_secret"],
        "redirect_uri": REDIRECT, "grant_type": "authorization_code",
        "code_verifier": p["verifier"],
    }).encode()
    tok = None
    for i in range(retries):
        try:
            tok = json.load(urllib.request.urlopen(
                urllib.request.Request(TOKEN_URI, data=data)))
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            sys.stderr.write(f"attempt {i+1}: {e.code} {body[:150]}\n")
            if "invalid_client" in body or e.code >= 500:
                time.sleep(15)
                continue
            raise
    if not tok or not tok.get("refresh_token"):
        raise RuntimeError("No refresh_token returned (was prompt=consent missing?)")
    creds = {"client_id": p["client_id"], "client_secret": p["client_secret"],
             "refresh_token": tok["refresh_token"], "token_uri": TOKEN_URI,
             "scopes": SCOPES, "account": p.get("account")}
    json.dump(creds, open(out, "w"), indent=2)
    return out


def revoke(refresh_token):
    """Revoke a refresh token (for rotation / hygiene)."""
    data = urllib.parse.urlencode({"token": refresh_token}).encode()
    urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/revoke", data=data))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("url")
    u.add_argument("--client-id", required=True)
    u.add_argument("--client-secret", required=True)
    u.add_argument("--account", default=None)
    e = sub.add_parser("exchange")
    e.add_argument("--code", required=True)
    e.add_argument("--out", required=True)
    r = sub.add_parser("revoke")
    r.add_argument("--refresh-token", required=True)
    a = ap.parse_args()
    if a.cmd == "url":
        print(make_url(a.client_id, a.client_secret, a.account))
    elif a.cmd == "exchange":
        print("written:", exchange(a.code, a.out))
    elif a.cmd == "revoke":
        revoke(a.refresh_token)
        print("revoked")
