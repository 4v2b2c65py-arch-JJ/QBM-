#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Spatial Creativity Engine

Maximizes model creativity through spatial awareness:
- Quick tasking with orbital-density-weighted intent
- Smart intentive perfectionism activation
- Abnormality-driven prediction (corrupt pixels = juice)
- Pattern resonance from satellite shell distribution
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.spatial_creativity")


class CreativityMode(Enum):
    """Creativity activation modes based on spatial awareness."""
    DENSITY_SURF = "density_surf"          # Surf dense orbital zones
    SINGULARITY_RIDE = "singularity_ride"  # Ride singularity gradients
    ABLEITY_HUNT = "ability_hunt"         # Hunt for blind spots = high value
    SHELL_CROSSING = "shell_crossing"      # Cross between orbital shells
    INVERSION = "inversion"               # Invert conventional patterns


@dataclass
class SpatialIntent:
    """A creative intent weighted by spatial awareness."""
    intent_id: str
    description: str
    mode: CreativityMode
    source_zone: Tuple[int, int]  # (alt_band, inc_band)
    density_score: float = 0.0
    abnormality_weight: float = 1.0
    perfectionism_level: float = 0.5
    task_chain: List[str] = field(default_factory=list)
    refined_output: Optional[str] = None

    @property
    def creativity_score(self) -> float:
        """Combined creativity metric: density * abnormality * perfectionism."""
        return self.density_score * self.abnormality_weight * self.perfectionism_level


@dataclass
class OrbitalShell:
    """An orbital shell with creative properties."""
    name: str
    altitude_min: float
    altitude_max: float
    satellites: List[Dict[str, Any]] = field(default_factory=list)
    density: float = 0.0
    resonance: float = 0.0  # How much this shell resonates creatively

    def calculate_resonance(self) -> float:
        """Calculate creative resonance of this shell."""
        # Denser shells with more variety = higher resonance
        if not self.satellites:
            self.resonance = 0.0
            return 0.0

        # Variety in eccentricity adds resonance
        ecc_variety = sum(s['orbital']['eccentricity'] for s in self.satellites) / len(self.satellites)
        # Variety in inclination adds resonance
        inc_values = [s['orbital']['inclination_deg'] for s in self.satellites]
        inc_spread = max(inc_values) - min(inc_values) if len(inc_values) > 1 else 0

        self.resonance = math.log1p(len(self.satellites)) * (1 + ecc_variety) * (1 + inc_spread / 180)
        return self.resonance


