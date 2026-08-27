#!/usr/bin/env python3
"""
QB Protocol - Inbox, Messaging & Userland Integration

Full userland interactions with cross-proxy enabled:
- Inbox management (read, write, delete, reply)
- Cross-proxy routing for all users
- Platform-hosted server frontends
- Message threading and notifications

Platforms: Bluesky, Mastodon, Instagram, TikTok, Twitter/X, YouTube, Discord
"""

from __future__ import annotations

import json
import time
import hashlib
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class MessageType(Enum):
    TEXT = "text"
    MEDIA = "media"
    REPLY = "reply"
    MENTION = "mention"
    LIKE = "like"
    REPOST = "repost"
    FOLLOW = "follow"
    SYSTEM = "system"


class MessageStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"
    SENT = "sent"
    DRAFT = "draft"


class PlatformHost(Enum):
    BLUESKY = "bluesky"
    MASTODON = "mastodon"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    DISCORD = "discord"
    REDDIT = "reddit"


@dataclass
class Message:
    """A single message."""
    message_id: str
    platform: str
    thread_id: str
    author_id: str
    author_name: str
    content: str
    message_type: MessageType
    status: MessageStatus
    created_at: float
    updated_at: float
    reply_to: Optional[str] = None
    media_urls: List[str] = field(default_factory=list)
    reactions: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Thread:
    """A message thread/conversation."""
    thread_id: str
    platform: str
    participants: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0
    is_group: bool = False
    title: str = ""
    last_message_at: float = 0.0
    unread_count: int = 0

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def last_message(self) -> Optional[Message]:
        return self.messages[-1] if self.messages else None


@dataclass
class Inbox:
    """User inbox for a platform."""
    inbox_id: str
    platform: str
    user_id: str
    threads: Dict[str, Thread] = field(default_factory=dict)
    created_at: float = 0.0
    last_sync: float = 0.0

    @property
    def total_unread(self) -> int:
        return sum(t.unread_count for t in self.threads.values())

    @property
    def total_messages(self) -> int:
        return sum(t.message_count for t in self.threads.values())

    @property
    def thread_count(self) -> int:
        return len(self.threads)


@dataclass
class UserlandSession:
    """Full userland interaction session."""
    session_id: str
    user_id: str
    platform: str
    credential_id: str
    proxy_chain: List[str] = field(default_factory=list)
    inbox: Optional[Inbox] = None
    started_at: float = 0.0
    last_activity: float = 0.0
    is_active: bool = True
    permissions: List[str] = field(default_factory=lambda: ["read", "write", "delete", "reply"])
    rate_limit_remaining: int = 300
    geo_location: Optional[Dict[str, Any]] = None


class InboxManager:
    """Manages inboxes across all platforms."""

    def __init__(self):
        self.inboxes: Dict[str, Inbox] = {}
        self.threads: Dict[str, Thread] = {}
        self.messages: Dict[str, Message] = {}
        self.userland_sessions: Dict[str, UserlandSession] = {}

    def create_inbox(self, platform: str, user_id: str) -> Inbox:
        """Create a new inbox for a user on a platform."""
        inbox_id = f"inbox_{platform}_{user_id}_{int(time.time())}"
        inbox = Inbox(
            inbox_id=inbox_id,
            platform=platform,
            user_id=user_id,
            created_at=time.time(),
        )
        self.inboxes[inbox_id] = inbox
        return inbox

    def get_inbox(self, platform: str, user_id: str) -> Optional[Inbox]:
        """Get inbox by platform and user."""
        for inbox in self.inboxes.values():
            if inbox.platform == platform and inbox.user_id == user_id:
                return inbox
        return None

    def create_thread(self, platform: str, participants: List[str], title: str = "") -> Thread:
        """Create a new message thread."""
        thread_id = f"thread_{platform}_{uuid.uuid4().hex[:12]}"
        thread = Thread(
            thread_id=thread_id,
            platform=platform,
            participants=participants,
            created_at=time.time(),
            updated_at=time.time(),
            title=title,
            is_group=len(participants) > 2,
        )
        self.threads[thread_id] = thread
        return thread

    def add_message(
        self,
        thread_id: str,
        author_id: str,
        author_name: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        reply_to: Optional[str] = None,
        media_urls: List[str] = None,
    ) -> Optional[Message]:
        """Add a message to a thread."""
        thread = self.threads.get(thread_id)
        if not thread:
            return None

        message = Message(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            platform=thread.platform,
            thread_id=thread_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            message_type=message_type,
            status=MessageStatus.UNREAD,
            created_at=time.time(),
            updated_at=time.time(),
            reply_to=reply_to,
            media_urls=media_urls or [],
        )

        thread.messages.append(message)
        thread.updated_at = time.time()
        thread.last_message_at = time.time()
        thread.unread_count += 1
        self.messages[message.message_id] = message

        return message

    def mark_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        if message_id in self.messages:
            self.messages[message_id].status = MessageStatus.READ
            return True
        return False

    def delete_message(self, message_id: str) -> bool:
        """Delete a message."""
        if message_id in self.messages:
            self.messages[message_id].status = MessageStatus.DELETED
            return True
        return False

    def get_thread_messages(self, thread_id: str, limit: int = 50) -> List[Message]:
        """Get messages in a thread."""
        thread = self.threads.get(thread_id)
        if not thread:
            return []
        return thread.messages[-limit:]

    def get_unread_threads(self, platform: str, user_id: str) -> List[Thread]:
        """Get all unread threads for a user."""
        inbox = self.get_inbox(platform, user_id)
        if not inbox:
            return []
        return [t for t in inbox.threads.values() if t.unread_count > 0]


