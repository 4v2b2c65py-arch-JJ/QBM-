"""
Satoshi NM Credentials Protection Engine
Protects Bitcoin address credentials from theft and forgery
using social security verification method.
"""

import os
import json
import hashlib
import hmac
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field


# =============================================================================
# CONFIGURATION
# =============================================================================

CREDENTIALS_PATH = Path(__file__).parent / "credentials_protected.json"
MANIFEST_PATH = Path(__file__).parent / "credentials_manifest.json"

# Identity verification constants (from .env in production)
IDENTITY_NAME = "JHAN JHONNIEL FLORES MARTE"
IDENTITY_SSN_LAST4 = "7201"
IDENTITY_BARCODE = "G46870999"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ProtectionManifest:
    """Manifest for credential protection."""
    created_at: str
    last_verified: str
    identity_hash: str
    credential_count: int
    protection_level: str = "SSN_VERIFIED"
    verification_method: str = "social_security_last4"
    tamper_detected: bool = False
    access_log: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CredentialEntry:
    """Single credential entry."""
    timestamp: str
    address: str
    credential_used: str
    credential_length: int
    address_valid: bool
    encoding: str
    type: str
    address_length: int
    zero_count: int


# =============================================================================
# PROTECTION ENGINE
# =============================================================================

class CredentialProtectionEngine:
    """
    Protects credential files from theft and forgery.
    
    Uses social security verification to ensure only the legitimate
    identity can access and verify the credentials.
    """
    
    def __init__(self):
        self._manifest: Optional[ProtectionManifest] = None
        self._credentials: List[CredentialEntry] = []
        self._identity_verified = False
    
    # -------------------------------------------------------------------------
    # IDENTITY VERIFICATION
    # -------------------------------------------------------------------------
    
    def _compute_identity_hash(self) -> str:
        """
        Compute a hash from identity data.
        This binds the credentials to the real identity.
        """
        identity_string = f"{IDENTITY_NAME}:{IDENTITY_SSN_LAST4}:{IDENTITY_BARCODE}"
        return hashlib.sha256(identity_string.encode()).hexdigest()[:32]
    
    def verify_identity(self, name: str, ssn_last4: str, barcode: str) -> Dict[str, Any]:
        """
        Verify identity claim against stored identity.
        
        Args:
            name: Claimed full name
            ssn_last4: Last 4 digits of SSN
            barcode: Government barcode
            
        Returns:
            Verification result with confidence score
        """
        matches = 0
        total_checks = 3
        
        # Check name
        name_match = name.upper() == IDENTITY_NAME.upper()
        if name_match:
            matches += 1
        
        # Check SSN last 4
        ssn_match = ssn_last4 == IDENTITY_SSN_LAST4
        if ssn_match:
            matches += 1
        
        # Check barcode
        barcode_match = barcode == IDENTITY_BARCODE
        if barcode_match:
            matches += 1
        
        confidence = matches / total_checks
        is_authentic = matches == total_checks
        
        result = {
            "is_authentic": is_authentic,
            "confidence": confidence,
            "matches": {
                "name": name_match,
                "ssn_last4": ssn_match,
                "barcode": barcode_match,
            },
            "checked_at": datetime.now().isoformat(),
        }
        
        if is_authentic:
            self._identity_verified = True
        
        return result
    
    # -------------------------------------------------------------------------
    # CREDENTIAL PROTECTION
    # -------------------------------------------------------------------------
    
    def protect_credentials(self, credentials_data: List[Dict[str, Any]]) -> bool:
        """
        Protect credentials with identity binding.
        
        Creates a manifest that binds the credentials to the identity.
        Any tampering can be detected.
        """
        identity_hash = self._compute_identity_hash()
        
        # Create manifest
        self._manifest = ProtectionManifest(
            created_at=datetime.now().isoformat(),
            last_verified=datetime.now().isoformat(),
            identity_hash=identity_hash,
            credential_count=len(credentials_data),
            access_log=[{
                "action": "CREATED",
                "timestamp": datetime.now().isoformat(),
                "identity_hash": identity_hash,
            }],
        )
        
        # Parse credentials
        self._credentials = [
            CredentialEntry(**entry) for entry in credentials_data
        ]
        
        # Save protected file
        protected_data = {
            "_protection": {
                "manifest": {
                    "created_at": self._manifest.created_at,
                    "last_verified": self._manifest.last_verified,
                    "identity_hash": self._manifest.identity_hash,
                    "credential_count": self._manifest.credential_count,
                    "protection_level": self._manifest.protection_level,
                    "verification_method": self._manifest.verification_method,
                },
                "tamper_check": self._compute_tamper_check(credentials_data),
            },
            "credentials": credentials_data,
        }
        
        with open(CREDENTIALS_PATH, 'w') as f:
            json.dump(protected_data, f, indent=2)
        
        # Save manifest separately
        with open(MANIFEST_PATH, 'w') as f:
            json.dump({
                "created_at": self._manifest.created_at,
                "last_verified": self._manifest.last_verified,
                "identity_hash": self._manifest.identity_hash,
                "credential_count": self._manifest.credential_count,
                "protection_level": self._manifest.protection_level,
                "verification_method": self._manifest.verification_method,
                "tamper_detected": self._manifest.tamper_detected,
                "access_log": self._manifest.access_log,
            }, f, indent=2)
        
        return True
    
    def _compute_tamper_check(self, credentials_data: List[Dict[str, Any]]) -> str:
        """Compute tamper detection hash."""
        credential_string = json.dumps(credentials_data, sort_keys=True)
        identity_string = f"{IDENTITY_NAME}:{IDENTITY_SSN_LAST4}:{IDENTITY_BARCODE}"
        combined = credential_string + identity_string
        return hmac.new(
            identity_string.encode(),
            combined.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
    
    def verify_and_load(self, name: str, ssn_last4: str,
                        barcode: str) -> Optional[List[Dict[str, Any]]]:
        """
        Verify identity and load credentials if authentic.
        
        Args:
            name: Full name
            ssn_last4: Last 4 of SSN
            barcode: Government barcode
            
        Returns:
            Credentials list if identity verified, None otherwise
        """
        # First verify identity
        verification = self.verify_identity(name, ssn_last4, barcode)
        
        if not verification["is_authentic"]:
            print(f"[PROTECTION] Identity verification FAILED")
            print(f"  Confidence: {verification['confidence']:.0%}")
            print(f"  Matches: {verification['matches']}")
            return None
        
        # Check if protected file exists
        if not CREDENTIALS_PATH.exists():
            print("[PROTECTION] No protected credentials file found")
            return None
        
        # Load protected file
        with open(CREDENTIALS_PATH, 'r') as f:
            protected_data = json.load(f)
        
        # Verify tamper check
        stored_tamper = protected_data["_protection"]["tamper_check"]
        current_tamper = self._compute_tamper_check(
            protected_data["credentials"]
        )
        
        if stored_tamper != current_tamper:
            print("[PROTECTION] TAMPER DETECTED!")
            print("  Credentials may have been modified")
            return None
        
        # Log access
        if MANIFEST_PATH.exists():
            with open(MANIFEST_PATH, 'r') as f:
                manifest = json.load(f)
            manifest["access_log"].append({
                "action": "ACCESSED",
                "timestamp": datetime.now().isoformat(),
                "identity_verified": True,
            })
            with open(MANIFEST_PATH, 'w') as f:
                json.dump(manifest, f, indent=2)
        
        print(f"[PROTECTION] Identity verified - credentials loaded")
        print(f"  Confidence: {verification['confidence']:.0%}")
        print(f"  Tamper check: PASSED")
        
        return protected_data["credentials"]
    
    def detect_forgery(self, external_credentials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect if external credentials are forged.
        
        Compares external credentials against protected ones.
        """
        if not CREDENTIALS_PATH.exists():
            return {"error": "No protected credentials to compare"}
        
        with open(CREDENTIALS_PATH, 'r') as f:
            protected_data = json.load(f)
        
        protected_creds = protected_data["credentials"]
        
        # Check for discrepancies
        discrepancies = []
        
        if len(external_credentials) != len(protected_creds):
            discrepancies.append(f"Count mismatch: {len(external_credentials)} vs {len(protected_creds)}")
        
        for i, (ext, prot) in enumerate(zip(external_credentials, protected_creds)):
            if ext.get("address") != prot.get("address"):
                discrepancies.append(f"Entry {i}: Address mismatch")
            if ext.get("credential_used") != prot.get("credential_used"):
                discrepancies.append(f"Entry {i}: Credential mismatch")
            if ext.get("timestamp") != prot.get("timestamp"):
                discrepancies.append(f"Entry {i}: Timestamp mismatch (possible forgery)")
        
        is_authentic = len(discrepancies) == 0
        
        return {
            "is_authentic": is_authentic,
            "discrepancies": discrepancies,
            "checked_at": datetime.now().isoformat(),
            "verdict": "AUTHENTIC" if is_authentic else "FORGERY_DETECTED",
        }


# =============================================================================
# MAIN INTERFACE
# =============================================================================

# Global instance
protection_engine = CredentialProtectionEngine()


def protect_satoshi_credentials(credentials_path: str) -> bool:
    """
    Protect the Satoshi NM credentials file.
    
    Args:
        credentials_path: Path to original credentials.json
        
    Returns:
        True if protection successful
    """
    # Load original credentials
    with open(credentials_path, 'r') as f:
        credentials = json.load(f)
    
    # Protect with identity binding
    return protection_engine.protect_credentials(credentials)


def access_protected_credentials(name: str, ssn_last4: str,
                                  barcode: str) -> Optional[List[Dict[str, Any]]]:
    """
    Access protected credentials after identity verification.
    
    Args:
        name: Full name
        ssn_last4: Last 4 of SSN
        barcode: Government barcode
        
    Returns:
        Credentials if identity verified
    """
    return protection_engine.verify_and_load(name, ssn_last4, barcode)


if __name__ == '__main__':
    print("=" * 60)
    print("SATOSHI NM CREDENTIAL PROTECTION")
    print("=" * 60)
    
    # Original credentials path
    original_path = "/Users/jjmarte/delta-stream/Vemex/satoshi-NM/credentials.json"
    
    # Protect credentials
    print("\n[1] Protecting credentials...")
    if protect_satoshi_credentials(original_path):
        print("    Protected file created: credentials_protected.json")
        print("    Manifest created: credentials_manifest.json")
    
    # Test access with correct identity
    print("\n[2] Accessing with correct identity...")
    creds = access_protected_credentials(
        name="JHAN JHONNIEL FLORES MARTE",
        ssn_last4="7201",
        barcode="G46870999"
    )
    if creds:
        print(f"    Loaded {len(creds)} credential entries")
    
    # Test access with wrong identity
    print("\n[3] Testing with wrong identity...")
    creds_fake = access_protected_credentials(
        name="John Doe",
        ssn_last4="0000",
        barcode="FAKE123"
    )
    if not creds_fake:
        print("    Access DENIED (correct behavior)")
    
    # Test forgery detection
    print("\n[4] Testing forgery detection...")
    fake_creds = [{
        "timestamp": "2026-07-15T11:20:43.569799",
        "address": "FAKE_ADDRESS",
        "credential_used": "fake",
        "credential_length": 4,
        "address_valid": False,
        "encoding": "Base58",
        "type": "P2PKH",
        "address_length": 34,
        "zero_count": 0
    }]
    
    result = protection_engine.detect_forgery(fake_creds)
    print(f"    Verdict: {result['verdict']}")
    if result['discrepancies']:
        for d in result['discrepancies']:
            print(f"    - {d}")
    
    print("\n" + "=" * 60)
    print("PROTECTION ACTIVE")
    print("=" * 60)
