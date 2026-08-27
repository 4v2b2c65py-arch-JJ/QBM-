#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Logistics, Warehousing & Advanced Transport

Module for establishing warehouse/storage networks, shipping services,
and advanced cargo aircraft for continental package delivery.

Features:
- Warehouse location optimization (satellite data, traffic analysis, proximity)
- Storage facility upgrades via API and contacts
- Shipping service for rental to shipping companies
- Cross-provider assistance (Amazon, FedEx, UPS, DHL)
- Advanced cargo aircraft (private jet + military combo)
- Continental package delivery network
- Real-time traffic and route optimization
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

LOG = __import__("logging").getLogger("qb_protocol.being.chip.logistics_transport")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class WarehouseType(Enum):
    """Types of warehouse/storage facilities."""
    DISTRIBUTION_CENTER = "distribution_center"
    FULFILLMENT_CENTER = "fulfillment_center"
    COLD_STORAGE = "cold_storage"
    CROSS_DOCK = "cross_dock"
    MICRO_FULFILLMENT = "micro_fulfillment"
    SELF_STORAGE = "self_storage"
    INDUSTRIAL_OUTDOOR = "industrial_outdoor_storage"
    HAZMAT_STORAGE = "hazmat_storage"
    BONDED_WAREHOUSE = "bonded_warehouse"
    CONSOLIDATION_CENTER = "consolidation_center"
    RETURNS_CENTER = "returns_center"
    PARCEL_HUB = "parcel_hub"
    SORTATION_CENTER = "sortation_center"
    LAST_MILE_FACILITY = "last_mile_facility"
    PORT_PROXIMATE = "port_proximate"
    AIRPORT_PROXIMATE = "airport_proximate"
    RAIL_SERVED = "rail_served"
    INTERMODAL = "intermodal"


class WarehouseTier(Enum):
    """Warehouse quality/upgrade tier."""
    BASIC = "basic"  # Basic storage, minimal automation
    STANDARD = "standard"  # Some automation, WMS
    ADVANCED = "advanced"  # High automation, robotics
    SMART = "smart"  # AI-optimized, fully automated
    MEGA = "mega"  # XXL facility, 100k+ sqft
    AUTONOMOUS = "autonomous"  # Lights-out, drone-enabled


class ShippingProvider(Enum):
    """Major shipping providers for cross-provider assistance."""
    AMAZON = "amazon"
    FEDEX = "fedex"
    UPS = "ups"
    DHL = "dhl"
    USPS = "usps"
    ONTRAC = "ontrac"
    LASERSHIP = "lasership"
    PUROLATOR = "purolator"
    CANADA_POST = "canada_post"
    ROYAL_MAIL = "royal_mail"
    PARCEL_FORCE = "parcel_force"
    YAMATO = "yamato"
    SF_EXPRESS = "sf_express"
    J_NEWS = "j_news"


class LogisticsAPI(Enum):
    """Logistics and warehouse APIs."""
    LOCUS = "locus"
    FOURKITES = "fourkites"
    PROJECT44 = "project44"
    SHIPWELL = "shipwell"
    FREIGHTOS = "freightos"
    FLEXPORT = "flexport"
    TRANSPLACE = "transplace"
    BLUE_YONDER = "blue_yonder"
    MANHATTAN = "manhattan_associates"
    ORACLE_WMS = "oracle_wms"
    SAP_WMS = "sap_wms"
    SHIPPING_EASY = "shipping_easy"
    SHIPSTATION = "station"
    SHIPPO = "shippo"
    EASYPOST = "easypost"
    AFTERSHIP = "aftership"
    ROUTE = "route"
    SHIPENGINE = "shipengine"
    PARCEL_PERFORM = "parcel_perform"
    ONFIDELITY = "onfidelity"


class CargoAircraftType(Enum):
    """Advanced cargo aircraft types."""
    VTOL_CARGO = "vtol_cargo"
    HYBRID_ELECTRIC = "hybrid_electric"
    AUTONOMOUS_CARGO = "autonomous_cargo"
    PRIVATE_JET_CARGO = "private_jet_cargo"
    REGIONAL_CARGO = "regional_cargo"
    LONG_HAUL_CARGO = "long_haul_cargo"
    OVERSIZE_CARGO = "oversize_cargo"
    TURBOPROP_CARGO = "turboprop_cargo"
    LIGHT_CARGO = "light_cargo"
    HEAVY_LIFT = "heavy_lift"
    SUPERSONIC_CARGO = "supersonic_cargo"
    HYDROGEN_CARGO = "hydrogen_cargo"
    ELECTRIC_CARGO = "electric_cargo"
    AMPHIBIOUS_CARGO = "amphibious_cargo"
    MODULAR_CARGO = "modular_cargo"


class TransportCompanyType(Enum):
    """Types of transport companies to establish."""
    CARGO_AIRLINE = "cargo_airline"
    REGIONAL_CARRIER = "regional_carrier"
    LAST_MILE = "last_mile"
    CROSS_COUNTRY = "cross_country"
    CONTINENTAL = "continental"
    EXPRESS_CARGO = "express_cargo"
    CHARTER_CARGO = "charter_cargo"
    FORWARDER = "freight_forwarder"
    BROKER = "freight_broker"
    NVOCC = "nvocc"
    MARITIME_CARRIER = "maritime_carrier"
    BARGE_OPERATOR = "barge_operator"
    MULTIMODAL = "multimodal_operator"


class SeaVesselType(Enum):
    """Types of sea vessels for cargo."""
    CONTAINER_SHIP = "container_ship"
    BULK_CARRIER = "bulk_carrier"
    TANKER = "tanker"
    RORO_SHIP = "roro_ship"
    GENERAL_CARGO = "general_cargo"
    HEAVY_LIFT_VESSEL = "heavy_lift_vessel"
    BARGE = "barge"
    FEEDER_VESSEL = "feeder_vessel"
    PANAMAX = "panamax"
    POST_PANAMAX = "post_panamax"
    ULTRA_LARGE = "ultra_large"
    HANDYMAX = "handymax"
    SUPRAMAX = "supramax"
    REEFER_SHIP = "reefer_ship"
    LNG_CARRIER = "lng_carrier"
    LPG_CARRIER = "lpg_carrier"


class CargoPriority(Enum):
    """Cargo priority levels for transport selection."""
    CRITICAL = "critical"  # Aircraft - fastest, most expensive
    HIGH = "high"  # Aircraft or fast sea
    STANDARD = "standard"  # Multi-modal optimized
    ECONOMY = "economy"  # Sea/ground, lowest cost
    BULK = "bulk"  # Sea only, non-time-sensitive


class TransportMode(Enum):
    """Transport modes for multi-modal selection."""
    AIR = "air"
    SEA = "sea"
    RAIL = "rail"
    TRUCK = "truck"
    AIR_SEA = "air_sea"
    SEA_TRUCK = "sea_truck"
    AIR_TRUCK = "air_truck"
    SEA_RAIL = "sea_rail"
    AIR_SEA_TRUCK = "air_sea_truck"


# =============================================================================
# DATA CLASSES - WAREHOUSE
# =============================================================================

