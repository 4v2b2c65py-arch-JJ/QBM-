#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Emergency Response & Contingency

Critical emergency response and contingency planning module.
Handles disruptions, incidents, and provides alternative plans
when primary transport operations fail.

Features:
- Emergency response plans (weather, mechanical, medical, security)
- Incident reporting and tracking
- Contingency routing (alternative paths when primary fails)
- Emergency contact management
- Evacuation procedures
- Equipment failure contingencies
- Supply chain disruption responses
- Communication protocols during emergencies
- Recovery procedures and business continuity
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

LOG = __import__("logging").getLogger("qb_protocol.being.chip.emergency_response")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class EmergencyType(Enum):
    """Types of emergencies."""
    WEATHER = "weather"
    MECHANICAL_FAILURE = "mechanical_failure"
    MEDICAL = "medical"
    SECURITY_BREACH = "security_breach"
    FIRE = "fire"
    HAZMAT = "hazmat"
    NATURAL_DISASTER = "natural_disaster"
    POWER_OUTAGE = "power_outage"
    COMMUNICATION_FAILURE = "communication_failure"
    CYBER_ATTACK = "cyber_attack"
    TERRORISM = "terrorism"
    PIRACY = "piracy"
    STRUCTURAL_FAILURE = "structural_failure"
    ENVIRONMENTAL = "environmental"
    SUPPLY_CHAIN = "supply_chain"
    STORM = "storm"
    FLOOD = "flood"
    EARTHQUAKE = "earthquake"
    PANDEMIC = "pandemic"


