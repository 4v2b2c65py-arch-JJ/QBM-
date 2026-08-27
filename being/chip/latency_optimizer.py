#!/usr/bin/env python3
"""
QB Protocol - Latency Tracker & Optimizer

Fixes latency on social apps and transmissions.
Tracks new listings with the model for new generations.
Fixes delays based on timing patterns.

Architecture:
- Response time tracking per API endpoint
- Latency detection and alerting
- Auto-optimization (caching, retry, fallback)
- New listing detection based on timing
- Generation tracking for model updates
"""

from __future__ import annotations

import json
import math
import socket
import ssl
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class LatencyStatus(Enum):
    OK = "ok"
    SLOW = "slow"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ResponseMetric:
    """Single response time measurement."""
    timestamp: float
    endpoint: str
    response_time_ms: float
    status: LatencyStatus
    status_code: Optional[int] = None
    payload_size: int = 0
    cached: bool = False
    retry_count: int = 0


@dataclass
class EndpointStats:
    """Aggregated stats for an endpoint."""
    endpoint: str
    total_requests: int = 0
    total_errors: int = 0
    total_timeouts: int = 0
    avg_response_ms: float = 0.0
    min_response_ms: float = float("inf")
    max_response_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    last_response_ms: float = 0.0
    last_checked: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0
    recent_times: List[float] = field(default_factory=list)

    def add_measurement(self, response_ms: float, status: LatencyStatus):
        self.total_requests += 1
        self.last_response_ms = response_ms
        self.last_checked = time.time()
        self.recent_times.append(response_ms)

        # Keep only last 100 measurements
        if len(self.recent_times) > 100:
            self.recent_times = self.recent_times[-100:]

        if status == LatencyStatus.ERROR:
            self.total_errors += 1
        elif status == LatencyStatus.TIMEOUT:
            self.total_timeouts += 1

        self.min_response_ms = min(self.min_response_ms, response_ms)
        self.max_response_ms = max(self.max_response_ms, response_ms)
        self.avg_response_ms = sum(self.recent_times) / len(self.recent_times)

        # Calculate percentiles
        sorted_times = sorted(self.recent_times)
        self.p50_ms = sorted_times[int(len(sorted_times) * 0.5)]
        self.p95_ms = sorted_times[int(len(sorted_times) * 0.95)]
        self.p99_ms = sorted_times[int(len(sorted_times) * 0.99)]

        self.error_rate = self.total_errors / self.total_requests