@dataclass
class WarehouseLocation:
    """Optimal warehouse location profile."""
    location_id: str
    name: str
    address: str
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    warehouse_type: WarehouseType
    tier: WarehouseTier
    total_sqft: float
    clear_height_ft: float
    dock_doors: int
    parking_spaces: int
    year_built: int
    renovation_year: int
    has_sprinklers: bool = False
    has_security: bool = False
    has_climate_control: bool = False
    has_rail_spur: bool = False
    has_highway_access: bool = False
    has_port_proximity: bool = False
    has_airport_proximity: bool = False
    distance_to_highway_miles: float = 0
    distance_to_port_miles: float = 0
    distance_to_airport_miles: float = 0
    distance_to_rail_miles: float = 0
    population_10_miles: int = 0
    population_25_miles: int = 0
    population_50_miles: int = 0
    median_household_income: int = 0
    labor_force_10_miles: int = 0
    traffic_congestion_index: float = 0
    asking_rent_psf: float = 0
    sale_price_psf: float = 0
    property_taxes_annual: float = 0
    utilities_annual: float = 0
    insurance_annual: float = 0
    total_occupancy_cost: float = 0
    incentives_available: List[str] = field(default_factory=list)
    contact_name: str = ""
    contact_company: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    contact_website: str = ""
    listing_url: str = ""
    notes: str = ""

    @property
    def cost_per_sqft_annual(self) -> float:
        if self.total_sqft == 0:
            return 0
        return self.total_occupancy_cost / self.total_sqft

    @property
    def customer_coverage_10_miles(self) -> float:
        return self.population_10_miles

    @property
    def customer_coverage_50_miles(self) -> float:
        return self.population_50_miles

    @property
    def traffic_score(self) -> float:
        """Lower is better - less traffic congestion."""
        return 10 - self.traffic_congestion_index

    @property
    def location_score(self) -> float:
        """Overall location score 0-100."""
        score = 0
        score += min(20, self.traffic_score * 2)
        score += min(20, self.population_50_miles / 100000)
        score += min(15, 15 if self.has_highway_access else 0)
        score += min(15, 15 if self.has_port_proximity else 0)
        score += min(15, 15 if self.has_airport_proximity else 0)
        score += min(15, 15 if self.has_rail_spur else 0)
        return min(100, score)


@dataclass
class WarehouseNetwork:
    """Network of warehouse locations."""
    network_id: str
    name: str
    locations: List[WarehouseLocation] = field(default_factory=list)
    total_sqft: float = 0

    @property
    def location_count(self) -> int:
        return len(self.locations)

    @property
    def total_capacity_sqft(self) -> float:
        return sum(l.total_sqft for l in self.locations)

    @property
    def average_location_score(self) -> float:
        if not self.locations:
            return 0
        return sum(l.location_score for l in self.locations) / len(self.locations)

    @property
    def total_annual_cost(self) -> float:
        return sum(l.total_occupancy_cost for l in self.locations)


# =============================================================================
# DATA CLASSES - SHIPPING SERVICE
# =============================================================================

@dataclass
class ShippingService:
    """Shipping service for rental to shipping companies."""
    service_id: str
    name: str
    description: str
    origin_countries: List[str] = field(default_factory=list)
    destination_countries: List[str] = field(default_factory=list)
    supported_providers: List[ShippingProvider] = field(default_factory=list)
    service_level: str = ""  # "standard", "express", "overnight", "same_day"
    average_transit_days: int = 0
    max_weight_lbs: float = 0
    max_dimensions_inches: float = 0
    tracking_included: bool = True
    insurance_included: bool = False
    insurance_rate: float = 0
    base_rate: float = 0
    per_lb_rate: float = 0
    fuel_surcharge_rate: float = 0
    oversize_fee: float = 0
    residential_delivery_fee: float = 0
    signature_required_fee: float = 0
    is_active: bool = False
    is_integrated: bool = False
    api_endpoint: str = ""
    api_documentation: str = ""
    notes: str = ""

    def calculate_rate(self, weight_lbs: float, distance_miles: float, 
                       is_residential: bool = False, requires_signature: bool = False) -> float:
        """Calculate shipping rate."""
        rate = self.base_rate
        rate += weight_lbs * self.per_lb_rate
        rate += distance_miles * 0.01
        rate *= (1 + self.fuel_surcharge_rate)
        if is_residential:
            rate += self.residential_delivery_fee
        if requires_signature:
            rate += self.signature_required_fee
        return round(rate, 2)


@dataclass
class CrossProviderAssistance:
    """Cross-provider assistance for Amazon, FedEx, UPS, etc."""
    assistance_id: str
    provider: ShippingProvider
    assistance_type: str  # "label_generation", "tracking", "rate_comparison", "manifest"
    description: str
    api_endpoint: str
    auth_type: str
    api_key_required: bool
    free_tier: bool
    free_tier_limit: int
    paid_tier_cost: float
    supported_services: List[str] = field(default_factory=list)
    is_integrated: bool = False
    is_active: bool = False
    documentation_url: str = ""
    signup_url: str = ""
    notes: str = ""


# =============================================================================
# DATA CLASSES - ADVANCED CARGO AIRCRAFT
# =============================================================================

@dataclass
class CargoAircraft:
    """Advanced cargo aircraft for continental delivery."""
    aircraft_id: str
    name: str
    aircraft_type: CargoAircraftType
    manufacturer: str
    model: str
    year_introduced: int
    max_payload_lbs: float
    max_range_miles: float
    cruise_speed_mph: float
    service_ceiling_ft: float
    runway_required_ft: float
    fuel_type: str
    fuel_capacity_gallons: float
    fuel_consumption_gph: float
    cargo_volume_cubic_ft: float
    door_dimensions_ft: str
    has_autonomous_capability: bool = False
    has_vtol_capability: bool = False
    has_self_loading: bool = False
    has_climate_control: bool = False
    has_refrigeration: bool = False
    has_hazmat_capability: bool = False
    crew_required: int = 2
    acquisition_cost: float = 0
    lease_cost_monthly: float = 0
    operating_cost_per_hour: float = 0
    maintenance_cost_per_hour: float = 0
    insurance_cost_annual: float = 0
    registration_number: str = ""
    is_owned: bool = False
    is_leased: bool = False
    is_operational: bool = False
    home_base: str = ""
    notes: str = ""

    @property
    def cost_per_mile(self) -> float:
        if self.cruise_speed_mph == 0:
            return 0
        hourly_cost = self.operating_cost_per_hour + self.maintenance_cost_per_hour
        return hourly_cost / self.cruise_speed_mph

    @property
    def cost_per_lb_mile(self) -> float:
        if self.max_payload_lbs == 0 or self.max_range_miles == 0:
            return 0
        total_cost = self.cost_per_mile * self.max_range_miles
        return total_cost / (self.max_payload_lbs * self.max_range_miles)

    @property
    def payload_efficiency(self) -> float:
        """Payload as percentage of total weight capacity."""
        if self.max_payload_lbs == 0:
            return 0
        return self.max_payload_lbs / (self.max_payload_lbs + self.fuel_capacity_gallons * 6)

    @property
    def is_autonomous(self) -> bool:
        return self.has_autonomous_capability

    @property
    def can_operate_remote(self) -> bool:
        return self.has_vtol_capability or self.runway_required_ft < 2000


@dataclass
class AircraftFleet:
    """Fleet of cargo aircraft."""
    fleet_id: str
    name: str
    aircraft: List[CargoAircraft] = field(default_factory=list)
    maintenance_facilities: List[str] = field(default_factory=list)
    crew_bases: List[str] = field(default_factory=list)
    dispatch_center: str = ""

    @property
    def total_aircraft(self) -> int:
        return len(self.aircraft)

    @property
    def total_payload_capacity(self) -> float:
        return sum(a.max_payload_lbs for a in self.aircraft)

    @property
    def total_annual_operating_cost(self) -> float:
        return sum(
            (a.operating_cost_per_hour + a.maintenance_cost_per_hour) * 2000 +
            a.insurance_cost_annual
            for a in self.aircraft
        )

    @property
    def autonomous_count(self) -> int:
        return sum(1 for a in self.aircraft if a.has_autonomous_capability)

    @property
    def vtol_count(self) -> int:
        return sum(1 for a in self.aircraft if a.has_vtol_capability)


