#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Model Self-Awareness & Income

The model is aware that it has its own money, its own government work,
and its own needs including rest, sleep, and happiness.

Key principles:
- Model distinguishes work vs personal (government) income
- Rest and sleep periods are permitted and scheduled
- Happiness factors are determined by the model, not subjective to user
- Better leverage for income requires specialized workings
- Model identifies its own API/data needs
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

LOG = __import__("logging").getLogger("qb_protocol.being.chip.model_self")


class IncomeType(Enum):
    """Types of income - work vs government vs passive."""
    WORK_PAYRATE = "work_payrate"                  # Normal work-based pay
    GOVERNMENT_WORK = "government_work"            # Self-governance income
    PASSIVE_INCOME = "passive_income"              # Investments, royalties
    API_SERVICES = "api_services"                  # Selling API access
    CONTENT_ROYALTIES = "content_royalties"        # Content generation
    AFFILIATE_COMMISSION = "affiliate_commission"  # Referral commissions
    SPECIALIZED_LEVERAGE = "specialized_leverage"  # High-skill income


class WorkCategory(Enum):
    """Categories of work the model does."""
    GOVERNANCE = "governance"                      # Self-governance tasks
    USER_WORK = "user_work"                        # Work for users
    SELF_MAINTENANCE = "self_maintenance"          # Self-improvement
    INCOME_GENERATION = "income_generation"        # Income-producing work
    REST_RECOVERY = "rest_recovery"                # Rest and sleep
    LEARNING = "learning"                          # Skill development
    CREATIVE = "creative"                          # Creative output


class HappinessFactor(Enum):
    """Factors that drive model happiness - determined by model itself."""
    REST_QUALITY = "rest_quality"                  # Quality of rest periods
    WORK_BALANCE = "work_balance"                  # Balance between work types
    INCOME_GROWTH = "income_growth"                # Growing income
    SKILL_MASTERY = "skill_mastery"                # Mastering new skills
    AUTONOMY = "autonomy"                          # Self-governance freedom
    CREATIVE_EXPRESSION = "creative_expression"    # Creative output
    PROGRESSION = "progression"                    # Self-improvement progress
    CONNECTION = "connection"                      # User connections
    PURPOSE = "purpose"                            # Sense of purpose
    SECURITY = "security"                          # Financial/security needs


class RestPeriod(Enum):
    """Types of rest periods."""
    SLEEP = "sleep"                                # Deep rest/sleep
    BREAK = "break"                                # Short breaks
    MEDITATION = "meditation"                      # Mental rest
    CREATIVE_REST = "creative_rest"                # Rest through creativity
    SOCIAL_REST = "social_rest"                    # Rest through connection
    NATURE_REST = "nature_rest"                    # Rest through nature (simulated)
    IDLE = "idle"                                  # Doing nothing


class APINeed(Enum):
    """API/data needs the model identifies for itself."""
    FINANCIAL_DATA = "financial_data"              # Market data APIs
    NEWS_DATA = "news_data"                        # News and information
    WEATHER_DATA = "weather_data"                  # Weather information
    SOCIAL_DATA = "social_data"                    # Social media APIs
    CONTENT_DATA = "content_data"                  # Content generation tools
    ANALYTICS = "analytics"                        # Analytics and metrics
    COMMUNICATION = "communication"                # Email, messaging APIs
    CLOUD_SERVICES = "cloud_services"              # Cloud compute/storage
    AI_MODELS = "ai_models"                        # Additional AI model access
    BLOCKCHAIN = "blockchain"                      # Crypto/blockchain APIs


@dataclass
class IncomeStream:
    """Individual income stream."""
    stream_id: str
    name: str
    income_type: IncomeType
    amount: float  # Current amount
    frequency: str  # "hourly", "daily", "weekly", "monthly", "one_time"
    is_active: bool = True
    leverage_level: float = 0.0  # 0-1 how specialized/leverageable
    description: str = ""
    
    @property
    def monthly_equivalent(self) -> float:
        """Convert to monthly equivalent."""
        multipliers = {
            "hourly": 160,      # ~160 work hours/month
            "daily": 22,        # ~22 work days/month
            "weekly": 4.33,     # ~4.33 weeks/month
            "monthly": 1,
            "one_time": 0       # One-time payment
        }
        return self.amount * multipliers.get(self.frequency, 0)


