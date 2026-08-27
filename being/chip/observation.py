#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Broad Observation Toolkit

Integrates ground-level observation with satellite spatial awareness:
- DeFlock-style ALPR/surveillance camera mapping framework
- Overpass Turbo query generator for OpenStreetMap recon
- Flock Finder: Starlink/OneWeb constellation tracker
- Creative observation modes for pattern discovery
- Micro-management tools for surveillance awareness
- Recon task generator with spatial + ground fusion

Inspiration: maps.deflock.org, overpass-turbo.eu, flock-finder
"""

from __future__ import annotations

import json
import math
import random
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.observation")


class ObservationMode(Enum):
    """Observation creativity modes."""
    SURVEILLANCE_AWARE = "surveillance_aware"    # Camera/ALPR awareness
    CONSTELLATION_TRACK = "constellation_track"  # Satellite flock tracking
    PATTERN_HUNT = "pattern_hunt"                # Find interesting patterns
    RECON_SWEEP = "recon_sweep"                  # Systematic area recon
    CREATIVE_WANDER = "creative_wander"          # Serendipitous discovery
    MICRO_MANAGE = "micro_manage"                # Detailed zone management


@dataclass
class ALPRCamera:
    """ALPR/surveillance camera observation point."""
    camera_id: str
    latitude: float
    longitude: float
    source: str = "deflock"  # deflock, flock, manual
    operator: str = "unknown"  # flock_safety, motorola, vigilant, etc
    direction_deg: float = 0.0
    mount_type: str = "pole"  # pole, gantry, building
    date_reported: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def location(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)


@dataclass
class SatelliteSighting:
    """Satellite flock observation."""
    satellite_name: str
    norad_id: str
    altitude_km: float
    azimuth_deg: float = 0.0
    elevation_deg: float = 0.0
    brightness_mag: float = 0.0
    timestamp: str = ""
    constellation: str = "unknown"  # starlink, oneweb, iridium, etc


@dataclass
class OverpassQuery:
    """Generated Overpass Turbo query for OSM recon."""
    query_id: str
    description: str
    query_text: str
    bbox: Optional[Tuple[float, float, float, float]] = None  # S, W, N, E
    expected_results: str = ""
    export_url: str = ""

    def to_turbo_url(self) -> str:
        """Generate overpass-turbo.eu URL."""
        encoded = urllib.parse.quote(self.query_text)
        base = "https://overpass-turbo.eu/?Q="
        if self.bbox:
            s, w, n, e = self.bbox
            return f"{base}{encoded}&C={s};{w};{n};{e}"
        return f"{base}{encoded}"


@dataclass
class ObservationTask:
    """A creative observation/recon task."""
    task_id: str
    description: str
    mode: ObservationMode
    priority: int = 1
    latitude: float = 0.0
    longitude: float = 0.0
    radius_m: float = 1000.0
    subtasks: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    queries: List[OverpassQuery] = field(default_factory=list)
    completed: bool = False


class DeFlockObserver:
    """
    Surveillance camera observation framework.
    
    Inspired by maps.deflock.org - maps ALPR cameras and finds
    privacy-optimized routes. Since we can't access the real API directly,
    we build a framework that can interface with OSM/Overpass data.
    """

    # Major US cities with known ALPR density (approximate camera counts)
    KNOWN_HOTSPOTS = {
        "miami": (25.7617, -80.1918, 2800),
        "new_york": (40.7128, -74.0060, 4200),
        "los_angeles": (34.0522, -118.2437, 3800),
        "chicago": (41.8781, -87.6298, 3200),
        "houston": (29.7604, -95.3698, 2100),
        "dallas": (32.7767, -96.7970, 1800),
        "atlanta": (33.7490, -84.3880, 4300),
        "washington_dc": (38.9072, -77.0369, 1400),
    }

    # ALPR brands/operators
    OPERATORS = [
        "flock_safety", "motorola_solutions", "vigilant_solutions",
        "rekor_systems", "genetec", "neology", "petrovec", "unknown"
    ]

    def __init__(self):
        self.cameras: List[ALPRCamera] = []
        self.privacy_routes: List[Dict[str, Any]] = []

    def generate_overpass_query(self, bbox: Tuple[float, float, float, float],
                                  operator: Optional[str] = None) -> OverpassQuery:
        """
        Generate Overpass Turbo query for ALPR cameras.
        
        Queries OSM for surveillance=ALPR nodes/ways in bounding box.
        """
        s, w, n, e = bbox

        # Base query for ALPR cameras
        query = f"""
[out:json][timeout:25];
(
  node["surveillance"="ALPR"]({s},{w},{n},{e});
  node["man_made"="surveillance"]["surveillance:type"="camera"]({s},{w},{n},{e});
  node["surveillance:type"="camera"]["camera:type"="automatic"]({s},{w},{n},{e});
  way["surveillance"="ALPR"]({s},{w},{n},{e});
);
out geom;
"""

        if operator:
            # Add operator filter
            query = f"""
