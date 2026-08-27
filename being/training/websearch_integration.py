#!/usr/bin/env python3
"""
QB Protocol - Websearch Integration for Manga/Manhwa Metadata

Fetches metadata from free APIs:
- Jikan REST API (MyAnimeList)
- AniList GraphQL API
- Kitsu API
- MangaDex API
- OmegaAPI (Manga & Manhwa)

Provides quality coordinate cookies for the transit system.
"""

from __future__ import annotations

import json
import socket
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MangaMetadata:
    title: str
    author: str
    year: int
    status: str
    chapters: Optional[int]
    volumes: Optional[int]
    synopsis: str
    rating: float
    genres: List[str]
    cover_image: str
    source_api: str
    source_url: str
    coordinates: tuple = ()


@dataclass
class ManhwaMetadata:
    title: str
    author: str
    year: int
    status: str
    chapters: Optional[int]
    synopsis: str
    rating: float
    genres: List[str]
    cover_image: str
    source_api: str
    source_url: str
    coordinates: tuple = ()


@dataclass
class CoordinateCookies:
    """Quality coordinate cookies for transit system."""
    universe_id: str
    title: str
    coordinates: tuple
    metadata: Dict[str, Any]
    ping_ms: float
    life_status: str
    atmosphere: str
    gravity: float
    reachable: bool
    category: str


