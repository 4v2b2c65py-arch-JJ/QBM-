#!/usr/bin/env python3
"""
BEING _ OMEGA + PRIM E -- FaceTime contact management.

FaceTime stalls when you dial a number/handle that isn't in the system Contacts
it has to "resolve" it (and, on a fresh contact, shows an interstitial). Adding
the contact *first* makes resolution instant, so FaceTime calls start
immediately. This module:

  * creates/updates contacts in the macOS Contacts.app via AppleScript
    (``make new person``) -- reliable, one-time Contacts Apple-event grant,
    unlike the root-locked Accessibility/TCC database;
  * launches a FaceTime call via the ``facetime://`` URL scheme (FaceTime has no
    AppleScript dictionary) -- no AX/GUI scripting required;
  * tears the call down.

Public API: :class:`FaceTimeClient` (add_contact / import_contacts / call /
end_call / list_contact_names), :func:`contact_for_otp`.
"""
from __future__ import annotations

import json
import subprocess
from typing import Dict, List, Optional, Sequence

OSASCRIPT = "/usr/bin/osascript"


def _aq(s) -> str:
    """AppleScript string literal quoting (escaping backslash + double quote)."""
    if s is None:
        return "missing value"
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def _run(script: str) -> subprocess.CompletedProcess:
    """Run an AppleScript string via ``osascript -`` (stdin) and return the result.

    Mirrors the project's real-``osascript`` driver policy (no fake backend).
    """
    proc = subprocess.run([OSASCRIPT, "-"], input=script, text=True,
                          capture_output=True, timeout=15)
    return proc


def _split_name(name: str):
    parts = (name or "").strip().split(None, 1)
    return (parts[0], parts[1] if len(parts) > 1 else "")


