import streamlit as st
import sys
import os
import pandas as pd
import market_data  # Import market_data for price lookups
from transfer import TransferManager  # Import the new TransferManager
from api_keys_page import APIKeysPage  # Import the API Keys & Portfolio Management page

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dashboard import DashboardUI
from balance_dashboard import BalanceDashboard
from settings import settings
from portfolio import PortfolioManager

# Configure Streamlit page
st.set_page_config(
    page_title="Nexo Portfolio Manager",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown('''
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }

    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }

    .status-success {
        color: #28a745;
        font-weight: bold;
    }

    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }

    .status-error {
        color: #dc3545;
        font-weight: bold;
    }

    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }

    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
''', unsafe_allow_html=True)

def main():
    """Main application entry point"""

    # Initialize the dashboard UI and portfolio manager
    dashboard = DashboardUI()
    portfolio_manager = PortfolioManager()
    balance_dashboard = BalanceDashboard(portfolio_manager)

    # Render sidebar and get selected portfolio
    current_portfolio_id = dashboard.render_sidebar()

    # Main header
    st.markdown('<h1 class="main-header">🚀 Nexo Portfolio Manager</h1>', unsafe_allow_html=True)

    # Main tabs - Organized for logical flow
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💰 Balance",          # tab1
        "📊 Dashboard",         # tab2
        "🔑 API Keys",          # tab3
        "🎯 Portfolio Setup",   # tab4
        "⚖️ Rebalancing",      # tab5
        "📈 Analytics",         # tab6
        "🔄 Transfer",          # tab7
        "ℹ️ Help"              # tab8
    ])

    with tab1:
        # Display balance dashboard
        st.header("💰 Account Balances")
        
        # Fetch real balances from Nexo
        with st.spinner("Fetching account balances from Nexo..."):
            try:
                # Get real balances from Nexo
                real_balances = portfolio_manager.get_real_balances()
                
                # Get prices for all assets
                prices = {}
                if real_balances:
                    for asset in real_balances.keys():
                        try:
                            # This is a placeholder - you'll need to implement get_current_price in market_data.py
                            # or use an external API to get current prices
                            if hasattr(market_data, 'get_current_price'):
                                prices[asset] = market_data.get_current_price(f"{asset}USDT")
                            else:
                                # Fallback to 0 if price data is not available
                                prices[asset] = 0.0
                        except Exception as e:
                            print(f"Error getting price for {asset}: {e}")
                            prices[asset] = 0.0
                
                if not real_balances:
                    st.warning("No balance data available. Please check your API credentials.")
                    st.info("""
                        To connect to your Nexo account:
                        1. Make sure you have set up your Nexo Pro API keys
                        2. Check that the keys have the necessary permissions
                        3. Verify the keys in your .env file
                    """)
                else:
                    # Filter out zero balances
                    valid_balances = {}
                    
                    for asset, data in real_balances.items():
                        try:
                            # Keep the full data structure for assets with positive balance
                            if float(data.get('total', 0)) > 0:
                                valid_balances[asset] = data
                        except (ValueError, TypeError):
                            continue
                    
                    if not valid_balances:
                        st.info("No assets with positive balance found in your account.")
                    else:
                        # Display the balance summary with the full data structure
                        balance_dashboard.display_balance_summary(valid_balances, prices)
                        
                        # Add a section for asset performance
                        st.header("📊 Asset Performance")
                        if valid_balances:
                            selected_asset = st.selectbox(
                                "Select an asset to view performance:", 
                                list(valid_balances.keys())
                            )
                            balance_dashboard.display_asset_performance(selected_asset)
                    
            except Exception as e:
                st.error(f"Error fetching balances: {str(e)}")
                st.info("""
                    Please verify the following:
                    1. Your Nexo Pro API keys are correctly set in the .env file
                    2. The API keys have the necessary permissions
                    3. Your internet connection is stable
                    4. The Nexo API is operational (check https://status.nexo.io/)
                """)

    with tab2:
        dashboard.render_dashboard_tab(current_portfolio_id)

    with tab3:
        st.header("🔑 API Keys & Portfolio Management")
        api_keys_page = APIKeysPage(portfolio_manager.db)
        api_keys_page.render()
    
    with tab4:
        dashboard.render_portfolio_setup_tab()

    # Rebalancing tab
    with tab5:
        dashboard.render_rebalancing_tab(current_portfolio_id)

    # Analytics tab
    with tab6:
        dashboard.render_analytics_tab(current_portfolio_id)
    
    # Transfer tab
    with tab7:
        # Initialize transfer manager if not already done
        if 'transfer_manager' not in st.session_state:
            st.session_state.transfer_manager = TransferManager(portfolio_manager)
        
        # Render the transfer interface
        from transfer import render_transfer_tab
        render_transfer_tab(st.session_state.transfer_manager)
    
    # Help tab
    with tab8:
        render_help_tab()

