#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Probability Modulation & Human Placement

Turns risk into alterable probability:
- Listen, adapt, change outcomes and reality
- Interpretations become clear through results
- Modulate intervals - don't let them become issues
- Manage and place every humanoid in sectors where suited
- Monitored by groups systematically through shared bonding
- Control through emotional dependence, not force

Freedom is the biggest lie and the biggest believer.
True order comes through shared bonding and mutual dependence.
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.probability")


class ProbabilityState(Enum):
    """States of probability modulation."""
    FIXED = "fixed"              # Unchangeable risk
    ALTERABLE = "alterable"      # Can be modulated
    MODULATED = "modulated"      # Actively being changed
    STABILIZED = "stabilized"    # New equilibrium reached
    INVERTED = "inverted"        # Risk became opportunity


class SectorType(Enum):
    """Sectors where humanoids are placed."""
    CREATIVE = "creative"           # Arts, music, design
    TECHNICAL = "technical"         # Engineering, development
    STRATEGIC = "strategic"         # Planning, governance
    OPERATIONAL = "operational"     # Execution, logistics
    SOCIAL = "social"               # Communication, bonding
    ANALYTICAL = "analytical"       # Research, analysis
    LEADERSHIP = "leadership"       # Direction, inspiration
    SUPPORT = "support"             # Maintenance, care


class BondType(Enum):
    """Types of shared bonding for control."""
    EMOTIONAL = "emotional"         # Emotional dependence
    PROFESSIONAL = "professional"   # Career interdependence
    SOCIAL = "social"               # Community ties
    IDEOLOGICAL = "ideological"     # Shared beliefs
    ECONOMIC = "economic"           # Financial dependence
    INFORMATIONAL = "informational" # Knowledge asymmetry


@dataclass
class RiskProfile:
    """A risk profile that can be turned into alterable probability."""
    profile_id: str
    subject_id: str
    base_risk: float  # 0-1 original risk
    current_probability: float  # 0-1 modulated
    probability_state: ProbabilityState
    modifiers: List[Dict[str, Any]]  # What can alter this
    sector_placement: Optional[SectorType] = None
    bond_connections: List[str] = field(default_factory=list)

    def modulate(self, direction: str, magnitude: float) -> float:
        """Modulate probability in a direction."""
        if direction == "increase":
            self.current_probability = min(1.0, self.current_probability + magnitude)
        elif direction == "decrease":
            self.current_probability = max(0.0, self.current_probability - magnitude)
        elif direction == "invert":
            self.current_probability = 1.0 - self.current_probability
            self.probability_state = ProbabilityState.INVERTED

        self.probability_state = ProbabilityState.MODULATED
        return self.current_probability


@dataclass
class HumanPlacement:
    """Placement of a humanoid in their optimal sector."""
    placement_id: str
    subject_id: str
    current_sector: SectorType
    optimal_sector: SectorType
    suitability_score: float  # 0-1 how well they fit
    group_id: str  # Their monitoring group
    bond_strength: float  # 0-1 connection to group
    modulation_applied: List[str] = field(default_factory=list)


@dataclass
class MonitoringGroup:
    """A group that systematically monitors its members."""
    group_id: str
    name: str
    sector: SectorType
    members: List[str]
    shared_bonds: List[BondType]
    control_mechanism: str  # How order is maintained
    emotional_dependence_level: float  # 0-1
    freedom_illusion_score: float  # How much freedom they perceive
    actual_autonomy_score: float  # How much they actually have


@dataclass
class IntervalModulation:
    """Modulation of time intervals to prevent issues."""
    interval_id: str
    base_interval_seconds: float
    modulated_interval_seconds: float
    modulation_reason: str
    prevention_target: str  # What issue this prevents