class FaceTimeClient:
    """Manage Contacts.app entries + launch FaceTime calls."""

    STATUS = {0: "not_determined", 1: "denied", 2: "authorized", 3: "restricted"}

    def __init__(self) -> None:
        self._store = OSASCRIPT  # contacts live in Contacts.app, driven via osascript

    # -- contacts -----------------------------------------------------------
    def add_contact(self, name: str, phone: Optional[str] = None,
                    email: Optional[str] = None, apple_id: Optional[str] = None,
                    identifier: Optional[str] = None) -> Dict[str, object]:
        """Create or update a contact. Idempotent: reusing a name updates the
        existing person rather than duplicating. One Apple-event round-trip."""
        given, family = _split_name(name)
        script = self._upsert_script(given, family, apple_id, phone, email, identifier)
        proc = _run(script)
        out = proc.stdout.strip()
        mode = "updated" if identifier is not None else "saved"
        pid = None
        if proc.returncode == 0 and out and "missing value" not in out:
            body = out.strip("{}").strip()
            parts = [p.strip() for p in body.split(", ")]
            valid = {"saved", "updated", "created", "deleted"}
            if parts and parts[-1] in valid:
                mode = parts[-1]
                pid = parts[0].split(":")[0] if len(parts) == 2 else ", ".join(parts[:-1]).split(":")[0]
            else:
                pid = body.split(":")[0]
        if pid:
            return {"name": name, "identifier": pid, "status": mode,
                    "phone": phone, "email": email}
        return {"name": name, "status": "error",
                "auth": self.STATUS.get(self._contacts_auth(), "unknown"),
                "error": (proc.stderr.strip() or out) or "create failed"}

    def _upsert_script(self, given, family, apple_id, phone, email, identifier) -> str:
        props = []
        if given:
            props.append(f"first name: {_aq(given)}")
        if family:
            props.append(f"last name: {_aq(family)}")
        if apple_id:
            props.append(f"middle name: {_aq(apple_id)}")
        prop = ", ".join(props)
        lines = ['tell application "Contacts"', '  set p to missing value']
        if identifier:
            lines.append(f'  set p to person id {_aq(identifier)} -- update')
        elif family:
            lines += [
                '  try',
                f'    set p to (first person whose first name is {_aq(given)} and last name is {_aq(family)})',
                '  end try',
                f'  if p is missing value then try',
                f'    set p to (first person whose first name is {_aq(given)})',
                '  end try',
            ]
        else:
            lines += [
                '  try',
                f'    set p to (first person whose first name is {_aq(given)})',
                '  end try',
            ]
        lines += [
            '  if p is missing value then',
            f'    set p to make new person with properties {{{prop}}}',
            '    set mode to "saved"',
            '  else',
            f'    set first name of p to {_aq(given)}',
            f'    set last name of p to {_aq(family)}',
            '    delete every phone of p',
            '    delete every email of p',
            '    set mode to "updated"',
            '  end if',
        ]
        if phone:
            lines.append(
                f'  make new phone at end of phones of p with properties '
                f'{{value: {_aq(phone)}, label: {_aq("Mobile")}}}'
            )
        if email:
            lines.append(
                f'  make new email at end of emails of p with properties '
                f'{{value: {_aq(email)}, label: {_aq("Home")}}}'
            )
        if apple_id:
            lines.append(f'  set middle name of p to {_aq(apple_id)}')
        lines.append('  return {id of p, mode}')
        lines.append('end tell')
        return "\n".join(lines)

    def import_contacts(self, contacts: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
        out = []
        for c in contacts:
            out.append(self.add_contact(
                name=c.get("name", ""),
                phone=c.get("phone"),
                email=c.get("email"),
                apple_id=c.get("apple_id"),
                identifier=c.get("identifier"),
            ))
        return out

    def list_contact_names(self) -> List[str]:
        """Names of Contact.app entries (for the OmegaTalk sidebar)."""
        proc = _run(
            'tell application "Contacts"\n'
            '  set out to {}\n'
            '  repeat with p in every person\n'
            '    set n to ""\n'
            '    set fn to first name of p\n'
            '    set ln to last name of p\n'
            '    if fn is not missing value then set n to fn\n'
            '    if ln is not missing value then set n to n & " " & ln\n'
            '    if n is not "" then copy n to end of out\n'
            '  end repeat\n'
            '  out\n'
            'end tell'
        )
        out = proc.stdout.strip()
        if proc.returncode != 0 or not out:
            return []
        import ast
        try:
            return [str(x).strip() for x in ast.literal_eval(out) if str(x).strip()]
        except Exception:
            return [s.strip() for s in out.split(", ") if s.strip() and s.strip() != ""]

    # -- calling ------------------------------------------------------------
    def call(self, destination: str, video: bool = True, dry_run: bool = False) -> Dict[str, object]:
        """Launch FaceTime pre-filled to *destination* (E.164 number or Apple ID).

        Uses the ``facetime://`` URL scheme -- FaceTime shows a confirmation
        dialog (no AX/GUI scripting). Pre-adding the contact via
        :meth:`add_contact` is what removes the resolution hang."""
        scheme = "facetime" if video else "facetime-audio"
        url = f"{scheme}://{destination}"
        if dry_run:
            return {"destination": destination, "url": url, "dry_run": True}
        subprocess.run(["open", "-a", "FaceTime", url], capture_output=True, text=True, timeout=10)
        return {"destination": destination, "url": url, "launched": True}

    def end_call(self, dry_run: bool = False) -> Dict[str, object]:
        if dry_run:
            return {"action": "end_call", "dry_run": True, "note": "would quit FaceTime"}
        _run('tell application "FaceTime" to quit')
        try:
            subprocess.run(["killall", "FaceTime"], capture_output=True, text=True, timeout=5)
        except Exception:
            pass
        return {"action": "end_call", "completed": True}

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _contacts_auth() -> int:
        try:
            from Contacts import CNContactStore
            return int(CNContactStore.authorizationStatusForEntityType_(0))
        except Exception:
            return -1


def contact_for_otp(number: str) -> Optional[str]:
    """Pin the virtual/SMS number to a Contacts entry so callers/2FA resolve
    instantly in FaceTime."""
    try:
        res = FaceTimeClient().add_contact(name="QB Virtual Number", phone=number)
        return res.get("identifier") if res.get("status") in ("saved", "updated") else None
    except Exception:
        return None


__all__ = ["FaceTimeClient", "contact_for_otp", "_split_name", "_aq"]
