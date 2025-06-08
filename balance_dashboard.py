import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class BalanceDashboard:
    def __init__(self, portfolio_manager):
        """Initialize the Balance Dashboard with a portfolio manager instance."""
        self.portfolio_manager = portfolio_manager

    def _normalize_balance_data(self, balances):
        """Normalize balance data to handle both dict and float formats"""
        normalized = {}
        
        if not isinstance(balances, dict):
            return normalized
            
        for asset, data in balances.items():
            if isinstance(data, dict):
                # Already in the expected format
                normalized[asset] = data.copy()
            else:
                # Convert float/dict to the expected format
                try:
                    amount = float(data)
                    normalized[asset] = {
                        'available': amount,
                        'total': amount,
                        'in_orders': 0.0,
                        'usd_value': 0.0  # Will be calculated later
                    }
                except (TypeError, ValueError):
                    print(f"Warning: Could not convert balance for {asset} to float")
                    
        return normalized

    def display_balance_summary(self, balances, prices: Dict[str, float] = None):
        """
        Display a detailed summary of balances with current values.
        
        Args:
            balances: Either:
                - Dictionary of asset data {
                    asset: {
                        'available': float,
                        'total': float,
                        'in_orders': float,
                        'usd_value': float
                    }
                }
                - Or simple dictionary of {asset: amount} where amount is a float
            prices: Optional dictionary of asset prices {asset: price_in_usd}
        """
        if not balances:
            st.warning("No balance data available.")
            return
            
        # Normalize the balance data to ensure consistent format
        normalized_balances = self._normalize_balance_data(balances)
        
        if not normalized_balances:
            st.warning("No valid balance data available.")
            return
            
        # Filter out zero balances and calculate values
        non_zero_balances = {
            asset: data for asset, data in normalized_balances.items() 
            if data.get('total', 0) > 0 or data.get('available', 0) > 0
        }
        
        if not non_zero_balances:
            st.info("All balances are currently zero.")
            return
            
        # Calculate total portfolio value
        total_value = sum(data.get('usd_value', 0) for data in non_zero_balances.values())
        
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Portfolio Value", f"${total_value:,.2f}" if total_value > 0 else "$0.00")
        col2.metric("Total Assets", len(non_zero_balances))
        
        # Calculate 24h change (placeholder - would come from market data)
        portfolio_change_24h = 0.0
        col3.metric("24h Change", 
                   f"{portfolio_change_24h:+.2f}%",
                   delta_color="normal" if portfolio_change_24h == 0 else "inverse")
        
        # Calculate total in orders
        total_in_orders = sum(data.get('in_orders', 0) * prices.get(asset, 0) 
                            for asset, data in non_zero_balances.items() 
                            if prices and asset in prices)
        col4.metric("In Orders", f"${total_in_orders:,.2f}")
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["📊 Asset Overview", "📈 Performance"])
        
        with tab1:
            # Display balances in an enhanced table
            balance_data = []
            for asset, data in sorted(non_zero_balances.items(), 
                                   key=lambda x: x[1].get('usd_value', 0), 
                                   reverse=True):
                amount = data.get('total', 0)
                available = data.get('available', 0)
                in_orders = data.get('in_orders', 0)
                price = prices.get(asset, 0) if prices else 0
                value = data.get('usd_value', amount * price)
                
                # Calculate change (placeholder - would come from market data)
                change_24h = 0.0
                
                balance_data.append({
                    'Asset': asset,
                    'Price': price,
                    'Available': available,
                    'In Orders': in_orders,
                    'Total': amount,
                    'Value': value,
                    '24h %': change_24h,
                    '% of Portfolio': (value / total_value * 100) if total_value > 0 else 0
                })
            
            if balance_data:
                df = pd.DataFrame(balance_data)
                
                # Format the display with better styling
                st.subheader("Asset Breakdown")
                
                # Custom CSS for the table
                st.markdown("""
                <style>
                .stDataFrame th { background-color: #f0f2f6 !important; }
                .positive { color: #00aa00; }
                .negative { color: #ff0000; }
                </style>
                """, unsafe_allow_html=True)
                
                # Display the table with custom formatting
                st.dataframe(
                    df.style.format({
                        'Available': '{:,.8f}'.format,
                        'In Orders': '{:,.8f}'.format,
                        'Total': '{:,.8f}'.format,
                        'Price': '${:,.8f}'.format,
                        'Value': '${:,.2f}'.format,
                        '24h %': '{:+.2f}%'.format,
                        '% of Portfolio': '{:,.2f}%'.format
                    }).apply(
                        lambda x: ['color: #00aa00' if v > 0 else 'color: #ff0000' 
                                 if v < 0 else '' for v in x] if x.name == '24h %' 
                                 else [''] * len(x),
                        axis=0
                    ),
                    column_config={
                        'Asset': st.column_config.TextColumn('Asset', width='small'),
                        'Price': st.column_config.NumberColumn('Price (USD)'),
                        'Available': st.column_config.NumberColumn('Available'),
                        'In Orders': st.column_config.NumberColumn('In Orders'),
                        'Total': st.column_config.NumberColumn('Total Balance'),
                        'Value': st.column_config.NumberColumn('Value (USD)'),
                        '24h %': st.column_config.NumberColumn('24h %'),
                        '% of Portfolio': st.column_config.ProgressColumn(
                            '% of Portfolio',
                            format='%.2f%%',
                            min_value=0,
                            max_value=100
                        )
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, 45 * len(df) + 40)  # Dynamic height based on rows
                )
                
                # Add a pie chart of the distribution
                self.display_balance_distribution(df)
            else:
                st.warning("No balance data available.")
                
        with tab2:
            # Add historical balance chart
            self.display_historical_balances()
            
            # Placeholder for performance metrics
            st.subheader("Performance Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("1M Return", "+2.5%")
            col2.metric("YTD Return", "+15.3%")
            col3.metric("All Time Return", "+42.7%")
    
    def display_balance_distribution(self, balance_df: pd.DataFrame):
        """Display a pie chart of asset distribution."""
        st.subheader("📊 Asset Distribution")
        
        # Check if we have valid data to display
        if balance_df.empty or 'Value' not in balance_df.columns or 'Asset' not in balance_df.columns:
            st.warning("Insufficient data to display asset distribution.")
            return
            
        try:
            # Filter out zero values for better visualization
            df = balance_df[balance_df['Value'] > 0].copy()
            
            if df.empty:
                st.info("No assets with positive value to display.")
                return
                
            # Create a pie chart
            fig = px.pie(
                df,
                values='Value',
                names='Asset',
                hole=0.3,
                color_discrete_sequence=px.colors.sequential.RdBu_r
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='%{label}<br>Value: $%{value:,.2f}<br>%{percent}')
                
            fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error generating asset distribution chart: {str(e)}")
            print(f"Error in display_balance_distribution: {str(e)}")
    
    def display_historical_balances(self, days: int = 30):
        """Display historical balance data."""
        st.subheader("📈 Historical Balances")
        
        # In a real implementation, you would fetch historical balance data from your database
        # For now, we'll use placeholder data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Placeholder for actual historical data
        st.info("Historical balance data will be displayed here. This requires historical data collection to be implemented.")
        
        # Example of what the implementation might look like with real data:
        """
        historical_data = self.portfolio_manager.get_historical_balances(start_date, end_date)
        if historical_data:
            fig = px.area(
                historical_data,
                x='date',
                y='value',
                color='asset',
                title='Historical Portfolio Value',
                labels={'value': 'Value (USD)', 'date': 'Date'}
            )
            st.plotly_chart(fig, use_container_width=True)
        """

    def display_asset_performance(self, asset: str):
        """Display performance metrics for a specific asset."""
        st.subheader(f"📈 {asset} Performance")
        
        # Placeholder for asset performance data
        # In a real implementation, you would fetch this data from your market data provider
        st.info(f"Performance metrics for {asset} will be displayed here.")
        
        # Example of what the implementation might look like with real data:
        """
        performance_data = self.portfolio_manager.get_asset_performance(asset)
        if performance_data:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("24h Change", f"{performance_data['24h_change']:.2f}%", 
                       delta_color="inverse" if performance_data['24h_change'] < 0 else "normal")
            col2.metric("7d Change", f"{performance_data['7d_change']:.2f}%",
                       delta_color="inverse" if performance_data['7d_change'] < 0 else "normal")
            col3.metric("30d Change", f"{performance_data['30d_change']:.2f}%",
                       delta_color="inverse" if performance_data['30d_change'] < 0 else "normal")
            col4.metric("YTD Change", f"{performance_data['ytd_change']:.2f}%",
                       delta_color="inverse" if performance_data['ytd_change'] < 0 else "normal")
            
            # Add a price chart
            fig = px.line(
                performance_data['price_history'],
                x='date',
                y='price',
                title=f'{asset} Price History'
            )
            st.plotly_chart(fig, use_container_width=True)
        """
