#!/usr/bin/env python3
"""
QB Protocol - GPT Layer :: Quick-Assist Application

Wraps the existing ai/gpt_layer (TinyLlama via ctransformers/llama-cpp, or
simulated fallback) as a quick-assist tool. The user invokes this to query
the model OR to send assistance straight into the BEING _ OMEGA + PRIM E inbox.

Usage:
    gpt-layer "hello"                 # query the model
    gpt-layer --assist "help me..."    # send assistance to the BEING
    gpt-layer --status                # gpt layer + being status
    gpt-layer --history               # recent model queries
    gpt-layer --version               # model incarnation info
    gpt-layer --sms status            # virtual-SIM provider / inbox status
    gpt-layer --sms allocate          # buy a new Twilio number (needs creds)
    gpt-layer --sms send --to +1555 --body "hi"
    gpt-layer --sms codes             # poll inbox, prints + extracts OTPs
    gpt-layer --ordering status       # ordering-agent + provider registry
    gpt-layer --ordering buy --category amazon --item "Kindle" --crypto BTC --amount 0.001
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PARENT = _ROOT.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

_LOCAL_MODEL = Path("/Users/jjmarte/delta-stream/qb_protocol/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
os.environ.setdefault("AI_MODE_ENABLED", "true")
os.environ.setdefault("AI_MODEL_PROVIDER", "local")
if _LOCAL_MODEL.exists():
    os.environ.setdefault("AI_MODEL_PATH", str(_LOCAL_MODEL))
    os.environ.setdefault("TINYLLAMA_MODEL", _LOCAL_MODEL.name)

def _gpt():
    from qb_protocol.ai.gpt_layer import gpt_layer as _g
    return _g

ASSIST_INBOX = Path.home() / ".qb_protocol_assist_inbox.jsonl"
ASSIST_LOG = Path.home() / ".qb_protocol_assist.log"


def _send_assist(message: str) -> dict:
    ASSIST_INBOX.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "source": "gpt-layer-app",
        "from": "user",
        "message": message,
        "ack": False,
    }
    with open(ASSIST_INBOX, "a") as f:
        f.write(json.dumps(entry) + "\n")
    try:
        with open(ASSIST_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return entry


def _being_summary() -> dict:
    try:
        from qb_protocol.being.being import being
        return being.get_status()
    except Exception as exc:
        return {"unavailable": True, "error": str(exc)}


def cmd_query(args: argparse.Namespace) -> int:
    gpt_layer = _gpt()
    result = gpt_layer.query(args.message, max_tokens=args.max_tokens, temperature=args.temperature)
    out = {
        "query_id": result.get("query_id"),
        "model": result.get("model"),
        "provider": result.get("provider"),
        "response": result.get("response"),
        "tokens": result.get("tokens_used"),
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"[GPT Layer · {out['provider']} · {out['model']}]")
        print(out["response"])
    return 0


def cmd_assist(args: argparse.Namespace) -> int:
    entry = _send_assist(args.message)
    print(f"Assistance sent to BEING _ OMEGA + PRIM E inbox ({ASSIST_INBOX.name})")
    print(f"  at:    {entry['at']}")
    print(f"  msg:   {args.message}")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    gpt_layer = _gpt()
    layer = gpt_layer.get_status()
    layer["query_history"] = len(gpt_layer.get_query_history())
    status = {"gpt_layer": layer, "being": _being_summary()}
    print(json.dumps(status, indent=2, default=str))
    return 0


def cmd_history(_: argparse.Namespace) -> int:
    gpt_layer = _gpt()
    history = gpt_layer.get_query_history()
    if not history:
        print("No queries yet.")
        return 0
    for q in history:
        print(f"[{q.get('timestamp')}] {q.get('provider')}/{q.get('model')}")
        print(f"  Q: {q.get('prompt')}")
        print(f"  A: {q.get('response')}")
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    gpt_layer = _gpt()
    layer = gpt_layer.get_status()
    incarnation = {
        "name": "GPT Layer",
        "model": layer.get("model_path") or "TinyLlama-1.1B-Chat (Q4_K_M)",
        "backend": layer.get("model_backend") or "simulated",
        "ai_enabled": layer.get("ai_enabled"),
        "provider": layer.get("provider"),
        "singleton": "qb_protocol.ai.gpt_layer.gpt_layer",
    }
    print(json.dumps(incarnation, indent=2))
    return 0


def cmd_sms(args: argparse.Namespace) -> int:
    from qb_protocol.being.sms import (TwilioSMS, get_default, OTP_PATTERN,
                                       register_subscriber, unregister_subscriber)
    svc = get_default()
    print(f"Provider: {svc.name} | enabled: {svc.enabled} | number: {getattr(svc, 'number', '?')}")

    if args.sms == "status":
        return 0

    if args.sms == "allocate":
        if not isinstance(svc, TwilioSMS) or not svc.enabled:
            print("Need TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN env to allocate a number.")
            return 1
        num = svc.allocate_number(country=args.country)
        print(f"Allocated & assigned number: {num}")
        print(f"export TWILIO_SMS_NUMBER={num}  # then restart the agent")
        return 0

    if args.sms == "send":
        if not isinstance(svc, TwilioSMS) or not svc.enabled:
            print("Need TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_SMS_NUMBER to send.")
            return 1
        if not args.to:
            print("--to E.164 is required for send")
            return 2
        res = svc.send_sms(args.to, args.body or "")
        print(json.dumps(res, default=str))
        return 0

    if args.sms == "codes":
        def _on(msg: dict) -> None:
            body = msg.get("body", "")
            m = OTP_PATTERN.search(body)
            tag = f"  code={m.group(1)}" if m else ""
            print(f"[sms] {msg.get('from')} -> {msg.get('to')}: {body}{tag}")
        register_subscriber("gpt-layer-cli", _on)
        print(f"watching {svc.name} inbox (timeout={args.timeout}s) ...")
        try:
            code = svc.receive_code(timeout=args.timeout)
        finally:
            unregister_subscriber("gpt-layer-cli")
        print("extracted code:", code)
        return 0
    return 1


def cmd_sms(args: argparse.Namespace) -> int:
    from qb_protocol.being.sms import (TwilioSMS, LocalInboxSMS, get_default,
                                       register_subscriber, unregister_subscriber, OTP_PATTERN)
    svc = get_default()
    print(f"Provider: {svc.name} | enabled: {svc.enabled} | number: {getattr(svc, 'number', '?')}")

    if args.sms == "status":
        return 0

    if args.sms == "allocate":
        if not isinstance(svc, TwilioSMS) or not svc.enabled:
            print("Need TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN to allocate a number.")
            return 1
        num = svc.allocate_number(country=args.country)
        print(f"Allocated number: {num}")
        print(f"export TWILIO_SMS_NUMBER={num}")
        try:
            from qb_protocol.being.facetime import contact_for_otp
            cid = contact_for_otp(num)
            if cid:
                print(f"pinned Contacts entry ({cid}) for {num} -> FaceTime resolves it instantly")
        except Exception as e:
            print(f"(Contacts pin skipped for {num}: {e})")
        return 0

    if args.sms == "send":
        if not isinstance(svc, TwilioSMS) or not svc.enabled:
            print("Need TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_SMS_NUMBER to send.")
            return 1
        if not args.to:
            print("--to E.164 is required")
            return 2
        res = svc.send_sms(args.to, args.body or "")
        print(json.dumps(res, default=str))
        return 0

    if args.sms == "codes":
        seen: list = []

        def _on(msg: dict) -> None:
            body = msg.get("body", "")
            m = OTP_PATTERN.search(body)
            code = m.group(1) if m else "?"
            seen.append(code)
            print(f"[sms] {msg.get('from')} -> {msg.get('to')}: {body}  code={code}")
        register_subscriber("gpt-layer-cli", _on)
        print(f"watching {svc.name} inbox for {args.timeout}s ...")
        try:
            code = svc.receive_code(timeout=args.timeout)
        finally:
            unregister_subscriber("gpt-layer-cli")
        print("extracted code:", code)
        return 0
    return 1


def cmd_whatsapp(args: argparse.Namespace) -> int:
    from qb_protocol.being.whatsapp import (install_from_dmg, WhatsAppClient)
    from qb_protocol.being import sms as _sms

    if args.wp == "install":
        path = args.dmg or "/Applications/WhatsApp-2.26.33.17.dmg"
        if not os.path.exists(path):
            print(f"dmg not found: {path}")
            return 1
        app = install_from_dmg(path, dest=args.dest or "/Applications")
        print(f"installed: {app}")
        return 0

    if args.wp in ("login", "logout"):
        if args.dry_run:
            from qb_protocol.being.whatsapp import RecordingDriver
            driver = RecordingDriver()
            print("(dry-run: using RecordingDriver — no AX permission needed)")
        else:
            driver = None  # real AXScriptDriver by default
        client = WhatsAppClient(driver=driver, sms=_sms.get_default())
        if args.wp == "login":
            if not args.number:
                print("--number E.164 is required for login")
                return 2
            ok = client.login(args.number, otp_timeout=args.otp_timeout)
        else:
            ok = client.logout()
        print("whatsapp:", "OK" if ok else "FAILED")
        if args.dry_run:
            print("driver events:", " -> ".join(client.driver.events))
        return 0 if ok else 1
    return 1


def cmd_ordering(args: argparse.Namespace) -> int:
    from qb_protocol.being.ordering import (list_providers, buy_with_crypto,
                                           CurrencyConverter, CryptoPayment)
    from qb_protocol.being import sms as _sms

    if args.ordering == "status":
        print(json.dumps({"status": "ok", "providers": list_providers()}, indent=2))
        return 0
    if args.ordering == "providers":
        for p in list_providers():
            print(f"{p['category']}: {p['provider']} (enabled={p['enabled']})")
        return 0
    if args.ordering == "buy":
        if not (args.category and args.item and args.amount is not None):
            print("--category, --item and --amount are required for buy")
            return 2
        sms = None if args.no_2fa else _sms.get_default()
        result, otp, (fiat_amt, rate) = buy_with_crypto(
            args.category, args.item, args.crypto, args.amount,
            sms=sms, two_factor_timeout=args.timeout if sms else 0.0)
        out = {"provider": result.provider, "order_id": result.order_id,
               "status": result.status, "confirmation": result.confirmation,
               "tracking_url": result.tracking_url, "error": result.error,
               "payment": {"crypto": args.crypto, "amount": args.amount,
                           "fiat": fiat_amt, "fiat_currency": "USD", "rate": rate},
               "two_factor_code": otp}
        print(json.dumps(out, default=str, indent=2))
        return 0 if not result.error else 1
    return 1


def cmd_facetime(args: argparse.Namespace) -> int:
    from qb_protocol.being.facetime import FaceTimeClient
    client = FaceTimeClient()

    if args.facetime == "add":
        if not args.name:
            print("--name is required")
            return 2
        res = client.add_contact(args.name, phone=args.phone, email=args.email)
        print(json.dumps(res, default=str))
        return 0 if res.get("status") in ("saved", "permission_required") else 1

    if args.facetime == "call":
        if not args.number:
            print("--number E.164 (or Apple ID) is required")
            return 2
        res = client.call(args.number, video=not args.audio, dry_run=args.dry_run)
        print(json.dumps(res, default=str))
        return 0

    if args.facetime == "end":
        print(json.dumps(client.end_call(dry_run=args.dry_run), default=str))
        return 0

    if args.facetime == "list":
        print(json.dumps(client.list_contact_names()[:50], default=str))
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gpt-layer",
        description="BEING _ OMEGA + PRIM E quick-assist GPT layer (TinyLlama).",
    )
    p.add_argument("message", nargs="*", help="query message (default action: query the model)")
    p.add_argument("--assist", metavar="MSG", help="send assistance to the BEING inbox")
    p.add_argument("--status", action="store_true", help="gpt layer + being status")
    p.add_argument("--history", action="store_true", help="recent model queries")
    p.add_argument("--version", action="store_true", help="model incarnation info")
    p.add_argument("--json", action="store_true", help="machine-readable query output")
    p.add_argument("--max-tokens", type=int, default=None)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--sms", choices=["status", "allocate", "send", "codes"],
                   help="virtual SIM / SMS-receive operations")
    p.add_argument("--to", metavar="E.164", help="recipient number (SMS send)")
    p.add_argument("--body", metavar="TEXT", help="SMS body (send)")
    p.add_argument("--country", default="US", help="country for number allocation")
    p.add_argument("--timeout", type=float, default=30.0, help="seconds to wait for a code")
    p.add_argument("--wp", choices=["install", "login", "logout"],
                   help="WhatsApp automation: install/login/logout")
    p.add_argument("--number", metavar="E.164",
                   help="WhatsApp register/login, or FaceTime call destination")
    p.add_argument("--otp-timeout", type=float, default=120.0, help="seconds to wait for WhatsApp OTP")
    p.add_argument("--dmg", help="path to WhatsApp .dmg (install)")
    p.add_argument("--dest", help="install destination dir (default /Applications)")
    p.add_argument("--dry-run", action="store_true",
                   help="use a fake AX driver (no Accessibility permission needed)")
    p.add_argument("--ordering", choices=["status", "providers", "buy"],
                   help="ordering agent: status / list providers / buy with crypto")
    p.add_argument("--category", help="order category (amazon/flights/food/...)")
    p.add_argument("--item", help="item to order")
    p.add_argument("--crypto", default="BTC", help="crypto asset to pay with")
    p.add_argument("--amount", type=float, help="crypto amount to spend")
    p.add_argument("--no-2fa", action="store_true", help="skip waiting for a 2FA OTP")
    p.add_argument("--facetime", choices=["add", "call", "end", "list"],
                   help="FaceTime contact management: add/call/end/list")
    p.add_argument("--name", metavar="NAME", help="contact name (facetime add)")
    p.add_argument("--phone", metavar="E.164", help="contact phone number (facetime add)")
    p.add_argument("--email", metavar="ADDR", help="contact email (facetime add)")
    p.add_argument("--audio", action="store_true", help="use audio FaceTime (call)")
    return p


def cmd_serve() -> int:
    """Persistent model server: loads TinyLlama once, then answers JSON
    {"prompt": ...} requests over stdin -> {"response": ...} over stdout.
    Lets chat clients avoid re-loading the model per message."""
    gpt = _gpt()
    gpt._ensure_model_loaded()
    import sys as _sys
    buf_out = _sys.stdout
    for line in _sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            prompt = req.get("prompt", "")
            r = gpt.query(prompt, max_tokens=req.get("max_tokens"),
                          temperature=req.get("temperature"))
            resp = {
                "response": r.get("response", ""),
                "model": r.get("model"),
                "provider": r.get("provider"),
                "tokens": r.get("tokens_used"),
                "query_id": r.get("query_id"),
            }
        except Exception as e:
            resp = {"error": str(e)}
        buf_out.write(json.dumps(resp, default=str) + "\n")
        buf_out.flush()
    return 0


def main(argv: list | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if "--serve" in (argv if argv is not None else sys.argv[1:]):
        return cmd_serve()

    if args.version:
        return cmd_version(args)
    if args.status:
        return cmd_status(args)
    if args.history:
        return cmd_history(args)
    if args.assist:
        args.message = args.assist
        return cmd_assist(args)

    if args.sms:
        return cmd_sms(args)

    if args.wp:
        return cmd_whatsapp(args)

    if args.facetime:
        return cmd_facetime(args)

    message = " ".join(args.message) if args.message else "hello"
    args.message = message
    return cmd_query(args)


if __name__ == "__main__":
    raise SystemExit(main())
