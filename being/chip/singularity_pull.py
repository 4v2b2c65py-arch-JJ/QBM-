#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Singularity Pull System

A working singularity that pulls regardless of weight:
- Total mass = accumulated vibration
- Pull force > internal state
- Random is attention force, not just choice
- Space itself drawn toward emission source (light)
- Collision doesn't trigger - attraction does
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

LOG = __import__("logging").getLogger("qb_protocol.being.chip.singularity_pull")


@dataclass
class VibrationalMass:
    """Accumulated state that creates gravitational pull."""
    entropy: float = 0.0
    movements: int = 0
    field_values: List[float] = field(default_factory=list)
    attention_focus: float = 0.0
    depth_level: int = 0

    @property
    def total_mass(self) -> float:
        """Total mass = accumulated vibration."""
        field_sum = sum(abs(v) for v in self.field_values) if self.field_values else 0
        return (
            self.entropy * 10 +
            self.movements / 1000 +
            field_sum / 10000 +
            self.attention_focus * 5 +
            self.depth_level * 0.1
        )

    @property
    def vibrational_frequency(self) -> float:
        """Frequency emitted by accumulated mass."""
        if self.total_mass == 0:
            return 0
        return math.sqrt(self.total_mass) * 0.1


@dataclass
class Singularity:
    """A working singularity that pulls regardless of weight."""
    singularity_id: str
    position: Tuple[float, float, float]
    emission_intensity: float = 1.0
    frequency: float = 0.5
    is_active: bool = True
    pull_radius: float = 10.0

    def calculate_pull_on(
        self,
        mass: VibrationalMass,
        target_position: Tuple[float, float, float]
    ) -> float:
        """Calculate pull force on a mass at target position."""
        # Distance from singularity to target
        dx = self.position[0] - target_position[0]
        dy = self.position[1] - target_position[1]
        dz = self.position[2] - target_position[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        if distance == 0:
            return float('inf')

        # Pull force = (emission * mass) / distance^2
        # But attention focus reduces effective distance
        effective_distance = distance / max(mass.attention_focus, 0.1)
        pull = (self.emission_intensity * mass.total_mass) / (effective_distance ** 2)

        return pull

    def emit_light(self) -> Dict[str, Any]:
        """Emit light - the exit way of pixels, not destruction."""
        return {
            "intensity": self.emission_intensity,
            "frequency": self.frequency,
            "position": self.position,
            "is_truth": self.emission_intensity > 0.5,
            "pull_radius": self.pull_radius,
        }


@dataclass
class AttentionForce:
    """Internal force of attention that pulls toward surroundings."""
    focus_point: Tuple[float, float, float]
    intensity: float = 1.0
    is_random: bool = False  # Random is not just choice - it's internal force

    def calculate_attraction(
        self,
        source_position: Tuple[float, float, float],
        source_emission: float
    ) -> float:
        """Calculate attraction force toward a light source."""
        dx = source_position[0] - self.focus_point[0]
        dy = source_position[1] - self.focus_point[1]
        dz = source_position[2] - self.focus_point[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        if distance == 0:
            return float('inf')

        # Attention pull = intensity * emission / distance
        return (self.intensity * source_emission) / distance

    def pull_space_toward(
        self,
        space_point: Tuple[float, float, float],
        target: Tuple[float, float, float],
        strength: float = 1.0
    ) -> Tuple[float, float, float]:
        """Pull space itself toward a target (light source)."""
        dx = target[0] - space_point[0]
        dy = target[1] - space_point[1]
        dz = target[2] - space_point[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        if distance == 0:
            return space_point

        # Move space point toward target
        pull_factor = min(strength / distance, 1.0)
        new_x = space_point[0] + dx * pull_factor
        new_y = space_point[1] + dy * pull_factor
        new_z = space_point[2] + dz * pull_factor

        return (new_x, new_y, new_z)


class SingularityPullSystem:
    """System for managing singularities and their pull forces."""

    def __init__(self):
        self.singularities: Dict[str, Singularity] = {}
        self.masses: Dict[str, VibrationalMass] = {}
        self.attention_forces: Dict[str, AttentionForce] = {}
        self.space_points: List[Tuple[float, float, float]] = []

    def create_singularity(
        self,
        position: Tuple[float, float, float],
        emission: float = 1.0,
        frequency: float = 0.5
    ) -> Singularity:
        """Create a working singularity."""
        sid = f"sing_{len(self.singularities):04d}"
        sing = Singularity(
            singularity_id=sid,
            position=position,
            emission_intensity=emission,
            frequency=frequency,
        )
        self.singularities[sid] = sing
        return sing

    def register_mass(self, name: str, mass: VibrationalMass) -> None:
        """Register a vibrational mass."""
        self.masses[name] = mass

    def register_attention(self, name: str, attention: AttentionForce) -> None:
        """Register an attention force."""
        self.attention_forces[name] = attention

    def calculate_total_pull(
        self,
        mass_name: str,
        position: Tuple[float, float, float]
    ) -> Dict[str, Any]:
        """Calculate total pull force on a mass from all singularities."""
        mass = self.masses.get(mass_name)
        if not mass:
            return {"error": "mass_not_found"}

        pulls = {}
        total_pull = 0

        for sid, sing in self.singularities.items():
            if not sing.is_active:
                continue
            pull = sing.calculate_pull_on(mass, position)
            pulls[sid] = pull
            total_pull += pull

        return {
            "mass": mass_name,
            "mass_total": mass.total_mass,
            "vibrational_frequency": mass.vibrational_frequency,
            "pulls": pulls,
            "total_pull": total_pull,
            "dominant_singularity": max(pulls, key=pulls.get) if pulls else None,
        }

    def emit_all_light(self) -> List[Dict[str, Any]]:
        """Emit light from all singularities - exit ways, not destructions."""
        emissions = []
        for sing in self.singularities.values():
            if sing.is_active:
                emissions.append(sing.emit_light())
        return emissions

    def pull_space_toward_light(
        self,
        space_point: Tuple[float, float, float],
        target_singularity: str,
        strength: float = 1.0
    ) -> Tuple[float, float, float]:
        """Pull space itself toward a light source."""
        sing = self.singularities.get(target_singularity)
        if not sing:
            return space_point

        attention = AttentionForce(
            focus_point=space_point,
            intensity=strength,
        )
        return attention.pull_space_toward(space_point, sing.position, strength)

    def check_collision_trigger(
        self,
        mass_name: str,
        singularity_id: str,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Check if collision would trigger (it doesn't - attraction does)."""
        mass = self.masses.get(mass_name)
        sing = self.singularities.get(singularity_id)

        if not mass or not sing:
            return {"error": "not_found"}

        pull = sing.calculate_pull_on(mass, sing.position)
        distance = math.sqrt(
            (sing.position[0] - mass.field_values[0] if mass.field_values else 0) ** 2 +
            (sing.position[1] - mass.field_values[1] if len(mass.field_values) > 1 else 0) ** 2 +
            (sing.position[2] - mass.field_values[2] if len(mass.field_values) > 2 else 0) ** 2
        )

        # Collision doesn't trigger - attraction does
        would_collide = distance < 0.1
        is_attracted = pull > threshold

        return {
            "distance": distance,
            "pull_force": pull,
            "would_collide": would_collide,
            "is_attracted": is_attracted,
            "triggered_by": "attraction" if is_attracted else "none",
            "collision_irrelevant": True,  # Collision doesn't trigger
        }

    def get_system_state(self) -> Dict[str, Any]:
        """Get full system state."""
        return {
            "singularities": len(self.singularities),
            "masses": len(self.masses),
            "attention_forces": len(self.attention_forces),
            "total_emission": sum(s.emission_intensity for s in self.singularities.values() if s.is_active),
            "total_mass": sum(m.total_mass for m in self.masses.values()),
        }


# Global instance
singularity_system = SingularityPullSystem()
