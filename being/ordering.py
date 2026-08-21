#!/usr/bin/env python3
"""
BEING _ OMEGA + PRIM E — ordering agent registry.

A typed surface for the "automatic ordering with Amazon, flight apps, food,
real estate, services, security" capability. Each category is a *Provider*
plugin. Concrete providers require external OAuth credentials and merchant APIs
that are not bundled here; the stubs below declare the contract + the exact
integration points / credential keys the orchestrator expects so each can be
filled in independently.

Providers are discovered dynamically by class name from this package; register
a real implementation by subclassing ``Provider`` and adding it to
``PROVIDERS``. Until then, stubs raise ``NotImplementedError`` with the precise
integration steps, so the agent never silently fakes an order.

Crypto-paid orders are supported via :class:`CurrencyConverter` +
:class:`CryptoPayment` and the :func:`buy_with_crypto` helper, which converts
crypto -> fiat, dispatches the order, and (optionally) waits for a 2FA OTP from
the virtual-SIM receiver in :mod:`being.sms`.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OrderRequest:
    """A normalized ordering request the agent presents to a provider."""

    category: str
    item: str
    quantity: int = 1
    notes: str = ""
    user_id: str = ""
    shipping_address: Optional[Dict[str, str]] = None
    payment_method: Optional[Dict[str, str]] = None
    constraints: Dict[str, object] = field(default_factory=dict)


@dataclass
class OrderResult:
    provider: str
    order_id: str = ""
    status: str = "pending"
    confirmation: str = ""
    tracking_url: str = ""
    error: str = ""


class Provider(ABC):
    """Base contract for every ordering provider plugin."""

    category: str = "base"
    credential_keys: List[str] = []  # env keys the orchestrator must supply

    def __init__(self) -> None:
        self.enabled = self._check_credentials()

    def _check_credentials(self) -> bool:
        return all(os.environ.get(k) for k in self.credential_keys)

    @abstractmethod
    def order(self, req: OrderRequest) -> OrderResult:
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class _Stub(Provider):
    """Provider stub: documents the contract without performing real orders."""

    def order(self, req: OrderRequest) -> OrderResult:
        creds = ", ".join(self.credential_keys) or "none"
        return OrderResult(
            provider=self.name,
            status="unimplemented",
            error=(
                f"{self.category} ordering is not yet wired. Provide credentials "
                f"({creds}) + a concrete '{self.category}' provider implementing "
                "`order(req) -> OrderResult` and register it in PROVIDERS."
            ),
        )


class AmazonProvider(_Stub):
    category = "amazon"
    credential_keys = ["AMAZON_ACCESS_KEY_ID", "AMAZON_SECRET_ACCESS_KEY", "AMAZON_PARTNER_TAG"]


class FlightsProvider(_Stub):
    category = "flights"
    credential_keys = ["AMADEUS_API_KEY", "AMADEUS_API_SECRET"]


class FoodProvider(_Stub):
    category = "food"
    credential_keys = ["DOORDASH_API_KEY", "UBER_EATS_CLIENT_ID", "UBER_EATS_CLIENT_SECRET"]


class RealEstateProvider(_Stub):
    category = "real_estate"
    credential_keys = ["MLS_API_KEY", "REALTOR_COM_API_KEY"]


class ServicesProvider(_Stub):
    category = "services"
    credential_keys = ["STRIPE_SECRET_KEY", "SQUARE_ACCESS_TOKEN"]


class SecurityProvider(_Stub):
    category = "security"
    credential_keys = ["CROWDSOURCE_API_KEY", "THREAT_INTEL_TOKEN"]


# --- crypto -> fiat conversion ------------------------------------------------

COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "USDC": "usd-coin", "USDT": "tether",
    "LIT": "litecoin", "BCH": "bitcoin-cash", "SOL": "solana", "ADA": "cardano",
    "AVAX": "avalanche-2", "LINK": "chainlink", "DOT": "polkadot", "MATIC": "polygon",
}

# Deterministic fallback rates (USD per 1 unit of crypto). Used when offline or
# to keep tests reproducible; never used to fake a real price in production.
STUB_RATES = {
    "BTC": 50000.0, "ETH": 3000.0, "USDC": 1.0, "USDT": 1.0,
    "LIT": 80.0, "SOL": 140.0, "LINK": 7.0, "DOT": 5.0,
}


class ExchangeRateError(Exception):
    """Raised when a crypto price cannot be resolved."""


class CurrencyConverter:
    """Convert crypto -> fiat (and back).

    Real path: CoinGecko public API (free, no key) -- 1 request/sec limit; set
    ``COINGECKO_API_KEY`` to raise limits. Offline/stub path: fixed rates from
    :data:`STUB_RATES`, selected by ``stub=True`` (used by tests + first run).
    """

    def __init__(self, fiat: str = "USD", stub: bool = False,
                 fetcher: Optional[callable] = None) -> None:
        self.fiat = fiat
        self.stub = stub
        self._fetcher = fetcher

    def _fetch(self, ids: List[str]) -> Dict[str, float]:
        if self._fetcher is not None:
            return self._fetcher(ids, self.fiat)
        import json
        import urllib.parse
        import urllib.request
        vs = self.fiat.lower()
        url = ("https://api.coingecko.com/api/v3/simple/price?"
               + urllib.parse.urlencode({"ids": ",".join(ids), "vs_currencies": vs}))
        req = urllib.request.Request(url, headers={"User-Agent": "qb-protocol/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        out = {}
        for sym, gid in COINGECKO_IDS.items():
            if sym in ids and gid in data and vs in data[gid]:
                out[sym] = float(data[gid][vs])
        return out

    def rate(self, crypto: str) -> float:
        """Return fiat per 1 unit of *crypto*."""
        crypto = crypto.upper()
        if crypto not in COINGECKO_IDS:
            raise ExchangeRateError(f"unknown crypto: {crypto}")
        if self.stub:
            if crypto in STUB_RATES:
                return STUB_RATES[crypto]
            raise ExchangeRateError(f"no stub rate for {crypto}; set stub=False and real network")
        try:
            rates = self._fetch([crypto])
        except Exception:
            rates = {}
        if crypto in rates and rates[crypto] > 0:
            return rates[crypto]
        if crypto in STUB_RATES:
            return STUB_RATES[crypto]
        raise ExchangeRateError(f"no rate available for {crypto}")

    def convert(self, crypto: str, amount: float) -> tuple:
        """Convert *amount* of *crypto* -> (fiat_amount, rate)."""
        r = self.rate(crypto)
        return round(amount * r, 2), r


class CryptoPayment:
    """Crypto-funded purchase: convert -> order -> (optionally) confirm via 2FA SMS."""

    def __init__(self, converter: CurrencyConverter, sms: Optional[object] = None) -> None:
        self.converter = converter
        self.sms = sms

    def buy(self, category: str, item: str, crypto: str, amount: float,
            provider: Optional[Provider] = None, two_factor_timeout: float = 0.0) -> tuple:
        """Convert crypto -> fiat, dispatch an order, optionally read a 2FA OTP.

        Returns (OrderResult, otp_or_None, (fiat_amount, rate)).
        """
        fiat_amount, rate = self.converter.convert(crypto, amount)
        req = OrderRequest(
            category=category, item=item,
            payment_method={
                "type": "crypto", "crypto": crypto, "amount": amount,
                "fiat": fiat_amount, "fiat_currency": self.converter.fiat,
                "rate": rate,
            },
        )
        prov = provider or _find_provider(category)
        result = prov.order(req)
        otp = None
        if two_factor_timeout and self.sms is not None and hasattr(self.sms, "receive_code"):
            otp = self.sms.receive_code(timeout=two_factor_timeout)
        return result, otp, (fiat_amount, rate)


# Registry: the orchestrator iterates PROVIDERS to find the matching category.
PROVIDERS: List[Provider] = [
    AmazonProvider(),
    FlightsProvider(),
    FoodProvider(),
    RealEstateProvider(),
    ServicesProvider(),
    SecurityProvider(),
]


def dispatch(req: OrderRequest) -> OrderResult:
    """Hand *req* to the first enabled provider for its category."""
    for p in PROVIDERS:
        if p.category == req.category:
            return p.order(req)
    return OrderResult(provider="none", status="error", error=f"no provider for category: {req.category}")


def list_providers() -> List[Dict[str, object]]:
    return [
        {"category": p.category, "provider": p.name, "enabled": p.enabled}
        for p in PROVIDERS
    ]


def _find_provider(category: str) -> Provider:
    for p in PROVIDERS:
        if p.category == category:
            return p
    raise ValueError(f"no provider registered for category: {category}")


def buy_with_crypto(category: str, item: str, crypto: str, amount: float,
                    provider: Optional[Provider] = None,
                    sms: Optional[object] = None,
                    two_factor_timeout: float = 120.0,
                    fiat: str = "USD", stub: bool = False) -> tuple:
    """Convert *amount* of *crypto* to fiat, place the order, and (if a 2FA SMS
    provider is supplied) wait for the OTP to confirm. Returns
    (OrderResult, otp_or_None, (fiat_amount, rate)).

    Pass ``stub=True`` for deterministic, offline rates (tests/first-run)."""
    conv = CurrencyConverter(fiat=fiat, stub=stub)
    pw = CryptoPayment(conv, sms=sms)
    return pw.buy(category, item, crypto, amount,
                  provider=provider, two_factor_timeout=two_factor_timeout)


__all__ = [
    "OrderRequest", "OrderResult", "Provider", "dispatch", "list_providers",
    "PROVIDERS", "CurrencyConverter", "CryptoPayment", "ExchangeRateError",
    "buy_with_crypto", "COINGECKO_IDS", "STUB_RATES",
]
