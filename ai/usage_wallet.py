#!/usr/bin/env python3
"""
QB Protocol - API Usage Pricing & Token Wallet
Transparent, fair pricing with a local ledger for transactions and balances.
NO private keys, seed phrases, or external wallet secrets are stored.
"""
import os, json, uuid, threading, time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime

WALLET_PATH = Path.home() / ".qb_protocol_usage_wallet.json"

# Fair, transparent pricing (USD-equivalent units; configurable via env)
# Local/self-hosted inference is free by default; remote/proxied usage can be metered.
DEFAULT_PRICING = {
    "currency": "USD",
    "version": "2026-11-07",
    "tiers": {
        "local_free": {"label": "Local device (self-hosted)", "price_per_1k_tokens": 0.0, "price_per_request": 0.0, "included_monthly_requests": 999999},
        "community":   {"label": "Community node",            "price_per_1k_tokens": 0.0005, "price_per_request": 0.0001, "included_monthly_requests": 10000},
        "standard":    {"label": "Standard API",              "price_per_1k_tokens": 0.002,  "price_per_request": 0.001,  "included_monthly_requests": 0},
        "pro":         {"label": "Pro API",                   "price_per_1k_tokens": 0.005,  "price_per_request": 0.002,  "included_monthly_requests": 0},
    },
    "notes": "Fair pricing: local inference is free. Metered tiers apply only to shared/remote node usage. You control your own node; no hidden fees.",
}

@dataclass
class Transaction:
    tx_id: str
    timestamp: str
    node_id: str
    type: str  # usage, credit, debit, grant, refund
    amount: float
    currency: str
    tokens: int = 0
    requests: int = 0
    tier: str = "local_free"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class UsageWallet:
    def __init__(self):
        self._lock = threading.RLock()
        self._data = {"balances": {}, "transactions": [], "pricing": DEFAULT_PRICING}
        self._load()

    def _load(self):
        if WALLET_PATH.exists():
            try:
                self._data.update(json.loads(WALLET_PATH.read_text()))
            except Exception:
                pass
        self._data.setdefault("pricing", DEFAULT_PRICING)

    def _save(self):
        try:
            WALLET_PATH.write_text(json.dumps(self._data, indent=2, default=str))
        except Exception:
            pass

    def pricing(self) -> Dict[str, Any]:
        # allow env override of a single default tier without exposing secrets
        return self._data.get("pricing", DEFAULT_PRICING)

    def set_pricing(self, pricing: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._data["pricing"] = pricing
            self._save()
        return self.pricing()

    def get_balance(self, node_id: str) -> Dict[str, Any]:
        b = self._data["balances"].get(node_id, {"node_id": node_id, "balance": 0.0, "currency": "USD", "tokens_credited": 0, "tokens_used": 0, "requests": 0})
        b["node_id"] = node_id
        return b

    def credit(self, node_id: str, amount: float, currency: str = "USD", reason: str = "credit", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        with self._lock:
            b = self.get_balance(node_id)
            b["balance"] = round(b.get("balance", 0.0) + float(amount), 8)
            self._data["balances"][node_id] = b
            tx = Transaction(str(uuid.uuid4()), datetime.utcnow().isoformat()+"Z", node_id, "credit", float(amount), currency, description=reason, metadata=metadata or {})
            self._data["transactions"].append(asdict(tx))
            self._data["transactions"] = self._data["transactions"][-5000:]
            self._save()
        return {"balance": b, "transaction": asdict(tx)}

    def record_usage(self, node_id: str, tokens: int = 0, requests: int = 1, tier: str = "local_free", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        pricing = self.pricing()
        t = (pricing.get("tiers") or {}).get(tier) or pricing["tiers"]["local_free"]
        cost = (max(0,int(tokens))/1000.0) * float(t.get("price_per_1k_tokens", 0)) + max(0,int(requests)) * float(t.get("price_per_request", 0))
        cost = round(cost, 8)
        with self._lock:
            b = self.get_balance(node_id)
            b["tokens_used"] = int(b.get("tokens_used", 0)) + max(0,int(tokens))
            b["requests"] = int(b.get("requests", 0)) + max(0,int(requests))
            b["balance"] = round(float(b.get("balance", 0.0)) - cost, 8)
            self._data["balances"][node_id] = b
            tx = Transaction(str(uuid.uuid4()), datetime.utcnow().isoformat()+"Z", node_id, "usage", -cost, pricing.get("currency","USD"), tokens=max(0,int(tokens)), requests=max(0,int(requests)), tier=tier, description=f"usage:{tier}", metadata=metadata or {})
            self._data["transactions"].append(asdict(tx))
            self._data["transactions"] = self._data["transactions"][-5000:]
            self._save()
        return {"cost": cost, "tier": tier, "balance": b, "transaction": asdict(tx)}

    def transactions(self, node_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        txs = self._data.get("transactions", [])
        if node_id:
            txs = [t for t in txs if t.get("node_id") == node_id]
        return txs[-max(1,min(limit,1000)):]

    def status(self) -> Dict[str, Any]:
        return {"balances": len(self._data.get("balances", {})), "transactions": len(self._data.get("transactions", {})), "pricing": self.pricing(), "wallet_path": str(WALLET_PATH)}

usage_wallet = UsageWallet()
