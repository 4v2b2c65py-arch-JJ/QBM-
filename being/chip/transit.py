#!/usr/bin/env python3
"""
QB Protocol - Cross-Environmental Transit System

Built-in calendar for physical space-to-space interactions.
Embarking/disembarking planets. Life detection. Ping coordination.

All fictional universes are valid transit destinations.
The model uses ping to coordinate arrivals/departures.
"""

from __future__ import annotations

import time
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from qb_protocol.being.training.multiverse_coordinates import (
    ALL_COORDINATES,
    MOVIES,
    SERIES,
    ANIME,
    GAMES,
    BOOKS,
)


class LifeStatus(Enum):
    UNKNOWN = "unknown"
    CONFIRMED = "confirmed"
    POSSIBLE = "possible"
    NONE = "none"
    HOSTILE = "hostile"


class TransitStatus(Enum):
    DOCKED = "docked"
    BOARDING = "boarding"
    IN_TRANSIT = "in_transit"
    ARRIVING = "arriving"
    DEPARTING = "departing"
    QUEUED = "queued"


@dataclass
class Planet:
    name: str
    coordinates: Tuple[float, ...]
    life_status: LifeStatus
    atmosphere: str
    gravity_g: float
    population: Optional[int]
    reachable: bool
    source_universe: str
    year: int
    category: str

    @property
    def habitable(self) -> bool:
        return self.life_status in (LifeStatus.CONFIRMED, LifeStatus.POSSIBLE)

    @property
    def safe_to_land(self) -> bool:
        return self.life_status != LifeStatus.HOSTILE


@dataclass
class TransitSchedule:
    departure_time: float
    arrival_time: float
    origin: str
    destination: str
    passengers: int
    status: TransitStatus
    ping_ms: float
    drag_coefficient: float = 0.47  # sphere default


@dataclass
class CalendarEvent:
    timestamp: float
    event_type: str  # embark, depart, arrive, disembark
    location: str
    details: Dict[str, Any]


