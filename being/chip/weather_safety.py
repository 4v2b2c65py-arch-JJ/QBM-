#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Weather & Safety Monitoring

Critical safety system for all transport operations.
Monitors weather conditions, performs pre-departure checks,
and ensures security of all personnel (employees, humanoids, beings) and equipment.

Features:
- Real-time weather monitoring for all transport modes
- Pre-departure safety checks for aircraft and sea vessels
- Personnel safety tracking (employees, humanoids, beings)
- Equipment security verification
- Route condition assessment
- Automated delay/cancellation recommendations
- Customer arrival time reliability scoring
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.weather_safety")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class WeatherSeverity(Enum):
    """Weather severity levels."""
    CLEAR = "clear"
    LIGHT = "light"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"
    DANGEROUS = "dangerous"


class TransportMode(Enum):
    """Transport modes for weather checks."""
    AIR = "air"
    SEA = "sea"
    GROUND = "ground"


class SafetyStatus(Enum):
    """Safety status for departure."""
    GO = "go"
    CAUTION = "caution"
    NO_GO = "no_go"
    ABORT = "abort"


class PersonnelType(Enum):
    """Types of personnel requiring safety."""
    EMPLOYEE = "employee"
    HUMANOID = "humanoid"
    BEING = "being"
    CONTRACTOR = "contractor"
    VISITOR = "visitor"


class EquipmentType(Enum):
    """Types of equipment requiring security."""
    AIRCRAFT = "aircraft"
    VESSEL = "vessel"
    VEHICLE = "vehicle"
    CONTAINER = "container"
    CARGO = "cargo"
    INFRASTRUCTURE = "infrastructure"
    COMMUNICATION = "communication"
    NAVIGATION = "navigation"


