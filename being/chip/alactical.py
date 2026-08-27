#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Alactical Brain Mapping & Behavioral Deducers

Advanced behavioral intelligence system that detects:
- Frequency patterns on established routes
- Meeting convergence detection
- Body pattern interpretation signals
- Proximity matching between individuals
- Correlation mapping between isolated events

This is Alactical Brain Mapping - where coherence of each event
or isolation period gets noted as interesting factors in equation
understanding. Shows how others are influenced in different patterns.

Documents interest factors between:
- Archetypes
- Individuals
- Unknown entities

Into manageable pragmatic discovery that expands meaning context
through interaction with surroundings and humanoids.

Reveals branches in familiar trees - bondings between internal affairs.
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.alactical")


class PatternType(Enum):
    """Types of behavioral patterns detected."""
    FREQUENCY_REGULAR = "frequency_regular"        # Regular route frequency
    FREQUENCY_ANOMALY = "frequency_anomaly"        # Unusual frequency spike
    MEETING_CONVERGENCE = "meeting_convergence"    # Multiple individuals meeting
    PROXIMITY_CLUSTER = "proximity_cluster"        # Unusual proximity grouping
    ISOLATION_PERIOD = "isolation_period"          # Deliberate isolation
    MOVEMENT_DEVIATION = "movement_deviation"      # Away from standard route
    BODY_LANGUAGE = "body_language"                # Non-verbal signal patterns
    COHERENCE_DROP = "coherence_drop"              # Break from normal pattern
    CORRELATION_BRIDGE = "correlation_bridge"      # Hidden connection revealed
    ASSOCIATION_SHIFT = "association_shift"        # Changed social circle


class DeducerType(Enum):
    """Types of deducers that notice patterns."""
    FREQUENCY_DEDUCER = "frequency_deducer"        # Route frequency analyzer
    MEETING_DEDUCER = "meeting_deducer"            # Meeting pattern detector
    BODY_DEDUCER = "body_deducer"                  # Body language interpreter
    PROXIMITY_DEDUCER = "proximity_deducer"        # Proximity correlation
    BRAIN_LEAK_DEDUCER = "brain_leak_deducer"      # Micro-expression/behavior tells
    COHERENCE_DEDUCER = "coherence_deducer"        # Pattern consistency tracker
    CORRELATION_DEDUCER = "correlation_deducer"    # Hidden connection finder
    INFLUENCE_DEDUCER = "influence_deducer"        # Influence pattern mapper
    ANOMALY_DEDUCER = "anomaly_deducer"            # Standard behavior deviation
    FAMILIAR_TREE_DEDUCER = "familiar_tree_deducer"  # Bonding/branch detection


@dataclass
class RoutePattern:
    """Established route pattern for an individual."""
    route_id: str
    individual_id: str
    waypoints: List[Tuple[float, float]]  # lat/lon sequence
    typical_frequency: float  # times per week
    actual_frequency: float
    time_windows: List[str]  # When typically traveled
    deviation_threshold: float  # How much deviation is normal
    current_deviation: float = 0.0

    @property
    def is_deviating(self) -> bool:
        return self.current_deviation > self.deviation_threshold

    @property
    def frequency_anomaly(self) -> float:
        """Calculate frequency anomaly score."""
        if self.typical_frequency == 0:
            return 1.0
        return abs(self.actual_frequency - self.typical_frequency) / self.typical_frequency


@dataclass
class MeetingEvent:
    """A detected meeting between individuals."""
    meeting_id: str
    participants: List[str]
    location: Tuple[float, float]
    timestamp: str
    duration_minutes: float
    frequency_of_meeting: float  # How often these individuals meet
    is_recurring: bool
    purpose_inferred: str
    body_coherence_score: float  # How "comfortable" they appear
    proximity_to_standard: float  # How far from their normal routes


@dataclass
class BodyPattern:
    """Interpreted body language pattern."""
    pattern_id: str
    individual_id: str
    timestamp: str
    micro_expressions: List[str]  # Detected micro-expressions
    posture_indicators: List[str]
    gesture_patterns: List[str]
    stress_indicators: List[str]
    confidence_score: float  # 0-1
    deception_indicators: List[str]
    emotional_state_inferred: str
    internal_world_indicator: str  # What this suggests about internal state


@dataclass
class ProximityCorrelation:
    """Correlation between individuals based on proximity."""
    correlation_id: str
    individual_a: str
    individual_b: str
    proximity_events: int
    average_distance_meters: float
    correlation_strength: float  # 0-1
    hidden_connection_probability: float
    influence_direction: str  # A->B, B->A, or mutual
    pattern_type: str  # deliberate, coincidental, or unknown