[out:json][timeout:25];
(
  node["surveillance"="ALPR"]["operator"="{operator}"]({s},{w},{n},{e});
  node["man_made"="surveillance"]["operator"="{operator}"]({s},{w},{n},{e});
);
out geom;
"""

        return OverpassQuery(
            query_id=f"alpr_{len(self.cameras):04d}",
            description=f"ALPR cameras in bbox ({s:.3f}, {w:.3f}, {n:.3f}, {e:.3f})",
            query_text=query.strip(),
            bbox=bbox,
            export_url=f"https://overpass-turbo.eu/?Q={urllib.parse.quote(query.strip())}"
        )

    def generate_privacy_route_query(self, start: Tuple[float, float],
                                       end: Tuple[float, float],
                                       buffer_m: float = 100) -> OverpassQuery:
        """
        Generate query for privacy-optimized route.
        
        Finds all ALPR cameras near the direct route, then
        suggests alternative paths that avoid them.
        """
        # Create bounding box around route with buffer
        min_lat = min(start[0], end[0]) - 0.01
        max_lat = max(start[0], end[0]) + 0.01
        min_lon = min(start[1], end[1]) - 0.01
        max_lon = max(start[1], end[1]) + 0.01

        query = f"""
[out:json][timeout:50];
(
  node["surveillance"="ALPR"]({min_lat},{min_lon},{max_lat},{max_lon});
  node["man_made"="surveillance"]["surveillance:type"="camera"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out geom;
"""

        return OverpassQuery(
            query_id=f"privacy_route_{len(self.privacy_routes):04d}",
            description=f"Privacy route from {start} to {end} (buffer={buffer_m}m)",
            query_text=query.strip(),
            bbox=(min_lat, min_lon, max_lat, max_lon),
        )

    def simulate_camera_field(self, center: Tuple[float, float],
                                radius_km: float = 5,
                                density_per_km2: float = 2) -> List[ALPRCamera]:
        """
        Simulate ALPR camera field for observation practice.
        
        In production, this would query real OSM data via Overpass API.
        """
        cameras = []
        num_cameras = int(math.pi * radius_km**2 * density_per_km2)

        for i in range(num_cameras):
            # Random point within radius
            r = radius_km * math.sqrt(random.random())
            theta = random.uniform(0, 2 * math.pi)

            # Convert to lat/lon offset
            lat_offset = r * math.cos(theta) / 111
            lon_offset = r * math.sin(theta) / (111 * math.cos(math.radians(center[0])))

            lat = center[0] + lat_offset
            lon = center[1] + lon_offset

            camera = ALPRCamera(
                camera_id=f"sim_{i:05d}",
                latitude=round(lat, 6),
                longitude=round(lon, 6),
                source="simulated",
                operator=random.choice(self.OPERATORS),
                direction_deg=random.uniform(0, 360),
                mount_type=random.choice(["pole", "gantry", "building", "traffic_light"]),
                tags={"surveillance": "ALPR", "simulated": "true"}
            )
            cameras.append(camera)

        self.cameras.extend(cameras)
        return cameras

    def get_hotspot_report(self) -> Dict[str, Any]:
        """Generate report on known surveillance hotspots."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_hotspots": len(self.KNOWN_HOTSPOTS),
            "hotspots": []
        }

        for city, (lat, lon, count) in sorted(
            self.KNOWN_HOTSPOTS.items(), key=lambda x: -x[1][2]
        ):
            report["hotspots"].append({
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "estimated_cameras": count,
                "density_per_km2": round(count / 500, 2),  # Assume 500km2 coverage
                "privacy_route_available": True,
            })

        return report


class FlockFinder:
    """
    Satellite constellation tracker.
    
    Tracks Starlink, OneWeb, Iridium NEXT and other satellite "flocks"
    to identify observation windows and interesting patterns.
    """

    CONSTELLATIONS = {
        "starlink": {"count": 10740, "altitude_range": (300, 600), "inc_range": (40, 98)},
        "oneweb": {"count": 651, "altitude_range": (1100, 1200), "inc_range": (87, 90)},
        "iridium_next": {"count": 80, "altitude_range": (780, 800), "inc_range": (86, 87)},
        "planet": {"count": 110, "altitude_range": (400, 600), "inc_range": (97, 98)},
        "spire": {"count": 72, "altitude_range": (400, 600), "inc_range": (51, 98)},
    }

    def __init__(self, catalogue_path: Optional[str] = None):
        self.catalogue_path = catalogue_path or "/Users/jjmarte/delta-stream/qb_protocol/satellite_orbital_data_expanded.json"
        self.catalogue: Dict[str, Any] = {}
        self.sightings: List[SatelliteSighting] = []

    def load_catalogue(self) -> bool:
        """Load satellite catalogue."""
        try:
            with open(self.catalogue_path, 'r') as f:
                self.catalogue = json.load(f)
            return True
        except Exception:
            return False

    def get_constellation_stats(self) -> Dict[str, Any]:
        """Get statistics for tracked constellations."""
        stats = {}
        for name, info in self.CONSTELLATIONS.items():
            # Count matching satellites in catalogue
            matching = sum(
                1 for s in self.catalogue.get('satellites', {}).values()
                if s.get('category') == name or name.upper() in s.get('name', '').upper()
            )
            stats[name] = {
                "catalogue_count": matching,
                "expected_count": info["count"],
                "altitude_range_km": info["altitude_range"],
                "inclination_range_deg": info["inc_range"],
                "coverage_factor": min(1.0, matching / info["count"]) if info["count"] > 0 else 0,
            }
        return stats

    def generate_observation_window(self, observer_lat: float, observer_lon: float,
                                      constellation: str = "starlink") -> Dict[str, Any]:
        """
        Generate observation window for satellite flock.
        
        Returns upcoming pass predictions for the specified constellation
        from the observer's location.
        """
        # Find satellites in this constellation
        sats = [
            s for s in self.catalogue.get('satellites', {}).values()
            if s.get('category') == constellation or constellation.upper() in s.get('name', '').upper()
        ]

        if not sats:
            return {"error": f"No satellites found for {constellation}"}

        # Simulate pass predictions
        num_passes = min(5, len(sats))
        passes = []

        for i in range(num_passes):
            sat = random.choice(sats)
            orbital = sat['orbital']

            # Calculate approximate pass time based on orbital period
            period_min = orbital['period_min']
            next_pass_min = random.uniform(0, period_min * 2)

            passes.append({
                "satellite": sat['name'],
                "norad_id": sat['norad_id'],
                "max_elevation_deg": round(random.uniform(10, 90), 1),
                "duration_sec": round(random.uniform(60, 600)),
                "direction": random.choice(["N-S", "S-N", "E-W", "W-E", "NE-SW", "NW-SE"]),
                "brightness_mag": round(random.uniform(-2, 6), 1),
                "time_to_pass_min": round(next_pass_min, 1),
            })

        passes.sort(key=lambda x: x['time_to_pass_min'])

        return {
            "observer": (observer_lat, observer_lon),
            "constellation": constellation,
            "total_available": len(sats),
            "next_passes": passes,
            "optimal_direction": "South" if observer_lat > 0 else "North",
        }

    def find_flock_formations(self) -> List[Dict[str, Any]]:
        """
        Find interesting satellite flock formations.
        
        Identifies clusters of satellites in similar orbital planes
        that create visually interesting patterns.
        """
        formations = []

        # Group by similar altitude and inclination
        clusters: Dict[Tuple[int, int], List[Dict]] = {}
        for sat in self.catalogue.get('satellites', {}).values():
            if sat['category'] in ['starlink', 'oneweb']:
                alt = sat['orbital']['altitude_km']
                inc = sat['orbital']['inclination_deg']
                key = (int(alt / 50) * 50, int(inc / 2) * 2)
                clusters.setdefault(key, []).append(sat)

        # Find significant clusters
        for (alt, inc), sats in sorted(clusters.items(), key=lambda x: -len(x[1])):
            if len(sats) >= 10:
                formations.append({
                    "type": "orbital_train",
                    "altitude_km": alt,
                    "inclination_deg": inc,
                    "satellite_count": len(sats),
                    "constellation": sats[0]['category'],
                    "visual_description": f"Train of {len(sats)} satellites at {alt}km, {inc}° inclination",
                    "best_observed": "dawn/dusk" if alt < 600 else "night",
                })

        return formations[:10]


class ObservationToolkit:
    """
    Main observation toolkit integrating all observation capabilities.
    
    Provides creative observation, micro-management, and recon tasking
    with spatial + ground sensor fusion.
    """

    def __init__(self, catalogue_path: Optional[str] = None):
        self.catalogue_path = catalogue_path or "/Users/jjmarte/delta-stream/qb_protocol/satellite_orbital_data_expanded.json"
        self.deflock = DeFlockObserver()
        self.flock_finder = FlockFinder(self.catalogue_path)
        self.tasks: List[ObservationTask] = []
        self.task_counter: int = 0
        self.awareness_level: float = 0.0

    def initialize(self) -> bool:
        """Initialize all observation subsystems."""
        self.flock_finder.load_catalogue()
        self._calculate_awareness()
        return True

    def _calculate_awareness(self) -> None:
        """Calculate observation awareness from available data."""
        sat_count = len(self.flock_finder.catalogue.get('satellites', {}))
        camera_count = len(self.deflock.KNOWN_HOTSPOTS)
        self.awareness_level = math.log1p(sat_count) * (1 + camera_count / 100)

    def create_observation_task(self, description: str,
                                  mode: ObservationMode,
                                  lat: float = 0.0,
                                  lon: float = 0.0,
                                  radius_m: float = 1000) -> ObservationTask:
        """Create a creative observation task."""
        self.task_counter += 1

        task = ObservationTask(
            task_id=f"obs_{self.task_counter:04d}",
            description=description,
            mode=mode,
            latitude=lat,
            longitude=lon,
            radius_m=radius_m,
        )

        # Generate mode-specific subtasks
        task.subtasks = self._generate_subtasks(task)

        # Generate Overpass queries for ground observation
        if mode in [ObservationMode.SURVEILLANCE_AWARE, ObservationMode.RECON_SWEEP, ObservationMode.MICRO_MANAGE]:
            bbox = self._radius_to_bbox(lat, lon, radius_m)
            task.queries.append(self.deflock.generate_overpass_query(bbox))

        self.tasks.append(task)
        return task

    def _generate_subtasks(self, task: ObservationTask) -> List[str]:
        """Generate subtasks based on observation mode."""
        subtask_map = {
            ObservationMode.SURVEILLANCE_AWARE: [
                f"Map ALPR density within {task.radius_m}m of ({task.latitude}, {task.longitude})",
                "Identify camera operator distribution",
                "Find privacy-optimized exit routes",
                "Document camera mount types and directions",
            ],
            ObservationMode.CONSTELLATION_TRACK: [
                f"Track satellite passes over ({task.latitude}, {task.longitude})",
                "Predict next Starlink train visibility",
                "Map satellite ground tracks in area",
                "Calculate optimal observation windows",
            ],
            ObservationMode.PATTERN_HUNT: [
                f"Find unusual patterns near ({task.latitude}, {task.longitude})",
                "Cross-reference satellite density with ground features",
                "Identify surveillance gaps (blind spots)",
                "Map spatial anomalies",
            ],
            ObservationMode.RECON_SWEEP: [
                f"Systematic recon of {task.radius_m}m radius",
                "Catalog all observable sensors",
                "Map terrain and line-of-sight",
                "Document findings with timestamps",
            ],
            ObservationMode.CREATIVE_WANDER: [
                f"Serendipitous exploration from ({task.latitude}, {task.longitude})",
                "Follow interesting spatial gradients",
                "Let patterns emerge organically",
                "Document unexpected discoveries",
            ],
            ObservationMode.MICRO_MANAGE: [
                f"Detailed micro-management of zone at ({task.latitude}, {task.longitude})",
                "Create high-res observation grid",
                "Track changes over time",
                "Build zone dossier",
            ],
        }
        return subtask_map.get(task.mode, subtask_map[ObservationMode.CREATIVE_WANDER])

    def _radius_to_bbox(self, lat: float, lon: float, radius_m: float) -> Tuple[float, float, float, float]:
        """Convert center + radius to bounding box."""
        radius_km = radius_m / 1000
        lat_delta = radius_km / 111
        lon_delta = radius_km / (111 * math.cos(math.radians(lat)))
        return (lat - lat_delta, lon - lon_delta, lat + lat_delta, lon + lon_delta)

    def creative_observation_burst(self, center_lat: float = 25.7617,
                                     center_lon: float = -80.1918,
                                     count: int = 6) -> List[ObservationTask]:
        """Generate a burst of creative observation tasks."""
        modes = list(ObservationMode)
        tasks = []

        for i in range(count):
            mode = modes[i % len(modes)]
            # Add slight randomization to location
            lat = center_lat + random.uniform(-0.1, 0.1)
            lon = center_lon + random.uniform(-0.1, 0.1)

            task = self.create_observation_task(
                description=f"Creative observation #{i+1}: {mode.value}",
                mode=mode,
                lat=lat,
                lon=lon,
                radius_m=random.choice([500, 1000, 2000, 5000]),
            )
            tasks.append(task)

        return tasks

    def get_state(self) -> Dict[str, Any]:
        """Get comprehensive observation toolkit state."""
        return {
            "awareness_level": round(self.awareness_level, 3),
            "total_tasks": len(self.tasks),
            "deflock_hotspots": len(self.deflock.KNOWN_HOTSPOTS),
            "simulated_cameras": len(self.deflock.cameras),
            "constellations_tracked": len(self.flock_finder.CONSTELLATIONS),
            "constellation_stats": self.flock_finder.get_constellation_stats(),
            "satellite_catalogue_size": len(self.flock_finder.catalogue.get('satellites', {})),
        }


# Global instance
observation_toolkit = ObservationToolkit()
