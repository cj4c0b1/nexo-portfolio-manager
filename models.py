from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from cryptography.fernet import Fernet
import os

@dataclass
class Portfolio:
    id: int
    name: str
    allocation: Dict[str, float]  # token -> percentage
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'allocation': json.dumps(self.allocation),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data['id'],
            name=data['name'],
            allocation=json.loads(data['allocation']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            is_active=data['is_active']
        )

@dataclass
class Transaction:
    id: int
    portfolio_id: int
    token: str
    transaction_type: str  # 'buy', 'sell', 'rebalance'
    quantity: float
    price: float
    fee: float
    platform: str  # 'nexo' or 'nexo_pro'
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'token': self.token,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'price': self.price,
            'fee': self.fee,
            'platform': self.platform,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class RebalanceEvent:
    id: int
    portfolio_id: int
    trigger_type: str  # 'time', 'threshold', 'manual'
    old_allocation: Dict[str, float]
    new_allocation: Dict[str, float]
    executed_trades: List[Dict]
    total_cost: float
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'trigger_type': self.trigger_type,
            'old_allocation': json.dumps(self.old_allocation),
            'new_allocation': json.dumps(self.new_allocation),
            'executed_trades': json.dumps(self.executed_trades),
            'total_cost': self.total_cost,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class PortfolioSnapshot:
    id: int
    portfolio_id: int
    balances: Dict[str, float]  # token -> quantity
    prices: Dict[str, float]    # token -> price in USD
    total_value: float
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'balances': json.dumps(self.balances),
            'prices': json.dumps(self.prices),
            'total_value': self.total_value,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class RebalanceSettings:
    id: int
    portfolio_id: int
    frequency: str  # 'daily', 'weekly', 'monthly'
    threshold: float  # percentage deviation that triggers rebalance
    min_trade_value: float
    auto_rebalance: bool
    paper_trading: bool
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'frequency': self.frequency,
            'threshold': self.threshold,
            'min_trade_value': self.min_trade_value,
            'auto_rebalance': self.auto_rebalance,
            'paper_trading': self.paper_trading,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class APIKey:
    """Represents an API key for an exchange."""
    
    id: int
    exchange: str
    name: str
    api_key: str
    api_secret: str
    portfolio_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self, mask_sensitive: bool = True) -> Dict[str, Any]:
        """Convert the API key to a dictionary.
        
        Args:
            mask_sensitive: If True, masks the API key and secret for security.
        """
        return {
            'id': self.id,
            'exchange': self.exchange,
            'name': self.name,
            'api_key': '••••••••' + self.api_key[-4:] if mask_sensitive and self.api_key else self.api_key,
            'api_secret': '••••••••' + self.api_secret[-4:] if mask_sensitive and self.api_secret else self.api_secret,
            'portfolio_id': self.portfolio_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIKey':
        """Create an APIKey instance from a dictionary."""
        return cls(
            id=data.get('id', 0),
            exchange=data['exchange'],
            name=data['name'],
            api_key=data['api_key'],
            api_secret=data['api_secret'],
            portfolio_id=data.get('portfolio_id'),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.utcnow()
        )
    
    def get_credentials(self) -> Dict[str, str]:
        """Get the API credentials for authentication."""
        return {
            'api_key': self.api_key,
            'api_secret': self.api_secret
        }