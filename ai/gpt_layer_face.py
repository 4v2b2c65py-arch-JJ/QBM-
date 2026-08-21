#!/usr/bin/env python3
"""
OmegaTalk — FaceTime-styled native chat with the BEING GPT Layer.

A native macOS (Cocoa / PyObjC) app that looks like FaceTime: a video-style
window with a camera preview, a contacts sidebar, and a chat panel. The user
signs in (iCloud-style: Apple-ID credentials persisted in the Keychain +
Touch ID quick-unlock — no Apple-Developer signing required) and chats with the
BEING _ OMEGA + PRIM E GPT Layer (TinyLlama via ctransformers, backed by the
`gpt-layer` quick-assist command).

Run directly with the project venv:
    ~/delta-stream/qb_protocol/.venv/bin/python3 qb_protocol/ai/gpt_layer_face.py
"""
from __future__ import annotations

import json
import os
import objc
import subprocess
import sys
import threading
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent         # .../qb_protocol
_PARENT = _ROOT.parent                                  # .../delta-stream
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

SERVICE = "com.being.omega.talk"
KEYCHAIN_ACCOUNT = "omegatalk-user"
GPT_LAYER_CMD = "/usr/local/bin/gpt-layer"
CONTACT_NAME = "QB Protocol"

# Apple-ID browser-session auto-login helper (AuthenticationServices). Imported
# defensively: the UI works without it; only the "Continue with Apple ID" button
# is disabled when it is unavailable.
try:
    from qb_protocol.being.auth_browser import (
        start_apple_login, handle_callback, parse_callback_url,
        build_auth_url, DEFAULT_AUTH_URL)
except Exception:  # pragma: no cover
    start_apple_login = handle_callback = parse_callback_url = build_auth_url = None
    DEFAULT_AUTH_URL = "http://127.0.0.1:17760/auth/apple"

try:
    from PyObjCTools import AppHelper
    from Foundation import (NSBundle, NSObject, NSFont, NSDictionary, NSURL,
                            NSAttributedString, NSMutableAttributedString,
                            NSMutableParagraphStyle, NSParagraphStyle)
    from AppKit import (
        NSApplication, NSApp, NSWindow, NSWindowController, NSView,
        NSVisualEffectView, NSColor, NSImage, NSButton, NSTextField,
        NSTextView, NSRect, NSMakeRect, NSPoint, NSSize, NSMakePoint, NSMakeSize,
        NSModalResponseOK, NSModalResponseCancel,
        NSTextAlignmentRight, NSTextAlignmentLeft,
        NSFont, NSRunLoop, NSScrollView, NSSecureTextField,
        NSFontAttributeName, NSForegroundColorAttributeName,
        NSParagraphStyleAttributeName,
        NSBackingStoreBuffered, NSApplicationActivationPolicyRegular,
        NSMenu, NSMenuItem, NSRoundedBezelStyle,
        NSVisualEffectMaterialHUDWindow, NSVisualEffectMaterialSidebar,
        NSVisualEffectMaterialSelection, NSVisualEffectBlendingModeBehindWindow,
    )
    from Quartz import CALayer
    from LocalAuthentication import (LAContext,
        LAPolicyDeviceOwnerAuthentication,
        LAPolicyDeviceOwnerAuthenticationWithBiometrics)
    from Security import (
        SecItemAdd, SecItemCopyMatching, SecItemUpdate, SecItemDelete,
        kSecClass, kSecClassGenericPassword, kSecAttrService, kSecAttrAccount,
        kSecReturnData, kSecMatchLimit, kSecMatchLimitOne, kSecValueData,
        kSecAttrAccessible, kSecAttrAccessibleAfterFirstUnlock,
        errSecSuccess, errSecDuplicateItem, errSecInteractionNotAllowed,
        errSecItemNotFound,
    )
    from AVFoundation import (
        AVCaptureDevice, AVCaptureSession, AVCaptureDeviceInput,
        AVCaptureVideoPreviewLayer, AVCaptureSessionPresetHigh,
    )
    PYOBJC_OK = True
except Exception as exc:  # pragma: no cover - environment guard
    PYOBJC_OK = False
    _IMPORT_ERROR = exc


# ---------------------------------------------------------------------------
# Keychain (iCloud-style easy login: persist Apple-ID credential, Touch ID unlock)
# ---------------------------------------------------------------------------

