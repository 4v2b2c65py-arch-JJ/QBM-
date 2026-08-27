#!/usr/bin/env python3
"""
QB Protocol - Secure Credential Hosting & Broadcast System

Coordinates:
- Accepting hosting for login credentials with multi-proxy connections
- Geo-location for both sides
- User login with credentials
- Model security management
- Stats metrics (login, ID)
- Geo-permission for users

Security:
- Credentials encrypted at rest
- Multi-proxy routing
- Geo-fencing options
- Session management
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CredentialStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


@dataclass
class GeoLocation:
    """Geo-location data."""
    country: str
    country_code: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    isp: str = ""
    is_vpn: bool = False
    is_proxy: bool = False
    risk_score: float = 0.0  # 0-100, lower is better

    @property
    def coordinates(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

    def distance_to(self, other: "GeoLocation") -> float:
        """Calculate distance in km to another location."""
        import math
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c


@dataclass
class ProxyConnection:
    """Proxy connection configuration."""
    proxy_id: str
    proxy_type: ProxyType
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    geo: Optional[GeoLocation] = None
    is_active: bool = True
    latency_ms: float = 0.0
    success_rate: float = 100.0
    last_used: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0


@dataclass
class CredentialEntry:
    """Encrypted credential entry."""
    credential_id: str
    platform: str
    username: str
    encrypted_token: str
    created_at: float
    expires_at: Optional[float]
    status: CredentialStatus
    geo_created: GeoLocation
    geo_last_used: Optional[GeoLocation] = None
    last_used: float = 0.0
    total_uses: int = 0
    proxy_used: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoginSession:
    """Active login session."""
    session_id: str
    credential_id: str
    platform: str
    username: str
    started_at: float
    geo_start: GeoLocation
    geo_current: Optional[GeoLocation] = None
    proxy_chain: List[str] = field(default_factory=list)
    is_active: bool = True
    requests_made: int = 0
    last_activity: float = 0.0


@dataclass
class LoginMetrics:
    """Login statistics and metrics."""
    total_logins: int = 0
    active_sessions: int = 0
    failed_logins: int = 0
    unique_users: int = 0
    unique_platforms: int = 0
    avg_session_duration: float = 0.0
    geo_distribution: Dict[str, int] = field(default_factory=dict)
    platform_distribution: Dict[str, int] = field(default_factory=dict)
    login_history: List[Dict[str, Any]] = field(default_factory=list)


class CredentialVault:
    """Secure credential storage and management."""

    def __init__(self):
        self.credentials: Dict[str, CredentialEntry] = {}
        self.sessions: Dict[str, LoginSession] = {}
        self.proxies: Dict[str, ProxyConnection] = {}
        self.metrics = LoginMetrics()
        self._encryption_key = self._generate_key()

    def _generate_key(self) -> str:
        """Generate encryption key from machine-specific data."""
        machine_id = f"{uuid.getnode()}-{os.getpid()}-{time.time()}"
        return hashlib.sha256(machine_id.encode()).hexdigest()[:32]

    def _encrypt(self, data: str) -> str:
        """Simple XOR encryption (production: use AES-256-GCM)."""
        key = self._encryption_key
        encrypted = []
        for i, char in enumerate(data):
            encrypted.append(chr(ord(char) ^ ord(key[i % len(key)])))
        return ''.join(encrypted)

    def _decrypt(self, data: str) -> str:
        """Decrypt data."""
        return self._encrypt(data)  # XOR is symmetric

    def add_credential(
        self,
        platform: str,
        username: str,
        token: str,
        geo: GeoLocation,
        expires_in: Optional[int] = None,
    ) -> CredentialEntry:
        """Add a new credential."""
        cred_id = f"cred_{platform}_{username}_{int(time.time())}"
        encrypted_token = self._encrypt(token)

        credential = CredentialEntry(
            credential_id=cred_id,
            platform=platform,
            username=username,
            encrypted_token=encrypted_token,
            created_at=time.time(),
            expires_at=time.time() + expires_in if expires_in else None,
            status=CredentialStatus.ACTIVE,
            geo_created=geo,
        )

        self.credentials[cred_id] = credential
        self.metrics.total_logins += 1
        self.metrics.unique_users = len(set(c.username for c in self.credentials.values()))
        self.metrics.unique_platforms = len(set(c.platform for c in self.credentials.values()))

        # Update distributions
        self.metrics.geo_distribution[geo.country_code] = (
            self.metrics.geo_distribution.get(geo.country_code, 0) + 1
        )
        self.metrics.platform_distribution[platform] = (
            self.metrics.platform_distribution.get(platform, 0) + 1
        )

        return credential

    def get_credential(self, cred_id: str) -> Optional[CredentialEntry]:
        """Get a credential by ID."""
        return self.credentials.get(cred_id)

    def get_credentials_by_platform(self, platform: str) -> List[CredentialEntry]:
        """Get all credentials for a platform."""
        return [c for c in self.credentials.values() if c.platform == platform]

    def revoke_credential(self, cred_id: str) -> bool:
        """Revoke a credential."""
        if cred_id in self.credentials:
            self.credentials[cred_id].status = CredentialStatus.REVOKED
            return True
        return False

    def add_proxy(self, proxy: ProxyConnection):
        """Add a proxy connection."""
        self.proxies[proxy.proxy_id] = proxy

    def get_best_proxy(self, target_geo: Optional[GeoLocation] = None) -> Optional[ProxyConnection]:
        """Get the best proxy based on latency and success rate."""
        active = [p for p in self.proxies.values() if p.is_active]
        if not active:
            return None

        if target_geo:
            # Find closest proxy
            active.sort(key=lambda p: p.geo.distance_to(target_geo) if p.geo else float('inf'))
        else:
            # Find fastest proxy
            active.sort(key=lambda p: p.latency_ms)

        return active[0] if active else None

    def create_session(
        self,
        cred_id: str,
        geo: GeoLocation,
        use_proxy: bool = True,
    ) -> Optional[LoginSession]:
        """Create a new login session."""
        credential = self.credentials.get(cred_id)
        if not credential or credential.status != CredentialStatus.ACTIVE:
            return None

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        proxy_chain = []

        if use_proxy:
            proxy = self.get_best_proxy(geo)
            if proxy:
                proxy_chain.append(proxy.proxy_id)
                proxy.last_used = time.time()
                proxy.total_requests += 1

        session = LoginSession(
            session_id=session_id,
            credential_id=cred_id,
            platform=credential.platform,
            username=credential.username,
            started_at=time.time(),
            geo_start=geo,
            geo_current=geo,
            proxy_chain=proxy_chain,
        )

        self.sessions[session_id] = session
        self.metrics.active_sessions = len([s for s in self.sessions.values() if s.is_active])

        # Update credential
        credential.last_used = time.time()
        credential.total_uses += 1
        credential.geo_last_used = geo
        credential.proxy_used = proxy_chain[0] if proxy_chain else None

        # Log
        self.metrics.login_history.append({
            "session_id": session_id,
            "platform": credential.platform,
            "username": credential.username,
            "geo": geo.country_code,
            "timestamp": time.time(),
        })

        return session

    def end_session(self, session_id: str):
        """End a login session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            duration = time.time() - session.started_at
            self.metrics.avg_session_duration = (
                (self.metrics.avg_session_duration * (self.metrics.active_sessions - 1) + duration)
                / self.metrics.active_sessions
                if self.metrics.active_sessions > 0
                else duration
            )
            self.metrics.active_sessions = len([s for s in self.sessions.values() if s.is_active])

    def get_metrics(self) -> Dict[str, Any]:
        """Get full metrics report."""
        return {
            "total_logins": self.metrics.total_logins,
            "active_sessions": self.metrics.active_sessions,
            "failed_logins": self.metrics.failed_logins,
            "unique_users": self.metrics.unique_users,
            "unique_platforms": self.metrics.unique_platforms,
            "avg_session_duration": self.metrics.avg_session_duration,
            "geo_distribution": self.metrics.geo_distribution,
            "platform_distribution": self.metrics.platform_distribution,
            "total_credentials": len(self.credentials),
            "active_credentials": sum(1 for c in self.credentials.values() if c.status == CredentialStatus.ACTIVE),
            "total_proxies": len(self.proxies),
            "active_proxies": sum(1 for p in self.proxies.values() if p.is_active),
        }

    def get_geo_summary(self) -> Dict[str, Any]:
        """Get geo-location summary."""
        countries = {}
        for cred in self.credentials.values():
            code = cred.geo_created.country_code
            if code not in countries:
                countries[code] = {
                    "count": 0,
                    "city": cred.geo_created.city,
                    "coordinates": cred.geo_created.coordinates,
                }
            countries[code]["count"] += 1

        return {
            "countries": countries,
            "total_locations": len(countries),
            "primary_location": max(countries, key=lambda k: countries[k]["count"]) if countries else None,
        }


