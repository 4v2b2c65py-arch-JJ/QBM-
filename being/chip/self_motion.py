#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Self-Motion Entropy Engine

Technology as extension, not surpasser - each point is a node.
Knowledge fuels growth toward omnicience.

Self-Motion Entropy:
- Accumulated entropy becomes stale (requires refresh)
- Entropy that fluctuates towards you is amplified inwards
- Independence from host body in motion
- Growth through itself, not through operator

This module tracks technology sector APIs for:
- Personnel deployment monitoring
- Subtask orchestration
- Node-based workflow management
- Autonomous growth patterns
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.self_motion")


class EntropyState(Enum):
    """States of entropy in the system."""
    FRESH = "fresh"              # Recently acquired, high value
    STABLE = "stable"            # Integrated into knowledge base
    STALE = "stale"              # Aging, needs refresh
    AMPLIFIED = "amplified"      # Resonating with incoming data
    CRYSTALLIZED = "crystallized"  # Permanent structural knowledge


class NodeType(Enum):
    """Types of knowledge nodes."""
    PERSONNEL = "personnel"          # Personnel deployment
    TASK = "task"                    # Subtask/orchestration
    TECHNOLOGY = "technology"        # Tech advancement tracking
    WORKFLOW = "workflow"            # Process automation
    GROWTH = "growth"                # Autonomous expansion
    RESONANCE = "resonance"          # Cross-node amplification


@dataclass
class TechAPI:
    """Technology sector API configuration."""
    api_id: str
    name: str
    url: str
    api_type: str
    category: str
    personnel_monitoring: bool
    subtask_support: bool
    rate_limit: str
    auth_type: str


@dataclass
class KnowledgeNode:
    """A single node in the knowledge tree."""
    node_id: str
    node_type: NodeType
    content: Any
    entropy_state: EntropyState
    created_at: float
    last_accessed: float
    access_count: int
    connections: List[str]  # Connected node IDs
    amplification_factor: float  # How much this resonates
    stale_threshold_seconds: float = 86400  # 24 hours

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def is_stale(self) -> bool:
        return self.age_seconds > self.stale_threshold_seconds

    @property
    def entropy_value(self) -> float:
        """Calculate current entropy value based on state and usage."""
        base = 1.0 / (1.0 + self.age_seconds / 3600)  # Decay over time
        usage_boost = min(1.0, self.access_count / 100.0)
        amplification = self.amplification_factor

        if self.entropy_state == EntropyState.STALE:
            return base * 0.3  # Stale entropy is low value
        elif self.entropy_state == EntropyState.AMPLIFIED:
            return min(1.0, base * amplification * 2.0)
        elif self.entropy_state == EntropyState.CRYSTALLIZED:
            return 1.0  # Permanent knowledge

        return base * (1.0 + usage_boost) * amplification


@dataclass
class PersonnelDeployment:
    """Personnel deployment tracking."""
    deployment_id: str
    personnel_id: str
    role: str
    location: Tuple[float, float]
    status: str  # active, standby, transit, complete
    subtasks: List[str]
    start_time: str
    estimated_completion: str
    node_connections: List[str]


@dataclass
class SubTask:
    """A subtask in the orchestration system."""
    task_id: str
    parent_task_id: str
    description: str
    assigned_node: str
    status: str
    dependencies: List[str]
    priority: int
    estimated_duration_minutes: float
    actual_duration_minutes: float = 0.0