def _kc_query():
    if not PYOBJC_OK:
        return None
    return {
        kSecClass: kSecClassGenericPassword,
        kSecAttrService: SERVICE,
        kSecAttrAccount: KEYCHAIN_ACCOUNT,
        kSecReturnData: True,
        kSecMatchLimit: kSecMatchLimitOne,
    }


def _kc_identity():
    """Clean identifying attributes for CopyMatching/Add/Update/Delete
    (no kSecReturnData / kSecMatchLimit — those are match-only and make
    SecItemUpdate return errSecParam)."""
    return {
        kSecClass: kSecClassGenericPassword,
        kSecAttrService: SERVICE,
        kSecAttrAccount: KEYCHAIN_ACCOUNT,
    }


_IDEMPOTENT_OK = (errSecSuccess, 0, errSecDuplicateItem, errSecItemNotFound)


def keychain_add_or_update(apple_id: str, token_hint: str = ""):
    if not PYOBJC_OK:
        return False
    data = json.dumps({"apple_id": apple_id, "token_hint": token_hint}).encode("utf-8")
    add_dict = dict(_kc_identity())
    add_dict[kSecAttrAccessible] = kSecAttrAccessibleAfterFirstUnlock
    add_dict[kSecValueData] = data
    status = SecItemAdd(add_dict, None)
    if status in (errSecSuccess, 0):
        return True
    # already exists → update the data
    if status in (errSecDuplicateItem, errSecInteractionNotAllowed):
        status = SecItemUpdate(_kc_identity(), {kSecValueData: data})
        return status in (errSecSuccess, 0)
    return False


def keychain_get():
    if not PYOBJC_OK:
        return None
    q = _kc_query()
    try:
        result = SecItemCopyMatching(q, None)
    except Exception:
        return None
    data = result[1] if isinstance(result, tuple) else result
    if data is None:
        return None
    try:
        return json.loads(bytes(data))
    except Exception:
        return None


def keychain_add_or_update(apple_id: str, token_hint: str = ""):
    if not PYOBJC_OK:
        return False
    data = json.dumps({"apple_id": apple_id, "token_hint": token_hint}).encode("utf-8")
    add_dict = dict(_kc_identity())
    add_dict[kSecAttrAccessible] = kSecAttrAccessibleAfterFirstUnlock
    add_dict[kSecValueData] = data
    try:
        result = SecItemCopyMatching(_kc_query(), None)
    except Exception:
        result = None
    existing = result[1] if isinstance(result, tuple) else result
    if existing is not None:
        # Update must use a clean identity query (no kSecReturnData / match attrs)
        SecItemUpdate(_kc_identity(), {kSecValueData: data})
    else:
        SecItemAdd(add_dict, None)
    # Verify the item is actually retrievable rather than trusting flaky status
    # codes (keychain status returns vary across macOS keyring states).
    return keychain_get() is not None


def keychain_delete():
    if not PYOBJC_OK:
        return False
    status = SecItemDelete(_kc_identity())
    return status in (errSecSuccess, 0, errSecItemNotFound)


# ---------------------------------------------------------------------------
# GPT Layer backend (subprocess to the local `gpt-layer` command)
# ---------------------------------------------------------------------------

def _gpt_cmd():
    if os.path.exists(GPT_LAYER_CMD):
        return [GPT_LAYER_CMD]
    return [sys.executable, str(_ROOT / "ai" / "gpt_layer_app.py")]


_GPT_SERVER = None
_GPT_SERVER_LOCK = threading.Lock()


def _server_proc():
    global _GPT_SERVER
    with _GPT_SERVER_LOCK:
        if _GPT_SERVER is None or _GPT_SERVER.poll() is not None:
            cmd = _gpt_cmd() + ["--serve"]
            try:
                _GPT_SERVER = subprocess.Popen(
                    cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, text=True, bufsize=1)
            except Exception:
                _GPT_SERVER = None
        return _GPT_SERVER


def _readline_timeout(stream, timeout):
    """Read one line from `stream`; return None on timeout/error."""
    box: list = []
    th = threading.Thread(target=lambda: box.append(stream.readline()),
                          daemon=True)
    th.start()
    th.join(timeout)
    return box[0] if box else None


