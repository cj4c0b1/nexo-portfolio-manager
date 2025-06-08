"""
API Keys Management Page

This module provides a Streamlit interface for managing API keys and portfolios.
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from database import DatabaseManager
from models import APIKey, Portfolio

class APIKeysPage:
    """Streamlit page for managing API keys and portfolios."""
    
    def __init__(self, db: DatabaseManager):
        """Initialize the API keys page with a database connection."""
        self.db = db
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables."""
        if 'editing_key' not in st.session_state:
            st.session_state.editing_key = None
        if 'editing_portfolio' not in st.session_state:
            st.session_state.editing_portfolio = None
    
    def render(self):
        """Render the API keys management page."""
        st.title("🔑 API Keys & Portfolio Management")
        
        # Create tabs for different sections
        tab1, tab2 = st.tabs(["API Keys", "Portfolios"])
        
        with tab1:
            self._render_api_keys_tab()
        
        with tab2:
            self._render_portfolios_tab()
    
    def _render_api_keys_tab(self):
        """Render the API keys management tab."""
        st.subheader("🔑 API Key Management")
        
        # Add new API key form
        with st.expander("➕ Add New API Key", expanded=False):
            self._render_add_api_key_form()
        
        # List existing API keys
        st.subheader("🔐 Your API Keys")
        self._render_api_keys_list()
    
    def _render_add_api_key_form(self):
        """Render the form to add a new API key."""
        with st.form("add_api_key_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                exchange = st.selectbox(
                    "Exchange",
                    ["Nexo", "Nexo Pro", "Binance", "Kraken", "Coinbase"],
                    key="api_key_exchange"
                )
                name = st.text_input("Name/Description", help="A friendly name to identify this API key")
            
            with col2:
                # Get portfolios for the dropdown
                portfolios = self.db.get_all_portfolios()
                portfolio_options = {p.name: p.id for p in portfolios}
                
                portfolio_name = st.selectbox(
                    "Link to Portfolio (Optional)",
                    options=[""] + list(portfolio_options.keys()),
                    format_func=lambda x: "Select a portfolio..." if x == "" else x,
                    key="api_key_portfolio"
                )
                
                api_key = st.text_input("API Key", type="password")
                api_secret = st.text_input("API Secret", type="password")
            
            if st.form_submit_button("Save API Key"):
                if not all([exchange, name, api_key, api_secret]):
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        portfolio_id = portfolio_options.get(portfolio_name) if portfolio_name else None
                        self.db.add_api_key(
                            exchange=exchange,
                            name=name,
                            api_key=api_key,
                            api_secret=api_secret,
                            portfolio_id=portfolio_id
                        )
                        st.success(f"API key for {exchange} added successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding API key: {str(e)}")
    
    def _render_api_keys_list(self):
        """Render the list of API keys."""
        api_keys = self.db.get_all_api_keys()
        
        if not api_keys:
            st.info("No API keys found. Add your first API key above.")
            return
        
        for key in api_keys:
            self._render_api_key_card(key)
    
    def _render_api_key_card(self, key: Dict[str, Any]):
        """Render a card for an API key."""
        with st.expander(f"{key['exchange']} - {key['name']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**ID:** {key['id']}")
                st.markdown(f"**Exchange:** {key['exchange']}")
                st.markdown(f"**Name:** {key['name']}")
                st.markdown(f"**Status:** {'🟢 Active' if key['is_active'] else '🔴 Inactive'}")
                
                # Show portfolio link if exists
                if key['portfolio_id']:
                    portfolio = self.db.get_portfolio(key['portfolio_id'])
                    if portfolio:
                        st.markdown(f"**Linked to:** {portfolio.name}")
            
            with col2:
                st.markdown(f"**API Key:** `{key['api_key']}`")
                st.markdown(f"**API Secret:** `{key['api_secret']}`")
                st.markdown(f"**Created:** {key['created_at']}")
                st.markdown(f"**Last Updated:** {key['updated_at']}")
            
            # Action buttons
            col1, col2, _ = st.columns([1, 1, 3])
            
            with col1:
                if st.button("Edit", key=f"edit_{key['id']}"):
                    st.session_state.editing_key = key['id']
                
                if st.session_state.editing_key == key['id']:
                    self._render_edit_api_key_form(key)
            
            with col2:
                if st.button("Delete", key=f"delete_{key['id']}"):
                    if self.db.delete_api_key(key['id']):
                        st.success("API key deleted successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to delete API key.")
            
            st.markdown("---")
    
    def _render_edit_api_key_form(self, key: Dict[str, Any]):
        """Render the form to edit an existing API key."""
        with st.form(f"edit_api_key_form_{key['id']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Name", value=key['name'], key=f"edit_name_{key['id']}")
            
            with col2:
                # Get portfolios for the dropdown
                portfolios = self.db.get_all_portfolios()
                portfolio_options = {p.name: p.id for p in portfolios}
                
                current_portfolio = None
                if key['portfolio_id']:
                    current_portfolio = next((p.name for p in portfolios if p.id == key['portfolio_id']), None)
                
                new_portfolio = st.selectbox(
                    "Link to Portfolio",
                    options=[""] + list(portfolio_options.keys()),
                    index=0 if not current_portfolio else list(portfolio_options.keys()).index(current_portfolio) + 1,
                    format_func=lambda x: "Select a portfolio..." if x == "" else x,
                    key=f"edit_portfolio_{key['id']}"
                )
            
            new_status = st.checkbox("Active", value=key['is_active'], key=f"edit_status_{key['id']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("Save Changes"):
                    try:
                        portfolio_id = portfolio_options.get(new_portfolio) if new_portfolio else None
                        self.db.update_api_key(
                            key_id=key['id'],
                            name=new_name,
                            portfolio_id=portfolio_id,
                            is_active=new_status
                        )
                        st.success("API key updated successfully!")
                        st.session_state.editing_key = None
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error updating API key: {str(e)}")
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.editing_key = None
                    st.experimental_rerun()
    
    def _render_portfolios_tab(self):
        """Render the portfolios management tab."""
        st.subheader("📊 Portfolio Management")
        
        # Add new portfolio form
        with st.expander("➕ Add New Portfolio", expanded=False):
            self._render_add_portfolio_form()
        
        # List existing portfolios
        st.subheader("📋 Your Portfolios")
        self._render_portfolios_list()
    
    def _render_add_portfolio_form(self):
        """Render the form to add a new portfolio."""
        with st.form("add_portfolio_form"):
            name = st.text_input("Portfolio Name", help="A unique name for this portfolio")
            
            # Get supported tokens from settings
            supported_tokens = ["BTC", "ETH", "ADA", "DOT", "MATIC", "LINK", "UNI", "SOL", "AVAX", "NEXO"]
            
            st.subheader("Target Allocation")
            st.info("Set the target allocation percentages for each asset. The total must sum to 100%.")
            
            allocations = {}
            total = 0
            
            for token in supported_tokens:
                alloc = st.slider(
                    f"{token} Allocation (%)",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    value=0.0,
                    key=f"alloc_{token}"
                )
                allocations[token] = alloc
                total += alloc
            
            st.metric("Total Allocation", f"{total:.2f}%", delta=None)
            
            if st.form_submit_button("Create Portfolio"):
                if not name:
                    st.error("Please enter a portfolio name.")
                elif total != 100.0:
                    st.error(f"Total allocation must be 100% (current: {total:.2f}%)")
                else:
                    try:
                        # Filter out assets with 0% allocation
                        filtered_alloc = {k: v for k, v in allocations.items() if v > 0}
                        self.db.create_portfolio(name, filtered_alloc)
                        st.success(f"Portfolio '{name}' created successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error creating portfolio: {str(e)}")
    
    def _render_portfolios_list(self):
        """Render the list of portfolios."""
        portfolios = self.db.get_all_portfolios()
        
        if not portfolios:
            st.info("No portfolios found. Create your first portfolio above.")
            return
        
        for portfolio in portfolios:
            self._render_portfolio_card(portfolio)
    
    def _render_portfolio_card(self, portfolio: Portfolio):
        """Render a card for a portfolio."""
        with st.expander(f"📊 {portfolio.name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**ID:** {portfolio.id}")
                st.markdown(f"**Name:** {portfolio.name}")
                st.markdown(f"**Created:** {portfolio.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Last Updated:** {portfolio.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                st.markdown("**Allocation:**")
                for token, alloc in portfolio.allocation.items():
                    st.markdown(f"- {token}: {alloc:.2f}%")
            
            # Action buttons
            col1, col2, _ = st.columns([1, 1, 3])
            
            with col1:
                if st.button("Edit", key=f"edit_portfolio_{portfolio.id}"):
                    st.session_state.editing_portfolio = portfolio.id
                
                if st.session_state.editing_portfolio == portfolio.id:
                    self._render_edit_portfolio_form(portfolio)
            
            with col2:
                delete_button = st.button("Delete", key=f"delete_portfolio_{portfolio.id}")
                if delete_button:
                    st.session_state.confirm_delete = portfolio.id
                
                # Show confirmation dialog if delete was clicked
                if st.session_state.get('confirm_delete') == portfolio.id:
                    st.warning("Are you sure you want to delete this portfolio? This action cannot be undone.")
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("Yes, delete it", key=f"confirm_delete_{portfolio.id}"):
                            # Check if portfolio has linked API keys
                            api_keys = self.db.get_api_keys_by_portfolio(portfolio.id)
                            if api_keys:
                                st.error("Cannot delete portfolio with linked API keys. Please unlink or delete the API keys first.")
                            else:
                                if self.db.delete_portfolio(portfolio.id):
                                    st.success("Portfolio deleted successfully!")
                                    del st.session_state.confirm_delete
                                    st.experimental_rerun()
                                else:
                                    st.error("Failed to delete portfolio.")
                    
                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_delete_{portfolio.id}"):
                            del st.session_state.confirm_delete
                            st.experimental_rerun()
            
            st.markdown("---")
    
    def _render_edit_portfolio_form(self, portfolio: Portfolio):
        """Render the form to edit an existing portfolio."""
        with st.form(f"edit_portfolio_form_{portfolio.id}"):
            new_name = st.text_input("Portfolio Name", value=portfolio.name, key=f"edit_portfolio_name_{portfolio.id}")
            
            st.subheader("Target Allocation")
            st.info("Update the target allocation percentages for each asset. The total must sum to 100%.")
            
            # Get supported tokens from settings
            supported_tokens = ["BTC", "ETH", "ADA", "DOT", "MATIC", "LINK", "UNI", "SOL", "AVAX", "NEXO"]
            
            allocations = {}
            total = 0
            
            for token in supported_tokens:
                alloc = st.slider(
                    f"{token} Allocation (%)",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    value=float(portfolio.allocation.get(token, 0.0)),
                    key=f"edit_alloc_{portfolio.id}_{token}"
                )
                allocations[token] = alloc
                total += alloc
            
            st.metric("Total Allocation", f"{total:.2f}%", delta=None)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("Save Changes"):
                    if not new_name:
                        st.error("Please enter a portfolio name.")
                    elif total != 100.0:
                        st.error(f"Total allocation must be 100% (current: {total:.2f}%)")
                    else:
                        try:
                            # Filter out assets with 0% allocation
                            filtered_alloc = {k: v for k, v in allocations.items() if v > 0}
                            self.db.update_portfolio(portfolio.id, new_name, filtered_alloc)
                            st.success(f"Portfolio '{new_name}' updated successfully!")
                            st.session_state.editing_portfolio = None
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error updating portfolio: {str(e)}")
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.editing_portfolio = None
                    st.experimental_rerun()

def main():
    """Main function to run the API keys page."""
    st.set_page_config(
        page_title="API Keys & Portfolio Management",
        page_icon="🔑",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseManager()
    
    # Render the page
    page = APIKeysPage(db)
    page.render()

if __name__ == "__main__":
    main()