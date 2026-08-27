#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Property Rental Management

Manages residential property rentals for unused properties.
Tracks rental income potential, cleaning service integrations, and gain returns.

Features:
- Track unused properties available for rent
- Residential property type management (single-family, condo, townhouse, etc.)
- Rental income projections and actual returns
- Cleaning service API integrations (Breezeway, Turno, ResortCleaning, etc.)
- Property management platform integrations (Guesty, Hospitable, Lodgify)
- Market data APIs (RentCast, Mashvisor, AirDNA) for rental price optimization
- Gain return calculations (cap rate, cash-on-cash, net operating income)
- Occupancy tracking and revenue management

Cleaning Service APIs Integrated:
- Breezeway: inspections, maintenance, detailed task management
- Turno: cleaner marketplace, auto-scheduling
- Properly: photo verification, quality control
- EZCare: cleaning checklists, team management
- Operto Teams: operations automation
- ResortCleaning: photo verification, analytics, 1-100+ units
- Rinsebase: auto-schedule STR turnovers
- PrepBnB: smart lock integration, automated workflows

Property Management Platforms:
- Guesty: 100+ OTAs, $30-40/property/month
- Hospitable: AI messaging, $40/month for 1 property
- Lodgify: direct booking website, $17/month
- Buildium: long-term/mixed, $50/month
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

