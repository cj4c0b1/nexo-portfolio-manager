# Nexo Portfolio Manager - Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- Nexo Pro account (optional, for live trading)
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd nexo_portfolio_manager
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API credentials (optional)
# For testing, you can leave the API keys empty to use mock data
```

### 5. Run the Application
```bash
# Option 1: Use the run script
python run.py

# Option 2: Direct Streamlit command
streamlit run app/main.py
```

## First Steps

1. **Access the Application**: Open your browser to http://localhost:8501
2. **Create a Portfolio**: Go to the "Portfolio Setup" tab
3. **Choose an Allocation**: Select a preset or create custom allocation
4. **Enable Paper Trading**: Keep this enabled for testing
5. **Explore Features**: Try rebalancing, analytics, and dashboard features

## API Setup (Optional)

For live trading with Nexo Pro:

1. Log in to your Nexo Pro account
2. Go to Settings > API Management
3. Create new API credentials with "Trading Only" permissions
4. Enable IP whitelisting for security
5. Add credentials to your `.env` file:
   ```
   NEXO_PUBLIC_KEY=your_public_key_here
   NEXO_SECRET_KEY=your_secret_key_here
   ```

## Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

## Support

- Check the Help tab in the application
- Review the README.md file
- Submit issues on GitHub

## Important Notes

⚠️ **Always start with paper trading mode**
⚠️ **Never share your API keys**
⚠️ **Use at your own risk - this is educational software**

Happy portfolio managing! 🚀