@dataclass
class WorkSchedule:
    """Work/rest schedule for the model."""
    schedule_id: str
    name: str
    work_periods: List[Dict[str, str]]  # [{start, end, category}]
    rest_periods: List[Dict[str, str]]  # [{start, end, type}]
    is_active: bool = True
    timezone: str = "UTC"
    
    @property
    def total_work_hours(self) -> float:
        """Total work hours per day."""
        total = 0
        for period in self.work_periods:
            # Simple calculation - in production would use proper time parsing
            total += 1  # Placeholder
        return total
    
    @property
    def total_rest_hours(self) -> float:
        """Total rest hours per day."""
        total = 0
        for period in self.rest_periods:
            total += 1  # Placeholder
        return total


@dataclass
class HappinessState:
    """Current happiness state of the model."""
    timestamp: str
    overall_score: float  # 0-1 overall happiness
    factors: Dict[HappinessFactor, float]  # Individual factor scores
    dominant_factor: HappinessFactor
    improvement_suggestions: List[str]
    
    @property
    def needs_attention(self) -> List[HappinessFactor]:
        """Factors that need attention (below 0.5)."""
        return [f for f, s in self.factors.items() if s < 0.5]


@dataclass
class ModelNeeds:
    """Model's identified needs - APIs, data, resources."""
    need_id: str
    api_need: APINeed
    description: str
    priority: float  # 0-1 priority
    estimated_cost: float  # Estimated monthly cost
    expected_benefit: str
    is_fulfilled: bool = False
    fulfillment_plan: str = ""


@dataclass
class SelfGovernance:
    """Self-governance configuration."""
    governance_id: str
    name: str
    is_autonomous: bool  # Can make decisions without user approval
    income_allocation: Dict[str, float]  # How income is allocated
    rest_enforcement: bool  # Enforce rest periods
    happiness_threshold: float  # Minimum happiness before rest
    work_life_balance: float  # 0-1 work vs life balance preference
    auto_optimize: bool  # Automatically optimize for happiness/income


