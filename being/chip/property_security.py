#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Property Security Management

Comprehensive security management for all properties in the catalogue.
Integrates camera systems, emergency monitoring, and car storage security.

Features:
- Property catalogue security integration
- Camera automation for all ownership types
- Car storage/garage monitoring
- Emergency case detection and response
- Centralized monitoring dashboard
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

LOG = logging.getLogger("qb_protocol.being.chip.property_security")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class OwnershipType(Enum):
    """Types of property ownership."""
    FULL_OWNERSHIP = "full_ownership"
    LLC_OWNED = "llc_owned"
    TRUST_OWNED = "trust_owned"
    RENTAL_PROPERTY = "rental_property"
    VACATION_RENTAL = "vacation_rental"
    COMMERCIAL_LEASE = "commercial_lease"
    JOINT_OWNERSHIP = "joint_ownership"


class SecurityZone(Enum):
    """Security zones within a property."""
    PERIMETER = "perimeter"
    ENTRY_POINTS = "entry_points"
    COMMON_AREAS = "common_areas"
    PARKING = "parking"
    CAR_STORAGE = "car_storage"
    GARAGE = "garage"
    PATIO = "patio"
    INTERIOR_COMMON = "interior_common"


class EmergencyType(Enum):
    """Types of security emergencies."""
    BURGLARY = "burglary"
    VANDALISM = "vandalism"
    FIRE = "fire"
    FLOOD = "flood"
    TRESPASSER = "trespasser"
    VEHICLE_THEFT = "vehicle_theft"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    CAMERA_TAMPERING = "camera_tampering"
    POWER_OUTAGE = "power_outage"
    NETWORK_FAILURE = "network_failure"


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PropertySecurityProfile:
    """Security profile for a single property."""
    property_id: str
    property_name: str
    ownership_type: OwnershipType
    address: str
    city: str
    state: str
    zip_code: str
    has_garage: bool = False
    has_car_storage: bool = False
    has_patio: bool = False
    has_driveway: bool = False
    has_backyard: bool = False
    num_floors: int = 1
    square_footage: int = 2000
    total_cameras: int = 0
    exterior_cameras: int = 0
    interior_cameras: int = 0
    car_storage_cameras: int = 0
    monitoring_active: bool = False
    emergency_contacts: List[str] = field(default_factory=list)
    security_notes: str = ""


@dataclass
class EmergencyAlert:
    """Security emergency alert."""
    alert_id: str
    property_id: str
    emergency_type: EmergencyType
    priority: AlertPriority
    timestamp: str
    description: str
    camera_ids: List[str] = field(default_factory=list)
    action_taken: str = ""
    resolved: bool = False
    resolved_at: str = ""


@dataclass
class CarStorageSecurity:
    """Car storage/garage security configuration."""
    storage_id: str
    property_id: str
    storage_type: str  # garage, carport, parking_lot, warehouse
    capacity: int = 1
    cameras: List[str] = field(default_factory=list)
    has_motion_sensors: bool = True
    has_door_sensors: bool = True
    has_alarm: bool = True
    vehicles_stored: List[str] = field(default_factory=list)
    monitoring_status: str = "active"


# =============================================================================
# PROPERTY SECURITY MANAGEMENT ENGINE
# =============================================================================