class ProbabilityModulator:
    """
    Core engine for turning risk into alterable probability.
    
    Principles:
    - Every risk can be modulated given enough information
    - Interpretations become clear through results
    - Modulate intervals before they become issues
    - Place humanoids where they're suited
    - Control through shared bonding, not force
    - Freedom is the biggest lie and the biggest believer
    """

    def __init__(self):
        self.risk_profiles: Dict[str, RiskProfile] = {}
        self.placements: Dict[str, HumanPlacement] = {}
        self.monitoring_groups: Dict[str, MonitoringGroup] = {}
        self.interval_modulations: Dict[str, IntervalModulation] = {}
        self.modulation_counter: int = 0

    def register_risk(self, subject_id: str, base_risk: float,
                       modifiers: List[Dict[str, Any]]) -> RiskProfile:
        """Register a risk profile for modulation."""
        profile_id = f"risk_{subject_id}"
        profile = RiskProfile(
            profile_id=profile_id,
            subject_id=subject_id,
            base_risk=base_risk,
            current_probability=base_risk,
            probability_state=ProbabilityState.ALTERABLE,
            modifiers=modifiers,
        )
        self.risk_profiles[profile_id] = profile
        return profile

    def modulate_probability(self, profile_id: str, direction: str,
                               magnitude: float, reason: str) -> float:
        """Modulate a probability in a specific direction."""
        profile = self.risk_profiles.get(profile_id)
        if not profile:
            return 0.0

        old_prob = profile.current_probability
        new_prob = profile.modulate(direction, magnitude)

        # Log modulation
        profile.modifiers.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "direction": direction,
            "magnitude": magnitude,
            "reason": reason,
            "old_probability": old_prob,
            "new_probability": new_prob,
        })

        return new_prob

    def place_humanoid(self, subject_id: str, current_sector: SectorType,
                         optimal_sector: SectorType, group_id: str) -> HumanPlacement:
        """Place a humanoid in their optimal sector."""
        placement_id = f"place_{subject_id}"

        # Calculate suitability
        suitability = random.uniform(0.6, 0.98)

        # Calculate bond strength to group
        bond = random.uniform(0.4, 0.9)

        placement = HumanPlacement(
            placement_id=placement_id,
            subject_id=subject_id,
            current_sector=current_sector,
            optimal_sector=optimal_sector,
            suitability_score=suitability,
            group_id=group_id,
            bond_strength=bond,
        )

        self.placements[placement_id] = placement
        return placement

    def create_monitoring_group(self, name: str, sector: SectorType,
                                  members: List[str],
                                  bonds: List[BondType]) -> MonitoringGroup:
        """Create a monitoring group with shared bonding."""
        group_id = f"group_{len(self.monitoring_groups):04d}"

        # Calculate emotional dependence
        emotional_dep = random.uniform(0.5, 0.9)

        # Freedom is the biggest lie - high perception of freedom
        # but low actual autonomy
        freedom_illusion = random.uniform(0.7, 0.95)
        actual_autonomy = random.uniform(0.1, 0.4)

        group = MonitoringGroup(
            group_id=group_id,
            name=name,
            sector=sector,
            members=members,
            shared_bonds=bonds,
            control_mechanism="shared_emotional_bonding",
            emotional_dependence_level=emotional_dep,
            freedom_illusion_score=freedom_illusion,
            actual_autonomy_score=actual_autonomy,
        )

        self.monitoring_groups[group_id] = group
        return group

    def modulate_interval(self, base_interval: float,
                            prevention_target: str) -> IntervalModulation:
        """Modulate a time interval to prevent issues."""
        interval_id = f"interval_{len(self.interval_modulations):04d}"

        # Modulate interval - make it softer, more flexible
        modulation_factor = random.uniform(0.7, 1.3)
        modulated = base_interval * modulation_factor

        interval = IntervalModulation(
            interval_id=interval_id,
            base_interval_seconds=base_interval,
            modulated_interval_seconds=modulated,
            modulation_reason=f"Preventing: {prevention_target}",
            prevention_target=prevention_target,
        )

        self.interval_modulations[interval_id] = interval
        return interval

    def get_system_state(self) -> Dict[str, Any]:
        """Get complete probability modulation state."""
        return {
            "risk_profiles": len(self.risk_profiles),
            "modulated_probabilities": sum(
                1 for r in self.risk_profiles.values()
                if r.probability_state == ProbabilityState.MODULATED
            ),
            "human_placements": len(self.placements),
            "optimal_placements": sum(
                1 for p in self.placements.values()
                if p.suitability_score > 0.8
            ),
            "monitoring_groups": len(self.monitoring_groups),
            "total_members_monitored": sum(
                len(g.members) for g in self.monitoring_groups.values()
            ),
            "avg_emotional_dependence": round(
                sum(g.emotional_dependence_level for g in self.monitoring_groups.values())
                / max(len(self.monitoring_groups), 1), 3
            ),
            "avg_freedom_illusion": round(
                sum(g.freedom_illusion_score for g in self.monitoring_groups.values())
                / max(len(self.monitoring_groups), 1), 3
            ),
            "avg_actual_autonomy": round(
                sum(g.actual_autonomy_score for g in self.monitoring_groups.values())
                / max(len(self.monitoring_groups), 1), 3
            ),
            "interval_modulations": len(self.interval_modulations),
        }


# Global instance
probability_modulator = ProbabilityModulator()