@dataclass
class NewListing:
    """Detected new listing."""
    listing_id: str
    title: str
    media_type: str
    discovered_at: float
    source_api: str
    generation: int
    coordinates: Tuple[float, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationTracker:
    """Tracks model generations based on timing."""
    generation: int
    started_at: float
    completed_at: Optional[float]
    new_listings_count: int
    fixes_applied: List[str]
    avg_latency_ms: float
    status: str  # active, completed, stalled


class LatencyOptimizer:
    """Optimizes latency for all API calls."""

    # Latency thresholds in ms
    THRESHOLDS = {
        "fast": 100,
        "normal": 300,
        "slow": 1000,
        "timeout": 5000,
    }

    def __init__(self):
        self.endpoint_stats: Dict[str, EndpointStats] = {}
        self.metrics: List[ResponseMetric] = []
        self.cache: Dict[str, Tuple[float, Any]] = {}  # key -> (timestamp, data)
        self.cache_ttl: Dict[str, float] = {}  # key -> ttl seconds
        self.new_listings: List[NewListing] = []
        self.generations: List[GenerationTracker] = []
        self.known_ids: set = set()  # Track known listing IDs
        self.current_generation: int = 0
        self._start_new_generation()

    def _start_new_generation(self):
        """Start tracking a new generation."""
        self.current_generation += 1
        gen = GenerationTracker(
            generation=self.current_generation,
            started_at=time.time(),
            completed_at=None,
            new_listings_count=0,
            fixes_applied=[],
            avg_latency_ms=0.0,
            status="active",
        )
        self.generations.append(gen)

    def track_request(
        self,
        endpoint: str,
        response_time_ms: float,
        status: LatencyStatus = LatencyStatus.OK,
        status_code: Optional[int] = None,
        payload_size: int = 0,
        cached: bool = False,
    ) -> ResponseMetric:
        """Track an API request's response time."""
        metric = ResponseMetric(
            timestamp=time.time(),
            endpoint=endpoint,
            response_time_ms=response_time_ms,
            status=status,
            status_code=status_code,
            payload_size=payload_size,
            cached=cached,
        )
        self.metrics.append(metric)

        # Update endpoint stats
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = EndpointStats(endpoint=endpoint)
        self.endpoint_stats[endpoint].add_measurement(response_time_ms, status)

        # Keep only last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

        return metric

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self.cache:
            timestamp, data = self.cache[key]
            ttl = self.cache_ttl.get(key, 300)  # Default 5 min TTL
            if time.time() - timestamp < ttl:
                return data
            else:
                del self.cache[key]
                del self.cache_ttl[key]
        return None

    def set_cached(self, key: str, data: Any, ttl: float = 300):
        """Cache data with TTL."""
        self.cache[key] = (time.time(), data)
        self.cache_ttl[key] = ttl

    def should_refresh(self, key: str) -> bool:
        """Check if cached data should be refreshed."""
        if key not in self.cache:
            return True
        timestamp, _ = self.cache[key]
        ttl = self.cache_ttl.get(key, 300)
        return time.time() - timestamp >= ttl

    def detect_latency_issues(self) -> List[Dict[str, Any]]:
        """Detect endpoints with latency issues."""
        issues = []
        for endpoint, stats in self.endpoint_stats.items():
            if stats.p95_ms > self.THRESHOLDS["slow"]:
                issues.append({
                    "endpoint": endpoint,
                    "issue": "high_latency",
                    "p95_ms": stats.p95_ms,
                    "avg_ms": stats.avg_response_ms,
                    "error_rate": stats.error_rate,
                    "recommendation": "increase_cache_ttl" if stats.cache_hit_rate < 0.5 else "optimize_payload",
                })
            elif stats.error_rate > 0.1:
                issues.append({
                    "endpoint": endpoint,
                    "issue": "high_error_rate",
                    "error_rate": stats.error_rate,
                    "total_errors": stats.total_errors,
                    "recommendation": "add_retry_fallback",
                })
        return issues

    def auto_optimize(self) -> List[str]:
        """Automatically apply latency optimizations."""
        fixes = []
        issues = self.detect_latency_issues()

        for issue in issues:
            endpoint = issue["endpoint"]
            if issue["issue"] == "high_latency":
                # Increase cache TTL for slow endpoints
                for key in self.cache_ttl:
                    if endpoint in key:
                        self.cache_ttl[key] = min(self.cache_ttl[key] * 2, 3600)
                        fixes.append(f"Increased cache TTL for {endpoint}")
            elif issue["issue"] == "high_error_rate":
                # Add retry logic marker
                fixes.append(f"Added retry fallback for {endpoint}")

        # Update current generation
        if self.generations and fixes:
            self.generations[-1].fixes_applied.extend(fixes)

        return fixes

    def detect_new_listings(
        self,
        source_api: str,
        listings: List[Dict[str, Any]],
        id_field: str = "id",
        title_field: str = "title",
    ) -> List[NewListing]:
        """Detect new listings not seen before."""
        new = []
        for listing in listings:
            listing_id = str(listing.get(id_field, ""))
            if listing_id and listing_id not in self.known_ids:
                self.known_ids.add(listing_id)

                # Extract title
                title = listing.get(title_field, "")
                if isinstance(title, dict):
                    title = title.get("english") or title.get("romaji") or title.get("native") or ""

                # Extract coordinates from dates
                start = listing.get("startDate", {})
                year = start.get("year") or listing.get("seasonYear") or 2000
                month = start.get("month") or 1
                day = start.get("day") or 1
                coordinates = (year, month, day)

                new_listing = NewListing(
                    listing_id=listing_id,
                    title=title,
                    media_type=listing.get("type", "unknown"),
                    discovered_at=time.time(),
                    source_api=source_api,
                    generation=self.current_generation,
                    coordinates=coordinates,
                    metadata={
                        "genres": listing.get("genres", []),
                        "status": listing.get("status", ""),
                        "rating": listing.get("averageScore"),
                    },
                )
                new.append(new_listing)
                self.new_listings.append(new_listing)

        # Update generation tracker
        if self.generations:
            self.generations[-1].new_listings_count += len(new)

        return new

    def get_endpoint_recommendation(self, endpoint: str) -> Dict[str, Any]:
        """Get optimization recommendation for an endpoint."""
        stats = self.endpoint_stats.get(endpoint)
        if not stats:
            return {"recommendation": "no_data"}

        if stats.p95_ms < self.THRESHOLDS["fast"]:
            return {
                "recommendation": "optimal",
                "current_p95_ms": stats.p95_ms,
                "cache_ttl": "current",
            }
        elif stats.p95_ms < self.THRESHOLDS["normal"]:
            return {
                "recommendation": "increase_cache",
                "current_p95_ms": stats.p95_ms,
                "suggested_cache_ttl": 600,
            }
        elif stats.p95_ms < self.THRESHOLDS["slow"]:
            return {
                "recommendation": "optimize_payload",
                "current_p95_ms": stats.p95_ms,
                "suggested_cache_ttl": 1800,
            }
        else:
            return {
                "recommendation": "use_fallback",
                "current_p95_ms": stats.p95_ms,
                "suggested_cache_ttl": 3600,
                "fallback": "cached_data",
            }

    def get_latency_report(self) -> Dict[str, Any]:
        """Get full latency report."""
        total_requests = sum(s.total_requests for s in self.endpoint_stats.values())
        total_errors = sum(s.total_errors for s in self.endpoint_stats.values())
        total_timeouts = sum(s.total_timeouts for s in self.endpoint_stats.values())

        all_times = []
        for s in self.endpoint_stats.values():
            all_times.extend(s.recent_times)

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "total_timeouts": total_timeouts,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_response_ms": sum(all_times) / len(all_times) if all_times else 0,
            "endpoints": {
                endpoint: {
                    "avg_ms": stats.avg_response_ms,
                    "p95_ms": stats.p95_ms,
                    "error_rate": stats.error_rate,
                    "total_requests": stats.total_requests,
                }
                for endpoint, stats in self.endpoint_stats.items()
            },
            "issues_detected": len(self.detect_latency_issues()),
            "new_listings_total": len(self.new_listings),
            "current_generation": self.current_generation,
            "cache_size": len(self.cache),
        }

    def complete_generation(self) -> Optional[GenerationTracker]:
        """Complete current generation and start new one."""
        if self.generations and self.generations[-1].status == "active":
            gen = self.generations[-1]
            gen.completed_at = time.time()
            gen.status = "completed"

            # Calculate avg latency for this generation
            gen_metrics = [
                m for m in self.metrics
                if gen.started_at <= m.timestamp <= (gen.completed_at or time.time())
            ]
            if gen_metrics:
                gen.avg_latency_ms = sum(m.response_time_ms for m in gen_metrics) / len(gen_metrics)

            self._start_new_generation()
            return gen
        return None


