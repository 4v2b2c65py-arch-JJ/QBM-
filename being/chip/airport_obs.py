#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Airport Observation Module

Integrates airport data sources for micro-management:
- OurAirports: 70,000+ airports, CSV/KML downloads
- AirportDB: 60k airports, runways, frequencies, navaids (JSON API)
- AirportsAPI: Free public API, global airport data
- OpenStreetMap Overpass: Airport boundaries, runways, terminals

Provides airport-specific flicker streams and observation modes.
"""

from __future__ import annotations

import csv
import io
import json
import math
import random
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.airport_obs")


class AirportType(Enum):
    """Airport classification."""
    LARGE = "large_airport"
    MEDIUM = "medium_airport"
    SMALL = "small_airport"
    HELIPORT = "heliport"
    SEAPLANE = "seaplane_base"
    BALLOONPORT = "balloonport"
    CLOSED = "closed"


@dataclass
class Airport:
    """Airport data structure."""
    icao: str
    iata: str
    name: str
    latitude: float
    longitude: float
    elevation_ft: float
    type: AirportType
    country: str
    region: str
    municipality: str
    runways: List[Dict[str, Any]] = field(default_factory=list)
    frequencies: List[Dict[str, Any]] = field(default_factory=list)
    navaids: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def location(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

    def distance_to(self, other: 'Airport') -> float:
        """Calculate distance in km using haversine."""
        R = 6371
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))


@dataclass
class Runway:
    """Runway data structure."""
    airport_icao: str
    length_ft: float
    width_ft: float
    surface: str
    lighted: bool
    closed: bool
    ident_le: str  # Landing end identifier
    ident_he: str  # Heading end identifier
    heading_le_deg: float
    heading_he_deg: float


@dataclass
class Navaid:
    """Navigation aid structure."""
    ident: str
    name: str
    type: str  # VOR, NDB, DME, TACAN, etc
    frequency_khz: float
    latitude: float
    longitude: float
    elevation_ft: float
    country: str


class AirportDataSource:
    """
    Manages airport data from multiple sources.
    
    Supports:
    - OurAirports CSV downloads (70k+ airports)
    - AirportDB JSON API (60k airports + details)
    - AirportsAPI public API
    - OSM Overpass for boundaries/runways
    """

    OURAIRPORTS_BASE = "https://davidmegginson.github.io/ourairports-data/"
    AIRPORTDB_BASE = "https://airportdb.io/api/v1"

    def __init__(self):
        self.airports: Dict[str, Airport] = {}
        self.runways: Dict[str, List[Runway]] = {}
        self.navaids: Dict[str, Navaid] = {}
        self.frequencies: Dict[str, List[Dict]] = {}

    def fetch_ourairports_csv(self, dataset: str = "airports") -> Optional[str]:
        """Fetch OurAirports CSV data."""
        url = f"{self.OURAIRPORTS_BASE}{dataset}.csv"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QB-Protocol/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except Exception as e:
            LOG.error(f"Failed to fetch {dataset}: {e}")
            return None

    def parse_ourairports_airports(self, csv_data: str) -> List[Airport]:
        """Parse OurAirports airports CSV."""
        airports = []
        reader = csv.DictReader(io.StringIO(csv_data))

        for row in reader:
            try:
                airport = Airport(
                    icao=row.get('ident', ''),
                    iata=row.get('iata_code', ''),
                    name=row.get('name', ''),
                    latitude=float(row.get('latitude_deg', 0)),
                    longitude=float(row.get('longitude_deg', 0)),
                    elevation_ft=float(row.get('elevation_ft', 0)),
                    type=AirportType(row.get('type', 'small_airport')),
                    country=row.get('iso_country', ''),
                    region=row.get('iso_region', ''),
                    municipality=row.get('municipality', ''),
                )
                airports.append(airport)
                self.airports[airport.icao] = airport
            except (ValueError, KeyError):
                continue

        return airports

    def fetch_airportdb_airport(self, icao: str) -> Optional[Dict[str, Any]]:
        """Fetch single airport details from AirportDB API."""
        url = f"{self.AIRPORTDB_BASE}/airport/{icao}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QB-Protocol/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception:
            return None

    def generate_overpass_airport_query(self, bbox: Tuple[float, float, float, float]) -> str:
        """
        Generate Overpass query for airport data.
        
        Queries OSM for:
        - Aeroway=aerodrome (airports)
        - Aeroway=runway
        - Aeroway=taxiway
        - Aeroway=terminal
        """
        s, w, n, e = bbox
        return f"""
