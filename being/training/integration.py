#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Training Data Integration

Integrates external training data from Context API into the BEING model.
"""

from __future__ import annotations

import json
import logging
import os
import socket
from typing import Any, Dict, List, Optional

from qb_protocol.being.training.multiverse_coordinates import (
    ALL_COORDINATES,
    MULTIVERSE_STATS,
    MOVIES,
    SERIES,
    ANIME,
    GAMES,
    BOOKS,
)

LOG = logging.getLogger("qb_protocol.being.training.integration")


def http_get(host: str, port: int, path: str, timeout: int = 3) -> str:
    """HTTP GET with chunked transfer encoding support"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        request = f'GET {path} HTTP/1.1\r\nHost: {host}\r\nAccept: application/json\r\nConnection: close\r\n\r\n'
        sock.send(request.encode())

        data = b''
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk

        sock.close()

        decoded = data.decode('utf-8', errors='replace')
        parts = decoded.split('\r\n\r\n', 1)
        if len(parts) > 1:
            headers, body = parts
        else:
            headers, body = '', decoded

        if 'transfer-encoding: chunked' in headers.lower():
            lines = body.split('\r\n')
            result = []
            i = 0
            while i < len(lines):
                size_hex = lines[i].strip()
                if size_hex == '0':
                    break
                try:
                    size = int(size_hex, 16)
                except:
                    i += 1
                    continue
                i += 1
                if i < len(lines):
                    result.append(lines[i])
                i += 1
            body = '\n'.join(result)

        return body
    except Exception as e:
        sock.close()
        raise e