class WebSearchAPI:
    """Fetch metadata from free manga/manhwa APIs."""

    API_ENDPOINTS = {
        "jikan": {
            "base_url": "api.jikan.moe",
            "port": 443,
            "path": "/v4/manga",
        },
        "kitsu": {
            "base_url": "kitsu.app",
            "port": 443,
            "path": "/api/edge/manga",
        },
        "omega": {
            "base_url": "omegaapi.vercel.app",
            "port": 443,
            "path": "/api/v1/series",
        },
    }

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.cache: Dict[str, Any] = {}

    def _http_get(self, host: str, port: int, path: str, use_ssl: bool = True) -> Optional[str]:
        """HTTP GET request."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((host, port))

            if use_ssl:
                import ssl
                ctx = ssl.create_default_context()
                sock = ctx.wrap_socket(sock, server_hostname=host)

            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nAccept: application/json\r\nConnection: close\r\n\r\n"
            sock.send(request.encode())

            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            sock.close()

            decoded = data.decode("utf-8", errors="replace")
            parts = decoded.split("\r\n\r\n", 1)
            if len(parts) > 1:
                return parts[1]
            return decoded
        except Exception:
            return None

    def search_jikan(self, query: str) -> Optional[Dict[str, Any]]:
        """Search manga via Jikan REST API."""
        cache_key = f"jikan:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        path = f"/v4/manga?q={query}&limit=5"
        result = self._http_get("api.jikan.moe", 443, path)
        if result:
            try:
                data = json.loads(result)
                self.cache[cache_key] = data
                return data
            except json.JSONDecodeError:
                return None
        return None

    def search_kitsu(self, query: str) -> Optional[Dict[str, Any]]:
        """Search manga via Kitsu API."""
        cache_key = f"kitsu:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        path = f"/api/edge/manga?filter[text]={query}&page[limit]=5"
        result = self._http_get("kitsu.app", 443, path)
        if result:
            try:
                data = json.loads(result)
                self.cache[cache_key] = data
                return data
            except json.JSONDecodeError:
                return None
        return None

    def search_omega(self, query: str) -> Optional[Dict[str, Any]]:
        """Search manhwa via OmegaAPI."""
        cache_key = f"omega:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        path = f"/api/v1/series?search={query}&perPage=5"
        result = self._http_get("omegaapi.vercel.app", 443, path)
        if result:
            try:
                data = json.loads(result)
                self.cache[cache_key] = data
                return data
            except json.JSONDecodeError:
                return None
        return None

    def get_omega_series(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get specific series from OmegaAPI."""
        cache_key = f"omega_series:{slug}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        path = f"/api/v1/series/{slug}?include=chapters"
        result = self._http_get("omegaapi.vercel.app", 443, path)
        if result:
            try:
                data = json.loads(result)
                self.cache[cache_key] = data
                return data
            except json.JSONDecodeError:
                return None
        return None

    def get_anilist(self, query: str) -> Optional[Dict[str, Any]]:
        """Search via AniList GraphQL API."""
        cache_key = f"anilist:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        graphql_query = """
        query ($search: String) {
            Page(page: 1, perPage: 5) {
                media(search: $search, type: MANGA) {
                    id
                    title { romaji native english }
                    description
                    status
                    chapters
                    volumes
                    averageScore
                    genres
                    coverImage { large medium }
                    startDate { year }
                    staff { nodes { name { full } } }
                }
            }
        }
        """

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect(("graphql.anilist.co", 443))

            import ssl
            ctx = ssl.create_default_context()
            sock = ctx.wrap_socket(sock, server_hostname="graphql.anilist.co")

            payload = json.dumps({"query": graphql_query, "variables": {"search": query}})
            request = f"POST / HTTP/1.1\r\nHost: graphql.anilist.co\r\nContent-Type: application/json\r\nContent-Length: {len(payload)}\r\nConnection: close\r\n\r\n{payload}"
            sock.send(request.encode())

            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            sock.close()

            decoded = data.decode("utf-8", errors="replace")
            parts = decoded.split("\r\n\r\n", 1)
            if len(parts) > 1:
                result = json.loads(parts[1])
                self.cache[cache_key] = result
                return result
        except Exception:
            return None

    def get_mangadex(self, query: str) -> Optional[Dict[str, Any]]:
        """Search via MangaDex API."""
        cache_key = f"mangadex:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        path = f"/manga?title={query}&limit=5&includes[]=author&includes[]=cover_art"
        result = self._http_get("api.mangadex.org", 443, path)
        if result:
            try:
                data = json.loads(result)
                self.cache[cache_key] = data
                return data
            except json.JSONDecodeError:
                return None
        return None


class CoordinateCookieGenerator:
    """Generate quality coordinate cookies from metadata."""

    def __init__(self):
        self.api = WebSearchAPI()

    def generate_manga_cookies(self, manga_entry: Dict[str, Any], universe_id: str) -> CoordinateCookies:
        """Generate coordinate cookies for a manga entry."""
        title = manga_entry.get("title", universe_id)
        coordinates = manga_entry.get("coordinates", (0, 0, 0))
        author = manga_entry.get("author", "Unknown")
        year = manga_entry.get("year", 2000)
        status = manga_entry.get("status", "unknown")
        chapters = manga_entry.get("chapters")
        volumes = manga_entry.get("volumes")

        # Generate ping from coordinates
        import math
        distance = math.sqrt(sum(c**2 for c in coordinates)) if coordinates else 0
        ping_ms = 1.0 + math.log10(distance + 1) * 50 if distance > 0 else 1.0

        metadata = {
            "author": author,
            "year": year,
            "status": status,
            "chapters": chapters,
            "volumes": volumes,
            "category": "manga",
        }

        return CoordinateCookies(
            universe_id=universe_id,
            title=title,
            coordinates=coordinates,
            metadata=metadata,
            ping_ms=ping_ms,
            life_status="confirmed",
            atmosphere="earth-like",
            gravity=1.0,
            reachable=True,
            category="manga",
        )

    def generate_manhwa_cookies(self, manhwa_entry: Dict[str, Any], universe_id: str) -> CoordinateCookies:
        """Generate coordinate cookies for a manhwa entry."""
        title = manhwa_entry.get("title", universe_id)
        coordinates = manhwa_entry.get("coordinates", (0, 0, 0))
        author = manhwa_entry.get("author", "Unknown")
        year = manhwa_entry.get("year", 2000)
        status = manhwa_entry.get("status", "unknown")
        chapters = manhwa_entry.get("chapters")

        import math
        distance = math.sqrt(sum(c**2 for c in coordinates)) if coordinates else 0
        ping_ms = 1.0 + math.log10(distance + 1) * 50 if distance > 0 else 1.0

        metadata = {
            "author": author,
            "year": year,
            "status": status,
            "chapters": chapters,
            "category": "manhwa",
        }

        return CoordinateCookies(
            universe_id=universe_id,
            title=title,
            coordinates=coordinates,
            metadata=metadata,
            ping_ms=ping_ms,
            life_status="confirmed",
            atmosphere="earth-like",
            gravity=1.0,
            reachable=True,
            category="manhwa",
        )

    def enrich_with_api_data(self, cookies: CoordinateCookies, query: str) -> CoordinateCookies:
        """Enrich coordinate cookies with live API data."""
        # Try multiple APIs
        api_data = None

        # Try AniList first (most comprehensive)
        api_data = self.api.get_anilist(query)
        if api_data and api_data.get("data", {}).get("Page", {}).get("media"):
            media = api_data["data"]["Page"]["media"][0]
            title_obj = media.get("title", {})
            cookies.title = title_obj.get("english") or title_obj.get("romaji") or cookies.title
            cookies.metadata["synopsis"] = media.get("description", "")[:200]
            cookies.metadata["rating"] = media.get("averageScore", 0)
            cookies.metadata["genres"] = media.get("genres", [])
            cookies.metadata["status"] = media.get("status", "").lower()
            cookies.metadata["chapters"] = media.get("chapters")
            cookies.metadata["volumes"] = media.get("volumes")
            cookies.metadata["source_api"] = "anilist"
            cover = media.get("coverImage", {})
            cookies.metadata["cover_image"] = cover.get("large", "")
            return cookies

        # Try Jikan (MyAnimeList)
        api_data = self.api.search_jikan(query)
        if api_data and api_data.get("data"):
            manga = api_data["data"][0]
            cookies.title = manga.get("title", cookies.title)
            cookies.metadata["synopsis"] = manga.get("synopsis", "")[:200]
            cookies.metadata["rating"] = manga.get("score", 0)
            cookies.metadata["status"] = manga.get("status", "").lower()
            cookies.metadata["chapters"] = manga.get("chapters")
            cookies.metadata["volumes"] = manga.get("volumes")
            cookies.metadata["source_api"] = "jikan"
            images = manga.get("images", {})
            jpg = images.get("jpg", {})
            cookies.metadata["cover_image"] = jpg.get("large_image_url", "")
            return cookies

        # Try OmegaAPI (manhwa focus)
        api_data = self.api.search_omega(query)
        if api_data and api_data.get("data"):
            series = api_data["data"][0]
            cookies.title = series.get("title", cookies.title)
            cookies.metadata["synopsis"] = series.get("description", "")[:200]
            cookies.metadata["rating"] = series.get("rating", 0)
            cookies.metadata["status"] = series.get("status", "").lower()
            cookies.metadata["chapters"] = series.get("chaptersCount")
            cookies.metadata["author"] = series.get("author", "")
            cookies.metadata["source_api"] = "omega"
            cookies.metadata["cover_image"] = series.get("cover", "")
            return cookies

        # Try MangaDex
        api_data = self.api.get_mangadex(query)
        if api_data and api_data.get("data"):
            manga = api_data["data"][0]
            title_obj = manga.get("attributes", {}).get("title", {})
            cookies.title = title_obj.get("en") or cookies.title
            desc_obj = manga.get("attributes", {}).get("description", {})
            cookies.metadata["synopsis"] = desc_obj.get("en", "")[:200]
            cookies.metadata["status"] = manga.get("attributes", {}).get("status", "")
            cookies.metadata["chapters"] = manga.get("attributes", {}).get("lastChapter")
            cookies.metadata["volumes"] = manga.get("attributes", {}).get("lastVolume")
            cookies.metadata["source_api"] = "mangadex"
            return cookies

        cookies.metadata["source_api"] = "local"
        return cookies

    def generate_all_cookies(self, coordinates: Dict[str, Any]) -> List[CoordinateCookies]:
        """Generate coordinate cookies for all entries."""
        cookies = []
        for universe_id, entry in coordinates.items():
            if entry.get("type") == "manga":
                cookie = self.generate_manga_cookies(entry, universe_id)
            elif entry.get("type") == "manhwa":
                cookie = self.generate_manhwa_cookies(entry, universe_id)
            else:
                continue
            cookies.append(cookie)
        return cookies


# Global instance
websearch_api = WebSearchAPI()
cookie_generator = CoordinateCookieGenerator()
