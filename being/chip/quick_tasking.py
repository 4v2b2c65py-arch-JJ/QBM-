#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Quick Tasking & Smart Intentive Perfectionism

Tools for rapid task generation that maximize creativity through spatial awareness:
- Quick Task Generator: Creates tasks weighted by orbital density patterns
- Intentive Perfectionism Activator: Refines outputs through spatial feedback loops
- Spatial Awareness Amplifier: Uses satellite data to boost model creativity
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.quick_tasking")


class TaskPriority(Enum):
    """Task priority based on spatial density."""
    CRITICAL = "critical"    # Densest zones - maximum creative potential
    HIGH = "high"           # High-density zones
    MEDIUM = "medium"       # Moderate density
    LOW = "low"             # Sparse zones (blind spots = high value)
    SINGULARITY = "singularity"  # Anomaly zones


@dataclass
class QuickTask:
    """A task generated with spatial awareness weighting."""
    task_id: str
    description: str
    priority: TaskPriority
    source_zone: Tuple[int, int]  # (altitude_km, inclination_deg)
    spatial_density: float = 0.0
    abnormality_factor: float = 1.0
    creativity_weight: float = 0.5
    refinement_cycles: int = 0
    subtasks: List[str] = field(default_factory=list)
    output: Optional[str] = None

    @property
    def task_score(self) -> float:
        """Combined task value score."""
        priority_multiplier = {
            TaskPriority.CRITICAL: 2.0,
            TaskPriority.HIGH: 1.5,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.LOW: 1.3,  # Blind spots get bonus
            TaskPriority.SINGULARITY: 2.5,
        }
        return (
            self.spatial_density *
            self.abnormality_factor *
            self.creativity_weight *
            priority_multiplier[self.priority]
        )


@dataclass
class RefinementRound:
    """A single refinement round in the perfectionism process."""
    round_number: int
    input_text: str
    output_text: str
    spatial_feedback: str
    improvement_score: float
    awareness_delta: float


class SmartIntentivePerfectionism:
    """
    Activates perfectionism through spatial awareness feedback.
    
    The more spatial data the model processes, the more refined its outputs become.
    Each refinement round uses orbital density patterns as a quality signal.
    """

    def __init__(self, awareness_level: float = 10.0):
        self.awareness_level = awareness_level
        self.refinement_history: List[RefinementRound] = []
        self.perfectionism_coefficient: float = 0.5

    def refine(self, text: str, spatial_context: Dict[str, Any], rounds: int = 3) -> str:
        """
        Refine text through multiple perfectionism rounds.
        
        Each round applies spatial awareness to improve the output.
        More awareness = more refinement = higher quality.
        """
        current = text

        for i in range(rounds):
            # Calculate refinement power based on awareness
            power = self.awareness_level * (i + 1) / rounds / 100

            # Generate spatial feedback
            feedback = self._generate_spatial_feedback(spatial_context, i)

            # Apply refinement
            refined = self._apply_refinement(current, feedback, power)

            # Calculate improvement
            improvement = self._calculate_improvement(current, refined)

            # Record round
            round_record = RefinementRound(
                round_number=i + 1,
                input_text=current,
                output_text=refined,
                spatial_feedback=feedback,
                improvement_score=improvement,
                awareness_delta=power,
            )
            self.refinement_history.append(round_record)

            current = refined
            self.perfectionism_coefficient += improvement / 10

        return current

    def _generate_spatial_feedback(self, context: Dict[str, Any], round_num: int) -> str:
        """Generate feedback based on spatial data context."""
        density = context.get('density', 0.5)
        altitude = context.get('altitude_km', 400)
        inclination = context.get('inclination_deg', 50)

        feedbacks = [
            f"Density signal at {altitude}km/{inclination}°: {density:.3f}",
            f"Orbital resonance feedback (round {round_num + 1})",
            f"Spatial awareness level: {self.awareness_level:.2f}",
        ]

        if density > 0.8:
            feedbacks.append("HIGH DENSITY ZONE - maximum pattern extraction")
        elif density < 0.2:
            feedbacks.append("BLIND SPOT DETECTED - high-value prediction zone")

        return " | ".join(feedbacks)

    def _apply_refinement(self, text: str, feedback: str, power: float) -> str:
        """Apply refinement to text using spatial feedback."""
        # In a real implementation, this would call the model
        # For now, we simulate the refinement
        return f"{text}\n[Refined | power={power:.4f} | feedback={feedback[:50]}...]"

    def _calculate_improvement(self, before: str, after: str) -> float:
        """Calculate improvement score between refinement rounds."""
        # Simple heuristic: longer = more detailed = better
        return min(1.0, (len(after) - len(before)) / max(len(before), 1))


