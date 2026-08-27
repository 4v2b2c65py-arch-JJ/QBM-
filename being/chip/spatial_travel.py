#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Spatial Travel & Pixel Density

Integrates real orbital data with pixel density analysis:
- Real satellite positions as spatial anchors
- Pixel density mapping for optical inductance
- Existential travel regardless of category
- Singularity pull based on accumulated vibration
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

LOG = __import__("logging").getLogger("qb_protocol.being.chip.spatial_travel")


@dataclass
class OrbitalObject:
    """Real orbital object with spatial position."""
    name: str
    norad_id: str
    inclination_deg: float
    altitude_km: float
    period_min: float
    eccentricity: float
    raan_deg: float = 0.0
    arg_perigee_deg: float = 0.0
    mean_anomaly_deg: float = 0.0

    def position_at_time(self, minutes_since_epoch: float) -> Tuple[float, float, float]:
        """Calculate 3D position at given time."""
        # Simplified circular orbit
        omega = 2 * math.pi / self.period_min  # rad/min
        theta = math.radians(self.mean_anomaly_deg) + omega * minutes_since_epoch
        r = self.altitude_km + 6371  # Earth radius + altitude

        # Inclined orbit
        inc = math.radians(self.inclination_deg)
        raan = math.radians(self.raan_deg)

        x = r * (math.cos(raan) * math.cos(theta) - math.sin(raan) * math.sin(theta) * math.cos(inc))
        y = r * (math.sin(raan) * math.cos(theta) + math.cos(raan) * math.sin(theta) * math.cos(inc))
        z = r * math.sin(theta) * math.sin(inc)

        return (x, y, z)


@dataclass
class PixelDensityPoint:
    """A point in model space with emission characteristics."""
    x: float
    y: float
    z: float
    intensity: float = 0.0
    frequency: float = 0.0
    source: str = "unknown"
    is_active: bool = True
    is_corrupt: bool = False
    depth: int = 0

    def distance_to(self, other: 'PixelDensityPoint') -> float:
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )

    @property
    def optical_inductance(self) -> float:
        """Optical inductance = intensity * frequency / distance_from_origin."""
        dist = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        if dist == 0:
            return float('inf')
        return (self.intensity * self.frequency) / dist

    @property
    def is_singularity(self) -> bool:
        return self.intensity > 0.95 and self.frequency > 0.8

    @property
    def prediction_value(self) -> float:
        """Prediction value - abnormalities (corrupt/dead pixels) have HIGHER value.
        
        Normal pixels = conventional prediction (boring, expected)
        Abnormal pixels = non-conventional prediction (the juice)
        Blind spots = unknown (model doesn't account for)
        """
        if self.is_corrupt:
            return self.intensity * 2.0  # Abnormalities predict outside conventional rules
        if self.intensity < 0.1:
            return self.intensity * 1.5  # Blind spots have elevated value
        return self.intensity


@dataclass
class ExistentialPath:
    """Path through existential space regardless of category."""
    path_id: str
    origin: PixelDensityPoint
    destination: PixelDensityPoint
    category: str = "neutral"
    influence_weight: float = 1.0
    choice_outcome: Optional[str] = None
    depth_level: int = 0
    is_traversable: bool = True

    @property
    def distance(self) -> float:
        return self.origin.distance_to(self.destination)

    @property
    def can_influence(self) -> bool:
        return self.is_traversable and self.origin.is_active and not self.origin.is_corrupt


