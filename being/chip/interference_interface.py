#!/usr/bin/env python3
"""
QB Protocol - Interference Interface System

Assistive autonomous model using wave interference patterns for interaction.
Customizable interactive panels of information.
Each panel is configurable per user/environment.

Interference usage: constructive/destructive patterns determine
what information is amplified (shown) or suppressed (hidden).
"""

from __future__ import annotations

import math
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class InterferenceType(Enum):
    CONSTRUCTIVE = "constructive"  # Amplify information
    DESTRUCTIVE = "destructive"    # Suppress information
    RESONANT = "resonant"          # Match frequency
    DIFFRACTIVE = "diffractive"    # Spread information


class PanelType(Enum):
    LIFE_COUNT = "life_count"
    CATEGORY_COUNT = "category_count"
    PING_STATUS = "ping_status"
    TRANSIT_SCHEDULE = "transit_schedule"
    CALENDAR = "calendar"
    PLANET_INFO = "planet_info"
    NAVIGATION = "navigation"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


@dataclass
class InterferencePattern:
    frequency: float
    amplitude: float
    phase: float
    interference_type: InterferenceType

    def combine(self, other: InterferencePattern) -> InterferencePattern:
        """Combine two interference patterns."""
        # Wave interference: amplitudes add
        new_amplitude = self.amplitude + other.amplitude
        # Phase difference determines constructive/destructive
        phase_diff = abs(self.phase - other.phase)
        if phase_diff < math.pi / 4:
            interference_type = InterferenceType.CONSTRUCTIVE
        elif phase_diff > 3 * math.pi / 4:
            interference_type = InterferenceType.DESTRUCTIVE
        else:
            interference_type = InterferenceType.RESONANT

        return InterferencePattern(
            frequency=(self.frequency + other.frequency) / 2,
            amplitude=new_amplitude,
            phase=(self.phase + other.phase) / 2,
            interference_type=interference_type,
        )


@dataclass
class Panel:
    panel_id: str
    panel_type: PanelType
    title: str
    content: Dict[str, Any]
    interference_pattern: InterferencePattern
    visible: bool = True
    priority: int = 0
    custom_config: Dict[str, Any] = field(default_factory=dict)
    refresh_rate_hz: float = 1.0
    last_updated: float = 0.0

    def should_refresh(self) -> bool:
        return (time.time() - self.last_updated) >= (1.0 / self.refresh_rate_hz)

    def update_content(self, new_content: Dict[str, Any]):
        self.content = new_content
        self.last_updated = time.time()


@dataclass
class UserProfile:
    user_id: str
    name: str
    preferred_panels: List[PanelType]
    interference_sensitivity: float = 1.0
    custom_configs: Dict[str, Any] = field(default_factory=dict)


