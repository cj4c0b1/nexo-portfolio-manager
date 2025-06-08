import unittest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import DatabaseManager
from app.db.models import Portfolio
from app.components.portfolio import PortfolioManager
from app.api.market_data import MarketDataProvider

class TestPortfolioManager(unittest.TestCase):
    """Test cases for Portfolio Manager"""

    def setUp(self):
        """Set up test fixtures"""
        # Use in-memory database for testing
        self.db = DatabaseManager(":memory:")
        self.portfolio_manager = PortfolioManager()
        self.portfolio_manager.db = self.db

    def test_create_portfolio(self):
        """Test portfolio creation"""
        allocation = {
            "BTC": 50.0,
            "ETH": 30.0,
            "USDT": 20.0
        }

        portfolio = self.portfolio_manager.create_portfolio("Test Portfolio", allocation)

        self.assertIsInstance(portfolio, Portfolio)
        self.assertEqual(portfolio.name, "Test Portfolio")
        self.assertEqual(portfolio.allocation, allocation)
        self.assertTrue(portfolio.is_active)

    def test_invalid_allocation(self):
        """Test portfolio creation with invalid allocation"""
        # Allocation that doesn't sum to 100%
        invalid_allocation = {
            "BTC": 60.0,
            "ETH": 30.0
        }

        with self.assertRaises(ValueError):
            self.portfolio_manager.create_portfolio("Invalid Portfolio", invalid_allocation)

    def test_unsupported_token(self):
        """Test portfolio creation with unsupported token"""
        allocation = {
            "BTC": 50.0,
            "INVALID_TOKEN": 50.0
        }

        with self.assertRaises(ValueError):
            self.portfolio_manager.create_portfolio("Invalid Token Portfolio", allocation)

class TestMarketDataProvider(unittest.TestCase):
    """Test cases for Market Data Provider"""

    def setUp(self):
        self.market_data = MarketDataProvider()

    def test_get_current_prices(self):
        """Test getting current prices"""
        tokens = ["BTC", "ETH", "USDT"]
        prices = self.market_data.get_current_prices(tokens)

        self.assertEqual(len(prices), 3)
        self.assertIn("BTC", prices)
        self.assertIn("ETH", prices)
        self.assertIn("USDT", prices)

        # Check that prices are positive
        for token, price in prices.items():
            self.assertGreater(price, 0)

if __name__ == "__main__":
    unittest.main()