[out:json][timeout:50];
(
  way["aeroway"="aerodrome"]({s},{w},{n},{e});
  node["aeroway"="aerodrome"]({s},{w},{n},{e});
  way["aeroway"="runway"]({s},{w},{n},{e});
  way["aeroway"="taxiway"]({s},{w},{n},{e});
  way["aeroway"="terminal"]({s},{w},{n},{e});
);
out geom;
"""

    def generate_overpass_navaid_query(self, bbox: Tuple[float, float, float, float]) -> str:
        """Generate Overpass query for navaids."""
        s, w, n, e = bbox
        return f"""
[out:json][timeout:25];
(
  node["aeroway"="navaid"]({s},{w},{n},{e});
  node["aeroway"="beacon"]({s},{w},{n},{e});
);
out geom;
"""

    def generate_overpass_frequencies_query(self, icao: str) -> str:
        """Generate Overpass query for airport frequencies."""
        return f"""
[out:json][timeout:25];
(
  node["aeroway"="aerodrome"]["icao"="{icao}"];
  way["aeroway"="aerodrome"]["icao"="{icao}"];
);
out tags;
"""


class AirportFlickerObserver:
    """
    Flicker-based airport observation streams.
    
    Creates controllable data streams for:
    - Airport arrival/departure simulation
    - Runway usage patterns
    - Frequency monitoring
    - Navaid status
    """

    def __init__(self):
        self.data_source = AirportDataSource()
        self.active_airports: Dict[str, Airport] = {}

    def create_airport_stream(self, airport: Airport) -> Dict[str, Any]:
        """Create flicker stream configuration for an airport."""
        def airport_generator():
            """Generate airport observation frame."""
            # Simulate airport activity
            activity_level = random.choice(['low', 'medium', 'high', 'peak'])
            flights = {
                'low': random.randint(0, 5),
                'medium': random.randint(5, 20),
                'high': random.randint(20, 50),
                'peak': random.randint(50, 100),
            }[activity_level]

            return {
                'icao': airport.icao,
                'iata': airport.iata,
                'name': airport.name,
                'activity': activity_level,
                'flights_current': flights,
                'flights_arrivals': random.randint(0, flights),
                'flights_departures': random.randint(0, flights),
                'runways_active': random.sample(
                    [r['ident_le'] for r in airport.runways] if airport.runways else ['09L'],
                    min(2, max(1, len(airport.runways)))
                ),
                'weather': random.choice(['VFR', 'MVFR', 'IFR', 'LIFR']),
                'visibility_sm': round(random.uniform(0.5, 10), 1),
                'ceiling_ft': random.choice([500, 1000, 2500, 5000, 10000, 25000]),
                'wind_deg': random.randint(0, 359),
                'wind_kts': random.randint(0, 30),
                'timestamp': random.randint(1700000000, 1800000000),
            }

        return {
            'stream_id': f'airport_{airport.icao}',
            'source': airport.name,
            'min_hz': 0.1,
            'max_hz': 30,
            'base_hz': 5 if airport.type == AirportType.LARGE else (2 if airport.type == AirportType.MEDIUM else 0.5),
            'generator': airport_generator,
            'airport': airport,
        }

    def create_navaid_stream(self, navaid: Navaid) -> Dict[str, Any]:
        """Create flicker stream for a navaid."""
        def navaid_generator():
            return {
                'ident': navaid.ident,
                'type': navaid.type,
                'frequency_khz': navaid.frequency_khz,
                'status': random.choice(['operational', 'operational', 'operational', 'maintenance']),
                'signal_strength': round(random.uniform(0.7, 1.0), 2),
            }

        return {
            'stream_id': f'navaid_{navaid.ident}',
            'source': f'{navaid.type} {navaid.ident}',
            'min_hz': 0.01,
            'max_hz': 1,
            'base_hz': 0.1,
            'generator': navaid_generator,
            'navaid': navaid,
        }

    def create_frequency_stream(self, airport: Airport, freq: Dict[str, Any]) -> Dict[str, Any]:
        """Create flicker stream for an airport frequency."""
        def freq_generator():
            return {
                'icao': airport.icao,
                'frequency_mhz': freq.get('frequency_mhz', 0),
                'type': freq.get('type', 'unknown'),
                'description': freq.get('description', ''),
                'in_use': random.random() > 0.3,
                'utilization': round(random.random(), 2),
            }

        return {
            'stream_id': f'freq_{airport.icao}_{freq.get("type", "unk")}',
            'source': f'{airport.icao} {freq.get("type", "")}',
            'min_hz': 1,
            'max_hz': 60,
            'base_hz': 15,
            'generator': freq_generator,
            'frequency': freq,
        }

    def simulate_regional_airspace(self, center: Tuple[float, float],
                                     radius_km: float = 100) -> List[Dict[str, Any]]:
        """
        Simulate all airport streams in a region.
        
        Creates flicker streams for all airports within radius.
        """
        streams = []

        for icao, airport in self.active_airports.items():
            dist = self._haversine(center[0], center[1], airport.latitude, airport.longitude)
            if dist <= radius_km:
                streams.append(self.create_airport_stream(airport))
                for freq in airport.frequencies[:3]:  # Top 3 frequencies
                    streams.append(self.create_frequency_stream(airport, freq))

        return streams

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km."""
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))