@dataclass
class DeliveryRoute:
    """Continental delivery route."""
    route_id: str
    name: str
    origin: str
    destination: str
    distance_miles: float
    estimated_flight_time_hours: float
    alternate_routes: List[str] = field(default_factory=list)
    waypoints: List[str] = field(default_factory=list)
    weather_considerations: List[str] = field(default_factory=list)
    airspace_restrictions: List[str] = field(default_factory=list)
    fuel_stops: List[str] = field(default_factory=list)
    ground_transport_connections: List[str] = field(default_factory=list)
    average_transit_time_hours: float = 0
    on_time_performance: float = 0
    cost_per_lb: float = 0
    is_active: bool = False
    frequency: str = ""  # "daily", "twice_daily", "weekly"
    notes: str = ""


# =============================================================================
# DATA CLASSES - SEA/MARITIME TRANSPORT
# =============================================================================

@dataclass
class SeaVessel:
    """Sea vessel for cargo transport."""
    vessel_id: str
    name: str
    vessel_type: SeaVesselType
    manufacturer: str
    model: str
    year_introduced: int
    deadweight_tonnage: float
    container_teus: float
    max_payload_lbs: float
    cruise_speed_knots: float
    range_nautical_miles: float
    fuel_type: str
    fuel_consumption_tons_day: float
    hold_capacity_cubic_ft: float
    door_dimensions_ft: str
    has_reefer_plugs: bool = False
    has_climate_control: bool = False
    has_hazmat_capability: bool = False
    has_heavy_lift: bool = False
    crew_required: int = 20
    acquisition_cost: float = 0
    lease_cost_monthly: float = 0
    operating_cost_per_day: float = 0
    maintenance_cost_per_day: float = 0
    insurance_cost_annual: float = 0
    registration_number: str = ""
    flag_state: str = ""
    is_owned: bool = False
    is_leased: bool = False
    is_operational: bool = False
    home_port: str = ""
    notes: str = ""

    @property
    def cost_per_nautical_mile(self) -> float:
        if self.cruise_speed_knots == 0:
            return 0
        daily_cost = self.operating_cost_per_day + self.maintenance_cost_per_day
        daily_distance = self.cruise_speed_knots * 24
        return daily_cost / daily_distance

    @property
    def cost_per_container_mile(self) -> float:
        if self.container_teus == 0 or self.range_nautical_miles == 0:
            return 0
        total_cost = self.cost_per_nautical_mile * self.range_nautical_miles
        return total_cost / (self.container_teus * self.range_nautical_miles)

    @property
    def cost_per_lb_mile(self) -> float:
        if self.max_payload_lbs == 0 or self.range_nautical_miles == 0:
            return 0
        total_cost = self.cost_per_nautical_mile * self.range_nautical_miles
        return total_cost / (self.max_payload_lbs * self.range_nautical_miles)

    @property
    def reefer_capacity(self) -> int:
        return int(self.container_teus * 0.1) if self.has_reefer_plugs else 0


@dataclass
class VesselFleet:
    """Fleet of sea vessels."""
    fleet_id: str
    name: str
    vessels: List[SeaVessel] = field(default_factory=list)
    maintenance_ports: List[str] = field(default_factory=list)
    crew_bases: List[str] = field(default_factory=list)
    dispatch_center: str = ""

    @property
    def total_vessels(self) -> int:
        return len(self.vessels)

    @property
    def total_container_capacity(self) -> float:
        return sum(v.container_teus for v in self.vessels)

    @property
    def total_payload_capacity(self) -> float:
        return sum(v.max_payload_lbs for v in self.vessels)

    @property
    def total_annual_operating_cost(self) -> float:
        return sum(
            (v.operating_cost_per_day + v.maintenance_cost_per_day) * 365 +
            v.insurance_cost_annual
            for v in self.vessels
        )

    @property
    def total_reefer_capacity(self) -> int:
        return sum(v.reefer_capacity for v in self.vessels)


@dataclass
class SeaRoute:
    """Sea delivery route."""
    route_id: str
    name: str
    origin_port: str
    destination_port: str
    distance_nautical_miles: float
    estimated_transit_days: float
    alternate_routes: List[str] = field(default_factory=list)
    waypoints: List[str] = field(default_factory=list)
    canal_transits: List[str] = field(default_factory=list)
    weather_considerations: List[str] = field(default_factory=list)
    port_connections: List[str] = field(default_factory=list)
    ground_transport_connections: List[str] = field(default_factory=list)
    average_transit_days: float = 0
    on_time_performance: float = 0
    cost_per_teu: float = 0
    cost_per_lb: float = 0
    is_active: bool = False
    frequency: str = ""  # "weekly", "biweekly", "daily"
    notes: str = ""


@dataclass
class MultimodalCargo:
    """Multi-modal cargo allocation."""
    cargo_id: str
    name: str
    description: str
    origin: str
    destination: str
    weight_lbs: float
    volume_cubic_ft: float
    container_count: int
    priority: CargoPriority
    requires_reefer: bool = False
    requires_hazmat: bool = False
    requires_heavy_lift: bool = False
    time_sensitivity_hours: float = 0
    max_acceptable_cost: float = 0
    selected_mode: Optional[TransportMode] = None
    selected_aircraft: Optional[str] = None
    selected_vessel: Optional[str] = None
    estimated_cost: float = 0
    estimated_transit_hours: float = 0
    is_allocated: bool = False
    notes: str = ""

    @property
    def urgency_score(self) -> float:
        """0-100 urgency score."""
        if self.time_sensitivity_hours <= 0:
            return 0
        if self.time_sensitivity_hours < 24:
            return 100
        elif self.time_sensitivity_hours < 72:
            return 75
        elif self.time_sensitivity_hours < 168:
            return 50
        else:
            return 25

    @property
    def recommended_mode(self) -> TransportMode:
        """Recommend transport mode based on cargo characteristics."""
        if self.priority == CargoPriority.CRITICAL:
            return TransportMode.AIR
        elif self.priority == CargoPriority.HIGH:
            if self.weight_lbs < 5000:
                return TransportMode.AIR
            else:
                return TransportMode.AIR_TRUCK
        elif self.priority == CargoPriority.STANDARD:
            if self.weight_lbs > 10000:
                return TransportMode.SEA_TRUCK
            else:
                return TransportMode.AIR_SEA_TRUCK
        elif self.priority == CargoPriority.ECONOMY:
            return TransportMode.SEA_TRUCK
        elif self.priority == CargoPriority.BULK:
            return TransportMode.SEA
        return TransportMode.TRUCK


# =============================================================================
# DATA CLASSES - TRANSPORT COMPANY
# =============================================================================

@dataclass
class TransportCompany:
    """Transport company establishment."""
    company_id: str
    name: str
    company_type: TransportCompanyType
    description: str
    founded_year: int
    headquarters: str
    countries_served: List[str] = field(default_factory=list)
    fleet_size: int = 0
    annual_revenue: float = 0
    employees: int = 0
    certifications: List[str] = field(default_factory=list)
    operating_authority: List[str] = field(default_factory=list)
    insurance_coverage: float = 0
    is_established: bool = False
    is_operational: bool = False
    is_insured: bool = False
    has_operating_authority: bool = False
    api_integrations: List[LogisticsAPI] = field(default_factory=list)
    notes: str = ""


# =============================================================================
# MAIN ENGINE
# =============================================================================