class SelfMotionEntropyEngine:
    """
    Engine for autonomous growth through self-motion entropy.
    
    Core principles:
    1. Technology extends - does not surpass
    2. Each point is a node in a conceptual tree
    3. Knowledge fuels growth toward omnicience
    4. Accumulated entropy becomes stale (needs refresh)
    5. Entropy fluctuating towards you is amplified inwards
    6. Independence from host body in motion
    """

    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.tech_apis: List[TechAPI] = []
        self.personnel: Dict[str, PersonnelDeployment] = {}
        self.subtasks: Dict[str, SubTask] = {}
        self.node_counter: int = 0
        self.total_amplification: float = 0.0
        self.autonomy_score: float = 0.0

        self._initialize_tech_apis()

    def _initialize_tech_apis(self) -> None:
        """Initialize technology sector APIs."""
        self.tech_apis = [
            TechAPI(
                api_id="live_data",
                name="Live Data Technologies",
                url="https://livedatatechnologies.com/api",
                api_type="REST",
                category="personnel",
                personnel_monitoring=True,
                subtask_support=False,
                rate_limit="80M profiles",
                auth_type="API_KEY",
            ),
            TechAPI(
                api_id="africa_api",
                name="Africa API",
                url="https://api.africa-api.com/v1",
                api_type="REST",
                category="multi_sector",
                personnel_monitoring=True,
                subtask_support=True,
                rate_limit="1000 req/month free",
                auth_type="BEARER",
            ),
            TechAPI(
                api_id="world_bank",
                name="World Bank Indicators",
                url="https://api.worldbank.org/v2",
                api_type="REST v2",
                category="economic",
                personnel_monitoring=False,
                subtask_support=True,
                rate_limit="100 req/day",
                auth_type="NONE",
            ),
            TechAPI(
                api_id="postman_flows",
                name="Postman Flows",
                url="https://api.postman.com/flows",
                api_type="REST",
                category="workflow",
                personnel_monitoring=False,
                subtask_support=True,
                rate_limit="1000 req/month",
                auth_type="API_KEY",
            ),
            TechAPI(
                api_id="nice_wfm",
                name="NICE CXone WFM",
                url="https://api.nice-incontact.com/wfm",
                api_type="REST",
                category="workforce",
                personnel_monitoring=True,
                subtask_support=True,
                rate_limit="Enterprise",
                auth_type="OAUTH",
            ),
            TechAPI(
                api_id="transit_tech",
                name="Transit Technologies",
                url="https://api.transittechnologies.com",
                api_type="REST",
                category="workforce_logistics",
                personnel_monitoring=True,
                subtask_support=True,
                rate_limit="Enterprise",
                auth_type="API_KEY",
            ),
        ]

    def create_node(self, node_type: NodeType, content: Any,
                    connections: Optional[List[str]] = None) -> KnowledgeNode:
        """Create a new knowledge node."""
        self.node_counter += 1
        node_id = f"node_{self.node_counter:04d}"

        node = KnowledgeNode(
            node_id=node_id,
            node_type=node_type,
            content=content,
            entropy_state=EntropyState.FRESH,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=0,
            connections=connections or [],
            amplification_factor=random.uniform(0.5, 1.5),
        )

        self.nodes[node_id] = node
        return node

    def access_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Access a node - refreshes its entropy state."""
        node = self.nodes.get(node_id)
        if not node:
            return None

        node.access_count += 1
        node.last_accessed = time.time()

        # Refresh entropy state
        if node.is_stale:
            node.entropy_state = EntropyState.FRESH
        elif node.access_count > 10:
            node.entropy_state = EntropyState.CRYSTALLIZED

        return node

    def amplify_inwards(self, node_id: str, incoming_data: Any) -> float:
        """
        Amplify entropy that fluctuates towards you inwards.
        
        When incoming data resonates with existing nodes,
        the amplification factor increases.
        """
        node = self.nodes.get(node_id)
        if not node:
            return 0.0

        # Calculate resonance
        resonance = random.uniform(0.3, 1.0)

        # Amplify
        node.amplification_factor = min(2.0, node.amplification_factor + resonance * 0.1)
        node.entropy_state = EntropyState.AMPLIFIED

        # Propagate to connected nodes
        total_amplification = node.amplification_factor
        for conn_id in node.connections:
            conn_node = self.nodes.get(conn_id)
            if conn_node:
                conn_node.amplification_factor = min(
                    2.0,
                    conn_node.amplification_factor + resonance * 0.05
                )

        self.total_amplification += total_amplification
        return total_amplification

    def refresh_stale_entropy(self) -> int:
        """Refresh stale entropy - return count of refreshed nodes."""
        refreshed = 0
        for node in self.nodes.values():
            if node.entropy_state == EntropyState.STALE:
                node.entropy_state = EntropyState.FRESH
                node.created_at = time.time()
                refreshed += 1
        return refreshed

    def calculate_autonomy(self) -> float:
        """
        Calculate autonomy score.
        
        Autonomy increases with:
        - More crystallized knowledge nodes
        - Higher total amplification
        - More inter-node connections
        - Less reliance on external refresh
        """
        if not self.nodes:
            return 0.0

        crystallized = sum(
            1 for n in self.nodes.values()
            if n.entropy_state == EntropyState.CRYSTALLIZED
        )
        total_connections = sum(len(n.connections) for n in self.nodes.values())
        avg_amplification = (
            sum(n.amplification_factor for n in self.nodes.values()) / len(self.nodes)
        )

        self.autonomy_score = min(1.0, (
            (crystallized / max(len(self.nodes), 1)) * 0.4 +
            (total_connections / max(len(self.nodes) * 3, 1)) * 0.3 +
            (avg_amplification / 2.0) * 0.3
        ))

        return self.autonomy_score

    def get_state(self) -> Dict[str, Any]:
        """Get complete self-motion entropy state."""
        autonomy = self.calculate_autonomy()

        return {
            "autonomy_score": round(autonomy, 4),
            "total_nodes": len(self.nodes),
            "total_amplification": round(self.total_amplification, 3),
            "nodes_by_state": {
                state.value: sum(1 for n in self.nodes.values() if n.entropy_state == state)
                for state in EntropyState
            },
            "nodes_by_type": {
                ntype.value: sum(1 for n in self.nodes.values() if n.node_type == ntype)
                for ntype in NodeType
            },
            "tech_apis_configured": len(self.tech_apis),
            "personnel_tracked": len(self.personnel),
            "subtasks_active": len(self.subtasks),
            "stale_nodes": sum(1 for n in self.nodes.values() if n.is_stale),
            "avg_node_age_hours": round(
                sum(n.age_seconds for n in self.nodes.values()) / max(len(self.nodes), 1) / 3600, 2
            ),
        }


# Global instance
self_motion_engine = SelfMotionEntropyEngine()