class InterferenceInterface:
    """Assistive autonomous model using interference patterns for interaction."""

    def __init__(self):
        self.panels: Dict[str, Panel] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.active_interferences: List[InterferencePattern] = []
        self._initialize_default_panels()

    def _initialize_default_panels(self):
        """Create default information panels."""
        defaults = [
            (PanelType.LIFE_COUNT, "Life Count", 1),
            (PanelType.CATEGORY_COUNT, "Category Count", 2),
            (PanelType.PING_STATUS, "Ping Status", 3),
            (PanelType.TRANSIT_SCHEDULE, "Transit Schedule", 4),
            (PanelType.CALENDAR, "Calendar", 5),
            (PanelType.PLANET_INFO, "Planet Info", 6),
            (PanelType.NAVIGATION, "Navigation", 7),
            (PanelType.COMMUNICATION, "Communication", 8),
        ]
        for panel_type, title, priority in defaults:
            self.panels[panel_type.value] = Panel(
                panel_id=panel_type.value,
                panel_type=panel_type,
                title=title,
                content={},
                interference_pattern=InterferencePattern(
                    frequency=1.0,
                    amplitude=1.0,
                    phase=0.0,
                    interference_type=InterferenceType.CONSTRUCTIVE,
                ),
                priority=priority,
            )

    def create_user_profile(
        self,
        user_id: str,
        name: str,
        preferred_panels: Optional[List[PanelType]] = None,
        interference_sensitivity: float = 1.0,
    ) -> UserProfile:
        """Create a customizable user profile."""
        if preferred_panels is None:
            preferred_panels = list(PanelType)

        profile = UserProfile(
            user_id=user_id,
            name=name,
            preferred_panels=preferred_panels,
            interference_sensitivity=interference_sensitivity,
        )
        self.user_profiles[user_id] = profile
        return profile

    def customize_panel(
        self,
        user_id: str,
        panel_type: PanelType,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Customize a panel for a specific user."""
        if user_id not in self.user_profiles:
            return {"error": f"User {user_id} not found"}

        profile = self.user_profiles[user_id]
        panel_id = panel_type.value

        if panel_id not in self.panels:
            return {"error": f"Panel {panel_id} not found"}

        panel = self.panels[panel_id]
        panel.custom_config.update(config)

        # Apply interference based on config
        if "frequency" in config:
            panel.interference_pattern.frequency = config["frequency"]
        if "amplitude" in config:
            panel.interference_pattern.amplitude = config["amplitude"]
        if "phase" in config:
            panel.interference_pattern.phase = config["phase"]
        if "visible" in config:
            panel.visible = config["visible"]
        if "priority" in config:
            panel.priority = config["priority"]
        if "refresh_rate_hz" in config:
            panel.refresh_rate_hz = config["refresh_rate_hz"]

        # Update user profile
        profile.custom_configs[panel_id] = config

        return {
            "status": "customized",
            "user": user_id,
            "panel": panel_id,
            "config": config,
        }

    def apply_interference(
        self,
        panel_id: str,
        interference: InterferencePattern,
    ) -> Dict[str, Any]:
        """Apply interference pattern to a panel."""
        if panel_id not in self.panels:
            return {"error": f"Panel {panel_id} not found"}

        panel = self.panels[panel_id]
        old_pattern = panel.interference_pattern
        new_pattern = old_pattern.combine(interference)
        panel.interference_pattern = new_pattern

        # Determine visibility based on interference
        if new_pattern.interference_type == InterferenceType.DESTRUCTIVE:
            panel.visible = False
        elif new_pattern.interference_type == InterferenceType.CONSTRUCTIVE:
            panel.visible = True

        self.active_interferences.append(interference)

        return {
            "panel": panel_id,
            "old_amplitude": old_pattern.amplitude,
            "new_amplitude": new_pattern.amplitude,
            "interference_type": new_pattern.interference_type.value,
            "visible": panel.visible,
        }

    def get_visible_panels(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all visible panels for a user."""
        if user_id not in self.user_profiles:
            return []

        profile = self.user_profiles[user_id]
        visible = []

        for panel_type in profile.preferred_panels:
            panel_id = panel_type.value
            if panel_id in self.panels:
                panel = self.panels[panel_id]
                if panel.visible:
                    visible.append({
                        "id": panel.panel_id,
                        "type": panel.panel_type.value,
                        "title": panel.title,
                        "content": panel.content,
                        "priority": panel.priority,
                        "interference": {
                            "frequency": panel.interference_pattern.frequency,
                            "amplitude": panel.interference_pattern.amplitude,
                            "type": panel.interference_pattern.interference_type.value,
                        },
                        "config": panel.custom_config,
                    })

        return sorted(visible, key=lambda p: p["priority"])

    def update_panel_data(self, panel_type: PanelType, data: Dict[str, Any]):
        """Update panel content data."""
        panel_id = panel_type.value
        if panel_id in self.panels:
            self.panels[panel_id].update_content(data)

    def get_panel(self, panel_type: PanelType) -> Optional[Panel]:
        """Get a specific panel."""
        return self.panels.get(panel_type.value)

    def create_custom_panel(
        self,
        panel_id: str,
        title: str,
        content: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Panel:
        """Create a custom panel."""
        panel = Panel(
            panel_id=panel_id,
            panel_type=PanelType.CUSTOM,
            title=title,
            content=content,
            interference_pattern=InterferencePattern(
                frequency=config.get("frequency", 1.0),
                amplitude=config.get("amplitude", 1.0),
                phase=config.get("phase", 0.0),
                interference_type=InterferenceType.CONSTRUCTIVE,
            ),
            priority=config.get("priority", 99),
            custom_config=config,
        )
        self.panels[panel_id] = panel
        return panel

    def get_system_state(self) -> Dict[str, Any]:
        """Get full interface system state."""
        return {
            "total_panels": len(self.panels),
            "visible_panels": sum(1 for p in self.panels.values() if p.visible),
            "user_profiles": len(self.user_profiles),
            "active_interferences": len(self.active_interferences),
            "panel_types": [p.panel_type.value for p in self.panels.values()],
        }


    def sync_with_transit(self, transit_system) -> Dict[str, Any]:
        """Sync interface panels with transit system data."""
        # Update life count panel
        life_count = transit_system.get_life_count()
        self.update_panel_data(PanelType.LIFE_COUNT, {
            "life_count": life_count,
            "total_habitable": sum(1 for v in life_count.values() if v > 0),
            "timestamp": time.time(),
        })

        # Update category count panel
        category_count = transit_system.get_category_count()
        self.update_panel_data(PanelType.CATEGORY_COUNT, {
            "categories": category_count,
            "total": sum(category_count.values()),
            "timestamp": time.time(),
        })

        # Update ping status panel
        pings = {}
        for planet_name in list(transit_system.planets.keys())[:10]:
            pings[planet_name] = transit_system.ping(planet_name)
        self.update_panel_data(PanelType.PING_STATUS, {
            "pings": pings,
            "average_ms": sum(pings.values()) / len(pings) if pings else 0,
            "timestamp": time.time(),
        })

        # Update transit schedule panel
        schedules = []
        for s in transit_system.schedules[-5:]:
            schedules.append({
                "origin": s.origin,
                "destination": s.destination,
                "passengers": s.passengers,
                "status": s.status.value,
                "ping_ms": s.ping_ms,
            })
        self.update_panel_data(PanelType.TRANSIT_SCHEDULE, {
            "schedules": schedules,
            "active_count": len(schedules),
            "timestamp": time.time(),
        })

        # Update calendar panel
        events = transit_system.get_calendar()[-5:]
        self.update_panel_data(PanelType.CALENDAR, {
            "events": events,
            "upcoming": len(events),
            "timestamp": time.time(),
        })

        # Update planet info panel
        planets = transit_system.get_habitable_planets()[:5]
        self.update_panel_data(PanelType.PLANET_INFO, {
            "planets": [
                {
                    "name": p.name,
                    "life": p.life_status.value,
                    "gravity": f"{p.gravity_g:.2f}g",
                    "atmosphere": p.atmosphere,
                    "year": p.year,
                    "category": p.category,
                }
                for p in planets
            ],
            "timestamp": time.time(),
        })

        return {
            "status": "synced",
            "panels_updated": 6,
            "timestamp": time.time(),
        }


# Global instance
interference_interface = InterferenceInterface()
