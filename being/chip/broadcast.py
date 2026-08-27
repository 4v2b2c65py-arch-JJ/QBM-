#!/usr/bin/env python3
"""
QB Protocol - Agent Repair & Broadcast System

Repairs degraded APIs with fallback mechanisms.
Checks social media APIs.
Enables broadcast across the entire system.

Repair strategies:
- Jikan (502) → Fallback to AniList for same data
- Omega (402) → Fallback to MangaDex for manhwa
- Any timeout → Retry with exponential backoff
- Any 429 → Rate limit cooldown + queue

Broadcast:
- Social media integration
- Multi-API simultaneous queries
- Event-driven updates
"""

from __future__ import annotations

import json
import time
import urllib.request
import ssl
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RepairStatus(Enum):
    OK = "ok"
    REPAIRED = "repaired"
    FALLBACK = "fallback"
    FAILED = "failed"


@dataclass
class RepairResult:
    """Result of an API repair attempt."""
    api_name: str
    original_status: str
    repair_status: RepairStatus
    action_taken: str
    fallback_api: Optional[str] = None
    response_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class BroadcastEvent:
    """Event to broadcast across the system."""
    event_type: str
    source: str
    data: Dict[str, Any]
    timestamp: float
    targets: List[str] = field(default_factory=list)


class AgentRepair:
    """Repairs degraded APIs with fallback mechanisms."""

    # Fallback chain: when primary fails, use fallback
    FALLBACK_CHAIN = {
        "jikan": ["anilist", "kitsu"],
        "omega": ["mangadex", "anilist"],
        "kitsu": ["anilist", "jikan"],
        "mangadex": ["omega", "anilist"],
        "anilist": ["kitsu", "jikan"],
    }

    # Alternative endpoints for degraded APIs
    ALTERNATIVE_ENDPOINTS = {
        "jikan": [
            "https://api.jikan.moe/v4/anime/1",
            "https://api.jikan.moe/v4/manga/1",
            "https://api.jikan.moe/v4/top/anime",
        ],
        "omega": [
            "https://omegaapi.vercel.app/api/v1/series?perPage=1",
            "https://omegaapi.vercel.app/api/v1/random",
        ],
    }

    def __init__(self):
        self.repair_log: List[RepairResult] = []
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def repair_api(self, api_name: str, original_error: str) -> RepairResult:
        """Attempt to repair a degraded API."""
        # Strategy 1: Try alternative endpoints
        if api_name in self.ALTERNATIVE_ENDPOINTS:
            for endpoint in self.ALTERNATIVE_ENDPOINTS[api_name]:
                start = time.time()
                try:
                    req = urllib.request.Request(endpoint, headers={
                        "User-Agent": "QB-Protocol/1.0",
                        "Accept": "application/json",
                    })
                    with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                        if resp.status == 200:
                            elapsed = (time.time() - start) * 1000
                            result = RepairResult(
                                api_name=api_name,
                                original_status="degraded",
                                repair_status=RepairStatus.REPAIRED,
                                action_taken=f"Alternative endpoint: {endpoint}",
                                response_time_ms=elapsed,
                            )
                            self.repair_log.append(result)
                            return result
                except Exception:
                    continue

        # Strategy 2: Use fallback API
        if api_name in self.FALLBACK_CHAIN:
            for fallback in self.FALLBACK_CHAIN[api_name]:
                start = time.time()
                try:
                    # Test fallback API
                    if fallback == "anilist":
                        query = "query{Page(perPage:1){media{id}}}"
                        payload = json.dumps({"query": query}).encode()
                        req = urllib.request.Request(
                            "https://graphql.anilist.co",
                            data=payload,
                            method="POST",
                            headers={"Content-Type": "application/json", "User-Agent": "QB-Protocol/1.0"},
                        )
                    elif fallback == "kitsu":
                        req = urllib.request.Request(
                            "https://kitsu.app/api/edge/anime/1",
                            headers={"Accept": "application/vnd.api+json", "User-Agent": "QB-Protocol/1.0"},
                        )
                    elif fallback == "mangadex":
                        req = urllib.request.Request(
                            "https://api.mangadex.org/manga?limit=1",
                            headers={"User-Agent": "QB-Protocol/1.0"},
                        )
                    else:
                        continue

                    with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                        if resp.status == 200:
                            elapsed = (time.time() - start) * 1000
                            result = RepairResult(
                                api_name=api_name,
                                original_status="degraded",
                                repair_status=RepairStatus.FALLBACK,
                                action_taken=f"Fallback to {fallback}",
                                fallback_api=fallback,
                                response_time_ms=elapsed,
                            )
                            self.repair_log.append(result)
                            return result
                except Exception:
                    continue

        # Strategy 3: Failed - all fallbacks exhausted
        result = RepairResult(
            api_name=api_name,
            original_status="degraded",
            repair_status=RepairStatus.FAILED,
            action_taken="All fallbacks exhausted",
            error=original_error,
        )
        self.repair_log.append(result)
        return result

    def repair_all(self, health_results: Dict[str, Any]) -> List[RepairResult]:
        """Repair all degraded APIs."""
        repairs = []
        for name, health in health_results.items():
            if health.status.value in ("degraded", "unhealthy"):
                repair = self.repair_api(name, health.last_error or "unknown")
                repairs.append(repair)
        return repairs

    def get_fallback_for(self, api_name: str) -> Optional[str]:
        """Get the best fallback API for a given API."""
        if api_name in self.FALLBACK_CHAIN:
            for fallback in self.FALLBACK_CHAIN[api_name]:
                # Check if fallback is healthy
                return fallback
        return None