class CrossProxyRouter:
    """Routes userland interactions through cross-proxy connections."""

    def __init__(self):
        self.proxy_pools: Dict[str, List[str]] = {}
        self.routing_table: Dict[str, str] = {}
        self.geo_proxy_map: Dict[str, List[str]] = {
            "US": ["proxy_us_east", "proxy_us_west"],
            "EU": ["proxy_eu_west", "proxy_eu_east"],
            "ASIA": ["proxy_asia", "proxy_jp"],
        }

    def register_proxy_pool(self, platform: str, proxies: List[str]):
        """Register a pool of proxies for a platform."""
        self.proxy_pools[platform] = proxies

    def get_route(self, platform: str, user_geo: str) -> List[str]:
        """Get optimal proxy route for a platform based on user geo."""
        # Get platform-specific proxies
        platform_proxies = self.proxy_pools.get(platform, [])
        
        # Get geo-optimized proxies
        geo_proxies = self.geo_proxy_map.get(user_geo, [])
        
        # Combine and deduplicate
        route = list(dict.fromkeys(platform_proxies + geo_proxies))
        return route if route else ["direct"]

    def rotate_proxy(self, platform: str, current_proxy: str) -> str:
        """Rotate to next proxy in pool."""
        proxies = self.proxy_pools.get(platform, [])
        if not proxies:
            return "direct"
        try:
            idx = proxies.index(current_proxy)
            return proxies[(idx + 1) % len(proxies)]
        except ValueError:
            return proxies[0]


