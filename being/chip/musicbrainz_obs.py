#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: MusicBrainz Observation Module

Integrates MusicBrainz for creative music metadata observation:
- Artists, Albums, Recordings, Labels, Genres
- ISRC/ISWC identifiers
- Relationship mapping between entities
- Flicker-based sampling of music metadata
- Pattern discovery in music data

API: https://musicbrainz.org/ws/2/
No API key required for read requests
Rate limit: 1 req/sec with proper User-Agent
"""

from __future__ import annotations

import json
import random
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.musicbrainz_obs")


class MusicEntity(Enum):
    """MusicBrainz entity types."""
    ARTIST = "artist"
    RELEASE = "release"
    RELEASE_GROUP = "release-group"
    RECORDING = "recording"
    WORK = "work"
    LABEL = "label"
    AREA = "area"
    PLACE = "place"
    EVENT = "event"
    INSTRUMENT = "instrument"
    SERIES = "series"
    GENRE = "genre"


@dataclass
class MusicArtist:
    """MusicBrainz artist entity."""
    mbid: str  # MusicBrainz ID
    name: str
    sort_name: str
    type: str  # Person, Group, Orchestra, etc
    country: str
    area: str
    begin_date: str
    end_date: str
    disambiguation: str
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    relations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MusicRelease:
    """MusicBrainz release entity."""
    mbid: str
    title: str
    status: str  # Official, Bootleg, Pseudo-Release
    date: str
    country: str
    artist_credit: List[Dict[str, str]]
    label: str
    catalog_number: str
    barcode: str
    track_count: int
    media: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)


@dataclass
class MusicRecording:
    """MusicBrainz recording entity."""
    mbid: str
    title: str
    length_ms: int
    artist: str
    isrc: str
    disambiguation: str
    tags: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)


@dataclass
class MusicLabel:
    """MusicBrainz label entity."""
    mbid: str
    name: str
    type: str  # Production, Publisher, Distributor, etc
    country: str
    begin_date: str
    end_date: str
    disambiguation: str


@dataclass
class MusicGenre:
    """MusicBrainz genre entity."""
    name: str
    count: int  # Number of times used


class MusicBrainzAPI:
    """
    MusicBrainz API client for creative observation.
    
    Provides flicker-rate sampling of music metadata:
    - Artists and their relationships
    - Release catalog exploration
    - Recording/ISRC tracking
    - Genre pattern discovery
    - Label network analysis
    """

    BASE_URL = "https://musicbrainz.org/ws/2/"
    USER_AGENT = "QB-Protocol-Observation/1.0 (observation@qb.protocol)"

    def __init__(self):
        self.last_request_time: float = 0
        self.request_count: int = 0
        self.cache: Dict[str, Any] = {}

    def _rate_limit(self) -> None:
        """Enforce 1 request per second rate limit."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self.last_request_time = time.time()

    def _request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Make rate-limited API request."""
        self._rate_limit()

        url = self.BASE_URL + endpoint
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.request_count += 1
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            LOG.error(f"MusicBrainz request failed: {e}")
            return None

    def search_artists(self, query: str, limit: int = 10) -> List[MusicArtist]:
        """Search for artists."""
        data = self._request("artist/", {"query": query, "fmt": "json", "limit": str(limit)})
        if not data or "artists" not in data:
            return []

        return [
            MusicArtist(
                mbid=a.get("id", ""),
                name=a.get("name", ""),
                sort_name=a.get("sort-name", ""),
                type=a.get("type", ""),
                country=a.get("country", ""),
                area=a.get("area", {}).get("name", ""),
                begin_date=a.get("life-span", {}).get("begin", ""),
                end_date=a.get("life-span", {}).get("end", ""),
                disambiguation=a.get("disambiguation", ""),
            )
            for a in data["artists"]
        ]

    def get_artist(self, mbid: str, include: str = "genres+tags+aliases") -> Optional[MusicArtist]:
        """Get artist details with relationships."""
        data = self._request(f"artist/{mbid}", {"inc": include, "fmt": "json"})
        if not data:
            return None

        return MusicArtist(
            mbid=data.get("id", ""),
            name=data.get("name", ""),
            sort_name=data.get("sort-name", ""),
            type=data.get("type", ""),
            country=data.get("country", ""),
            area=data.get("area", {}).get("name", ""),
            begin_date=data.get("life-span", {}).get("begin", ""),
            end_date=data.get("life-span", {}).get("end", ""),
            disambiguation=data.get("disambiguation", ""),
            genres=[g.get("name", "") for g in data.get("genres", [])],
            tags=[t.get("name", "") for t in data.get("tags", [])],
            aliases=[a.get("name", "") for a in data.get("aliases", [])],
        )

    def search_releases(self, query: str, limit: int = 10) -> List[MusicRelease]:
        """Search for releases."""
        data = self._request("release/", {"query": query, "fmt": "json", "limit": str(limit)})
        if not data or "releases" not in data:
            return []

        return [
            MusicRelease(
                mbid=r.get("id", ""),
                title=r.get("title", ""),
                status=r.get("status", ""),
                date=r.get("date", ""),
                country=r.get("country", ""),
                artist_credit=r.get("artist-credit", []),
                label=r.get("label-info", [{}])[0].get("label", {}).get("name", "") if r.get("label-info") else "",
                catalog_number=r.get("label-info", [{}])[0].get("catalog-number", "") if r.get("label-info") else "",
                barcode=r.get("barcode", ""),
                track_count=r.get("track-count", 0),
            )
            for r in data["releases"]
        ]

    def get_release(self, mbid: str, include: str = "recordings+artists+labels") -> Optional[MusicRelease]:
        """Get release details."""
        data = self._request(f"release/{mbid}", {"inc": include, "fmt": "json"})
        if not data:
            return None

        return MusicRelease(
            mbid=data.get("id", ""),
            title=data.get("title", ""),
            status=data.get("status", ""),
            date=data.get("date", ""),
            country=data.get("country", ""),
            artist_credit=data.get("artist-credit", []),
            label=data.get("label-info", [{}])[0].get("label", {}).get("name", "") if data.get("label-info") else "",
            catalog_number=data.get("label-info", [{}])[0].get("catalog-number", "") if data.get("label-info") else "",
            barcode=data.get("barcode", ""),
            track_count=data.get("track-count", 0),
        )

    def search_recordings(self, query: str, limit: int = 10) -> List[MusicRecording]:
        """Search for recordings."""
        data = self._request("recording/", {"query": query, "fmt": "json", "limit": str(limit)})
        if not data or "recordings" not in data:
            return []

        return [
            MusicRecording(
                mbid=r.get("id", ""),
                title=r.get("title", ""),
                length_ms=r.get("length", 0),
                artist=r.get("artist-credit", [{}])[0].get("name", "") if r.get("artist-credit") else "",
                isrc=r.get("isrcs", [""])[0] if r.get("isrcs") else "",
                disambiguation=r.get("disambiguation", ""),
            )
            for r in data["recordings"]
        ]

    def get_all_genres(self) -> List[MusicGenre]:
        """Get all genres in MusicBrainz."""
        data = self._request("genre/all", {"fmt": "json"})
        if not data or "genres" not in data:
            return []

        return [
            MusicGenre(name=g.get("name", ""), count=g.get("count", 0))
            for g in data["genres"]
        ]

    def search_labels(self, query: str, limit: int = 10) -> List[MusicLabel]:
        """Search for labels."""
        data = self._request("label/", {"query": query, "fmt": "json", "limit": str(limit)})
        if not data or "labels" not in data:
            return []

        return [
            MusicLabel(
                mbid=l.get("id", ""),
                name=l.get("name", ""),
                type=l.get("type", ""),
                country=l.get("country", ""),
                begin_date=l.get("life-span", {}).get("begin", ""),
                end_date=l.get("life-span", {}).get("end", ""),
                disambiguation=l.get("disambiguation", ""),
            )
            for l in data["labels"]
        ]


class MusicFlickerObserver:
    """
    Flicker-based music observation streams.
    
    Creates controllable data streams for:
    - Artist discovery and exploration
    - Release catalog browsing
    - Genre pattern sampling
    - Label network observation
    - Recording/ISRC tracking
    """

    def __init__(self):
        self.api = MusicBrainzAPI()
        self.discovery_queue: List[str] = []
        self.observed_artists: Dict[str, MusicArtist] = {}
        self.observed_releases: Dict[str, MusicRelease] = {}
        self.observed_genres: Dict[str, int] = {}

    def create_artist_discovery_stream(self, seed_artist: str) -> Dict[str, Any]:
        """Create a flicker stream for artist discovery."""
        def artist_generator():
            """Generate artist discovery frames."""
            artists = self.api.search_artists(seed_artist, limit=5)
            if artists:
                artist = random.choice(artists)
                self.observed_artists[artist.mbid] = artist
                return {
                    "type": "artist_discovery",
                    "name": artist.name,
                    "mbid": artist.mbid,
                    "artist_type": artist.type,
                    "country": artist.country,
                    "active": f"{artist.begin_date}-{artist.end_date}" if artist.end_date else artist.begin_date,
                    "disambiguation": artist.disambiguation,
                    "new_discovery": artist.mbid not in self.observed_artists,
                }
            return {"type": "artist_discovery", "error": "no results"}

        return {
            "stream_id": f"artist_{seed_artist}",
            "source": f"Artist: {seed_artist}",
            "min_hz": 0.1,
            "max_hz": 1.0,  # Rate limited to 1 req/sec
            "base_hz": 0.5,
            "generator": artist_generator,
        }

    def create_genre_exploration_stream(self) -> Dict[str, Any]:
        """Create a flicker stream for genre exploration."""
        def genre_generator():
            """Generate genre exploration frames."""
            if not self.observed_genres:
                genres = self.api.get_all_genres()
                for g in genres[:50]:  # Top 50
                    self.observed_genres[g.name] = g.count

            if self.observed_genres:
                genre = random.choice(list(self.observed_genres.keys()))
                return {
                    "type": "genre_exploration",
                    "genre": genre,
                    "usage_count": self.observed_genres[genre],
                    "relative_popularity": self.observed_genres[genre] / max(self.observed_genres.values()) if self.observed_genres else 0,
                }
            return {"type": "genre_exploration", "error": "no genres loaded"}

        return {
            "stream_id": "genre_explorer",
            "source": "Genre Exploration",
            "min_hz": 0.05,
            "max_hz": 0.5,
            "base_hz": 0.1,
            "generator": genre_generator,
        }

    def create_release_radar_stream(self, artist_name: str) -> Dict[str, Any]:
        """Create a flicker stream for release discovery."""
        def release_generator():
            """Generate release radar frames."""
            releases = self.api.search_releases(f"artist:{artist_name}", limit=5)
            if releases:
                release = random.choice(releases)
                self.observed_releases[release.mbid] = release
                return {
                    "type": "release_radar",
                    "title": release.title,
                    "mbid": release.mbid,
                    "status": release.status,
                    "date": release.date,
                    "country": release.country,
                    "label": release.label,
                    "tracks": release.track_count,
                    "new_discovery": release.mbid not in self.observed_releases,
                }
            return {"type": "release_radar", "error": "no releases found"}

        return {
            "stream_id": f"releases_{artist_name}",
            "source": f"Releases: {artist_name}",
            "min_hz": 0.1,
            "max_hz": 1.0,
            "base_hz": 0.3,
            "generator": release_generator,
        }

    def create_label_network_stream(self, label_query: str) -> Dict[str, Any]:
        """Create a flicker stream for label network observation."""
        def label_generator():
            """Generate label network frames."""
            labels = self.api.search_labels(label_query, limit=5)
            if labels:
                label = random.choice(labels)
                return {
                    "type": "label_network",
                    "name": label.name,
                    "mbid": label.mbid,
                    "label_type": label.type,
                    "country": label.country,
                    "active": f"{label.begin_date}-{label.end_date}" if label.end_date else label.begin_date,
                }
            return {"type": "label_network", "error": "no labels found"}

        return {
            "stream_id": f"label_{label_query}",
            "source": f"Labels: {label_query}",
            "min_hz": 0.05,
            "max_hz": 0.5,
            "base_hz": 0.1,
            "generator": label_generator,
        }

    def hyperaccel_music_discovery(self, seed_artists: List[str],
                                     duration_sec: float = 5.0) -> Dict[str, Any]:
        """
        Hyperacceleration music discovery session.
        
        Rapidly flickers through artist, release, and genre streams
        to discover interesting patterns and connections.
        """
        start = time.time()
        discoveries = {
            "artists": [],
            "releases": [],
            "genres": [],
            "patterns": [],
        }

        # Create streams for each seed artist
        streams = []
        for artist in seed_artists:
            streams.append(self.create_artist_discovery_stream(artist))
            streams.append(self.create_release_radar_stream(artist))

        # Add genre exploration
        streams.append(self.create_genre_exploration_stream())

        # Flicker through streams
        while time.time() - start < duration_sec:
            for stream in streams:
                if random.random() < 0.3:  # 30% chance to fire per cycle
                    if stream.get("generator"):
                        frame = stream["generator"]()
                        frame_type = frame.get("type", "")

                        if frame_type == "artist_discovery" and "error" not in frame:
                            discoveries["artists"].append(frame)
                        elif frame_type == "release_radar" and "error" not in frame:
                            discoveries["releases"].append(frame)
                        elif frame_type == "genre_exploration" and "error" not in frame:
                            discoveries["genres"].append(frame)

        # Find patterns
        if discoveries["artists"]:
            countries = {}
            for a in discoveries["artists"]:
                c = a.get("country", "unknown")
                countries[c] = countries.get(c, 0) + 1
            discoveries["patterns"].append({
                "type": "artist_country_distribution",
                "distribution": countries,
            })

        if discoveries["genres"]:
            discoveries["patterns"].append({
                "type": "genre_diversity",
                "unique_genres": len(set(g.get("genre", "") for g in discoveries["genres"])),
                "total_observations": len(discoveries["genres"]),
            })

        return {
            "duration_sec": round(duration_sec, 2),
            "streams_active": len(streams),
            "discoveries": {
                "artists_found": len(discoveries["artists"]),
                "releases_found": len(discoveries["releases"]),
                "genres_sampled": len(discoveries["genres"]),
                "patterns_detected": len(discoveries["patterns"]),
            },
            "details": discoveries,
        }

    def get_state(self) -> Dict[str, Any]:
        """Get observation state."""
        return {
            "api_requests_made": self.api.request_count,
            "artists_observed": len(self.observed_artists),
            "releases_observed": len(self.observed_releases),
            "genres_mapped": len(self.observed_genres),
            "discovery_queue_length": len(self.discovery_queue),
        }


# Global instance
music_observer = MusicFlickerObserver()
music_api = MusicBrainzAPI()
