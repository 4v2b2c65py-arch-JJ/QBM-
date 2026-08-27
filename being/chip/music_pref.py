#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Music Preference Reference Board

Stores user's music references for model taste alignment:
- Spotify profile references
- Favorite artists/tracks/genres tracking
- MusicBrainz cross-referencing for metadata
- Tune profile for creative observation

The model can use this to "get a tune" on what the user likes.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

LOG = __import__("logging").getLogger("qb_protocol.being.chip.music_pref")


@dataclass
class MusicPreferenceProfile:
    """User's music preference reference profile."""
    # Spotify references (public profiles)
    spotify_profiles: List[str] = field(default_factory=list)

    # Favorite artists (manually curated or discovered)
    favorite_artists: List[Dict[str, str]] = field(default_factory=list)

    # Favorite tracks
    favorite_tracks: List[Dict[str, str]] = field(default_factory=list)

    # Genre preferences (weighted)
    genre_preferences: Dict[str, float] = field(default_factory=dict)

    # Mood/energy preferences
    energy_preference: float = 0.5  # 0=calm, 1=energetic
    mood_preferences: List[str] = field(default_factory=list)

    # Discovery settings
    discovery_openness: float = 0.7  # 0=same stuff, 1=always new
    preferred_era: str = "any"  # e.g., "90s", "2000s", "any"

    # Last updated
    last_updated: str = ""


@dataclass
class MusicReferenceBoard:
    """
    Reference board for model to understand user's music taste.
    
    This allows the model to:
    - Recommend music aligned with preferences
    - Seed MusicBrainz discovery with known favorites
    - Understand the "vibe" the user is into
    - Cross-reference with spatial observation data
    """

    profile: MusicPreferenceProfile = field(default_factory=MusicPreferenceProfile)

    # Discovery history
    discovered_artists: List[Dict[str, Any]] = field(default_factory=list)
    discovery_sessions: List[Dict[str, Any]] = field(default_factory=list)

    # Pattern insights
    taste_patterns: Dict[str, Any] = field(default_factory=dict)


class PreferenceManager:
    """
    Manages the user's music preference reference board.
    
    Provides methods to:
    - Add Spotify profile references
    - Track favorite artists/tracks
    - Query MusicBrainz for metadata
    - Generate taste summaries
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "/Users/jjmarte/delta-stream/qb_protocol/music_preferences.json"
        self.board = MusicReferenceBoard()
        self._load()

    def _load(self) -> None:
        """Load preferences from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                # TODO: Parse data into board structure
            except Exception:
                pass

    def _save(self) -> None:
        """Save preferences to storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            # TODO: Serialize board to JSON
            with open(self.storage_path, 'w') as f:
                json.dump({"saved": True}, f)
        except Exception as e:
            LOG.error(f"Failed to save preferences: {e}")

    def add_spotify_profile(self, profile_url: str) -> None:
        """Add a Spotify profile reference."""
        if profile_url not in self.board.profile.spotify_profiles:
            self.board.profile.spotify_profiles.append(profile_url)
            self.board.profile.last_updated = datetime.now(timezone.utc).isoformat()

    def add_favorite_artist(self, name: str, genre: str = "", notes: str = "") -> None:
        """Add a favorite artist."""
        self.board.profile.favorite_artists.append({
            "name": name,
            "genre": genre,
            "notes": notes,
            "added": datetime.now(timezone.utc).isoformat(),
        })

    def add_favorite_track(self, title: str, artist: str, notes: str = "") -> None:
        """Add a favorite track."""
        self.board.profile.favorite_tracks.append({
            "title": title,
            "artist": artist,
            "notes": notes,
            "added": datetime.now(timezone.utc).isoformat(),
        })

    def get_taste_summary(self) -> Dict[str, Any]:
        """Generate a summary of the user's taste for model reference."""
        profile = self.board.profile

        # Extract genres from favorites
        genres = {}
        for artist in profile.favorite_artists:
            g = artist.get("genre", "unknown")
            genres[g] = genres.get(g, 0) + 1

        return {
            "spotify_profiles": len(profile.spotify_profiles),
            "favorite_artists_count": len(profile.favorite_artists),
            "favorite_tracks_count": len(profile.favorite_tracks),
            "top_genres": dict(sorted(genres.items(), key=lambda x: -x[1])[:5]),
            "energy_preference": profile.energy_preference,
            "discovery_openness": profile.discovery_openness,
            "mood_preferences": profile.mood_preferences,
            "spotify_references": profile.spotify_profiles,
        }

    def get_model_reference_card(self) -> str:
        """
        Generate a reference card the model can use to understand taste.
        
        This is the "get a tune" card - quick summary for the model.
        """
        summary = self.get_taste_summary()

        card = f"""
=== MUSIC PREFERENCE REFERENCE ===
Spotify Profiles: {summary['spotify_profiles']}
Favorite Artists: {summary['favorite_artists_count']}
Favorite Tracks: {summary['favorite_tracks_count']}
Top Genres: {', '.join(f'{k}({v})' for k, v in summary['top_genres'].items())}
Energy: {'High' if summary['energy_preference'] > 0.6 else 'Medium' if summary['energy_preference'] > 0.3 else 'Low'}
Discovery: {'Open to new' if summary['discovery_openness'] > 0.6 else 'Stick to favorites'}
Mood: {', '.join(summary['mood_preferences']) if summary['mood_preferences'] else 'Any'}

Spotify Refs:
"""
        for url in summary.get('spotify_references', []):
            card += f"  - {url}\n"

        return card


# Initialize with user's Spotify profiles
def initialize_with_user_prefs() -> PreferenceManager:
    """Initialize preference manager with user's Spotify profiles."""
    mgr = PreferenceManager()

    # User's Spotify profiles
    spotify_profiles = [
        "https://open.spotify.com/user/31h2m3qtsl7yt6m2tyakqntv5ne4?si=2742b69efb904831",
        "https://open.spotify.com/user/316rzupnmqxd3oa4lqs7cs4yyyny?si=47606b19261a4528",
    ]

    for profile in spotify_profiles:
        mgr.add_spotify_profile(profile)

    return mgr


# Global instance
pref_manager = initialize_with_user_prefs()