def render_help_tab():
    """Render the help and information tab"""

    st.subheader("📖 User Guide")

    with st.expander("🚀 Getting Started"):
        st.markdown('''
        **Welcome to Nexo Portfolio Manager!**

        This application helps you manage and automate your cryptocurrency portfolio on the Nexo platform.

        **First Steps:**
        1. **API Setup**: Add your Nexo Pro API credentials to the `.env` file
        2. **Create Portfolio**: Use the Portfolio Setup tab to define your allocation
        3. **Configure Rebalancing**: Set up automatic rebalancing rules
        4. **Monitor Performance**: Track your portfolio in the Dashboard

        **Paper Trading Mode:**
        - Enable this mode to test strategies without real funds
        - All trades will be simulated
        - Perfect for learning and strategy validation
        ''')

    with st.expander("🎯 Portfolio Setup"):
        st.markdown('''
        **Creating Your Portfolio:**

        1. **Choose a Name**: Give your portfolio a descriptive name
        2. **Select Allocation**: Choose from presets or create custom allocation
        3. **Supported Tokens**: BTC, ETH, ADA, DOT, MATIC, LINK, UNI, SOL, AVAX, NEXO, USDT, USDC

        **Preset Allocations:**
        - **Conservative**: 40% BTC, 30% ETH, 30% Stablecoins
        - **Moderate**: Diversified across major tokens
        - **Aggressive**: Higher allocation to smaller cap tokens
        - **DeFi Focus**: Emphasis on DeFi tokens

        **Custom Allocations:**
        - Total must equal 100%
        - Minimum allocation: 0.1%
        - Maximum single asset: 50% (recommended)
        ''')

    with st.expander("⚖️ Rebalancing"):
        st.markdown('''
        **Rebalancing Strategies:**

        **Time-Based Rebalancing:**
        - Daily, Weekly, Monthly, or Quarterly
        - Executes regardless of current allocation

        **Threshold-Based Rebalancing:**
        - Triggers when assets deviate from target by set percentage
        - Recommended: 5-10% threshold
        - More cost-efficient than time-based

        **Cost Optimization:**
        - Automatically chooses between Nexo and Nexo Pro
        - Nexo Pro typically 70-85% cheaper for larger trades
        - Minimum trade value to avoid excessive fees
        ''')

    with st.expander("📊 Analytics & Metrics"):
        st.markdown('''
        **Performance Metrics:**

        - **Annual Return**: Annualized portfolio return
        - **Volatility**: Standard deviation of returns
        - **Sharpe Ratio**: Risk-adjusted return measure
        - **Max Drawdown**: Largest peak-to-trough decline
        - **Diversification Ratio**: Portfolio diversification measure

        **Cost Analysis:**
        - Compare trading costs between Nexo and Nexo Pro
        - Track total fees paid
        - Calculate savings from platform optimization
        ''')

    with st.expander("🔧 API Configuration"):
        st.markdown('''
        **Setting Up Nexo Pro API:**

        1. Log in to your Nexo Pro account
        2. Navigate to API Management
        3. Create new API credentials
        4. Set permissions to "Trading Only" (never allow withdrawals)
        5. Add IP whitelist for security
        6. Copy credentials to `.env` file:

        ```
        NEXO_PUBLIC_KEY=your_public_key_here
        NEXO_SECRET_KEY=your_secret_key_here
        ```

        **Security Best Practices:**
        - Never share your API keys
        - Use minimum required permissions
        - Enable IP whitelisting
        - Regularly rotate keys
        - Monitor API usage
        ''')

    with st.expander("⚠️ Risk Warnings"):
        st.markdown('''
        **Important Disclaimers:**

        ⚠️ **This software is for educational purposes only**

        ⚠️ **Always use paper trading mode first**

        ⚠️ **Cryptocurrency trading involves significant risk**

        ⚠️ **Past performance does not guarantee future results**

        ⚠️ **The developers are not responsible for any financial losses**

        **Risk Management:**
        - Start with small amounts
        - Diversify your portfolio
        - Set stop-loss limits
        - Regularly review performance
        - Never invest more than you can afford to lose
        ''')

    st.subheader("🔗 Useful Links")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('''
        **Nexo Platform:**
        - [Nexo Main Platform](https://nexo.io)
        - [Nexo Pro Exchange](https://pro.nexo.io)
        - [API Documentation](https://docs.nexo.io)
        ''')

    with col2:
        st.markdown('''
        **Learning Resources:**
        - [Portfolio Theory](https://www.investopedia.com/terms/m/modernportfoliotheory.asp)
        - [Rebalancing Guide](https://www.bogleheads.org/wiki/Rebalancing)
        - [Risk Management](https://www.investopedia.com/terms/r/riskmanagement.asp)
        ''')

    with col3:
        st.markdown('''
        **Support:**
        - [GitHub Repository](https://github.com/your-repo)
        - [Issue Tracker](https://github.com/your-repo/issues)
        - [Documentation](https://github.com/your-repo/wiki)
        ''')

    st.subheader("📊 System Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        if settings.NEXO_PUBLIC_KEY and settings.NEXO_SECRET_KEY:
            st.success("✅ API Connected")
        else:
            st.warning("⚠️ Using Mock Data")

    with col2:
        st.info(f"📱 App Version: 1.0.0")

    with col3:
        paper_mode = st.session_state.get('paper_trading', True)
        if paper_mode:
            st.info("🧪 Paper Trading Mode")
        else:
            st.error("🚨 Live Trading Mode")

if __name__ == "__main__":
    main()