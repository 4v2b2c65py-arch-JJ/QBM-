#!/usr/bin/env python3
"""
BEING _ OMEGA + PRIM E — Apple-ID auto login via an in-browser session.

Reuses the user's *existing Apple-ID browser session* to sign in to QB Protocol
without re-prompting for credentials. The flow:

  1. OmegaTalk starts an ``ASWebAuthenticationSession`` (AuthenticationServices)
     pointed at QB Protocol's ``/auth/apple`` endpoint. On macOS the system opens
     the user's *default browser* (which already holds the Apple-ID session
     cookies), so the consent page is pre-authenticated.
  2. QB Protocol verifies the Apple identity (Sign in with Apple under the hood)
     and redirects back to the app's custom scheme
     ``com.being.omega.talk://auth?token=<session>&apple_id=<email>``.
  3. The callback is parsed, the session token is persisted to the Keychain
     (via the same iCloud-style store OmegaTalk already uses), and the chat opens.

All networking lives in QB Protocol's server (the daemon); the client only
orchestrates the system browser session and reads back the callback. Nothing
here stores Apple credentials — it relies on the system browser's keychain.
"""
from __future__ import annotations

import os
from typing import Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse, urlencode

SERVICE = "com.being.omega.talk"
DEFAULT_CALLBACK_SCHEME = "com.being.omega.talk"
DEFAULT_AUTH_URL = "http://127.0.0.1:17760/auth/apple"


def build_auth_url(base: Optional[str] = None, scheme: Optional[str] = None,
                   extra: Optional[Dict[str, str]] = None) -> str:
    """Build the QB Protocol Apple-auth URL the system browser will load."""
    base = base or os.environ.get("QB_AUTH_URL", DEFAULT_AUTH_URL)
    scheme = scheme or os.environ.get("QB_CALLBACK_SCHEME", DEFAULT_CALLBACK_SCHEME)
    q = {"callback_url": f"{scheme}://auth"}
    if extra:
        q.update(extra)
    sep = "&" if "?" in base else "?"
    return base + sep + urlencode(q)


def parse_callback_url(url: str) -> Dict[str, str]:
    """Parse ``com.being.omega.talk://auth?token=...&apple_id=...``."""
    parsed = urlparse(url)
    qs = {k: v[0] for k, v in parse_qs(parsed.query, keep_blank_values=True).items()}
    if parsed.path not in ("/auth", ""):
        qs.setdefault("path", parsed.path)
    return qs


# --- ASWebAuthenticationSession (native UI) ---------------------------------
# Imported lazily so this module is importable headlessly (e.g. for the pure
# helpers above and the self-test) even if AuthenticationServices is unavailable.
_session_ref = None


def start_apple_login(on_done: Callable[[Dict[str, object]], None],
                      auth_url: Optional[str] = None,
                      callback_scheme: Optional[str] = None) -> bool:
    """Start the browser-session Apple-ID login. Returns False if unsupported.

    *on_done* receives a dict: ``{"ok": True, "token": ..., "apple_id": ...}``
    or ``{"ok": False, "error": ...}`` once the flow completes (success or
    failure/cancel). The callback runs on the main thread (AppHelper).
    """
    try:
        from AuthenticationServices import ASWebAuthenticationSession
    except Exception as exc:  # pragma: no cover - environment guard
        on_done({"ok": False, "error": f"ASWebAuthenticationSession unavailable: {exc}"})
        return False

    url = auth_url or build_auth_url()
    scheme = callback_scheme or os.environ.get("QB_CALLBACK_SCHEME", DEFAULT_CALLBACK_SCHEME)
    session = ASWebAuthenticationSession.alloc().initWithURL_callbackURLScheme_completionHandler_(
        url, scheme, on_done
    )
    if session is None:
        on_done({"ok": False, "error": "could not create ASWebAuthenticationSession"})
        return False
    global _session_ref
    _session_ref = session  # keep alive until completion
    session.setPrefersEphemeralWebBrowserSession_(False)  # reuse existing Apple-ID cookies
    if not session.start():
        _session_ref = None
        on_done({"ok": False, "error": "session failed to start"})
        return False
    return True


def _persist_token(apple_id: str, token: str) -> bool:
    """Persist the authenticated session token to the Keychain store.

    Reuses OmegaTalk's keychain helper so the same iCloud-style credential +
    Touch-ID quick-unlock path applies when the app (re)opens.
    """
    try:
        from qb_protocol.ai.gpt_layer_face import keychain_add_or_update
    except Exception:  # pragma: no cover
        try:
            from ..ai.gpt_layer_face import keychain_add_or_update  # type: ignore
        except Exception:
            return False
    return keychain_add_or_update(apple_id or "unknown@icloud.local", token_hint=token)


def handle_callback(url: str, on_complete: Callable[[Tuple[bool, str, Optional[str]]], None]) -> None:
    """Call after the system browser returns *url* to the app.

    Persists the token to the Keychain and reports (ok, apple_id, token_or_error).
    """
    try:
        data = parse_callback_url(url)
        token = data.get("token", "")
        apple_id = data.get("apple_id", "")
        if not token:
            on_complete((False, apple_id, "callback missing token"))
            return
        ok = _persist_token(apple_id, token)
        on_complete((ok, apple_id, token if ok else "keychain persist failed"))
    except Exception as exc:
        on_complete((False, "", str(exc)))


__all__ = [
    "SERVICE", "DEFAULT_CALLBACK_SCHEME", "DEFAULT_AUTH_URL",
    "build_auth_url", "parse_callback_url", "start_apple_login", "handle_callback",
]