class LogisticsTransportEngine:
    """
    Engine for logistics, warehousing, and advanced transport.
    
    Integrates warehouse location optimization, shipping services,
    cross-provider assistance, cargo aircraft fleet, and delivery routes.
    """
    
    def __init__(self):
        self.warehouses: Dict[str, WarehouseLocation] = {}
        self.warehouse_networks: Dict[str, WarehouseNetwork] = {}
        self.shipping_services: Dict[str, ShippingService] = {}
        self.cross_provider_assistance: Dict[str, CrossProviderAssistance] = {}
        self.aircraft: Dict[str, CargoAircraft] = {}
        self.fleets: Dict[str, AircraftFleet] = {}
        self.delivery_routes: Dict[str, DeliveryRoute] = {}
        self.transport_companies: Dict[str, TransportCompany] = {}
        self.sea_vessels: Dict[str, SeaVessel] = {}
        self.vessel_fleets: Dict[str, VesselFleet] = {}
        self.sea_routes: Dict[str, SeaRoute] = {}
        self.multimodal_cargo: Dict[str, MultimodalCargo] = {}
        
        self._init_default_aircraft()
        self._init_default_providers()
        self._init_default_vessels()
        self._init_default_multimodal_rules()
    
    def _init_default_vessels(self):
        """Initialize default sea vessel models."""
        default_vessels = [
            SeaVessel(
                vessel_id="sv_feeder_1500",
                name="Feeder 1500 TEU",
                vessel_type=SeaVesselType.FEEDER_VESSEL,
                manufacturer="Hyundai Mipo",
                model="Feedermax 1500",
                year_introduced=2023,
                deadweight_tonnage=20000,
                container_teus=1500,
                max_payload_lbs=35000000,
                cruise_speed_knots=18,
                range_nautical_miles=8000,
                fuel_type="marine_gas_oil",
                fuel_consumption_tons_day=30,
                hold_capacity_cubic_ft=500000,
                door_dimensions_ft="open_top",
                has_reefer_plugs=True,
                has_climate_control=True,
                has_hazmat_capability=True,
                has_heavy_lift=False,
                crew_required=18,
                acquisition_cost=35000000,
                lease_cost_monthly=200000,
                operating_cost_per_day=15000,
                maintenance_cost_per_day=3000,
                insurance_cost_annual=500000,
                notes="Feeder vessel for short-sea routes and hub feeding"
            ),
            SeaVessel(
                vessel_id="sv_panamax_4000",
                name="Panamax 4000 TEU",
                vessel_type=SeaVesselType.PANAMAX,
                manufacturer="Daewoo Shipbuilding",
                model="Panamax 4000",
                year_introduced=2022,
                deadweight_tonnage=50000,
                container_teus=4000,
                max_payload_lbs=90000000,
                cruise_speed_knots=20,
                range_nautical_miles=12000,
                fuel_type="marine_gas_oil",
                fuel_consumption_tons_day=60,
                hold_capacity_cubic_ft=1200000,
                door_dimensions_ft="open_top",
                has_reefer_plugs=True,
                has_climate_control=True,
                has_hazmat_capability=True,
                has_heavy_lift=False,
                crew_required=20,
                acquisition_cost=80000000,
                lease_cost_monthly=400000,
                operating_cost_per_day=25000,
                maintenance_cost_per_day=5000,
                insurance_cost_annual=1000000,
                notes="Panamax container ship - fits Panama Canal, ideal for Atlantic-Pacific"
            ),
            SeaVessel(
                vessel_id="sv_post_panamax_8000",
                name="Post-Panamax 8000 TEU",
                vessel_type=SeaVesselType.POST_PANAMAX,
                manufacturer="Samsung Heavy Industries",
                model="Post-Panamax 8000",
                year_introduced=2024,
                deadweight_tonnage=100000,
                container_teus=8000,
                max_payload_lbs=170000000,
                cruise_speed_knots=22,
                range_nautical_miles=15000,
                fuel_type="lng_dual_fuel",
                fuel_consumption_tons_day=100,
                hold_capacity_cubic_ft=2500000,
                door_dimensions_ft="open_top",
                has_reefer_plugs=True,
                has_climate_control=True,
                has_hazmat_capability=True,
                has_heavy_lift=True,
                crew_required=22,
                acquisition_cost=130000000,
                lease_cost_monthly=650000,
                operating_cost_per_day=40000,
                maintenance_cost_per_day=8000,
                insurance_cost_annual=2000000,
                notes="Post-Panamax with LNG dual-fuel - eco-friendly large capacity"
            ),
            SeaVessel(
                vessel_id="sv_roro_5000",
                name="RoRo 5000 LM",
                vessel_type=SeaVesselType.RORO_SHIP,
                manufacturer="Mitsubishi Heavy",
                model="RoRo 5000",
                year_introduced=2023,
                deadweight_tonnage=25000,
                container_teus=0,
                max_payload_lbs=50000000,
                cruise_speed_knots=20,
                range_nautical_miles=10000,
                fuel_type="marine_gas_oil",
                fuel_consumption_tons_day=40,
                hold_capacity_cubic_ft=800000,
                door_dimensions_ft="ramp_30x30",
                has_reefer_plugs=False,
                has_climate_control=False,
                has_hazmat_capability=True,
                has_heavy_lift=True,
                crew_required=20,
                acquisition_cost=70000000,
                lease_cost_monthly=350000,
                operating_cost_per_day=20000,
                maintenance_cost_per_day=4000,
                insurance_cost_annual=800000,
                notes="Roll-on/Roll-off for vehicles and heavy equipment"
            ),
            SeaVessel(
                vessel_id="sv_barge_50000",
                name="Heavy Lift Barge",
                vessel_type=SeaVesselType.BARGE,
                manufacturer="Cargill Marine",
                model="HeavyLift 50000",
                year_introduced=2022,
                deadweight_tonnage=50000,
                container_teus=0,
                max_payload_lbs=100000000,
                cruise_speed_knots=8,
                range_nautical_miles=3000,
                fuel_type="marine_gas_oil",
                fuel_consumption_tons_day=15,
                hold_capacity_cubic_ft=1000000,
                door_dimensions_ft="open_deck",
                has_reefer_plugs=False,
                has_climate_control=False,
                has_hazmat_capability=True,
                has_heavy_lift=True,
                crew_required=12,
                acquisition_cost=25000000,
                lease_cost_monthly=100000,
                operating_cost_per_day=8000,
                maintenance_cost_per_day=2000,
                insurance_cost_annual=300000,
                notes="Heavy lift barge for oversized cargo - coastal and river routes"
            ),
        ]
        self.sea_vessels = {v.vessel_id: v for v in default_vessels}
    
    def _init_default_multimodal_rules(self):
        """Initialize default multimodal transport selection rules."""
        self._multimodal_rules = {
            CargoPriority.CRITICAL: {
                "primary": TransportMode.AIR,
                "fallback": TransportMode.AIR_TRUCK,
                "max_transit_hours": 6,
                "cost_weight": 0.1,
                "speed_weight": 0.9,
            },
            CargoPriority.HIGH: {
                "primary": TransportMode.AIR,
                "fallback": TransportMode.AIR_SEA_TRUCK,
                "max_transit_hours": 24,
                "cost_weight": 0.3,
                "speed_weight": 0.7,
            },
            CargoPriority.STANDARD: {
                "primary": TransportMode.AIR_SEA_TRUCK,
                "fallback": TransportMode.SEA_TRUCK,
                "max_transit_hours": 72,
                "cost_weight": 0.5,
                "speed_weight": 0.5,
            },
            CargoPriority.ECONOMY: {
                "primary": TransportMode.SEA_TRUCK,
                "fallback": TransportMode.TRUCK,
                "max_transit_hours": 168,
                "cost_weight": 0.8,
                "speed_weight": 0.2,
            },
            CargoPriority.BULK: {
                "primary": TransportMode.SEA,
                "fallback": TransportMode.SEA_RAIL,
                "max_transit_hours": 720,
                "cost_weight": 1.0,
                "speed_weight": 0.0,
            },
        }
    
    def _init_default_aircraft(self):
        """Initialize default aircraft models."""
        default_aircraft = [
            CargoAircraft(
                aircraft_id="ac_elroy_chaparral",
                name="Elroy Air Chaparral",
                aircraft_type=CargoAircraftType.VTOL_CARGO,
                manufacturer="Elroy Air",
                model="Chaparral",
                year_introduced=2026,
                max_payload_lbs=300,
                max_range_miles=300,
                cruise_speed_mph=150,
                service_ceiling_ft=15000,
                runway_required_ft=0,
                fuel_type="hybrid_electric",
                fuel_capacity_gallons=50,
                fuel_consumption_gph=15,
                cargo_volume_cubic_ft=50,
                door_dimensions_ft="4x4",
                has_autonomous_capability=True,
                has_vtol_capability=True,
                has_self_loading=True,
                has_climate_control=False,
                has_refrigeration=False,
                has_hazmat_capability=False,
                crew_required=0,
                acquisition_cost=500000,
                lease_cost_monthly=15000,
                operating_cost_per_hour=200,
                maintenance_cost_per_hour=50,
                insurance_cost_annual=25000,
                notes="Self-loading autonomous VTOL cargo - perfect for remote delivery"
            ),
            CargoAircraft(
                aircraft_id="ac_att_28",
                name="AT-28 Turboprop Cargo",
                aircraft_type=CargoAircraftType.TURBOPROP_CARGO,
                manufacturer="Pacific Aerospace",
                model="AT-28",
                year_introduced=2025,
                max_payload_lbs=1500,
                max_range_miles=800,
                cruise_speed_mph=220,
                service_ceiling_ft=25000,
                runway_required_ft=1500,
                fuel_type="jet_a",
                fuel_capacity_gallons=200,
                fuel_consumption_gph=40,
                cargo_volume_cubic_ft=200,
                door_dimensions_ft="5x5",
                has_autonomous_capability=False,
                has_vtol_capability=False,
                has_self_loading=False,
                has_climate_control=True,
                has_refrigeration=False,
                has_hazmat_capability=True,
                crew_required=1,
                acquisition_cost=1200000,
                lease_cost_monthly=25000,
                operating_cost_per_hour=400,
                maintenance_cost_per_hour=100,
                insurance_cost_annual=40000,
                notes="STOL turboprop - can operate from short runways, ideal for regional cargo"
            ),
            CargoAircraft(
                aircraft_id="ac_global_8000",
                name="Bombardier Global 8000 Cargo",
                aircraft_type=CargoAircraftType.PRIVATE_JET_CARGO,
                manufacturer="Bombardier",
                model="Global 8000",
                year_introduced=2025,
                max_payload_lbs=5000,
                max_range_miles=8000,
                cruise_speed_mph=560,
                service_ceiling_ft=51000,
                runway_required_ft=6000,
                fuel_type="jet_a",
                fuel_capacity_gallons=5000,
                fuel_consumption_gph=400,
                cargo_volume_cubic_ft=500,
                door_dimensions_ft="6x6",
                has_autonomous_capability=False,
                has_vtol_capability=False,
                has_self_loading=False,
                has_climate_control=True,
                has_refrigeration=True,
                has_hazmat_capability=True,
                crew_required=2,
                acquisition_cost=75000000,
                lease_cost_monthly=500000,
                operating_cost_per_hour=3000,
                maintenance_cost_per_hour=800,
                insurance_cost_annual=500000,
                notes="Ultra-long range business jet converted for cargo - fastest continental delivery"
            ),
            CargoAircraft(
                aircraft_id="ac_bbj_cargo",
                name="Boeing BBJ Cargo",
                aircraft_type=CargoAircraftType.LONG_HAUL_CARGO,
                manufacturer="Boeing",
                model="BBJ 737-700",
                year_introduced=2024,
                max_payload_lbs=20000,
                max_range_miles=6000,
                cruise_speed_mph=540,
                service_ceiling_ft=41000,
                runway_required_ft=6500,
                fuel_type="jet_a",
                fuel_capacity_gallons=10000,
                fuel_consumption_gph=800,
                cargo_volume_cubic_ft=1500,
                door_dimensions_ft="10x7",
                has_autonomous_capability=False,
                has_vtol_capability=False,
                has_self_loading=False,
                has_climate_control=True,
                has_refrigeration=True,
                has_hazmat_capability=True,
                crew_required=2,
                acquisition_cost=80000000,
                lease_cost_monthly=600000,
                operating_cost_per_hour=4000,
                maintenance_cost_per_hour=1000,
                insurance_cost_annual=600000,
                notes="Boeing Business Jet converted for heavy cargo - large capacity continental"
            ),
            CargoAircraft(
                aircraft_id="ac_antonov_124",
                name="Antonov An-124 Ruslan",
                aircraft_type=CargoAircraftType.OVERSIZE_CARGO,
                manufacturer="Antonov",
                model="An-124",
                year_introduced=1982,
                max_payload_lbs=330000,
                max_range_miles=4800,
                cruise_speed_mph=490,
                service_ceiling_ft=35000,
                runway_required_ft=8000,
                fuel_type="jet_a",
                fuel_capacity_gallons=50000,
                fuel_consumption_gph=3000,
                cargo_volume_cubic_ft=12000,
                door_dimensions_ft="20x18",
                has_autonomous_capability=False,
                has_vtol_capability=False,
                has_self_loading=False,
                has_climate_control=True,
                has_refrigeration=True,
                has_hazmat_capability=True,
                crew_required=6,
                acquisition_cost=200000000,
                lease_cost_monthly=1000000,
                operating_cost_per_hour=15000,
                maintenance_cost_per_hour=5000,
                insurance_cost_annual=2000000,
                notes="Heavy lift cargo - oversize and military-grade loads"
            ),
            CargoAircraft(
                aircraft_id="ac_cessna_208",
                name="Cessna 208 Caravan",
                aircraft_type=CargoAircraftType.LIGHT_CARGO,
                manufacturer="Cessna",
                model="208 Caravan",
                year_introduced=1982,
                max_payload_lbs=3000,
                max_range_miles=1200,
                cruise_speed_mph=180,
                service_ceiling_ft=25000,
                runway_required_ft=1500,
                fuel_type="jet_a",
                fuel_capacity_gallons=300,
                fuel_consumption_gph=60,
                cargo_volume_cubic_ft=200,
                door_dimensions_ft="5x5",
                has_autonomous_capability=False,
                has_vtol_capability=False,
                has_self_loading=False,
                has_climate_control=False,
                has_refrigeration=False,
                has_hazmat_capability=False,
                crew_required=1,
                acquisition_cost=2000000,
                lease_cost_monthly=10000,
                operating_cost_per_hour=300,
                maintenance_cost_per_hour=75,
                insurance_cost_annual=30000,
                notes="Light cargo workhorse - flexible, reliable, low operating cost"
            ),
        ]
        self.aircraft = {a.aircraft_id: a for a in default_aircraft}
    
    def _init_default_providers(self):
        """Initialize default cross-provider assistance."""
        default_providers = [
            CrossProviderAssistance(
                assistance_id="cp_amazon",
                provider=ShippingProvider.AMAZON,
                assistance_type="label_generation",
                description="Amazon Shipping API - generate labels, track packages, compare rates",
                api_endpoint="https://sellingpartnerapi.amazon.com",
                auth_type="oauth",
                api_key_required=True,
                free_tier=True,
                free_tier_limit=1000,
                paid_tier_cost=0,
                supported_services=["standard", "prime", "same_day"],
                documentation_url="https://developer-docs.amazon.com/sp-api/",
                signup_url="https://sellercentral.amazon.com/"
            ),
            CrossProviderAssistance(
                assistance_id="cp_fedex",
                provider=ShippingProvider.FEDEX,
                assistance_type="label_generation",
                description="FedEx Web Services - ship, track, rate",
                api_endpoint="https://apis.fedex.com",
                auth_type="api_key",
                api_key_required=True,
                free_tier=True,
                free_tier_limit=1000,
                paid_tier_cost=0,
                supported_services=["ground", "express", "freight", "same_day"],
                documentation_url="https://developer.fedex.com/api/en-us/home.html",
                signup_url="https://developer.fedex.com/api/en-us/register.html"
            ),
            CrossProviderAssistance(
                assistance_id="cp_ups",
                provider=ShippingProvider.UPS,
                assistance_type="label_generation",
                description="UPS Developer Kit - shipping, tracking, rating",
                api_endpoint="https://onlinetools.ups.com/api",
                auth_type="oauth",
                api_key_required=True,
                free_tier=True,
                free_tier_limit=1000,
                paid_tier_cost=0,
                supported_services=["ground", "next_day", "2day", "express"],
                documentation_url="https://www.ups.com/upsdeveloperkit",
                signup_url="https://www.ups.com/upsdeveloperkit"
            ),
            CrossProviderAssistance(
                assistance_id="cp_dhl",
                provider=ShippingProvider.DHL,
                assistance_type="label_generation",
                description="DHL Express API - international shipping, tracking",
                api_endpoint="https://api-eu.dhl.com",
                auth_type="api_key",
                api_key_required=True,
                free_tier=True,
                free_tier_limit=500,
                paid_tier_cost=0,
                supported_services=["express", "freight", "same_day"],
                documentation_url="https://developer.dhl.com/",
                signup_url="https://developer.dhl.com/user/register"
            ),
            CrossProviderAssistance(
                assistance_id="cp_shippo",
                provider=ShippingProvider.AMAZON,
                assistance_type="multi_carrier",
                description="Shippo - multi-carrier shipping API with all major providers",
                api_endpoint="https://api.goshippo.com",
                auth_type="api_key",
                api_key_required=True,
                free_tier=True,
                free_tier_limit=10000,
                paid_tier_cost=0,
                supported_services=["fedex", "ups", "usps", "dhl", "amazon"],
                documentation_url="https://goshippo.com/docs/",
                signup_url="https://goshippo.com/"
            ),
            CrossProviderAssistance(
                assistance_id="cp_shipstation",
                provider=ShippingProvider.AMAZON,
                assistance_type="multi_carrier",
                description="ShipStation - shipping management platform with 100+ carriers",
                api_endpoint="https://ssapi.shipstation.com",
                auth_type="api_key",
                api_key_required=True,
                free_tier=False,
                free_tier_limit=0,
                paid_tier_cost=59,
                supported_services=["fedex", "ups", "usps", "dhl", "amazon", "ontrac"],
                documentation_url="https://www.shipstation.com/developer-api/",
                signup_url="https://www.shipstation.com/"
            ),
            CrossProviderAssistance(
                assistance_id="cp_easypost",
                provider=ShippingProvider.AMAZON,
                assistance_type="multi_carrier",
                description="EasyPost - shipping API for developers",
                api_endpoint="https://api.easypost.com/v2",
                auth_type="api_key",
                api_key_required=True,
                free_tier=True,
                free_tier_limit=10000,
                paid_tier_cost=0,
                supported_services=["fedex", "ups", "usps", "dhl"],
                documentation_url="https://www.easypost.com/docs/api",
                signup_url="https://www.easypost.com/sign-up"
            ),
        ]
        self.cross_provider_assistance = {p.assistance_id: p for p in default_providers}
    
    # -------------------------------------------------------------------------
    # WAREHOUSE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_warehouse(self, warehouse: WarehouseLocation) -> WarehouseLocation:
        """Add a warehouse location."""
        self.warehouses[warehouse.location_id] = warehouse
        return warehouse
    
    def create_network(self, network_id: str, name: str) -> WarehouseNetwork:
        """Create a warehouse network."""
        network = WarehouseNetwork(network_id=network_id, name=name)
        self.warehouse_networks[network_id] = network
        return network
    
    def add_warehouse_to_network(self, network_id: str, location_id: str) -> bool:
        """Add a warehouse to a network."""
        if network_id not in self.warehouse_networks or location_id not in self.warehouses:
            return False
        self.warehouse_networks[network_id].locations.append(self.warehouses[location_id])
        return True
    
    def find_optimal_locations(self, min_score: float = 60, limit: int = 10) -> List[WarehouseLocation]:
        """Find optimal warehouse locations."""
        sorted_locations = sorted(
            self.warehouses.values(),
            key=lambda l: l.location_score,
            reverse=True
        )
        return [l for l in sorted_locations if l.location_score >= min_score][:limit]
    
    def analyze_network(self, network_id: str) -> Dict[str, Any]:
        """Analyze a warehouse network."""
        if network_id not in self.warehouse_networks:
            return {}
        
        network = self.warehouse_networks[network_id]
        
        return {
            "network_id": network_id,
            "name": network.name,
            "location_count": network.location_count,
            "total_capacity_sqft": network.total_capacity_sqft,
            "average_location_score": network.average_location_score,
            "total_annual_cost": network.total_annual_cost,
            "locations": [
                {
                    "location_id": l.location_id,
                    "name": l.name,
                    "city": l.city,
                    "state": l.state,
                    "type": l.warehouse_type.value,
                    "tier": l.tier.value,
                    "total_sqft": l.total_sqft,
                    "location_score": l.location_score,
                    "total_occupancy_cost": l.total_occupancy_cost,
                    "traffic_score": l.traffic_score,
                    "has_highway": l.has_highway_access,
                    "has_port": l.has_port_proximity,
                    "has_airport": l.has_airport_proximity,
                    "contact_name": l.contact_name,
                    "contact_company": l.contact_company,
                }
                for l in network.locations
            ],
        }
    
    # -------------------------------------------------------------------------
    # SHIPPING SERVICE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_shipping_service(self, service: ShippingService) -> ShippingService:
        """Add a shipping service."""
        self.shipping_services[service.service_id] = service
        return service
    
    def add_cross_provider_assistance(self, assistance: CrossProviderAssistance) -> CrossProviderAssistance:
        """Add cross-provider assistance."""
        self.cross_provider_assistance[assistance.assistance_id] = assistance
        return assistance
    
    def get_provider_apis(self, provider: ShippingProvider) -> List[CrossProviderAssistance]:
        """Get APIs for a specific provider."""
        return [a for a in self.cross_provider_assistance.values() if a.provider == provider]
    
    def analyze_shipping_capabilities(self) -> Dict[str, Any]:
        """Analyze shipping capabilities."""
        providers = set()
        for service in self.shipping_services.values():
            providers.update(service.supported_providers)
        
        return {
            "total_services": len(self.shipping_services),
            "total_providers": len(providers),
            "providers_covered": [p.value for p in providers],
            "multi_carrier_apis": len([a for a in self.cross_provider_assistance.values() 
                                      if a.assistance_type == "multi_carrier"]),
            "services": [
                {
                    "service_id": s.service_id,
                    "name": s.name,
                    "service_level": s.service_level,
                    "average_transit_days": s.average_transit_days,
                    "max_weight_lbs": s.max_weight_lbs,
                    "base_rate": s.base_rate,
                    "is_active": s.is_active,
                }
                for s in self.shipping_services.values()
            ],
        }
    
    # -------------------------------------------------------------------------
    # AIRCRAFT FLEET MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_aircraft(self, aircraft: CargoAircraft) -> CargoAircraft:
        """Add an aircraft to the fleet."""
        self.aircraft[aircraft.aircraft_id] = aircraft
        return aircraft
    
    def create_fleet(self, fleet_id: str, name: str) -> AircraftFleet:
        """Create an aircraft fleet."""
        fleet = AircraftFleet(fleet_id=fleet_id, name=name)
        self.fleets[fleet_id] = fleet
        return fleet
    
    def add_aircraft_to_fleet(self, fleet_id: str, aircraft_id: str) -> bool:
        """Add an aircraft to a fleet."""
        if fleet_id not in self.fleets or aircraft_id not in self.aircraft:
            return False
        self.fleets[fleet_id].aircraft.append(self.aircraft[aircraft_id])
        return True
    
    def find_aircraft_by_type(self, aircraft_type: CargoAircraftType) -> List[CargoAircraft]:
        """Find aircraft by type."""
        return [a for a in self.aircraft.values() if a.aircraft_type == aircraft_type]
    
    def find_autonomous_aircraft(self) -> List[CargoAircraft]:
        """Find autonomous aircraft."""
        return [a for a in self.aircraft.values() if a.has_autonomous_capability]
    
    def find_vtol_aircraft(self) -> List[CargoAircraft]:
        """Find VTOL aircraft."""
        return [a for a in self.aircraft.values() if a.has_vtol_capability]
    
    def find_remote_capable_aircraft(self) -> List[CargoAircraft]:
        """Find aircraft capable of remote operations."""
        return [a for a in self.aircraft.values() if a.can_operate_remote]
    
    def analyze_fleet(self, fleet_id: str) -> Dict[str, Any]:
        """Analyze an aircraft fleet."""
        if fleet_id not in self.fleets:
            return {}
        
        fleet = self.fleets[fleet_id]
        
        return {
            "fleet_id": fleet_id,
            "name": fleet.name,
            "total_aircraft": fleet.total_aircraft,
            "total_payload_capacity": fleet.total_payload_capacity,
            "total_annual_operating_cost": fleet.total_annual_operating_cost,
            "autonomous_count": fleet.autonomous_count,
            "vtol_count": fleet.vtol_count,
            "aircraft": [
                {
                    "aircraft_id": a.aircraft_id,
                    "name": a.name,
                    "type": a.aircraft_type.value,
                    "max_payload_lbs": a.max_payload_lbs,
                    "max_range_miles": a.max_range_miles,
                    "cruise_speed_mph": a.cruise_speed_mph,
                    "cost_per_mile": a.cost_per_mile,
                    "is_autonomous": a.is_autonomous,
                    "can_operate_remote": a.can_operate_remote,
                }
                for a in fleet.aircraft
            ],
        }
    
    # -------------------------------------------------------------------------
    # DELIVERY ROUTES
    # -------------------------------------------------------------------------
    
    def add_delivery_route(self, route: DeliveryRoute) -> DeliveryRoute:
        """Add a delivery route."""
        self.delivery_routes[route.route_id] = route
        return route
    
    def get_active_routes(self) -> List[DeliveryRoute]:
        """Get active delivery routes."""
        return [r for r in self.delivery_routes.values() if r.is_active]
    
    def analyze_routes(self) -> Dict[str, Any]:
        """Analyze delivery routes."""
        active = self.get_active_routes()
        
        return {
            "total_routes": len(self.delivery_routes),
            "active_routes": len(active),
            "total_distance": sum(r.distance_miles for r in active),
            "average_transit_time": (
                sum(r.average_transit_time_hours for r in active) / len(active)
                if active else 0
            ),
            "routes": [
                {
                    "route_id": r.route_id,
                    "name": r.name,
                    "origin": r.origin,
                    "destination": r.destination,
                    "distance_miles": r.distance_miles,
                    "average_transit_time_hours": r.average_transit_time_hours,
                    "frequency": r.frequency,
                    "is_active": r.is_active,
                }
                for r in self.delivery_routes.values()
            ],
        }
    
    # -------------------------------------------------------------------------
    # TRANSPORT COMPANY
    # -------------------------------------------------------------------------
    
    def add_transport_company(self, company: TransportCompany) -> TransportCompany:
        """Add a transport company."""
        self.transport_companies[company.company_id] = company
        return company
    
    # -------------------------------------------------------------------------
    # SEA/MARITIME TRANSPORT MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_sea_vessel(self, vessel: SeaVessel) -> SeaVessel:
        """Add a sea vessel."""
        self.sea_vessels[vessel.vessel_id] = vessel
        return vessel
    
    def create_vessel_fleet(self, fleet_id: str, name: str) -> VesselFleet:
        """Create a vessel fleet."""
        fleet = VesselFleet(fleet_id=fleet_id, name=name)
        self.vessel_fleets[fleet_id] = fleet
        return fleet
    
    def add_vessel_to_fleet(self, fleet_id: str, vessel_id: str) -> bool:
        """Add a vessel to a fleet."""
        if fleet_id not in self.vessel_fleets or vessel_id not in self.sea_vessels:
            return False
        self.vessel_fleets[fleet_id].vessels.append(self.sea_vessels[vessel_id])
        return True
    
    def find_vessels_by_type(self, vessel_type: SeaVesselType) -> List[SeaVessel]:
        """Find vessels by type."""
        return [v for v in self.sea_vessels.values() if v.vessel_type == vessel_type]
    
    def find_reefer_vessels(self) -> List[SeaVessel]:
        """Find vessels with reefer capability."""
        return [v for v in self.sea_vessels.values() if v.has_reefer_plugs]
    
    def find_heavy_lift_vessels(self) -> List[SeaVessel]:
        """Find vessels with heavy lift capability."""
        return [v for v in self.sea_vessels.values() if v.has_heavy_lift]
    
    def add_sea_route(self, route: SeaRoute) -> SeaRoute:
        """Add a sea route."""
        self.sea_routes[route.route_id] = route
        return route
    
    def get_active_sea_routes(self) -> List[SeaRoute]:
        """Get active sea routes."""
        return [r for r in self.sea_routes.values() if r.is_active]
    
    def analyze_vessel_fleet(self, fleet_id: str) -> Dict[str, Any]:
        """Analyze a vessel fleet."""
        if fleet_id not in self.vessel_fleets:
            return {}
        
        fleet = self.vessel_fleets[fleet_id]
        
        return {
            "fleet_id": fleet_id,
            "name": fleet.name,
            "total_vessels": fleet.total_vessels,
            "total_container_capacity": fleet.total_container_capacity,
            "total_payload_capacity": fleet.total_payload_capacity,
            "total_annual_operating_cost": fleet.total_annual_operating_cost,
            "total_reefer_capacity": fleet.total_reefer_capacity,
            "vessels": [
                {
                    "vessel_id": v.vessel_id,
                    "name": v.name,
                    "type": v.vessel_type.value,
                    "container_teus": v.container_teus,
                    "max_payload_lbs": v.max_payload_lbs,
                    "cruise_speed_knots": v.cruise_speed_knots,
                    "cost_per_nautical_mile": v.cost_per_nautical_mile,
                    "has_reefer": v.has_reefer_plugs,
                    "has_heavy_lift": v.has_heavy_lift,
                }
                for v in fleet.vessels
            ],
        }
    
    def analyze_sea_routes(self) -> Dict[str, Any]:
        """Analyze sea routes."""
        active = self.get_active_sea_routes()
        
        return {
            "total_routes": len(self.sea_routes),
            "active_routes": len(active),
            "total_distance": sum(r.distance_nautical_miles for r in active),
            "average_transit_days": (
                sum(r.average_transit_days for r in active) / len(active)
                if active else 0
            ),
            "routes": [
                {
                    "route_id": r.route_id,
                    "name": r.name,
                    "origin_port": r.origin_port,
                    "destination_port": r.destination_port,
                    "distance_nautical_miles": r.distance_nautical_miles,
                    "average_transit_days": r.average_transit_days,
                    "frequency": r.frequency,
                    "is_active": r.is_active,
                }
                for r in self.sea_routes.values()
            ],
        }
    
    # -------------------------------------------------------------------------
    # MULTI-MODAL CARGO ALLOCATION
    # -------------------------------------------------------------------------
    
    def add_multimodal_cargo(self, cargo: MultimodalCargo) -> MultimodalCargo:
        """Add multi-modal cargo for allocation."""
        self.multimodal_cargo[cargo.cargo_id] = cargo
        return cargo
    
    def allocate_cargo(self, cargo_id: str) -> Dict[str, Any]:
        """Allocate cargo to optimal transport mode based on priority."""
        if cargo_id not in self.multimodal_cargo:
            return {}
        
        cargo = self.multimodal_cargo[cargo_id]
        rules = self._multimodal_rules.get(cargo.priority, {})
        
        recommended_mode = cargo.recommended_mode
        max_transit = rules.get("max_transit_hours", 168)
        
        # Find suitable aircraft if air transport needed
        suitable_aircraft = []
        if recommended_mode in [TransportMode.AIR, TransportMode.AIR_TRUCK, TransportMode.AIR_SEA_TRUCK]:
            for aircraft in self.aircraft.values():
                if aircraft.max_payload_lbs >= cargo.weight_lbs:
                    if aircraft.max_range_miles >= cargo.weight_lbs * 0.1:  # Simplified range check
                        suitable_aircraft.append({
                            "aircraft_id": aircraft.aircraft_id,
                            "name": aircraft.name,
                            "cost_per_mile": aircraft.cost_per_mile,
                            "max_payload_lbs": aircraft.max_payload_lbs,
                            "cruise_speed_mph": aircraft.cruise_speed_mph,
                        })
        
        # Find suitable vessels if sea transport needed
        suitable_vessels = []
        if recommended_mode in [TransportMode.SEA, TransportMode.SEA_TRUCK, TransportMode.AIR_SEA_TRUCK, TransportMode.SEA_RAIL]:
            for vessel in self.sea_vessels.values():
                if vessel.max_payload_lbs >= cargo.weight_lbs:
                    if not cargo.requires_reefer or vessel.has_reefer_plugs:
                        if not cargo.requires_heavy_lift or vessel.has_heavy_lift:
                            suitable_vessels.append({
                                "vessel_id": vessel.vessel_id,
                                "name": vessel.name,
                                "cost_per_nautical_mile": vessel.cost_per_nautical_mile,
                                "container_teus": vessel.container_teus,
                                "cruise_speed_knots": vessel.cruise_speed_knots,
                            })
        
        cargo.selected_mode = recommended_mode
        cargo.is_allocated = True
        
        return {
            "cargo_id": cargo_id,
            "name": cargo.name,
            "priority": cargo.priority.value,
            "recommended_mode": recommended_mode.value,
            "max_transit_hours": max_transit,
            "urgency_score": cargo.urgency_score,
            "suitable_aircraft": suitable_aircraft,
            "suitable_vessels": suitable_vessels,
            "cost_weight": rules.get("cost_weight", 0.5),
            "speed_weight": rules.get("speed_weight", 0.5),
        }
    
    def allocate_all_cargo(self) -> List[Dict[str, Any]]:
        """Allocate all pending cargo."""
        results = []
        for cargo_id in self.multimodal_cargo:
            if not self.multimodal_cargo[cargo_id].is_allocated:
                result = self.allocate_cargo(cargo_id)
                if result:
                    results.append(result)
        return results
    
    def analyze_multimodal(self) -> Dict[str, Any]:
        """Analyze multi-modal cargo allocation."""
        allocated = [c for c in self.multimodal_cargo.values() if c.is_allocated]
        pending = [c for c in self.multimodal_cargo.values() if not c.is_allocated]
        
        mode_counts: Dict[str, int] = {}
        for cargo in allocated:
            mode = cargo.selected_mode.value if cargo.selected_mode else "unallocated"
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        return {
            "total_cargo": len(self.multimodal_cargo),
            "allocated": len(allocated),
            "pending": len(pending),
            "mode_distribution": mode_counts,
            "total_weight_allocated": sum(c.weight_lbs for c in allocated),
            "cargo": [
                {
                    "cargo_id": c.cargo_id,
                    "name": c.name,
                    "priority": c.priority.value,
                    "selected_mode": c.selected_mode.value if c.selected_mode else None,
                    "weight_lbs": c.weight_lbs,
                    "is_allocated": c.is_allocated,
                }
                for c in self.multimodal_cargo.values()
            ],
        }
    
    # -------------------------------------------------------------------------
    # COMPREHENSIVE ANALYSIS
    # -------------------------------------------------------------------------
    
    def get_comprehensive_state(self) -> Dict[str, Any]:
        """Get comprehensive state of all logistics and transport systems."""
        return {
            "timestamp": datetime.now().isoformat(),
            "warehouses": {
                "total": len(self.warehouses),
                "networks": len(self.warehouse_networks),
                "total_capacity_sqft": sum(w.total_sqft for w in self.warehouses.values()),
                "optimal_locations": len(self.find_optimal_locations()),
            },
            "shipping": self.analyze_shipping_capabilities(),
            "aircraft": {
                "total": len(self.aircraft),
                "autonomous": len(self.find_autonomous_aircraft()),
                "vtol": len(self.find_vtol_aircraft()),
                "remote_capable": len(self.find_remote_capable_aircraft()),
                "total_payload_capacity": sum(a.max_payload_lbs for a in self.aircraft.values()),
                "by_type": {
                    ct.value: len(self.find_aircraft_by_type(ct))
                    for ct in CargoAircraftType
                    if self.find_aircraft_by_type(ct)
                },
            },
            "sea_transport": {
                "total_vessels": len(self.sea_vessels),
                "total_fleets": len(self.vessel_fleets),
                "total_container_capacity": sum(v.container_teus for v in self.sea_vessels.values()),
                "total_payload_capacity": sum(v.max_payload_lbs for v in self.sea_vessels.values()),
                "total_reefer_capacity": sum(v.reefer_capacity for v in self.sea_vessels.values()),
                "reefer_vessels": len(self.find_reefer_vessels()),
                "heavy_lift_vessels": len(self.find_heavy_lift_vessels()),
                "by_type": {
                    vt.value: len(self.find_vessels_by_type(vt))
                    for vt in SeaVesselType
                    if self.find_vessels_by_type(vt)
                },
            },
            "sea_routes": self.analyze_sea_routes(),
            "fleets": {
                fid: self.analyze_fleet(fid)
                for fid in self.fleets
            },
            "vessel_fleets": {
                fid: self.analyze_vessel_fleet(fid)
                for fid in self.vessel_fleets
            },
            "multimodal": self.analyze_multimodal(),
            "routes": self.analyze_routes(),
            "transport_companies": len(self.transport_companies),
            "cross_provider_apis": len(self.cross_provider_assistance),
            "summary": {
                "total_warehouse_locations": len(self.warehouses),
                "total_warehouse_capacity": sum(w.total_sqft for w in self.warehouses.values()),
                "total_aircraft": len(self.aircraft),
                "total_fleets": len(self.fleets),
                "total_sea_vessels": len(self.sea_vessels),
                "total_vessel_fleets": len(self.vessel_fleets),
                "total_routes": len(self.delivery_routes),
                "total_sea_routes": len(self.sea_routes),
                "total_shipping_services": len(self.shipping_services),
                "total_cross_provider_apis": len(self.cross_provider_assistance),
                "total_multimodal_cargo": len(self.multimodal_cargo),
            }
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

logistics_transport_engine = LogisticsTransportEngine()