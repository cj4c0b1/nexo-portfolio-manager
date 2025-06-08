# Create run.py - Easy script to run the application
run_script_content = """#!/usr/bin/env python3
\"\"\"
Nexo Portfolio Manager - Run Script

Simple script to start the Streamlit application.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    \"\"\"Check if required packages are installed\"\"\"
    try:
        import streamlit
        import pandas
        import plotly
        import requests
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    \"\"\"Check if .env file exists\"\"\"
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("Copy .env.example to .env and add your API credentials")
        print("The app will run in mock mode without API credentials")
        return False

def main():
    \"\"\"Run the Streamlit application\"\"\"
    
    print("🚀 Starting Nexo Portfolio Manager...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment file
    check_env_file()
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Run Streamlit
    try:
        print("\\n🌐 Starting Streamlit server...")
        print("📱 The application will open in your default browser")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/main.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
        
    except KeyboardInterrupt:
        print("\\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

with open("nexo_portfolio_manager/run.py", "w") as f:
    f.write(run_script_content.strip())

# Create a sample test file
test_content = """import unittest
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
    \"\"\"Test cases for Portfolio Manager\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures\"\"\"
        # Use in-memory database for testing
        self.db = DatabaseManager(":memory:")
        self.portfolio_manager = PortfolioManager()
        self.portfolio_manager.db = self.db
    
    def test_create_portfolio(self):
        \"\"\"Test portfolio creation\"\"\"
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
        \"\"\"Test portfolio creation with invalid allocation\"\"\"
        # Allocation that doesn't sum to 100%
        invalid_allocation = {
            "BTC": 60.0,
            "ETH": 30.0
        }
        
        with self.assertRaises(ValueError):
            self.portfolio_manager.create_portfolio("Invalid Portfolio", invalid_allocation)
    
    def test_unsupported_token(self):
        \"\"\"Test portfolio creation with unsupported token\"\"\"
        allocation = {
            "BTC": 50.0,
            "INVALID_TOKEN": 50.0
        }
        
        with self.assertRaises(ValueError):
            self.portfolio_manager.create_portfolio("Invalid Token Portfolio", allocation)
    
    def test_portfolio_retrieval(self):
        \"\"\"Test portfolio retrieval\"\"\"
        allocation = {"BTC": 100.0}
        created_portfolio = self.portfolio_manager.create_portfolio("Test", allocation)
        
        retrieved_portfolio = self.db.get_portfolio(created_portfolio.id)
        
        self.assertIsNotNone(retrieved_portfolio)
        self.assertEqual(retrieved_portfolio.name, "Test")
        self.assertEqual(retrieved_portfolio.allocation, allocation)

class TestMarketDataProvider(unittest.TestCase):
    \"\"\"Test cases for Market Data Provider\"\"\"
    
    def setUp(self):
        self.market_data = MarketDataProvider()
    
    def test_get_current_prices(self):
        \"\"\"Test getting current prices\"\"\"
        tokens = ["BTC", "ETH", "USDT"]
        prices = self.market_data.get_current_prices(tokens)
        
        self.assertEqual(len(prices), 3)
        self.assertIn("BTC", prices)
        self.assertIn("ETH", prices)
        self.assertIn("USDT", prices)
        
        # Check that prices are positive
        for token, price in prices.items():
            self.assertGreater(price, 0)
    
    def test_stablecoin_price(self):
        \"\"\"Test that stablecoins have price of 1.0\"\"\"
        prices = self.market_data.get_current_prices(["USDT", "USDC"])
        
        self.assertEqual(prices["USDT"], 1.0)
        self.assertEqual(prices["USDC"], 1.0)
    
    def test_portfolio_value_calculation(self):
        \"\"\"Test portfolio value calculation\"\"\"
        balances = {
            "BTC": 0.1,
            "ETH": 1.0,
            "USDT": 1000.0
        }
        
        result = self.market_data.calculate_portfolio_value(balances)
        
        self.assertIn("total_value", result)
        self.assertIn("asset_values", result)
        self.assertIn("prices", result)
        
        self.assertGreater(result["total_value"], 0)
        self.assertEqual(len(result["asset_values"]), 3)

class TestDatabaseOperations(unittest.TestCase):
    \"\"\"Test database operations\"\"\"
    
    def setUp(self):
        self.db = DatabaseManager(":memory:")
    
    def test_database_initialization(self):
        \"\"\"Test that database tables are created\"\"\"
        # This test passes if no exception is raised during initialization
        self.assertIsNotNone(self.db)
    
    def test_portfolio_crud_operations(self):
        \"\"\"Test Create, Read, Update operations for portfolios\"\"\"
        # Create
        allocation = {"BTC": 60.0, "ETH": 40.0}
        portfolio = self.db.create_portfolio("CRUD Test", allocation)
        
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.name, "CRUD Test")
        
        # Read
        retrieved = self.db.get_portfolio(portfolio.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "CRUD Test")
        
        # Update
        new_allocation = {"BTC": 50.0, "ETH": 50.0}
        success = self.db.update_portfolio(portfolio.id, new_allocation)
        
        self.assertTrue(success)
        
        # Verify update
        updated = self.db.get_portfolio(portfolio.id)
        self.assertEqual(updated.allocation, new_allocation)

if __name__ == "__main__":
    unittest.main()
"""

with open("nexo_portfolio_manager/tests/test_portfolio.py", "w") as f:
    f.write(test_content.strip())

# Create a GitHub workflow file
workflow_content = """name: Nexo Portfolio Manager CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 black isort
    
    - name: Lint with flake8
      run: |
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero treats all errors as warnings
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Check formatting with black
      run: |
        black --check .
    
    - name: Check import sorting with isort
      run: |
        isort --check-only .

  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety
    
    - name: Run security checks with bandit
      run: |
        bandit -r app/ -f json -o bandit-report.json || true
    
    - name: Check dependencies with safety
      run: |
        safety check --json --output safety-report.json || true
"""

# Create .github/workflows directory
os.makedirs("nexo_portfolio_manager/.github/workflows", exist_ok=True)

with open("nexo_portfolio_manager/.github/workflows/ci.yml", "w") as f:
    f.write(workflow_content.strip())

# Create .gitignore
gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Streamlit
.streamlit/

# Data files
data/*.csv
data/*.json
data/*.pkl

# API keys and secrets
secrets.toml
credentials.json
api_keys.txt

# Temporary files
tmp/
temp/
cache/

# Coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/
"""

with open("nexo_portfolio_manager/.gitignore", "w") as f:
    f.write(gitignore_content.strip())

print("Created additional project files:")
print("- run.py (easy startup script)")
print("- tests/test_portfolio.py (sample tests)")
print("- .github/workflows/ci.yml (GitHub Actions)")
print("- .gitignore (Git ignore file)")