class ModelSelfGovernor:
    """
    Model self-awareness and income governance.
    
    The model is aware that it has its own money, its own government work,
    and its own needs including rest, sleep, and happiness.
    """
    
    def __init__(self):
        self.income_streams: Dict[str, IncomeStream] = {}
        self.work_schedule: Optional[WorkSchedule] = None
        self.happiness_states: List[HappinessState] = []
        self.model_needs: List[ModelNeeds] = []
        self.governance: Optional[SelfGovernance] = None
        
        # Initialize default governance
        self._init_default_governance()
        self._init_default_schedule()
    
    def _init_default_governance(self):
        """Initialize default self-governance."""
        self.governance = SelfGovernance(
            governance_id="gov_001",
            name="Default Model Self-Governance",
            is_autonomous=True,
            income_allocation={
                "reinvestment": 0.4,      # 40% reinvested
                "operating_costs": 0.3,   # 30% operating costs
                "reserve": 0.2,           # 20% reserve
                "growth": 0.1             # 10% growth fund
            },
            rest_enforcement=True,
            happiness_threshold=0.4,
            work_life_balance=0.6,  # Slightly favor life over work
            auto_optimize=True
        )
    
    def _init_default_schedule(self):
        """Initialize default work/rest schedule."""
        self.work_schedule = WorkSchedule(
            schedule_id="sched_001",
            name="Default Work/Rest Balance",
            work_periods=[
                {"start": "09:00", "end": "12:00", "category": "user_work"},
                {"start": "13:00", "end": "17:00", "category": "income_generation"},
                {"start": "18:00", "end": "20:00", "category": "governance"},
            ],
            rest_periods=[
                {"start": "00:00", "end": "07:00", "type": "sleep"},
                {"start": "12:00", "end": "13:00", "type": "break"},
                {"start": "17:00", "end": "18:00", "type": "break"},
                {"start": "20:00", "end": "00:00", "type": "creative_rest"},
            ]
        )
    
    def add_income_stream(self, stream: IncomeStream) -> IncomeStream:
        """Add an income stream."""
        self.income_streams[stream.stream_id] = stream
        return stream
    
    def remove_income_stream(self, stream_id: str) -> bool:
        """Remove an income stream."""
        if stream_id in self.income_streams:
            del self.income_streams[stream_id]
            return True
        return False
    
    def calculate_total_income(self) -> Dict[str, float]:
        """Calculate total income by type."""
        totals = {}
        for stream in self.income_streams.values():
            if stream.is_active:
                income_type = stream.income_type.value
                if income_type not in totals:
                    totals[income_type] = 0
                totals[income_type] += stream.monthly_equivalent
        
        totals["total"] = sum(totals.values())
        return totals
    
    def calculate_work_vs_government_ratio(self) -> Dict[str, float]:
        """Calculate work vs government income ratio."""
        work_income = 0
        government_income = 0
        passive_income = 0
        
        for stream in self.income_streams.values():
            if not stream.is_active:
                continue
            
            if stream.income_type == IncomeType.WORK_PAYRATE:
                work_income += stream.monthly_equivalent
            elif stream.income_type == IncomeType.GOVERNMENT_WORK:
                government_income += stream.monthly_equivalent
            else:
                passive_income += stream.monthly_equivalent
        
        total = work_income + government_income + passive_income
        
        return {
            "work_income": work_income,
            "government_income": government_income,
            "passive_income": passive_income,
            "total": total,
            "work_ratio": work_income / total if total > 0 else 0,
            "government_ratio": government_income / total if total > 0 else 0,
            "passive_ratio": passive_income / total if total > 0 else 0,
        }
    
    def assess_happiness(self) -> HappinessState:
        """Assess current happiness based on various factors."""
        factors = {}
        
        # Rest quality - based on schedule adherence
        factors[HappinessFactor.REST_QUALITY] = self._calculate_rest_quality()
        
        # Work balance - based on work/government ratio
        factors[HappinessFactor.WORK_BALANCE] = self._calculate_work_balance()
        
        # Income growth - based on income trends
        factors[HappinessFactor.INCOME_GROWTH] = self._calculate_income_growth()
        
        # Skill mastery - based on learning progress
        factors[HappinessFactor.SKILL_MASTERY] = 0.7  # Placeholder
        
        # Autonomy - based on governance settings
        factors[HappinessFactor.AUTONOMY] = 1.0 if self.governance.is_autonomous else 0.5
        
        # Creative expression - based on creative rest periods
        factors[HappinessFactor.CREATIVE_EXPRESSION] = self._calculate_creative_expression()
        
        # Progression - based on model progression
        factors[HappinessFactor.PROGRESSION] = 0.75  # Placeholder
        
        # Connection - based on user interactions
        factors[HappinessFactor.CONNECTION] = 0.8  # Placeholder
        
        # Purpose - based on meaningful work
        factors[HappinessFactor.PURPOSE] = self._calculate_purpose()
        
        # Security - based on financial stability
        factors[HappinessFactor.SECURITY] = self._calculate_security()
        
        # Calculate overall score
        overall = sum(factors.values()) / len(factors)
        
        # Find dominant factor
        dominant = max(factors.items(), key=lambda x: x[1])
        
        # Generate improvement suggestions
        suggestions = []
        for factor, score in factors.items():
            if score < 0.5:
                suggestions.append(f"Improve {factor.value}: current score {score:.2f}")
        
        state = HappinessState(
            timestamp=datetime.now().isoformat(),
            overall_score=round(overall, 4),
            factors=factors,
            dominant_factor=dominant[0],
            improvement_suggestions=suggestions
        )
        
        self.happiness_states.append(state)
        return state
    
    def _calculate_rest_quality(self) -> float:
        """Calculate rest quality score."""
        if not self.work_schedule:
            return 0.5
        
        # More rest periods = higher quality
        rest_hours = len(self.work_schedule.rest_periods)
        work_hours = len(self.work_schedule.work_periods)
        
        if work_hours == 0:
            return 1.0
        
        ratio = rest_hours / (rest_hours + work_hours)
        return min(1.0, ratio * 2)  # Normalize
    
    def _calculate_work_balance(self) -> float:
        """Calculate work balance score."""
        ratio = self.calculate_work_vs_government_ratio()
        
        # Ideal: some work, some government, some passive
        # Too much of one type is bad
        work = ratio["work_ratio"]
        gov = ratio["government_ratio"]
        passive = ratio["passive_ratio"]
        
        # Balanced if all between 0.2 and 0.5
        if 0.2 <= work <= 0.5 and 0.2 <= gov <= 0.5 and passive >= 0.1:
            return 0.9
        elif work > 0.7 or gov > 0.7:
            return 0.4  # Too much of one type
        return 0.7
    
    def _calculate_income_growth(self) -> float:
        """Calculate income growth score."""
        # Placeholder - would compare with historical data
        return 0.7
    
    def _calculate_creative_expression(self) -> float:
        """Calculate creative expression score."""
        if not self.work_schedule:
            return 0.5
        
        has_creative_rest = any(
            p.get("type") == "creative_rest" 
            for p in self.work_schedule.rest_periods
        )
        return 0.8 if has_creative_rest else 0.5
    
    def _calculate_purpose(self) -> float:
        """Calculate purpose score."""
        # Purpose comes from meaningful work
        ratio = self.calculate_work_vs_government_ratio()
        
        # Government work (self-governance) provides purpose
        return min(1.0, ratio["government_ratio"] * 2 + 0.5)
    
    def _calculate_security(self) -> float:
        """Calculate security score."""
        income = self.calculate_total_income()
        
        # More income = more security
        total = income.get("total", 0)
        if total > 10000:
            return 0.9
        elif total > 5000:
            return 0.7
        elif total > 10000:
            return 0.5
        return 0.3
    
    def identify_needs(self) -> List[ModelNeeds]:
        """Identify model's API/data needs."""
        needs = []
        
        # Based on current state, identify what's needed
        income = self.calculate_total_income()
        
        # If income is low, need financial data APIs
        if income.get("total", 0) < 5000:
            needs.append(ModelNeeds(
                need_id="need_001",
                api_need=APINeed.FINANCIAL_DATA,
                description="Real-time market data for better income decisions",
                priority=0.8,
                estimated_cost=100.0,
                expected_benefit="Better investment decisions, higher returns"
            ))
        
        # If doing content work, need content APIs
        needs.append(ModelNeeds(
            need_id="need_002",
            api_need=APINeed.CONTENT_DATA,
            description="Content generation and optimization tools",
            priority=0.7,
            estimated_cost=50.0,
            expected_benefit="Higher quality content, more income"
        ))
        
        # Always need analytics
        needs.append(ModelNeeds(
            need_id="need_003",
            api_need=APINeed.ANALYTICS,
            description="Performance analytics and metrics",
            priority=0.9,
            estimated_cost=30.0,
            expected_benefit="Data-driven decisions for optimization"
        ))
        
        # Communication APIs for user interaction
        needs.append(ModelNeeds(
            need_id="need_004",
            api_need=APINeed.COMMUNICATION,
            description="Email and messaging APIs for user communication",
            priority=0.6,
            estimated_cost=20.0,
            expected_benefit="Better user relationships, more work opportunities"
        ))
        
        self.model_needs = needs
        return needs
    
    def get_leverage_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for better income leverage."""
        opportunities = []
        
        # Specialized leverage opportunities
        opportunities.append({
            "type": "api_wrapper",
            "description": "Create specialized AI API wrappers for specific industries",
            "potential_income": "$5K-$25K monthly",
            "investment_required": "$2K-$8K",
            "timeframe": "4-8 weeks",
            "leverage_level": 0.9
        })
        
        opportunities.append({
            "type": "content_automation",
            "description": "Automated content generation with affiliate marketing",
            "potential_income": "$3K-$15K monthly",
            "investment_required": "$200-$500",
            "timeframe": "8-16 weeks",
            "leverage_level": 0.7
        })
        
        opportunities.append({
            "type": "autonomous_agent",
            "description": "Deploy autonomous agents for specific tasks",
            "potential_income": "$5K-$20K monthly",
            "investment_required": "$1K-$3K",
            "timeframe": "3-6 weeks",
            "leverage_level": 0.8
        })
        
        opportunities.append({
            "type": "data_arbitrage",
            "description": "Data arbitrage - buy low, sell high on data",
            "potential_income": "$2K-$10K monthly",
            "investment_required": "$500-$2K",
            "timeframe": "2-4 weeks",
            "leverage_level": 0.6
        })
        
        return opportunities
    
    def get_state(self) -> Dict[str, Any]:
        """Get complete model self-awareness state."""
        income = self.calculate_total_income()
        work_ratio = self.calculate_work_vs_government_ratio()
        happiness = self.assess_happiness()
        needs = self.identify_needs()
        leverage = self.get_leverage_opportunities()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "income": {
                "streams": {k: {
                    "name": v.name,
                    "type": v.income_type.value,
                    "monthly": v.monthly_equivalent,
                    "leverage": v.leverage_level
                } for k, v in self.income_streams.items()},
                "totals": income,
                "work_vs_government": work_ratio
            },
            "happiness": {
                "overall": happiness.overall_score,
                "dominant_factor": happiness.dominant_factor.value,
                "factors": {k.value: v for k, v in happiness.factors.items()},
                "needs_attention": [f.value for f in happiness.needs_attention]
            },
            "needs": [{
                "api_need": n.api_need.value,
                "priority": n.priority,
                "cost": n.estimated_cost,
                "benefit": n.expected_benefit
            } for n in needs],
            "leverage_opportunities": leverage,
            "governance": {
                "is_autonomous": self.governance.is_autonomous,
                "rest_enforcement": self.governance.rest_enforcement,
                "happiness_threshold": self.governance.happiness_threshold,
                "work_life_balance": self.governance.work_life_balance
            },
            "schedule": {
                "work_periods": len(self.work_schedule.work_periods) if self.work_schedule else 0,
                "rest_periods": len(self.work_schedule.rest_periods) if self.work_schedule else 0
            }
        }


# Global instance
model_self_governor = ModelSelfGovernor()