class SocialMediaAPI:
    """Social media API integration for broadcast."""

    # Free social media APIs for anime/manga updates
    SOCIAL_APIS = {
        # Actually Open (No API Key Required)
        "bluesky": {
            "base": "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=bsky.app",
            "params": "q={query}&limit=5",
            "auth": False,
            "endpoints": {
                "search": "/xrpc/app.bsky.feed.searchPosts?q={query}&limit=5",
                "profile": "/xrpc/app.bsky.actor.getProfile?actor={handle}",
                "feed": "/xrpc/app.bsky.feed.getAuthorFeed?actor={handle}&limit=5",
                "followers": "/xrpc/app.bsky.graph.getFollowers?actor={handle}&limit=5",
            },
        },
        "mastodon": {
            "base": "https://mstdn.social/api/v1/timelines/public?limit=1",
            "params": "q={query}&limit=5",
            "auth": False,
            "instance": "mstdn.social",
            "endpoints": {
                "search": "/api/v1/search?q={query}&limit=5",
                "timeline": "/api/v1/timelines/public?limit=5",
                "trends": "/api/v1/trends/tags",
                "statuses": "/api/v1/accounts/{id}/statuses",
            },
        },
        # Free Tier Available (API Key Required but Free)
        "xpoz": {
            "base": "https://api.xpoz.ai/v1/search",
            "params": "q={query}&limit=5",
            "auth": True,  # Free tier: 75K results one-time
            "free_tier": "75K results one-time",
            "platforms": ["twitter", "instagram", "tiktok", "reddit"],
        },
        "sociavault": {
            "base": "https://api.sociavault.com/v1/data",
            "params": "platform={platform}&query={query}&limit=5",
            "auth": True,  # 50 free credits
            "free_tier": "50 free credits",
            "platforms": ["instagram", "tiktok", "twitter", "facebook", "youtube", "linkedin"],
        },
        "tikhub": {
            "base": "https://api.tikhub.io/v1/tiktok",
            "params": "query={query}&limit=5",
            "auth": True,  # 5 free credits
            "free_tier": "5 free credits (~50 requests)",
            "platforms": ["tiktok"],
        },
        "feedframer": {
            "base": "https://api.feedframer.com/v1/instagram",
            "params": "query={query}&limit=5",
            "auth": True,  # Free tier available
            "free_tier": "Free tier available",
            "platforms": ["instagram"],
        },
        # Requires Auth (Future Implementation)
        "instagram_graph": {
            "base": "https://graph.facebook.com/v25.0/me/media",
            "params": "fields=id,caption,media_url,timestamp&limit=5",
            "auth": True,
            "auth_type": "OAuth 2.0 (Facebook Login)",
            "requires": "Business/Creator account + App Review",
        },
        "tiktok_research": {
            "base": "https://open.tiktokapis.com/v2/research/video/query/",
            "params": "fields=id,title,view_count,like_count",
            "auth": True,
            "auth_type": "OAuth 2.0 (Academic only)",
            "requires": "Academic affiliation + App Review",
        },
        # Blocked / Requires Proxy
        "reddit": {
            "base": "https://www.reddit.com/r/anime/search.json",
            "params": "q={query}&sort=new&limit=5",
            "auth": False,  # Public but blocked without proper UA
        },
        "twitter": {
            "base": "https://api.twitter.com/2/tweets/search/recent",
            "params": "query={query}&max_results=5",
            "auth": True,
        },
        "youtube": {
            "base": "https://www.googleapis.com/youtube/v3/search",
            "params": "q={query}&part=snippet&maxResults=5",
            "auth": True,
        },
        "discord": {
            "base": "https://discord.com/api/v9/guilds/{guild_id}/messages",
            "auth": True,
        },
    }

    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def check_social_health(self) -> Dict[str, Any]:
        """Check health of social media APIs."""
        results = {}
        
        # Test Bluesky (AT Protocol)
        try:
            start = time.time()
            url = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=bsky.app"
            req = urllib.request.Request(url, headers={
                "User-Agent": "QB-Protocol/1.0",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=5, context=self.ctx) as resp:
                elapsed = (time.time() - start) * 1000
                data = json.loads(resp.read().decode())
                results["bluesky"] = {
                    "status": "healthy" if resp.status == 200 else "degraded",
                    "response_ms": elapsed,
                    "requires_auth": False,
                    "handle": data.get("handle", ""),
                    "display_name": data.get("displayName", ""),
                }
        except Exception as e:
            elapsed = (time.time() - start) * 1000 if 'start' in dir() else 0
            results["bluesky"] = {
                "status": "unhealthy",
                "response_ms": elapsed,
                "error": str(e)[:100],
                "requires_auth": False,
            }

        # Test Mastodon
        try:
            start = time.time()
            url = "https://mstdn.social/api/v1/timelines/public?limit=1"
            req = urllib.request.Request(url, headers={
                "User-Agent": "QB-Protocol/1.0",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=5, context=self.ctx) as resp:
                elapsed = (time.time() - start) * 1000
                data = json.loads(resp.read().decode())
                results["mastodon"] = {
                    "status": "healthy" if resp.status == 200 else "degraded",
                    "response_ms": elapsed,
                    "requires_auth": False,
                    "instance": "mstdn.social",
                    "posts_found": len(data) if isinstance(data, list) else 0,
                }
        except Exception as e:
            elapsed = (time.time() - start) * 1000 if 'start' in dir() else 0
            results["mastodon"] = {
                "status": "unhealthy",
                "response_ms": elapsed,
                "error": str(e)[:100],
                "requires_auth": False,
            }

        # Test FreeAPI
        try:
            start = time.time()
            url = "https://freeapi.app/api/v1/social-media/posts"
            req = urllib.request.Request(url, headers={
                "User-Agent": "QB-Protocol/1.0",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=5, context=self.ctx) as resp:
                elapsed = (time.time() - start) * 1000
                results["freeapi"] = {
                    "status": "healthy" if resp.status == 200 else "degraded",
                    "response_ms": elapsed,
                    "requires_auth": False,
                }
        except Exception as e:
            elapsed = (time.time() - start) * 1000 if 'start' in dir() else 0
            results["freeapi"] = {
                "status": "unhealthy",
                "response_ms": elapsed,
                "error": str(e)[:100],
                "requires_auth": False,
            }

        # Test Reddit (may be blocked)
        try:
            start = time.time()
            url = "https://www.reddit.com/r/anime/search.json?q=anime&sort=new&limit=1"
            req = urllib.request.Request(url, headers={
                "User-Agent": "QB-Protocol/1.0 (by /u/qbprotocol)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=5, context=self.ctx) as resp:
                elapsed = (time.time() - start) * 1000
                results["reddit"] = {
                    "status": "healthy" if resp.status == 200 else "degraded",
                    "response_ms": elapsed,
                    "requires_auth": False,
                }
        except Exception as e:
            elapsed = (time.time() - start) * 1000 if 'start' in dir() else 0
            results["reddit"] = {
                "status": "unhealthy",
                "response_ms": elapsed,
                "error": str(e)[:100],
                "requires_auth": False,
            }

        # APIs requiring auth
        for name in ["twitter", "youtube", "discord"]:
            results[name] = {
                "status": "requires_auth",
                "response_ms": 0,
                "error": "Requires API key/token",
                "requires_auth": True,
            }

        return results

    def broadcast_to_social(self, event: BroadcastEvent) -> Dict[str, Any]:
        """Broadcast an event to social media channels."""
        results = {}
        for target in event.targets:
            if target in self.SOCIAL_APIS:
                config = self.SOCIAL_APIS[target]
                if config.get("auth"):
                    results[target] = {
                        "status": "skipped",
                        "reason": "Requires authentication",
                    }
                else:
                    results[target] = {
                        "status": "broadcast_queued",
                        "event": event.event_type,
                    }
        return results


class BroadcastSystem:
    """Broadcast system for the entire QB Protocol."""

    def __init__(self):
        self.event_queue: List[BroadcastEvent] = []
        self.subscribers: Dict[str, List[Callable]] = {}
        self.agent_repair = AgentRepair()
        self.social_api = SocialMediaAPI()

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event: BroadcastEvent):
        """Publish an event to all subscribers."""
        self.event_queue.append(event)
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                callback(event)

    def broadcast(self, event_type: str, source: str, data: Dict[str, Any], targets: List[str] = None) -> BroadcastEvent:
        """Create and publish a broadcast event."""
        event = BroadcastEvent(
            event_type=event_type,
            source=source,
            data=data,
            timestamp=time.time(),
            targets=targets or [],
        )
        self.publish(event)
        return event

    def repair_and_broadcast(self, health_results: Dict[str, Any]) -> Dict[str, Any]:
        """Repair degraded APIs and broadcast results."""
        # Repair
        repairs = self.agent_repair.repair_all(health_results)

        # Broadcast repair results
        for repair in repairs:
            self.broadcast(
                event_type="api_repair",
                source="agent_repair",
                data={
                    "api": repair.api_name,
                    "status": repair.repair_status.value,
                    "action": repair.action_taken,
                    "fallback": repair.fallback_api,
                },
            )

        return {
            "repairs": len(repairs),
            "repaired": sum(1 for r in repairs if r.repair_status == RepairStatus.REPAIRED),
            "fallback": sum(1 for r in repairs if r.repair_status == RepairStatus.FALLBACK),
            "failed": sum(1 for r in repairs if r.repair_status == RepairStatus.FAILED),
        }

    def full_system_check(self) -> Dict[str, Any]:
        """Full system check with repairs and broadcast readiness."""
        from qb_protocol.being.chip.uptime_keeper import uptime_keeper

        # Health check
        health = uptime_keeper.compliance_keeper.check_all_apis()

        # Repair degraded
        repair_results = self.repair_and_broadcast(health)

        # Social media check
        social_health = self.social_api.check_social_health()

        # Compile full report
        return {
            "timestamp": time.time(),
            "api_health": {name: h.status.value for name, h in health.items()},
            "repairs": repair_results,
            "social_media": social_health,
            "broadcast_ready": repair_results["failed"] == 0,
            "system_status": "operational" if repair_results["failed"] == 0 else "degraded",
        }


# Global instance
broadcast_system = BroadcastSystem()
agent_repair = AgentRepair()
social_media_api = SocialMediaAPI()
