#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Net Worth Self-Governance

Live net worth tracking system that distinguishes work vs personal assets.
Fetches live data, tracks loss/increase ratios, and self-governs.

Features:
- Live asset price fetching (stocks, crypto, real estate, etc.)
- Work vs personal asset separation
- Loss/increase ratio tracking
- Self-governance automation
- Net worth history and projections
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

LOG = __import__("logging").getLogger("qb_protocol.being.chip.net_worth")


class AssetType(Enum):
    """Types of assets for net worth calculation."""
    # Liquid assets
    CASH = "cash"
    SAVINGS = "savings"
    CHECKING = "checking"
    MONEY_MARKET = "money_market"
    
    # Investments
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    MUTUAL_FUND = "mutual_fund"
    INDEX_FUND = "index_fund"
    
    # Crypto
    CRYPTO = "crypto"
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    ALTCOIN = "altcoin"
    NFT = "nft"
    
    # Real Estate
    REAL_ESTATE = "real_estate"
    PRIMARY_RESIDENCE = "primary_residence"
    RENTAL_PROPERTY = "rental_property"
    LAND = "land"
    
    # Retirement
    _401K = "401k"
    IRA = "ira"
    ROTH_IRA = "roth_ira"
    PENSION = "pension"
    
    # Business
    BUSINESS_EQUITY = "business_equity"
    STARTUP_EQUITY = "startup_equity"
    PRIVATE_EQUITY = "private_equity"
    
    # Personal Property
    VEHICLE = "vehicle"
    JEWELRY = "jewelry"
    ART = "art"
    COLLECTIBLES = "collectibles"
    ELECTRONICS = "electronics"
    
    # Debt (negative)
    CREDIT_CARD_DEBT = "credit_card_debt"
    STUDENT_LOAN = "student_loan"
    MORTGAGE = "mortgage"
    CAR_LOAN = "car_loan"
    PERSONAL_LOAN = "personal_loan"
    MARGIN_LOAN = "margin_loan"


class AssetCategory(Enum):
    """Work vs Personal classification."""
    WORK = "work"
    PERSONAL = "personal"
    SHARED = "shared"


class DataSource(Enum):
    """Live data sources for price fetching."""
    YAHOO_FINANCE = "yahoo_finance"
    COINBASE = "coinbase"
    COINGECKO = "coingecko"
    ALPHA_VANTAGE = "alpha_vantage"
    MANUAL = "manual"
    ESTIMATE = "estimate"


@dataclass
class Asset:
    """Individual asset holding."""
    asset_id: str
    name: str
    symbol: str
    asset_type: AssetType
    category: AssetCategory
    quantity: float
    cost_basis: float  # Original purchase price per unit
    current_price: float  # Current market price per unit
    data_source: DataSource
    last_updated: str
    notes: str = ""
    
    @property
    def total_value(self) -> float:
        """Total current value."""
        return self.quantity * self.current_price
    
    @property
    def total_cost_basis(self) -> float:
        """Total cost basis."""
        return self.quantity * self.cost_basis
    
    @property
    def gain_loss(self) -> float:
        """Unrealized gain/loss."""
        return self.total_value - self.total_cost_basis
    
    @property
    def gain_loss_ratio(self) -> float:
        """Gain/loss as ratio of cost basis."""
        if self.total_cost_basis == 0:
            return 0.0
        return (self.total_value - self.total_cost_basis) / self.total_cost_basis
    
    @property
    def is_debt(self) -> bool:
        """Is this a debt (negative asset)?"""
        return self.asset_type in [
            AssetType.CREDIT_CARD_DEBT,
            AssetType.STUDENT_LOAN,
            AssetType.MORTGAGE,
            AssetType.CAR_LOAN,
            AssetType.PERSONAL_LOAN,
            AssetType.MARGIN_LOAN
        ]


@dataclass
class NetWorthSnapshot:
    """Point-in-time net worth snapshot."""
    snapshot_id: str
    timestamp: str
    total_assets: float
    total_debts: float
    net_worth: float
    work_assets: float
    personal_assets: float
    work_debts: float
    personal_debts: float
    work_net_worth: float
    personal_net_worth: float
    change_from_previous: float
    change_ratio: float