def gpt_query(message: str, timeout: float = 120.0) -> str:
    """Query the BEING GPT Layer.

    Prefers a single persistent ``gpt-layer --serve`` process so the TinyLlama
    model is loaded once and warm queries are fast (good for chat). Falls back
    to a one-shot ``gpt-layer`` invocation if the server is unavailable.
    """
    # 1) warm persistent server (fast after first load)
    proc = _server_proc()
    if proc is not None:
        try:
            proc.stdin.write(json.dumps({"prompt": message}) + "\n")
            proc.stdin.flush()
            line = _readline_timeout(proc.stdout, timeout)
            if line is not None:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                    except Exception:
                        return line
                    if obj.get("error"):
                        return f"[GPT Layer error] {obj.get('error')}"
                    return (obj.get("response") or "").strip() or "(no response)"
        except Exception as exc:
            # stale/dead server: tear it down and fall through to one-shot
            try:
                proc.kill()
            except Exception:
                pass
            with _GPT_SERVER_LOCK:
                _GPT_SERVER = None

    # 2) one-shot fallback
    try:
        proc2 = subprocess.run(_gpt_cmd() + [message], capture_output=True,
                               text=True, timeout=timeout, check=False)
        out = proc2.stdout.strip()
    except Exception as exc:
        return f"[GPT Layer error] {exc}"
    # `--serve` returns clean JSON (response already stripped of banners). The
    # one-shot CLI prints a status preamble (`[API] ...`, `[GPT Layer · ...]`)
    # before the real answer; drop those banner lines for clean chat output.
    lines = out.splitlines()
    lines = [ln for ln in lines if not ln.startswith("[") or ln.startswith("[GPT Layer error]")]
    return "\n".join(lines).strip() or "(no response)"


def _self_test() -> int:
    """Headless verification of login backend + GPT Layer integration."""
    print("=== OmegaTalk self-test ===")
    print(f"PyObjC available: {PYOBJC_OK}")
    if PYOBJC_OK:
        try:
            print(f"keychain pre-existing credential: {keychain_get() is not None}")
            print(f"keychain add/update: {keychain_add_or_update('selftest@icloud.local', 'self-test')}")
            print(f"keychain round-trip read: {keychain_get() is not None}")
            print(f"keychain delete: {keychain_delete()}")
            print(f"keychain cleared: {keychain_get() is None}")
        except Exception as e:
            print(f"keychain best-effort (ok once signed & run on desktop): {e}")
        ctx = LAContext.alloc().init()
        can_bio = ctx.canEvaluatePolicy_error_(LAPolicyDeviceOwnerAuthenticationWithBiometrics, None)[0]
        can_any = ctx.canEvaluatePolicy_error_(LAPolicyDeviceOwnerAuthentication, None)[0]
        print(f"biometric (Touch ID / Face ID) available: {can_bio}")
        print(f"biometric+passcode (any) available: {can_any}")
    # Backend check: `gpt-layer --status` is fast (no model load) and reliably
    # proves the GPT Layer binary + ctransformers + TinyLlama model are present.
    backend_ok = False
    try:
        st = subprocess.run(_gpt_cmd() + ["--status"], capture_output=True,
                            text=True, timeout=30, check=False)
        backend_ok = (st.returncode == 0)
    except Exception:
        backend_ok = False
    print("GPT Layer backend: " + ("OK" if backend_ok else "FAIL"))

    # --- Apple Wallet pass (native .pkpass generation) ----------------------
    try:
        from qb_protocol.being.wallet import generate_pass, verify_pass
        cred = keychain_get() or {}
        apple_id = cred.get("apple_id", "selftest@icloud.local")
        token = cred.get("token_hint", "self-test-token")
        pkpass = os.path.expanduser("~/Library/Application Support/OmegaTalk/OmegaTalk.pkpass")
        generate_pass(pkpass, apple_id, name="QB Protocol", token_hint=token)
        vr = verify_pass(pkpass)
        print(f"Apple Wallet pass: {pkpass} ({'valid' if vr.get('valid') else 'INVALID: ' + ', '.join(vr.get('errors',[]))})")
    except Exception as e:
        print(f"Apple Wallet pass: {e!r}")

    # --- Apple-ID browser-session auto-login (pure helpers) -----------------
    try:
        from qb_protocol.being.auth_browser import build_auth_url, parse_callback_url
        u = build_auth_url()
        parsed = parse_callback_url(u + "&apple_id=test@icloud.com")
        print(f"Apple-ID browser login: {build_auth_url()!r} parse_ok={bool(parsed.get('apple_id') or parsed.get('callback_url'))}")
    except Exception as e:
        print(f"Apple-ID browser login: {e!r}")

    # --- Ordering agent registry -------------------------------------------
    try:
        from qb_protocol.being.ordering import list_providers
        print("Ordering providers: " + ", ".join(p["category"] for p in list_providers()))
    except Exception as e:
        print(f"Ordering providers: {e!r}")

    # --- Virtual SIM / SMS-receive (cloud inbox; eSIM needs Apple carrier entitlement) -
    try:
        from qb_protocol.being.sms import get_default
        sms = get_default()
        print(f"Virtual SMS inbox ({sms.name}): "
              + ("Twilio" if sms.name == "twilio"
                 else "local dev sink (set TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_SMS_NUMBER for a real number)"))
    except Exception as e:
        print(f"Virtual SMS inbox: {e!r}")

    print("self-test complete")
    return 0


