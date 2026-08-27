#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Vehicle Collection & Management

Vehicle collection management system with color theory, usability tracking,
workshop/tuning, storage, rental, and transport logistics.

Features:
- Vehicle catalogue with detailed specifications
- Color theory engine (natural colors, niche shades, body+rim contrast)
- Usability case tracking (where/when driven, who's driving)
- Exclusive storage facility management
- Rental management for unused vehicles
- Workshop and tuning capabilities
- Vehicle transport logistics
- Model's uniqueness-based discovery algorithm
- Movie/lifestyle reference catalogue (mafia/gangster cars)

Color Philosophy:
- Abstract natural colors that aren't overbearing
- Niche shades that stand out without being flashy
- Beautiful contrast between neutral body and vibrant rims
- Nature-inspired palette (ocean blues, forest greens, volcanic grays)
- Quality through combination, not saturation

User Preferences (from childhood gaming):
- BMW i8 (favorite - Forza/Nostalgia)
- Acura TLX Type S in blue (Long Beach Blue Pearl / Apex Blue Pearl)
- VW Golf MK2 in blue
- Rivian R1T (truck)
- Mercedes Benz E500
- Passat VR6 in green
- Mafia/gangster movie cars
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.vehicle_collection")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class VehicleCategory(Enum):
    """Vehicle categories."""
    SPORTS_CAR = "sports_car"
    SUPERCAR = "supercar"
    HYPER_CAR = "hyper_car"
    SEDAN = "sedan"
    COUPE = "coupe"
    CONVERTIBLE = "convertible"
    TRUCK = "truck"
    SUV = "suv"
    WAGON = "wagon"
    HATCHBACK = "hatchback"
    CLASSIC = "classic"
    MUSCLE = "muscle"
    GRAND_TOURER = "grand_tourer"
    ELECTRIC = "electric"
    HYBRID = "hybrid"

class VehicleStatus(Enum):
    """Vehicle status."""
    ACTIVE = "active"
    IN_STORAGE = "in_storage"
    RENTED = "rented"
    IN_WORKSHOP = "in_workshop"
    IN_TRANSPORT = "in_transport"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"
    SHOW = "show"

class StorageType(Enum):
    """Storage facility types."""
    HOME_GARAGE = "home_garage"
    CLIMATE_CONTROLLED = "climate_controlled"
    EXCLUSIVE_VAULT = "exclusive_vault"
    DISPLAY_SHOWROOM = "display_showroom"
    SECURE_FACILITY = "secure_facility"
    UNDERGROUND = "underground"
    PRIVATE_COLLECTION = "private_collection"

class TuningStage(Enum):
    """Tuning/workshop stages."""
    STOCK = "stock"
    STAGE_1 = "stage_1"
    STAGE_2 = "stage_2"
    STAGE_3 = "stage_3"
    STAGE_4 = "stage_4"
    CUSTOM = "custom"

class ColorFamily(Enum):
    """Color families (nature-inspired)."""
    OCEAN_BLUE = "ocean_blue"
    FOREST_GREEN = "forest_green"
    VOLCANIC_GRAY = "volcanic_gray"
    DESERT_SAND = "desert_sand"
    MIDNIGHT_BLACK = "midnight_black"
    GLACIER_WHITE = "glacier_white"
    SUNSET_ORANGE = "sunset_orange"
    DEEP_PURPLE = "deep_purple"
    RACING_RED = "racing_red"
    COPPER_BRONZE = "copper_bronze"
    MILITARY_OLIVE = "military_olive"
    BURGUNDY_WINE = "burgundy_wine"

class DriveOccasion(Enum):
    """When the vehicle is driven."""
    DAILY_COMMUTE = "daily_commute"
    WEEKEND_CRUISING = "weekend_cruising"
    TRACK_DAY = "track_day"
    OFF_ROAD = "off_road"
    ROAD_TRIP = "road_trip"
    SPECIAL_OCCASION = "special_occasion"
    SHOW_EVENT = "show_event"
    NIGHT_DRIVES = "night_drives"
    RAINY_DAY = "rainy_day"
    DATE_NIGHT = "date_night"
    BUSINESS = "business"
    NOSTALGIA = "nostalgia"

class DriverProfile(Enum):
    """Who is driving."""
    OWNER = "owner"
    PARTNER = "partner"
    FRIEND = "friend"
    PROFESSIONAL_DRIVER = "professional_driver"
    VALET = "valet"
    MECHANIC = "mechanic"
    RENTER = "renter"
    DISPLAY_ONLY = "display_only"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class VehicleColor:
    """Vehicle color specification."""
    name: str
    color_family: ColorFamily
    hex_code: str
    is_metallic: bool = False
    is_pearl: bool = False
    is_matte: bool = False
    is_frozen: bool = False
    rim_color: str = "silver"
    rim_contrast: str = "complementary"
    notes: str = ""

@dataclass
class VehicleSpec:
    """Vehicle specifications."""
    make: str
    model: str
    year: int
    category: VehicleCategory
    engine: str
    horsepower: int
    torque: int
    transmission: str
    drivetrain: str
    zero_to_sixty: float
    top_speed: int
    fuel_type: str
    mpg_city: int = 0
    mpg_highway: int = 0
    weight: int = 0
    seating: int = 2
    price_new: float = 0
    price_current: float = 0

@dataclass
class Vehicle:
    """Vehicle in the collection."""
    vehicle_id: str
    name: str
    spec: VehicleSpec
    colors: List[VehicleColor] = field(default_factory=list)
    primary_color: Optional[VehicleColor] = None
    status: VehicleStatus = VehicleStatus.ACTIVE
    storage_type: Optional[StorageType] = None
    tuning_stage: TuningStage = TuningStage.STOCK
    mileage: int = 0
    purchase_date: str = ""
    purchase_price: float = 0
    current_value: float = 0
    vin: str = ""
    license_plate: str = ""
    insurance_policy: str = ""
    is_insured: bool = False
    occasions: List[DriveOccasion] = field(default_factory=list)
    approved_drivers: List[DriverProfile] = field(default_factory=list)
    notes: str = ""

@dataclass
class StorageFacility:
    """Storage facility for vehicles."""
    facility_id: str
    name: str
    storage_type: StorageType
    capacity: int = 10
    is_climate_controlled: bool = True
    is_security_24_7: bool = True
    is_insured: bool = True
    monthly_cost: float = 0
    vehicles_stored: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    address: str = ""
    notes: str = ""

@dataclass
class RentalRecord:
    """Vehicle rental record."""
    rental_id: str
    vehicle_id: str
    renter_name: str
    start_date: str
    end_date: str
    daily_rate: float
    total_amount: float
    deposit: float
    is_insured: bool = True
    mileage_limit: int = 0
    status: str = "active"
    notes: str = ""

@dataclass
class WorkshopMod:
    """Workshop modification record."""
    mod_id: str
    vehicle_id: str
    name: str
    category: str
    description: str
    cost: float
    installation_date: str = ""
    shop_name: str = ""
    warranty_months: int = 0
    is_reversible: bool = True
    notes: str = ""

@dataclass
class TransportRecord:
    """Vehicle transport logistics."""
    transport_id: str
    vehicle_id: str
    from_location: str
    to_location: str
    transport_type: str
    scheduled_date: str = ""
    completed_date: str = ""
    cost: float = 0
    status: str = "scheduled"
    notes: str = ""

@dataclass
class UniquenessScore:
    """Vehicle uniqueness score for discovery algorithm."""
    vehicle_id: str
    overall_score: float = 0
    exterior_design: float = 0
    interior_design: float = 0
    color_appeal: float = 0
    rarity: float = 0
    performance: float = 0
    usability: float = 0
    emotional_connection: float = 0
    childhood_relevance: float = 0
    movie_reference: float = 0
    notes: str = ""


# =============================================================================
# MAIN ENGINE
# =============================================================================

class VehicleCollectionEngine:
    """
    Vehicle collection management engine.
    
    Manages vehicle acquisition, storage, rental, tuning, transport,
    and discovery based on uniqueness scoring.
    """
    
    def __init__(self):
        self.vehicles: Dict[str, Vehicle] = {}
        self.storage_facilities: Dict[str, StorageFacility] = {}
        self.rentals: Dict[str, RentalRecord] = {}
        self.workshop_mods: Dict[str, WorkshopMod] = {}
        self.transports: Dict[str, TransportRecord] = {}
        self.uniqueness_scores: Dict[str, UniquenessScore] = {}
        
        self.color_palette: Dict[ColorFamily, List[VehicleColor]] = {
            ColorFamily.OCEAN_BLUE: [
                VehicleColor("Long Beach Blue Pearl", ColorFamily.OCEAN_BLUE, "#1E5AA8", is_pearl=True, rim_color="silver", rim_contrast="complementary", notes="Acura NSX supercar color"),
                VehicleColor("Apex Blue Pearl", ColorFamily.OCEAN_BLUE, "#2B6CB0", is_pearl=True, rim_color="gloss_black", rim_contrast="contrasting", notes="Acura Type S signature"),
                VehicleColor("Frozen Blue", ColorFamily.OCEAN_BLUE, "#4A90D9", is_frozen=True, rim_color="white", rim_contrast="complementary", notes="BMW i8 signature"),
                VehicleColor("Rivian Blue", ColorFamily.OCEAN_BLUE, "#3D7BBA", is_metallic=True, rim_color="black", rim_contrast="contrasting"),
            ],
            ColorFamily.FOREST_GREEN: [
                VehicleColor("British Racing Green", ColorFamily.FOREST_GREEN, "#004225", is_metallic=True, rim_color="gold", rim_contrast="complementary"),
                VehicleColor("Verdant Green", ColorFamily.FOREST_GREEN, "#2D5A27", is_metallic=True, rim_color="bronze", rim_contrast="complementary", notes="Passat VR6 natural green"),
                VehicleColor("Forest Green", ColorFamily.FOREST_GREEN, "#228B22", is_metallic=True, rim_color="black", rim_contrast="contrasting", notes="Rivian R1T"),
            ],
            ColorFamily.VOLCANIC_GRAY: [
                VehicleColor("Sophisto Gray", ColorFamily.VOLCANIC_GRAY, "#708090", is_metallic=True, rim_color="silver", rim_contrast="matching", notes="BMW i8 signature"),
                VehicleColor("Liquid Carbon", ColorFamily.VOLCANIC_GRAY, "#3D3D3D", is_metallic=True, rim_color="gloss_black", rim_contrast="matching", notes="Acura Type S"),
                VehicleColor("El Cap Granite", ColorFamily.VOLCANIC_GRAY, "#5A5A5A", is_metallic=True, rim_color="black", rim_contrast="matching", notes="Rivian R1T"),
                VehicleColor("Gotham Gray", ColorFamily.VOLCANIC_GRAY, "#4A4A4A", is_metallic=True, rim_color="copper", rim_contrast="contrasting", notes="Acura PMC Edition"),
            ],
            ColorFamily.GLACIER_WHITE: [
                VehicleColor("Crystal White Pearl", ColorFamily.GLACIER_WHITE, "#F8F8FF", is_pearl=True, rim_color="frozen_blue", rim_contrast="complementary", notes="BMW i8 signature"),
                VehicleColor("Platinum White Pearl", ColorFamily.GLACIER_WHITE, "#FAF0E6", is_pearl=True, rim_color="gloss_black", rim_contrast="contrasting", notes="Acura Type S"),
                VehicleColor("Glacier White", ColorFamily.GLACIER_WHITE, "#E8E8E8", is_metallic=True, rim_color="dark_graphite", rim_contrast="contrasting", notes="Rivian R1T"),
            ],
            ColorFamily.MIDNIGHT_BLACK: [
                VehicleColor("Majestic Black Pearl", ColorFamily.MIDNIGHT_BLACK, "#1C1C1C", is_pearl=True, rim_color="silver", rim_contrast="complementary", notes="Acura Type S"),
                VehicleColor("Midnight", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_metallic=True, rim_color="black", rim_contrast="matching", notes="Rivian R1T"),
            ],
        }
        
        self._init_default_storage()
        self._init_dream_vehicles()
    
    def _init_default_storage(self):
        """Initialize default storage facilities."""
        facilities = [
            StorageFacility(
                facility_id="vault_01",
                name="Primary Collection Vault",
                storage_type=StorageType.EXCLUSIVE_VAULT,
                capacity=20,
                is_climate_controlled=True,
                is_security_24_7=True,
                is_insured=True,
                monthly_cost=2500,
                features=["Climate Control", "24/7 Security", "Maintenance Bay", "Detail Bay", "Camera Monitoring", "Dehumidifier"],
            ),
            StorageFacility(
                facility_id="garage_home",
                name="Home Garage",
                storage_type=StorageType.HOME_GARAGE,
                capacity=4,
                is_climate_controlled=True,
                is_security_24_7=False,
                is_insured=True,
                monthly_cost=0,
                features=["Home Access", "Tool Storage", "Charging Station"],
            ),
            StorageFacility(
                facility_id="showroom",
                name="Private Showroom",
                storage_type=StorageType.DISPLAY_SHOWROOM,
                capacity=10,
                is_climate_controlled=True,
                is_security_24_7=True,
                is_insured=True,
                monthly_cost=3500,
                features=["LED Lighting", "Rotating Platforms", "Glass Display", "Security", "Climate Control"],
            ),
        ]
        for f in facilities:
            self.storage_facilities[f.facility_id] = f
    
    def _init_dream_vehicles(self):
        """Initialize user's dream vehicle catalogue."""
        dream_vehicles = [
            Vehicle(
                vehicle_id="bmw_i8_001",
                name="BMW i8",
                spec=VehicleSpec(
                    make="BMW", model="i8", year=2026, category=VehicleCategory.SUPERCAR,
                    engine="1.5L Turbo I3 + Electric Motor", horsepower=369, torque=420,
                    transmission="6-Speed Automatic", drivetrain="AWD", zero_to_sixty=4.2,
                    top_speed=155, fuel_type="PHEV", mpg_city=28, mpg_highway=30,
                    weight=3455, seating=2, price_new=165000, price_current=165000,
                ),
                colors=[
                    VehicleColor("Crystal White Pearl / Frozen Blue", ColorFamily.GLACIER_WHITE, "#F8F8FF", is_pearl=True, rim_color="frozen_blue", rim_contrast="complementary"),
                    VehicleColor("Sophisto Gray / Frozen Blue", ColorFamily.VOLCANIC_GRAY, "#708090", is_metallic=True, rim_color="frozen_blue", rim_contrast="complementary", notes="Signature combo"),
                ],
                primary_color=VehicleColor("Sophisto Gray / Frozen Blue", ColorFamily.VOLCANIC_GRAY, "#708090", is_metallic=True, rim_color="frozen_blue", rim_contrast="complementary"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.EXCLUSIVE_VAULT,
                occasions=[DriveOccasion.WEEKEND_CRUISING, DriveOccasion.SPECIAL_OCCASION, DriveOccasion.SHOW_EVENT, DriveOccasion.NOSTALGIA],
                notes="Childhood dream car. Forza and NFS Most Wanted inspired. Butterfly doors, hybrid supercar.",
            ),
            Vehicle(
                vehicle_id="acura_tlx_001",
                name="Acura TLX Type S",
                spec=VehicleSpec(
                    make="Acura", model="TLX Type S", year=2026, category=VehicleCategory.SEDAN,
                    engine="3.0L Turbo V6", horsepower=355, torque=354,
                    transmission="10-Speed Automatic", drivetrain="AWD (SH-AWD)", zero_to_sixty=4.7,
                    top_speed=155, fuel_type="Gasoline", mpg_city=19, mpg_highway=25,
                    weight=4200, seating=5, price_new=57000, price_current=57000,
                ),
                colors=[
                    VehicleColor("Long Beach Blue Pearl", ColorFamily.OCEAN_BLUE, "#1E5AA8", is_pearl=True, rim_color="silver", rim_contrast="complementary", notes="NSX supercar color - THE CHOICE"),
                    VehicleColor("Apex Blue Pearl", ColorFamily.OCEAN_BLUE, "#2B6CB0", is_pearl=True, rim_color="gloss_black", rim_contrast="contrasting", notes="Type S signature"),
                ],
                primary_color=VehicleColor("Long Beach Blue Pearl", ColorFamily.OCEAN_BLUE, "#1E5AA8", is_pearl=True, rim_color="silver", rim_contrast="complementary"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.HOME_GARAGE,
                occasions=[DriveOccasion.DAILY_COMMUTE, DriveOccasion.WEEKEND_CRUISING, DriveOccasion.DATE_NIGHT],
                notes="Childhood dream sedan. Long Beach Blue Pearl from NSX supercar. SH-AWD system.",
            ),
            Vehicle(
                vehicle_id="rivian_r1t_001",
                name="Rivian R1T",
                spec=VehicleSpec(
                    make="Rivian", model="R1T", year=2026, category=VehicleCategory.TRUCK,
                    engine="Quad Motor Electric", horsepower=835, torque=908,
                    transmission="1-Speed Direct Drive", drivetrain="AWD", zero_to_sixty=3.0,
                    top_speed=115, fuel_type="Electric", weight=7148, seating=5,
                    price_new=79990, price_current=79990,
                ),
                colors=[
                    VehicleColor("Forest Green", ColorFamily.FOREST_GREEN, "#228B22", is_metallic=True, rim_color="black", rim_contrast="contrasting", notes="Natural earth tone"),
                    VehicleColor("El Cap Granite", ColorFamily.VOLCANIC_GRAY, "#5A5A5A", is_metallic=True, rim_color="black", rim_contrast="matching"),
                ],
                primary_color=VehicleColor("Forest Green", ColorFamily.FOREST_GREEN, "#228B22", is_metallic=True, rim_color="black", rim_contrast="contrasting"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.HOME_GARAGE,
                occasions=[DriveOccasion.OFF_ROAD, DriveOccasion.ROAD_TRIP, DriveOccasion.WEEKEND_CRUISING],
                notes="Electric truck. Gear Tunnel storage. 11,000 lbs towing. Kick Turn feature.",
            ),
            Vehicle(
                vehicle_id="vw_golf_mk2_001",
                name="VW Golf MK2 GTI",
                spec=VehicleSpec(
                    make="Volkswagen", model="Golf MK2 GTI", year=1990, category=VehicleCategory.HATCHBACK,
                    engine="1.8L I4 8V", horsepower=112, torque=125,
                    transmission="5-Speed Manual", drivetrain="FWD", zero_to_sixty=8.5,
                    top_speed=125, fuel_type="Gasoline", mpg_city=22, mpg_highway=28,
                    weight=2100, seating=5, price_new=12000, price_current=25000,
                ),
                colors=[
                    VehicleColor("Bright Blue", ColorFamily.OCEAN_BLUE, "#4169E1", is_metallic=True, rim_color="silver", rim_contrast="complementary", notes="Classic MK2 blue"),
                ],
                primary_color=VehicleColor("Bright Blue", ColorFamily.OCEAN_BLUE, "#4169E1", is_metallic=True, rim_color="silver", rim_contrast="complementary"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.EXCLUSIVE_VAULT,
                occasions=[DriveOccasion.NOSTALGIA, DriveOccasion.WEEKEND_CRUISING, DriveOccasion.SHOW_EVENT],
                notes="Childhood NFS Most Wanted nostalgia. GameCube era. Classic hot hatch.",
            ),
            Vehicle(
                vehicle_id="mercedes_e500_001",
                name="Mercedes-Benz E500",
                spec=VehicleSpec(
                    make="Mercedes-Benz", model="E500", year=2005, category=VehicleCategory.SEDAN,
                    engine="5.0L V8", horsepower=302, torque=339,
                    transmission="7-Speed Automatic", drivetrain="RWD", zero_to_sixty=5.8,
                    top_speed=155, fuel_type="Gasoline", mpg_city=16, mpg_highway=23,
                    weight=3800, seating=5, price_new=58000, price_current=18000,
                ),
                colors=[
                    VehicleColor("Brilliant Silver", ColorFamily.VOLCANIC_GRAY, "#C0C0C0", is_metallic=True, rim_color="silver", rim_contrast="matching"),
                ],
                primary_color=VehicleColor("Brilliant Silver", ColorFamily.VOLCANIC_GRAY, "#C0C0C0", is_metallic=True, rim_color="silver", rim_contrast="matching"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.EXCLUSIVE_VAULT,
                occasions=[DriveOccasion.BUSINESS, DriveOccasion.DATE_NIGHT, DriveOccasion.SPECIAL_OCCASION],
                notes="Classic Mercedes V8 luxury. W211 generation. Smooth and refined.",
            ),
            Vehicle(
                vehicle_id="passat_vr6_001",
                name="VW Passat VR6",
                spec=VehicleSpec(
                    make="Volkswagen", model="Passat VR6", year=2003, category=VehicleCategory.SEDAN,
                    engine="2.8L VR6", horsepower=190, torque=206,
                    transmission="5-Speed Tiptronic", drivetrain="FWD", zero_to_sixty=7.2,
                    top_speed=140, fuel_type="Gasoline", mpg_city=18, mpg_highway=25,
                    weight=3300, seating=5, price_new=28000, price_current=12000,
                ),
                colors=[
                    VehicleColor("Verdant Green", ColorFamily.FOREST_GREEN, "#2D5A27", is_metallic=True, rim_color="bronze", rim_contrast="complementary", notes="Natural green - THE CHOICE"),
                ],
                primary_color=VehicleColor("Verdant Green", ColorFamily.FOREST_GREEN, "#2D5A27", is_metallic=True, rim_color="bronze", rim_contrast="complementary"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.EXCLUSIVE_VAULT,
                occasions=[DriveOccasion.DAILY_COMMUTE, DriveOccasion.WEEKEND_CRUISING],
                notes="VR6 rumble. Green machine. Wagon practicality with sports car sound.",
            ),
            # BMW 320i M Sport - Compact sports sedan
            Vehicle(
                vehicle_id="bmw_320i_001",
                name="BMW 320i M Sport",
                spec=VehicleSpec(
                    make="BMW", model="320i M Sport", year=2025, category=VehicleCategory.SEDAN,
                    engine="2.0L Turbo I4", horsepower=184, torque=221,
                    transmission="8-Speed Steptronic Auto", drivetrain="RWD", zero_to_sixty=7.4,
                    top_speed=146, fuel_type="Gasoline", mpg_city=31, mpg_highway=42,
                    weight=3500, seating=5, price_new=42000, price_current=42000,
                ),
                colors=[
                    VehicleColor("Black Sapphire Metallic", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_metallic=True, rim_color="silver", rim_contrast="complementary", notes="Sleek and classy"),
                    VehicleColor("Arctic Race Blue Metallic", ColorFamily.OCEAN_BLUE, "#1E5AA8", is_metallic=True, rim_color="silver", rim_contrast="complementary", notes="New for 2025"),
                    VehicleColor("Fire Red Metallic", ColorFamily.RACING_RED, "#CC0000", is_metallic=True, rim_color="silver", rim_contrast="complementary", notes="New for 2025"),
                    VehicleColor("Mineral White Metallic", ColorFamily.GLACIER_WHITE, "#F0F0F0", is_metallic=True, rim_color="silver", rim_contrast="complementary"),
                ],
                primary_color=VehicleColor("Black Sapphire Metallic", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_metallic=True, rim_color="silver", rim_contrast="complementary", notes="Sleek and classy"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.HOME_GARAGE,
                tuning_stage=TuningStage.STAGE_1,
                occasions=[DriveOccasion.DAILY_COMMUTE, DriveOccasion.BUSINESS, DriveOccasion.DATE_NIGHT],
                approved_drivers=[DriverProfile.OWNER, DriverProfile.PARTNER],
                notes="Entry-level 3 Series. Black Sapphire M Sport. Dynamic benchmark executive sedan. RWD purity.",
            ),
            # Audi S1 Quattro - Hot hatch
            Vehicle(
                vehicle_id="audi_s1_001",
                name="Audi S1 Quattro",
                spec=VehicleSpec(
                    make="Audi", model="S1 Quattro", year=2015, category=VehicleCategory.HATCHBACK,
                    engine="2.0L TFSI Turbo I4", horsepower=228, torque=273,
                    transmission="6-Speed Manual", drivetrain="Quattro AWD", zero_to_sixty=5.8,
                    top_speed=155, fuel_type="Gasoline", mpg_city=26, mpg_highway=40,
                    weight=3120, seating=4, price_new=34000, price_current=18000,
                ),
                colors=[
                    VehicleColor("Misano Red Pearl", ColorFamily.RACING_RED, "#C41E3A", is_pearl=True, rim_color="silver", rim_contrast="complementary"),
                    VehicleColor("Daytona Gray Pearl", ColorFamily.VOLCANIC_GRAY, "#708090", is_pearl=True, rim_color="silver", rim_contrast="complementary"),
                    VehicleColor("Glacier White Metallic", ColorFamily.GLACIER_WHITE, "#F0F0F0", is_metallic=True, rim_color="silver", rim_contrast="complementary"),
                    VehicleColor("Mythos Black Metallic", ColorFamily.MIDNIGHT_BLACK, "#1C1C1C", is_metallic=True, rim_color="silver", rim_contrast="complementary"),
                ],
                primary_color=VehicleColor("Daytona Gray Pearl", ColorFamily.VOLCANIC_GRAY, "#708090", is_pearl=True, rim_color="silver", rim_contrast="complementary"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.HOME_GARAGE,
                tuning_stage=TuningStage.STAGE_1,
                occasions=[DriveOccasion.DAILY_COMMUTE, DriveOccasion.WEEKEND_CRUISING, DriveOccasion.NOSTALGIA],
                approved_drivers=[DriverProfile.OWNER],
                notes="Compact hot hatch. Quattro AWD. 228 HP from 2.0L. Rally-inspired. Fun daily driver.",
            ),
            Vehicle(
                vehicle_id="mafia_s600_001",
                name="1999 Mercedes-Benz S600",
                spec=VehicleSpec(
                    make="Mercedes-Benz", model="S600", year=1999, category=VehicleCategory.SEDAN,
                    engine="5.8L V12", horsepower=362, torque=391,
                    transmission="5-Speed Automatic", drivetrain="RWD", zero_to_sixty=6.0,
                    top_speed=155, fuel_type="Gasoline", mpg_city=13, mpg_highway=18,
                    weight=4400, seating=5, price_new=95000, price_current=25000,
                ),
                colors=[
                    VehicleColor("Brilliant Black", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_metallic=True, rim_color="chrome", rim_contrast="complementary", notes="The mafia choice"),
                ],
                primary_color=VehicleColor("Brilliant Black", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_metallic=True, rim_color="chrome", rim_contrast="complementary"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.EXCLUSIVE_VAULT,
                occasions=[DriveOccasion.SPECIAL_OCCASION, DriveOccasion.NIGHT_DRIVES],
                notes="The Godfather, Goodfellas, Scarface. Classic mafia sedan. V12 power.",
            ),
            # Ram 1500 TRX SRT - Supertruck
            Vehicle(
                vehicle_id="ram_trx_001",
                name="Ram 1500 TRX SRT",
                spec=VehicleSpec(
                    make="Ram", model="1500 TRX SRT", year=2027, category=VehicleCategory.TRUCK,
                    engine="6.2L Supercharged HEMI V8", horsepower=777, torque=680,
                    transmission="8-Speed Automatic", drivetrain="4WD", zero_to_sixty=3.5,
                    top_speed=118, fuel_type="Gasoline", mpg_city=12, mpg_highway=15,
                    weight=6350, seating=5, price_new=99995, price_current=99995,
                ),
                colors=[
                    VehicleColor("Diamond Black Crystal", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_pearl=True, rim_color="satin_black", rim_contrast="matching", notes="Launch edition with Flame Red stripe"),
                    VehicleColor("Anvil Gray", ColorFamily.VOLCANIC_GRAY, "#5A5A5A", is_metallic=True, rim_color="satin_titanium", rim_contrast="complementary", notes="Launch edition exclusive"),
                    VehicleColor("Flame Red", ColorFamily.RACING_RED, "#CC0000", is_metallic=True, rim_color="satin_black", rim_contrast="contrasting"),
                    VehicleColor("Glacier White", ColorFamily.GLACIER_WHITE, "#E8E8E8", is_metallic=True, rim_color="satin_black", rim_contrast="contrasting"),
                ],
                primary_color=VehicleColor("Diamond Black Crystal", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_pearl=True, rim_color="satin_black", rim_contrast="matching", notes="Launch edition with Flame Red stripe"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.EXCLUSIVE_VAULT,
                occasions=[DriveOccasion.OFF_ROAD, DriveOccasion.WEEKEND_CRUISING, DriveOccasion.SHOW_EVENT],
                notes="Most Powerful Production Gas Off-Road Truck Ever. 777 HP / 680 lb-ft. 3.5s 0-60. 13in front/14in rear suspension travel. 35in tires. Hellcat HEMI.",
            ),
            # Nissan Titan XD Cummins - Diesel beast
            Vehicle(
                vehicle_id="nissan_titan_cummins_001",
                name="Nissan Titan XD Cummins",
                spec=VehicleSpec(
                    make="Nissan", model="Titan XD", year=2025, category=VehicleCategory.TRUCK,
                    engine="5.0L Cummins V8 Turbo Diesel", horsepower=310, torque=555,
                    transmission="6-Speed Automatic", drivetrain="4WD", zero_to_sixty=7.5,
                    top_speed=115, fuel_type="Diesel", mpg_city=18, mpg_highway=21,
                    weight=6500, seating=5, price_new=52000, price_current=52000,
                ),
                colors=[
                    VehicleColor("Brilliant Silver", ColorFamily.VOLCANIC_GRAY, "#C0C0C0", is_metallic=True, rim_color="chrome", rim_contrast="complementary"),
                    VehicleColor("Deep Blue Pearl", ColorFamily.OCEAN_BLUE, "#1E3A5F", is_pearl=True, rim_color="silver", rim_contrast="complementary"),
                    VehicleColor("Glacier White", ColorFamily.GLACIER_WHITE, "#E8E8E8", is_metallic=True, rim_color="dark_graphite", rim_contrast="contrasting"),
                    VehicleColor("Super Black", ColorFamily.MIDNIGHT_BLACK, "#0D0D0D", is_metallic=True, rim_color="black", rim_contrast="matching"),
                ],
                primary_color=VehicleColor("Deep Blue Pearl", ColorFamily.OCEAN_BLUE, "#1E3A5F", is_pearl=True, rim_color="silver", rim_contrast="complementary"),
                status=VehicleStatus.RESERVED, storage_type=StorageType.HOME_GARAGE,
                occasions=[DriveOccasion.OFF_ROAD, DriveOccasion.ROAD_TRIP, DriveOccasion.WEEKEND_CRUISING],
                notes="Cummins 5.0L V8 Turbo Diesel. 555 lb-ft torque. 12,300 lbs towing. Legendary diesel reliability.",
            ),
        ]
        
        for vehicle in dream_vehicles:
            self.vehicles[vehicle.vehicle_id] = vehicle
            self._calculate_uniqueness(vehicle)
    
    # -------------------------------------------------------------------------
    # VEHICLE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_vehicle(self, vehicle: Vehicle) -> Vehicle:
        """Add a vehicle to the collection."""
        self.vehicles[vehicle.vehicle_id] = vehicle
        self._calculate_uniqueness(vehicle)
        return vehicle
    
    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get a vehicle by ID."""
        return self.vehicles.get(vehicle_id)
    
    def get_vehicles_by_status(self, status: VehicleStatus) -> List[Vehicle]:
        """Get vehicles by status."""
        return [v for v in self.vehicles.values() if v.status == status]
    
    def get_vehicles_by_category(self, category: VehicleCategory) -> List[Vehicle]:
        """Get vehicles by category."""
        return [v for v in self.vehicles.values() if v.spec.category == category]
    
    # -------------------------------------------------------------------------
    # STORAGE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_storage_facility(self, facility: StorageFacility) -> StorageFacility:
        """Add a storage facility."""
        self.storage_facilities[facility.facility_id] = facility
        return facility
    
    def get_storage_facility(self, facility_id: str) -> Optional[StorageFacility]:
        """Get a storage facility."""
        return self.storage_facilities.get(facility_id)
    
    # -------------------------------------------------------------------------
    # RENTAL MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_rental(self, rental: RentalRecord) -> RentalRecord:
        """Add a rental record."""
        self.rentals[rental.rental_id] = rental
        vehicle = self.vehicles.get(rental.vehicle_id)
        if vehicle:
            vehicle.status = VehicleStatus.RENTED
        return rental
    
    def get_active_rentals(self) -> List[RentalRecord]:
        """Get active rentals."""
        return [r for r in self.rentals.values() if r.status == "active"]
    
    # -------------------------------------------------------------------------
    # WORKSHOP/TUNING
    # -------------------------------------------------------------------------
    
    def add_modification(self, mod: WorkshopMod) -> WorkshopMod:
        """Add a workshop modification."""
        self.workshop_mods[mod.mod_id] = mod
        return mod
    
    def tune_vehicle(self, vehicle_id: str, stage: TuningStage) -> Optional[Vehicle]:
        """Set tuning stage for a vehicle."""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id].tuning_stage = stage
            return self.vehicles[vehicle_id]
        return None
    
    # -------------------------------------------------------------------------
    # TRANSPORT LOGISTICS
    # -------------------------------------------------------------------------
    
    def add_transport(self, transport: TransportRecord) -> TransportRecord:
        """Add a transport record."""
        self.transports[transport.transport_id] = transport
        vehicle = self.vehicles.get(transport.vehicle_id)
        if vehicle:
            vehicle.status = VehicleStatus.IN_TRANSPORT
        return transport
    
    # -------------------------------------------------------------------------
    # UNIQUENESS SCORING
    # -------------------------------------------------------------------------
    
    def _calculate_uniqueness(self, vehicle: Vehicle) -> UniquenessScore:
        """Calculate uniqueness score for a vehicle."""
        score = UniquenessScore(vehicle_id=vehicle.vehicle_id)
        
        if vehicle.spec.category == VehicleCategory.SUPERCAR:
            score.exterior_design = 95
        elif vehicle.spec.category == VehicleCategory.SPORTS_CAR:
            score.exterior_design = 88
        elif vehicle.spec.category == VehicleCategory.HYPER_CAR:
            score.exterior_design = 99
        elif vehicle.spec.category == VehicleCategory.CLASSIC:
            score.exterior_design = 90
        else:
            score.exterior_design = 75
        
        if vehicle.spec.price_new > 100000:
            score.interior_design = 92
        elif vehicle.spec.price_new > 50000:
            score.interior_design = 85
        else:
            score.interior_design = 78
        
        if vehicle.primary_color:
            if vehicle.primary_color.is_pearl:
                score.color_appeal = 90
            elif vehicle.primary_color.is_frozen:
                score.color_appeal = 88
            elif vehicle.primary_color.is_metallic:
                score.color_appeal = 82
            else:
                score.color_appeal = 75
            if vehicle.primary_color.color_family in [ColorFamily.OCEAN_BLUE, ColorFamily.FOREST_GREEN, ColorFamily.VOLCANIC_GRAY]:
                score.color_appeal += 5
        
        if vehicle.spec.year < 2000:
            score.rarity = 85
        elif vehicle.spec.price_new > 150000:
            score.rarity = 90
        elif vehicle.spec.price_new > 80000:
            score.rarity = 80
        else:
            score.rarity = 65
        
        if vehicle.spec.horsepower > 500:
            score.performance = 95
        elif vehicle.spec.horsepower > 300:
            score.performance = 85
        elif vehicle.spec.horsepower > 200:
            score.performance = 75
        else:
            score.performance = 65
        
        if vehicle.spec.seating >= 4:
            score.usability = 85
        elif vehicle.spec.seating == 2:
            score.usability = 70
        else:
            score.usability = 60
        
        emotional_bonus = 0
        if "BMW i8" in vehicle.name:
            emotional_bonus = 15
        elif "Acura" in vehicle.spec.make:
            emotional_bonus = 12
        elif "Golf MK2" in vehicle.name:
            emotional_bonus = 10
        elif "Passat VR6" in vehicle.name:
            emotional_bonus = 8
        elif "Rivian" in vehicle.spec.make:
            emotional_bonus = 5
        score.emotional_connection = min(100, 70 + emotional_bonus)
        
        if vehicle.spec.year < 2000:
            score.childhood_relevance = 90
        elif "i8" in vehicle.name or "Golf" in vehicle.name:
            score.childhood_relevance = 85
        else:
            score.childhood_relevance = 60
        
        if "S600" in vehicle.name or "E500" in vehicle.spec.model:
            score.movie_reference = 90
        else:
            score.movie_reference = 50
        
        score.overall_score = (
            score.exterior_design * 0.20 +
            score.interior_design * 0.10 +
            score.color_appeal * 0.20 +
            score.rarity * 0.10 +
            score.performance * 0.15 +
            score.usability * 0.05 +
            score.emotional_connection * 0.10 +
            score.childhood_relevance * 0.05 +
            score.movie_reference * 0.05
        )
        
        self.uniqueness_scores[vehicle.vehicle_id] = score
        return score
    
    def get_top_vehicles(self, count: int = 5) -> List[UniquenessScore]:
        """Get top vehicles by uniqueness score."""
        scores = sorted(self.uniqueness_scores.values(), key=lambda x: x.overall_score, reverse=True)
        return scores[:count]
    
    def get_uniqueness_score(self, vehicle_id: str) -> Optional[UniquenessScore]:
        """Get uniqueness score for a vehicle."""
        return self.uniqueness_scores.get(vehicle_id)
    
    # -------------------------------------------------------------------------
    # PORTFOLIO ANALYSIS
    # -------------------------------------------------------------------------
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get comprehensive collection summary."""
        total_vehicles = len(self.vehicles)
        total_value = sum(v.current_value for v in self.vehicles.values())
        
        by_category: Dict[str, int] = {}
        for vehicle in self.vehicles.values():
            cat = vehicle.spec.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        by_status: Dict[str, int] = {}
        for vehicle in self.vehicles.values():
            status = vehicle.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        active_rentals = self.get_active_rentals()
        monthly_rental_income = sum(r.total_amount / 30 for r in active_rentals)
        total_storage_cost = sum(f.monthly_cost for f in self.storage_facilities.values())
        
        top_vehicles = self.get_top_vehicles(3)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_vehicles": total_vehicles,
            "total_collection_value": total_value,
            "by_category": by_category,
            "by_status": by_status,
            "active_rentals": len(active_rentals),
            "monthly_rental_income": monthly_rental_income,
            "monthly_storage_cost": total_storage_cost,
            "storage_facilities": len(self.storage_facilities),
            "total_modifications": len(self.workshop_mods),
            "top_vehicles": [
                {
                    "name": self.vehicles[s.vehicle_id].name if s.vehicle_id in self.vehicles else "",
                    "score": round(s.overall_score, 1),
                    "category": self.vehicles[s.vehicle_id].spec.category.value if s.vehicle_id in self.vehicles else "",
                }
                for s in top_vehicles
            ],
        }


# =============================================================================
# VEHICLE MARKETPLACE, PURCHASE & MAINTENANCE APIS
# =============================================================================

class DealershipType(Enum):
    """Types of dealerships."""
    AUTHORIZED = "authorized"
    INDEPENDENT = "independent"
    SPECIALTY = "specialty"
    LUXURY = "luxury"
    CLASSIC = "classic"
    ONLINE = "online"
    AUCTION = "auction"
    PRIVATE_SELLER = "private_seller"

class ServiceType(Enum):
    """Types of maintenance services."""
    OIL_CHANGE = "oil_change"
    TIRE_ROTATION = "tire_rotation"
    BRAKE_SERVICE = "brake_service"
    ENGINE_TUNE = "engine_tune"
    TRANSMISSION_SERVICE = "transmission_service"
    COOLANT_FLUSH = "coolant_flush"
    DETAILING = "detailing"
    INSPECTION = "inspection"
    ALIGNMENT = "alignment"
    BATTERY_SERVICE = "battery_service"
    FLUID_CHECK = "fluid_check"
    SOFTWARE_UPDATE = "software_update"
    MODIFICATION_INSTALL = "modification_install"
    SAFETY_INSPECTION = "safety_inspection"
    EMISSIONS_TEST = "emissions_test"

class InsuranceType(Enum):
    """Types of vehicle insurance."""
    LIABILITY = "liability"
    COLLISION = "collision"
    COMPREHENSIVE = "comprehensive"
    AGREED_VALUE = "agreed_value"
    COLLECTOR = "collector"
    AGREED_MILEAGE = "agreed_mileage"


@dataclass
class Dealership:
    """Vehicle dealership."""
    dealership_id: str
    name: str
    dealership_type: DealershipType
    address: str
    city: str
    state: str
    phone: str
    email: str
    website: str
    specialties: List[str] = field(default_factory=list)
    rating: float = 0
    is_verified: bool = False
    inventory: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class PurchaseOrder:
    """Vehicle purchase order."""
    order_id: str
    vehicle_id: str
    buyer_name: str
    dealership_id: str
    offer_price: float
    final_price: float
    down_payment: float
    financing: bool = False
    loan_term_months: int = 0
    interest_rate: float = 0
    trade_in_value: float = 0
    tax_rate: float = 0
    registration_fee: float = 0
    delivery_fee: float = 0
    total_cost: float = 0
    order_date: str = ""
    delivery_date: str = ""
    status: str = "pending"  # pending, approved, financed, delivered, complete
    notes: str = ""


@dataclass
class MaintenanceRecord:
    """Vehicle maintenance record."""
    record_id: str
    vehicle_id: str
    service_type: ServiceType
    service_date: str
    next_service_date: str
    mileage_at_service: int
    cost: float
    provider: str
    provider_id: str
    description: str
    parts_replaced: List[str] = field(default_factory=list)
    warranty_months: int = 0
    is_warranty: bool = False
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    notes: str = ""


@dataclass
class InsurancePolicy:
    """Vehicle insurance policy."""
    policy_id: str
    vehicle_id: str
    provider: str
    insurance_type: InsuranceType
    monthly_premium: float
    deductible: float
    coverage_amount: float
    start_date: str
    end_date: str
    mileage_limit: int = 0
    agreed_value: float = 0
    is_active: bool = True
    notes: str = ""


@dataclass
class StorageBooking:
    """Storage facility booking."""
    booking_id: str
    vehicle_id: str
    facility_id: str
    start_date: str
    end_date: str
    monthly_rate: float
    is_insured: bool = True
    needs_charging: bool = False
    needs_maintenance: bool = False
    access_level: str = "owner"  # owner, partner, manager, none
    status: str = "active"
    notes: str = ""


# =============================================================================
# VEHICLE MARKETPLACE ENGINE
# =============================================================================

class VehicleMarketplaceEngine:
    """
    Vehicle marketplace engine for purchasing, storage, and maintenance.
    
    Features:
    - Dealership discovery and verification
    - Purchase order creation and financing
    - Secure storage facility selection and booking
    - Maintenance scheduling and tracking
    - Insurance policy management
    - Full vehicle lifecycle management
    """
    
    def __init__(self):
        self.dealerships: Dict[str, Dealership] = {}
        self.purchase_orders: Dict[str, PurchaseOrder] = {}
        self.maintenance_records: Dict[str, MaintenanceRecord] = {}
        self.insurance_policies: Dict[str, InsurancePolicy] = {}
        self.storage_bookings: Dict[str, StorageBooking] = {}
        
        self._init_dealerships()
    
    def _init_dealerships(self):
        """Initialize trusted dealerships."""
        dealerships = [
            Dealership(
                dealership_id="bmw_premier",
                name="Premier BMW of Miami",
                dealership_type=DealershipType.AUTHORIZED,
                address="1200 Biscayne Blvd",
                city="Miami", state="FL",
                phone="305-555-0100",
                email="sales@premierbmw.com",
                website="https://premierbmw.com",
                specialties=["BMW", "BMW M", "BMW i"],
                rating=4.8,
                is_verified=True,
                notes="Authorized BMW dealer. Full inventory. Service center on-site.",
            ),
            Dealership(
                dealership_id="acura_downtown",
                name="Downtown Acura",
                dealership_type=DealershipType.AUTHORIZED,
                address="456 Federal Hwy",
                city="Miami", state="FL",
                phone="305-555-0200",
                email="sales@downtownacura.com",
                website="https://downtownacura.com",
                specialties=["Acura", "Acura Type S", "Acura NSX"],
                rating=4.7,
                is_verified=True,
                notes="Authorized Acura dealer. Type S specialist. SH-AWD expertise.",
            ),
            Dealership(
                dealership_id="rivian_space",
                name="Rivian Space Miami",
                dealership_type=DealershipType.AUTHORIZED,
                address="789 Electric Ave",
                city="Miami", state="FL",
                phone="305-555-0300",
                email="hello@rivianmiami.com",
                website="https://rivian.com/locations/miami",
                specialties=["Rivian", "Electric", "Adventure"],
                rating=4.9,
                is_verified=True,
                notes="Direct-to-consumer EV brand. Adventure Gear Tunnel accessories.",
            ),
            Dealership(
                dealership_id="mercedes_classic",
                name="Classic Mercedes Motorcars",
                dealership_type=DealershipType.SPECIALTY,
                address="321 Heritage Dr",
                city="Miami", state="FL",
                phone="305-555-0400",
                email="sales@classicmercedes.com",
                website="https://classicmercedes.com",
                specialties=["Mercedes-Benz", "Classic Mercedes", "AMG"],
                rating=4.6,
                is_verified=True,
                notes="Specializes in vintage and modern Mercedes. W211 W140 expert.",
            ),
            Dealership(
                dealership_id="vw_garage",
                name="VW Garage Miami",
                dealership_type=DealershipType.INDEPENDENT,
                address="555 Import Ln",
                city="Miami", state="FL",
                phone="305-555-0500",
                email="sales@vwgarage.com",
                website="https://vwgaragemiami.com",
                specialties=["Volkswagen", "MK2 Specialist", "VR6"],
                rating=4.5,
                is_verified=True,
                notes="Independent VW specialist. MK2 Golf expert. VR6 builds.",
            ),
            Dealership(
                dealership_id="audi_sport",
                name="Audi Sport Miami",
                dealership_type=DealershipType.AUTHORIZED,
                address="888 Quattro Blvd",
                city="Miami", state="FL",
                phone="305-555-0600",
                email="sales@audisportmiami.com",
                website="https://audisportmiami.com",
                specialties=["Audi", "Audi S", "Audi RS", "Quattro"],
                rating=4.7,
                is_verified=True,
                notes="Authorized Audi dealer. Quattro AWD specialist. S1 available.",
            ),
            Dealership(
                dealership_id="nissan_diesel",
                name="Nissan Diesel Performance",
                dealership_type=DealershipType.SPECIALTY,
                address="222 Diesel Way",
                city="Miami", state="FL",
                phone="305-555-0700",
                email="sales@nissandiesel.com",
                website="https://nissandiesel.com",
                specialties=["Nissan", "Titan XD", "Cummins Diesel"],
                rating=4.4,
                is_verified=True,
                notes="Cummins diesel specialist. Titan XD 5.0L expert. Towing builds.",
            ),
            Dealership(
                dealership_id="ram_srt",
                name="Ram SRT Headquarters",
                dealership_type=DealershipType.SPECIALTY,
                address="999 HEMI Rd",
                city="Miami", state="FL",
                phone="305-555-0800",
                email="sales@ramsrt.com",
                website="https://ramsrt.com",
                specialties=["Ram", "TRX", "SRT", "HEMI"],
                rating=4.8,
                is_verified=True,
                notes="Ram SRT specialist. TRX allocation priority. Hellcat HEMI builds.",
            ),
        ]
        for d in dealerships:
            self.dealerships[d.dealership_id] = d
    
    # -------------------------------------------------------------------------
    # DEALERSHIP DISCOVERY
    # -------------------------------------------------------------------------
    
    def find_dealerships(self, brand: str = None, specialty: str = None) -> List[Dealership]:
        """Find dealerships by brand or specialty."""
        results = []
        for d in self.dealerships.values():
            if brand and brand.lower() in [s.lower() for s in d.specialties]:
                results.append(d)
            elif specialty and specialty.lower() in [s.lower() for s in d.specialties]:
                results.append(d)
            elif not brand and not specialty:
                results.append(d)
        return results
    
    def get_dealership(self, dealership_id: str) -> Optional[Dealership]:
        """Get a dealership by ID."""
        return self.dealerships.get(dealership_id)
    
    def get_verified_dealerships(self) -> List[Dealership]:
        """Get verified dealerships only."""
        return [d for d in self.dealerships.values() if d.is_verified]
    
    # -------------------------------------------------------------------------
    # PURCHASE ORDER MANAGEMENT
    # -------------------------------------------------------------------------
    
    def create_purchase_order(self, vehicle_id: str, buyer_name: str,
                               dealership_id: str, offer_price: float,
                               down_payment: float = 0,
                               financing: bool = False,
                               loan_term_months: int = 60,
                               interest_rate: float = 0.05,
                               trade_in_value: float = 0,
                               tax_rate: float = 0.07) -> PurchaseOrder:
        """Create a vehicle purchase order."""
        # Calculate total cost
        tax_amount = offer_price * tax_rate
        registration_fee = 500
        delivery_fee = 1500
        
        if financing:
            loan_amount = offer_price - down_payment - trade_in_value + tax_amount + registration_fee + delivery_fee
            monthly_rate = interest_rate / 12
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**loan_term_months) / ((1 + monthly_rate)**loan_term_months - 1)
            total_cost = down_payment + trade_in_value + (monthly_payment * loan_term_months) + tax_amount + registration_fee + delivery_fee
        else:
            total_cost = offer_price + tax_amount + registration_fee + delivery_fee - trade_in_value
        
        order = PurchaseOrder(
            order_id=f"po_{vehicle_id}_{int(time.time())}",
            vehicle_id=vehicle_id,
            buyer_name=buyer_name,
            dealership_id=dealership_id,
            offer_price=offer_price,
            final_price=offer_price,
            down_payment=down_payment,
            financing=financing,
            loan_term_months=loan_term_months,
            interest_rate=interest_rate,
            trade_in_value=trade_in_value,
            tax_rate=tax_rate,
            registration_fee=registration_fee,
            delivery_fee=delivery_fee,
            total_cost=total_cost,
            order_date=datetime.now().isoformat(),
            status="pending",
        )
        
        self.purchase_orders[order.order_id] = order
        return order
    
    def approve_purchase(self, order_id: str) -> Optional[PurchaseOrder]:
        """Approve a purchase order."""
        if order_id in self.purchase_orders:
            order = self.purchase_orders[order_id]
            order.status = "approved"
            return order
        return None
    
    def get_purchase_orders_by_status(self, status: str) -> List[PurchaseOrder]:
        """Get purchase orders by status."""
        return [o for o in self.purchase_orders.values() if o.status == status]
    
    # -------------------------------------------------------------------------
    # MAINTENANCE SCHEDULING
    # -------------------------------------------------------------------------
    
    def schedule_maintenance(self, vehicle_id: str, service_type: ServiceType,
                              service_date: str, provider_id: str,
                              description: str = "",
                              mileage_at_service: int = 0) -> MaintenanceRecord:
        """Schedule vehicle maintenance."""
        # Calculate next service date based on type
        service_durations = {
            ServiceType.OIL_CHANGE: 90,
            ServiceType.TIRE_ROTATION: 180,
            ServiceType.BRAKE_SERVICE: 365,
            ServiceType.ENGINE_TUNE: 180,
            ServiceType.TRANSMISSION_SERVICE: 365,
            ServiceType.COOLANT_FLUSH: 365,
            ServiceType.DETAILING: 90,
            ServiceType.INSPECTION: 180,
            ServiceType.ALIGNMENT: 180,
            ServiceType.BATTERY_SERVICE: 365,
            ServiceType.FLUID_CHECK: 90,
            ServiceType.SOFTWARE_UPDATE: 180,
            ServiceType.MODIFICATION_INSTALL: 0,
            ServiceType.SAFETY_INSPECTION: 365,
            ServiceType.EMISSIONS_TEST: 365,
        }
        
        days = service_durations.get(service_type, 180)
        next_date = (datetime.fromisoformat(service_date) + timedelta(days=days)).isoformat()
        
        provider = self.dealerships.get(provider_id, Dealership(
            provider_id, "Independent Shop", DealershipType.INDEPENDENT,
            "", "", "", "", "", "", [], 0, False
        ))
        
        record = MaintenanceRecord(
            record_id=f"maint_{vehicle_id}_{int(time.time())}",
            vehicle_id=vehicle_id,
            service_type=service_type,
            service_date=service_date,
            next_service_date=next_date,
            mileage_at_service=mileage_at_service,
            cost=0,
            provider=provider.name,
            provider_id=provider_id,
            description=description,
            status="scheduled",
        )
        
        self.maintenance_records[record.record_id] = record
        return record
    
    def get_upcoming_maintenance(self, vehicle_id: str) -> List[MaintenanceRecord]:
        """Get upcoming maintenance for a vehicle."""
        return [m for m in self.maintenance_records.values() 
                if m.vehicle_id == vehicle_id and m.status == "scheduled"]
    
    def get_maintenance_history(self, vehicle_id: str) -> List[MaintenanceRecord]:
        """Get maintenance history for a vehicle."""
        return [m for m in self.maintenance_records.values() if m.vehicle_id == vehicle_id]
    
    def complete_maintenance(self, record_id: str, cost: float, parts: List[str] = None) -> Optional[MaintenanceRecord]:
        """Mark maintenance as completed."""
        if record_id in self.maintenance_records:
            record = self.maintenance_records[record_id]
            record.status = "completed"
            record.cost = cost
            if parts:
                record.parts_replaced = parts
            return record
        return None
    
    # -------------------------------------------------------------------------
    # INSURANCE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def create_insurance_policy(self, vehicle_id: str, provider: str,
                                 insurance_type: InsuranceType,
                                 monthly_premium: float,
                                 deductible: float,
                                 coverage_amount: float,
                                 mileage_limit: int = 0,
                                 agreed_value: float = 0) -> InsurancePolicy:
        """Create an insurance policy for a vehicle."""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=365)
        
        policy = InsurancePolicy(
            policy_id=f"ins_{vehicle_id}_{int(time.time())}",
            vehicle_id=vehicle_id,
            provider=provider,
            insurance_type=insurance_type,
            monthly_premium=monthly_premium,
            deductible=deductible,
            coverage_amount=coverage_amount,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            mileage_limit=mileage_limit,
            agreed_value=agreed_value,
            is_active=True,
        )
        
        self.insurance_policies[policy.policy_id] = policy
        return policy
    
    def get_active_policies(self, vehicle_id: str) -> List[InsurancePolicy]:
        """Get active insurance policies for a vehicle."""
        return [p for p in self.insurance_policies.values() 
                if p.vehicle_id == vehicle_id and p.is_active]
    
    # -------------------------------------------------------------------------
    # STORAGE BOOKING
    # -------------------------------------------------------------------------
    
    def book_storage(self, vehicle_id: str, facility_id: str,
                     start_date: str, end_date: str,
                     monthly_rate: float,
                     needs_charging: bool = False,
                     needs_maintenance: bool = False,
                     access_level: str = "owner") -> StorageBooking:
        """Book storage for a vehicle."""
        booking = StorageBooking(
            booking_id=f"store_{vehicle_id}_{int(time.time())}",
            vehicle_id=vehicle_id,
            facility_id=facility_id,
            start_date=start_date,
            end_date=end_date,
            monthly_rate=monthly_rate,
            needs_charging=needs_charging,
            needs_maintenance=needs_maintenance,
            access_level=access_level,
            status="active",
        )
        
        self.storage_bookings[booking.booking_id] = booking
        return booking
    
    def get_active_bookings(self, vehicle_id: str) -> List[StorageBooking]:
        """Get active storage bookings for a vehicle."""
        return [b for b in self.storage_bookings.values() 
                if b.vehicle_id == vehicle_id and b.status == "active"]
    
    # -------------------------------------------------------------------------
    # COMPREHENSIVE LIFECYCLE
    # -------------------------------------------------------------------------
    
    def get_vehicle_lifecycle(self, vehicle_id: str) -> Dict[str, Any]:
        """Get complete vehicle lifecycle information."""
        purchase = [o for o in self.purchase_orders.values() if o.vehicle_id == vehicle_id]
        maintenance = self.get_maintenance_history(vehicle_id)
        insurance = self.get_active_policies(vehicle_id)
        storage = self.get_active_bookings(vehicle_id)
        
        total_maintenance_cost = sum(m.cost for m in maintenance)
        total_insurance_cost = sum(p.monthly_premium * 12 for p in insurance)
        total_storage_cost = sum(b.monthly_rate * 12 for b in storage)
        
        return {
            "vehicle_id": vehicle_id,
            "purchase_orders": len(purchase),
            "total_purchase_cost": sum(o.total_cost for o in purchase),
            "maintenance_records": len(maintenance),
            "total_maintenance_cost": total_maintenance_cost,
            "active_insurance_policies": len(insurance),
            "annual_insurance_cost": total_insurance_cost,
            "active_storage_bookings": len(storage),
            "annual_storage_cost": total_storage_cost,
            "total_annual_cost": total_insurance_cost + total_storage_cost,
        }
    
    def get_marketplace_summary(self) -> Dict[str, Any]:
        """Get marketplace summary."""
        return {
            "timestamp": datetime.now().isoformat(),
            "dealerships": {
                "total": len(self.dealerships),
                "verified": len(self.get_verified_dealerships()),
                "by_type": {
                    dt.value: len([d for d in self.dealerships.values() if d.dealership_type == dt])
                    for dt in DealershipType
                },
            },
            "purchase_orders": {
                "total": len(self.purchase_orders),
                "pending": len(self.get_purchase_orders_by_status("pending")),
                "approved": len(self.get_purchase_orders_by_status("approved")),
                "delivered": len(self.get_purchase_orders_by_status("delivered")),
            },
            "maintenance": {
                "total_records": len(self.maintenance_records),
                "scheduled": len([m for m in self.maintenance_records.values() if m.status == "scheduled"]),
                "completed": len([m for m in self.maintenance_records.values() if m.status == "completed"]),
            },
            "insurance": {
                "total_policies": len(self.insurance_policies),
                "active": len([p for p in self.insurance_policies.values() if p.is_active]),
            },
            "storage": {
                "total_bookings": len(self.storage_bookings),
                "active": len([b for b in self.storage_bookings.values() if b.status == "active"]),
            },
        }


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

vehicle_collection_engine = VehicleCollectionEngine()
vehicle_marketplace_engine = VehicleMarketplaceEngine()