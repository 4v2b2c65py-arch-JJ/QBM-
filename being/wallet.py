#!/usr/bin/env python3
"""
BEING _ OMEGA + PRIM E — native Apple Wallet pass generation.

Builds a standards-compliant ``.pkpass`` bundle (a ZIP archive containing
``pass.json``, the required images, ``manifest.json`` with SHA-1 hashes, and a
PKCS#7 detached signature over the manifest) for an OmegaTalk/QB Protocol
session credential. This is the "details already there" native Apple Wallet card.

Implementation notes (per Apple's *Building a Pass* and the PKPASS spec):
  * A ``.pkpass`` is a ZIP archive; files live at the root (no wrapper folder).
  * ``manifest.json`` maps every file's relative path -> its SHA-1 hex.
  * ``signature`` is a PKCS#7 detached signature over ``manifest.json``, signed
    with the Apple-issued PassKit "Pass Type ID" private key and carrying the
    WWDR intermediate for chain building.
  * Icons are generated as solid-color PNGs with no third-party deps (Pillow
    is not required).

Signing requires Apple-developer artifacts:
  * a Pass Type ID certificate (private key + .p12/.pem),
  * the Apple WWDR intermediate certificate.

When those are *not* provided, the generator falls back to a throwaway
self-signed certificate so the bundle structure is still produced and can be
validated. Such a pass is NOT accepted by Apple Wallet on device (it will report
"signed by an untrusted issuer") — it is intended for pipeline/structure tests
and for environments where provisioning an Apple cert is out of scope. Provide
real certs via arguments / the documented env vars to produce shippable passes.

Env overrides (all optional):
  QB_PASS_TYPE_ID   pass.com.being.omega.talk
  QB_TEAM_ID        Apple developer team identifier
  QB_AUTH_URL       web service URL for push updates
  QB_SIGNER_CERT    path to Pass Type ID .pem
  QB_SIGNER_KEY     path to Pass Type ID private key .pem
  QB_WWDR_CERT      path to Apple WWDR intermediate .pem
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_PASS_TYPE = "pass.com.being.omega.talk"
DEFAULT_TEAM = "0000000000"  # Apple requires 10-char team id
APPLE_BLUE = (0, 122, 255)  # systemBlue on macOS


def _sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _png(width: int, height: int, rgb: Tuple[int, int, int]) -> bytes:
    """Encode a solid-color PNG (no dependencies)."""
    if isinstance(rgb, str) and rgb.startswith("#"):
        rgb = tuple(int(rgb[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
    px = bytes((r, g, b))
    raw = bytearray()
    for _ in range(height):
        raw.append(0)  # PNG filter type 0 (None) per scanline
        raw.extend(px * width)
    idat = zlib.compress(bytes(raw), 9)

    def _chunk(tag: bytes, data: bytes) -> bytes:
        chunk = tag + data
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    sig = b"\x89PNG\r\n\x1a\n"
    return sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


def _load_or_create_cert(signer_cert: Optional[str], signer_key: Optional[str],
                         wwdr_cert: Optional[str]) -> Tuple[str, str, str]:
    """Return (cert_pem, key_pem, chain_pem). If Apple credentials are missing,
    mint a throwaway self-signed dev cert + key."""
    rc = shutil.which("openssl")
    if not rc:
        raise RuntimeError("openssl not found on PATH; required to sign passes")

    if signer_cert and signer_key:
        chain = wwdr_cert or signer_cert
        if not Path(signer_cert).exists():
            raise FileNotFoundError(signer_cert)
        if not Path(signer_key).exists():
            raise FileNotFoundError(signer_key)
        return signer_cert, signer_key, chain

    # --- dev-only self-signed fallback ---
    tmp = tempfile.mkdtemp(prefix="qbpass-dev-")
    key_pem = os.path.join(tmp, "dev_key.pem")
    cert_pem = os.path.join(tmp, "dev_cert.pem")
    subj = "/CN=QB Protocol OmegaTalk Dev Pass/O=org.beo/OU=passkit-dev"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", key_pem, "-out", cert_pem, "-days", "3650", "-subj", subj,
         "-addext", "keyUsage = digitalSignature"],
        check=True, capture_output=True,
    )
    return cert_pem, key_pem, cert_pem


def _build_pass_json(apple_id: str, name: str, token_hint: str,
                     pass_type_id: str, team_id: str, web_service_url: Optional[str]) -> bytes:
    serial = token_hint or "omegatalk-1"
    payload: Dict = {
        "formatVersion": 1,
        "passTypeIdentifier": pass_type_id,
        "serialNumber": serial[:64],
        "organizationName": "BEING _ OMEGA + PRIM E",
        "description": "OmegaTalk chat session credential for QB Protocol",
        "teamIdentifier": team_id,
        "labelColor": "rgb(255,255,255)",
        "foregroundColor": "rgb(255,255,255)",
        "backgroundColor": "rgb(0,122,255)",
        "barcode": {
            "format": "PKBarcodeFormatQR",
            "message": ("omegatalk://session/" + (token_hint or "default")),
            "messageEncoding": "iso-8859-1",
        },
        # primaryFields renders large center text on the loyalty/card face.
        "primaryFields": [{"label": "Apple ID", "value": apple_id, "key": "appleid"}],
        "secondaryFields": [{"label": "Session", "value": name or "active", "key": "session"}],
    }
    if token_hint:
        payload["auxiliaryFields"] = [{"label": "Token ref", "value": token_hint[:10], "key": "token"}]
    if web_service_url:
        payload["webServiceURL"] = web_service_url
    # Apple requires alphabetically stable, deterministic JSON (not strictly
    # mandatory, but good practice and matches reference builders).
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _build_manifest(files: Dict[str, bytes]) -> bytes:
    manifest = {name: _sha1(data) for name, data in files.items()}
    return json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sign(manifest_path: str, cert_pem: str, key_pem: str, chain_pem: str) -> bytes:
    """Produce a PKCS#7 detached DER signature over manifest.json."""
    cmd = ["openssl", "smime", "-sign", "-binary", "-in", manifest_path,
           "-signer", cert_pem, "-inkey", key_pem, "-certfile", chain_pem,
           "-outform", "DER"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        raise RuntimeError(f"openssl signing failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def build_pass_bundle(files: Dict[str, bytes]) -> Dict[str, bytes]:
    """Given the source files (path->bytes), attach manifest + signature."""
    files = dict(files)  # don't mutate caller's dict
    manifest = _build_manifest(files)
    files["manifest.json"] = manifest
    cert, key, chain = _load_or_create_cert(
        os.environ.get("QB_SIGNER_CERT"),
        os.environ.get("QB_SIGNER_KEY"),
        os.environ.get("QB_WWDR_CERT"),
    )
    files["signature"] = _sign_manifest_bytes(manifest, cert, key, chain)
    return files


def _sign_manifest_bytes(manifest: bytes, cert_pem: str, key_pem: str, chain_pem: str) -> bytes:
    tmp = tempfile.mkdtemp(prefix="qbpass-sign-")
    man_path = os.path.join(tmp, "manifest.json")
    with open(man_path, "wb") as fh:
        fh.write(manifest)
    return _sign(man_path, cert_pem, key_pem, chain_pem)


def generate_pass(out_path: str, apple_id: str, name: str = "QB Protocol",
                  token_hint: str = "", self_signed: bool = False) -> str:
    """Generate a ``.pkpass`` at *out_path* (overwriting) and return its path."""
    out_path = os.fspath(out_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    pass_type = os.environ.get("QB_PASS_TYPE_ID", DEFAULT_PASS_TYPE)
    team_id = os.environ.get("QB_TEAM_ID", DEFAULT_TEAM).ljust(10, "0")[:10]
    web_url = os.environ.get("QB_AUTH_URL") or "https://qbprotocol.local/wallet"

    files: Dict[str, bytes] = {
        "pass.json": _build_pass_json(apple_id, name, token_hint, pass_type, team_id, web_url),
        "icon.png": _png(58, 58, APPLE_BLUE),
        "icon@2x.png": _png(114, 114, APPLE_BLUE),
    }
    bundled = build_pass_bundle(files)

    parent = Path(out_path).parent
    tmp_zip = parent / (Path(out_path).name + ".tmp.zip")
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in bundled.items():
            zf.writestr(name, data)
    tmp_zip.replace(out_path)
    return out_path


def verify_pass(pass_path: str) -> Dict[str, object]:
    """Validate bundle structure: required files present + manifest hashes match.

    Does NOT verify the cryptographic signature (that requires the Apple trust
    chain); it confirms the packaging is internally consistent."""
    pass_path = os.fspath(pass_path)
    result: Dict[str, object] = {"path": pass_path, "valid": False, "files": [], "errors": []}
    if not Path(pass_path).exists():
        result["errors"].append("file not found")
        return result
    try:
        with zipfile.ZipFile(pass_path) as zf:
            names = zf.namelist()
            result["files"] = names
            if "pass.json" not in names:
                result["errors"].append("missing pass.json")
            if "manifest.json" not in names:
                result["errors"].append("missing manifest.json")
            if "signature" not in names:
                result["errors"].append("missing signature")
            if "manifest.json" in names:
                manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                for fname, expected in manifest.items():
                    if fname not in names:
                        result["errors"].append(f"manifest lists {fname} but it is missing")
                        continue
                    actual = _sha1(zf.read(fname))
                    if actual != expected:
                        result["errors"].append(f"hash mismatch for {fname}")
    except zipfile.BadZipFile:
        result["errors"].append("not a valid zip / pkpass")
    result["valid"] = (not result["errors"])
    return result


__all__ = ["generate_pass", "verify_pass", "build_pass_bundle", "DEFAULT_PASS_TYPE"]