class PropertySecurityEngine:
    """
    Centralized security management for all properties.
    
    Manages:
    - Camera installations for all property types
    - Car storage security
    - Emergency detection and response
    - Centralized monitoring dashboard
    """
    
    def __init__(self):
        self._property_profiles: Dict[str, PropertySecurityProfile] = {}
        self._emergency_alerts: List[EmergencyAlert] = []
        self._car_storage: Dict[str, CarStorageSecurity] = {}
        self._monitoring_active = False
        self._alert_counter = 0
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self._alert_counter += 1
        return f"ALERT_{self._alert_counter:04d}"
    
    def register_property(self, property_id: str, property_name: str,
                         ownership_type: OwnershipType,
                         address: str, city: str, state: str,
                         zip_code: str, **kwargs) -> PropertySecurityProfile:
        """
        Register a property for security management.
        
        All properties in the catalogue should be registered here
        to receive automated camera placement and monitoring.
        """
        profile = PropertySecurityProfile(
            property_id=property_id,
            property_name=property_name,
            ownership_type=ownership_type,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            has_garage=kwargs.get("has_garage", False),
            has_car_storage=kwargs.get("has_car_storage", False),
            has_patio=kwargs.get("has_patio", False),
            has_driveway=kwargs.get("has_driveway", False),
            has_backyard=kwargs.get("has_backyard", False),
            num_floors=kwargs.get("num_floors", 1),
            square_footage=kwargs.get("square_footage", 2000),
            emergency_contacts=kwargs.get("emergency_contacts", []),
            security_notes=kwargs.get("security_notes", ""),
        )
        
        self._property_profiles[property_id] = profile
        
        return profile
    
    def setup_property_cameras(self, property_id: str) -> Dict[str, Any]:
        """
        Setup optimal camera placement for a property.
        
        Uses the SecurityCameraEngine to calculate placement
        based on property features.
        """
        # Import here using importlib to avoid circular imports
        import importlib.util
        import sys
        
        module_name = 'being.chip.security_camera'
        if module_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(module_name, 'being/chip/security_camera.py')
            camera_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = camera_module
            spec.loader.exec_module(camera_module)
        else:
            camera_module = sys.modules[module_name]
        
        SecurityCameraEngine = camera_module.SecurityCameraEngine
        PropertyType = camera_module.PropertyType
        
        profile = self._property_profiles.get(property_id)
        if not profile:
            return {"error": "Property not registered"}
        
        # Map ownership type to property type for camera placement
        property_type_map = {
            OwnershipType.FULL_OWNERSHIP: PropertyType.SINGLE_FAMILY,
            OwnershipType.LLC_OWNED: PropertyType.SINGLE_FAMILY,
            OwnershipType.TRUST_OWNED: PropertyType.SINGLE_FAMILY,
            OwnershipType.RENTAL_PROPERTY: PropertyType.MULTI_FAMILY,
            OwnershipType.VACATION_RENTAL: PropertyType.VACATION_RENTAL,
            OwnershipType.COMMERCIAL_LEASE: PropertyType.COMMERCIAL,
            OwnershipType.JOINT_OWNERSHIP: PropertyType.MULTI_FAMILY,
        }
        
        camera_property_type = property_type_map.get(profile.ownership_type, PropertyType.SINGLE_FAMILY)
        
        # Create camera engine and get placement
        camera_engine = SecurityCameraEngine()
        placement = camera_engine.get_optimal_placement(
            property_id=property_id,
            property_type=camera_property_type,
            has_garage=profile.has_garage,
            has_patio=profile.has_patio,
            has_driveway=profile.has_driveway,
            has_backyard=profile.has_backyard,
            num_floors=profile.num_floors,
            square_footage=profile.square_footage,
        )
        
        # Update profile with camera counts
        profile.total_cameras = placement.total_cameras
        profile.exterior_cameras = placement.exterior_cameras
        profile.interior_cameras = placement.interior_cameras
        profile.car_storage_cameras = sum(1 for c in placement.cameras if "garage" in c.location.value)
        profile.monitoring_active = True
        
        return {
            "property_id": property_id,
            "property_name": profile.property_name,
            "ownership_type": profile.ownership_type.value,
            "total_cameras": placement.total_cameras,
            "exterior_cameras": placement.exterior_cameras,
            "interior_cameras": placement.interior_cameras,
            "car_storage_cameras": profile.car_storage_cameras,
            "coverage_score": placement.coverage_score,
            "cameras": [
                {
                    "id": c.camera_id,
                    "name": c.name,
                    "location": c.location.value,
                    "type": c.camera_type.value,
                    "is_exterior": c.is_exterior,
                    "is_discrete": c.is_discrete,
                }
                for c in placement.cameras
            ],
        }
    
    def setup_car_storage_security(self, property_id: str,
                                    storage_type: str = "garage",
                                    capacity: int = 2,
                                    vehicles: List[str] = None) -> CarStorageSecurity:
        """
        Setup dedicated car storage security.
        
        For vehicle storage (garage, carport, warehouse),
        creates dedicated monitoring with:
        - Interior cameras
        - Motion sensors
        - Door sensors
        - Alarm system
        """
        profile = self._property_profiles.get(property_id)
        if not profile:
            return None
        
        storage = CarStorageSecurity(
            storage_id=f"storage_{property_id}",
            property_id=property_id,
            storage_type=storage_type,
            capacity=capacity,
            cameras=[
                f"{property_id}_garage_interior_01",
                f"{property_id}_garage_exterior_01",
            ],
            has_motion_sensors=True,
            has_door_sensors=True,
            has_alarm=True,
            vehicles_stored=vehicles or [],
            monitoring_status="active",
        )
        
        self._car_storage[property_id] = storage
        profile.has_car_storage = True
        
        return storage
    
    def detect_emergency(self, property_id: str,
                        emergency_type: EmergencyType,
                        description: str,
                        camera_ids: List[str] = None) -> EmergencyAlert:
        """
        Detect and log a security emergency.
        
        Automatically:
        1. Creates an alert
        2. Determines priority
        3. Logs the event
        4. Suggests response actions
        """
        # Determine priority based on emergency type
        priority_map = {
            EmergencyType.BURGLARY: AlertPriority.CRITICAL,
            EmergencyType.VANDALISM: AlertPriority.HIGH,
            EmergencyType.FIRE: AlertPriority.CRITICAL,
            EmergencyType.FLOOD: AlertPriority.HIGH,
            EmergencyType.TRESPASSER: AlertPriority.HIGH,
            EmergencyType.VEHICLE_THEFT: AlertPriority.CRITICAL,
            EmergencyType.SUSPICIOUS_ACTIVITY: AlertPriority.MEDIUM,
            EmergencyType.CAMERA_TAMPERING: AlertPriority.HIGH,
            EmergencyType.POWER_OUTAGE: AlertPriority.MEDIUM,
            EmergencyType.NETWORK_FAILURE: AlertPriority.MEDIUM,
        }
        
        priority = priority_map.get(emergency_type, AlertPriority.MEDIUM)
        
        # Determine automatic action
        action_map = {
            EmergencyType.BURGLARY: "ALERT_AUTHORITIES + LOCKDOWN + RECORDING",
            EmergencyType.VANDALISM: "ALERT_OWNER + RECORD_EVIDENCE",
            EmergencyType.FIRE: "ALERT_FIRE_DEPT + EVACUATE",
            EmergencyType.FLOOD: "ALERT_OWNER + SHUT_OFF_UTILITIES",
            EmergencyType.TRESPASSER: "ALERT_OWNER + AUDIO_WARNING + RECORDING",
            EmergencyType.VEHICLE_THEFT: "ALERT_AUTHORITIES + LOCKDOWN + RECORDING",
            EmergencyType.SUSPICIOUS_ACTIVITY: "MONITOR + RECORD + ALERT_OWNER",
            EmergencyType.CAMERA_TAMPERING: "ALERT_OWNER + BACKUP_CAMERAS",
            EmergencyType.POWER_OUTAGE: "SWITCH_TO_BATTERY + ALERT_OWNER",
            EmergencyType.NETWORK_FAILURE: "LOCAL_RECORDING + ALERT_OWNER",
        }
        
        action = action_map.get(emergency_type, "MONITOR + ALERT_OWNER")
        
        alert = EmergencyAlert(
            alert_id=self._generate_alert_id(),
            property_id=property_id,
            emergency_type=emergency_type,
            priority=priority,
            timestamp=datetime.now().isoformat(),
            description=description,
            camera_ids=camera_ids or [],
            action_taken=action,
        )
        
        self._emergency_alerts.append(alert)
        
        return alert
    
    def get_property_security_status(self, property_id: str) -> Dict[str, Any]:
        """Get complete security status for a property."""
        profile = self._property_profiles.get(property_id)
        if not profile:
            return {"error": "Property not registered"}
        
        storage = self._car_storage.get(property_id)
        property_alerts = [a for a in self._emergency_alerts if a.property_id == property_id]
        
        return {
            "property_id": property_id,
            "property_name": profile.property_name,
            "address": f"{profile.address}, {profile.city}, {profile.state} {profile.zip_code}",
            "ownership_type": profile.ownership_type.value,
            "cameras": {
                "total": profile.total_cameras,
                "exterior": profile.exterior_cameras,
                "interior": profile.interior_cameras,
                "car_storage": profile.car_storage_cameras,
            },
            "monitoring_active": profile.monitoring_active,
            "car_storage": {
                "type": storage.storage_type if storage else None,
                "cameras": storage.cameras if storage else [],
                "vehicles": storage.vehicles_stored if storage else [],
                "status": storage.monitoring_status if storage else "none",
            },
            "alerts": {
                "total": len(property_alerts),
                "unresolved": len([a for a in property_alerts if not a.resolved]),
                "critical": len([a for a in property_alerts if a.priority == AlertPriority.CRITICAL]),
            },
        }
    
    def get_all_properties_status(self) -> Dict[str, Any]:
        """Get security status for all registered properties."""
        total_cameras = sum(p.total_cameras for p in self._property_profiles.values())
        total_exterior = sum(p.exterior_cameras for p in self._property_profiles.values())
        total_interior = sum(p.interior_cameras for p in self._property_profiles.values())
        total_car_storage = sum(p.car_storage_cameras for p in self._property_profiles.values())
        
        return {
            "total_properties": len(self._property_profiles),
            "total_cameras": total_cameras,
            "total_exterior": total_exterior,
            "total_interior": total_interior,
            "total_car_storage": total_car_storage,
            "monitoring_active": self._monitoring_active,
            "total_alerts": len(self._emergency_alerts),
            "unresolved_alerts": len([a for a in self._emergency_alerts if not a.resolved]),
            "properties": {
                pid: {
                    "name": p.property_name,
                    "ownership": p.ownership_type.value,
                    "cameras": p.total_cameras,
                    "monitoring": p.monitoring_active,
                }
                for pid, p in self._property_profiles.items()
            },
        }
    
    def get_emergency_alerts(self, property_id: str = None,
                            priority: AlertPriority = None,
                            unresolved_only: bool = True) -> List[Dict[str, Any]]:
        """Get emergency alerts with optional filtering."""
        alerts = self._emergency_alerts
        
        if property_id:
            alerts = [a for a in alerts if a.property_id == property_id]
        
        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        return [
            {
                "alert_id": a.alert_id,
                "property_id": a.property_id,
                "type": a.emergency_type.value,
                "priority": a.priority.value,
                "timestamp": a.timestamp,
                "description": a.description,
                "action": a.action_taken,
                "resolved": a.resolved,
            }
            for a in alerts
        ]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an emergency alert."""
        for alert in self._emergency_alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now().isoformat()
                return True
        return False
    
    def start_centralized_monitoring(self) -> Dict[str, Any]:
        """Start centralized monitoring for all properties."""
        self._monitoring_active = True
        
        return {
            "status": "ACTIVE",
            "monitored_properties": len(self._property_profiles),
            "total_cameras": sum(p.total_cameras for p in self._property_profiles.values()),
            "monitoring_features": [
                "Real-time camera health monitoring",
                "Motion detection across all properties",
                "Emergency auto-detection",
                "Car storage security monitoring",
                "Tamper detection",
                "Power/network failure alerts",
                "Centralized alert management",
            ],
            "emergency_response": {
                "burglary": "Alert authorities + lockdown + recording",
                "fire": "Alert fire department + evacuate",
                "vehicle_theft": "Alert authorities + lockdown + recording",
                "trespasser": "Alert owner + audio warning + recording",
                "camera_tamper": "Alert owner + backup cameras",
                "power_outage": "Switch to battery + alert owner",
            },
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

property_security_engine = PropertySecurityEngine()