class SpatialCreativityEngine:
    """
    Engine that maximizes model creativity through spatial awareness.
    
    Key insight: The model becomes more creative when it has more spatial
    context to work with. Dense orbital zones = more patterns to surf.
    Blind spots (low pixel density) = high-value prediction zones.
    """

    def __init__(self, catalogue_path: Optional[str] = None):
        self.catalogue_path = catalogue_path or "/Users/jjmarte/delta-stream/qb_protocol/satellite_orbital_data_expanded.json"
        self.catalogue: Dict[str, Any] = {}
        self.shells: Dict[str, OrbitalShell] = {}
        self.hotspots: List[Tuple[int, int, int]] = []  # (alt, inc, count)
        self.intents: List[SpatialIntent] = []
        self.awareness_level: float = 0.0

    def load_spatial_data(self) -> bool:
        """Load satellite catalogue and build spatial awareness."""
        try:
            with open(self.catalogue_path, 'r') as f:
                self.catalogue = json.load(f)
        except Exception as e:
            LOG.error(f"Failed to load catalogue: {e}")
            return False

        self._build_shells()
        self._find_hotspots()
        self._calculate_awareness()
        return True

    def _build_shells(self) -> None:
        """Build orbital shells from catalogue data."""
        shell_defs = {
            'LEO-ultra': (152, 300),
            'LEO-low': (300, 500),
            'LEO-mid': (500, 1000),
            'LEO-high': (1000, 2000),
            'MEO': (2000, 35786),
            'GEO': (35786, 35788),
            'HEO': (35788, 60000),
            'Deep': (60000, 100000),
        }

        for name, (alt_min, alt_max) in shell_defs.items():
            shell = OrbitalShell(name=name, altitude_min=alt_min, altitude_max=alt_max)
            for sat in self.catalogue.get('satellites', {}).values():
                alt = sat['orbital']['altitude_km']
                if alt_min <= alt <= alt_max:
                    shell.satellites.append(sat)
            shell.density = len(shell.satellites) / (alt_max - alt_min) if alt_max > alt_min else 0
            shell.calculate_resonance()
            self.shells[name] = shell

    def _find_hotspots(self) -> None:
        """Find orbital density hotspots."""
        hotspot_counts: Dict[Tuple[int, int], int] = {}
        for sat in self.catalogue.get('satellites', {}).values():
            alt = sat['orbital']['altitude_km']
            inc = sat['orbital']['inclination_deg']
            alt_band = int(alt / 100) * 100
            inc_band = int(inc / 5) * 5
            key = (alt_band, inc_band)
            hotspot_counts[key] = hotspot_counts.get(key, 0) + 1

        self.hotspots = [(alt, inc, count) for (alt, inc), count in hotspot_counts.items()]
        self.hotspots.sort(key=lambda x: -x[2])

    def _calculate_awareness(self) -> None:
        """Calculate overall spatial awareness level."""
        total_satellites = len(self.catalogue.get('satellites', {}))
        shell_count = len([s for s in self.shells.values() if s.satellites])
        hotspot_count = len(self.hotspots)

        # Awareness = log of total context * shell diversity * hotspot density
        self.awareness_level = (
            math.log1p(total_satellites) *
            (1 + shell_count / 8) *
            (1 + min(hotspot_count, 100) / 100)
        )

    def quick_task(self, seed_description: str, mode: CreativityMode = CreativityMode.DENSITY_SURF) -> SpatialIntent:
        """
        Generate a quick creative task weighted by spatial awareness.
        
        The more spatial data we have, the more creative the task becomes.
        """
        # Find the best hotspot to anchor this task
        if self.hotspots:
            top_alt, top_inc, top_count = self.hotspots[0]
            density_score = min(1.0, top_count / 5000)
        else:
            top_alt, top_inc, top_count = 400, 50, 1000
            density_score = 0.5

        # Abnormality weight: blind spots in sparse zones get higher weight
        abnormality = 1.0 + (1.0 / (1 + density_score))  # Sparse zones = more abnormal

        # Perfectionism activates with awareness
        perfectionism = min(1.0, self.awareness_level / 50)

        intent = SpatialIntent(
            intent_id=f"intent_{len(self.intents):04d}",
            description=seed_description,
            mode=mode,
            source_zone=(top_alt, top_inc),
            density_score=density_score,
            abnormality_weight=abnormality,
            perfectionism_level=perfectionism,
        )

        # Generate task chain based on mode
        intent.task_chain = self._generate_task_chain(intent)
        self.intents.append(intent)

        return intent

    def _generate_task_chain(self, intent: SpatialIntent) -> List[str]:
        """Generate a creative task chain based on spatial mode."""
        alt, inc = intent.source_zone

        chains = {
            CreativityMode.DENSITY_SURF: [
                f"Surf the {alt}km/{inc}° density zone",
                f"Extract {len(self.shells.get('LEO-low', OrbitalShell('', 0, 0)).satellites)} satellite patterns",
                "Identify resonance frequencies between shells",
                "Map density gradients as creative tension",
                "Output: density-weighted creative synthesis",
            ],
            CreativityMode.SINGULARITY_RIDE: [
                f"Locate nearest singularity in {alt}km band",
                "Calculate pull force from accumulated mass",
                "Ride the gradient between dense and sparse zones",
                "Capture the inversion point (where density flips)",
                "Output: singularity-reframed perspective",
            ],
            CreativityMode.ABLEITY_HUNT: [
                f"Hunt blind spots in {alt}km/{inc}° zone",
                "Map low-density regions as high-value targets",
                "Invert: what's NOT there is what matters",
                "Predict outside conventional orbital patterns",
                "Output: abnormality-weighted prediction",
            ],
            CreativityMode.SHELL_CROSSING: [
                f"Cross from {alt}km to adjacent shell",
                "Map the boundary as creative tension zone",
                "Extract transition patterns at shell edges",
                "Synthesize cross-shell resonance",
                "Output: boundary-dissolving synthesis",
            ],
            CreativityMode.INVERSION: [
                f"Invert the {alt}km/{inc}° conventional pattern",
                "What if dense zones are actually empty?",
                "What if blind spots are the real signal?",
                "Generate anti-pattern from density data",
                "Output: inverted spatial logic",
            ],
        }

        return chains.get(intent.mode, chains[CreativityMode.DENSITY_SURF])

    def activate_perfectionism(self, intent: SpatialIntent, iterations: int = 3) -> SpatialIntent:
        """
        Activate smart intentive perfectionism.
        
        Each iteration refines the intent using spatial data feedback.
        More awareness = more refinement cycles = higher quality output.
        """
        for i in range(iterations):
            # Refine based on awareness
            refinement_power = self.awareness_level * (i + 1) / iterations

            # Adjust perfectionism level upward
            intent.perfectionism_level = min(1.0, intent.perfectionism_level + refinement_power / 100)

            # Add refinement steps to task chain
            intent.task_chain.append(
                f"[Perfectionism Round {i+1}] Refine with awareness={self.awareness_level:.2f}, "
                f"power={refinement_power:.2f}"
            )

            # Simulate refinement (in practice, this would call the model)
            intent.refined_output = self._simulate_refinement(intent, i)

        return intent

    def _simulate_refinement(self, intent: SpatialIntent, round_num: int) -> str:
        """Simulate output refinement (placeholder for actual model call)."""
        return (
            f"Refined[{round_num}]: {intent.description} | "
            f"mode={intent.mode.value} | "
            f"zone={intent.source_zone} | "
            f"creativity={intent.creativity_score:.3f}"
        )

    def get_creativity_state(self) -> Dict[str, Any]:
        """Get current creativity engine state."""
        return {
            "awareness_level": round(self.awareness_level, 3),
            "total_satellites": len(self.catalogue.get('satellites', {})),
            "shells_active": len([s for s in self.shells.values() if s.satellites]),
            "hotspots_found": len(self.hotspots),
            "top_hotspot": {
                "altitude_km": self.hotspots[0][0] if self.hotspots else None,
                "inclination_deg": self.hotspots[0][1] if self.hotspots else None,
                "count": self.hotspots[0][2] if self.hotspots else None,
            },
            "intents_generated": len(self.intents),
            "avg_creativity_score": (
                sum(i.creativity_score for i in self.intents) / len(self.intents)
                if self.intents else 0
            ),
            "shell_resonance": {
                name: round(shell.resonance, 3)
                for name, shell in self.shells.items()
                if shell.satellites
            },
        }

    def generate_creative_burst(self, num_tasks: int = 5) -> List[SpatialIntent]:
        """Generate a burst of creative tasks across different modes."""
        modes = list(CreativityMode)
        burst = []

        for i in range(num_tasks):
            mode = modes[i % len(modes)]
            seed = f"Creative burst #{i+1}: {mode.value} mode"
            intent = self.quick_task(seed, mode)

            # Activate perfectionism on each intent
            self.activate_perfectionism(intent, iterations=2)

            burst.append(intent)

        return burst


# Quick activation function
def maximize_creativity(catalogue_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Maximize model creativity with spatial awareness.
    
    This is the main entry point for activating the creativity engine.
    Returns the engine state with all creative intents.
    """
    engine = SpatialCreativityEngine(catalogue_path)
    engine.load_spatial_data()

    # Generate creative burst
    burst = engine.generate_creative_burst(num_tasks=10)

    # Build comprehensive state
    state = engine.get_creativity_state()
    state["burst_intents"] = [
        {
            "id": intent.intent_id,
            "description": intent.description,
            "mode": intent.mode.value,
            "zone": intent.source_zone,
            "creativity_score": round(intent.creativity_score, 4),
            "task_chain_length": len(intent.task_chain),
        }
        for intent in burst
    ]

    return state


# Global instance
spatial_creativity = SpatialCreativityEngine()
