# Create app/main.py - Main Streamlit application
main_app_content = """import streamlit as st
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.components.dashboard import DashboardUI
from config.settings import settings

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
    \"\"\"Main application entry point\"\"\"
    
    # Initialize the dashboard UI
    dashboard = DashboardUI()
    
    # Render sidebar and get selected portfolio
    current_portfolio_id = dashboard.render_sidebar()
    
    # Main header
    st.markdown('<h1 class="main-header">🚀 Nexo Portfolio Manager</h1>', unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "🎯 Portfolio Setup", 
        "⚖️ Rebalancing", 
        "📈 Analytics", 
        "ℹ️ Help"
    ])
    
    with tab1:
        dashboard.render_dashboard_tab(current_portfolio_id)
    
    with tab2:
        dashboard.render_portfolio_setup_tab()
    
    with tab3:
        dashboard.render_rebalancing_tab(current_portfolio_id)
    
    with tab4:
        dashboard.render_analytics_tab(current_portfolio_id)
    
    with tab5:
        render_help_tab()

def render_help_tab():
    \"\"\"Render the help and information tab\"\"\"
    
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
"""

with open("nexo_portfolio_manager/app/main.py", "w") as f:
    f.write(main_app_content.strip())

# Create empty __init__.py files
init_files = [
    "nexo_portfolio_manager/__init__.py",
    "nexo_portfolio_manager/app/__init__.py",
    "nexo_portfolio_manager/app/api/__init__.py",
    "nexo_portfolio_manager/app/db/__init__.py",
    "nexo_portfolio_manager/app/components/__init__.py",
    "nexo_portfolio_manager/app/utils/__init__.py",
    "nexo_portfolio_manager/config/__init__.py",
    "nexo_portfolio_manager/tests/__init__.py"
]

for init_file in init_files:
    with open(init_file, "w") as f:
        f.write("# This file makes Python treat the directory as a package\n")

print("Created main application and __init__.py files!")