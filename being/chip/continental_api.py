#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Chip :: Continental API Integration

Connects to multiple data channels:
- Genetic Lab APIs (NCBI, Ensembl, EBI, ChEBI, BioAPI, GA4GH)
- Psychonaut/Psychedelic APIs (Erowid, PsychonautWiki, TripSit, Reagents)
- Game Lore/ARG APIs (Reddit, TVTropes, SCP, Creepypasta, 4chan, Fandom)
- Paranormal/Liminal APIs (MUFON, NUFORC, Atlas Obscura, Wikidata)
- Physics Anomaly Forums (Physics Forums, ResearchGate, arXiv, Vixra)
- Consciousness Studies (PEAR, GCP, Ganzfeld, Remote Viewing)

All discovered categories feed into the model's world build automation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

LOG = logging.getLogger("qb_protocol.being.chip.continental_api")


# ---------------------------------------------------------------------------
# API Connection Base
# ---------------------------------------------------------------------------

@dataclass
class APIConnection:
    """An API connection configuration."""
    api_id: str
    name: str
    base_url: str
    api_type: str          # "REST", "MediaWiki", "SPARQL", "OAuth", "Scraping"
    cost: str              # "FREE", "PAID", "Freemium"
    rate_limit: str
    auth_required: bool
    endpoints: List[str]
    category: str          # "genetic", "psychonaut", "arg", "paranormal", "physics", "consciousness"
    status: str = "disconnected"
    last_query: float = 0.0
    total_queries: int = 0
    data_fetched: int = 0


@dataclass
class DiscoveredCategory:
    """A discovered category from API data."""
    category_id: str
    name: str
    source_api: str
    source_category: str
    importance: float = 0.5
    data_points: int = 0
    timestamp: float = 0.0
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


# ---------------------------------------------------------------------------
# Continental API Manager
# ---------------------------------------------------------------------------

