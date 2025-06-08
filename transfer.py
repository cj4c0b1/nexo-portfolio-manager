"""
Nexo to Nexo Pro Transfer Module

This module handles the transfer of assets between Nexo and Nexo Pro accounts.
"""
import streamlit as st
from typing import Dict, List, Tuple, Optional
import pandas as pd
from nexo.client import Client as NexoClient

class TransferManager:
    def __init__(self, portfolio_manager):
        """Initialize the Transfer Manager with a portfolio manager instance."""
        self.portfolio_manager = portfolio_manager
        self.nexo_client = self._init_nexo_client()
        
    def _init_nexo_client(self) -> Optional[NexoClient]:
        """Initialize the Nexo client with API credentials."""
        try:
            # Get credentials from environment or config
            api_key = os.getenv('NEXO_API_KEY')
            api_secret = os.getenv('NEXO_API_SECRET')
            
            if not api_key or not api_secret:
                st.warning("Nexo API credentials not found. Some features may be limited.")
                return None
                
            return NexoClient(api_key, api_secret)
        except Exception as e:
            st.error(f"Failed to initialize Nexo client: {e}")
            return None
    
    def get_available_balances(self) -> Dict[str, Dict[str, float]]:
        """Get available balances for transfer from both accounts."""
        balances = {'nexo': {}, 'pro': {}}
        
        try:
            # Get Nexo balances (from Nexo Pro API)
            if self.nexo_client:
                account_summary = self.nexo_client.get_account_summary()
                if account_summary and 'balances' in account_summary:
                    balances['nexo'] = {
                        asset: float(data['available'])
                        for asset, data in account_summary['balances'].items()
                        if 'available' in data and float(data['available']) > 0
                    }
            
            # Get Nexo Pro balances (from our portfolio manager)
            pro_balances = self.portfolio_manager.get_balances()
            if pro_balances:
                balances['pro'] = {
                    asset: data['available']
                    for asset, data in pro_balances.items()
                    if 'available' in data and data['available'] > 0
                }
            
        except Exception as e:
            st.error(f"Error fetching balances: {e}")
            print(f"Error in get_available_balances: {e}")
            
        return balances
    
    def transfer_assets(self, asset: str, amount: float, from_account: str, to_account: str) -> bool:
        """
        Transfer assets between Nexo and Nexo Pro.
        
        Args:
            asset: The asset to transfer (e.g., 'BTC', 'ETH')
            amount: Amount to transfer
            from_account: 'nexo' or 'pro'
            to_account: 'nexo' or 'pro' (must be different from from_account)
            
        Returns:
            bool: True if transfer was successful, False otherwise
        """
        if from_account == to_account:
            st.error("Cannot transfer to the same account")
            return False
            
        if amount <= 0:
            st.error("Amount must be positive")
            return False
            
        try:
            if from_account == 'nexo' and to_account == 'pro':
                # Transfer from Nexo to Nexo Pro (withdrawal from Nexo)
                if not self.nexo_client:
                    st.error("Nexo client not initialized")
                    return False
                    
                # Get deposit address for Nexo Pro
                deposit_address = self.portfolio_manager.get_deposit_address(asset)
                if not deposit_address:
                    st.error(f"Could not get deposit address for {asset}")
                    return False
                
                # Execute withdrawal from Nexo to Nexo Pro
                result = self.nexo_client.withdraw(
                    asset=asset,
                    amount=amount,
                    address=deposit_address,
                    network=self._get_network_for_asset(asset)
                )
                
            elif from_account == 'pro' and to_account == 'nexo':
                # Transfer from Nexo Pro to Nexo (withdrawal from Nexo Pro)
                # This would require Nexo Pro API implementation
                result = self.portfolio_manager.transfer_to_nexo(asset, amount)
                
            else:
                st.error("Invalid account combination")
                return False
                
            if result.get('success', False):
                st.success(f"Successfully transferred {amount} {asset} from {from_account} to {to_account}")
                return True
            else:
                st.error(f"Transfer failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            st.error(f"Transfer error: {str(e)}")
            return False
    
    def _get_network_for_asset(self, asset: str) -> str:
        """Get the appropriate network for an asset withdrawal."""
        # This is a simplified version - you'd want to map assets to their networks
        network_map = {
            'BTC': 'BTC',
            'ETH': 'ERC20',
            'USDT': 'ERC20',
            'USDC': 'ERC20',
            # Add more mappings as needed
        }
        return network_map.get(asset, 'ERC20')  # Default to ERC20

def render_transfer_tab(transfer_manager):
    """Render the transfer interface."""
    st.title("🔄 Transfer Between Nexo & Nexo Pro")
    
    if not transfer_manager.nexo_client:
        st.warning("Nexo API credentials not configured. Some features may be limited.")
    
    # Get balances
    with st.spinner("Loading balances..."):
        balances = transfer_manager.get_available_balances()
    
    if not balances.get('nexo') and not balances.get('pro'):
        st.warning("No balances found in either account")
        return
    
    # Create transfer form
    with st.form("transfer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("From")
            from_account = st.radio(
                "Source Account",
                ["Nexo", "Nexo Pro"],
                key="from_account"
            ).lower()
            
            # Filter assets with balance > 0 for the source account
            source_assets = balances.get(from_account, {})
            if not source_assets:
                st.warning(f"No assets found in {from_account} account")
                st.stop()
                
            selected_asset = st.selectbox(
                "Asset",
                options=list(source_assets.keys()),
                format_func=lambda x: f"{x} (Available: {source_assets[x]:.8f})",
                key="asset"
            )
            
            max_amount = source_assets.get(selected_asset, 0)
            amount = st.number_input(
                "Amount",
                min_value=0.0,
                max_value=float(max_amount) if max_amount else 0.0,
                step=0.00000001,
                format="%f",
                key="amount"
            )
        
        with col2:
            st.subheader("To")
            to_account = "pro" if from_account == "nexo" else "nexo"
            st.info(f"Nexo Pro" if to_account == "pro" else "Nexo")
            
            if selected_asset:
                dest_balance = balances.get(to_account, {}).get(selected_asset, 0)
                st.metric(
                    f"Current {selected_asset} balance in {to_account}",
                    f"{dest_balance:.8f} {selected_asset}"
                )
        
        # Transfer button
        submitted = st.form_submit_button("Transfer")
        
        if submitted:
            if amount <= 0:
                st.error("Please enter a valid amount")
            else:
                with st.spinner("Processing transfer..."):
                    success = transfer_manager.transfer_assets(
                        asset=selected_asset,
                        amount=amount,
                        from_account=from_account,
                        to_account=to_account
                    )
                    
                    if success:
                        st.balloons()
                        # Refresh balances after successful transfer
                        st.experimental_rerun()
    
    # Show recent transfers (placeholder)
    st.subheader("Recent Transfers")
    st.info("Transaction history will appear here")