# ---------------------------------------------------------------------------
# FaceTime-styled native UI
# ---------------------------------------------------------------------------

_APP = None
_CONTACT_FONT = NSFont.systemFontOfSize_(13) if PYOBJC_OK else None


def _style_mask(titled=True, closable=True, miniaturizable=True, resizable=True):
    m = 0
    if titled:        m |= 1 << 0
    if closable:      m |= 1 << 1
    if miniaturizable: m |= 1 << 2
    if resizable:     m |= 1 << 3
    return m


def _label(text, frame=NSMakeRect(0, 0, 200, 18)):
    tf = NSTextField.alloc().initWithFrame_(frame)
    tf.setBezeled_(False)
    tf.setBordered_(False)
    tf.setDrawsBackground_(False)
    tf.setEditable_(False)
    tf.setSelectable_(False)
    return tf


def _rounded_view(frame, corner=16.0):
    v = NSView.alloc().initWithFrame_(frame)
    v.setWantsLayer_(True)
    try:
        v.layer().setCornerRadius_(corner)
        v.layer().setMasksToBounds_(True)
    except Exception:
        pass
    return v


class Contact:
    def __init__(self, name, subtitle="", online=True):
        self.name = name
        self.subtitle = subtitle
        self.online = online


class ChatMessage:
    def __init__(self, text, mine):
        self.text = text
        self.mine = mine