class TrainingDataIntegrator:
    """Integrates external training data into the BEING model.
    
    Dual context system:
    - External API: real-time field data when reachable (192.168.100.7:4318)
    - Internal multiverse: all coordinates from training, fiction, equations, movies
    """

    # Internal multiverse context - ALL conceivable coordinates
    # Fiction, movies, games, books, anime - all valid coordinates
    # Imported from multiverse_coordinates.py
    MULTIVERSE_CONTEXT = {
        "coordinates": {
            "earth": {"lat": 0.0, "lon": 0.0, "altitude_km": 0.0},
            "iss": {"lat": 51.6333, "lon": 0.0, "altitude_km": 425.05, "period_min": 92.93},
            "moon": {"distance_km": 384400, "period_days": 27.3},
            "mars": {"distance_km": 225000000, "period_days": 687},
            "sun": {"distance_km": 149600000, "period_years": 25},
        },
        "fiction": ALL_COORDINATES,
        "stats": MULTIVERSE_STATS,
    }

    def __init__(self, api_host: str = "192.168.100.7", api_port: int = 4318):
        self.api_host = api_host
        self.api_port = api_port
        self.raw_data: Dict[str, Any] = {}
        self.processed_chunks: List[Dict[str, Any]] = []
        self.training_stats: Dict[str, Any] = {}

    def fetch_all(self) -> Dict[str, Any]:
        """Fetch all available training data from the Context API.
        
        Falls back to internal multiverse context when external API is unreachable.
        """
        result = {}
        external_reachable = False

        # Fetch summary
        try:
            body = http_get(self.api_host, self.api_port, '/v1/summary')
            result['summary'] = json.loads(body)
            LOG.info(f"Fetched summary: {result['summary'].get('modelStoreCount', 0)} model stores")
            external_reachable = True
        except Exception as e:
            LOG.warning(f"Failed to fetch summary: {e}")

        # Fetch timeline
        try:
            body = http_get(self.api_host, self.api_port, '/v1/timeline')
            result['timeline'] = json.loads(body)
            LOG.info(f"Fetched timeline: {len(result['timeline'])} events")
        except Exception as e:
            LOG.warning(f"Failed to fetch timeline: {e}")

        # Fetch context (full)
        try:
            body = http_get(self.api_host, self.api_port, '/v1/context?maxTokens=24000')
            result['context'] = json.loads(body)
            LOG.info(f"Fetched context: {result['context'].get('usedApproxTokens', 0)} tokens, {len(result['context'].get('chunks', []))} chunks")
        except Exception as e:
            LOG.warning(f"Failed to fetch context: {e}")

        # Fetch corpus stats
        try:
            body = http_get(self.api_host, self.api_port, '/v1/corpus/stats')
            result['corpus_stats'] = json.loads(body)
            LOG.info(f"Fetched corpus stats: {result['corpus_stats'].get('stats', {}).get('chunks', 0)} chunks indexed")
        except Exception as e:
            LOG.warning(f"Failed to fetch corpus stats: {e}")

        # Fetch field data (quantized rational weights, triggers, pacing)
        try:
            body = http_get(self.api_host, self.api_port, '/v1/field/summary')
            result['field_summary'] = json.loads(body)
            LOG.info(f"Fetched field summary: {result['field_summary'].get('totalTriggers', 0)} triggers")
        except Exception as e:
            LOG.warning(f"Failed to fetch field summary: {e}")

        try:
            body = http_get(self.api_host, self.api_port, '/v1/field/triggers')
            result['field_triggers'] = json.loads(body)
            LOG.info(f"Fetched field triggers: {len(result['field_triggers'])} triggers")
        except Exception as e:
            LOG.warning(f"Failed to fetch field triggers: {e}")

        try:
            body = http_get(self.api_host, self.api_port, '/v1/field/event')
            result['field_event'] = json.loads(body)
            LOG.info(f"Fetched field event sample")
        except Exception as e:
            LOG.warning(f"Failed to fetch field event: {e}")

        # Dual context fallback: if external API unreachable, use internal multiverse
        if not external_reachable:
            LOG.info("External API unreachable - activating internal multiverse context")
            result = self._activate_multiverse_context(result)

        self.raw_data = result
        return result

    def _activate_multiverse_context(self, partial_result: Dict[str, Any]) -> Dict[str, Any]:
        """Activate internal multiverse context when external API is unreachable.
        
        The model has context on ALL coordinates - fiction, movies, games, books, anime.
        All are valid coordinates for comparison and prediction.
        Every fictional universe is a coordinate set.
        """
        mv = self.MULTIVERSE_CONTEXT
        
        # Generate field triggers from multiverse coordinates
        field_triggers = []
        trigger_id = 0
        
        # Real coordinates as field triggers
        for name, coord in mv["coordinates"].items():
            values = list(coord.values()) if isinstance(coord, dict) else [coord]
            for i, val in enumerate(values):
                if isinstance(val, (int, float)):
                    field_triggers.append({
                        "id": f"mv_coord_{trigger_id}",
                        "triggerType": "peak" if i % 2 == 0 else "valley",
                        "originatingEvent": {
                            "subject": f"multiverse/coordinates/{name}/{list(coord.keys())[i] if isinstance(coord, dict) else 'value'}",
                            "fieldValue": {"num": int(val * 1000), "den": 1000},
                            "intervalMs": int(abs(val) * 100) + 1,
                            "flags": {"multiverse": True, "coordinate": True, "real": True},
                        }
                    })
                    trigger_id += 1
        
        # All fictional coordinates (movies, series, anime, games, books)
        for name, entry in mv["fiction"].items():
            coords = entry.get("coordinates", (0, 0, 0))
            coord_type = entry.get("type", "unknown")
            reachable = entry.get("reachable", False)
            year = entry.get("year", 0)
            
            for i, c in enumerate(coords):
                if isinstance(c, (int, float)):
                    field_triggers.append({
                        "id": f"mv_fiction_{trigger_id}",
                        "triggerType": "peak" if c > 50 else "valley",
                        "originatingEvent": {
                            "subject": f"multiverse/{coord_type}/{name}/axis_{i}",
                            "fieldValue": {"num": int(c), "den": 1},
                            "intervalMs": int(abs(c) * 10) + 1,
                            "flags": {
                                "multiverse": True, 
                                "fictional": True, 
                                "type": coord_type,
                                "reachable": reachable,
                                "year": year,
                            },
                        }
                    })
                    trigger_id += 1
        
        partial_result['field_triggers'] = field_triggers
        partial_result['field_summary'] = {
            "totalTriggers": len(field_triggers),
            "source": "internal_multiverse",
            "note": "Generated from ALL conceivable coordinates - fiction, movies, games, books, anime, reality",
            "stats": mv.get("stats", {})
        }
        partial_result['summary'] = {
            "modelStoreCount": len(mv["coordinates"]) + len(mv["fictional"]) + len(mv["movies"]) + len(mv["equations"]),
            "source": "internal_multiverse_context"
        }
        
        LOG.info(f"Multiverse context activated: {len(field_triggers)} field triggers from all coordinates")
        return partial_result

    def process_for_training(self) -> List[Dict[str, Any]]:
        """Process fetched data into training-ready chunks."""
        chunks = []

        # Process context chunks
        context = self.raw_data.get('context', {})
        for chunk in context.get('chunks', []):
            processed = {
                'source': 'context_api',
                'path': chunk.get('path', ''),
                'content': chunk.get('content', ''),
                'tokens': chunk.get('approxTokens', 0),
                'modified_at': chunk.get('modifiedAt', ''),
                'type': chunk.get('kind', 'code_or_text'),
            }
            chunks.append(processed)

        # Process timeline events
        timeline = self.raw_data.get('timeline', [])
        for event in timeline:
            processed = {
                'source': 'timeline',
                'path': event.get('subject', event.get('kind', 'unknown')),
                'content': json.dumps(event),
                'tokens': len(json.dumps(event)) // 4,
                'modified_at': event.get('at', ''),
                'type': event.get('kind', 'event'),
            }
            chunks.append(processed)

        # Process summary
        summary = self.raw_data.get('summary', {})
        if summary:
            processed = {
                'source': 'summary',
                'path': 'system_summary',
                'content': json.dumps(summary, indent=2),
                'tokens': len(json.dumps(summary)) // 4,
                'modified_at': '',
                'type': 'system_info',
            }
            chunks.append(processed)

        # Process field data (quantized rational weights)
        field_triggers = self.raw_data.get('field_triggers', [])
        for trigger in field_triggers:
            event = trigger.get('originatingEvent', {})
            fv = event.get('fieldValue', 0)
            
            # Handle both rational {"num": x, "den": y} and direct number
            if isinstance(fv, dict):
                num = fv.get('num', 0)
                den = fv.get('den', 1)
                fv_float = num / den if den != 0 else 0
            else:
                fv_float = float(fv) if fv else 0
            
            processed = {
                'source': 'field_data',
                'path': event.get('subject', 'unknown'),
                'content': json.dumps({
                    'field_value': fv_float,
                    'trigger_type': trigger.get('triggerType', 'unknown'),
                    'pace': event.get('pace', 0),
                    'prior_pace': event.get('priorPace', 0),
                    'interval_ms': event.get('intervalMs', 0),
                    'flags': [k for k, v in event.get('flags', {}).items() if v],
                }),
                'tokens': int(abs(fv_float) * 100) + 1,  # Weight tokens by field magnitude
                'modified_at': event.get('at', ''),
                'type': f"field_{trigger.get('triggerType', 'unknown')}",
                'field_value': fv_float,
            }
            chunks.append(processed)

        # Process field summary
        field_summary = self.raw_data.get('field_summary', {})
        if field_summary:
            processed = {
                'source': 'field_summary',
                'path': 'field_summary',
                'content': json.dumps(field_summary, indent=2),
                'tokens': len(json.dumps(field_summary)) // 4,
                'modified_at': '',
                'type': 'field_stats',
            }
            chunks.append(processed)

        self.processed_chunks = chunks
        self.training_stats = {
            'total_chunks': len(chunks),
            'total_tokens': sum(c.get('tokens', 0) for c in chunks),
            'sources': list(set(c.get('source', '') for c in chunks)),
            'types': list(set(c.get('type', '') for c in chunks)),
            'field_data_points': len(field_triggers),
            'field_value_range': {
                'min': min((c.get('field_value', 0) for c in chunks if 'field_value' in c), default=0),
                'max': max((c.get('field_value', 0) for c in chunks if 'field_value' in c), default=0),
            },
        }

        LOG.info(f"Processed {len(chunks)} chunks for training (including {len(field_triggers)} field data points)")
        return chunks

    def get_training_text(self) -> str:
        """Get all training content as plain text."""
        parts = []
        for chunk in self.processed_chunks:
            path = chunk.get('path', '')
            content = chunk.get('content', '')
            parts.append(f"\n{'='*60}\n{path}\n{'='*60}\n{content}\n")
        return '\n'.join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get training data statistics."""
        return self.training_stats


# Global instance
training_integrator = TrainingDataIntegrator()