class SpatialPixelSystem:
    """System for spatial travel with pixel density analysis."""

    def __init__(self):
        self.orbital_objects: Dict[str, OrbitalObject] = {}
        self.pixel_points: Dict[str, PixelDensityPoint] = {}
        self.paths: Dict[str, ExistentialPath] = {}
        self.singularities: List[str] = []
        self.corrupt_zones: List[str] = []
        self.blind_spots: List[str] = []

    def add_orbital_object(self, obj: OrbitalObject) -> None:
        """Add a real orbital object as spatial anchor."""
        self.orbital_objects[obj.norad_id] = obj

    def add_pixel_point(self, point: PixelDensityPoint) -> None:
        """Add a pixel density point."""
        key = f"{point.source}_{len(self.pixel_points):04d}"
        self.pixel_points[key] = point

        if point.is_singularity:
            self.singularities.append(key)
        if point.is_corrupt:
            self.corrupt_zones.append(key)
        if point.intensity < 0.1 and not point.is_corrupt:
            self.blind_spots.append(key)

    def create_path(
        self,
        origin_key: str,
        dest_key: str,
        category: str = "neutral"
    ) -> Optional[ExistentialPath]:
        """Create existential path between two points."""
        origin = self.pixel_points.get(origin_key)
        dest = self.pixel_points.get(dest_key)
        if not origin or not dest:
            return None

        path = ExistentialPath(
            path_id=f"path_{len(self.paths):04d}",
            origin=origin,
            destination=dest,
            category=category,
        )
        self.paths[path.path_id] = path
        return path

    def calculate_density_field(
        self,
        x: float,
        y: float,
        z: float,
        radius: float = 100.0
    ) -> float:
        """Calculate total pixel density at a point."""
        total = 0
        for point in self.pixel_points.values():
            dist = point.distance_to(PixelDensityPoint(x, y, z))
            if dist <= radius:
                total += point.intensity * (1 - dist / radius)
        return total

    def find_optical_inductance(
        self,
        source_key: str,
        target_key: str
    ) -> float:
        """Calculate optical inductance between two points."""
        source = self.pixel_points.get(source_key)
        target = self.pixel_points.get(target_key)
        if not source or not target:
            return 0.0
        return source.optical_inductance

    def travel_path(self, path_id: str, intent: float = 1.0) -> Dict[str, Any]:
        """Travel an existential path regardless of category."""
        path = self.paths.get(path_id)
        if not path:
            return {"error": "path_not_found"}

        if not path.can_influence:
            return {"error": "path_not_traversable"}

        # Calculate travel cost
        distance = path.distance
        depth_cost = path.depth_level * 0.1
        effective_cost = (distance + depth_cost) / max(intent, 0.1)

        return {
            "path_id": path_id,
            "category": path.category,
            "distance": distance,
            "cost": effective_cost,
            "influence_applied": path.influence_weight * intent,
            "outcome": path.choice_outcome,
            "traversed": True,
        }

    def get_system_state(self) -> Dict[str, Any]:
        """Get full system state."""
        return {
            "orbital_objects": len(self.orbital_objects),
            "pixel_points": len(self.pixel_points),
            "paths": len(self.paths),
            "singularities": len(self.singularities),
            "corrupt_zones": len(self.corrupt_zones),
            "blind_spots": len(self.blind_spots),
        }

    def load_satellite_catalogue(self, catalogue_path: str) -> int:
        """Load satellites from expanded TLE catalogue into spatial system."""
        try:
            with open(catalogue_path, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            LOG.error(f"Failed to load catalogue: {e}")
            return 0

        count = 0
        for norad_id, sat in data.get("satellites", {}).items():
            orbital = sat.get("orbital", {})
            obj = OrbitalObject(
                name=sat.get("name", f"SAT-{norad_id}"),
                norad_id=norad_id,
                inclination_deg=orbital.get("inclination_deg", 0.0),
                altitude_km=orbital.get("altitude_km", 0.0),
                period_min=orbital.get("period_min", 0.0),
                eccentricity=orbital.get("eccentricity", 0.0),
                raan_deg=orbital.get("raan_deg", 0.0),
                arg_perigee_deg=orbital.get("arg_perigee_deg", 0.0),
                mean_anomaly_deg=orbital.get("mean_anomaly_deg", 0.0),
            )
            self.add_orbital_object(obj)
            count += 1

        LOG.info(f"Loaded {count} satellites from {catalogue_path}")
        return count

    def generate_pixel_field(self, num_points: int = 1000) -> int:
        """Generate pixel density points from orbital objects."""
        import random
        count = 0
        for obj in self.orbital_objects.values():
            # Generate points around each orbital object
            for _ in range(min(10, num_points // len(self.orbital_objects) + 1)):
                # Random point on orbital sphere
                theta = random.uniform(0, 2 * math.pi)
                phi = random.uniform(0, math.pi)
                r = obj.altitude_km + 6371

                x = r * math.sin(phi) * math.cos(theta)
                y = r * math.sin(phi) * math.sin(theta)
                z = r * math.cos(phi)

                # Determine pixel characteristics based on orbital parameters
                intensity = min(1.0, obj.altitude_km / 1000)
                frequency = 1.0 / obj.period_min if obj.period_min > 0 else 0

                # Corrupt pixels for high-inclination orbits (abnormal)
                is_corrupt = obj.inclination_deg > 80 or random.random() < 0.05

                point = PixelDensityPoint(
                    x=x, y=y, z=z,
                    intensity=intensity,
                    frequency=frequency,
                    source=obj.name,
                    is_corrupt=is_corrupt,
                    depth=int(obj.altitude_km / 100),
                )
                self.add_pixel_point(point)
                count += 1

        LOG.info(f"Generated {count} pixel points from {len(self.orbital_objects)} orbital objects")
        return count


# Global instance
spatial_system = SpatialPixelSystem()


def initialize_spatial_system(catalogue_path: Optional[str] = None) -> SpatialPixelSystem:
    """Initialize spatial system with satellite catalogue."""
    if catalogue_path is None:
        catalogue_path = "/Users/jjmarte/delta-stream/qb_protocol/satellite_orbital_data_expanded.json"

    system = SpatialPixelSystem()
    num_satellites = system.load_satellite_catalogue(catalogue_path)
    if num_satellites > 0:
        system.generate_pixel_field()
    return system