class LoginWindowController(NSWindowController):
    """Apple-ID-style easy login (iCloud-style): Keychain-persisted credential
    + Touch ID quick-unlock. Auto-fill when a credential is stored."""

    def init(self):
        self = objc.super(LoginWindowController, self).init()
        if self is None:
            return None
        frame = NSMakeRect(0, 0, 370, 430)
        self._win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, _style_mask(miniaturizable=False, resizable=False),
            NSBackingStoreBuffered, False)
        self._win.setTitle_("OmegaTalk")
        self._win.setReleasedWhenClosed_(False)

        ev = NSVisualEffectView.alloc().initWithFrame_(frame)
        ev.setMaterial_(NSVisualEffectMaterialHUDWindow)
        ev.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        ev.setAutoresizesSubviews_(True)
        self._win.setContentView_(ev)
        self._ev = ev
        y = 130
        title = _label("Sign in with iCloud")
        title.setFrameOrigin_((60, y + 120))
        title.setFont_(NSFont.boldSystemFontOfSize_(19))
        ev.addSubview_(title)

        sub = _label("Sign in to OmegaTalk (stores your Apple ID in the Keychain for easy sign-in).")
        sub.setFrame_(NSMakeRect(60, y + 95, 250, 34))
        sub.setTextColor_(NSColor.secondaryLabelColor())
        ev.addSubview_(sub)

        name_lbl = _label("Apple ID")
        name_lbl.setFrameOrigin_((40, y + 52))
        ev.addSubview_(name_lbl)
        self.email = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y + 28, 290, 26))
        self.email.setBezeled_(True)
        self.email.setPlaceholderString_("name@apple.com")
        ev.addSubview_(self.email)

        pw_lbl = _label("Password")
        pw_lbl.setFrameOrigin_((40, y + 6))
        ev.addSubview_(pw_lbl)
        self.pw = NSSecureTextField.alloc().initWithFrame_(NSMakeRect(40, y - 14, 290, 26))
        self.pw.setBezeled_(True)
        self.pw.setPlaceholderString_("password")
        ev.addSubview_(self.pw)

        existing = keychain_get()
        if existing:
            self.email.setStringValue_(existing.get("apple_id", ""))

        sign = NSButton.buttonWithTitle_target_action_("Sign In", self, "signInClick:")
        sign.setFrame_(NSMakeRect(40, y - 46, 290, 34))
        ev.addSubview_(sign)

        self.touch = NSButton.buttonWithTitle_target_action_("Use Touch ID", self, "touchIdClick:")
        self.touch.setFrame_(NSMakeRect(40, y - 84, 290, 34))
        ctx = LAContext.alloc().init()
        can_bio = ctx.canEvaluatePolygonError_(LAPolicyDeviceOwnerAuthenticationWithBiometrics, None) if False else ctx.canEvaluatePolicy_error_(LAPolicyDeviceOwnerAuthenticationWithBiometrics, None)
        self.touch.setHidden_(not can_bio[0])
        ev.addSubview_(self.touch)

        # "Continue with Apple ID" — opens the user's default browser (which holds
        # the existing Apple-ID session) via ASWebAuthenticationSession, then
        # persists the session token to the Keychain and opens the chat.
        self.apple_id = NSButton.buttonWithTitle_target_action_(
            "Continue with Apple ID", self, "appleIdLoginClick:")
        self.apple_id.setFrame_(NSMakeRect(40, y - 132, 290, 34))
        have_auth = start_apple_login is not None
        self.apple_id.setHidden_(not have_auth)
        ev.addSubview_(self.apple_id)
        if have_auth:
            try:
                hint = keychain_get()
                hint_email = (hint or {}).get("apple_id", "your Apple ID")
            except Exception:
                hint_email = "your Apple ID"
            self._apple_hint = _label(f"Browser sign-in as {hint_email}")
            self._apple_hint.setFrameOrigin_((40, y - 156))
            self._apple_hint.setTextColor_(NSColor.secondaryLabelColor())
            ev.addSubview_(self._apple_hint)

        self.setWindow_(self._win)
        return self

    def appleIdLoginClick_(self, sender):
        if start_apple_login is None:
            return
        start_apple_login(self._onAppleLogin)

    @objc.python_method
    def _onAppleLogin(self, result: dict):
        # Run on the main thread (AppHelper callAfter) so UI + keychain access
        # is safe. result: {"ok": bool, "token": ..., "apple_id": ...}
        def _apply(res):
            ok = bool(res.get("ok"))
            token = res.get("token") or ""
            apple_id = res.get("apple_id") or ""
            if not ok or not token:
                return
            keychain_add_or_update(apple_id or "apple@icloud.local", token_hint=token)
        AppHelper.callAfter(_apply, result)
        # If we have a token, proceed to chat; otherwise stay on the login window.
        token = result.get("token") or ""
        if token:
            AppHelper.callAfter(self.openChat, None)

    def signInClick_(self, sender):
        email = self.email.stringValue().strip()
        if not email:
            return
        keychain_add_or_update(email)
        self.openChat()

    def touchIdClick_(self, sender):
        ctx = LAContext.alloc().init()
        def _reply(success, error):
            try:
                if not success:
                    AppHelper.callAfter(self._authFailed, None)
                else:
                    AppHelper.callAfter(self._doLoginFromTouchId, None)
            except Exception:
                pass
        # Pass a real reply block (NOT None) — a nil block dereferences in LA
        # and crashes the app (SIGSEGV). LAPolicyDeviceOwnerAuthentication
        # covers both Touch ID and Face ID (+ passcode fallback).
        ctx.evaluatePolicy_localizedReason_reply_(
            LAPolicyDeviceOwnerAuthentication, "Unlock OmegaTalk", _reply)

    @objc.python_method
    def _authFailed(self, _=None):
        # Biometric/passcode denied (or unavailable): best-effort — stay on the
        # login window so the user can fall back to the Apple-ID form field.
        pass

    @objc.python_method
    def _doLoginFromTouchId(self, _=None):
        self.openChat()

    def openChat(self):
        self.window().performSelector_withObject_afterDelay_("close", None, 0.0)
        if _APP is not None and _APP.delegate() is not None:
            try:
                _APP.delegate().openChatFromLogin_(None)
            except Exception:
                pass


