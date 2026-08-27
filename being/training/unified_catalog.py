#!/usr/bin/env python3
"""
QB Protocol - Unified Media Catalog

Normalized media graph with:
- AniList (canonical anime metadata)
- Jikan (cross-validation)
- Multi-region availability
- Unified Media ID mapping
- Identity/region/release mapping

Architecture:
                    MEDIA INDEX
                         │
          ┌──────────────┴──────────────┐
          │                             │
       ANIME                           GAMES
          │                             │
    ┌─────┴─────┐               ┌──────┴──────┐
    │           │               │             │
 AniList      Jikan           IGDB          RAWGG
    │           │               │             │
    └─────┬─────┘               └──────┬──────┘
          │                             │
          └──────────┬──────────────────┘
                     ▼
              NORMALIZATION
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Identity    Region     Release
       mapping     mapping    mapping
          │          │          │
          └──────────┼──────────┘
                     ▼
              UNIFIED CATALOG
"""

from __future__ import annotations

import json
import math
import socket
import ssl
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class MediaType(Enum):
    ANIME = "anime"
    MANGA = "manga"
    MANHWA = "manhwa"
    GAME = "game"
    MOVIE = "movie"
    SERIES = "series"
    BOOK = "book"


class RegionCode(Enum):
    JP = "JP"
    US = "US"
    CA = "CA"
    GB = "GB"
    EU = "EU"
    LATAM = "LATAM"
    BR = "BR"
    MX = "MX"
    DR = "DR"
    KR = "KR"
    CN = "CN"
    AU = "AU"
    IN = "IN"
    FR = "FR"
    DE = "DE"
    ES = "ES"
    IT = "IT"
    RU = "RU"


class AvailabilityType(Enum):
    STREAMING = "streaming"
    PURCHASE = "purchase"
    RENTAL = "rental"
    SUBSCRIPTION = "subscription"
    FREE = "free"
    UNAVAILABLE = "unavailable"


@dataclass
class MediaIdentity:
    """Unified Media ID mapping across sources."""
    unified_id: str
    anilist_id: Optional[int] = None
    mal_id: Optional[int] = None
    imdb_id: Optional[str] = None
    igdb_id: Optional[int] = None
    rawg_id: Optional[int] = None
    steam_id: Optional[int] = None
    kitsu_id: Optional[int] = None
    mangadex_id: Optional[str] = None


@dataclass
class MediaTitle:
    """Normalized title across languages."""
    romaji: Optional[str] = None
    english: Optional[str] = None
    native: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)


@dataclass
class RegionAvailability:
    """Regional availability entry."""
    region: RegionCode
    country_code: str
    language: str
    provider: str
    availability_type: AvailabilityType
    release_date: Optional[str] = None
    expires_at: Optional[str] = None
    source: str = ""
    last_checked: float = 0.0


@dataclass
class MediaEntry:
    """Normalized media entry in unified catalog."""
    identity: MediaIdentity
    media_type: MediaType
    titles: MediaTitle
    description: str = ""
    status: str = ""
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    creators: List[str] = field(default_factory=list)
    studio: Optional[str] = None
    release_year: Optional[int] = None
    end_year: Optional[int] = None
    episode_count: Optional[int] = None
    chapter_count: Optional[int] = None
    volume_count: Optional[int] = None
    rating: Optional[float] = None
    cover_image: Optional[str] = None
    banner_image: Optional[str] = None
    external_links: Dict[str, str] = field(default_factory=dict)
    regions: List[RegionAvailability] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    coordinates: Tuple[float, ...] = ()
    source_apis: List[str] = field(default_factory=list)
    last_updated: float = 0.0

    @property
    def primary_title(self) -> str:
        return (
            self.titles.english
            or self.titles.romaji
            or self.titles.native
            or self.titles.synonyms[0]
            if self.titles.synonyms
            else self.identity.unified_id
        )


