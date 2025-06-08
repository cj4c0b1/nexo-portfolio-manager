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

def main():
    """Main application entry point"""
    st.sidebar.title("Nexo Portfolio Manager")
    
    # Initialize session state for page navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Balance Dashboard", "API Keys & Portfolio", "Help"],
        index=0  # Default to first item if not found
    )
    
    # Update current page in session state
    st.session_state.current_page = page
    
    # Initialize dashboard UI
    dashboard_ui = DashboardUI()
    
    # Page routing
    if page == "Dashboard":
        dashboard_ui.render()
    elif page == "Balance Dashboard":
        balance_dashboard = BalanceDashboard()
        balance_dashboard.render()
    elif page == "API Keys & Portfolio":
        api_keys_page = APIKeysPage()
        api_keys_page.render()
    elif page == "Help":
        render_help_tab()

def render_help_tab():
    """Render the help and information tab"""
    st.title("Help & Information")
    
    st.markdown("""
    ## Nexo Portfolio Manager
    
    A comprehensive dashboard for managing your Nexo portfolio, tracking performance,
    and monitoring your crypto assets.
    
    ### Features
    - **Portfolio Overview**: View your complete Nexo portfolio at a glance
    - **Performance Tracking**: Monitor your portfolio's performance over time
    - **Asset Allocation**: Analyze and manage your asset allocation
    - **Transaction History**: View and export your transaction history
    - **Price Alerts**: Set up price alerts for your assets
    - **API Integration**: Connect your Nexo account via API
    
    ### Getting Started
    1. Navigate to the **API Keys & Portfolio** section
    2. Enter your Nexo API credentials
    3. Click **Save API Keys**
    4. Your portfolio data will be automatically loaded
    
    ### Support
    For support or feature requests, please open an issue on our 
    [GitHub repository](https://github.com/yourusername/nexo-portfolio-manager).
    
    ### Version
    v1.0.0
    """)

if __name__ == "__main__":
    main()