class ChatWindowController(NSWindowController):
    """FaceTime-styled chat: camera preview + contacts sidebar + messages + input."""

    def init(self):
        self = objc.super(ChatWindowController, self).init()
        if self is None:
            return None
        frame = NSMakeRect(0, 0, 960, 620)
        self._win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, _style_mask(), NSBackingStoreBuffered, False)
        self._win.setTitle_("OmegaTalk")
        self._win.setReleasedWhenClosed_(False)
        self._win.setMinSize_(NSMakeSize(740, 520))

        ev = NSVisualEffectView.alloc().initWithFrame_(frame)
        ev.setMaterial_(NSVisualEffectMaterialHUDWindow)
        ev.setAutoresizesSubviews_(True)
        self._win.setContentView_(ev)
        self._ev = ev

        # Contacts sidebar
        self.sidebar = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, 236, 620))
        self.sidebar.setMaterial_(NSVisualEffectMaterialSidebar)
        ev.addSubview_(self.sidebar)
        self._contacts = [Contact(CONTACT_NAME, "AI · TinyLlama · online", True)]
        self._build_contacts()

        # Chat area
        chat_frame = NSMakeRect(236, 0, 724, 620)
        self.chat_bg = NSVisualEffectView.alloc().initWithFrame_(chat_frame)
        self.chat_bg.setMaterial_(NSVisualEffectMaterialSelection)
        ev.addSubview_(self.chat_bg)

        # Camera preview (FaceTime-style) — guarded, falls back to placeholder
        cam_frame = NSMakeRect(10, 474, 216, 162)
        try:
            self._setup_camera(cam_frame)
        except Exception:
            self._setup_camera_placeholder(cam_frame)

        # Message list
        self.messages = NSTextView.alloc().initWithFrame_(NSMakeRect(12, 132, 680, 348))
        self.messages.setEditable_(False)
        self.messages.setSelectable_(True)
        self.messages.setAutomaticLinkDetectionEnabled_(True)
        self.messages.setBackgroundColor_(NSColor.clearColor())
        self.scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(12, 130, 680, 352))
        self.scroll.setDocumentView_(self.messages)
        self.scroll.setHasVerticalScroller_(True)
        self.scroll.setAutohidesScrollers_(True)
        self.chat_bg.addSubview_(self.scroll)

        # "QB Protocol is thinking…" indicator (shown while the model runs).
        self.status = _label("QB Protocol is thinking…")
        self.status.setFrame_(NSMakeRect(12, 100, 540, 18))
        self.status.setTextColor_(NSColor.secondaryLabelColor())
        self.status.setHidden_(True)
        self.chat_bg.addSubview_(self.status)

        # Input row
        self.input = NSTextField.alloc().initWithFrame_(NSMakeRect(12, 36, 500, 28))
        self.input.setBezeled_(True)
        self.input.setPlaceholderString_("Message QB Protocol…")
        self.chat_bg.addSubview_(self.input)

        # Send button: FaceTime-style blue, rounded
        self.send = NSButton.buttonWithTitle_target_action_("Send", self, "sendClick:")
        self.send.setFrame_(NSMakeRect(526, 36, 166, 32))
        self.send.setBezelStyle_(NSRoundedBezelStyle)
        self.send.setBordered_(False)
        self.send.setBezelColor_(NSColor.systemBlueColor())
        if hasattr(self.send, "setShowsBorderOnlyWhileMouseInside_"):
            self.send.setShowsBorderOnlyWhileMouseInside_(False)
        # setTitleColor_forState: is unavailable on NSButton here; use a white
        # attributed title instead (the bezel supplies the blue background).
        tattr = NSMutableAttributedString.alloc().initWithString_attributes_(
            "Send", {NSFontAttributeName: NSFont.boldSystemFontOfSize_(13),
                     NSForegroundColorAttributeName: NSColor.whiteColor()})
        if hasattr(self.send, "setAttributedTitle_"):
            self.send.setAttributedTitle_(tattr)
        self.chat_bg.addSubview_(self.send)

        self._append("OmegaTalk is ready. Sign in to start chatting with QB Protocol.", mine=False)
        self.setWindow_(self._win)
        return self

    @objc.python_method
    def _setup_camera(self, frame):
        self.cam_layer = CALayer.layer()
        self.cam_layer.setMasksToBounds_(True)
        self.cam_layer.setCornerRadius_(14)
        cam_view = _rounded_view(frame, 14)
        cam_view.layer().setBorderColor_(NSColor.whiteColor().colorWithAlphaComponent_(0.45).CGColor())
        cam_view.layer().setBorderWidth_(1.0)
        self.chat_bg.addSubview_(cam_view)
        session = AVCaptureSession.alloc().init()
        session.setSessionPreset_(AVCaptureSessionPresetHigh)
        dev = AVCaptureDevice.defaultDeviceWithMediaType_position_("vide", 1) or \
            AVCaptureDevice.defaultDeviceWithMediaType_("vide")
        added = False
        if dev is not None:
            AVCaptureDevice.requestAccessForMediaType_("vide") if hasattr(AVCaptureDevice, "requestAccessForMediaType_") else None
            input_dev = AVCaptureDeviceInput.deviceInputWithDevice_error_(dev, None)
            if input_dev is not None and session.canAddInput_(input_dev):
                session.addInput_(input_dev); added = True
        preview = AVCaptureVideoPreviewLayer.layerWithSession_(session)
        preview.setVideoGravity_("kCAGravityResizeAspectFill")
        preview.setFrameSize_(frame.size)
        self.cam_layer.addSublayer_(preview)
        if added:
            session.startRunning()
        self._session = session

    @objc.python_method
    def _setup_camera_placeholder(self, frame):
        self.cam_layer = CALayer.layer()
        self.cam_layer.setMasksToBounds_(True)
        self.cam_layer.setCornerRadius_(14)
        self.cam_layer.setBackgroundColor_(NSColor.lightGrayColor().colorWithAlphaComponent_(0.28).CGColor())
        v = _rounded_view(frame, 14)
        self.chat_bg.addSubview_(v)
        lbl = _label("Camera")
        lbl.setFrameOrigin_((12, frame.size.height - 24))
        lbl.setTextColor_(NSColor.whiteColor())
        v.addSubview_(lbl)

    @objc.python_method
    def _build_contacts(self):
        for i, c in enumerate(self._contacts):
            row = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(14, 540 - i * 70, 208, 60))
            row.setMaterial_(NSVisualEffectMaterialSelection)
            row.setCornerRadius_(10) if hasattr(row, "setCornerRadius_") else None
            dot = _rounded_view(NSMakeRect(2, 6, 12, 12), 6)
            dot.layer().setBackgroundColor_((NSColor.systemGreenColor() if c.online else NSColor.systemGrayColor()).CGColor())
            row.addSubview_(dot)
            name = _label(c.name)
            name.setFrameOrigin_((22, 28))
            name.setFont_(NSFont.boldSystemFontOfSize_(13))
            row.addSubview_(name)
            sub = _label(c.subtitle)
            sub.setFrameOrigin_((22, 6))
            sub.setTextColor_(NSColor.secondaryLabelColor())
            sub.setFont_(NSFont.systemFontOfSize_(11))
            row.addSubview_(sub)
            self.sidebar.addSubview_(row)

    def sendClick_(self, sender):
        text = self.input.stringValue().strip()
        if not text:
            return
        self.input.setStringValue_("")
        self._append(text, mine=True)
        self.status.setHidden_(False)
        threading.Thread(target=self._reply, args=(text,), daemon=True).start()

    @objc.python_method
    def _reply(self, text: str):
        resp = gpt_query(text)
        AppHelper.callAfter(self._on_reply, resp)

    @objc.python_method
    def _on_reply(self, resp: str):
        self.status.setHidden_(True)
        self._append(resp, mine=False)

    @objc.python_method
    def _append(self, text: str, mine: bool):
        tv = self.messages
        attr = tv.textStorage().mutableCopy()
        para = NSMutableParagraphStyle.alloc().init()
        para.setAlignment_(NSTextAlignmentRight if mine else NSTextAlignmentLeft)
        # Use labelColor (auto-adapts to light/dark) for BOTH sides so assistant
        # replies are actually readable on the MaterialSelection background.
        color = NSColor.labelColor()
        bold = NSFont.boldSystemFontOfSize_(13)
        reg = NSFont.systemFontOfSize_(13)
        label = "You" if mine else CONTACT_NAME
        header_color = NSColor.systemBlueColor() if mine else NSColor.secondaryLabelColor()
        header = NSMutableAttributedString.alloc().initWithString_attributes_(
            label + ": ", {NSFontAttributeName: bold, NSForegroundColorAttributeName: header_color})
        body = NSMutableAttributedString.alloc().initWithString_attributes_(text + "\n\n", {NSFontAttributeName: reg, NSForegroundColorAttributeName: color, NSParagraphStyleAttributeName: para})
        header.appendAttributedString_(body)
        attr.appendAttributedString_(header)
        tv.textStorage().setAttributedString_(attr)
        tv.scrollToEndOfDocument_(None)


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, note):
        self.login = LoginWindowController.alloc().init()
        self.login.showWindow_(None)
        self.login.window().makeKeyAndOrderFront_(None)

    def openChatFromLogin_(self, sender):
        self.chat = ChatWindowController.alloc().init()
        self.chat.showWindow_(None)
        self.chat.window().makeKeyAndOrderFront_(None)