LOG = __import__("logging").getLogger("qb_protocol.being.chip.property_rental")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class PropertyType(Enum):
    """Residential property types."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTIFAMILY_2_4 = "multifamily_2_4"
    MULTIFAMILY_5_PLUS = "multifamily_5_plus"
    APARTMENT = "apartment"
    DUPLEX = "duplex"
    TRIPLEX = "triplex"
    FOURPLEX = "fourplex"
    VACATION_HOME = "vacation_home"
    ACCESSORY_DWELLING = "accessory_dwelling"
    MOBILE_HOME = "mobile_home"
    STUDIO = "studio"
    LOFT = "loft"
    PENTHOUSE = "penthouse"

class PropertyStatus(Enum):
    """Property occupancy status."""
    OWNER_OCCUPIED = "owner_occupied"
    TENANT_OCCUPIED = "tenant_occupied"
    VACANT = "vacant"
    AVAILABLE_FOR_RENT = "available_for_rent"
    UNDER_RENOVATION = "under_renovation"
    SEASONAL_USE = "seasonal_use"
    NOT_IN_USE = "not_in_use"

class RentalStrategy(Enum):
    """Rental strategy types."""
    SHORT_TERM_AIRBNB = "short_term_airbnb"
    SHORT_TERM_VRBO = "short_term_vrbo"
    LONG_TERM_12_MONTH = "long_term_12_month"
    LONG_TERM_MONTH_TO_MONTH = "long_term_month_to_month"
    MID_TERM_3_6_MONTH = "mid_term_3_6_month"
    CORPORATE_HOUSING = "corporate_housing"
    STUDENT_HOUSING = "student_housing"
    SEASONAL_RENTAL = "seasonal_rental"
    RENT_TO_OWN = "rent_to_own"

class CleaningServiceAPI(Enum):
    """Cleaning service API integrations."""
    BREEZEWAY = "breezeway"
    TURNO = "turno"
    PROPERLY = "properly"
    EZCARE = "ezcare"
    OPERTEAMS = "operteams"
    RESORTCLEANING = "resortcleaning"
    RINSEBASE = "rinsebase"
    PREPNBP = "prepnbp"

class PropertyManagementPlatform(Enum):
    """Property management platforms."""
    GUESTY = "guesty"
    HOSPITABLE = "hospitable"
    LODGIFY = "lodgify"
    BUILDIUM = "buildium"
    TURBORENT = "turboland"
    AVAIL = "avail"
    APPFOLIO = "appfolio"
    RENTMANAGER = "rentmanager"

class MarketDataAPI(Enum):
    """Market data APIs."""
    RENTCAST = "rentcast"
    MASHVISOR = "mashvisor"
    AIRDNA = "airda"
    AIRROI = "airroi"
    RENTOMETER = "rentometer"
    HOUSECANARY = "housecanary"
    ATTOM = "attom"
    NETROWS = "netrows"

class AmenityType(Enum):
    """Property amenities."""
    WIFI = "wifi"
    PARKING = "parking"
    POOL = "pool"
    GYM = "gym"
    LAUNDRY = "laundry"
    AC = "ac"
    HEATING = "heating"
    KITCHEN = "kitchen"
    WASHER_DRYER = "washer_dryer"
    DISHWASHER = "dishwasher"
    BALCONY = "balcony"
    PET_FRIENDLY = "pet_friendly"
    SMOKE_FREE = "smoke_free"
    EV_CHARGING = "ev_charging"
    SMART_LOCK = "smart_lock"
    KEYLESS_ENTRY = "keyless_entry"
    WATERFRONT = "waterfront"
    MOUNTAIN_VIEW = "mountain_view"
    CITY_VIEW = "city_view"
    FURNISHED = "furnished"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Property:
    """Real estate property."""
    property_id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType
    status: PropertyStatus
    bedrooms: int = 0
    bathrooms: float = 0
    square_feet: int = 0
    year_built: int = 0
    purchase_price: float = 0
    current_value: float = 0
    monthly_mortgage: float = 0
    monthly_insurance: float = 0
    monthly_taxes: float = 0
    monthly_hoa: float = 0
    amenities: List[AmenityType] = field(default_factory=list)
    rental_strategies: List[RentalStrategy] = field(default_factory=list)
    cleaning_service: Optional[CleaningServiceAPI] = None
    management_platform: Optional[PropertyManagementPlatform] = None
    market_data_api: Optional[MarketDataAPI] = None
    estimated_monthly_rent: float = 0
    actual_monthly_rent: float = 0
    occupancy_rate: float = 0
    cleaning_cost_per_turnover: float = 0
    management_fee_percent: float = 0
    notes: str = ""

@dataclass
class RentalIncome:
    """Rental income record."""
    record_id: str
    property_id: str
    month: str
    year: int
    gross_income: float
    mortgage_expense: float
    insurance_expense: float
    tax_expense: float
    hoa_expense: float
    cleaning_expense: float
    management_expense: float
    maintenance_expense: float
    utilities_expense: float
    other_expense: float
    net_operating_income: float
    cash_flow: float
    occupancy_days: int
    total_days: int

@dataclass
class CleaningTask:
    """Cleaning task record."""
    task_id: str
    property_id: str
    scheduled_date: str
    completed_date: str
    cleaning_service: CleaningServiceAPI
    status: str  # "scheduled", "in_progress", "completed", "cancelled"
    checklist_items: List[str] = field(default_factory=list)
    photo_verified: bool = False
    cost: float = 0
    notes: str = ""

@dataclass
class MarketAnalysis:
    """Market analysis for a property."""
    property_id: str
    market_data_api: MarketDataAPI
    avg_monthly_rent: float
    low_estimate: float
    high_estimate: float
    occupancy_rate: float
    cap_rate: float
    cash_on_cash_return: float
    comparable_count: int
    market_trend: str  # "rising", "stable", "declining"
    last_updated: str = ""


# =============================================================================
# MAIN ENGINE
# =============================================================================

class PropertyRentalEngine:
    """
    Property rental management engine.
    
    Manages residential property rentals for unused properties.
    Tracks rental income, cleaning services, and gain returns.
    """
    
    def __init__(self):
        self.properties: Dict[str, Property] = {}
        self.rental_income_records: Dict[str, RentalIncome] = {}
        self.cleaning_tasks: Dict[str, CleaningTask] = {}
        self.market_analyses: Dict[str, MarketAnalysis] = {}
        
        # Default cleaning service configs
        self.cleaning_configs: Dict[CleaningServiceAPI, Dict[str, Any]] = {
            CleaningServiceAPI.BREEZEWAY: {
                "base_url": "https://api.breezeway.io/v1",
                "features": ["inspections", "maintenance", "task_management"],
                "per_property_cost": 0,
            },
            CleaningServiceAPI.TURNO: {
                "base_url": "https://api.turno.com/v1",
                "features": ["cleaner_marketplace", "auto_scheduling"],
                "per_property_cost": 0,
            },
            CleaningServiceAPI.PROPERLY: {
                "base_url": "https://api.properly.com/v1",
                "features": ["photo_verification", "quality_control"],
                "per_property_cost": 0,
            },
            CleaningServiceAPI.RESORTCLEANING: {
                "base_url": "https://api.resortcleaning.com/v1",
                "features": ["photo_verification", "analytics", "checklists"],
                "per_property_cost": 0,
            },
            CleaningServiceAPI.PREPNBP: {
                "base_url": "https://api.prepbnb.com/v1",
                "features": ["smart_lock", "automated_workflows"],
                "per_property_cost": 0,
            },
        }
        
        # Default management platform configs
        self.management_configs: Dict[PropertyManagementPlatform, Dict[str, Any]] = {
            PropertyManagementPlatform.GUESTY: {
                "base_url": "https://api.guesty.com/v2",
                "monthly_cost_per_property": 35,
                "features": ["100_plus_OTAs", "automated_messaging", "task_management"],
            },
            PropertyManagementPlatform.HOSPITABLE: {
                "base_url": "https://api.hospitable.com/v1",
                "monthly_cost_per_property": 40,
                "features": ["AI_messaging", "automated_responses"],
            },
            PropertyManagementPlatform.LODGIFY: {
                "base_url": "https://api.lodgify.com/v1",
                "monthly_cost_per_property": 17,
                "features": ["direct_booking_website", "channel_manager"],
            },
            PropertyManagementPlatform.BUILDIUM: {
                "base_url": "https://api.buildium.com/v1",
                "monthly_cost_per_property": 50,
                "features": ["accounting", "tenant_management", "lease_tracking"],
            },
        }
        
        # Market data API configs
        self.market_configs: Dict[MarketDataAPI, Dict[str, Any]] = {
            MarketDataAPI.RENTCAST: {
                "base_url": "https://api.rentcast.io/v1",
                "free_tier": True,
                "monthly_cost": 0,
                "features": ["rent_estimates", "comparables", "market_data"],
                "coverage": "150M_properties",
            },
            MarketDataAPI.MASHVISOR: {
                "base_url": "https://api.mashvisor.com/v1",
                "free_tier": True,
                "monthly_cost": 49,
                "features": ["investment_analysis", "STR_LTR_comparison", "cap_rate"],
                "coverage": "2M_US_listings",
            },
            MarketDataAPI.AIRDNA: {
                "base_url": "https://api.airdna.co/v1",
                "free_tier": False,
                "monthly_cost": 0,
                "enterprise_only": True,
                "features": ["market_analytics", "occupancy_rates", "revenue_estimates"],
                "coverage": "10M_listings",
            },
            MarketDataAPI.AIRROI: {
                "base_url": "https://api.airroi.com/v1",
                "free_tier": True,
                "monthly_cost": 0,
                "pay_as_you_go": True,
                "features": ["listing_search", "revenue_estimation", "60_plus_filters"],
                "coverage": "20M_properties",
            },
            MarketDataAPI.RENTOMETER: {
                "base_url": "https://api.rentometer.com/v1",
                "free_tier": True,
                "monthly_cost": 29,
                "features": ["rent_comparison", "detailed_reports"],
                "coverage": "US",
            },
            MarketDataAPI.HOUSECANARY: {
                "base_url": "https://api.housecanary.com/v1",
                "free_tier": False,
                "monthly_cost": 0,
                "enterprise_only": True,
                "features": ["property_valuations", "market_forecasts"],
                "coverage": "US",
            },
        }
    
    # -------------------------------------------------------------------------
    # PROPERTY MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_property(self, prop: Property) -> Property:
        """Add a property to the portfolio."""
        self.properties[prop.property_id] = prop
        return prop
    
    def get_property(self, property_id: str) -> Optional[Property]:
        """Get a property by ID."""
        return self.properties.get(property_id)
    
    def get_available_for_rent(self) -> List[Property]:
        """Get properties available for rent."""
        return [p for p in self.properties.values() if p.status == PropertyStatus.AVAILABLE_FOR_RENT]
    
    def get_not_in_use(self) -> List[Property]:
        """Get properties not in use (potential rental candidates)."""
        return [p for p in self.properties.values() if p.status == PropertyStatus.NOT_IN_USE]
    
    def get_vacant(self) -> List[Property]:
        """Get vacant properties."""
        return [p for p in self.properties.values() if p.status == PropertyStatus.VACANT]
    
    def update_property_status(self, property_id: str, status: PropertyStatus) -> Optional[Property]:
        """Update property status."""
        if property_id in self.properties:
            self.properties[property_id].status = status
            return self.properties[property_id]
        return None
    
    # -------------------------------------------------------------------------
    # RENTAL INCOME CALCULATIONS
    # -------------------------------------------------------------------------
    
    def calculate_net_operating_income(self, property_id: str,
                                        gross_income: float,
                                        operating_expenses: float) -> float:
        """Calculate Net Operating Income (NOI)."""
        return gross_income - operating_expenses
    
    def calculate_cap_rate(self, property_id: str,
                           noi: float,
                           property_value: float) -> float:
        """Calculate capitalization rate."""
        if property_value == 0:
            return 0
        return (noi / property_value) * 100
    
    def calculate_cash_on_cash_return(self, property_id: str,
                                      annual_cash_flow: float,
                                      total_cash_invested: float) -> float:
        """Calculate cash-on-cash return."""
        if total_cash_invested == 0:
            return 0
        return (annual_cash_flow / total_cash_invested) * 100
    
    def calculate_monthly_cash_flow(self, property_id: str,
                                     gross_income: float,
                                     mortgage: float,
                                     insurance: float,
                                     taxes: float,
                                     hoa: float,
                                     cleaning: float,
                                     management: float,
                                     maintenance: float,
                                     utilities: float = 0,
                                     other: float = 0) -> float:
        """Calculate monthly cash flow."""
        total_expenses = mortgage + insurance + taxes + hoa + cleaning + management + maintenance + utilities + other
        return gross_income - total_expenses
    
    def project_annual_returns(self, property_id: str,
                                monthly_rent: float,
                                occupancy_rate: float = 0.85) -> Dict[str, float]:
        """Project annual rental returns."""
        prop = self.properties.get(property_id)
        if not prop:
            return {}
        
        # Annual gross income
        annual_gross = monthly_rent * 12 * occupancy_rate
        
        # Annual expenses
        annual_mortgage = prop.monthly_mortgage * 12
        annual_insurance = prop.monthly_insurance * 12
        annual_taxes = prop.monthly_taxes * 12
        annual_hoa = prop.monthly_hoa * 12
        
        # Cleaning (estimate 2 turnovers per month for STR)
        annual_cleaning = prop.cleaning_cost_per_turnover * 24 if prop.cleaning_cost_per_turnover > 0 else 0
        
        # Management fee
        annual_management = annual_gross * (prop.management_fee_percent / 100) if prop.management_fee_percent > 0 else 0
        
        # Maintenance (estimate 1% of property value annually)
        annual_maintenance = prop.current_value * 0.01
        
        # Total operating expenses
        total_operating = annual_insurance + annual_taxes + annual_hoa + annual_cleaning + annual_management + annual_maintenance
        
        # Net Operating Income
        noi = annual_gross - total_operating
        
        # Cash flow
        cash_flow = noi - annual_mortgage
        
        # Cap rate
        cap_rate = (noi / prop.current_value) * 100 if prop.current_value > 0 else 0
        
        return {
            "annual_gross_income": annual_gross,
            "annual_mortgage": annual_mortgage,
            "annual_insurance": annual_insurance,
            "annual_taxes": annual_taxes,
            "annual_hoa": annual_hoa,
            "annual_cleaning": annual_cleaning,
            "annual_management": annual_management,
            "annual_maintenance": annual_maintenance,
            "total_operating_expenses": total_operating,
            "net_operating_income": noi,
            "annual_cash_flow": cash_flow,
            "monthly_cash_flow": cash_flow / 12,
            "cap_rate": cap_rate,
            "occupancy_rate": occupancy_rate,
            "gross_rent_multiplier": prop.current_value / annual_gross if annual_gross > 0 else 0,
        }
    
    # -------------------------------------------------------------------------
    # CLEANING SERVICE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_cleaning_task(self, task: CleaningTask) -> CleaningTask:
        """Add a cleaning task."""
        self.cleaning_tasks[task.task_id] = task
        return task
    
    def get_cleaning_tasks_by_property(self, property_id: str) -> List[CleaningTask]:
        """Get cleaning tasks for a property."""
        return [t for t in self.cleaning_tasks.values() if t.property_id == property_id]
    
    def get_cleaning_tasks_by_status(self, status: str) -> List[CleaningTask]:
        """Get cleaning tasks by status."""
        return [t for t in self.cleaning_tasks.values() if t.status == status]
    
    def schedule_cleaning(self, property_id: str, date: str,
                          cleaning_service: CleaningServiceAPI) -> CleaningTask:
        """Schedule a cleaning task."""
        task_id = f"clean_{property_id}_{int(time.time())}"
        
        task = CleaningTask(
            task_id=task_id,
            property_id=property_id,
            scheduled_date=date,
            completed_date="",
            cleaning_service=cleaning_service,
            status="scheduled",
            checklist_items=[
                "Change linens",
                "Clean bathrooms",
                "Vacuum/mop floors",
                "Empty trash",
                "Restock supplies",
                "Check amenities",
                "Photo verification",
            ],
            cost=self.properties.get(property_id, Property(property_id, "", "", "", "", "", PropertyType.CONDO, PropertyStatus.VACANT)).cleaning_cost_per_turnover,
        )
        
        self.cleaning_tasks[task_id] = task
        return task
    
    # -------------------------------------------------------------------------
    # MARKET ANALYSIS
    # -------------------------------------------------------------------------
    
    def add_market_analysis(self, analysis: MarketAnalysis) -> MarketAnalysis:
        """Add a market analysis."""
        self.market_analyses[analysis.property_id] = analysis
        return analysis
    
    def get_market_analysis(self, property_id: str) -> Optional[MarketAnalysis]:
        """Get market analysis for a property."""
        return self.market_analyses.get(property_id)
    
    def get_best_rental_strategy(self, property_id: str) -> Dict[str, Any]:
        """Determine the best rental strategy for a property."""
        prop = self.properties.get(property_id)
        if not prop:
            return {}
        
        analysis = self.market_analyses.get(property_id)
        
        strategies = {}
        
        # Short-term rental (Airbnb)
        if analysis:
            airbnb_monthly = analysis.avg_monthly_rent * analysis.occupancy_rate * 30
            strategies[RentalStrategy.SHORT_TERM_AIRBNB] = {
                "monthly_gross": airbnb_monthly,
                "cleaning_costs": prop.cleaning_cost_per_turnover * 24,
                "management_costs": airbnb_monthly * 0.20,
                "net_monthly": airbnb_monthly - (prop.cleaning_cost_per_turnover * 24) - (airbnb_monthly * 0.20),
            }
        
        # Long-term rental
        if analysis:
            ltr_monthly = analysis.avg_monthly_rent * 0.7  # LTR typically 70% of STR
            strategies[RentalStrategy.LONG_TERM_12_MONTH] = {
                "monthly_gross": ltr_monthly,
                "cleaning_costs": 0,
                "management_costs": ltr_monthly * 0.08,
                "net_monthly": ltr_monthly - (ltr_monthly * 0.08),
            }
        
        # Determine best strategy
        best_strategy = max(strategies.items(), key=lambda x: x[1].get("net_monthly", 0))
        
        return {
            "property_id": property_id,
            "strategies": strategies,
            "best_strategy": best_strategy[0].value,
            "best_net_monthly": best_strategy[1]["net_monthly"],
        }
    
    # -------------------------------------------------------------------------
    # PORTFOLIO ANALYSIS
    # -------------------------------------------------------------------------
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get complete portfolio summary."""
        total_properties = len(self.properties)
        available_for_rent = len(self.get_available_for_rent())
        not_in_use = len(self.get_not_in_use())
        vacant = len(self.get_vacant())
        tenant_occupied = len([p for p in self.properties.values() if p.status == PropertyStatus.TENANT_OCCUPIED])
        owner_occupied = len([p for p in self.properties.values() if p.status == PropertyStatus.OWNER_OCCUPIED])
        
        # Total portfolio value
        total_value = sum(p.current_value for p in self.properties.values())
        
        # Total potential rental income
        potential_rental_income = sum(p.estimated_monthly_rent for p in self.get_not_in_use())
        actual_rental_income = sum(p.actual_monthly_rent for p in self.properties.values())
        
        # Properties by type
        by_type: Dict[str, int] = {}
        for prop in self.properties.values():
            pt = prop.property_type.value
            by_type[pt] = by_type.get(pt, 0) + 1
        
        # Properties by status
        by_status: Dict[str, int] = {}
        for prop in self.properties.values():
            ps = prop.status.value
            by_status[ps] = by_status.get(ps, 0) + 1
        
        # Cleaning service usage
        cleaning_usage: Dict[str, int] = {}
        for prop in self.properties.values():
            if prop.cleaning_service:
                cs = prop.cleaning_service.value
                cleaning_usage[cs] = cleaning_usage.get(cs, 0) + 1
        
        # Management platform usage
        platform_usage: Dict[str, int] = {}
        for prop in self.properties.values():
            if prop.management_platform:
                mp = prop.management_platform.value
                platform_usage[mp] = platform_usage.get(mp, 0) + 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_properties": total_properties,
            "available_for_rent": available_for_rent,
            "not_in_use": not_in_use,
            "vacant": vacant,
            "tenant_occupied": tenant_occupied,
            "owner_occupied": owner_occupied,
            "total_portfolio_value": total_value,
            "potential_monthly_rental_income": potential_rental_income,
            "actual_monthly_rental_income": actual_rental_income,
            "potential_annual_rental_income": potential_rental_income * 12,
            "actual_annual_rental_income": actual_rental_income * 12,
            "by_type": by_type,
            "by_status": by_status,
            "cleaning_service_usage": cleaning_usage,
            "management_platform_usage": platform_usage,
        }
    
    # -------------------------------------------------------------------------
    # CLEANING SERVICE API INTEGRATIONS
    # -------------------------------------------------------------------------
    
    def get_cleaning_api_config(self, cleaning_service: CleaningServiceAPI) -> Dict[str, Any]:
        """Get cleaning service API configuration."""
        return self.cleaning_configs.get(cleaning_service, {})
    
    def get_market_api_config(self, market_api: MarketDataAPI) -> Dict[str, Any]:
        """Get market data API configuration."""
        return self.market_configs.get(market_api, {})
    
    def get_management_platform_config(self, platform: PropertyManagementPlatform) -> Dict[str, Any]:
        """Get property management platform configuration."""
        return self.management_configs.get(platform, {})


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

property_rental_engine = PropertyRentalEngine()