class AirportNetworkAnalyzer:
    """
    Analyzes airport networks for interesting patterns.
    
    Finds:
    - Airport clusters (density zones)
    - Route corridors
    - Coverage gaps (blind spots)
    - Navaid coverage overlap
    """

    def __init__(self):
        self.airports: Dict[str, Airport] = {}

    def add_airports(self, airports: List[Airport]) -> None:
        """Add airports for analysis."""
        for ap in airports:
            self.airports[ap.icao] = ap

    def find_clusters(self, max_dist_km: float = 50) -> List[Dict[str, Any]]:
        """Find airport clusters (dense zones)."""
        clusters = []
        visited = set()

        for icao, airport in self.airports.items():
            if icao in visited:
                continue

            cluster = [airport]
            visited.add(icao)

            for other_icao, other in self.airports.items():
                if other_icao in visited:
                    continue
                if airport.distance_to(other) <= max_dist_km:
                    cluster.append(other)
                    visited.add(other_icao)

            if len(cluster) >= 2:
                avg_lat = sum(a.latitude for a in cluster) / len(cluster)
                avg_lon = sum(a.longitude for a in cluster) / len(cluster)
                clusters.append({
                    'center': (round(avg_lat, 4), round(avg_lon, 4)),
                    'airport_count': len(cluster),
                    'airports': [a.icao for a in cluster],
                    'density': len(cluster) / (math.pi * max_dist_km**2),
                })

        return sorted(clusters, key=lambda x: -x['airport_count'])

    def find_coverage_gaps(self, min_spacing_km: float = 100) -> List[Dict[str, Any]]:
        """Find areas with sparse airport coverage."""
        gaps = []

        if not self.airports:
            return gaps

        # Get bounds
        lats = [a.latitude for a in self.airports.values()]
        lons = [a.longitude for a in self.airports.values()]

        # Sample grid points
        for lat in range(int(min(lats)), int(max(lats)), 2):
            for lon in range(int(min(lons)), int(max(lons)), 2):
                min_dist = min(
                    self._haversine(lat, lon, a.latitude, a.longitude)
                    for a in self.airports.values()
                )
                if min_dist >= min_spacing_km:
                    gaps.append({
                        'location': (lat, lon),
                        'nearest_airport_km': round(min_dist, 1),
                        'type': 'coverage_gap',
                    })

        return sorted(gaps, key=lambda x: -x['nearest_airport_km'])[:20]

    def analyze_runway_patterns(self) -> Dict[str, Any]:
        """Analyze runway orientation patterns."""
        headings = []
        for airport in self.airports.values():
            for runway in airport.runways:
                headings.append(runway.get('heading_le_deg', 0))

        if not headings:
            return {'error': 'no runway data'}

        # Common runway orientations
        heading_counts = {}
        for h in headings:
            bucket = int(h / 10) * 10
            heading_counts[bucket] = heading_counts.get(bucket, 0) + 1

        return {
            'total_runways': len(headings),
            'heading_distribution': dict(sorted(heading_counts.items())),
            'most_common_heading': max(heading_counts, key=heading_counts.get) if heading_counts else None,
            'parallel_runway_pairs': sum(1 for c in heading_counts.values() if c >= 2),
        }

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km."""
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))


# Global instance
airport_observer = AirportFlickerObserver()
airport_network = AirportNetworkAnalyzer()
airport_data = AirportDataSource()