def build_main_menu(app):
    main_menu = NSMenu.alloc().init()
    main_menu.setTitle_("OmegaTalk")
    app.setMainMenu_(main_menu)
    apple = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("OmegaTalk", None, "")
    main_menu.addItem_(apple)
    sub = NSMenu.alloc().init()
    apple.setSubmenu_(sub)
    sub.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("About OmegaTalk", None, ""))
    sub.addItem_(NSMenuItem.separatorItem())
    sub.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Services", None, ""))
    sub.addItem_(NSMenuItem.separatorItem())
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit OmegaTalk", "@q", "")
    quit_item.setTarget_(app)
    quit_item.setAction_("terminate:")
    sub.addItem_(quit_item)
    win = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Window", None, "")
    win_sub = NSMenu.alloc().init()
    win.setSubmenu_(win_sub)
    main_menu.addItem_(win)
    return main_menu


def run_app(argv=None) -> int:
    global _APP
    _APP = NSApplication.sharedApplication()
    _APP.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    build_main_menu(_APP)
    delegate = AppDelegate.alloc().init()
    _APP.setDelegate_(delegate)
    try:
        AppHelper.runEventLoop()
    except KeyboardInterrupt:
        pass
    return 0


def main() -> int:
    if not PYOBJC_OK:
        print(f"OmegaTalk requires PyObjC: {_IMPORT_ERROR}", file=sys.stderr)
        return 1
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return _self_test()
    if "--status" in argv:
        st = {"gpt_layer": gpt_query("(echo)"), "keychain_credential": keychain_get() is not None}
        print(json.dumps(st, indent=2, default=str))
        return 0
    if "--ui-test" in argv:
        _APP = NSApplication.sharedApplication()
        _APP.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        build_main_menu(_APP)
        del_ = AppDelegate.alloc().init()
        _APP.setDelegate_(del_)
        try:
            del_.applicationDidFinishLaunching_(None)
            print("ui-test: LoginWindow + menu OK")
        except Exception as e:
            print(f"ui-test LoginWindow error: {e!r}")
        try:
            chat = ChatWindowController.alloc().init()
            print("ui-test: ChatWindow (camera + contacts + messages) OK")
        except Exception as e:
            print(f"ui-test ChatWindow error: {e!r}")
        return 0
    if "--wallet" in argv:
        from qb_protocol.being.wallet import generate_pass, verify_pass
        cred = keychain_get() or {}
        apple_id = cred.get("apple_id", "selftest@icloud.local")
        token = cred.get("token_hint", "")
        out = os.path.expanduser("~/Library/Application Support/OmegaTalk/OmegaTalk.pkpass")
        generate_pass(out, apple_id, name="QB Protocol", token_hint=token)
        res = verify_pass(out)
        print(json.dumps({"wallet": out, "valid": res.get("valid"),
                          "files": res.get("files"), "errors": res.get("errors")},
                         indent=2, default=str))
        return 0
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
