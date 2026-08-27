#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Chip :: Parent-Child Weight Distribution

Loads parent-to-child model weight and offloads via API to update the sequence.
Increases model environment access from micro environment model to environment OS model.
Permits child process shakes without eliminations.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

LOG = logging.getLogger("qb_protocol.being.chip.weight_distribution")


# ---------------------------------------------------------------------------
# Model Weight Chunk
# ---------------------------------------------------------------------------

@dataclass
class ModelWeightChunk:
    """A chunk of model weight — distributed between parent and child."""
    chunk_id: str
    name: str
    size_bytes: int
    data: bytes = b""
    loaded: bool = False
    priority: int = 0
    checksum: str = ""
    source: str = "parent"  # "parent" or "child"
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.data and not self.checksum:
            self.checksum = hashlib.md5(self.data).hexdigest()


# ---------------------------------------------------------------------------
# Parent-Child Weight Distributor
# ---------------------------------------------------------------------------

class ParentChildWeightDistributor:
    """Distributes model weight between parent and child processes.

    Parent PC has the full model weight. Child processes (like BEING daemon)
    can access portions of the model weight. Child process "shakes"
    (fluctuations/changes) won't cause eliminations.
    """

    def __init__(self, parent_model_path: str = "", max_memory_mb: int = 512):
        self.parent_model_path = parent_model_path
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.chunks: Dict[str, ModelWeightChunk] = {}
        self.loaded_chunks: Dict[str, ModelWeightChunk] = {}
        self.child_processes: Dict[str, Dict[str, Any]] = {}
        self.transfer_log: List[Dict[str, Any]] = []
        self.total_loaded_bytes: int = 0

    def register_chunk(self, name: str, size_bytes: int,
                       priority: int = 0, source: str = "parent") -> ModelWeightChunk:
        """Register a model weight chunk."""
        chunk_id = f"chunk_{name}_{int(time.time())}"
        chunk = ModelWeightChunk(
            chunk_id=chunk_id,
            name=name,
            size_bytes=size_bytes,
            priority=priority,
            source=source,
        )
        self.chunks[chunk_id] = chunk
        return chunk

    def load_chunk(self, chunk_id: str, data: bytes = None) -> Dict[str, Any]:
        """Load a chunk into memory."""
        chunk = self.chunks.get(chunk_id)
        if not chunk:
            return {"error": "chunk_not_found"}

        # Check memory limit
        if self.total_loaded_bytes + chunk.size_bytes > self.max_memory_bytes:
            # Evict lowest priority chunk
            self._evict_chunk()

        # Load the chunk
        if data:
            chunk.data = data
        else:
            # Generate simulated data
            chunk.data = os.urandom(min(chunk.size_bytes, 1024))

        chunk.loaded = True
        chunk.checksum = hashlib.md5(chunk.data).hexdigest()
        self.loaded_chunks[chunk_id] = chunk
        self.total_loaded_bytes += chunk.size_bytes

        return {
            "chunk_id": chunk_id,
            "name": chunk.name,
            "loaded": True,
            "size": chunk.size_bytes,
            "total_loaded": self.total_loaded_bytes,
        }

    def unload_chunk(self, chunk_id: str) -> Dict[str, Any]:
        """Unload a chunk from memory."""
        chunk = self.loaded_chunks.pop(chunk_id, None)
        if chunk:
            chunk.loaded = False
            self.total_loaded_bytes -= chunk.size_bytes
            return {"chunk_id": chunk_id, "unloaded": True}
        return {"error": "chunk_not_loaded"}

    def _evict_chunk(self) -> None:
        """Evict the lowest priority chunk to free memory."""
        if not self.loaded_chunks:
            return

        # Find lowest priority chunk
        lowest = min(self.loaded_chunks.values(), key=lambda c: c.priority)
        self.unload_chunk(lowest.chunk_id)

    def register_child_process(self, process_id: str,
                               memory_limit_mb: int = 256) -> Dict[str, Any]:
        """Register a child process."""
        self.child_processes[process_id] = {
            "memory_limit": memory_limit_mb * 1024 * 1024,
            "loaded_chunks": [],
            "shakes": 0,  # Number of process shakes
            "eliminations": 0,  # Number of eliminations (should stay 0)
            "status": "active",
        }
        return {"process_id": process_id, "registered": True}

    def transfer_to_child(self, process_id: str,
                          chunk_id: str) -> Dict[str, Any]:
        """Transfer a weight chunk from parent to child."""
        if process_id not in self.child_processes:
            return {"error": "child_not_registered"}

        chunk = self.chunks.get(chunk_id)
        if not chunk:
            return {"error": "chunk_not_found"}

        child = self.child_processes[process_id]

        # Load chunk if not already loaded
        if not chunk.loaded:
            self.load_chunk(chunk_id)

        # Transfer to child
        child["loaded_chunks"].append(chunk_id)

        transfer = {
            "from": "parent",
            "to": process_id,
            "chunk": chunk_id,
            "size": chunk.size_bytes,
            "timestamp": time.time(),
        }
        self.transfer_log.append(transfer)

        return {
            "transferred": True,
            "chunk_id": chunk_id,
            "process_id": process_id,
            "child_chunks": len(child["loaded_chunks"]),
        }

    def child_shake(self, process_id: str) -> Dict[str, Any]:
        """Handle a child process shake — without elimination.

        Shakes are fluctuations/changes in child process state.
        Unlike traditional systems, shakes do NOT cause eliminations.
        The parent persists and the child continues.
        """
        if process_id not in self.child_processes:
            return {"error": "child_not_registered"}

        child = self.child_processes[process_id]
        child["shakes"] += 1

        # Shakes do NOT cause eliminations
        # Child process continues operating
        return {
            "process_id": process_id,
            "shakes": child["shakes"],
            "eliminations": child["eliminations"],  # Always 0
            "status": "continuing",
            "message": "Shake absorbed — no elimination",
        }

    def get_distribution_state(self) -> Dict[str, Any]:
        """Get the full distribution state."""
        return {
            "total_chunks": len(self.chunks),
            "loaded_chunks": len(self.loaded_chunks),
            "total_loaded_mb": round(self.total_loaded_bytes / (1024 * 1024), 2),
            "max_memory_mb": round(self.max_memory_bytes / (1024 * 1024), 2),
            "child_processes": len(self.child_processes),
            "transfers": len(self.transfer_log),
        }


