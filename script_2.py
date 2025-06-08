# Create config/settings.py
settings_content = """import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Application
    APP_NAME = os.getenv("APP_NAME", "Nexo Portfolio Manager")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///portfolio.db")
    DATA_DIR = Path("data")
    DATABASE_PATH = DATA_DIR / "portfolio.db"
    
    # Nexo API
    NEXO_PUBLIC_KEY = os.getenv("NEXO_PUBLIC_KEY")
    NEXO_SECRET_KEY = os.getenv("NEXO_SECRET_KEY")
    
    # Supported tokens
    SUPPORTED_TOKENS = [
        "BTC", "ETH", "ADA", "DOT", "MATIC", 
        "LINK", "UNI", "SOL", "AVAX", "NEXO",
        "USDT", "USDC"
    ]
    
    # Trading pairs for Nexo Pro
    NEXO_PRO_PAIRS = [
        "BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT", 
        "MATIC/USDT", "LINK/USDT", "UNI/USDT", "SOL/USDT", 
        "AVAX/USDT", "NEXO/USDT"
    ]
    
    # Rebalancing settings
    DEFAULT_REBALANCE_THRESHOLD = 5.0  # 5% deviation
    DEFAULT_REBALANCE_FREQUENCY = "weekly"
    MIN_TRADE_VALUE = 10.0  # Minimum trade value in USD
    
    # Risk management
    MAX_POSITION_SIZE = 50.0  # Maximum 50% in any single asset
    EMERGENCY_STOP_LOSS = 20.0  # 20% portfolio loss threshold
    
    # Email notifications (optional)
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

# Global settings instance
settings = Settings()
"""

with open("nexo_portfolio_manager/config/settings.py", "w") as f:
    f.write(settings_content.strip())

# Create app/db/models.py
models_content = """from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import json

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
"""

with open("nexo_portfolio_manager/app/db/models.py", "w") as f:
    f.write(models_content.strip())

print("Created configuration and models files!")