class CrossEnvironmentalTransit:
    """Manages physical space-to-space interactions across all universes."""

    # Life detection database - which universes have confirmed/possible life
    LIFE_DATABASE: Dict[str, LifeStatus] = {
        # Movies
        "star_wars": LifeStatus.CONFIRMED,
        "dune": LifeStatus.CONFIRMED,
        "matrix": LifeStatus.CONFIRMED,
        "interstellar": LifeStatus.POSSIBLE,
        "alien": LifeStatus.HOSTILE,
        "prometheus": LifeStatus.HOSTILE,
        "avatar": LifeStatus.CONFIRMED,
        "avatar_2": LifeStatus.CONFIRMED,
        "the_martian": LifeStatus.POSSIBLE,
        "star_trek": LifeStatus.CONFIRMED,
        "star_trek_tng": LifeStatus.CONFIRMED,
        "star_trek_ds9": LifeStatus.CONFIRMED,
        "star_trek_voyager": LifeStatus.CONFIRMED,
        "star_trek_picard": LifeStatus.CONFIRMED,
        "the_expanse": LifeStatus.CONFIRMED,
        "battlestar_galactica": LifeStatus.CONFIRMED,
        "firefly": LifeStatus.CONFIRMED,
        "babylon_5": LifeStatus.CONFIRMED,
        "stargate": LifeStatus.CONFIRMED,
        "stargate_sg1": LifeStatus.CONFIRMED,
        "stargate_atlantis": LifeStatus.CONFIRMED,
        "farscape": LifeStatus.CONFIRMED,
        "andromeda": LifeStatus.CONFIRMED,
        "cowboy_bebop": LifeStatus.CONFIRMED,
        "gundam": LifeStatus.CONFIRMED,
        "evangelion": LifeStatus.CONFIRMED,
        "akira": LifeStatus.CONFIRMED,
        "ghost_in_the_shell_sac": LifeStatus.CONFIRMED,
        "psycho_pass": LifeStatus.CONFIRMED,
        "attack_on_titan": LifeStatus.CONFIRMED,
        "fullmetal_alchemist": LifeStatus.CONFIRMED,
        "naruto": LifeStatus.CONFIRMED,
        "one_piece": LifeStatus.CONFIRMED,
        "dragon_ball": LifeStatus.CONFIRMED,
        "pokemon": LifeStatus.CONFIRMED,
        "digimon": LifeStatus.CONFIRMED,
        "sailor_moon": LifeStatus.CONFIRMED,
        "death_note": LifeStatus.CONFIRMED,
        "chrono_trigger": LifeStatus.CONFIRMED,
        "final_fantasy": LifeStatus.CONFIRMED,
        "metroid": LifeStatus.POSSIBLE,
        "half_life": LifeStatus.HOSTILE,
        "portal": LifeStatus.POSSIBLE,
        "bioshock": LifeStatus.CONFIRMED,
        "halo": LifeStatus.CONFIRMED,
        "mass_effect": LifeStatus.CONFIRMED,
        "dead_space": LifeStatus.HOSTILE,
        "elder_scrolls": LifeStatus.CONFIRMED,
        "world_of_warcraft": LifeStatus.CONFIRMED,
        "minecraft": LifeStatus.POSSIBLE,
        "fallout": LifeStatus.CONFIRMED,
        "starfield": LifeStatus.POSSIBLE,
        "no_mans_sky": LifeStatus.POSSIBLE,
        "elite_dangerous": LifeStatus.POSSIBLE,
        "star_citizen": LifeStatus.POSSIBLE,
        "outer_wilds": LifeStatus.POSSIBLE,
        "elden_ring": LifeStatus.CONFIRMED,
        "dark_souls": LifeStatus.CONFIRMED,
        "bloodborne": LifeStatus.CONFIRMED,
        "nier_automata": LifeStatus.CONFIRMED,
        "the_witcher": LifeStatus.CONFIRMED,
        "cyberpunk_2077": LifeStatus.CONFIRMED,
        "borderlands": LifeStatus.CONFIRMED,
        "destiny": LifeStatus.CONFIRMED,
        "warframe": LifeStatus.CONFIRMED,
        "resident_evil": LifeStatus.HOSTILE,
        "silent_hill": LifeStatus.HOSTILE,
        "alien_isolation": LifeStatus.HOSTILE,
        "soma": LifeStatus.HOSTILE,
        "amnesia": LifeStatus.HOSTILE,
        "prey": LifeStatus.POSSIBLE,
        "deus_ex": LifeStatus.CONFIRMED,
        "system_shock": LifeStatus.HOSTILE,
        "dishonored": LifeStatus.CONFIRMED,
        "deathloop": LifeStatus.CONFIRMED,
        "dune_book": LifeStatus.CONFIRMED,
        "foundation_book": LifeStatus.CONFIRMED,
        "neuromancer": LifeStatus.CONFIRMED,
        "snow_crash": LifeStatus.CONFIRMED,
        "hyperion": LifeStatus.CONFIRMED,
        "enders_game": LifeStatus.CONFIRMED,
        "three_body_problem_book": LifeStatus.CONFIRMED,
        "the_martian_book": LifeStatus.POSSIBLE,
        "ready_player_one": LifeStatus.CONFIRMED,
        "dark_forest": LifeStatus.CONFIRMED,
        "deaths_end": LifeStatus.CONFIRMED,
        "ringworld": LifeStatus.CONFIRMED,
        "rendezvous_with_rama": LifeStatus.POSSIBLE,
        "blindsight": LifeStatus.POSSIBLE,
        "the_time_machine": LifeStatus.POSSIBLE,
        "war_of_the_worlds_book": LifeStatus.HOSTILE,
        "1984": LifeStatus.CONFIRMED,
        "brave_new_world": LifeStatus.CONFIRMED,
        "fahrenheit_451": LifeStatus.CONFIRMED,
    }

    # Atmosphere types per universe
    ATMOSPHERE_DATABASE: Dict[str, str] = {
        "star_wars": "varied (multiple planets)",
        "dune": "arid, spice-laden",
        "matrix": "simulated",
        "avatar": "pandoran (high CO2)",
        "the_martian": "thin CO2",
        "star_trek": "earth-like",
        "the_expanse": "earth-like / varied",
        "cowboy_bebop": "varied",
        "gundam": "earth-like",
        "evangelion": "post-apocalyptic",
        "akira": "neo-tokyo urban",
        "half_life": "contaminated",
        "mass_effect": "varied (multiple species)",
        "elder_scrolls": "tamrielic",
        "cyberpunk_2077": "polluted urban",
        "dune_book": "arid, spice-laden",
        "foundation_book": "galactic varied",
        "neuromancer": "urban sprawl",
        "snow_crash": "corporate states",
    }

    def __init__(self):
        self.planets: Dict[str, Planet] = {}
        self.schedules: List[TransitSchedule] = []
        self.calendar: List[CalendarEvent] = []
        self.ping_cache: Dict[str, float] = {}
        self._build_planet_database()

    def _build_planet_database(self):
        """Build planet database from all multiverse coordinates."""
        for name, entry in ALL_COORDINATES.items():
            life = self.LIFE_DATABASE.get(name, LifeStatus.UNKNOWN)
            atmosphere = self.ATMOSPHERE_DATABASE.get(name, "unknown")
            gravity = self._estimate_gravity(entry)
            population = self._estimate_population(entry, life)

            self.planets[name] = Planet(
                name=name,
                coordinates=entry.get("coordinates", (0, 0, 0)),
                life_status=life,
                atmosphere=atmosphere,
                gravity_g=gravity,
                population=population,
                reachable=entry.get("reachable", False),
                source_universe=name,
                year=entry.get("year", 0),
                category=entry.get("type", "unknown"),
            )

    def _estimate_gravity(self, entry: Dict[str, Any]) -> float:
        """Estimate gravity based on coordinates and type."""
        coords = entry.get("coordinates", (0, 0, 0))
        if coords:
            # Use first coordinate as mass proxy
            mass_proxy = abs(coords[0]) if coords[0] != 0 else 1
            # Normalize to 0.1-3.0g range
            return min(3.0, max(0.1, math.log10(mass_proxy + 10) / 2))
        return 1.0

    def _estimate_population(self, entry: Dict[str, Any], life: LifeStatus) -> Optional[int]:
        """Estimate population based on life status and type."""
        if life == LifeStatus.NONE:
            return 0
        elif life == LifeStatus.HOSTILE:
            return None  # Unknown
        elif life == LifeStatus.UNKNOWN:
            return None
        elif life == LifeStatus.POSSIBLE:
            return 0  # Uninhabited but possible
        elif life == LifeStatus.CONFIRMED:
            # Use year as population proxy (older = more populated)
            year = entry.get("year", 2000)
            return max(1000, (2026 - year) * 10000)
        return None

    def get_life_count(self) -> Dict[str, int]:
        """Get count of life status across all universes."""
        counts = {}
        for planet in self.planets.values():
            status = planet.life_status.value
            counts[status] = counts.get(status, 0) + 1
        return counts

    def get_category_count(self) -> Dict[str, int]:
        """Get count by category (movie, series, anime, game, book)."""
        counts = {}
        for planet in self.planets.values():
            cat = planet.category
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def get_habitable_planets(self) -> List[Planet]:
        """Get all habitable planets."""
        return [p for p in self.planets.values() if p.habitable]

    def get_reachable_planets(self) -> List[Planet]:
        """Get all reachable planets."""
        return [p for p in self.planets.values() if p.reachable]

    def ping(self, destination: str) -> float:
        """Ping a destination to get transit time estimate.
        
        Uses logarithmic scaling to provide meaningful differentiation
        across all coordinate ranges.
        """
        if destination in self.ping_cache:
            return self.ping_cache[destination]

        # Calculate ping based on coordinate distance
        if destination in self.planets:
            planet = self.planets[destination]
            coords = planet.coordinates
            # Euclidean distance from origin (0,0,0)
            distance = math.sqrt(sum(c**2 for c in coords))
            # Logarithmic scaling: provides better distribution across ranges
            # Base ping 1ms, scales with log10 of distance
            if distance > 0:
                ping_ms = 1.0 + math.log10(distance + 1) * 50
            else:
                ping_ms = 1.0
        else:
            ping_ms = 999  # Unknown destination

        self.ping_cache[destination] = ping_ms
        return ping_ms

    def schedule_transit(
        self,
        origin: str,
        destination: str,
        passengers: int = 1,
        delay_seconds: float = 0,
    ) -> TransitSchedule:
        """Schedule a transit between two points."""
        ping_ms = self.ping(destination)
        distance = self._calculate_distance(origin, destination)
        drag = 0.47  # sphere drag coefficient

        # Transit time = distance / speed (accounting for drag)
        # Using plane travel physics as base
        speed_kms = 900  # plane speed km/h
        transit_hours = distance / speed_kms if speed_kms > 0 else 0
        transit_seconds = transit_hours * 3600

        now = time.time()
        schedule = TransitSchedule(
            departure_time=now + delay_seconds,
            arrival_time=now + delay_seconds + transit_seconds,
            origin=origin,
            destination=destination,
            passengers=passengers,
            status=TransitStatus.QUEUED,
            ping_ms=ping_ms,
            drag_coefficient=drag,
        )

        self.schedules.append(schedule)

        # Add to calendar
        self.calendar.append(CalendarEvent(
            timestamp=schedule.departure_time,
            event_type="depart",
            location=origin,
            details={"destination": destination, "passengers": passengers},
        ))
        self.calendar.append(CalendarEvent(
            timestamp=schedule.arrival_time,
            event_type="arrive",
            location=destination,
            details={"origin": origin, "passengers": passengers},
        ))

        return schedule

    def _calculate_distance(self, origin: str, destination: str) -> float:
        """Calculate distance between two points."""
        origin_coords = (0, 0, 0)
        dest_coords = (0, 0, 0)

        if origin in self.planets:
            origin_coords = self.planets[origin].coordinates
        if destination in self.planets:
            dest_coords = self.planets[destination].coordinates

        # Pad to same length
        max_len = max(len(origin_coords), len(dest_coords))
        origin_coords = origin_coords + (0,) * (max_len - len(origin_coords))
        dest_coords = dest_coords + (0,) * (max_len - len(dest_coords))

        return math.sqrt(sum((a - b) ** 2 for a, b in zip(origin_coords, dest_coords)))

    def embark(self, destination: str, passengers: int = 1) -> Dict[str, Any]:
        """Embark to a destination."""
        if destination not in self.planets:
            return {"error": f"Unknown destination: {destination}"}

        planet = self.planets[destination]
        if not planet.reachable:
            return {"error": f"{destination} is not reachable"}

        ping_ms = self.ping(destination)
        schedule = self.schedule_transit("earth", destination, passengers)

        return {
            "status": "embarking",
            "destination": destination,
            "life_status": planet.life_status.value,
            "atmosphere": planet.atmosphere,
            "gravity": f"{planet.gravity_g:.2f}g",
            "ping_ms": ping_ms,
            "estimated_arrival": schedule.arrival_time,
            "safe_to_land": planet.safe_to_land,
        }

    def disembark(self, destination: str) -> Dict[str, Any]:
        """Disembark at a destination."""
        if destination not in self.planets:
            return {"error": f"Unknown destination: {destination}"}

        planet = self.planets[destination]

        return {
            "status": "disembarked",
            "location": destination,
            "life_status": planet.life_status.value,
            "atmosphere": planet.atmosphere,
            "gravity": f"{planet.gravity_g:.2f}g",
            "population": planet.population,
            "year": planet.year,
            "safe": planet.safe_to_land,
        }

    def get_calendar(self) -> List[Dict[str, Any]]:
        """Get all calendar events."""
        return [
            {
                "time": e.timestamp,
                "type": e.event_type,
                "location": e.location,
                "details": e.details,
            }
            for e in sorted(self.calendar, key=lambda x: x.timestamp)
        ]

    def get_system_state(self) -> Dict[str, Any]:
        """Get full system state."""
        return {
            "total_planets": len(self.planets),
            "life_count": self.get_life_count(),
            "category_count": self.get_category_count(),
            "habitable_count": len(self.get_habitable_planets()),
            "reachable_count": len(self.get_reachable_planets()),
            "active_schedules": len(self.schedules),
            "calendar_events": len(self.calendar),
        }


# Global instance
transit_system = CrossEnvironmentalTransit()