class WeatherCondition(Enum):
    """Weather conditions affecting transport."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    HAIL = "hail"
    FOG = "fog"
    WIND = "wind"
    THUNDERSTORM = "thunderstorm"
    TORNADO = "tornado"
    HURRICANE = "hurricane"
    TROPICAL_STORM = "tropical_storm"
    DUST_STORM = "dust_storm"
    SAND_STORM = "sand_storm"
    ICING = "icing"
    LIGHTNING = "lighting"
    MICROBURST = "microburst"
    TURBULENCE = "turbulence"
    STORM_SURGE = "storm_rouse"
    HIGH_WAVES = "high_waves"
    RIP_CURRENT = "rip_current"
    TSUNAMI = "tsunami"
    EARTHQUAKE = "earthquake"
    VOLCANIC_ASH = "volcanic_ash"


# =============================================================================
# DATA CLASSES - WEATHER
# =============================================================================

@dataclass
class WeatherConditionData:
    """Current weather condition at a location."""
    condition_id: str
    location: str
    latitude: float
    longitude: float
    timestamp: str
    temperature_f: float
    humidity_percent: float
    wind_speed_mph: float
    wind_direction_degrees: float
    wind_gust_mph: float
    visibility_miles: float
    cloud_cover_percent: float
    precipitation_inches: float
    pressure_inhg: float
    dew_point_f: float
    uv_index: float
    weather_description: str
    weather_severity: WeatherSeverity
    alerts: List[str] = field(default_factory=list)
    forecast_next_6h: str = ""
    forecast_next_12h: str = ""
    forecast_next_24h: str = ""
    notes: str = ""

    @property
    def is_safe_for_air(self) -> bool:
        """Check if weather is safe for air transport."""
        if self.wind_speed_mph > 50:
            return False
        if self.wind_gust_mph > 60:
            return False
        if self.visibility_miles < 1:
            return False
        if self.weather_severity in [WeatherSeverity.EXTREME, WeatherSeverity.DANGEROUS]:
            return False
        if self.weather_description in ["thunderstorm", "tornado", "hurricane", "tropical_storm",
                                         "microburst", "turbulence", "icing", "volcanic_ash"]:
            return False
        return True

    @property
    def is_safe_for_sea(self) -> bool:
        """Check if weather is safe for sea transport."""
        if self.wind_speed_mph > 60:
            return False
        if self.wind_gust_mph > 75:
            return False
        if self.visibility_miles < 0.5:
            return False
        if self.weather_severity in [WeatherSeverity.EXTREME, WeatherSeverity.DANGEROUS]:
            return False
        if self.weather_description in ["hurricane", "tropical_storm", "tsunami", "storm_surge",
                                         "high_waves", "rip_current"]:
            return False
        return True

    @property
    def is_safe_for_ground(self) -> bool:
        """Check if weather is safe for ground transport."""
        if self.wind_speed_mph > 70:
            return False
        if self.visibility_miles < 0.25:
            return False
        if self.weather_severity == WeatherSeverity.DANGEROUS:
            return False
        if self.weather_description in ["tornado", "hurricane", "tropical_storm", "tsunami"]:
            return False
        return True


@dataclass
class WeatherForecast:
    """Weather forecast for route planning."""
    forecast_id: str
    location: str
    latitude: float
    longitude: float
    forecast_time: str
    temperature_high_f: float
    temperature_low_f: float
    wind_speed_mph: float
    wind_gust_mph: float
    precipitation_chance: float
    visibility_miles: float
    weather_description: str
    severity: WeatherSeverity
    alerts: List[str] = field(default_factory=list)


# =============================================================================
# DATA CLASSES - PERSONNEL SAFETY
# =============================================================================

@dataclass
class Personnel:
    """Personnel requiring safety monitoring."""
    personnel_id: str
    name: str
    personnel_type: PersonnelType
    role: str
    location: str
    assigned_equipment: str
    certifications: List[str] = field(default_factory=list)
    safety_training_current: bool = True
    medical_clearance: bool = True
    emergency_contact: str = ""
    emergency_phone: str = ""
    last_safety_check: str = ""
    is_on_duty: bool = False
    is_active: bool = True
    notes: str = ""

    @property
    def is_safe_to_operate(self) -> bool:
        """Check if personnel is safe to operate."""
        return self.safety_training_current and self.medical_clearance and self.is_active


@dataclass
class SafetyCheck:
    """Individual safety check record."""
    check_id: str
    personnel_id: str
    checker_name: str
    check_time: str
    safety_status: SafetyStatus
    certifications_verified: bool
    medical_clearance_verified: bool
    equipment_check_passed: bool
    weather_briefing_completed: bool
    emergency_procedures_reviewed: bool
    notes: str = ""


# =============================================================================
# DATA CLASSES - EQUIPMENT SECURITY
# =============================================================================

@dataclass
class Equipment:
    """Equipment requiring security and safety checks."""
    equipment_id: str
    name: str
    equipment_type: EquipmentType
    location: str
    assigned_personnel: str
    last_inspection: str = ""
    next_inspection_due: str = ""
    maintenance_current: bool = True
    insurance_current: bool = True
    security_system_active: bool = True
    gps_tracking_active: bool = True
    communication_system_functional: bool = True
    navigation_system_functional: bool = True
    is_operational: bool = True
    notes: str = ""

    @property
    def is_safe_to_operate(self) -> bool:
        """Check if equipment is safe to operate."""
        return (self.maintenance_current and self.insurance_current and
                self.security_system_active and self.gps_tracking_active and
                self.communication_system_functional and self.navigation_system_functional and
                self.is_operational)


@dataclass
class EquipmentInspection:
    """Equipment inspection record."""
    inspection_id: str
    equipment_id: str
    inspector_name: str
    inspection_time: str
    safety_status: SafetyStatus
    maintenance_check_passed: bool
    security_check_passed: bool
    communication_check_passed: bool
    navigation_check_passed: bool
    structural_integrity_passed: bool
    notes: str = ""


# =============================================================================
# DATA CLASSES - PRE-DEPARTURE CHECKS
# =============================================================================

@dataclass
class PreDepartureCheck:
    """Pre-departure safety check for transport."""
    check_id: str
    transport_mode: TransportMode
    vehicle_id: str
    vehicle_name: str
    route_id: str
    origin: str
    destination: str
    scheduled_departure: str
    check_time: str
    weather_origin_safe: bool = False
    weather_destination_safe: bool = False
    weather_route_safe: bool = False
    personnel_safe: bool = False
    equipment_safe: bool = False
    cargo_secured: bool = False
    communication_check: bool = False
    navigation_check: bool = False
    fuel_sufficient: bool = False
    emergency_equipment_check: bool = False
    overall_status: SafetyStatus = SafetyStatus.NO_GO
    delay_recommended: bool = False
    delay_duration_minutes: int = 0
    cancellation_recommended: bool = False
    notes: str = ""

    @property
    def all_checks_passed(self) -> bool:
        """Check if all pre-departure checks passed."""
        return (self.weather_origin_safe and self.weather_destination_safe and
                self.weather_route_safe and self.personnel_safe and self.equipment_safe and
                self.cargo_secured and self.communication_check and self.navigation_check and
                self.fuel_sufficient and self.emergency_equipment_check)

    @property
    def arrival_time_reliability(self) -> float:
        """Calculate arrival time reliability score 0-100."""
        if self.overall_status == SafetyStatus.GO:
            return 95.0
        elif self.overall_status == SafetyStatus.CAUTION:
            return 75.0
        elif self.overall_status == SafetyStatus.NO_GO:
            return 25.0
        else:
            return 0.0


@dataclass
class CustomerArrivalEstimate:
    """Customer-facing arrival time estimate."""
    estimate_id: str
    cargo_id: str
    customer_name: str
    origin: str
    destination: str
    original_eta: str
    adjusted_eta: str
    reliability_score: float
    weather_impact: str
    delay_reason: str = ""
    delay_minutes: int = 0
    customer_notified: bool = False
    notes: str = ""

    @property
    def customer_can_relax(self) -> bool:
        """Whether customer can relax based on reliability."""
        return self.reliability_score >= 85


# =============================================================================
# MAIN ENGINE
# =============================================================================

class WeatherSafetyEngine:
    """
    Engine for weather monitoring and safety checks.
    
    Ensures all transport operations are safe for personnel and equipment.
    Provides reliable arrival time estimates for customers.
    """
    
    def __init__(self):
        self.weather_conditions: Dict[str, WeatherConditionData] = {}
        self.weather_forecasts: Dict[str, WeatherForecast] = {}
        self.personnel: Dict[str, Personnel] = {}
        self.equipment: Dict[str, Equipment] = {}
        self.safety_checks: Dict[str, SafetyCheck] = {}
        self.equipment_inspections: Dict[str, EquipmentInspection] = {}
        self.pre_departure_checks: Dict[str, PreDepartureCheck] = {}
        self.customer_estimates: Dict[str, CustomerArrivalEstimate] = {}
        
        self._init_default_personnel()
        self._init_default_equipment()
    
    def _init_default_personnel(self):
        """Initialize default personnel."""
        default_personnel = [
            Personnel(
                personnel_id="per_001",
                name="Captain Sarah Mitchell",
                personnel_type=PersonnelType.EMPLOYEE,
                role="Aircraft Commander",
                location="Austin, TX",
                assigned_equipment="ac_global_8000",
                certifications=["ATPL", "Type Rating - Bombardier Global", "CRM", "Dangerous Goods"],
                safety_training_current=True,
                medical_clearance=True,
                emergency_contact="John Mitchell",
                emergency_phone="+1-512-555-1001",
                is_on_duty=True,
            ),
            Personnel(
                personnel_id="per_002",
                name="First Officer David Chen",
                personnel_type=PersonnelType.EMPLOYEE,
                role="Co-Pilot",
                location="Austin, TX",
                assigned_equipment="ac_global_8000",
                certifications=["ATPL", "Type Rating - Bombardier Global", "CRM"],
                safety_training_current=True,
                medical_clearance=True,
                emergency_contact="Lisa Chen",
                emergency_phone="+1-512-555-1002",
                is_on_duty=True,
            ),
            Personnel(
                personnel_id="per_003",
                name="ARIA-7",
                personnel_type=PersonnelType.HUMANOID,
                role="Autonomous Systems Operator",
                location="Austin, TX",
                assigned_equipment="ac_elroy_chaparral",
                certifications=["Autonomous Operations", "Remote Systems", "Emergency Response"],
                safety_training_current=True,
                medical_clearance=True,
                is_on_duty=True,
                notes="Humanoid robot - autonomous cargo handling specialist"
            ),
            Personnel(
                personnel_id="per_004",
                name="Nexus-Prime",
                personnel_type=PersonnelType.BEING,
                role="Consciousness Logistics Coordinator",
                location="Dallas, TX",
                assigned_equipment="fleet_001",
                certifications=["Multi-modal Operations", "Safety Coordination", "Emergency Command"],
                safety_training_current=True,
                medical_clearance=True,
                is_on_duty=True,
                notes="Being - distributed consciousness for fleet coordination"
            ),
            Personnel(
                personnel_id="per_005",
                name="Captain Maria Rodriguez",
                personnel_type=PersonnelType.EMPLOYEE,
                role="Vessel Master",
                location="Savannah, GA",
                assigned_equipment="sv_post_panamax_8000",
                certifications=["Master Mariner", "GMDSS", "Medical First Aid", "Fire Fighting"],
                safety_training_current=True,
                medical_clearance=True,
                emergency_contact="Carlos Rodriguez",
                emergency_phone="+1-912-555-2001",
                is_on_duty=True,
            ),
            Personnel(
                personnel_id="per_006",
                name="Chief Engineer Tanaka",
                personnel_type=PersonnelType.EMPLOYEE,
                role="Chief Engineer",
                location="Savannah, GA",
                assigned_equipment="sv_post_panamax_8000",
                certifications=["Chief Engineer Certificate", "Marine Engineering", "HVAC", "Electrical"],
                safety_training_current=True,
                medical_clearance=True,
                emergency_contact="Yuki Tanaka",
                emergency_phone="+1-912-555-2002",
                is_on_duty=True,
            ),
        ]
        self.personnel = {p.personnel_id: p for p in default_personnel}
    
    def _init_default_equipment(self):
        """Initialize default equipment."""
        default_equipment = [
            Equipment(
                equipment_id="eq_ac_global_8000",
                name="Bombardier Global 8000 Cargo",
                equipment_type=EquipmentType.AIRCRAFT,
                location="Austin, TX",
                assigned_personnel="per_001",
                last_inspection="2026-08-20",
                next_inspection_due="2026-09-20",
                maintenance_current=True,
                insurance_current=True,
                security_system_active=True,
                gps_tracking_active=True,
                communication_system_functional=True,
                navigation_system_functional=True,
                is_operational=True,
            ),
            Equipment(
                equipment_id="eq_ac_elroy_chaparral",
                name="Elroy Air Chaparral",
                equipment_type=EquipmentType.AIRCRAFT,
                location="Austin, TX",
                assigned_personnel="per_003",
                last_inspection="2026-08-22",
                next_inspection_due="2026-09-22",
                maintenance_current=True,
                insurance_current=True,
                security_system_active=True,
                gps_tracking_active=True,
                communication_system_functional=True,
                navigation_system_functional=True,
                is_operational=True,
            ),
            Equipment(
                equipment_id="eq_sv_post_panamax",
                name="Post-Panamax 8000 TEU",
                equipment_type=EquipmentType.VESSEL,
                location="Savannah, GA",
                assigned_personnel="per_005",
                last_inspection="2026-08-15",
                next_inspection_due="2026-09-15",
                maintenance_current=True,
                insurance_current=True,
                security_system_active=True,
                gps_tracking_active=True,
                communication_system_functional=True,
                navigation_system_functional=True,
                is_operational=True,
            ),
        ]
        self.equipment = {e.equipment_id: e for e in default_equipment}
    
    # -------------------------------------------------------------------------
    # WEATHER MONITORING
    # -------------------------------------------------------------------------
    
    def add_weather_condition(self, weather: WeatherConditionData) -> WeatherConditionData:
        """Add weather condition data."""
        self.weather_conditions[weather.condition_id] = weather
        return weather
    
    def get_weather_at_location(self, location: str) -> Optional[WeatherConditionData]:
        """Get weather at a specific location."""
        for weather in self.weather_conditions.values():
            if weather.location == location:
                return weather
        return None
    
    def get_unsafe_locations(self, transport_mode: TransportMode) -> List[str]:
        """Get locations with unsafe weather for transport mode."""
        unsafe = []
        for weather in self.weather_conditions.values():
            if transport_mode == TransportMode.AIR and not weather.is_safe_for_air:
                unsafe.append(weather.location)
            elif transport_mode == TransportMode.SEA and not weather.is_safe_for_sea:
                unsafe.append(weather.location)
            elif transport_mode == TransportMode.GROUND and not weather.is_safe_for_ground:
                unsafe.append(weather.location)
        return unsafe
    
    def check_route_weather(self, origin: str, destination: str, 
                            transport_mode: TransportMode) -> Dict[str, Any]:
        """Check weather conditions along a route."""
        origin_weather = self.get_weather_at_location(origin)
        dest_weather = self.get_weather_at_location(destination)
        
        result = {
            "origin": origin,
            "destination": destination,
            "transport_mode": transport_mode.value,
            "origin_safe": False,
            "destination_safe": False,
            "route_safe": False,
            "origin_weather": None,
            "destination_weather": None,
            "recommendation": "",
        }
        
        if origin_weather:
            if transport_mode == TransportMode.AIR:
                result["origin_safe"] = origin_weather.is_safe_for_air
            elif transport_mode == TransportMode.SEA:
                result["origin_safe"] = origin_weather.is_safe_for_sea
            else:
                result["origin_safe"] = origin_weather.is_safe_for_ground
            result["origin_weather"] = {
                "temperature_f": origin_weather.temperature_f,
                "wind_speed_mph": origin_weather.wind_speed_mph,
                "visibility_miles": origin_weather.visibility_miles,
                "severity": origin_weather.weather_severity.value,
                "description": origin_weather.weather_description,
            }
        
        if dest_weather:
            if transport_mode == TransportMode.AIR:
                result["destination_safe"] = dest_weather.is_safe_for_air
            elif transport_mode == TransportMode.SEA:
                result["destination_safe"] = dest_weather.is_safe_for_sea
            else:
                result["destination_safe"] = dest_weather.is_safe_for_ground
            result["destination_weather"] = {
                "temperature_f": dest_weather.temperature_f,
                "wind_speed_mph": dest_weather.wind_speed_mph,
                "visibility_miles": dest_weather.visibility_miles,
                "severity": dest_weather.weather_severity.value,
                "description": dest_weather.weather_description,
            }
        
        result["route_safe"] = result["origin_safe"] and result["destination_safe"]
        
        if result["route_safe"]:
            result["recommendation"] = "GO - All weather conditions acceptable"
        elif not result["origin_safe"] and not result["destination_safe"]:
            result["recommendation"] = "NO GO - Unsafe weather at both origin and destination"
        elif not result["origin_safe"]:
            result["recommendation"] = "NO GO - Unsafe weather at origin"
        else:
            result["recommendation"] = "NO GO - Unsafe weather at destination"
        
        return result
    
    # -------------------------------------------------------------------------
    # PERSONNEL SAFETY
    # -------------------------------------------------------------------------
    
    def add_personnel(self, personnel: Personnel) -> Personnel:
        """Add personnel record."""
        self.personnel[personnel.personnel_id] = personnel
        return personnel
    
    def get_personnel_by_type(self, personnel_type: PersonnelType) -> List[Personnel]:
        """Get personnel by type."""
        return [p for p in self.personnel.values() if p.personnel_type == personnel_type]
    
    def get_personnel_on_duty(self) -> List[Personnel]:
        """Get personnel currently on duty."""
        return [p for p in self.personnel.values() if p.is_on_duty]
    
    def verify_personnel_safety(self, personnel_id: str) -> Dict[str, Any]:
        """Verify personnel safety to operate."""
        if personnel_id not in self.personnel:
            return {}
        
        p = self.personnel[personnel_id]
        
        return {
            "personnel_id": personnel_id,
            "name": p.name,
            "type": p.personnel_type.value,
            "role": p.role,
            "is_safe_to_operate": p.is_safe_to_operate,
            "safety_training_current": p.safety_training_current,
            "medical_clearance": p.medical_clearance,
            "certifications": p.certifications,
            "certifications_verified": len(p.certifications) > 0,
        }
    
    def verify_all_personnel(self) -> List[Dict[str, Any]]:
        """Verify safety of all personnel."""
        results = []
        for personnel_id in self.personnel:
            results.append(self.verify_personnel_safety(personnel_id))
        return results
    
    def record_safety_check(self, check: SafetyCheck) -> SafetyCheck:
        """Record a safety check."""
        self.safety_checks[check.check_id] = check
        return check
    
    # -------------------------------------------------------------------------
    # EQUIPMENT SECURITY
    # -------------------------------------------------------------------------
    
    def add_equipment(self, equipment: Equipment) -> Equipment:
        """Add equipment record."""
        self.equipment[equipment.equipment_id] = equipment
        return equipment
    
    def get_equipment_by_type(self, equipment_type: EquipmentType) -> List[Equipment]:
        """Get equipment by type."""
        return [e for e in self.equipment.values() if e.equipment_type == equipment_type]
    
    def get_equipment_by_location(self, location: str) -> List[Equipment]:
        """Get equipment at a location."""
        return [e for e in self.equipment.values() if e.location == location]
    
    def verify_equipment_safety(self, equipment_id: str) -> Dict[str, Any]:
        """Verify equipment safety to operate."""
        if equipment_id not in self.equipment:
            return {}
        
        e = self.equipment[equipment_id]
        
        return {
            "equipment_id": equipment_id,
            "name": e.name,
            "type": e.equipment_type.value,
            "is_safe_to_operate": e.is_safe_to_operate,
            "maintenance_current": e.maintenance_current,
            "insurance_current": e.insurance_current,
            "security_system_active": e.security_system_active,
            "gps_tracking_active": e.gps_tracking_active,
            "communication_system_functional": e.communication_system_functional,
            "navigation_system_functional": e.navigation_system_functional,
        }
    
    def verify_all_equipment(self) -> List[Dict[str, Any]]:
        """Verify safety of all equipment."""
        results = []
        for equipment_id in self.equipment:
            results.append(self.verify_equipment_safety(equipment_id))
        return results
    
    def record_inspection(self, inspection: EquipmentInspection) -> EquipmentInspection:
        """Record an equipment inspection."""
        self.equipment_inspections[inspection.inspection_id] = inspection
        return inspection
    
    # -------------------------------------------------------------------------
    # PRE-DEPARTURE CHECKS
    # -------------------------------------------------------------------------
    
    def perform_pre_departure_check(self, check: PreDepartureCheck) -> PreDepartureCheck:
        """Perform and record a pre-departure check."""
        # Determine overall status based on individual checks
        if check.all_checks_passed:
            check.overall_status = SafetyStatus.GO
        elif (check.weather_origin_safe and check.personnel_safe and 
              check.equipment_safe and check.cargo_secured):
            check.overall_status = SafetyStatus.CAUTION
        elif not check.weather_origin_safe:
            check.overall_status = SafetyStatus.NO_GO
        else:
            check.overall_status = SafetyStatus.NO_GO
        
        self.pre_departure_checks[check.check_id] = check
        return check
    
    def get_check_status(self, check_id: str) -> Dict[str, Any]:
        """Get pre-departure check status."""
        if check_id not in self.pre_departure_checks:
            return {}
        
        check = self.pre_departure_checks[check_id]
        
        return {
            "check_id": check_id,
            "vehicle_name": check.vehicle_name,
            "origin": check.origin,
            "destination": check.destination,
            "overall_status": check.overall_status.value,
            "all_checks_passed": check.all_checks_passed,
            "arrival_time_reliability": check.arrival_time_reliability,
            "delay_recommended": check.delay_recommended,
            "cancellation_recommended": check.cancellation_recommended,
            "weather_origin_safe": check.weather_origin_safe,
            "weather_destination_safe": check.weather_destination_safe,
            "personnel_safe": check.personnel_safe,
            "equipment_safe": check.equipment_safe,
        }
    
    def get_all_active_checks(self) -> List[Dict[str, Any]]:
        """Get all active pre-departure checks."""
        return [self.get_check_status(cid) for cid in self.pre_departure_checks]
    
    # -------------------------------------------------------------------------
    # CUSTOMER ARRIVAL ESTIMATES
    # -------------------------------------------------------------------------
    
    def add_customer_estimate(self, estimate: CustomerArrivalEstimate) -> CustomerArrivalEstimate:
        """Add customer arrival estimate."""
        self.customer_estimates[estimate.estimate_id] = estimate
        return estimate
    
    def update_estimate_for_weather(self, estimate_id: str, weather_delay_minutes: int,
                                     weather_impact: str) -> Optional[Dict[str, Any]]:
        """Update customer estimate based on weather."""
        if estimate_id not in self.customer_estimates:
            return None
        
        estimate = self.customer_estimates[estimate_id]
        estimate.delay_minutes = weather_delay_minutes
        estimate.weather_impact = weather_impact
        estimate.delay_reason = f"Weather delay: {weather_impact}"
        
        # Adjust reliability score based on delay
        if weather_delay_minutes == 0:
            estimate.reliability_score = 95.0
        elif weather_delay_minutes <= 30:
            estimate.reliability_score = 85.0
        elif weather_delay_minutes <= 60:
            estimate.reliability_score = 70.0
        elif weather_delay_minutes <= 120:
            estimate.reliability_score = 50.0
        else:
            estimate.reliability_score = 25.0
        
        # Adjust ETA
        original = datetime.fromisoformat(estimate.original_eta)
        adjusted = original + timedelta(minutes=weather_delay_minutes)
        estimate.adjusted_eta = adjusted.isoformat()
        
        return {
            "estimate_id": estimate_id,
            "customer_name": estimate.customer_name,
            "original_eta": estimate.original_eta,
            "adjusted_eta": estimate.adjusted_eta,
            "delay_minutes": weather_delay_minutes,
            "reliability_score": estimate.reliability_score,
            "customer_can_relax": estimate.customer_can_relax,
        }
    
    def get_reliable_estimates(self) -> List[CustomerArrivalEstimate]:
        """Get estimates where customer can relax."""
        return [e for e in self.customer_estimates.values() if e.customer_can_relax]
    
    def get_delayed_estimates(self) -> List[CustomerArrivalEstimate]:
        """Get delayed estimates."""
        return [e for e in self.customer_estimates.values() if e.delay_minutes > 0]
    
    # -------------------------------------------------------------------------
    # COMPREHENSIVE ANALYSIS
    # -------------------------------------------------------------------------
    
    def get_comprehensive_state(self) -> Dict[str, Any]:
        """Get comprehensive weather and safety state."""
        # Count safe/unsafe personnel
        personnel_safe_count = sum(1 for p in self.personnel.values() if p.is_safe_to_operate)
        personnel_unsafe_count = len(self.personnel) - personnel_safe_count
        
        # Count safe/unsafe equipment
        equipment_safe_count = sum(1 for e in self.equipment.values() if e.is_safe_to_operate)
        equipment_unsafe_count = len(self.equipment) - equipment_safe_count
        
        # Count check statuses
        go_count = sum(1 for c in self.pre_departure_checks.values() 
                       if c.overall_status == SafetyStatus.GO)
        caution_count = sum(1 for c in self.pre_departure_checks.values() 
                           if c.overall_status == SafetyStatus.CAUTION)
        no_go_count = sum(1 for c in self.pre_departure_checks.values() 
                         if c.overall_status == SafetyStatus.NO_GO)
        
        # Count reliable estimates
        reliable_count = len(self.get_reliable_estimates())
        delayed_count = len(self.get_delayed_estimates())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "weather": {
                "locations_monitored": len(self.weather_conditions),
                "unsafe_locations_air": len(self.get_unsafe_locations(TransportMode.AIR)),
                "unsafe_locations_sea": len(self.get_unsafe_locations(TransportMode.SEA)),
                "unsafe_locations_ground": len(self.get_unsafe_locations(TransportMode.GROUND)),
            },
            "personnel": {
                "total": len(self.personnel),
                "safe": personnel_safe_count,
                "unsafe": personnel_unsafe_count,
                "on_duty": len(self.get_personnel_on_duty()),
                "by_type": {
                    pt.value: len(self.get_personnel_by_type(pt))
                    for pt in PersonnelType
                    if self.get_personnel_by_type(pt)
                },
            },
            "equipment": {
                "total": len(self.equipment),
                "safe": equipment_safe_count,
                "unsafe": equipment_unsafe_count,
                "by_type": {
                    et.value: len(self.get_equipment_by_type(et))
                    for et in EquipmentType
                    if self.get_equipment_by_type(et)
                },
            },
            "pre_departure_checks": {
                "total": len(self.pre_departure_checks),
                "go": go_count,
                "caution": caution_count,
                "no_go": no_go_count,
            },
            "customer_estimates": {
                "total": len(self.customer_estimates),
                "reliable": reliable_count,
                "delayed": delayed_count,
                "customer_can_rely": reliable_count,
            },
            "summary": {
                "personnel_safe": personnel_safe_count,
                "personnel_total": len(self.personnel),
                "equipment_safe": equipment_safe_count,
                "equipment_total": len(self.equipment),
                "checks_go": go_count,
                "checks_total": len(self.pre_departure_checks),
                "estimates_reliable": reliable_count,
                "estimates_total": len(self.customer_estimates),
            }
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

weather_safety_engine = WeatherSafetyEngine()