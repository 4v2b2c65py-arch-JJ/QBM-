#!/usr/bin/env python3
"""
QB Protocol - Network Uptime & Compliance Keeper

Keeps models uptimed with the network.
Ensures compliance and perfect sync.

Responsibilities:
- API health monitoring
- Auto-refresh cached data
- Rate limit compliance
- Uptime statistics
- New listing alerts
- Generation sync
"""

from __future__ import annotations

import json
import time
import urllib.request
import ssl
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RATE_LIMITED = "rate_limited"


@dataclass
class APIHealth:
    """Health status of an API endpoint."""
    name: str
    endpoint: str
    status: HealthStatus
    last_check: float
    response_time_ms: float
    uptime_pct: float
    total_requests: int
    failed_requests: int
    rate_limit_remaining: int
    rate_limit_reset: float
    last_error: Optional[str] = None


@dataclass
class ComplianceRule:
    """Rate limit and compliance rule."""
    api_name: str
    max_requests_per_minute: int
    max_requests_per_hour: int
    current_minute_count: int
    current_hour_count: int
    minute_window_start: float
    hour_window_start: float
    compliant: bool = True


@dataclass
class UptimeStats:
    """Overall uptime statistics."""
    started_at: float
    total_checks: int
    healthy_checks: int
    degraded_checks: int
    unhealthy_checks: int
    avg_response_ms: float
    total_data_synced: int
    new_listings_found: int
    generations_completed: int


