# Create app/components/dashboard.py
dashboard_content = """import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

from app.components.portfolio import PortfolioManager
from app.utils.helpers import (
    format_currency, format_percentage, create_metrics_dashboard,
    display_portfolio_summary, create_transaction_history_table,
    validate_allocation_input, get_preset_allocations, SessionState
)
from config.settings import settings

class DashboardUI:
    def __init__(self):
        self.portfolio_manager = PortfolioManager()
        SessionState.initialize()
    
    def render_sidebar(self):
        \"\"\"Render the sidebar with navigation and settings\"\"\"
        
        st.sidebar.title("🚀 Nexo Portfolio Manager")
        
        # Portfolio selection
        portfolios = self.portfolio_manager.db.get_all_portfolios()
        portfolio_options = {p.name: p.id for p in portfolios}
        
        if portfolio_options:
            selected_portfolio_name = st.sidebar.selectbox(
                "Select Portfolio",
                options=list(portfolio_options.keys()),
                key="portfolio_selector"
            )
            
            selected_portfolio_id = portfolio_options[selected_portfolio_name]
            SessionState.set_current_portfolio_id(selected_portfolio_id)
        else:
            st.sidebar.info("No portfolios found. Create one in the Portfolio Setup tab.")
            SessionState.set_current_portfolio_id(None)
        
        # Global settings
        st.sidebar.subheader("⚙️ Settings")
        
        st.session_state.paper_trading = st.sidebar.toggle(
            "Paper Trading Mode",
            value=st.session_state.get('paper_trading', True),
            help="Enable paper trading to test strategies without real funds"
        )
        
        # API Status
        st.sidebar.subheader("📡 API Status")
        
        if settings.NEXO_PUBLIC_KEY and settings.NEXO_SECRET_KEY:
            st.sidebar.success("✅ Nexo Pro API Connected")
        else:
            st.sidebar.warning("⚠️ Using Mock Data")
            st.sidebar.info("Add your Nexo Pro API keys to .env file for live trading")
        
        return SessionState.get_current_portfolio_id()
    
    def render_dashboard_tab(self, portfolio_id: int):
        \"\"\"Render the main dashboard tab\"\"\"
        
        if not portfolio_id:
            st.info("Please select or create a portfolio to view the dashboard.")
            return
        
        # Get portfolio performance data
        performance_data = self.portfolio_manager.get_portfolio_performance(portfolio_id)
        
        if not performance_data:
            st.error("Could not load portfolio data.")
            return
        
        # Portfolio summary
        display_portfolio_summary(performance_data)
        
        # Risk metrics
        if performance_data.get('risk_metrics'):
            st.subheader("📊 Risk Metrics")
            create_metrics_dashboard(performance_data['risk_metrics'])
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Current Allocation")
            chart_data = self.portfolio_manager.get_portfolio_allocation_chart_data(portfolio_id)
            
            if chart_data and chart_data['labels']:
                # Create pie chart data for Streamlit
                allocation_df = pd.DataFrame({
                    'Token': chart_data['labels'],
                    'Value': chart_data['values']
                })
                st.plotly_chart(
                    self._create_pie_chart(allocation_df),
                    use_container_width=True
                )
            else:
                st.info("No allocation data available")
        
        with col2:
            st.subheader("📈 Performance History")
            
            if performance_data['snapshots']:
                performance_df = pd.DataFrame(performance_data['snapshots'])
                performance_df['date'] = pd.to_datetime(performance_df['date'])
                
                st.line_chart(
                    performance_df.set_index('date')['value'],
                    height=400
                )
            else:
                st.info("No performance history available")
        
        # Asset breakdown
        st.subheader("💰 Asset Breakdown")
        
        if performance_data.get('asset_breakdown'):
            asset_data = []
            for token, data in performance_data['asset_breakdown'].items():
                asset_data.append({
                    'Token': token,
                    'Balance': f"{data['balance']:.6f}",
                    'Price': format_currency(data['price']),
                    'Value': format_currency(data['value']),
                    'Target %': f"{performance_data['target_allocation'].get(token, 0):.1f}%"
                })
            
            asset_df = pd.DataFrame(asset_data)
            st.dataframe(asset_df, use_container_width=True)
        
        # Recent transactions
        st.subheader("📋 Recent Transactions")
        transactions = self.portfolio_manager.db.get_portfolio_transactions(portfolio_id, limit=10)
        
        if transactions:
            transaction_data = [t.to_dict() for t in transactions]
            transaction_df = create_transaction_history_table(transaction_data)
            st.dataframe(transaction_df, use_container_width=True)
        else:
            st.info("No transactions found")
    
    def render_portfolio_setup_tab(self):
        \"\"\"Render the portfolio setup tab\"\"\"
        
        st.subheader("🎯 Portfolio Setup")
        
        tab1, tab2 = st.tabs(["Create New Portfolio", "Manage Existing"])
        
        with tab1:
            self._render_create_portfolio_form()
        
        with tab2:
            self._render_manage_portfolio_form()
    
    def render_rebalancing_tab(self, portfolio_id: int):
        \"\"\"Render the rebalancing tab\"\"\"
        
        if not portfolio_id:
            st.info("Please select a portfolio to manage rebalancing.")
            return
        
        st.subheader("⚖️ Portfolio Rebalancing")
        
        # Get rebalancing suggestions
        suggestions = self.portfolio_manager.get_rebalance_suggestions(portfolio_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Rebalancing Status",
                "Needed" if suggestions.get('should_rebalance') else "Not Needed",
                delta=None
            )
        
        with col2:
            st.metric(
                "Estimated Cost",
                format_currency(suggestions.get('estimated_cost', 0)),
                delta=None
            )
        
        # Rebalancing settings
        with st.expander("⚙️ Rebalancing Settings"):
            self._render_rebalancing_settings(portfolio_id)
        
        # Current deviations
        if suggestions.get('deviations'):
            st.subheader("📊 Current Deviations from Target")
            
            deviation_data = []
            for token, deviation in suggestions['deviations'].items():
                status = "⚠️" if deviation > suggestions.get('threshold', 5) else "✅"
                deviation_data.append({
                    'Status': status,
                    'Token': token,
                    'Deviation': f"{deviation:.2f}%",
                    'Threshold': f"{suggestions.get('threshold', 5):.1f}%"
                })
            
            deviation_df = pd.DataFrame(deviation_data)
            st.dataframe(deviation_df, use_container_width=True)
        
        # Suggested trades
        if suggestions.get('suggested_trades'):
            st.subheader("📋 Suggested Trades")
            
            trade_data = []
            for trade in suggestions['suggested_trades']:
                trade_data.append({
                    'Token': trade['token'],
                    'Action': trade['side'].upper(),
                    'Quantity': f"{trade['quantity']:.6f}",
                    'Estimated Value': format_currency(trade['estimated_value']),
                    'Current %': f"{trade['current_percent']:.2f}%",
                    'Target %': f"{trade['target_percent']:.2f}%"
                })
            
            trade_df = pd.DataFrame(trade_data)
            st.dataframe(trade_df, use_container_width=True)
            
            # Execute rebalancing button
            if st.button("🚀 Execute Rebalancing", type="primary"):
                with st.spinner("Executing rebalancing..."):
                    result = self.portfolio_manager.execute_rebalance(
                        portfolio_id, 
                        paper_trading=st.session_state.paper_trading
                    )
                
                if result['success']:
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['message'])
        else:
            st.info("No trades needed at this time.")
    
    def render_analytics_tab(self, portfolio_id: int):
        \"\"\"Render the analytics tab\"\"\"
        
        if not portfolio_id:
            st.info("Please select a portfolio to view analytics.")
            return
        
        st.subheader("📊 Portfolio Analytics")
        
        # Cost analysis
        st.subheader("💰 Trading Cost Analysis")
        cost_analysis = self.portfolio_manager.get_cost_analysis(portfolio_id)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Nexo Platform Costs",
                format_currency(cost_analysis['nexo']['total_cost']),
                delta=f"{cost_analysis['nexo']['transaction_count']} trades"
            )
        
        with col2:
            st.metric(
                "Nexo Pro Costs",
                format_currency(cost_analysis['nexo_pro']['total_cost']),
                delta=f"{cost_analysis['nexo_pro']['transaction_count']} trades"
            )
        
        with col3:
            st.metric(
                "Total Savings",
                format_currency(cost_analysis['total_savings']),
                delta="Using Nexo Pro"
            )
        
        # Performance analytics
        performance_data = self.portfolio_manager.get_portfolio_performance(portfolio_id, days=90)
        
        if performance_data.get('risk_metrics'):
            st.subheader("📈 Risk-Return Analysis")
            
            metrics = performance_data['risk_metrics']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Total Return",
                    f"{metrics.get('total_return', 0)*100:.2f}%",
                    delta=None
                )
                
                st.metric(
                    "Annual Return",
                    f"{metrics.get('annual_return', 0)*100:.2f}%",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Volatility",
                    f"{metrics.get('annual_volatility', 0)*100:.2f}%",
                    delta=None
                )
                
                st.metric(
                    "Sharpe Ratio",
                    f"{metrics.get('sharpe_ratio', 0):.3f}",
                    delta=None
                )
    
    def _create_pie_chart(self, df: pd.DataFrame):
        \"\"\"Create a pie chart using Plotly\"\"\"
        import plotly.express as px
        
        fig = px.pie(
            df, 
            values='Value', 
            names='Token',
            title="Portfolio Allocation"
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        return fig
    
    def _render_create_portfolio_form(self):
        \"\"\"Render the create portfolio form\"\"\"
        
        with st.form("create_portfolio_form"):
            portfolio_name = st.text_input("Portfolio Name", placeholder="My Crypto Portfolio")
            
            # Preset allocations
            st.subheader("Choose a preset or create custom allocation:")
            
            preset_options = get_preset_allocations()
            selected_preset = st.selectbox(
                "Preset Allocations",
                options=["Custom"] + list(preset_options.keys())
            )
            
            if selected_preset != "Custom":
                allocation = preset_options[selected_preset]
                st.info(f"Using {selected_preset} preset allocation")
            else:
                allocation = {}
            
            # Custom allocation inputs
            st.subheader("Custom Allocation (%)")
            
            allocation_inputs = {}
            for token in settings.SUPPORTED_TOKENS:
                default_value = allocation.get(token, 0.0)
                allocation_inputs[token] = st.number_input(
                    f"{token} %",
                    min_value=0.0,
                    max_value=100.0,
                    value=default_value,
                    step=0.1,
                    key=f"allocation_{token}"
                )
            
            # Filter out zero allocations
            final_allocation = {k: v for k, v in allocation_inputs.items() if v > 0}
            
            # Validation
            total_allocation = sum(final_allocation.values())
            
            if total_allocation > 0:
                st.info(f"Total allocation: {total_allocation:.1f}%")
            
            submitted = st.form_submit_button("Create Portfolio")
            
            if submitted:
                if not portfolio_name:
                    st.error("Please enter a portfolio name")
                elif not final_allocation:
                    st.error("Please set at least one token allocation")
                else:
                    is_valid, message = validate_allocation_input(final_allocation)
                    
                    if is_valid:
                        try:
                            portfolio = self.portfolio_manager.create_portfolio(
                                portfolio_name,
                                final_allocation
                            )
                            st.success(f"Portfolio '{portfolio_name}' created successfully!")
                            SessionState.set_current_portfolio_id(portfolio.id)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating portfolio: {str(e)}")
                    else:
                        st.error(message)
    
    def _render_manage_portfolio_form(self):
        \"\"\"Render the manage existing portfolio form\"\"\"
        
        portfolios = self.portfolio_manager.db.get_all_portfolios()
        
        if not portfolios:
            st.info("No portfolios found. Create one first.")
            return
        
        portfolio_options = {p.name: p for p in portfolios}
        
        selected_portfolio_name = st.selectbox(
            "Select Portfolio to Manage",
            options=list(portfolio_options.keys())
        )
        
        selected_portfolio = portfolio_options[selected_portfolio_name]
        
        st.subheader(f"Managing: {selected_portfolio.name}")
        
        # Show current allocation
        st.write("**Current Allocation:**")
        for token, percent in selected_portfolio.allocation.items():
            st.write(f"- {token}: {percent:.1f}%")
        
        # Update allocation form
        with st.form("update_portfolio_form"):
            st.subheader("Update Allocation")
            
            updated_allocation = {}
            for token in settings.SUPPORTED_TOKENS:
                current_value = selected_portfolio.allocation.get(token, 0.0)
                updated_allocation[token] = st.number_input(
                    f"{token} %",
                    min_value=0.0,
                    max_value=100.0,
                    value=current_value,
                    step=0.1,
                    key=f"update_allocation_{token}"
                )
            
            # Filter out zero allocations
            final_allocation = {k: v for k, v in updated_allocation.items() if v > 0}
            
            # Show total
            total_allocation = sum(final_allocation.values())
            st.info(f"Total allocation: {total_allocation:.1f}%")
            
            submitted = st.form_submit_button("Update Portfolio")
            
            if submitted:
                is_valid, message = validate_allocation_input(final_allocation)
                
                if is_valid:
                    try:
                        success = self.portfolio_manager.update_portfolio_allocation(
                            selected_portfolio.id,
                            final_allocation
                        )
                        
                        if success:
                            st.success("Portfolio updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update portfolio")
                    except Exception as e:
                        st.error(f"Error updating portfolio: {str(e)}")
                else:
                    st.error(message)
    
    def _render_rebalancing_settings(self, portfolio_id: int):
        \"\"\"Render rebalancing settings form\"\"\"
        
        current_settings = self.portfolio_manager.db.get_rebalance_settings(portfolio_id)
        
        with st.form("rebalancing_settings_form"):
            frequency = st.selectbox(
                "Rebalancing Frequency",
                options=["daily", "weekly", "monthly", "quarterly"],
                index=1 if not current_settings else ["daily", "weekly", "monthly", "quarterly"].index(current_settings.frequency)
            )
            
            threshold = st.number_input(
                "Deviation Threshold (%)",
                min_value=1.0,
                max_value=20.0,
                value=current_settings.threshold if current_settings else 5.0,
                step=0.5,
                help="Trigger rebalancing when any asset deviates by this percentage"
            )
            
            auto_rebalance = st.checkbox(
                "Enable Automatic Rebalancing",
                value=current_settings.auto_rebalance if current_settings else False,
                help="Automatically execute rebalancing when conditions are met"
            )
            
            submitted = st.form_submit_button("Save Settings")
            
            if submitted:
                success = self.portfolio_manager.set_rebalance_settings(
                    portfolio_id=portfolio_id,
                    frequency=frequency,
                    threshold=threshold,
                    auto_rebalance=auto_rebalance,
                    paper_trading=st.session_state.paper_trading
                )
                
                if success:
                    st.success("Rebalancing settings saved!")
                    st.rerun()
                else:
                    st.error("Failed to save settings")
"""

with open("nexo_portfolio_manager/app/components/dashboard.py", "w") as f:
    f.write(dashboard_content.strip())

print("Created dashboard component!")