class PlatformFrontendHost:
    """Hosts platform-specific server frontends."""

    FRONTEND_CONFIG = {
        "bluesky": {
            "port": 8081,
            "host": "0.0.0.0",
            "api_base": "https://public.api.bsky.app/xrpc",
            "features": ["feed", "post", "reply", "like", "repost", "follow", "notifications"],
        },
        "mastodon": {
            "port": 8082,
            "host": "0.0.0.0",
            "api_base": "https://mstdn.social/api/v1",
            "features": ["timeline", "post", "reply", "boost", "favourite", "follow", "notifications"],
        },
        "instagram": {
            "port": 8083,
            "host": "0.0.0.0",
            "api_base": "https://graph.instagram.com/me",
            "features": ["feed", "post", "story", "reply", "like", "dm", "notifications"],
        },
        "tiktok": {
            "port": 8084,
            "host": "0.0.0.0",
            "api_base": "https://open.tiktokapis.com/v2",
            "features": ["feed", "post", "reply", "like", "follow", "notifications"],
        },
        "twitter": {
            "port": 8085,
            "host": "0.0.0.0",
            "api_base": "https://api.twitter.com/2",
            "features": ["timeline", "tweet", "reply", "retweet", "like", "follow", "dm", "notifications"],
        },
        "youtube": {
            "port": 8086,
            "host": "0.0.0.0",
            "api_base": "https://www.googleapis.com/youtube/v3",
            "features": ["feed", "comment", "like", "subscribe", "notifications"],
        },
        "discord": {
            "port": 8087,
            "host": "0.0.0.0",
            "api_base": "https://discord.com/api/v9",
            "features": ["channels", "messages", "reactions", "voice", "notifications"],
        },
    }

    def __init__(self):
        self.active_frontends: Dict[str, Dict[str, Any]] = {}

    def start_frontend(self, platform: str) -> Dict[str, Any]:
        """Start a platform frontend."""
        if platform not in self.FRONTEND_CONFIG:
            return {"error": f"Unknown platform: {platform}"}

        config = self.FRONTEND_CONFIG[platform]
        self.active_frontends[platform] = {
            **config,
            "status": "running",
            "started_at": time.time(),
            "requests_served": 0,
        }

        return {
            "platform": platform,
            "status": "running",
            "url": f"http://{config['host']}:{config['port']}",
            "features": config["features"],
        }

    def stop_frontend(self, platform: str) -> bool:
        """Stop a platform frontend."""
        if platform in self.active_frontends:
            self.active_frontends[platform]["status"] = "stopped"
            return True
        return False

    def get_frontend(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get frontend status."""
        return self.active_frontends.get(platform)

    def get_all_frontends(self) -> Dict[str, Any]:
        """Get all frontend statuses."""
        return {
            platform: {
                "status": info["status"],
                "url": f"http://{info['host']}:{info['port']}",
                "features": info["features"],
                "requests_served": info["requests_served"],
            }
            for platform, info in self.active_frontends.items()
        }


class UserlandInteractionManager:
    """Manages full userland interactions for all users."""

    def __init__(self):
        self.inbox_manager = InboxManager()
        self.proxy_router = CrossProxyRouter()
        self.frontend_host = PlatformFrontendHost()
        self.active_sessions: Dict[str, UserlandSession] = {}

    def start_session(
        self,
        user_id: str,
        platform: str,
        credential_id: str,
        user_geo: str = "US",
    ) -> UserlandSession:
        """Start a full userland interaction session."""
        session_id = f"userland_{platform}_{user_id}_{int(time.time())}"

        # Get proxy route
        proxy_chain = self.proxy_router.get_route(platform, user_geo)

        # Create inbox
        inbox = self.inbox_manager.create_inbox(platform, user_id)

        session = UserlandSession(
            session_id=session_id,
            user_id=user_id,
            platform=platform,
            credential_id=credential_id,
            proxy_chain=proxy_chain,
            inbox=inbox,
            started_at=time.time(),
            last_activity=time.time(),
            geo_location={"country": user_geo},
        )

        self.active_sessions[session_id] = session
        return session

    def send_message(
        self,
        session_id: str,
        thread_id: str,
        content: str,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message in a thread."""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            return {"error": "Invalid session"}

        if "write" not in session.permissions:
            return {"error": "No write permission"}

        # Add message
        message = self.inbox_manager.add_message(
            thread_id=thread_id,
            author_id=session.user_id,
            author_name=session.user_id,
            content=content,
            reply_to=reply_to,
        )

        if message:
            session.last_activity = time.time()
            session.requests_made += 1 if hasattr(session, 'requests_made') else 1
            return {
                "message_id": message.message_id,
                "status": "sent",
                "proxy_used": session.proxy_chain,
            }

        return {"error": "Failed to send message"}

    def read_inbox(self, session_id: str) -> Dict[str, Any]:
        """Read inbox for a session."""
        session = self.active_sessions.get(session_id)
        if not session or not session.inbox:
            return {"error": "Invalid session"}

        inbox = session.inbox
        return {
            "inbox_id": inbox.inbox_id,
            "platform": inbox.platform,
            "total_unread": inbox.total_unread,
            "total_messages": inbox.total_messages,
            "thread_count": inbox.thread_count,
            "threads": [
                {
                    "thread_id": t.thread_id,
                    "title": t.title,
                    "message_count": t.message_count,
                    "unread_count": t.unread_count,
                    "last_message": t.last_message.content[:100] if t.last_message else "",
                }
                for t in inbox.threads.values()
            ],
        }

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics."""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Invalid session"}

        return {
            "session_id": session.session_id,
            "platform": session.platform,
            "user_id": session.user_id,
            "is_active": session.is_active,
            "proxy_chain": session.proxy_chain,
            "permissions": session.permissions,
            "started_at": session.started_at,
            "last_activity": session.last_activity,
            "duration_seconds": time.time() - session.started_at,
        }

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        return [
            {
                "session_id": s.session_id,
                "platform": s.platform,
                "user_id": s.user_id,
                "is_active": s.is_active,
                "proxy_chain": s.proxy_chain,
            }
            for s in self.active_sessions.values()
        ]


# Global instance
userland_manager = UserlandInteractionManager()
