#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Direct Investment System

Direct investment into companies bypassing traditional brokers.
Uses DRS (Direct Registration System), DSPPs (Direct Stock Purchase Plans),
and direct transfer agent interactions for true ownership.

Key Concepts:
- DRS: Hold shares directly in YOUR name on company books (not broker's "street name")
- DSPP: Buy shares directly from the company via transfer agent
- Transfer Agents: Computershare, Equiniti, Continental Stock, VStock, Colonial Stock
- True Ownership: Your name is the registered shareholder, not the broker

Benefits over Traditional Brokers:
- No broker bankruptcy risk (shares held in your name)
- Direct communication with company (voting rights, annual reports)
- No commission fees (or very low fees)
- Fractional shares available
- No "street name" lending (your shares can't be lent to short sellers)
- Direct dividend payments from company

Transfer Agents:
- Computershare: Largest, handles 1000+ companies (Coca-Cola, Intel, Walmart)
- Equiniti: Major UK/US transfer agent
- Continental Stock Transfer: NYSE/NASDAQ/OTC specialist
- VStock Transfer: DTC participant, 1000+ issuers
- Colonial Stock Transfer: Personalized service since 1987
- American Stock Transfer & Trust (AST): Large cap specialist
- Broadridge: Corporate actions and proxy
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

LOG = __import__("logging").getLogger("qb_protocol.being.chip.direct_investment")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class TransferAgent(Enum):
    """Major transfer agents for direct registration."""
    COMPUTERSHARE = "computershare"
    EQUINITI = "equiniti"
    CONTINENTAL_STOCK = "continental_stock"
    VSTOCK_TRANSFER = "vstock_transfer"
    COLONIAL_STOCK = "colonial_stock"
    AST = "american_stock_transfer"
    BROADRIDGE = "broadridge"
    EQUITY_STOCK_TRANSFER = "equity_stock_transfer"

class InvestmentType(Enum):
    """Direct investment types."""
    DRS = "direct_registration_system"
    DSPP = "direct_stock_purchase_plan"
    DRIP = "dividend_reinvestment_plan"
    DIRECT_PURCHASE = "direct_purchase"
    ESPP = "employee_stock_purchase_plan"
    PRIVATE_PLACEMENT = "private_placement"
    REG_A = "regulation_a"
    REG_CF = "regulation_crowdfunding"

class HoldingType(Enum):
    """How shares are held."""
    DRS_BOOK_ENTRY = "drs_book_entry"
    DSPP_PLAN = "dspp_plan"
    CERTIFICATE = "physical_certificate"
    DIRECT_PURCHASE = "direct_purchase"

class CorporateActionType(Enum):
    """Corporate action types."""
    DIVIDEND_CASH = "dividend_cash"
    DIVIDEND_STOCK = "dividend_stock"
    STOCK_SPLIT = "stock_split"
    REVERSE_SPLIT = "reverse_split"
    MERGER = "merger"
    SPINOFF = "spinoff"
    RIGHTS_OFFERING = "rights_offering"
    TENDER_OFFER = "tender_offender"
    ACQUISITION = "acquisition"

class InvestmentStatus(Enum):
    """Investment status."""
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    TRANSFER_IN_PROGRESS = "transfer_in_progress"
    TRANSFER_OUT = "transfer_out"
    DIVIDEND_PENDING = "dividend_pending"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Company:
    """Public company information."""
    company_id: str
    name: str
    ticker: str
    sector: str
    industry: str
    transfer_agent: TransferAgent
    has_dspp: bool = False
    has_drip: bool = False
    has_drs: bool = True
    min_initial_investment: float = 0
    min_recurring_investment: float = 0
    purchase_fee: float = 0
    sell_fee: float = 0
    dividend_yield: float = 0
    market_cap: float = 0
    notes: str = ""

@dataclass
class DirectHolding:
    """Directly registered share holding."""
    holding_id: str
    company_id: str
    ticker: str
    transfer_agent: TransferAgent
    holding_type: HoldingType
    share_quantity: float
    cost_basis_per_share: float
    current_price: float
    total_cost_basis: float
    current_market_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_percent: float
    dividend_reinvestment: bool = False
    registration_date: str = ""
    status: InvestmentStatus = InvestmentStatus.ACTIVE
    notes: str = ""

@dataclass
class DirectPurchase:
    """Direct purchase transaction."""
    purchase_id: str
    company_id: str
    ticker: str
    transfer_agent: TransferAgent
    purchase_date: str
    settlement_date: str
    share_quantity: float
    price_per_share: float
    total_amount: float
    fees: float
    investment_type: InvestmentType
    status: InvestmentStatus = InvestmentStatus.PENDING
    is_fractional: bool = False
    notes: str = ""

@dataclass
class DividendPayment:
    """Dividend payment record."""
    dividend_id: str
    company_id: str
    ticker: str
    payment_date: str
    record_date: str
    shares_held: float
    dividend_per_share: float
    total_amount: float
    is_reinvested: bool = False
    reinvestment_price: float = 0
    reinvestment_shares: float = 0
    notes: str = ""

@dataclass
class CorporateAction:
    """Corporate action event."""
    action_id: str
    company_id: str
    ticker: str
    action_type: CorporateActionType
    announcement_date: str
    effective_date: str
    description: str
    impact: str = ""
    is_mandatory: bool = True
    requires_action: bool = False
    status: str = "pending"
    notes: str = ""

@dataclass
class TransferAgentAccount:
    """Transfer agent account details."""
    account_id: str
    transfer_agent: TransferAgent
    account_number: str
    is_active: bool = True
    holdings: List[str] = field(default_factory=list)
    cash_balance: float = 0
    opened_date: str = ""
    last_activity: str = ""
    notes: str = ""

@dataclass
class DirectInvestmentPlan:
    """Direct investment plan configuration."""
    plan_id: str
    name: str
    description: str
    target_companies: List[str] = field(default_factory=list)
    monthly_investment: float = 0
    strategy: str = "dca"  # dca, value, growth
    is_active: bool = True
    started_date: str = ""
    total_invested: float = 0
    notes: str = ""


# =============================================================================
# MAIN ENGINE
# =============================================================================

class DirectInvestmentEngine:
    """
    Direct investment engine for bypassing brokers.
    
    Manages DRS holdings, DSPP enrollments, direct purchases,
    dividend reinvestment, and corporate actions.
    """
    
    def __init__(self):
        self.companies: Dict[str, Company] = {}
        self.holdings: Dict[str, DirectHolding] = {}
        self.purchases: Dict[str, DirectPurchase] = {}
        self.dividends: Dict[str, DividendPayment] = {}
        self.corporate_actions: Dict[str, CorporateAction] = {}
        self.transfer_agent_accounts: Dict[str, TransferAgentAccount] = {}
        self.investment_plans: Dict[str, DirectInvestmentPlan] = {}
        
        # Initialize transfer agent configs
        self.transfer_agent_configs: Dict[TransferAgent, Dict[str, Any]] = {
            TransferAgent.COMPUTERSHARE: {
                "base_url": "https://www-us.computershare.com/Investor",
                "phone": "1-800-962-4284",
                "website": "https://www.computershare.com",
                "features": ["DSPP", "DRIP", "DRS", "Direct Purchase"],
                "coverage": "1000+ companies",
                "fee_structure": "varies by company",
            },
            TransferAgent.EQUINITI: {
                "base_url": "https://www.equiniti.com/us/ast-access/individuals",
                "phone": "1-800-937-5449",
                "website": "https://www.equiniti.com",
                "features": ["DSPP", "DRIP", "DRS"],
                "coverage": "500+ companies",
                "fee_structure": "varies by company",
            },
            TransferAgent.CONTINENTAL_STOCK: {
                "base_url": "https://continentalstock.com",
                "phone": "1-212-509-4000",
                "website": "https://continentalstock.com",
                "features": ["DRIP", "DSPP", "DRS", "Share Sale"],
                "coverage": "1000+ companies",
                "fee_structure": "varies by company",
            },
            TransferAgent.VSTOCK_TRANSFER: {
                "base_url": "https://vstocktransfer.com",
                "phone": "1-212-828-8436",
                "website": "https://vstocktransfer.com",
                "features": ["DRS", "DWAC", "Physical Certificates"],
                "coverage": "1000+ issuers",
                "fee_structure": "per transaction",
            },
            TransferAgent.COLONIAL_STOCK: {
                "base_url": "https://colonialstock.com",
                "phone": "1-801-355-5740",
                "website": "https://colonialstock.com",
                "features": ["DRS", "DWAC", "Corporate Actions"],
                "coverage": "500+ companies",
                "fee_structure": "varies by company",
            },
            TransferAgent.AST: {
                "base_url": "https://www.astfinancial.com",
                "phone": "1-800-937-5449",
                "website": "https://www.astfinancial.com",
                "features": ["DSPP", "DRIP", "DRS", "ESPP"],
                "coverage": "Large cap specialist",
                "fee_structure": "varies by company",
            },
        }
        
        # Initialize known companies with DSPP/DRS
        self._init_known_companies()
    
    def _init_known_companies(self):
        """Initialize known companies with direct investment options."""
        companies = [
            Company(
                company_id="ko",
                name="Coca-Cola Co",
                ticker="KO",
                sector="Consumer Staples",
                industry="Beverages",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=50,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=3.0,
            ),
            Company(
                company_id="intc",
                name="Intel Corporation",
                ticker="INTC",
                sector="Technology",
                industry="Semiconductors",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=50,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=2.5,
            ),
            Company(
                company_id="wmt",
                name="Walmart Inc",
                ticker="WMT",
                sector="Consumer Staples",
                industry="Retail",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=1.5,
            ),
            Company(
                company_id="cost",
                name="Costco Wholesale",
                ticker="COST",
                sector="Consumer Staples",
                industry="Retail",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=25,
                purchase_fee=3.50,
                sell_fee=15,
                dividend_yield=0.7,
            ),
            Company(
                company_id="sbux",
                name="Starbucks Corporation",
                ticker="SBUX",
                sector="Consumer Discretionary",
                industry="Restaurants",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=2.3,
            ),
            Company(
                company_id="msft",
                name="Microsoft Corporation",
                ticker="MSFT",
                sector="Technology",
                industry="Software",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=False,
                has_drip=True,
                has_drs=True,
                min_initial_investment=0,
                min_recurring_investment=0,
                purchase_fee=0,
                sell_fee=0,
                dividend_yield=0.8,
            ),
            Company(
                company_id="jnj",
                name="Johnson & Johnson",
                ticker="JNJ",
                sector="Healthcare",
                industry="Pharmaceuticals",
                transfer_agent=TransferAgent.EQUINITI,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=2.9,
            ),
            Company(
                company_id="pg",
                name="Procter & Gamble",
                ticker="PG",
                sector="Consumer Staples",
                industry="Household Products",
                transfer_agent=TransferAgent.EQUINITI,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=2.4,
            ),
            Company(
                company_id="t",
                name="AT&T Inc",
                ticker="T",
                sector="Communication Services",
                industry="Telecom",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=500,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=5.5,
            ),
            Company(
                company_id="xom",
                name="Exxon Mobil Corporation",
                ticker="XOM",
                sector="Energy",
                industry="Oil & Gas",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=5.2,
            ),
            Company(
                company_id="pfe",
                name="Pfizer Inc",
                ticker="PFE",
                sector="Healthcare",
                industry="Pharmaceuticals",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=5.8,
            ),
            Company(
                company_id="cvx",
                name="Chevron Corporation",
                ticker="CVX",
                sector="Energy",
                industry="Oil & Gas",
                transfer_agent=TransferAgent.COMPUTERSHARE,
                has_dspp=True,
                has_drip=True,
                has_drs=True,
                min_initial_investment=250,
                min_recurring_investment=50,
                purchase_fee=0,
                sell_fee=15,
                dividend_yield=4.0,
            ),
        ]
        
        for company in companies:
            self.companies[company.company_id] = company
    
    # -------------------------------------------------------------------------
    # COMPANY MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_company(self, company: Company) -> Company:
        """Add a company to the database."""
        self.companies[company.company_id] = company
        return company
    
    def get_company(self, company_id: str) -> Optional[Company]:
        """Get a company by ID."""
        return self.companies.get(company_id)
    
    def get_companies_with_dspp(self) -> List[Company]:
        """Get companies offering DSPPs."""
        return [c for c in self.companies.values() if c.has_dspp]
    
    def get_companies_with_drip(self) -> List[Company]:
        """Get companies offering DRIPs."""
        return [c for c in self.companies.values() if c.has_drip]
    
    def get_companies_by_transfer_agent(self, agent: TransferAgent) -> List[Company]:
        """Get companies by transfer agent."""
        return [c for c in self.companies.values() if c.transfer_agent == agent]
    
    # -------------------------------------------------------------------------
    # HOLDING MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_holding(self, holding: DirectHolding) -> DirectHolding:
        """Add a direct holding."""
        self.holdings[holding.holding_id] = holding
        return holding
    
    def get_holding(self, holding_id: str) -> Optional[DirectHolding]:
        """Get a holding by ID."""
        return self.holdings.get(holding_id)
    
    def get_holdings_by_company(self, company_id: str) -> List[DirectHolding]:
        """Get all holdings for a company."""
        return [h for h in self.holdings.values() if h.company_id == company_id]
    
    def get_holdings_by_transfer_agent(self, agent: TransferAgent) -> List[DirectHolding]:
        """Get holdings by transfer agent."""
        return [h for h in self.holdings.values() if h.transfer_agent == agent]
    
    def update_holding_price(self, holding_id: str, current_price: float) -> Optional[DirectHolding]:
        """Update holding with current price."""
        if holding_id in self.holdings:
            holding = self.holdings[holding_id]
            holding.current_price = current_price
            holding.current_market_value = holding.share_quantity * current_price
            holding.unrealized_gain_loss = holding.current_market_value - holding.total_cost_basis
            holding.unrealized_gain_loss_percent = (holding.unrealized_gain_loss / holding.total_cost_basis) * 100 if holding.total_cost_basis > 0 else 0
            return holding
        return None
    
    # -------------------------------------------------------------------------
    # DIRECT PURCHASES
    # -------------------------------------------------------------------------
    
    def add_purchase(self, purchase: DirectPurchase) -> DirectPurchase:
        """Add a direct purchase."""
        self.purchases[purchase.purchase_id] = purchase
        return purchase
    
    def create_direct_purchase(self, company_id: str, amount: float,
                                is_fractional: bool = True) -> Optional[DirectPurchase]:
        """Create a direct purchase order."""
        company = self.companies.get(company_id)
        if not company:
            return None
        
        # Simulate purchase execution
        price_per_share = self._get_simulated_price(company.ticker)
        share_quantity = amount / price_per_share if price_per_share > 0 else 0
        
        purchase = DirectPurchase(
            purchase_id=f"dp_{company_id}_{int(time.time())}",
            company_id=company_id,
            ticker=company.ticker,
            transfer_agent=company.transfer_agent,
            purchase_date=datetime.now().isoformat(),
            settlement_date=(datetime.now() + timedelta(days=3)).isoformat(),
            share_quantity=share_quantity,
            price_per_share=price_per_share,
            total_amount=amount,
            fees=company.purchase_fee,
            investment_type=InvestmentType.DSPP if company.has_dspp else InvestmentType.DIRECT_PURCHASE,
            is_fractional=is_fractional,
        )
        
        self.purchases[purchase.purchase_id] = purchase
        return purchase
    
    def _get_simulated_price(self, ticker: str) -> float:
        """Get simulated stock price."""
        prices = {
            "KO": 62.0,
            "INTC": 22.0,
            "WMT": 68.0,
            "COST": 920.0,
            "SBUX": 95.0,
            "MSFT": 420.0,
            "JNJ": 155.0,
            "PG": 165.0,
            "T": 22.0,
            "XOM": 110.0,
            "PFE": 28.0,
            "CVX": 160.0,
        }
        return prices.get(ticker, 100.0)
    
    # -------------------------------------------------------------------------
    # DIVIDEND MANAGEMENT
    # -------------------------------------------------------------------------
    
    def add_dividend(self, dividend: DividendPayment) -> DividendPayment:
        """Add a dividend payment."""
        self.dividends[dividend.dividend_id] = dividend
        return dividend
    
    def calculate_dividend(self, company_id: str, shares_held: float) -> Optional[DividendPayment]:
        """Calculate expected dividend payment."""
        company = self.companies.get(company_id)
        if not company or company.dividend_yield <= 0:
            return None
        
        price = self._get_simulated_price(company.ticker)
        annual_dividend = price * (company.dividend_yield / 100)
        quarterly_dividend = annual_dividend / 4
        total_amount = shares_held * quarterly_dividend
        
        dividend = DividendPayment(
            dividend_id=f"div_{company_id}_{int(time.time())}",
            company_id=company_id,
            ticker=company.ticker,
            payment_date=datetime.now().isoformat(),
            record_date=datetime.now().isoformat(),
            shares_held=shares_held,
            dividend_per_share=quarterly_dividend,
            total_amount=total_amount,
            is_reinvested=company.has_drip,
            reinvestment_price=price,
            reinvestment_shares=total_amount / price if company.has_drip else 0,
        )
        
        self.dividends[dividend.dividend_id] = dividend
        return dividend
    
    def get_dividends_by_company(self, company_id: str) -> List[DividendPayment]:
        """Get all dividends for a company."""
        return [d for d in self.dividends.values() if d.company_id == company_id]
    
    def get_total_dividend_income(self, period: str = "annual") -> float:
        """Get total dividend income."""
        total = sum(d.total_amount for d in self.dividends.values())
        if period == "annual":
            return total * 4  # Quarterly dividends
        elif period == "quarterly":
            return total
        elif period == "monthly":
            return total / 3
        return total
    
    # -------------------------------------------------------------------------
    # TRANSFER AGENT ACCOUNTS
    # -------------------------------------------------------------------------
    
    def add_transfer_agent_account(self, account: TransferAgentAccount) -> TransferAgentAccount:
        """Add a transfer agent account."""
        self.transfer_agent_accounts[account.account_id] = account
        return account
    
    def get_transfer_agent_account(self, account_id: str) -> Optional[TransferAgentAccount]:
        """Get a transfer agent account."""
        return self.transfer_agent_accounts.get(account_id)
    
    def get_accounts_by_agent(self, agent: TransferAgent) -> List[TransferAgentAccount]:
        """Get accounts by transfer agent."""
        return [a for a in self.transfer_agent_accounts.values() if a.transfer_agent == agent]
    
    # -------------------------------------------------------------------------
    # INVESTMENT PLANS
    # -------------------------------------------------------------------------
    
    def add_investment_plan(self, plan: DirectInvestmentPlan) -> DirectInvestmentPlan:
        """Add a direct investment plan."""
        self.investment_plans[plan.plan_id] = plan
        return plan
    
    def get_investment_plan(self, plan_id: str) -> Optional[DirectInvestmentPlan]:
        """Get an investment plan."""
        return self.investment_plans.get(plan_id)
    
    def get_active_plans(self) -> List[DirectInvestmentPlan]:
        """Get active investment plans."""
        return [p for p in self.investment_plans.values() if p.is_active]
    
    # -------------------------------------------------------------------------
    # PORTFOLIO ANALYSIS
    # -------------------------------------------------------------------------
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        total_holdings = len(self.holdings)
        total_market_value = sum(h.current_market_value for h in self.holdings.values())
        total_cost_basis = sum(h.total_cost_basis for h in self.holdings.values())
        total_unrealized_gain = total_market_value - total_cost_basis
        total_unrealized_gain_percent = (total_unrealized_gain / total_cost_basis) * 100 if total_cost_basis > 0 else 0
        
        # Holdings by transfer agent
        by_agent: Dict[str, int] = {}
        for holding in self.holdings.values():
            agent = holding.transfer_agent.value
            by_agent[agent] = by_agent.get(agent, 0) + 1
        
        # Holdings by type
        by_type: Dict[str, int] = {}
        for holding in self.holdings.values():
            ht = holding.holding_type.value
            by_type[ht] = by_type.get(ht, 0) + 1
        
        # Dividend income
        annual_dividend_income = self.get_total_dividend_income("annual")
        dividend_yield = (annual_dividend_income / total_market_value) * 100 if total_market_value > 0 else 0
        
        # Transfer agent accounts
        total_accounts = len(self.transfer_agent_accounts)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_holdings": total_holdings,
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "total_unrealized_gain_loss": total_unrealized_gain,
            "total_unrealized_gain_loss_percent": total_unrealized_gain_percent,
            "annual_dividend_income": annual_dividend_income,
            "portfolio_dividend_yield": dividend_yield,
            "holdings_by_transfer_agent": by_agent,
            "holdings_by_type": by_type,
            "total_transfer_agent_accounts": total_accounts,
            "total_companies_available": len(self.companies),
            "companies_with_dspp": len(self.get_companies_with_dspp()),
            "companies_with_drip": len(self.get_companies_with_drip()),
        }
    
    def get_transfer_agent_config(self, agent: TransferAgent) -> Dict[str, Any]:
        """Get transfer agent configuration."""
        return self.transfer_agent_configs.get(agent, {})
    
    # -------------------------------------------------------------------------
    # DIRECT INVESTMENT WORKFLOW
    # -------------------------------------------------------------------------
    
    def execute_direct_investment_workflow(self, company_id: str,
                                            investment_amount: float,
                                            enable_drip: bool = True) -> Dict[str, Any]:
        """
        Execute complete direct investment workflow.
        
        Steps:
        1. Find company and transfer agent
        2. Open transfer agent account
        3. Execute direct purchase
        4. Register shares in your name (DRS)
        5. Enable dividend reinvestment (DRIP) if available
        """
        company = self.companies.get(company_id)
        if not company:
            return {"error": "Company not found"}
        
        workflow = {
            "company": company.name,
            "ticker": company.ticker,
            "transfer_agent": company.transfer_agent.value,
            "steps": [],
        }
        
        # Step 1: Open transfer agent account
        account = TransferAgentAccount(
            account_id=f"ta_{company_id}_{int(time.time())}",
            transfer_agent=company.transfer_agent,
            account_number=f"CS{int(time.time())}",
            is_active=True,
            cash_balance=investment_amount,
            opened_date=datetime.now().isoformat(),
        )
        self.add_transfer_agent_account(account)
        workflow["steps"].append({
            "step": 1,
            "action": "Open transfer agent account",
            "status": "completed",
            "account_id": account.account_id,
        })
        
        # Step 2: Execute direct purchase
        purchase = self.create_direct_purchase(company_id, investment_amount)
        if purchase:
            workflow["steps"].append({
                "step": 2,
                "action": "Execute direct purchase",
                "status": "completed",
                "purchase_id": purchase.purchase_id,
                "shares": purchase.share_quantity,
                "price": purchase.price_per_share,
                "fees": purchase.fees,
            })
        
        # Step 3: Register shares (DRS)
        holding = DirectHolding(
            holding_id=f"hold_{company_id}_{int(time.time())}",
            company_id=company_id,
            ticker=company.ticker,
            transfer_agent=company.transfer_agent,
            holding_type=HoldingType.DSPP_PLAN if company.has_dspp else HoldingType.DRS_BOOK_ENTRY,
            share_quantity=purchase.share_quantity if purchase else 0,
            cost_basis_per_share=purchase.price_per_share if purchase else 0,
            current_price=purchase.price_per_share if purchase else 0,
            total_cost_basis=investment_amount,
            current_market_value=investment_amount,
            unrealized_gain_loss=0,
            unrealized_gain_loss_percent=0,
            dividend_reinvestment=enable_drip and company.has_drip,
            registration_date=datetime.now().isoformat(),
        )
        self.add_holding(holding)
        workflow["steps"].append({
            "step": 3,
            "action": "Register shares in your name (DRS)",
            "status": "completed",
            "holding_id": holding.holding_id,
        })
        
        # Step 4: Enable DRIP
        if enable_drip and company.has_drip:
            workflow["steps"].append({
                "step": 4,
                "action": "Enable dividend reinvestment (DRIP)",
                "status": "completed",
            })
        
        workflow["total_invested"] = investment_amount
        workflow["shares_acquired"] = purchase.share_quantity if purchase else 0
        workflow["annual_dividend_estimate"] = investment_amount * (company.dividend_yield / 100)
        
        return workflow


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

direct_investment_engine = DirectInvestmentEngine()