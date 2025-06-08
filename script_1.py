# Create requirements.txt
requirements_content = """streamlit==1.32.0
pandas==2.0.3
numpy==1.24.3
plotly==5.14.1
requests==2.31.0
python-dotenv==1.0.0
sqlite3
cryptography==41.0.3
hashlib
datetime
python-nexo==1.0.0
yfinance==0.2.18
scipy==1.11.1
matplotlib==3.7.1
seaborn==0.12.2
"""

with open("nexo_portfolio_manager/requirements.txt", "w") as f:
    f.write(requirements_content.strip())

# Create .env.example
env_example_content = """# Nexo Pro API Configuration
NEXO_PUBLIC_KEY=your_nexo_public_key_here
NEXO_SECRET_KEY=your_nexo_secret_key_here

# Application Configuration
APP_NAME=Nexo Portfolio Manager
DEBUG=True
DATABASE_URL=sqlite:///portfolio.db

# Security
SECRET_KEY=your_secret_key_here

# Notification Settings (Optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_email_password_here
"""

with open("nexo_portfolio_manager/.env.example", "w") as f:
    f.write(env_example_content.strip())

# Create README.md
readme_content = """# Nexo Portfolio Manager

A comprehensive portfolio management system for Nexo and Nexo Pro platforms, built with Python and Streamlit.

## Features

- **Portfolio Definition**: Define your portfolio with percentage allocations for supported tokens
- **Automated Rebalancing**: Rebalance based on time intervals or threshold deviations
- **Cost Optimization**: Automatically transfer funds between Nexo and Nexo Pro for optimal trading costs
- **Real-time Dashboard**: Monitor portfolio performance with interactive charts
- **Risk Management**: Track and analyze portfolio risk metrics
- **Paper Trading**: Test strategies without real funds
- **Tax Reporting**: Generate reports for tax purposes

## Supported Tokens

BTC, ETH, ADA, DOT, MATIC, LINK, UNI, SOL, AVAX, NEXO, USDT, USDC

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nexo_portfolio_manager
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Nexo Pro API credentials
```

5. Run the application:
```bash
streamlit run app/main.py
```

## Configuration

### Nexo Pro API Setup

1. Log in to your Nexo Pro account
2. Go to API Management section
3. Create new API credentials with trading permissions
4. Add your public and secret keys to the `.env` file

### Security Notes

- Never share your API keys
- Use IP whitelisting in Nexo Pro
- Set API permissions to minimum required (trading only, no withdrawals)
- Keep your `.env` file out of version control

## Usage

### Basic Portfolio Setup

1. **Define Portfolio**: Set percentage allocations for each token
2. **Configure Rebalancing**: Choose time-based or threshold-based rebalancing
3. **Set Risk Parameters**: Define your risk tolerance and limits
4. **Enable Paper Trading**: Test your strategy before going live

### Advanced Features

- **Cost Analysis**: Compare trading costs between Nexo and Nexo Pro
- **Performance Tracking**: Monitor returns, Sharpe ratio, and volatility
- **Alert System**: Get notified of rebalancing events and significant changes
- **Historical Analysis**: Backtest your strategies with historical data

## Project Structure

```
nexo_portfolio_manager/
├── app/
│   ├── main.py                 # Main Streamlit application
│   ├── api/
│   │   ├── nexo_client.py      # Nexo Pro API client
│   │   └── market_data.py      # Market data fetching
│   ├── db/
│   │   ├── database.py         # Database operations
│   │   └── models.py           # Data models
│   ├── components/
│   │   ├── dashboard.py        # Dashboard components
│   │   ├── portfolio.py        # Portfolio management
│   │   └── rebalancer.py       # Rebalancing logic
│   └── utils/
│       ├── helpers.py          # Utility functions
│       ├── calculations.py     # Financial calculations
│       └── notifications.py    # Alert system
├── config/
│   └── settings.py             # Application settings
├── tests/                      # Unit tests
├── data/                       # Data storage
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This software is for educational and research purposes only. Use at your own risk. 
The authors are not responsible for any financial losses incurred through the use of this software.
Always test thoroughly with paper trading before using real funds.
"""

with open("nexo_portfolio_manager/README.md", "w") as f:
    f.write(readme_content.strip())

print("Created requirements.txt, .env.example, and README.md files!")