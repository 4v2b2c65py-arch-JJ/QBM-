#!/usr/bin/env python3
"""
BEING _ OMEGA + PRIM E — virtual SIM / SMS-receive capability.

"Native Apple eSIM" is not an option here: Apple's
``CTCellularPlanProvisioning.addPlan`` API is restricted to carrier/MNO partners
that hold a special entitlement from Apple (granted only after a lengthy approval
and carrier agreement), and macOS has no native cellular radio at all. So a
"virtual SIM with SMS receiving" is realized through a **cloud virtual phone
number** exposed over an SMS provider's REST API.

Default provider: Twilio (canonical, per Twilio's "Receive an inbound SMS" and
"Virtual Phone" docs). A Twilio number is a programmatically accessible inbox:
messages sent to it arrive over the carrier network, Twilio stores them, and the
agent polls the REST API (no public webhook/tunnel required) to read codes back.

Credentials (env):
  TWILIO_ACCOUNT_SID  Twilio Account SID
  TWILIO_AUTH_TOKEN   Twilio Auth Token
  TWILIO_SMS_NUMBER   E.164 number owned by the account (the inbox)

Only the Python standard library is required (urllib). OTPs are extracted from
inbound message bodies with a regex.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional

TWILIO_API_BASE = "https://api.twilio.com/2010-04-01/Accounts"
OTP_PATTERN = re.compile(r"(?: verification |code |is |:\s*)?(\b[0-9A-F]{4,8}\b)", re.IGNORECASE)
DEFAULT_TIMEOUT = 90.0
DEFAULT_POLL_INTERVAL = 3.0


class SMSRouter:
    """Lightweight pub/sub fan-out for inbound SMS.

    Any inbound message observed by a provider's :meth:`receive_code` /
    :meth:`latest_inbound` is routed to every registered subscriber, so multiple
    client consumers (a 2FA auto-fill, a logger, a notifier) can receive codes
    in parallel off a single virtual number.
    """

    def __init__(self) -> None:
        self._subs: Dict[str, Callable[[dict], None]] = {}

    def register(self, client_id: str, callback: Callable[[dict], None]) -> None:
        self._subs[client_id] = callback

    def unregister(self, client_id: str) -> None:
        self._subs.pop(client_id, None)

    def route(self, msg: dict) -> int:
        """Deliver *msg* to every subscriber; returns count delivered."""
        if not msg or not self._subs:
            return 0
        for cb in list(self._subs.values()):
            try:
                cb(msg)
            except Exception:
                pass
        return len(self._subs)


_default_router = SMSRouter()


def register_subscriber(client_id: str, callback: Callable[[dict], None]) -> None:
    """Register *callback(msg)* to receive every inbound SMS (pub/sub)."""
    _default_router.register(client_id, callback)


def unregister_subscriber(client_id: str) -> None:
    _default_router.unregister(client_id)


class SMSService:
    """Base contract for a virtual-SMS receiver."""

    name = "base"
    credential_keys = []

    def __init__(self) -> None:
        self.enabled = self.is_configured()
        self.router = _default_router

    def is_configured(self) -> bool:
        return bool(self.credential_keys) and all(os.environ.get(k) for k in self.credential_keys)

    def _route(self, msg: Optional[dict]) -> None:
        """Fan an inbound message out to all registered subscribers."""
        if msg:
            self.router.route(msg)

    def receive_code(self, timeout: float = DEFAULT_TIMEOUT,
                     pattern: Optional[re.Pattern] = None) -> Optional[str]:
        raise NotImplementedError


class TwilioSMS(SMSService):
    """Poll a Twilio number's inbox for the most recent inbound OTP."""

    name = "twilio"
    credential_keys = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_SMS_NUMBER"]

    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None,
                 number: Optional[str] = None) -> None:
        self.account_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.number = number or os.environ.get("TWILIO_SMS_NUMBER", "")
        super().__init__()  # sets self.enabled
        # is_configured depends on the loaded creds, re-eval after assignment
        self.enabled = self.is_configured()

    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.number)

    def _auth_header(self) -> str:
        token = base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
        return "Basic " + token

    def _list_messages(self) -> List[dict]:
        url = f"{TWILIO_API_BASE}/{self.account_sid}/Messages.json?PageSize=50&To={urllib.parse.quote(self.number)}"
        req = urllib.request.Request(url, headers={"Authorization": self._auth_header()})
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - Twilio HTTPS
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("messages", [])

    def _http(self, method: str, path: str, data: dict) -> dict:
        """POST/GET a Twilio REST resource, returning parsed JSON. Raises on error."""
        url = f"{TWILIO_API_BASE}/{self.account_sid}/{path}"
        body = json.dumps(data).encode("utf-8") if data else b""
        req = urllib.request.Request(
            url, data=body or None, method=method,
            headers={"Authorization": self._auth_header(),
                     "Content-Type": "application/x-www-form-urlencoded" if data else "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - Twilio HTTPS
            return json.loads(resp.read().decode("utf-8"))

    def allocate_number(self, country: str = "US",
                        sms_enabled: bool = True) -> str:
        """Purchase a new Twilio number (E.164) for this account and return it.

        Requires an account with purchasing enabled. The number is *assigned to
        this account* immediately and becomes the active inbox via ``self.number``
        (so subsequent :meth:`receive_code` polls it).
        """
        data = {"PhoneNumber": {"country": country}}
        if sms_enabled:
            data["PhoneNumber"]["SMSReceiver"] = []
            data["PhoneNumber"]["SmsEnabled"] = "true"
        avails = self._http("GET", "AvailablePhoneNumbers/"
                            + urllib.parse.quote(country) + "/AvailablePhoneNumbers.json", {})
        nums = avails.get("available_phone_numbers", [])
        if not nums:
            raise RuntimeError(f"No Twilio numbers available for {country}")
        number = nums[0]["phone_number"]
        purchase = self._http("POST", "IncomingPhoneNumbers.json",
                              {"PhoneNumber": number, "SmsUrl": ""})
        self.number = purchase.get("phone_number") or number
        self.enabled = self.is_configured()
        return self.number

    def send_sms(self, to: str, body: str) -> dict:
        """Send an outbound SMS from the configured Twilio number."""
        url = f"{TWILIO_API_BASE}/{self.account_sid}/Messages.json"
        form = urllib.parse.urlencode({"From": self.number, "To": to, "Body": body}).encode("utf-8")
        req = urllib.request.Request(
            url, data=form, method="POST",
            headers={"Authorization": self._auth_header(),
                     "Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))

    def latest_inbound(self, since: Optional[float] = None) -> Optional[dict]:
        """Return the newest inbound message (from != own number) after *since*."""
        msgs = self._list_messages()
        inbound = [m for m in msgs if m.get("from", "") != self.number]
        if since is not None:
            def _after(m):
                try:
                    return time.mktime(time.strptime(m["date_sent"], "%a, %d %b %Y %H:%M:%S %z")) >= since
                except Exception:
                    return True
            inbound = [m for m in inbound if _after(m)]
        return inbound[0] if inbound else None

    def receive_code(self, timeout: float = DEFAULT_TIMEOUT,
                     pattern: Optional[re.Pattern] = None) -> Optional[str]:
        """Poll the inbox until an OTP/code appears in a new inbound SMS."""
        if not self.enabled:
            return None
        pat = pattern or OTP_PATTERN
        start = time.time()
        floor = start - 1.0
        while time.time() - start < timeout:
            msg = self.latest_inbound(since=floor)
            self._route(msg)
            if msg and (code := _extract_code(msg.get("body", ""), pat)):
                return code
            time.sleep(DEFAULT_POLL_INTERVAL)
        return None


class LocalInboxSMS(SMSService):
    """Credential-free virtual-SMS provider backed by a local JSONL inbox.

    Used for self-tests, CI, and local dev: an inbound message written to
    ``~/.qb_protocol_sms_inbox.jsonl`` (one JSON object per line: ``{"from":
    "<e164>", "to": "<e164>", "body": "...", "ts": <unix>}``) becomes visible to
    :meth:`receive_code` as soon as it is appended. This exercises the full
    receive -> extract-OTP pipeline without any external account or network.
    """

    name = "local_inbox"
    credential_keys: List[str] = []

    def __init__(self, number: Optional[str] = None,
                 inbox_path: Optional[str] = None) -> None:
        self.number = number or os.environ.get("VIRTUAL_SMS_NUMBER", "+1_VIRTUAL")
        self.inbox_path = inbox_path or os.environ.get(
            "QB_SMS_INBOX", os.path.expanduser("~/.qb_protocol_sms_inbox.jsonl"))
        super().__init__()
        self.enabled = True

    def _read_inbox(self, since: Optional[float] = None) -> List[dict]:
        if not os.path.exists(self.inbox_path):
            return []
        out: List[dict] = []
        with open(self.inbox_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = msg.get("ts", 0)
                if since is None or ts >= since:
                    out.append(msg)
        return out

    def latest_inbound(self, since: Optional[float] = None) -> Optional[dict]:
        msgs = self._read_inbox(since=since)
        inbound = [m for m in msgs if m.get("to", "") == self.number]
        return inbound[-1] if inbound else None

    def receive_code(self, timeout: float = DEFAULT_TIMEOUT,
                     pattern: Optional[re.Pattern] = None) -> Optional[str]:
        pat = pattern or OTP_PATTERN
        start = time.time()
        floor = start - 1.0
        while time.time() - start < timeout:
            msg = self.latest_inbound(since=floor)
            self._route(msg)
            if msg and (code := _extract_code(msg.get("body", ""), pat)):
                return code
            time.sleep(DEFAULT_POLL_INTERVAL)
        return None


def simulate_inbound_sms(sender: str, to: str, body: str,
                         inbox_path: Optional[str] = None) -> dict:
    """Append a synthetic inbound SMS to the local inbox sink (testing only)."""
    path = inbox_path or os.environ.get(
        "QB_SMS_INBOX", os.path.expanduser("~/.qb_protocol_sms_inbox.jsonl"))
    rec = {"from": sender, "to": to, "body": body, "ts": time.time()}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def _extract_code(body: str, pattern: re.Pattern) -> Optional[str]:
    if not body:
        return None
    m = pattern.search(body)
    return m.group(1) if m else None


def get_default() -> SMSService:
    """Return TwilioSMS if configured, else a functional LocalInboxSMS."""
    tw = TwilioSMS()
    if tw.enabled:
        return tw
    return LocalInboxSMS()


__all__ = ["SMSService", "TwilioSMS", "LocalInboxSMS", "SMSRouter",
           "simulate_inbound_sms", "register_subscriber", "unregister_subscriber",
           "get_default", "DEFAULT_TIMEOUT", "OTP_PATTERN"]