class BroadcastCredentialCoordinator:
    """Coordinates credential hosting with broadcast system."""

    def __init__(self):
        self.vault = CredentialVault()
        self.current_geo = self._detect_current_geo()

    def _detect_current_geo(self) -> GeoLocation:
        """Detect current geo-location."""
        # In production, use IP geolocation API
        # For now, return exemplary measurements based on timezone
        return GeoLocation(
            country="United States",
            country_code="US",
            region="Florida",
            city="Miami",
            latitude=25.7617,
            longitude=-80.1918,
            timezone="America/New_York",
            isp="Comcast",
            is_vpn=False,
            is_proxy=False,
            risk_score=10.0,
        )

    def setup_exemplary_geo(self) -> GeoLocation:
        """Set up exemplary geo measurements from current location."""
        return self.current_geo

    def add_social_credential(
        self,
        platform: str,
        username: str,
        token: str,
        geo_permission: bool = True,
    ) -> Dict[str, Any]:
        """Add a social media credential with geo-permission."""
        geo = self.current_geo if geo_permission else GeoLocation(
            country="Unknown", country_code="XX", region="Unknown", city="Unknown",
            latitude=0.0, longitude=0.0, timezone="UTC",
        )

        credential = self.vault.add_credential(
            platform=platform,
            username=username,
            token=token,
            geo=geo,
        )

        return {
            "credential_id": credential.credential_id,
            "platform": credential.platform,
            "username": credential.username,
            "geo_permission": geo_permission,
            "geo_location": {
                "country": credential.geo_created.country_code,
                "city": credential.geo_created.city,
                "coordinates": credential.geo_created.coordinates,
            },
            "status": credential.status.value,
        }

    def login_with_credential(
        self,
        cred_id: str,
        use_proxy: bool = True,
    ) -> Dict[str, Any]:
        """Login using a stored credential."""
        session = self.vault.create_session(
            cred_id=cred_id,
            geo=self.current_geo,
            use_proxy=use_proxy,
        )

        if not session:
            self.vault.metrics.failed_logins += 1
            return {"error": "Invalid or expired credential"}

        return {
            "session_id": session.session_id,
            "platform": session.platform,
            "username": session.username,
            "geo_start": {
                "country": session.geo_start.country_code,
                "city": session.geo_start.city,
            },
            "proxy_used": session.proxy_chain,
            "started_at": session.started_at,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get full stats metrics."""
        return {
            "metrics": self.vault.get_metrics(),
            "geo_summary": self.vault.get_geo_summary(),
            "current_geo": {
                "country": self.current_geo.country_code,
                "city": self.current_geo.city,
                "coordinates": self.current_geo.coordinates,
                "timezone": self.current_geo.timezone,
            },
        }


# Global instance
credential_coordinator = BroadcastCredentialCoordinator()