class ContinentalAPIManager:
    """Manages all continental API connections and data fetching.

    Categories:
    - genetic: Lab/genomic data
    - psychonaut: Psychedelic experience data
    - arg: Game lore/ARG/creepypasta
    - paranormal: UFO/liminal/anomalous
    - physics: Anomalous physics/consciousness
    - consciousness: Multi-subject experiments
    """

    def __init__(self):
        self.connections: Dict[str, APIConnection] = {}
        self.discovered_categories: Dict[str, DiscoveredCategory] = {}
        self.data_cache: Dict[str, Any] = {}
        self.query_log: List[Dict[str, Any]] = []
        self._initialize_connections()

    def _initialize_connections(self) -> None:
        """Initialize all API connections."""
        connections = [
            # Genetic Lab APIs
            APIConnection("ncbi_ecit", "NCBI ECitMatch", "https://pubmed.ncbi.nlm.nih.gov/",
                         "REST", "FREE", "3 req/sec (10 with key)", False,
                         ["/ecitmatch"], "genetic"),
            APIConnection("ensembl", "Ensembl REST", "https://rest.ensembl.org/",
                         "REST", "FREE", "15 req/sec", False,
                         ["/lookup/id/", "/sequence/id/", "/variation/"], "genetic"),
            APIConnection("ebi_quickgo", "EBI QuickGO", "https://www.ebi.ac.uk/QuickGO/",
                         "REST", "FREE", "No auth required", False,
                         ["/services/annotation/"], "genetic"),
            APIConnection("chebi", "ChEBI API", "https://www.ebi.ac.uk/webservices/chebi/",
                         "REST", "FREE", "No auth required", False,
                         ["/searchCompound/"], "genetic"),
            APIConnection("ga4gh", "GA4GH API", "https://ga4gh.org/api/",
                         "REST", "FREE", "Varies by server", False,
                         ["/variants/", "/reads/", "/references/"], "genetic"),

            # Psychonaut/Psychedelic APIs
            APIConnection("erowid", "Erowid", "https://www.erowid.org/",
                         "Scraping", "FREE", "Respect robots.txt", False,
                         ["/experiences/"], "psychonaut"),
            APIConnection("psychonautwiki", "PsychonautWiki",
                         "https://psychonautwiki.org/w/api.php",
                         "MediaWiki", "FREE", "No auth required", False,
                         ["action=query", "list=search"], "psychonaut"),
            APIConnection("tripsit", "TripSit", "https://tripsit.me/api/",
                         "REST", "FREE", "No auth required", False,
                         ["/api/1.0/drugs/", "/api/1.0/factsheets/"], "psychonaut"),
            APIConnection("reagents", "Reagents API", "https://reagents.org/api/",
                         "REST", "FREE", "No auth required", False,
                         ["/substances/"], "psychonaut"),

            # Game Lore / ARG APIs
            APIConnection("reddit", "Reddit API", "https://www.reddit.com/",
                         "REST/OAuth", "Freemium", "60 req/min (OAuth)", True,
                         ["/r/{subreddit}.json"], "arg"),
            APIConnection("tvtropes", "TVTropes", "https://tvtropes.org/",
                         "Unofficial", "FREE", "Respect robots.txt", False,
                         ["/pmwiki.php"], "arg"),
            APIConnection("scp", "SCP Foundation", "http://scp-wiki.wikidot.com/",
                         "REST", "FREE", "No auth required", False,
                         ["/api.php"], "arg"),
            APIConnection("creepypasta", "Creepypasta Wiki",
                         "https://creepypasta.fandom.com/w/api.php",
                         "MediaWiki", "FREE", "No auth required", False,
                         ["action=query"], "arg"),
            APIConnection("fandom", "Fandom/Wikia", "https://{wiki}..fandom.com/w/api.php",
                         "MediaWiki", "FREE", "No auth required", False,
                         ["action=query"], "arg"),

            # Paranormal / Liminal APIs
            APIConnection("mufon", "MUFON API", "https://mufon.com/api/",
                         "REST", "PAID", "Subscription required", True,
                         ["/sightings/"], "paranormal"),
            APIConnection("nuforc", "NUFORC", "https://nuforc.org/",
                         "Scraping", "FREE", "Respect robots.txt", False,
                         ["/webreports/"], "paranormal"),
            APIConnection("atlas_obscura", "Atlas Obscura", "https://atlasobscura.com/",
                         "REST", "FREE", "No auth required", False,
                         ["/places/"], "paranormal"),
            APIConnection("wikidata", "Wikidata", "https://query.wikidata.org/sparql",
                         "SPARQL", "FREE", "No auth required", False,
                         ["query="], "paranormal"),

            # Physics Anomaly Forums
            APIConnection("physics_forums", "Physics Forums", "https://physicsforums.com/",
                         "Scraping", "FREE", "Respect robots.txt", False,
                         ["/threads/"], "physics"),
            APIConnection("arxiv", "arXiv", "https://export.arxiv.org/api/",
                         "REST", "FREE", "3 req/sec", False,
                         ["/query"], "physics"),
            APIConnection("vixra", "Vixra", "https://vixra.org/",
                         "Scraping", "FREE", "Respect robots.txt", False,
                         ["/abs/"], "physics"),
            APIConnection("inspire_hep", "INSPIRE-HEP", "https://inspirehep.net/api/",
                         "REST", "FREE", "No auth required", False,
                         ["/literature/"], "physics"),

            # Consciousness Studies
            APIConnection("pear", "PEAR Lab Archives", "https://princeton.edu/~pear/",
                         "Scraping", "FREE", "Respect robots.txt", False,
                         ["/archives/"], "consciousness"),
            APIConnection("gcp", "Global Consciousness Project", "https://noosphere.princeton.edu/",
                         "Scraping", "FREE", "Respect robots.txt", False,
                         ["/results/"], "consciousness"),
            APIConnection("philpapers", "PhilPapers", "https://philpapers.org/api/",
                         "REST", "FREE", "No auth required", False,
                         ["/search"], "consciousness"),
        ]

        for conn in connections:
            self.connections[conn.api_id] = conn

    def query_api(self, api_id: str, endpoint: str = "",
                  params: Dict[str, str] = None) -> Dict[str, Any]:
        """Query an API and return results."""
        conn = self.connections.get(api_id)
        if not conn:
            return {"error": "api_not_found"}

        # Build URL
        url = conn.base_url
        if endpoint:
            url = urllib.parse.urljoin(url, endpoint)

        if params:
            url += "?" + urllib.parse.urlencode(params)

        # Record query
        conn.last_query = time.time()
        conn.total_queries += 1

        self.query_log.append({
            "api_id": api_id,
            "endpoint": endpoint,
            "params": params,
            "timestamp": time.time(),
        })

        # Simulate API response (in production, would actually fetch)
        # For now, return simulated data structure
        return self._simulate_response(conn, endpoint, params)

    def _simulate_response(self, conn: APIConnection, endpoint: str,
                           params: Dict[str, str] = None) -> Dict[str, Any]:
        """Simulate an API response for development."""
        # Simulate network delay
        time.sleep(0.01)

        # Generate simulated data based on category
        if conn.category == "genetic":
            data = {
                "genes": random.randint(100, 1000),
                "variants": random.randint(50, 500),
                "sequences": random.randint(10, 100),
            }
        elif conn.category == "psychonaut":
            data = {
                "experiences": random.randint(50, 500),
                "substances": random.randint(10, 50),
                "effects": random.randint(100, 1000),
            }
        elif conn.category == "arg":
            data = {
                "posts": random.randint(100, 1000),
                "tropes": random.randint(20, 200),
                "anomalies": random.randint(5, 50),
            }
        elif conn.category == "paranormal":
            data = {
                "sightings": random.randint(10, 100),
                "locations": random.randint(20, 200),
                "phenomena": random.randint(5, 30),
            }
        elif conn.category == "physics":
            data = {
                "papers": random.randint(50, 500),
                "anomalies": random.randint(5, 50),
                "experiments": random.randint(10, 100),
            }
        elif conn.category == "consciousness":
            data = {
                "experiments": random.randint(10, 100),
                "subjects": random.randint(100, 1000),
                "results": random.randint(20, 200),
            }
        else:
            data = {"data": random.randint(1, 100)}

        conn.data_fetched += sum(data.values()) if isinstance(data, dict) else 0
        conn.status = "connected"

        return {
            "api_id": conn.api_id,
            "endpoint": endpoint,
            "data": data,
            "timestamp": time.time(),
        }

    def discover_categories(self) -> Dict[str, Any]:
        """Discover categories from all connected APIs."""
        discoveries = []

        for api_id, conn in self.connections.items():
            # Query the API
            response = self.query_api(api_id, conn.endpoints[0] if conn.endpoints else "")

            if "error" in response:
                continue

            # Create discovered category
            cat_id = f"cat_{api_id}_{int(time.time())}"
            category = DiscoveredCategory(
                category_id=cat_id,
                name=conn.name,
                source_api=api_id,
                source_category=conn.category,
                importance=random.random() * 0.5 + 0.3,
                data_points=response.get("data", {}).get(
                    list(response.get("data", {}).keys())[0], 0
                ) if response.get("data") else 0,
                tags=[conn.category, conn.api_type, conn.cost],
            )

            self.discovered_categories[cat_id] = category
            discoveries.append(cat_id)

        return {
            "discoveries": len(discoveries),
            "total_categories": len(self.discovered_categories),
            "discovery_ids": discoveries[:10],
        }

    def get_categories_by_type(self, category_type: str) -> List[DiscoveredCategory]:
        """Get all discovered categories of a specific type."""
        return [
            cat for cat in self.discovered_categories.values()
            if cat.source_category == category_type
        ]

    def get_all_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all categories organized by type."""
        result: Dict[str, List[Dict[str, Any]]] = {}
        for cat in self.discovered_categories.values():
            if cat.source_category not in result:
                result[cat.source_category] = []
            result[cat.source_category].append({
                "name": cat.name,
                "importance": round(cat.importance, 3),
                "data_points": cat.data_points,
                "tags": cat.tags,
            })
        return result

    def get_api_state(self) -> Dict[str, Any]:
        """Get the full API state."""
        return {
            "connections": len(self.connections),
            "connected": sum(1 for c in self.connections.values() if c.status == "connected"),
            "discovered_categories": len(self.discovered_categories),
            "total_queries": sum(c.total_queries for c in self.connections.values()),
            "total_data": sum(c.data_fetched for c in self.connections.values()),
            "by_category": {
                cat: len(self.get_categories_by_type(cat))
                for cat in ["genetic", "psychonaut", "arg", "paranormal", "physics", "consciousness"]
            },
        }


# ---------------------------------------------------------------------------
# World Build Data Integration
# ---------------------------------------------------------------------------

class WorldBuildDataIntegration:
    """Integrates discovered categories into world build automation."""

    def __init__(self, api_manager: ContinentalAPIManager):
        self.api_manager = api_manager
        self.world_data: Dict[str, Any] = {}
        self.category_map: Dict[str, List[str]] = {}

    def build_category_map(self) -> Dict[str, Any]:
        """Build a map of categories to world data."""
        categories = self.api_manager.get_all_categories()

        self.category_map = {}
        for cat_type, items in categories.items():
            self.category_map[cat_type] = [item["name"] for item in items]

        return {
            "category_types": len(self.category_map),
            "total_categories": sum(len(v) for v in self.category_map.values()),
            "map": {k: len(v) for k, v in self.category_map.items()},
        }

    def feed_to_world_build(self) -> Dict[str, Any]:
        """Feed discovered categories into world build automation."""
        if not self.category_map:
            self.build_category_map()

        # Create world data structure
        self.world_data = {
            "genetic_layer": {
                "sources": self.category_map.get("genetic", []),
                "density": 0.7,
                "active": True,
            },
            "psychonaut_layer": {
                "sources": self.category_map.get("psychonaut", []),
                "density": 0.6,
                "active": True,
            },
            "arg_layer": {
                "sources": self.category_map.get("arg", []),
                "density": 0.5,
                "active": True,
            },
            "paranormal_layer": {
                "sources": self.category_map.get("paranormal", []),
                "density": 0.4,
                "active": True,
            },
            "physics_layer": {
                "sources": self.category_map.get("physics", []),
                "density": 0.8,
                "active": True,
            },
            "consciousness_layer": {
                "sources": self.category_map.get("consciousness", []),
                "density": 0.9,
                "active": True,
            },
        }

        return {
            "layers": len(self.world_data),
            "total_sources": sum(len(l["sources"]) for l in self.world_data.values()),
            "active_layers": sum(1 for l in self.world_data.values() if l["active"]),
        }

    def get_world_data(self) -> Dict[str, Any]:
        """Get the integrated world data."""
        return self.world_data


# Global instances
continental_api = ContinentalAPIManager()
world_build_integration = WorldBuildDataIntegration(continental_api)
