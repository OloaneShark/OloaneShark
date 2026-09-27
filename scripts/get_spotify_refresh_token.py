#!/usr/bin/env python3
"""Obtain a Spotify refresh token using only the Python standard library."""

from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "user-read-currently-playing user-read-playback-state"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"


class CallbackState:
    def __init__(self, expected_state: str) -> None:
        self.expected_state = expected_state
        self.code: str | None = None
        self.error: str | None = None
        self.event = threading.Event()


def build_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
    )
    return f"{AUTH_URL}?{params}"


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict[str, object]:
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")

    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    auth_header = base64.b64encode(credentials).decode("ascii")

    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Spotify token exchange failed: {message}") from exc


def make_handler(callback_state: CallbackState) -> type[BaseHTTPRequestHandler]:
    class SpotifyCallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            returned_state = query.get("state", [""])[0]

            if returned_state != callback_state.expected_state:
                callback_state.error = "Callback state did not match."
            elif "error" in query:
                callback_state.error = query["error"][0]
            else:
                callback_state.code = query.get("code", [None])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"Spotify authorization received. You can close this window."
            )
            callback_state.event.set()

    return SpotifyCallbackHandler


def wait_for_local_code(redirect_uri: str, state: str) -> str:
    parsed = urllib.parse.urlparse(redirect_uri)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("Local callback mode requires a localhost redirect URI.")

    port = parsed.port or 80
    callback_state = CallbackState(expected_state=state)
    server = HTTPServer((parsed.hostname or "127.0.0.1", port), make_handler(callback_state))

    print(f"Waiting for Spotify callback on {redirect_uri} ...")
    try:
        server.handle_request()
    finally:
        server.server_close()

    if callback_state.error:
        raise RuntimeError(callback_state.error)
    if not callback_state.code:
        raise RuntimeError("Spotify callback did not include an authorization code.")
    return callback_state.code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a Spotify refresh token for the profile now-playing SVG."
    )
    parser.add_argument("--manual", action="store_true", help="paste the authorization code manually")
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    args = parser.parse_args()

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your environment first.",
            file=sys.stderr,
        )
        return 1

    state = secrets.token_urlsafe(24)
    auth_url = build_auth_url(client_id, args.redirect_uri, state)
    print("\nOpen this Spotify authorization URL:\n")
    print(auth_url)
    print()

    if not args.manual:
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass
        code = wait_for_local_code(args.redirect_uri, state)
    else:
        code = input("Paste the authorization code from the callback URL: ").strip()

    token_response = exchange_code(client_id, client_secret, code, args.redirect_uri)
    refresh_token = token_response.get("refresh_token")

    if not isinstance(refresh_token, str) or not refresh_token:
        print(json.dumps(token_response, indent=2))
        print("Spotify did not return a refresh token.", file=sys.stderr)
        return 1

    print("\nSPOTIFY_REFRESH_TOKEN:\n")
    print(refresh_token)
    print("\nAdd this value to Vercel. Do not commit it to Git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