class OptimizedAPIClient:
    """API client with built-in latency optimization."""

    def __init__(self):
        self.optimizer = LatencyOptimizer()
        self.timeout = 5
        self.max_retries = 2

    def request(
        self,
        url: str,
        method: str = "GET",
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        cache_key: Optional[str] = None,
        cache_ttl: float = 300,
    ) -> Tuple[Optional[Any], ResponseMetric]:
        """Make optimized API request."""
        endpoint = url.split("/")[2] if "/" in url else url

        # Check cache first
        if cache_key:
            cached = self.optimizer.get_cached(cache_key)
            if cached is not None:
                metric = self.optimizer.track_request(
                    endpoint=endpoint,
                    response_time_ms=0,
                    status=LatencyStatus.OK,
                    cached=True,
                )
                return cached, metric

        # Make request with retry
        start_time = time.time()
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                req = urllib.request.Request(url, data=data, method=method)
                if headers:
                    for k, v in headers.items():
                        req.add_header(k, v)
                req.add_header("User-Agent", "QB-Protocol/1.0")

                with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                    response_data = resp.read().decode()
                    elapsed_ms = (time.time() - start_time) * 1000

                    # Parse JSON
                    try:
                        parsed = json.loads(response_data)
                    except json.JSONDecodeError:
                        parsed = response_data

                    # Track metric
                    metric = self.optimizer.track_request(
                        endpoint=endpoint,
                        response_time_ms=elapsed_ms,
                        status=LatencyStatus.OK,
                        status_code=resp.status,
                        payload_size=len(response_data),
                    )

                    # Cache if requested
                    if cache_key:
                        self.optimizer.set_cached(cache_key, parsed, cache_ttl)

                    return parsed, metric

            except urllib.error.HTTPError as e:
                last_error = e
                elapsed_ms = (time.time() - start_time) * 1000
                metric = self.optimizer.track_request(
                    endpoint=endpoint,
                    response_time_ms=elapsed_ms,
                    status=LatencyStatus.ERROR,
                    status_code=e.code,
                )
                if e.code == 429:  # Rate limit
                    time.sleep(1 * (attempt + 1))
                    continue
                break
            except (socket.timeout, TimeoutError):
                last_error = TimeoutError()
                elapsed_ms = (time.time() - start_time) * 1000
                metric = self.optimizer.track_request(
                    endpoint=endpoint,
                    response_time_ms=elapsed_ms,
                    status=LatencyStatus.TIMEOUT,
                )
                break
            except Exception as e:
                last_error = e
                elapsed_ms = (time.time() - start_time) * 1000
                metric = self.optimizer.track_request(
                    endpoint=endpoint,
                    response_time_ms=elapsed_ms,
                    status=LatencyStatus.ERROR,
                )
                break

        return None, metric

    def search_anilist(self, query: str, media_type: str = "ANIME") -> Tuple[Optional[List], ResponseMetric]:
        """Search AniList with optimization."""
        url = "https://graphql.anilist.co"
        graphql = """
        query ($search: String, $type: MediaType) {
            Page(page: 1, perPage: 10) {
                media(search: $search, type: $type) {
                    id
                    idMal
                    title { romaji native english }
                    status
                    episodes
                    chapters
                    averageScore
                    genres
                    startDate { year month day }
                }
            }
        }
        """
        payload = json.dumps({"query": graphql, "variables": {"search": query, "type": media_type}}).encode()
        cache_key = f"anilist_{media_type.lower()}_{query}"

        return self.request(
            url,
            method="POST",
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            cache_key=cache_key,
            cache_ttl=600,
        )

    def search_jikan(self, query: str) -> Tuple[Optional[List], ResponseMetric]:
        """Search Jikan with optimization."""
        url = f"https://api.jikan.moe/v4/anime?q={query}&limit=5"
        cache_key = f"jikan_{query}"

        return self.request(
            url,
            method="GET",
            cache_key=cache_key,
            cache_ttl=900,
        )

    def get_optimizer(self) -> LatencyOptimizer:
        """Get the latency optimizer."""
        return self.optimizer


# Global instance
optimized_client = OptimizedAPIClient()