class QuickTaskGenerator:
    """
    Generates tasks quickly using spatial data for creative weighting.
    
    The generator uses orbital density patterns to determine:
    - Task priority (denser zones = higher priority)
    - Creative weight (abnormal zones = more creative)
    - Refinement depth (awareness level determines cycles)
    """

    def __init__(self, catalogue_path: Optional[str] = None):
        self.catalogue_path = catalogue_path or "/Users/jjmarte/delta-stream/qb_protocol/satellite_orbital_data_expanded.json"
        self.catalogue: Dict[str, Any] = {}
        self.hotspots: List[Tuple[int, int, int]] = []
        self.shell_densities: Dict[str, float] = {}
        self.awareness_level: float = 0.0
        self.perfectionism = SmartIntentivePerfectionism()
        self.task_counter: int = 0

    def load(self) -> bool:
        """Load spatial data and calculate awareness."""
        try:
            with open(self.catalogue_path, 'r') as f:
                self.catalogue = json.load(f)
        except Exception as e:
            LOG.error(f"Failed to load catalogue: {e}")
            return False

        self._analyze_hotspots()
        self._calculate_shell_densities()
        self._update_awareness()
        self.perfectionism.awareness_level = self.awareness_level
        return True

    def _analyze_hotspots(self) -> None:
        """Analyze orbital density hotspots."""
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

    def _calculate_shell_densities(self) -> None:
        """Calculate density for each orbital shell."""
        shell_defs = {
            'LEO-low': (300, 500),
            'LEO-mid': (500, 1000),
            'LEO-high': (1000, 2000),
            'MEO': (2000, 35786),
            'GEO': (35786, 35788),
            'HEO': (35788, 60000),
        }

        for name, (alt_min, alt_max) in shell_defs.items():
            count = sum(
                1 for s in self.catalogue.get('satellites', {}).values()
                if alt_min <= s['orbital']['altitude_km'] <= alt_max
            )
            self.shell_densities[name] = count / (alt_max - alt_min) if alt_max > alt_min else 0

    def _update_awareness(self) -> None:
        """Update spatial awareness level."""
        total = len(self.catalogue.get('satellites', {}))
        shell_count = len([d for d in self.shell_densities.values() if d > 0])
        hotspot_count = len(self.hotspots)

        self.awareness_level = (
            math.log1p(total) *
            (1 + shell_count / 6) *
            (1 + min(hotspot_count, 100) / 100)
        )

    def quick_task(self, description: str, mode: str = "density_surf") -> QuickTask:
        """Generate a quick task with spatial awareness weighting."""
        self.task_counter += 1

        # Find best hotspot for this task
        if self.hotspots:
            alt, inc, count = random.choice(self.hotspots[:10])
            density = min(1.0, count / 5000)
        else:
            alt, inc, count = 400, 50, 1000
            density = 0.5

        # Determine priority based on density
        if density > 0.8:
            priority = TaskPriority.CRITICAL
        elif density > 0.5:
            priority = TaskPriority.HIGH
        elif density > 0.2:
            priority = TaskPriority.MEDIUM
        elif density < 0.05:
            priority = TaskPriority.SINGULARITY
        else:
            priority = TaskPriority.LOW

        # Abnormality factor: sparse zones get higher weight
        abnormality = 1.0 + (1.0 / (1 + density))

        # Creativity weight scales with awareness
        creativity = min(1.0, self.awareness_level / 50)

        task = QuickTask(
            task_id=f"task_{self.task_counter:04d}",
            description=description,
            priority=priority,
            source_zone=(alt, inc),
            spatial_density=density,
            abnormality_factor=abnormality,
            creativity_weight=creativity,
        )

        # Generate subtasks
        task.subtasks = self._generate_subtasks(task, mode)

        return task

    def _generate_subtasks(self, task: QuickTask, mode: str) -> List[str]:
        """Generate subtasks based on mode and spatial context."""
        alt, inc = task.source_zone

        subtask_templates = {
            "density_surf": [
                f"Map density patterns at {alt}km/{inc}°",
                "Identify resonance frequencies",
                "Extract creative tension from gradients",
                "Synthesize cross-zone patterns",
            ],
            "singularity_ride": [
                f"Locate singularity at {alt}km",
                "Calculate pull forces",
                "Ride density gradients",
                "Capture inversion points",
            ],
            "ability_hunt": [
                f"Hunt blind spots at {alt}km/{inc}°",
                "Map low-density high-value zones",
                "Predict outside conventional patterns",
                "Generate abnormality-weighted output",
            ],
            "shell_crossing": [
                f"Cross from {alt}km to adjacent shell",
                "Map boundary tension zones",
                "Extract transition patterns",
                "Synthesize cross-shell resonance",
            ],
            "inversion": [
                f"Invert conventional {alt}km patterns",
                "Generate anti-patterns from density data",
                "What if dense zones are empty?",
                "Output inverted spatial logic",
            ],
        }

        return subtask_templates.get(mode, subtask_templates["density_surf"])

    def activate_perfectionism(self, task: QuickTask, rounds: int = 3) -> QuickTask:
        """Activate smart intentive perfectionism on a task."""
        spatial_context = {
            'density': task.spatial_density,
            'altitude_km': task.source_zone[0],
            'inclination_deg': task.source_zone[1],
        }

        # Refine the task description
        refined = self.perfectionism.refine(task.description, spatial_context, rounds)
        task.output = refined
        task.refinement_cycles = rounds

        return task

    def burst(self, count: int = 5) -> List[QuickTask]:
        """Generate a burst of quick tasks across different modes."""
        modes = ["density_surf", "singularity_ride", "ability_hunt", "shell_crossing", "inversion"]
        tasks = []

        for i in range(count):
            mode = modes[i % len(modes)]
            task = self.quick_task(f"Burst task #{i+1}: {mode}", mode)
            self.activate_perfectionism(task, rounds=2)
            tasks.append(task)

        return tasks

    def get_state(self) -> Dict[str, Any]:
        """Get current generator state."""
        return {
            "awareness_level": round(self.awareness_level, 3),
            "total_satellites": len(self.catalogue.get('satellites', {})),
            "hotspots_found": len(self.hotspots),
            "shell_densities": {k: round(v, 4) for k, v in self.shell_densities.items()},
            "tasks_generated": self.task_counter,
            "refinement_rounds_total": len(self.perfectionism.refinement_history),
            "perfectionism_coefficient": round(self.perfectionism.perfectionism_coefficient, 4),
        }


# Activation function
def maximize_creativity(catalogue_path: Optional[str] = None) -> Dict[str, Any]:
    """Maximize model creativity through spatial awareness."""
    gen = QuickTaskGenerator(catalogue_path)
    gen.load()

    # Generate creative burst
    burst = gen.burst(10)

    state = gen.get_state()
    state["burst"] = [
        {
            "id": t.task_id,
            "description": t.description,
            "priority": t.priority.value,
            "zone": t.source_zone,
            "score": round(t.task_score, 4),
            "subtasks": len(t.subtasks),
        }
        for t in burst
    ]

    return state


# Global instance
quick_tasker = QuickTaskGenerator()