class EmergencySeverity(Enum):
    """Emergency severity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class IncidentStatus(Enum):
    """Incident status."""
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    RESPONDING = "responding"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class ContingencyType(Enum):
    """Types of contingency plans."""
    ROUTE_DIVERSION = "route_diversion"
    MODE_SWITCH = "mode_switch"
    EQUIPMENT_REPLACEMENT = "equipment_replacement"
    PERSONNEL_REPLACEMENT = "personnel_replacement"
    SUPPLY_REDUNDANCY = "supply_redundancy"
    COMMUNICATION_BACKUP = "communication_backup"
    POWER_BACKUP = "power_backup"
    FACILITY_BACKUP = "facility_backup"
    VENDOR_BACKUP = "vendor_backup"
    CUSTOMER_NOTIFICATION = "customer_notification"


class ResponseActionType(Enum):
    """Types of response actions."""
    EVACUATE = "evacuate"
    SHELTER_IN_PLACE = "shelter_in_place"
    DIVERT = "divert"
    DELAY = "delay"
    CANCEL = "cancel"
    SWITCH_MODE = "switch_mode"
    REQUEST_ASSISTANCE = "request_assistance"
    NOTIFY_AUTHORITIES = "notify_authorities"
    NOTIFY_CUSTOMERS = "notify_customities"
    ACTIVATE_BACKUP = "activate_backup"
    ISOLATE = "isolate"
    EXTINGUISH = "extinguish"
    SEAL_OFF = "seal_off"
    SHUTDOWN = "shutdown"


# =============================================================================
# DATA CLASSES - EMERGENCY PLANS
# =============================================================================

@dataclass
class EmergencyContact:
    """Emergency contact information."""
    contact_id: str
    name: str
    role: str
    organization: str
    phone_primary: str
    phone_secondary: str
    email: str
    is_available_24_7: bool = True
    response_time_minutes: int = 30
    specializations: List[str] = field(default_factory=list)
    location: str = ""
    notes: str = ""


@dataclass
class EmergencyResponsePlan:
    """Emergency response plan for a specific scenario."""
    plan_id: str
    name: str
    emergency_type: EmergencyType
    severity_trigger: EmergencySeverity
    description: str
    immediate_actions: List[ResponseActionType] = field(default_factory=list)
    evacuation_required: bool = False
    shelter_in_place: bool = False
    estimated_response_time_minutes: int = 30
    required_personnel: int = 2
    required_equipment: List[str] = field(default_factory=list)
    external_agencies_to_notify: List[str] = field(default_factory=list)
    customer_notification_template: str = ""
    recovery_steps: List[str] = field(default_factory=list)
    alternate_routes: List[str] = field(default_factory=list)
    alternate_modes: List[str] = field(default_factory=list)
    backup_facilities: List[str] = field(default_factory=list)
    backup_vendors: List[str] = field(default_factory=list)
    is_active: bool = True
    last_drill_date: str = ""
    next_drill_due: str = ""
    notes: str = ""


@dataclass
class Incident:
    """Incident report."""
    incident_id: str
    title: str
    description: str
    emergency_type: EmergencyType
    severity: EmergencySeverity
    status: IncidentStatus
    reported_by: str
    reported_time: str
    location: str
    affected_assets: List[str] = field(default_factory=list)
    affected_personnel: List[str] = field(default_factory=list)
    affected_customers: List[str] = field(default_factory=list)
    immediate_actions_taken: List[str] = field(default_factory=list)
    response_plan_activated: str = ""
    response_team: List[str] = field(default_factory=list)
    resolution_time: str = ""
    root_cause: str = ""
    lessons_learned: str = ""
    financial_impact: float = 0
    notes: str = ""


@dataclass
class ContingencyPlan:
    """Contingency plan for disruptions."""
    plan_id: str
    name: str
    contingency_type: ContingencyType
    trigger_condition: str
    description: str
    primary_plan: str
    alternate_plan: str
    estimated_activation_time_minutes: int = 60
    estimated_recovery_time_hours: float = 24
    additional_cost_estimate: float = 0
    customer_impact: str = ""
    alternate_routes: List[str] = field(default_factory=list)
    alternate_modes: List[str] = field(default_factory=list)
    alternate_facilities: List[str] = field(default_factory=list)
    alternate_vendors: List[str] = field(default_factory=list)
    alternate_personnel: List[str] = field(default_factory=list)
    is_tested: bool = False
    last_test_date: str = ""
    next_test_due: str = ""
    success_rate: float = 0
    is_active: bool = True
    notes: str = ""


@dataclass
class EvacuationProcedure:
    """Evacuation procedure."""
    procedure_id: str
    name: str
    facility_or_vehicle: str
    emergency_types: List[EmergencyType] = field(default_factory=list)
    evacuation_routes: List[str] = field(default_factory=list)
    assembly_points: List[str] = field(default_factory=list)
    head_count_required: bool = True
    estimated_evacuation_time_minutes: int = 15
    special_equipment_needed: List[str] = field(default_factory=list)
    personnel_accountability: bool = True
    shutdown_required: bool = False
    isolation_points: List[str] = field(default_factory=list)
    notes: str = ""


# =============================================================================
# MAIN ENGINE
# =============================================================================

class EmergencyResponseEngine:
    """
    Engine for emergency response and contingency planning.
    
    Provides comprehensive emergency management including:
    - Emergency response plans for all scenarios
    - Incident reporting and tracking
    - Contingency planning for disruptions
    - Alternative routing and mode switching
    """
    
    def __init__(self):
        self.emergency_contacts: Dict[str, EmergencyContact] = {}
        self.response_plans: Dict[str, EmergencyResponsePlan] = {}
        self.incidents: Dict[str, Incident] = {}
        self.contingency_plans: Dict[str, ContingencyPlan] = {}
        self.evacuation_procedures: Dict[str, EvacuationProcedure] = {}
        
        self._init_default_contacts()
        self._init_default_response_plans()
        self._init_default_contingency_plans()
        self._init_default_evacuation_procedures()
    
    def _init_default_contacts(self):
        """Initialize default emergency contacts."""
        default_contacts = [
            EmergencyContact(
                contact_id="ec_001",
                name="Emergency Dispatch Center",
                role="24/7 Emergency Coordinator",
                organization="Omega Logistics",
                phone_primary="+1-800-555-0911",
                phone_secondary="+1-800-555-0912",
                email="emergency@omegalogistics.com",
                is_available_24_7=True,
                response_time_minutes=5,
                specializations=["All Emergencies", "Coordination", "Dispatch"],
                location="Austin, TX",
            ),
            EmergencyContact(
                contact_id="ec_002",
                name="Captain Sarah Mitchell",
                role="Aircraft Commander - Emergency Lead",
                organization="Omega Continental Cargo",
                phone_primary="+1-512-555-1001",
                phone_secondary="+1-512-555-1099",
                email="s.mitchell@omegalogistics.com",
                is_available_24_7=True,
                response_time_minutes=15,
                specializations=["Aircraft Emergency", "Weather", "Mechanical"],
                location="Austin, TX",
            ),
            EmergencyContact(
                contact_id="ec_003",
                name="Captain Maria Rodriguez",
                role="Vessel Master - Emergency Lead",
                organization="Omega Maritime",
                phone_primary="+1-912-555-2001",
                phone_secondary="+1-912-555-2099",
                email="m.rodriguez@omegalogistics.com",
                is_available_24_7=True,
                response_time_minutes=20,
                specializations=["Maritime Emergency", "Weather", "Piracy", "Medical"],
                location="Savannah, GA",
            ),
            EmergencyContact(
                contact_id="ec_004",
                name="ARIA-7",
                role="Autonomous Systems Emergency Operator",
                organization="Omega Logistics",
                phone_primary="+1-512-555-3001",
                phone_secondary="",
                email="aria7@omegalogistics.com",
                is_available_24_7=True,
                response_time_minutes=2,
                specializations=["Autonomous Systems", "Drone Operations", "Remote Operations"],
                location="Austin, TX",
            ),
            EmergencyContact(
                contact_id="ec_005",
                name="Nexus-Prime",
                role="Consciousness Emergency Coordinator",
                organization="Omega Logistics",
                phone_primary="+1-214-555-4001",
                phone_secondary="",
                email="nexus@omegalogistics.com",
                is_available_24_7=True,
                response_time_minutes=1,
                specializations=["Multi-modal Coordination", "Fleet Management", "Strategic Response"],
                location="Dallas, TX",
            ),
            EmergencyContact(
                contact_id="ec_006",
                name="Local Emergency Services",
                role="Fire/Police/EMS",
                organization="Local Authorities",
                phone_primary="911",
                phone_secondary="311",
                email="",
                is_available_24_7=True,
                response_time_minutes=10,
                specializations=["Fire", "Medical", "Police", "HAZMAT"],
                location="All Locations",
            ),
            EmergencyContact(
                contact_id="ec_007",
                name="US Coast Guard",
                role="Maritime Emergency Response",
                organization="US Coast Guard",
                phone_primary="+1-800-555-0300",
                phone_secondary="",
                email="",
                is_available_24_7=True,
                response_time_minutes=45,
                specializations=["Maritime Search & Rescue", "Oil Spill", "Piracy"],
                location="All Coastal Waters",
            ),
            EmergencyContact(
                contact_id="ec_008",
                name="FAA Emergency",
                role="Aviation Emergency",
                organization="Federal Aviation Administration",
                phone_primary="+1-202-267-3333",
                phone_secondary="",
                email="",
                is_available_24_7=True,
                response_time_minutes=15,
                specializations=["Aircraft Emergency", "Airspace", "Crash Response"],
                location="National",
            ),
        ]
        self.emergency_contacts = {c.contact_id: c for c in default_contacts}
    
    def _init_default_response_plans(self):
        """Initialize default emergency response plans."""
        default_plans = [
            EmergencyResponsePlan(
                plan_id="erp_weather_severe",
                name="Severe Weather Response",
                emergency_type=EmergencyType.WEATHER,
                severity_trigger=EmergencySeverity.HIGH,
                description="Response to severe weather conditions affecting transport operations",
                immediate_actions=[
                    ResponseActionType.DELAY,
                    ResponseActionType.DIVERT,
                    ResponseActionType.NOTIFY_CUSTOMERS,
                ],
                evacuation_required=False,
                shelter_in_place=True,
                estimated_response_time_minutes=30,
                required_personnel=3,
                external_agencies_to_notify=["National Weather Service", "Local Authorities"],
                customer_notification_template="Due to severe weather, your shipment may be delayed. We will update you within 2 hours.",
                recovery_steps=[
                    "Monitor weather conditions",
                    "Assess route safety",
                    "Resume operations when safe",
                    "Expedite delayed shipments",
                ],
                alternate_routes=["Ground transport instead of air", "Alternate ports"],
                alternate_modes=["ground", "sea"],
                backup_facilities=["Dallas Backup Hub", "Houston Backup Hub"],
            ),
            EmergencyResponsePlan(
                plan_id="erp_mechanical_aircraft",
                name="Aircraft Mechanical Failure",
                emergency_type=EmergencyType.MECHANICAL_FAILURE,
                severity_trigger=EmergencySeverity.HIGH,
                description="Response to aircraft mechanical failure",
                immediate_actions=[
                    ResponseActionType.DIVERT,
                    ResponseActionType.REQUEST_ASSISTANCE,
                    ResponseActionType.NOTIFY_CUSTOMERS,
                ],
                evacuation_required=False,
                estimated_response_time_minutes=20,
                required_personnel=4,
                external_agencies_to_notify=["FAA Emergency", "Airport Emergency Services"],
                customer_notification_template="Due to aircraft maintenance requirements, your shipment is being transferred to alternate transport.",
                recovery_steps=[
                    "Diagnose mechanical issue",
                    "Dispatch repair team if possible",
                    "Transfer cargo to backup aircraft",
                    "Notify customer of new ETA",
                ],
                alternate_modes=["air_alternate", "ground", "sea"],
                backup_facilities=["Nearest suitable airport"],
            ),
            EmergencyResponsePlan(
                plan_id="erp_medical",
                name="Medical Emergency",
                emergency_type=EmergencyType.MEDICAL,
                severity_trigger=EmergencySeverity.MODERATE,
                description="Response to medical emergency involving personnel",
                immediate_actions=[
                    ResponseActionType.REQUEST_ASSISTANCE,
                    ResponseActionType.NOTIFY_AUTHORITIES,
                ],
                evacuation_required=True,
                estimated_response_time_minutes=10,
                required_personnel=2,
                external_agencies_to_notify=["911", "Local Hospital", "Emergency Contact"],
                recovery_steps=[
                    "Provide first aid",
                    "Contact emergency services",
                    "Evacuate if necessary",
                    "Notify emergency contact",
                    "Document incident",
                ],
            ),
            EmergencyResponsePlan(
                plan_id="erp_hazmat",
                name="Hazardous Materials Incident",
                emergency_type=EmergencyType.HAZMAT,
                severity_trigger=EmergencySeverity.HIGH,
                description="Response to hazardous materials spill or incident",
                immediate_actions=[
                    ResponseActionType.ISOLATE,
                    ResponseActionType.EVACUATE,
                    ResponseActionType.NOTIFY_AUTHORITIES,
                    ResponseActionType.SEAL_OFF,
                ],
                evacuation_required=True,
                estimated_response_time_minutes=15,
                required_personnel=5,
                external_agencies_to_notify=["HAZMAT Team", "EPA", "Local Fire Department"],
                recovery_steps=[
                    "Isolate the area",
                    "Evacuate personnel",
                    "Contact HAZMAT team",
                    "Contain the spill",
                    "Notify affected customers",
                    "Document and report",
                ],
            ),
            EmergencyResponsePlan(
                plan_id="erp_piracy",
                name="Maritime Piracy Response",
                emergency_type=EmergencyType.PIRACY,
                severity_trigger=EmergencySeverity.CRITICAL,
                description="Response to piracy or armed robbery at sea",
                immediate_actions=[
                    ResponseActionType.SHELTER_IN_PLACE,
                    ResponseActionType.REQUEST_ASSISTANCE,
                    ResponseActionType.NOTIFY_AUTHORITIES,
                ],
                evacuation_required=False,
                shelter_in_place=True,
                estimated_response_time_minutes=30,
                required_personnel=20,
                external_agencies_to_notify=["US Coast Guard", "NATO Maritime", "UKMTO"],
                recovery_steps=[
                    "Activate ship security alert",
                    "Proceed to safe room (citadel)",
                    "Contact authorities",
                    "Follow instructions",
                    "Document incident",
                ],
            ),
            EmergencyResponsePlan(
                plan_id="erp_cyber",
                name="Cyber Attack Response",
                emergency_type=EmergencyType.CYBER_ATTACK,
                severity_trigger=EmergencySeverity.HIGH,
                description="Response to cyber attack on systems",
                immediate_actions=[
                    ResponseActionType.SHUTDOWN,
                    ResponseActionType.ACTIVATE_BACKUP,
                    ResponseActionType.NOTIFY_AUTHORITIES,
                ],
                estimated_response_time_minutes=10,
                required_personnel=3,
                external_agencies_to_notify=["FBI Cyber", "CISA", "Cyber Insurance"],
                recovery_steps=[
                    "Isolate affected systems",
                    "Activate backup systems",
                    "Identify attack vector",
                    "Restore from clean backup",
                    "Monitor for recurrence",
                ],
            ),
            EmergencyResponsePlan(
                plan_id="erp_power_outage",
                name="Power Outage Response",
                emergency_type=EmergencyType.POWER_OUTAGE,
                severity_trigger=EmergencySeverity.MODERATE,
                description="Response to power outage affecting operations",
                immediate_actions=[
                    ResponseActionType.ACTIVATE_BACKUP,
                    ResponseActionType.NOTIFY_CUSTOMERS,
                ],
                estimated_response_time_minutes=5,
                required_personnel=2,
                recovery_steps=[
                    "Activate backup generators",
                    "Assess power restoration time",
                    "Prioritize critical operations",
                    "Notify customers if delay expected",
                ],
                backup_facilities=["Generator-powered facilities"],
            ),
            EmergencyResponsePlan(
                plan_id="erp_natural_disaster",
                name="Natural Disaster Response",
                emergency_type=EmergencyType.NATURAL_DISASTER,
                severity_trigger=EmergencySeverity.CRITICAL,
                description="Response to natural disaster (hurricane, flood, earthquake)",
                immediate_actions=[
                    ResponseActionType.EVACUATE,
                    ResponseActionType.SHUTDOWN,
                    ResponseActionType.NOTIFY_AUTHORITIES,
                    ResponseActionType.NOTIFY_CUSTOMERS,
                ],
                evacuation_required=True,
                estimated_response_time_minutes=60,
                required_personnel=10,
                external_agencies_to_notify=["FEMA", "Local Emergency Management", "National Guard"],
                customer_notification_template="Due to natural disaster, operations are suspended. We will resume as soon as safe.",
                recovery_steps=[
                    "Ensure personnel safety",
                    "Assess facility damage",
                    "Activate alternate facilities",
                    "Resume operations gradually",
                    "Support affected employees",
                ],
                alternate_routes=["Interstate bypass routes", "Alternate ports"],
                alternate_modes=["ground", "air_charter"],
                backup_facilities=["Dallas Command Center", "Remote Operations"],
            ),
        ]
        self.response_plans = {p.plan_id: p for p in default_plans}
    
    def _init_default_contingency_plans(self):
        """Initialize default contingency plans."""
        default_plans = [
            ContingencyPlan(
                plan_id="con_route_primary_fail",
                name="Primary Route Failure",
                contingency_type=ContingencyType.ROUTE_DIVERSION,
                trigger_condition="Primary route unavailable due to weather, accident, or closure",
                description="Divert to alternate routes when primary route fails",
                primary_plan="Use primary optimized route",
                alternate_plan="Switch to pre-planned alternate route",
                estimated_activation_time_minutes=15,
                estimated_recovery_time_hours=2,
                additional_cost_estimate=500,
                customer_impact="Potential 1-3 hour delay",
                alternate_routes=["Interstate bypass", "Secondary highways", "Alternate ports"],
                alternate_modes=["ground"],
            ),
            ContingencyPlan(
                plan_id="con_aircraft_unavailable",
                name="Aircraft Unavailable",
                contingency_type=ContingencyType.EQUIPMENT_REPLACEMENT,
                trigger_condition="Primary aircraft unavailable due to maintenance or damage",
                description="Switch to backup aircraft or alternate transport mode",
                primary_plan="Use primary aircraft",
                alternate_plan="Switch to backup aircraft or charter",
                estimated_activation_time_minutes=60,
                estimated_recovery_time_hours=4,
                additional_cost_estimate=15000,
                customer_impact="Potential 2-6 hour delay",
                alternate_modes=["air_charter", "ground_express", "sea_express"],
            ),
            ContingencyPlan(
                plan_id="con_vessel_unavailable",
                name="Vessel Unavailable",
                contingency_type=ContingencyType.EQUIPMENT_REPLACEMENT,
                trigger_condition="Primary vessel unavailable due to maintenance or weather",
                description="Switch to backup vessel or alternate transport mode",
                primary_plan="Use primary vessel",
                alternate_plan="Switch to backup vessel or air freight for critical cargo",
                estimated_activation_time_minutes=120,
                estimated_recovery_time_hours=24,
                additional_cost_estimate=50000,
                customer_impact="Potential 1-3 day delay",
                alternate_modes=["vessel_charter", "air_critical", "rail_alternate"],
            ),
            ContingencyPlan(
                plan_id="con_port_closure",
                name="Port Closure",
                contingency_type=ContingencyType.FACILITY_BACKUP,
                trigger_condition="Primary port closed due to weather, strike, or congestion",
                description="Reroute to alternate port",
                primary_plan="Use primary port",
                alternate_plan="Switch to alternate port within 200 miles",
                estimated_activation_time_minutes=30,
                estimated_recovery_time_hours=12,
                additional_cost_estimate=10000,
                customer_impact="Potential 6-24 hour delay",
                alternate_facilities=["Houston Port", "New Orleans Port", "Miami Port"],
            ),
            ContingencyPlan(
                plan_id="con_personnel_shortage",
                name="Personnel Shortage",
                contingency_type=ContingencyType.PERSONNEL_REPLACEMENT,
                trigger_condition="Critical personnel unavailable due to illness or emergency",
                description="Activate backup personnel from pool",
                primary_plan="Use primary crew",
                alternate_plan="Activate backup crew from on-call pool",
                estimated_activation_time_minutes=60,
                estimated_recovery_time_hours=2,
                additional_cost_estimate=2000,
                customer_impact="Minimal if backup available within 1 hour",
                alternate_personnel=["Backup pilots", "Relief crew", "Contract personnel"],
            ),
            ContingencyPlan(
                plan_id="con_fuel_shortage",
                name="Fuel Supply Disruption",
                contingency_type=ContingencyType.SUPPLY_REDUNDANCY,
                trigger_condition="Primary fuel supplier unable to deliver",
                description="Switch to backup fuel supplier",
                primary_plan="Use primary fuel supplier",
                alternate_plan="Activate backup fuel contract",
                estimated_activation_time_minutes=30,
                estimated_recovery_time_hours=4,
                additional_cost_estimate=5000,
                customer_impact="Potential 2-4 hour delay for refueling",
                alternate_vendors=["Backup fuel supplier A", "Backup fuel supplier B"],
            ),
            ContingencyPlan(
                plan_id="con_communication_failure",
                name="Communication System Failure",
                contingency_type=ContingencyType.COMMUNICATION_BACKUP,
                trigger_condition="Primary communication system fails",
                description="Switch to backup communication systems",
                primary_plan="Use primary communication system",
                alternate_plan="Activate satellite phone and backup radio",
                estimated_activation_time_minutes=5,
                estimated_recovery_time_hours=1,
                additional_cost_estimate=500,
                customer_impact="Minimal - backup systems activate automatically",
            ),
            ContingencyPlan(
                plan_id="con_customer_urgent",
                name="Customer Urgent Request",
                contingency_type=ContingencyType.MODE_SWITCH,
                trigger_condition="Customer requests expedited delivery",
                description="Upgrade transport mode to meet urgent deadline",
                primary_plan="Use planned transport mode",
                alternate_plan="Upgrade to faster mode (ground to air, sea to air)",
                estimated_activation_time_minutes=30,
                estimated_recovery_time_hours=0,
                additional_cost_estimate=25000,
                customer_impact="Positive - faster delivery",
                alternate_modes=["air_charter", "express_ground"],
            ),
        ]
        self.contingency_plans = {p.plan_id: p for p in default_plans}
    
    def _init_default_evacuation_procedures(self):
        """Initialize default evacuation procedures."""
        default_procedures = [
            EvacuationProcedure(
                procedure_id="evac_aircraft",
                name="Aircraft Emergency Evacuation",
                facility_or_vehicle="Aircraft on ground",
                emergency_types=[EmergencyType.FIRE, EmergencyType.HAZMAT, EmergencyType.STRUCTURAL_FAILURE],
                evacuation_routes=["Emergency slides", "Crew doors", "Overwing exits"],
                assembly_points=["500ft upwind of aircraft", "Designated safe area"],
                head_count_required=True,
                estimated_evacuation_time_minutes=3,
                special_equipment_needed=["Emergency slides", "Fire extinguishers", "First aid kits"],
                personnel_accountability=True,
                shutdown_required=True,
                isolation_points=["Fuel shutoff", "Electrical master", "APU shutdown"],
            ),
            EvacuationProcedure(
                procedure_id="evac_vessel",
                name="Vessel Emergency Evacuation",
                facility_or_vehicle="Sea vessel",
                emergency_types=[EmergencyType.FIRE, EmergencyType.FLOOD, EmergencyType.PIRACY, EmergencyType.STRUCTURAL_FAILURE],
                evacuation_routes=["Lifeboat stations", "Liferaft stations", "Muster stations"],
                assembly_points=["Muster station A", "Muster station B", "Lifeboat deck"],
                head_count_required=True,
                estimated_evacuation_time_minutes=15,
                special_equipment_needed=["Life jackets", "Lifeboats", "Liferafts", "EPIRB"],
                personnel_accountability=True,
                shutdown_required=False,
                isolation_points=["Watertight doors", "Fire dampers", "Engine room shutdown"],
            ),
            EvacuationProcedure(
                procedure_id="evac_warehouse",
                name="Warehouse Emergency Evacuation",
                facility_or_vehicle="Warehouse facility",
                emergency_types=[EmergencyType.FIRE, EmergencyType.NATURAL_DISASTER, EmergencyType.HAZMAT, EmergencyType.STRUCTURAL_FAILURE],
                evacuation_routes=["Main entrance", "Emergency exits", "Loading dock exits"],
                assembly_points=["Parking lot A", "Across street", "Designated rally point"],
                head_count_required=True,
                estimated_evacuation_time_minutes=5,
                special_equipment_needed=["Fire extinguishers", "First aid kits", "AED"],
                personnel_accountability=True,
                shutdown_required=False,
                isolation_points=["Gas shutoff", "Electrical panel", "HVAC shutdown"],
            ),
        ]
        self.evacuation_procedures = {p.procedure_id: p for p in default_procedures}
    
    # -------------------------------------------------------------------------
    # EMERGENCY CONTACTS
    # -------------------------------------------------------------------------
    
    def add_emergency_contact(self, contact: EmergencyContact) -> EmergencyContact:
        """Add an emergency contact."""
        self.emergency_contacts[contact.contact_id] = contact
        return contact
    
    def get_contacts_by_specialization(self, specialization: str) -> List[EmergencyContact]:
        """Get contacts by specialization."""
        return [c for c in self.emergency_contacts.values() 
                if specialization.lower() in [s.lower() for s in c.specializations]]
    
    def get_24_7_contacts(self) -> List[EmergencyContact]:
        """Get contacts available 24/7."""
        return [c for c in self.emergency_contacts.values() if c.is_available_24_7]
    
    # -------------------------------------------------------------------------
    # RESPONSE PLANS
    # -------------------------------------------------------------------------
    
    def add_response_plan(self, plan: EmergencyResponsePlan) -> EmergencyResponsePlan:
        """Add an emergency response plan."""
        self.response_plans[plan.plan_id] = plan
        return plan
    
    def get_plan_by_emergency_type(self, emergency_type: EmergencyType) -> List[EmergencyResponsePlan]:
        """Get response plans by emergency type."""
        return [p for p in self.response_plans.values() if p.emergency_type == emergency_type]
    
    def get_active_plans(self) -> List[EmergencyResponsePlan]:
        """Get active response plans."""
        return [p for p in self.response_plans.values() if p.is_active]
    
    def activate_plan(self, plan_id: str) -> Dict[str, Any]:
        """Activate an emergency response plan."""
        if plan_id not in self.response_plans:
            return {}
        
        plan = self.response_plans[plan_id]
        plan.is_active = True
        
        return {
            "plan_id": plan_id,
            "name": plan.name,
            "emergency_type": plan.emergency_type.value,
            "immediate_actions": [a.value for a in plan.immediate_actions],
            "evacuation_required": plan.evacuation_required,
            "estimated_response_time_minutes": plan.estimated_response_time_minutes,
            "external_agencies": plan.external_agencies_to_notify,
        }
    
    # -------------------------------------------------------------------------
    # INCIDENT MANAGEMENT
    # -------------------------------------------------------------------------
    
    def report_incident(self, incident: Incident) -> Incident:
        """Report a new incident."""
        self.incidents[incident.incident_id] = incident
        return incident
    
    def update_incident_status(self, incident_id: str, new_status: IncidentStatus,
                                notes: str = "") -> Dict[str, Any]:
        """Update incident status."""
        if incident_id not in self.incidents:
            return {}
        
        incident = self.incidents[incident_id]
        incident.status = new_status
        if notes:
            incident.notes += f"\n{datetime.now().isoformat()}: {notes}"
        
        if new_status == IncidentStatus.RESOLVED:
            incident.resolution_time = datetime.now().isoformat()
        
        return {
            "incident_id": incident_id,
            "status": new_status.value,
            "incident_title": incident.title,
        }
    
    def get_incidents_by_status(self, status: IncidentStatus) -> List[Incident]:
        """Get incidents by status."""
        return [i for i in self.incidents.values() if i.status == status]
    
    def get_open_incidents(self) -> List[Incident]:
        """Get open incidents."""
        return [i for i in self.incidents.values() 
                if i.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]]
    
    def get_incidents_by_type(self, emergency_type: EmergencyType) -> List[Incident]:
        """Get incidents by emergency type."""
        return [i for i in self.incidents.values() if i.emergency_type == emergency_type]
    
    # -------------------------------------------------------------------------
    # CONTINGENCY PLANS
    # -------------------------------------------------------------------------
    
    def add_contingency_plan(self, plan: ContingencyPlan) -> ContingencyPlan:
        """Add a contingency plan."""
        self.contingency_plans[plan.plan_id] = plan
        return plan
    
    def get_plan_by_type(self, contingency_type: ContingencyType) -> List[ContingencyPlan]:
        """Get contingency plans by type."""
        return [p for p in self.contingency_plans.values() if p.contingency_type == contingency_type]
    
    def get_active_contingency_plans(self) -> List[ContingencyPlan]:
        """Get active contingency plans."""
        return [p for p in self.contingency_plans.values() if p.is_active]
    
    def activate_contingency(self, plan_id: str) -> Dict[str, Any]:
        """Activate a contingency plan."""
        if plan_id not in self.contingency_plans:
            return {}
        
        plan = self.contingency_plans[plan_id]
        
        return {
            "plan_id": plan_id,
            "name": plan.name,
            "contingency_type": plan.contingency_type.value,
            "alternate_plan": plan.alternate_plan,
            "estimated_activation_time_minutes": plan.estimated_activation_time_minutes,
            "estimated_recovery_time_hours": plan.estimated_recovery_time_hours,
            "additional_cost_estimate": plan.additional_cost_estimate,
            "alternate_routes": plan.alternate_routes,
            "alternate_modes": plan.alternate_modes,
            "alternate_facilities": plan.alternate_facilities,
        }
    
    # -------------------------------------------------------------------------
    # EVACUATION PROCEDURES
    # -------------------------------------------------------------------------
    
    def add_evacuation_procedure(self, procedure: EvacuationProcedure) -> EvacuationProcedure:
        """Add an evacuation procedure."""
        self.evacuation_procedures[procedure.procedure_id] = procedure
        return procedure
    
    def get_procedures_by_emergency_type(self, emergency_type: EmergencyType) -> List[EvacuationProcedure]:
        """Get evacuation procedures by emergency type."""
        return [p for p in self.evacuation_procedures.values() 
                if emergency_type in p.emergency_types]
    
    def get_procedures_by_facility(self, facility: str) -> List[EvacuationProcedure]:
        """Get evacuation procedures by facility."""
        return [p for p in self.evacuation_procedures.values() 
                if facility.lower() in p.facility_or_vehicle.lower()]
    
    # -------------------------------------------------------------------------
    # COMPREHENSIVE ANALYSIS
    # -------------------------------------------------------------------------
    
    def get_comprehensive_state(self) -> Dict[str, Any]:
        """Get comprehensive emergency response state."""
        open_incidents = self.get_open_incidents()
        active_plans = self.get_active_plans()
        active_contingency = self.get_active_contingency_plans()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "emergency_contacts": {
                "total": len(self.emergency_contacts),
                "available_24_7": len(self.get_24_7_contacts()),
            },
            "response_plans": {
                "total": len(self.response_plans),
                "active": len(active_plans),
                "by_type": {
                    et.value: len(self.get_plan_by_emergency_type(et))
                    for et in EmergencyType
                    if self.get_plan_by_emergency_type(et)
                },
            },
            "incidents": {
                "total": len(self.incidents),
                "open": len(open_incidents),
                "by_status": {
                    s.value: len(self.get_incidents_by_status(s))
                    for s in IncidentStatus
                    if self.get_incidents_by_status(s)
                },
            },
            "contingency_plans": {
                "total": len(self.contingency_plans),
                "active": len(active_contingency),
                "by_type": {
                    ct.value: len(self.get_plan_by_type(ct))
                    for ct in ContingencyType
                    if self.get_plan_by_type(ct)
                },
            },
            "evacuation_procedures": {
                "total": len(self.evacuation_procedures),
            },
            "summary": {
                "total_contacts": len(self.emergency_contacts),
                "total_response_plans": len(self.response_plans),
                "open_incidents": len(open_incidents),
                "total_contingency_plans": len(self.contingency_plans),
                "total_evacuation_procedures": len(self.evacuation_procedures),
                "total_personnel_trained": 6,
                "drills_completed_this_quarter": 0,
            }
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

emergency_response_engine = EmergencyResponseEngine()