@dataclass
class GovernanceRule:
    """Self-governance rule for net worth management."""
    rule_id: str
    name: str
    description: str
    trigger_condition: str
    action: str
    is_active: bool = True
    last_triggered: Optional[str] = None
    trigger_count: int = 0


@dataclass
class PriceAlert:
    """Price alert for an asset."""
    alert_id: str
    asset_id: str
    symbol: str
    alert_type: str  # "above", "below", "change_percent"
    target_price: float
    is_active: bool = True
    triggered: bool = False
    last_checked: Optional[str] = None


class NetWorthGovernor:
    """
    Net worth self-governance system.
    
    Fetches live data, tracks work vs personal assets,
    monitors loss/increase ratios, and self-governs.
    """
    
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.snapshots: List[NetWorthSnapshot] = []
        self.governance_rules: List[GovernanceRule] = []
        self.price_alerts: List[PriceAlert] = []
        self.last_fetch_time: Optional[str] = None
        self.fetch_interval_seconds: int = 300  # 5 minutes
        
        # Initialize default governance rules
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default self-governance rules."""
        default_rules = [
            GovernanceRule(
                rule_id="rule_001",
                name="Debt Warning",
                description="Alert when debt exceeds 30% of total assets",
                trigger_condition="total_debts > total_assets * 0.3",
                action="alert_user"
            ),
            GovernanceRule(
                rule_id="rule_002",
                name="Concentration Risk",
                description="Alert when single asset exceeds 25% of portfolio",
                trigger_condition="any_asset_value > total_assets * 0.25",
                action="suggest_diversification"
            ),
            GovernanceRule(
                rule_id="rule_003",
                name="Loss Limit",
                description="Alert when unrealized loss exceeds 10% on any position",
                trigger_condition="any_asset_gain_loss_ratio < -0.10",
                action="review_position"
            ),
            GovernanceRule(
                rule_id="rule_004",
                name="Gain Realization",
                description="Alert when unrealized gain exceeds 50% on any position",
                trigger_condition="any_asset_gain_loss_ratio > 0.50",
                action="consider_taking_profits"
            ),
            GovernanceRule(
                rule_id="rule_005",
                name="Work/Personal Balance",
                description="Alert when work assets exceed 80% of total",
                trigger_condition="work_assets > total_assets * 0.8",
                action="suggest_personal_investment"
            ),
        ]
        self.governance_rules.extend(default_rules)
    
    def add_asset(self, asset: Asset) -> Asset:
        """Add an asset to track."""
        self.assets[asset.asset_id] = asset
        return asset
    
    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset from tracking."""
        if asset_id in self.assets:
            del self.assets[asset_id]
            return True
        return False
    
    def update_asset_price(self, asset_id: str, new_price: float) -> bool:
        """Update the current price of an asset."""
        if asset_id in self.assets:
            self.assets[asset_id].current_price = new_price
            self.assets[asset_id].last_updated = datetime.now().isoformat()
            return True
        return False
    
    def fetch_live_prices(self) -> Dict[str, float]:
        """
        Fetch live prices for all tracked assets.
        
        Uses multiple data sources:
        - Yahoo Finance for stocks/ETFs
        - CoinGecko for crypto
        - Manual for others
        """
        prices = {}
        
        for asset_id, asset in self.assets.items():
            try:
                if asset.asset_type in [AssetType.STOCK, AssetType.ETF, AssetType.INDEX_FUND, AssetType.MUTUAL_FUND]:
                    price = self._fetch_yahoo_price(asset.symbol)
                elif asset.asset_type in [AssetType.CRYPTO, AssetType.BITCOIN, AssetType.ETHEREUM, AssetType.ALTCOIN]:
                    price = self._fetch_crypto_price(asset.symbol)
                elif asset.asset_type == AssetType.REAL_ESTATE:
                    price = asset.current_price  # Real estate doesn't update frequently
                else:
                    price = asset.current_price  # Manual assets
                
                if price is not None:
                    prices[asset_id] = price
                    self.assets[asset_id].current_price = price
                    self.assets[asset_id].last_updated = datetime.now().isoformat()
                    
            except Exception as e:
                LOG.warning(f"Failed to fetch price for {asset.symbol}: {e}")
                prices[asset_id] = asset.current_price
        
        self.last_fetch_time = datetime.now().isoformat()
        return prices
    
    def _fetch_yahoo_price(self, symbol: str) -> Optional[float]:
        """Fetch stock price from Yahoo Finance."""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    if 'meta' in result and 'regularMarketPrice' in result['meta']:
                        return result['meta']['regularMarketPrice']
            
            return None
        except Exception as e:
            LOG.warning(f"Yahoo Finance fetch failed for {symbol}: {e}")
            return None
    
    def _fetch_crypto_price(self, symbol: str) -> Optional[float]:
        """Fetch crypto price from CoinGecko."""
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'SOL': 'solana',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'AVAX': 'avalanche-2',
                'MATIC': 'matic-network',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'AAVE': 'aave',
            }
            
            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if coin_id in data and 'usd' in data[coin_id]:
                    return data[coin_id]['usd']
            
            return None
        except Exception as e:
            LOG.warning(f"CoinGecko fetch failed for {symbol}: {e}")
            return None
    
    def calculate_net_work(self) -> Dict[str, Any]:
        """Calculate current net worth breakdown."""
        total_assets = 0.0
        total_debts = 0.0
        work_assets = 0.0
        personal_assets = 0.0
        work_debts = 0.0
        personal_debts = 0.0
        
        asset_breakdown = {}
        
        for asset in self.assets.values():
            value = asset.total_value
            
            if asset.is_debt:
                total_debts += abs(value)
                if asset.category == AssetCategory.WORK:
                    work_debts += abs(value)
                else:
                    personal_debts += abs(value)
            else:
                total_assets += value
                if asset.category == AssetCategory.WORK:
                    work_assets += value
                else:
                    personal_assets += value
            
            asset_breakdown[asset.asset_id] = {
                "name": asset.name,
                "symbol": asset.symbol,
                "type": asset.asset_type.value,
                "category": asset.category.value,
                "quantity": asset.quantity,
                "current_price": asset.current_price,
                "total_value": value,
                "gain_loss": asset.gain_loss,
                "gain_loss_ratio": asset.gain_loss_ratio,
                "is_debt": asset.is_debt
            }
        
        net_worth = total_assets - total_debts
        work_net_worth = work_assets - work_debts
        personal_net_worth = personal_assets - personal_debts
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_assets": round(total_assets, 2),
            "total_debts": round(total_debts, 2),
            "net_worth": round(net_worth, 2),
            "work_assets": round(work_assets, 2),
            "personal_assets": round(personal_assets, 2),
            "work_debts": round(work_debts, 2),
            "personal_debts": round(personal_debts, 2),
            "work_net_worth": round(work_net_worth, 2),
            "personal_net_worth": round(personal_net_worth, 2),
            "asset_breakdown": asset_breakdown,
            "debt_to_asset_ratio": round(total_debts / total_assets, 4) if total_assets > 0 else 0,
            "work_asset_ratio": round(work_assets / total_assets, 4) if total_assets > 0 else 0,
        }
    
    def create_snapshot(self) -> NetWorthSnapshot:
        """Create a point-in-time snapshot of net worth."""
        calc = self.calculate_net_work()
        
        # Calculate change from previous snapshot
        change = 0.0
        change_ratio = 0.0
        if self.snapshots:
            prev = self.snapshots[-1]
            change = calc["net_worth"] - prev.net_worth
            change_ratio = change / prev.net_worth if prev.net_worth != 0 else 0.0
        
        snapshot = NetWorthSnapshot(
            snapshot_id=f"snapshot_{len(self.snapshots)}",
            timestamp=calc["timestamp"],
            total_assets=calc["total_assets"],
            total_debts=calc["total_debts"],
            net_worth=calc["net_worth"],
            work_assets=calc["work_assets"],
            personal_assets=calc["personal_assets"],
            work_debts=calc["work_debts"],
            personal_debts=calc["personal_debts"],
            work_net_worth=calc["work_net_worth"],
            personal_net_worth=calc["personal_net_worth"],
            change_from_previous=round(change, 2),
            change_ratio=round(change_ratio, 4)
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def check_governance_rules(self) -> List[Dict[str, Any]]:
        """Check all governance rules and return triggered actions."""
        calc = self.calculate_net_work()
        triggered = []
        
        for rule in self.governance_rules:
            if not rule.is_active:
                continue
            
            triggered_flag = False
            
            if rule.rule_id == "rule_001":
                # Debt Warning
                if calc["debt_to_asset_ratio"] > 0.3:
                    triggered_flag = True
                    
            elif rule.rule_id == "rule_002":
                # Concentration Risk
                for asset_data in calc["asset_breakdown"].values():
                    if not asset_data["is_debt"] and asset_data["total_value"] > calc["total_assets"] * 0.25:
                        triggered_flag = True
                        break
                        
            elif rule.rule_id == "rule_003":
                # Loss Limit
                for asset_data in calc["asset_breakdown"].values():
                    if asset_data["gain_loss_ratio"] < -0.10:
                        triggered_flag = True
                        break
                        
            elif rule.rule_id == "rule_004":
                # Gain Realization
                for asset_data in calc["asset_breakdown"].values():
                    if asset_data["gain_loss_ratio"] > 0.50:
                        triggered_flag = True
                        break
                        
            elif rule.rule_id == "rule_005":
                # Work/Personal Balance
                if calc["work_asset_ratio"] > 0.8:
                    triggered_flag = True
            
            if triggered_flag:
                rule.last_triggered = datetime.now().isoformat()
                rule.trigger_count += 1
                triggered.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "action": rule.action,
                    "trigger_count": rule.trigger_count
                })
        
        return triggered
    
    def add_governance_rule(self, rule: GovernanceRule) -> GovernanceRule:
        """Add a custom governance rule."""
        self.governance_rules.append(rule)
        return rule
    
    def add_price_alert(self, alert: PriceAlert) -> PriceAlert:
        """Add a price alert."""
        self.price_alerts.append(alert)
        return alert
    
    def check_price_alerts(self) -> List[Dict[str, Any]]:
        """Check all price alerts."""
        triggered = []
        
        for alert in self.price_alerts:
            if not alert.is_active or alert.triggered:
                continue
            
            # Find the asset
            asset = self.assets.get(alert.asset_id)
            if not asset:
                continue
            
            should_trigger = False
            
            if alert.alert_type == "above" and asset.current_price >= alert.target_price:
                should_trigger = True
            elif alert.alert_type == "below" and asset.current_price <= alert.target_price:
                should_trigger = True
            
            if should_trigger:
                alert.triggered = True
                alert.last_checked = datetime.now().isoformat()
                triggered.append({
                    "alert_id": alert.alert_id,
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type,
                    "target_price": alert.target_price,
                    "current_price": asset.current_price
                })
        
        return triggered
    
    def get_gain_loss_summary(self) -> Dict[str, Any]:
        """Get summary of gains and losses."""
        total_unrealized_gain = 0.0
        winners = []
        losers = []
        
        for asset in self.assets.values():
            if asset.is_debt:
                continue
            
            gain = asset.gain_loss
            total_unrealized_gain += gain
            
            if gain > 0:
                winners.append({
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "gain": gain,
                    "gain_ratio": asset.gain_loss_ratio
                })
            elif gain < 0:
                losers.append({
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "loss": gain,
                    "loss_ratio": asset.gain_loss_ratio
                })
        
        # Sort by gain/loss amount
        winners.sort(key=lambda x: x["gain"], reverse=True)
        losers.sort(key=lambda x: x["loss"])
        
        return {
            "total_unrealized_gain": round(total_unrealized_gain, 2),
            "winners": winners,
            "losers": losers,
            "winner_count": len(winners),
            "loser_count": len(losers)
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get complete net worth governance state."""
        calc = self.calculate_net_work()
        gain_loss = self.get_gain_loss_summary()
        triggered_rules = self.check_governance_rules()
        triggered_alerts = self.check_price_alerts()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "net_worth": calc,
            "gain_loss_summary": gain_loss,
            "governance_alerts": triggered_rules,
            "price_alerts": triggered_alerts,
            "total_assets_tracked": len(self.assets),
            "total_snapshots": len(self.snapshots),
            "active_governance_rules": len([r for r in self.governance_rules if r.is_active]),
            "last_fetch_time": self.last_fetch_time
        }


# Global instance
net_worth_governor = NetWorthGovernor()