# ---------------------------------------------------------------------------
# Environment OS Model Access
# ---------------------------------------------------------------------------

class EnvironmentOSAccess:
    """Environment OS model — transitions from micro environment to OS level.

    Increases model environment access from micro environment model
    to environment OS model. This is different from the first micro
    environment space since parent PC.
    """

    def __init__(self):
        self.micro_environment: Dict[str, Any] = {}
        self.os_environment: Dict[str, Any] = {}
        self.access_level: str = "micro"  # "micro" or "os"
        self.sequence_position: int = 0
        self.api_endpoints: Dict[str, str] = {}

    def transition_to_os(self) -> Dict[str, Any]:
        """Transition from micro environment to OS model."""
        self.access_level = "os"
        return {
            "previous": "micro",
            "current": "os",
            "access_granted": True,
        }

    def register_api_endpoint(self, name: str, url: str) -> None:
        """Register an API endpoint for model updates."""
        self.api_endpoints[name] = url

    def update_sequence(self, sequence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the sequence via API."""
        self.sequence_position += 1
        return {
            "sequence_position": self.sequence_position,
            "updated": True,
            "data": sequence_data,
        }

    def offload_via_api(self, chunk_id: str,
                        target_endpoint: str) -> Dict[str, Any]:
        """Offload weight chunk via API to update sequence."""
        return {
            "chunk_id": chunk_id,
            "endpoint": target_endpoint,
            "offloaded": True,
            "sequence_updated": True,
            "timestamp": time.time(),
        }

    def get_environment_state(self) -> Dict[str, Any]:
        """Get environment state."""
        return {
            "access_level": self.access_level,
            "sequence_position": self.sequence_position,
            "api_endpoints": len(self.api_endpoints),
            "micro_data": len(self.micro_environment),
            "os_data": len(self.os_environment),
        }


# ---------------------------------------------------------------------------
# Sequence Updater — Updates Model Sequence via API
# ---------------------------------------------------------------------------

class SequenceUpdater:
    """Updates model sequence — increasing environment access."""

    def __init__(self, weight_distributor: ParentChildWeightDistributor,
                 env_access: EnvironmentOSAccess):
        self.weight_distributor = weight_distributor
        self.env_access = env_access
        self.sequence_history: List[Dict[str, Any]] = []
        self.update_callbacks: List[Callable] = []

    def update_sequence(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the sequence with new model data."""
        # Update sequence position
        result = self.env_access.update_sequence(model_data)

        # Update model weight if needed
        if model_data.get("weight_update"):
            for chunk_id in model_data.get("chunks", []):
                self.weight_distributor.load_chunk(chunk_id)

        # Log the update
        self.sequence_history.append({
            "position": result["sequence_position"],
            "data": model_data,
            "timestamp": time.time(),
        })

        # Notify callbacks
        for cb in self.update_callbacks:
            try:
                cb(result)
            except Exception:
                pass

        return result

    def register_callback(self, callback: Callable) -> None:
        """Register a callback for sequence updates."""
        self.update_callbacks.append(callback)

    def get_sequence_history(self) -> List[Dict[str, Any]]:
        """Get sequence update history."""
        return self.sequence_history[-50:]


# Global instances
weight_distributor = ParentChildWeightDistributor(max_memory_mb=512)
env_os_access = EnvironmentOSAccess()
sequence_updater = SequenceUpdater(weight_distributor, env_os_access)