class AniListAPI:
    """AniList GraphQL API integration - canonical anime metadata."""

    ENDPOINT = "graphql.anilist.co"

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.cache: Dict[str, Any] = {}

    def _graphql_query(self, query: str, variables: Dict[str, Any]) -> Optional[Dict]:
        """Execute GraphQL query."""
        try:
            import urllib.request
            import ssl

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            url = f"https://{self.ENDPOINT}"
            payload = json.dumps({"query": query, "variables": variables}).encode()

            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "User-Agent": "QB-Protocol/1.0",
                "Accept": "application/json",
            })

            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                data = json.loads(resp.read().decode())
                return data
        except Exception:
            return None

    def search_anime(self, query: str, limit: int = 10) -> Optional[List[MediaEntry]]:
        """Search anime by title."""
        cache_key = f"anilist_search_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        graphql = """
        query ($search: String, $limit: Int) {
            Page(page: 1, perPage: $limit) {
                media(search: $search, type: ANIME) {
                    id
                    idMal
                    title { romaji native english }
                    description
                    status
                    season
                    seasonYear
                    episodes
                    duration
                    chapters
                    volumes
                    averageScore
                    popularity
                    genres
                    tags { name rank }
                    studios { nodes { name } }
                    startDate { year month day }
                    endDate { year month day }
                    coverImage { large medium extraLarge }
                    bannerImage
                    siteUrl
                    externalLinks { site url }
                    relations { edges { relationType node { id title { romaji english } } } }
                }
            }
        }
        """

        result = self._graphql_query(graphql, {"search": query, "limit": limit})
        if not result or not result.get("data", {}).get("Page", {}).get("media"):
            return None

        entries = []
        for media in result["data"]["Page"]["media"]:
            entry = self._parse_media(media)
            entries.append(entry)

        self.cache[cache_key] = entries
        return entries

    def search_manga(self, query: str, limit: int = 10) -> Optional[List[MediaEntry]]:
        """Search manga by title."""
        cache_key = f"anilist_manga_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        graphql = """
        query ($search: String, $limit: Int) {
            Page(page: 1, perPage: $limit) {
                media(search: $search, type: MANGA) {
                    id
                    idMal
                    title { romaji native english }
                    description
                    status
                    chapters
                    volumes
                    averageScore
                    popularity
                    genres
                    tags { name rank }
                    studios { nodes { name } }
                    startDate { year month day }
                    endDate { year month day }
                    coverImage { large medium extraLarge }
                    bannerImage
                    siteUrl
                    externalLinks { site url }
                }
            }
        }
        """

        result = self._graphql_query(graphql, {"search": query, "limit": limit})
        if not result or not result.get("data", {}).get("Page", {}).get("media"):
            return None

        entries = []
        for media in result["data"]["Page"]["media"]:
            entry = self._parse_manga_media(media)
            entries.append(entry)

        self.cache[cache_key] = entries
        return entries

    def get_by_id(self, anilist_id: int) -> Optional[MediaEntry]:
        """Get anime by AniList ID."""
        graphql = """
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                idMal
                title { romaji native english }
                description
                status
                season
                seasonYear
                episodes
                duration
                chapters
                volumes
                averageScore
                popularity
                genres
                tags { name rank }
                studios { nodes { name } }
                startDate { year month day }
                endDate { year month day }
                coverImage { large medium extraLarge }
                bannerImage
                siteUrl
                externalLinks { site url }
                relations { edges { relationType node { id title { romaji english } type } } }
            }
        }
        """

        result = self._graphql_query(graphql, {"id": anilist_id})
        if not result or not result.get("data", {}).get("Media"):
            return None

        return self._parse_media(result["data"]["Media"])

    def _parse_media(self, media: Dict[str, Any]) -> MediaEntry:
        """Parse AniList anime media into normalized entry."""
        title = media.get("title", {})
        titles = MediaTitle(
            romaji=title.get("romaji"),
            english=title.get("english"),
            native=title.get("native"),
        )

        identity = MediaIdentity(
            unified_id=f"anilist:{media.get('id')}",
            anilist_id=media.get("id"),
            mal_id=media.get("idMal"),
        )

        start = media.get("startDate", {})
        end = media.get("endDate", {})

        studios = media.get("studios", {}).get("nodes", [])
        studio = studios[0].get("name") if studios else None

        tags = [t.get("name") for t in media.get("tags", [])]

        external_links = {}
        for link in media.get("externalLinks", []):
            site = link.get("site", "")
            url = link.get("url", "")
            if site and url:
                external_links[site] = url

        relationships = {}
        for edge in media.get("relations", {}).get("edges", []):
            rel_type = edge.get("relationType", "unknown")
            node = edge.get("node", {})
            node_title = node.get("title", {})
            name = node_title.get("english") or node_title.get("romaji") or "unknown"
            if rel_type not in relationships:
                relationships[rel_type] = []
            relationships[rel_type].append(name)

        # Generate coordinates from release date
        year = start.get("year") or media.get("seasonYear") or 2000
        month = start.get("month") or 1
        day = start.get("day") or 1
        coordinates = (year, month, day)

        cover = media.get("coverImage", {})
        banner = media.get("bannerImage")

        description = media.get("description") or ""

        return MediaEntry(
            identity=identity,
            media_type=MediaType.ANIME,
            titles=titles,
            description=description[:500],
            status=media.get("status", "").lower(),
            genres=media.get("genres", []),
            tags=tags,
            studio=studio,
            release_year=start.get("year"),
            end_year=end.get("year"),
            episode_count=media.get("episodes"),
            rating=media.get("averageScore"),
            cover_image=cover.get("large") or cover.get("medium"),
            banner_image=banner,
            external_links=external_links,
            relationships=relationships,
            coordinates=coordinates,
            source_apis=["anilist"],
            last_updated=time.time(),
        )

    def _parse_manga_media(self, media: Dict[str, Any]) -> MediaEntry:
        """Parse AniList manga media into normalized entry."""
        title = media.get("title", {})
        titles = MediaTitle(
            romaji=title.get("romaji"),
            english=title.get("english"),
            native=title.get("native"),
        )

        identity = MediaIdentity(
            unified_id=f"anilist_manga:{media.get('id')}",
            anilist_id=media.get("id"),
            mal_id=media.get("idMal"),
        )

        start = media.get("startDate", {})
        end = media.get("endDate", {})

        tags = [t.get("name") for t in media.get("tags", [])]

        external_links = {}
        for link in media.get("externalLinks", []):
            site = link.get("site", "")
            url = link.get("url", "")
            if site and url:
                external_links[site] = url

        year = start.get("year") or 2000
        month = start.get("month") or 1
        day = start.get("day") or 1
        coordinates = (year, month, day)

        cover = media.get("coverImage", {})

        description = media.get("description") or ""

        return MediaEntry(
            identity=identity,
            media_type=MediaType.MANGA,
            titles=titles,
            description=description[:500],
            status=media.get("status", "").lower(),
            genres=media.get("genres", []),
            tags=tags,
            release_year=start.get("year"),
            end_year=end.get("year"),
            chapter_count=media.get("chapters"),
            volume_count=media.get("volumes"),
            rating=media.get("averageScore"),
            cover_image=cover.get("large") or cover.get("medium"),
            external_links=external_links,
            coordinates=coordinates,
            source_apis=["anilist"],
            last_updated=time.time(),
        )


class JikanAPI:
    """Jikan REST API - MyAnimeList cross-validation."""

    ENDPOINT = "api.jikan.moe"

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.cache: Dict[str, Any] = {}

    def _http_get(self, path: str) -> Optional[Dict]:
        """HTTP GET request."""
        try:
            import urllib.request
            import ssl

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            url = f"https://{self.ENDPOINT}{path}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "QB-Protocol/1.0",
                "Accept": "application/json",
            })

            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def search_anime(self, query: str, limit: int = 5) -> Optional[List[Dict]]:
        """Search anime via Jikan."""
        cache_key = f"jikan_search_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = self._http_get(f"/v4/anime?q={query}&limit={limit}")
        if result and result.get("data"):
            self.cache[cache_key] = result["data"]
            return result["data"]
        return None

    def get_anime(self, mal_id: int) -> Optional[Dict]:
        """Get anime by MAL ID."""
        cache_key = f"jikan_anime_{mal_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = self._http_get(f"/v4/anime/{mal_id}")
        if result and result.get("data"):
            self.cache[cache_key] = result["data"]
            return result["data"]
        return None

    def cross_validate(self, entry: MediaEntry) -> Dict[str, Any]:
        """Cross-validate an AniList entry with Jikan."""
        if entry.identity.mal_id:
            jikan_data = self.get_anime(entry.identity.mal_id)
            if jikan_data:
                return {
                    "title_match": jikan_data.get("title") == entry.titles.english,
                    "episode_match": jikan_data.get("episodes") == entry.episode_count,
                    "score_diff": abs((jikan_data.get("score") or 0) - (entry.rating or 0)),
                    "status_match": jikan_data.get("status", "").lower() == entry.status,
                    "jikan_synopsis": jikan_data.get("synopsis", "")[:200],
                }
        return {}


class UnifiedMediaCatalog:
    """Unified media catalog with normalized media graph."""

    def __init__(self):
        self.anilist = AniListAPI()
        self.jikan = JikanAPI()
        self.entries: Dict[str, MediaEntry] = {}
        self.identity_map: Dict[str, str] = {}  # external_id -> unified_id

    def search(self, query: str, media_type: Optional[MediaType] = None) -> List[MediaEntry]:
        """Search unified catalog."""
        results = []

        # Search AniList
        if media_type == MediaType.ANIME or media_type is None:
            anime_results = self.anilist.search_anime(query)
            if anime_results:
                results.extend(anime_results)

        if media_type == MediaType.MANGA or media_type is None:
            manga_results = self.anilist.search_manga(query)
            if manga_results:
                results.extend(manga_results)

        # Add to catalog
        for entry in results:
            self.entries[entry.identity.unified_id] = entry
            if entry.identity.anilist_id:
                self.identity_map[f"anilist:{entry.identity.anilist_id}"] = entry.identity.unified_id
            if entry.identity.mal_id:
                self.identity_map[f"mal:{entry.identity.mal_id}"] = entry.identity.unified_id

        return results

    def get_by_unified_id(self, unified_id: str) -> Optional[MediaEntry]:
        """Get entry by unified ID."""
        return self.entries.get(unified_id)

    def get_by_anilist_id(self, anilist_id: int) -> Optional[MediaEntry]:
        """Get entry by AniList ID."""
        key = f"anilist:{anilist_id}"
        if key in self.identity_map:
            return self.entries.get(self.identity_map[key])
        return None

    def get_by_mal_id(self, mal_id: int) -> Optional[MediaEntry]:
        """Get entry by MAL ID."""
        key = f"mal:{mal_id}"
        if key in self.identity_map:
            return self.entries.get(self.identity_map[key])
        return None

    def cross_validate_entry(self, unified_id: str) -> Dict[str, Any]:
        """Cross-validate entry with Jikan."""
        entry = self.entries.get(unified_id)
        if entry:
            return self.jikan.cross_validate(entry)
        return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        type_counts = {}
        for entry in self.entries.values():
            t = entry.media_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_entries": len(self.entries),
            "type_counts": type_counts,
            "identity_mappings": len(self.identity_map),
            "cache_size": len(self.anilist.cache) + len(self.jikan.cache),
        }


# Global instance
unified_catalog = UnifiedMediaCatalog()
