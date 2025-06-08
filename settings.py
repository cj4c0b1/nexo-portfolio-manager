import os
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