#!/usr/bin/env python3
"""
BEING _ OMEGA + PRIM E — WhatsApp login automation (full management).

Drive the WhatsApp macOS app (installed from a .dmg) through account login /
registration / logout entirely from the QB Protocol layer, and auto-fill the
verification code using the virtual-SIM SMS provider in ``being.sms``.

Two WhatsApp login modes exist on WhatsApp <= 2.26 on macOS:
  * Link to an existing account — the Mac displays a QR code that the user
    scans with their phone. No SMS to the Mac (handled by eye/phone). This
    module targets the QR-link path by bringing the app to the foreground so
    the QR surface is shown; the user scans it once.
  * Register a new number — WhatsApp sends an SMS (or voice call) OTP to the
    phone number being registered. If that number is the QB-controlled virtual
    Twilio number, :meth:`WhatsAppClient.login` receives the code automatically
    and submits it -- "full management".

UI automation uses AppleScript via ``System Events`` (Accessibility API). The
automation process MUST be granted Accessibility permission in System Settings
→ Privacy & Security → Accessibility; otherwise every script returns
"access not allowed". A :class:`RecordingDriver` (fake) is used in tests so the
login state-machine and OTP auto-fill can be verified deterministically.
"""
from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import time
from typing import List, Optional

from .sms import SMSService, get_default


def install_from_dmg(dmg_path: str, dest: str = "/Applications",
                     app_name: Optional[str] = None) -> str:
    """Mount *dmg_path*, copy the contained .app to *dest*, unmount, return path.

    Idempotent: skips install if the app already exists at dest.
    """
    name = app_name or os.path.splitext(os.path.splitext(os.path.basename(dmg_path))[0])[0]
    if not name.endswith(".app"):
        name = name + ".app"
    dest_app = os.path.join(dest, name)
    if os.path.exists(dest_app):
        return dest_app

    import plistlib
    attach = subprocess.run(["hdiutil", "attach", "-nobrowse", "-plist", dmg_path],
                            capture_output=True, text=True)
    if attach.returncode != 0:
        raise RuntimeError(f"hdiutil attach failed: {attach.stderr.strip()}")
    mounts = []
    try:
        plist = plistlib.loads(attach.stdout.encode("utf-8"))
    except Exception:
        plist = None
    if isinstance(plist, dict):
        for entity in plist.get("system-entities", []):
            mp = entity.get("mount-point")
            if isinstance(mp, str) and mp.startswith("/Volumes/"):
                mounts.append(mp)
    if not mounts:
        mounts = [f"/Volumes/{name}"]
    mnt = mounts[0]
    atexit.register(lambda: subprocess.run(["hdiutil", "detach", mnt, "-quiet"],
                                           capture_output=True, text=True))

    apps = [d for d in os.listdir(mnt) if d.endswith(".app")]
    if not apps:
        raise RuntimeError(f"no .app found in {mnt}")
    src = os.path.join(mnt, apps[0])
    final_name = apps[0]
    dest_app = os.path.join(dest, final_name)
    os.makedirs(dest, exist_ok=True)
    shutil.copytree(src, dest_app, dirs_exist_ok=True)
    subprocess.run(["hdiutil", "detach", mnt, "-quiet"], capture_output=True, text=True)
    return dest_app


class WhatsAppDriver:
    """Abstract UI driver: real AppleScript vs. a fake for tests."""

    def open_app(self) -> None: ...
    def click(self, label: str) -> bool: ...
    def type_text(self, text: str) -> None: ...
    def set_text(self, label: str, text: str) -> None: ...
    def exists(self, label: str) -> bool: ...
    def screenshot(self, path: str) -> None: ...