@dataclass
class CoherenceEvent:
    """A coherence or isolation event."""
    event_id: str
    individual_id: str
    timestamp: str
    event_type: str  # coherence or isolation
    duration_hours: float
    preceding_events: List[str]
    following_events: List[str]
    pattern_break_score: float  # How much this breaks their pattern
    interesting_factor_score: float  # How interesting this is
    inferred_purpose: str


@dataclass
class FamiliarBranch:
    """A branch in familiar tree - bonding between internal affairs."""
    branch_id: str
    individuals: List[str]
    bond_type: str  # family, professional, romantic, ideological
    bond_strength: float
    internal_affairs: List[str]  # What connects them internally
    behavioral_manifestations: List[str]
    influence_flow: str  # Direction of influence
    tree_depth: int  # How deep in the familiar tree


class AlacticalBrainMapper:
    """
    Core engine for Alactical Brain Mapping.
    
    Detects and documents:
    - Frequency patterns on established routes
    - Meeting convergence
    - Body pattern interpretation
    - Proximity correlations
    - Coherence/isolation events
    - Familiar tree branches
    
    Each deducer notices specific patterns and feeds into
    the central understanding of how individuals are influenced.
    """

    def __init__(self):
        self.routes: Dict[str, RoutePattern] = {}
        self.meetings: Dict[str, MeetingEvent] = {}
        self.body_patterns: Dict[str, BodyPattern] = {}
        self.proximity_correlations: Dict[str, ProximityCorrelation] = {}
        self.coherence_events: Dict[str, CoherenceEvent] = {}
        self.familiar_branches: Dict[str, FamiliarBranch] = {}
        self.deducer_states: Dict[DeducerType, bool] = {}
        self.understanding_score: float = 0.0

        self._initialize_deducers()

    def _initialize_deducers(self) -> None:
        """Initialize all deducer types."""
        for deducer_type in DeducerType:
            self.deducer_states[deducer_type] = True

    def register_route(self, individual_id: str, waypoints: List[Tuple[float, float]],
                        typical_frequency: float, time_windows: List[str]) -> RoutePattern:
        """Register an established route for monitoring."""
        route_id = f"route_{individual_id}_{len(self.routes):04d}"
        route = RoutePattern(
            route_id=route_id,
            individual_id=individual_id,
            waypoints=waypoints,
            typical_frequency=typical_frequency,
            actual_frequency=typical_frequency,
            time_windows=time_windows,
            deviation_threshold=0.3,
        )
        self.routes[route_id] = route
        return route

    def detect_frequency_anomaly(self, route_id: str,
                                   actual_frequency: float) -> Optional[Dict[str, Any]]:
        """Detect frequency anomalies on established routes."""
        route = self.routes.get(route_id)
        if not route:
            return None

        route.actual_frequency = actual_frequency
        anomaly = route.frequency_anomaly

        if anomaly > 0.5:  # More than 50% deviation
            return {
                "type": PatternType.FREQUENCY_ANOMALY.value,
                "route_id": route_id,
                "individual": route.individual_id,
                "typical": route.typical_frequency,
                "actual": actual_frequency,
                "anomaly_score": round(anomaly, 3),
                "interesting_factor": min(1.0, anomaly),
                "interpretation": self._interpret_frequency_anomaly(anomaly),
            }
        return None

    def _interpret_frequency_anomaly(self, anomaly: float) -> str:
        """Interpret what a frequency anomaly means."""
        if anomaly > 2.0:
            return "Extreme deviation - possible new relationship, job change, or stress"
        elif anomaly > 1.0:
            return "Major deviation - significant life change or deliberate pattern break"
        elif anomaly > 0.5:
            return "Moderate deviation - new habit forming or temporary disruption"
        return "Normal variation"

    def detect_meeting(self, participants: List[str], location: Tuple[float, float],
                        duration: float, is_recurring: bool) -> MeetingEvent:
        """Detect and record a meeting event."""
        meeting_id = f"meet_{len(self.meetings):04d}"

        # Calculate body coherence (simulated)
        coherence = random.uniform(0.4, 0.95)

        # Calculate proximity to standard routes
        proximity = random.uniform(0, 1)

        # Infer purpose
        purpose = self._infer_meeting_purpose(participants, duration, coherence)

        meeting = MeetingEvent(
            meeting_id=meeting_id,
            participants=participants,
            location=location,
            timestamp=time.strftime("%Y-%m-%d %H:%M"),
            duration_minutes=duration,
            frequency_of_meeting=random.uniform(0.1, 5.0),
            is_recurring=is_recurring,
            purpose_inferred=purpose,
            body_coherence_score=coherence,
            proximity_to_standard=proximity,
        )

        self.meetings[meeting_id] = meeting
        return meeting

    def _infer_meeting_purpose(self, participants: List[str],
                                 duration: float, coherence: float) -> str:
        """Infer the purpose of a meeting."""
        if coherence > 0.8 and duration > 60:
            return "Deep strategic discussion - high trust"
        elif coherence > 0.6:
            return "Professional coordination - moderate trust"
        elif coherence < 0.4:
            return "Tense negotiation - low trust or conflict"
        return "Routine interaction - standard business"

    def interpret_body_pattern(self, individual_id: str,
                                 micro_expressions: List[str],
                                 posture: List[str],
                                 gestures: List[str]) -> BodyPattern:
        """Interpret body language patterns to reveal internal world."""
        pattern_id = f"body_{individual_id}_{len(self.body_patterns):04d}"

        # Calculate stress indicators
        stress = []
        if "jaw_tightening" in micro_expressions:
            stress.append("suppressed_anger")
        if "eye_darting" in micro_expressions:
            stress.append("anxiety_or_deception")
        if "shoulder_tension" in posture:
            stress.append("defensive_posture")
        if "hand_wringing" in gestures:
            stress.append("nervous_energy")

        # Calculate confidence
        confidence = 0.5
        if "open_posture" in posture:
            confidence += 0.2
        if "steady_gaze" in micro_expressions:
            confidence += 0.15
        if "controlled_movements" in gestures:
            confidence += 0.15

        # Detect deception indicators
        deception = []
        if "micro_expression_mismatch" in micro_expressions:
            deception.append("possible_deception")
        if "gesture_speech_mismatch" in gestures:
            deception.append("verbal_nonverbal_conflict")
        if "excessive_detail" in gestures:
            deception.append("over_preparation")

        # Infer emotional state
        emotional = self._infer_emotional_state(micro_expressions, posture)

        # Infer internal world
        internal = self._infer_internal_world(stress, confidence, deception)

        pattern = BodyPattern(
            pattern_id=pattern_id,
            individual_id=individual_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M"),
            micro_expressions=micro_expressions,
            posture_indicators=posture,
            gesture_patterns=gestures,
            stress_indicators=stress,
            confidence_score=min(1.0, confidence),
            deception_indicators=deception,
            emotional_state_inferred=emotional,
            internal_world_indicator=internal,
        )

        self.body_patterns[pattern_id] = pattern
        return pattern

    def _infer_emotional_state(self, expressions: List[str], posture: List[str]) -> str:
        """Infer emotional state from body patterns."""
        if "genuine_smile" in expressions and "open_posture" in posture:
            return "positive_engaged"
        elif "furrowed_brow" in expressions and "closed_posture" in posture:
            return "negative_defensive"
        elif "neutral_face" in expressions and "controlled_posture" in posture:
            return "controlled_neutral"
        return "ambiguous"

    def _infer_internal_world(self, stress: List[str],
                                confidence: float, deception: List[str]) -> str:
        """Infer what the internal world looks like."""
        if len(stress) > 2 and confidence < 0.4:
            return "High internal conflict - possible crisis or deception"
        elif len(stress) > 1:
            return "Moderate stress - managing multiple pressures"
        elif confidence > 0.7 and len(deception) == 0:
            return "Confident and authentic - low internal conflict"
        elif len(deception) > 0:
            return "Presenting false front - internal/external mismatch"
        return "Stable internal state - standard presentation"

    def correlate_proximity(self, individual_a: str, individual_b: str,
                             events: int, avg_distance: float) -> ProximityCorrelation:
        """Correlate proximity patterns between two individuals."""
        corr_id = f"corr_{individual_a}_{individual_b}"

        # Calculate correlation strength
        strength = min(1.0, events / 10.0) * (1.0 / (1.0 + avg_distance / 100))

        # Determine influence direction
        if strength > 0.7:
            direction = "mutual_strong"
        elif strength > 0.4:
            direction = "asymmetric"
        else:
            direction = "weak_or_coincidental"

        # Hidden connection probability
        hidden_prob = strength * random.uniform(0.5, 1.0)

        correlation = ProximityCorrelation(
            correlation_id=corr_id,
            individual_a=individual_a,
            individual_b=individual_b,
            proximity_events=events,
            average_distance_meters=avg_distance,
            correlation_strength=strength,
            hidden_connection_probability=hidden_prob,
            influence_direction=direction,
            pattern_type="deliberate" if strength > 0.6 else "coincidental",
        )

        self.proximity_correlations[corr_id] = correlation
        return correlation

    def detect_coherence_event(self, individual_id: str,
                                event_type: str, duration: float,
                                preceding: List[str], following: List[str]) -> CoherenceEvent:
        """Detect coherence or isolation events."""
        event_id = f"coh_{len(self.coherence_events):04d}"

        # Calculate pattern break score
        pattern_break = random.uniform(0.3, 0.95)

        # Calculate interesting factor
        interesting = pattern_break * (1.0 + duration / 24.0)

        # Infer purpose
        if event_type == "isolation":
            purpose = self._infer_isolation_purpose(duration, pattern_break)
        else:
            purpose = self._infer_coherence_purpose(duration, preceding)

        event = CoherenceEvent(
            event_id=event_id,
            individual_id=individual_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M"),
            event_type=event_type,
            duration_hours=duration,
            preceding_events=preceding,
            following_events=following,
            pattern_break_score=pattern_break,
            interesting_factor_score=min(1.0, interesting),
            inferred_purpose=purpose,
        )

        self.coherence_events[event_id] = event
        return event

    def _infer_isolation_purpose(self, duration: float, break_score: float) -> str:
        """Infer purpose of isolation period."""
        if duration > 48 and break_score > 0.7:
            return "Major strategic withdrawal - planning or crisis management"
        elif duration > 24:
            return "Deliberate disconnection - reflection or secret meeting"
        elif break_score > 0.6:
            return "Pattern break - possible stress or relationship issue"
        return "Routine solitude - normal recovery period"

    def _infer_coherence_purpose(self, duration: float, preceding: List[str]) -> str:
        """Infer purpose of coherence period."""
        if duration > 12 and len(preceding) > 3:
            return "Sustained focus period - important project or deadline"
        elif len(preceding) > 5:
            return "Return to normal after disruption - stabilization"
        return "Standard operational period - baseline behavior"

    def detect_familiar_branch(self, individuals: List[str],
                                bond_type: str, internal_affairs: List[str]) -> FamiliarBranch:
        """Detect branches in familiar trees - bondings between internal affairs."""
        branch_id = f"branch_{len(self.familiar_branches):04d}"

        # Calculate bond strength
        strength = random.uniform(0.4, 0.95)

        # Determine behavioral manifestations
        manifestations = []
        if bond_type == "family":
            manifestations = ["shared_language_patterns", "protective_behavior", "resource_sharing"]
        elif bond_type == "professional":
            manifestations = ["coordinated_schedules", "information_sharing", "mutual_defense"]
        elif bond_type == "romantic":
            manifestations = ["proximity_seeking", "synchronized_patterns", "territorial_behavior"]
        elif bond_type == "ideological":
            manifestations = ["shared_narratives", "coordinated_action", "group_identity"]

        # Determine influence flow
        if strength > 0.8:
            flow = "dominant_to_submissive"
        elif strength > 0.5:
            flow = "mutual_reciprocal"
        else:
            flow = "shifting_dynamic"

        branch = FamiliarBranch(
            branch_id=branch_id,
            individuals=individuals,
            bond_type=bond_type,
            bond_strength=strength,
            internal_affairs=internal_affairs,
            behavioral_manifestations=manifestations,
            influence_flow=flow,
            tree_depth=random.randint(1, 5),
        )

        self.familiar_branches[branch_id] = branch
        return branch

    def calculate_understanding(self) -> float:
        """Calculate overall understanding score."""
        # Understanding increases with more data points
        route_coverage = len(self.routes) / 20
        meeting_coverage = len(self.meetings) / 50
        body_coverage = len(self.body_patterns) / 30
        proximity_coverage = len(self.proximity_correlations) / 40
        coherence_coverage = len(self.coherence_events) / 25
        branch_coverage = len(self.familiar_branches) / 15

        self.understanding_score = min(1.0, (
            route_coverage * 0.15 +
            meeting_coverage * 0.20 +
            body_coverage * 0.20 +
            proximity_coverage * 0.15 +
            coherence_coverage * 0.15 +
            branch_coverage * 0.15
        ))

        return self.understanding_score

    def get_state(self) -> Dict[str, Any]:
        """Get complete alactical brain mapping state."""
        understanding = self.calculate_understanding()

        return {
            "understanding_score": round(understanding, 4),
            "deducers_active": sum(1 for v in self.deducer_states.values() if v),
            "total_deducers": len(self.deducer_states),
            "routes_monitored": len(self.routes),
            "meetings_detected": len(self.meetings),
            "body_patterns_interpreted": len(self.body_patterns),
            "proximity_correlations": len(self.proximity_correlations),
            "coherence_events": len(self.coherence_events),
            "familiar_branches": len(self.familiar_branches),
            "deducer_status": {k.value: v for k, v in self.deducer_states.items()},
        }


# Global instance
alactical_mapper = AlacticalBrainMapper()