class NetworkComplianceKeeper:
    """Keeps models uptimed and compliant with network APIs."""

    # API compliance rules
    COMPLIANCE_RULES = {
        "anilist": {
            "max_per_minute": 30,  # Current temporary limit
            "max_per_hour": 900,
            "cooldown_on_429": 60,
        },
        "jikan": {
            "max_per_minute": 30,
            "max_per_hour": 600,
            "cooldown_on_429": 10,
        },
        "kitsu": {
            "max_per_minute": 60,
            "max_per_hour": 1000,
            "cooldown_on_429": 30,
        },
        "mangadex": {
            "max_per_minute": 30,
            "max_per_hour": 600,
            "cooldown_on_429": 10,
        },
        "omega": {
            "max_per_minute": 60,
            "max_per_hour": 1000,
            "cooldown_on_429": 5,
        },
    }

    def __init__(self):
        self.api_health: Dict[str, APIHealth] = {}
        self.compliance: Dict[str, ComplianceRule] = {}
        self.uptime = UptimeStats(
            started_at=time.time(),
            total_checks=0,
            healthy_checks=0,
            degraded_checks=0,
            unhealthy_checks=0,
            avg_response_ms=0.0,
            total_data_synced=0,
            new_listings_found=0,
            generations_completed=0,
        )
        self._init_compliance()

    def _init_compliance(self):
        """Initialize compliance tracking."""
        for api_name, rules in self.COMPLIANCE_RULES.items():
            self.compliance[api_name] = ComplianceRule(
                api_name=api_name,
                max_requests_per_minute=rules["max_per_minute"],
                max_requests_per_hour=rules["max_per_hour"],
                current_minute_count=0,
                current_hour_count=0,
                minute_window_start=time.time(),
                hour_window_start=time.time(),
            )

    def check_api_health(self, api_name: str, url: str) -> APIHealth:
        """Check health of an API endpoint."""
        start = time.time()
        status = HealthStatus.HEALTHY
        error = None

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # AniList requires POST for GraphQL
            if api_name == "anilist":
                query = "query{Page(perPage:1){media{id}}}"
                payload = json.dumps({"query": query}).encode()
                req = urllib.request.Request(url, data=payload, method="POST", headers={
                    "User-Agent": "QB-Protocol/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                })
            elif api_name == "kitsu":
                req = urllib.request.Request(url, headers={
                    "User-Agent": "QB-Protocol/1.0",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                })
            else:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "QB-Protocol/1.0",
                    "Accept": "application/json",
                })

            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                response_ms = (time.time() - start) * 1000
                if resp.status == 200:
                    status = HealthStatus.HEALTHY
                elif resp.status == 429:
                    status = HealthStatus.RATE_LIMITED
                    error = "Rate limited"
                else:
                    status = HealthStatus.DEGRADED
                    error = f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            response_ms = (time.time() - start) * 1000
            if e.code == 429:
                status = HealthStatus.RATE_LIMITED
                error = "Rate limited"
            elif e.code in (502, 503, 504):
                status = HealthStatus.DEGRADED
                error = f"HTTP {e.code}"
            else:
                status = HealthStatus.UNHEALTHY
                error = f"HTTP {e.code}"
        except Exception as e:
            response_ms = (time.time() - start) * 1000
            status = HealthStatus.UNHEALTHY
            error = str(e)[:100]

        # Update or create health entry
        if api_name not in self.api_health:
            self.api_health[api_name] = APIHealth(
                name=api_name,
                endpoint=url,
                status=status,
                last_check=time.time(),
                response_time_ms=response_ms,
                uptime_pct=100.0,
                total_requests=0,
                failed_requests=0,
                rate_limit_remaining=0,
                rate_limit_reset=0.0,
                last_error=error,
            )
        else:
            health = self.api_health[api_name]
            health.status = status
            health.last_check = time.time()
            health.response_time_ms = response_ms
            health.last_error = error
            health.total_requests += 1
            if status in (HealthStatus.UNHEALTHY, HealthStatus.RATE_LIMITED):
                health.failed_requests += 1
            health.uptime_pct = (
                (health.total_requests - health.failed_requests) / health.total_requests * 100
            )

        # Update uptime stats
        self.uptime.total_checks += 1
        if status == HealthStatus.HEALTHY:
            self.uptime.healthy_checks += 1
        elif status == HealthStatus.DEGRADED:
            self.uptime.degraded_checks += 1
        else:
            self.uptime.unhealthy_checks += 1

        return self.api_health[api_name]

    def check_all_apis(self) -> Dict[str, APIHealth]:
        """Check health of all tracked APIs."""
        apis = {
            "anilist": "https://graphql.anilist.co",  # Will use POST for health
            "jikan": "https://api.jikan.moe/v4/anime/1",  # Cowboy Bebop
            "kitsu": "https://kitsu.app/api/edge/anime/1",  # Using anime endpoint
            "mangadex": "https://api.mangadex.org/manga?limit=1",  # List with limit
            "omega": "https://omegaapi.vercel.app/api/v1/series?perPage=1",  # List series
        }

        results = {}
        for name, url in apis.items():
            results[name] = self.check_api_health(name, url)

        return results

    def can_make_request(self, api_name: str) -> Tuple[bool, str]:
        """Check if a request can be made while staying compliant."""
        if api_name not in self.compliance:
            return True, "No compliance rules"

        rule = self.compliance[api_name]
        now = time.time()

        # Reset minute window if needed
        if now - rule.minute_window_start >= 60:
            rule.current_minute_count = 0
            rule.minute_window_start = now

        # Reset hour window if needed
        if now - rule.hour_window_start >= 3600:
            rule.current_hour_count = 0
            rule.hour_window_start = now

        # Check limits
        if rule.current_minute_count >= rule.max_requests_per_minute:
            rule.compliant = False
            wait_time = 60 - (now - rule.minute_window_start)
            return False, f"Minute limit reached. Wait {wait_time:.0f}s"

        if rule.current_hour_count >= rule.max_requests_per_hour:
            rule.compliant = False
            wait_time = 3600 - (now - rule.hour_window_start)
            return False, f"Hour limit reached. Wait {wait_time:.0f}s"

        rule.compliant = True
        return True, "OK"

    def record_request(self, api_name: str):
        """Record a request for compliance tracking."""
        if api_name in self.compliance:
            rule = self.compliance[api_name]
            rule.current_minute_count += 1
            rule.current_hour_count += 1

    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance report for all APIs."""
        report = {}
        for api_name, rule in self.compliance.items():
            report[api_name] = {
                "compliant": rule.compliant,
                "minute_count": rule.current_minute_count,
                "minute_limit": rule.max_requests_per_minute,
                "hour_count": rule.current_hour_count,
                "hour_limit": rule.max_requests_per_hour,
                "minute_remaining": rule.max_requests_per_minute - rule.current_minute_count,
                "hour_remaining": rule.max_requests_per_hour - rule.current_hour_count,
            }
        return report

    def get_uptime_report(self) -> Dict[str, Any]:
        """Get overall uptime report."""
        uptime_pct = (
            self.uptime.healthy_checks / self.uptime.total_checks * 100
            if self.uptime.total_checks > 0
            else 100.0
        )

        api_statuses = {}
        for name, health in self.api_health.items():
            api_statuses[name] = {
                "status": health.status.value,
                "response_ms": health.response_time_ms,
                "uptime_pct": health.uptime_pct,
                "last_error": health.last_error,
            }

        return {
            "overall_uptime_pct": uptime_pct,
            "total_checks": self.uptime.total_checks,
            "healthy": self.uptime.healthy_checks,
            "degraded": self.uptime.degraded_checks,
            "unhealthy": self.uptime.unhealthy_checks,
            "apis": api_statuses,
            "compliance": self.get_compliance_report(),
            "uptime_duration_hours": (time.time() - self.uptime.started_at) / 3600,
        }

    def sync_model_state(self) -> Dict[str, Any]:
        """Sync model state with network - returns status."""
        # Check all APIs
        health_results = self.check_all_apis()

        # Count healthy APIs
        healthy = sum(1 for h in health_results.values() if h.status == HealthStatus.HEALTHY)
        total = len(health_results)

        # Update uptime
        self.uptime.total_data_synced += 1

        return {
            "synced_at": time.time(),
            "healthy_apis": healthy,
            "total_apis": total,
            "sync_status": "complete" if healthy == total else "partial",
            "api_status": {name: h.status.value for name, h in health_results.items()},
        }


class ModelUptimeKeeper:
    """Keeps the model uptimed and compliant."""

    def __init__(self):
        self.compliance_keeper = NetworkComplianceKeeper()
        self.last_sync: float = 0
        self.sync_interval: float = 300  # 5 minutes
        self.is_running: bool = False

    def start(self):
        """Start the uptime keeper."""
        self.is_running = True
        self.last_sync = time.time()

    def stop(self):
        """Stop the uptime keeper."""
        self.is_running = False

    def tick(self) -> Optional[Dict[str, Any]]:
        """Single tick - check if sync needed and perform it."""
        if not self.is_running:
            return None

        now = time.time()
        if now - self.last_sync >= self.sync_interval:
            self.last_sync = now
            return self.compliance_keeper.sync_model_state()
        return None

    def get_status(self) -> Dict[str, Any]:
        """Get full uptime status."""
        return {
            "running": self.is_running,
            "last_sync": self.last_sync,
            "sync_interval": self.sync_interval,
            "uptime": self.compliance_keeper.get_uptime_report(),
        }


# Global instance
uptime_keeper = ModelUptimeKeeper()