class AXScriptDriver(WhatsAppDriver):
    """Real driver: AppleScript GUI scripting via System Events (needs AX permission)."""

    APP = "WhatsApp"

    def _run(self, script: str) -> subprocess.CompletedProcess:
        return subprocess.run(["osascript", "-e", script], capture_output=True,
                              text=True, timeout=20)

    def open_app(self) -> None:
        self._run(f'tell application "{self.APP}" to activate')
        time.sleep(1.0)

    def exists(self, label: str) -> bool:
        """True if any UI element in the WhatsApp process has AXName containing *label*."""
        sc = (f'tell application "System Events" to tell process "{self.APP}"\n'
              f'  set hits to (get name of every UI element whose name contains "{label}")\n'
              f'  return (count of hits) > 0\n'
              f'end tell')
        r = self._run(sc)
        return ("true" in r.stdout.lower()) if r.returncode == 0 else False

    def click(self, label: str) -> bool:
        """Click the first button/menu-item/element whose name contains *label*."""
        sc = (f'tell application "System Events" to tell process "{self.APP}"\n'
              f'  if exists (first button whose name contains "{label}") then\n'
              f'    click (first button whose name contains "{label}")\n'
              f'  else if exists (first menu item whose name contains "{label}") then\n'
              f'    click (first menu item whose name contains "{label}")\n'
              f'  else if exists (first UI element whose name contains "{label}") then\n'
              f'    click (first UI element whose name contains "{label}")\n'
              f'  else\n'
              f'    error "no AX element named {label}"\n'
              f'  end if\n'
              f'end tell')
        r = self._run(sc)
        return r.returncode == 0 and "error" not in r.stderr.lower()

    def type_text(self, text: str) -> None:
        sc = (f'tell application "System Events"\n  keystroke "{text}"\nend tell')
        self._run(sc)

    def set_text(self, label: str, text: str) -> None:
        """Type *text* into the focused input (WhatsApp text fields aren't always
        directly addressable, so focus then keystroke). Falls back to any
        text field whose AXValue contains *label*."""
        sc = (f'tell application "System Events" to tell process "{self.APP}"\n'
              f'  try\n'
              f'    set value of text field 1 of scroll area 1 to "{text}"\n'
              f'  on error\n'
              f'    keystroke "{text}"\n'
              f'  end try\n'
              f'end tell')
        self._run(sc)

    def screenshot(self, path: str) -> None:
        subprocess.run(["screencapture", "-l$(osascript -e 'id of process \"WhatsApp\"')", path],
                       capture_output=True, text=True)


class RecordingDriver(WhatsAppDriver):
    """Fake driver that records calls for deterministic unit tests."""

    def __init__(self) -> None:
        self.events: List[str] = []

    def open_app(self) -> None:
        self.events.append("open_app")

    def click(self, label: str) -> bool:
        self.events.append(f"click:{label}")
        return True

    def type_text(self, text: str) -> None:
        self.events.append(f"type:{text}")

    def set_text(self, label: str, text: str) -> None:
        self.events.append(f"set_text:{label}={text}")

    def exists(self, label: str) -> bool:
        self.events.append(f"exists:{label}")
        return True

    def screenshot(self, path: str) -> None:
        self.events.append("screenshot")


class WhatsAppClient:
    """Drive WhatsApp login/logout + auto-fill OTP from the virtual-SIM inbox."""

    def __init__(self, driver: Optional[WhatsAppDriver] = None,
                 sms: Optional[SMSService] = None) -> None:
        self.driver = driver or AXScriptDriver()
        self.sms = sms or get_default()

    def login(self, phone_number: str, otp_timeout: float = 120.0) -> bool:
        """Register/link flow for *phone_number*.

        - Opens WhatsApp to the QR-link surface (existing account) by default;
          if a phone-number entry is present, submits *phone_number*, requests an
          SMS OTP to that number via the virtual-SIM provider, and auto-fills it.
        Returns True on success.
        """
        self.driver.open_app()
        # New-account / phone-number path (WhatsApp macOS "Enter your phone number").
        if self.driver.exists("Phone Number") or self.driver.exists("phone number"):
            self.driver.set_text("phone", phone_number)
            self.driver.click("Continue")
            if self.driver.exists("SMS") or self.driver.exists("Text message"):
                self.driver.click("Send code")
            code = self.sms.receive_code(timeout=otp_timeout)
            if not code:
                return False
            self.driver.set_text("code", code)
            self.driver.click("Verify")
            return self.driver.exists("Chats") or self.driver.exists("Settings")
        # Link-existing-account path: show QR so the user can scan with their phone.
        self.driver.click("Link a Device")
        return self.driver.exists("Scan QR")

    def logout(self) -> bool:
        self.driver.open_app()
        self.driver.click("Settings")
        self.driver.click("Log Out")
        self.driver.click("Log Out")
        return not self.driver.exists("Chats")


def login_cli(number: str, otp_timeout: float = 120.0) -> int:
    cli = WhatsAppClient()
    ok = cli.login(number, otp_timeout=otp_timeout)
    print("login:", "OK" if ok else "FAILED")
    return 0 if ok else 1


__all__ = ["install_from_dmg", "WhatsAppDriver", "AXScriptDriver",
           "RecordingDriver", "WhatsAppClient", "login_cli"]
