# Create app/components/portfolio.py
portfolio_content = """from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd

from app.db.database import DatabaseManager
from app.db.models import Portfolio, PortfolioSnapshot, RebalanceSettings
from app.api.market_data import market_data
from app.components.rebalancer import PortfolioRebalancer, RiskAnalyzer
from config.settings import settings

class PortfolioManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.risk_analyzer = RiskAnalyzer()
    
    def create_portfolio(self, name: str, allocation: Dict[str, float]) -> Portfolio:
        \"\"\"Create a new portfolio with validation\"\"\"
        
        # Validate allocation
        if not self._validate_allocation(allocation):
            raise ValueError("Invalid allocation: must sum to 100%")
        
        # Check for supported tokens
        unsupported_tokens = set(allocation.keys()) - set(settings.SUPPORTED_TOKENS)
        if unsupported_tokens:
            raise ValueError(f"Unsupported tokens: {unsupported_tokens}")
        
        return self.db.create_portfolio(name, allocation)
    
    def get_portfolio_performance(self, portfolio_id: int, days: int = 30) -> Dict:
        \"\"\"Get comprehensive portfolio performance metrics\"\"\"
        
        portfolio = self.db.get_portfolio(portfolio_id)
        if not portfolio:
            return {}
        
        # Get portfolio snapshots
        snapshots = self.db.get_portfolio_snapshots(portfolio_id, days)
        
        # Calculate risk metrics
        risk_metrics = self.risk_analyzer.calculate_portfolio_metrics(snapshots)
        
        # Calculate diversification
        diversification_ratio = self.risk_analyzer.calculate_diversification_ratio(portfolio.allocation)
        
        # Get current portfolio value
        current_balances = self._get_current_balances(portfolio_id)
        portfolio_data = market_data.calculate_portfolio_value(current_balances)
        
        return {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'current_value': portfolio_data['total_value'],
            'asset_breakdown': portfolio_data['asset_values'],
            'target_allocation': portfolio.allocation,
            'diversification_ratio': diversification_ratio,
            'risk_metrics': risk_metrics,
            'snapshots': [
                {
                    'date': snapshot.timestamp.strftime('%Y-%m-%d'),
                    'value': snapshot.total_value
                } for snapshot in snapshots
            ]
        }
    
    def get_rebalance_suggestions(self, portfolio_id: int) -> Dict:
        \"\"\"Get rebalancing suggestions for a portfolio\"\"\"
        
        portfolio = self.db.get_portfolio(portfolio_id)
        if not portfolio:
            return {}
        
        current_balances = self._get_current_balances(portfolio_id)
        rebalancer = PortfolioRebalancer(portfolio_id)
        
        # Get current portfolio value
        portfolio_data = market_data.calculate_portfolio_value(current_balances)
        total_value = portfolio_data['total_value']
        
        # Calculate required trades
        trades = rebalancer.calculate_rebalance_trades(
            current_balances, 
            portfolio.allocation, 
            total_value
        )
        
        # Check if rebalancing is needed
        rebalance_settings = self.db.get_rebalance_settings(portfolio_id)
        threshold = rebalance_settings.threshold if rebalance_settings else settings.DEFAULT_REBALANCE_THRESHOLD
        
        should_rebalance, deviations = rebalancer.should_rebalance(
            current_balances, 
            portfolio.allocation, 
            threshold
        )
        
        return {
            'should_rebalance': should_rebalance,
            'threshold': threshold,
            'deviations': deviations,
            'suggested_trades': trades,
            'estimated_cost': sum(trade['estimated_value'] * 0.002 for trade in trades),
            'total_trade_value': sum(trade['estimated_value'] for trade in trades)
        }
    
    def execute_rebalance(self, portfolio_id: int, paper_trading: bool = True) -> Dict:
        \"\"\"Execute portfolio rebalancing\"\"\"
        
        suggestions = self.get_rebalance_suggestions(portfolio_id)
        
        if not suggestions['should_rebalance']:
            return {
                'success': False,
                'message': 'No rebalancing needed',
                'suggestions': suggestions
            }
        
        rebalancer = PortfolioRebalancer(portfolio_id)
        
        try:
            transactions, total_cost = rebalancer.execute_rebalance(
                suggestions['suggested_trades'], 
                paper_trading
            )
            
            # Save transactions to database
            for transaction in transactions:
                self.db.add_transaction(transaction)
            
            # Create rebalance event record
            portfolio = self.db.get_portfolio(portfolio_id)
            current_balances = self._get_current_balances(portfolio_id)
            
            # Take new snapshot after rebalancing
            self._take_portfolio_snapshot(portfolio_id)
            
            return {
                'success': True,
                'message': f'Rebalancing completed successfully',
                'transactions': [t.to_dict() for t in transactions],
                'total_cost': total_cost,
                'paper_trading': paper_trading
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Rebalancing failed: {str(e)}',
                'suggestions': suggestions
            }
    
    def update_portfolio_allocation(self, portfolio_id: int, new_allocation: Dict[str, float]) -> bool:
        \"\"\"Update portfolio target allocation\"\"\"
        
        if not self._validate_allocation(new_allocation):
            raise ValueError("Invalid allocation: must sum to 100%")
        
        success = self.db.update_portfolio(portfolio_id, new_allocation)
        
        if success:
            # Take snapshot to record the change
            self._take_portfolio_snapshot(portfolio_id)
        
        return success
    
    def set_rebalance_settings(self, 
                              portfolio_id: int,
                              frequency: str = "weekly",
                              threshold: float = 5.0,
                              auto_rebalance: bool = False,
                              paper_trading: bool = True) -> bool:
        \"\"\"Set or update rebalancing settings for a portfolio\"\"\"
        
        now = datetime.now()
        settings_obj = RebalanceSettings(
            id=0,
            portfolio_id=portfolio_id,
            frequency=frequency,
            threshold=threshold,
            min_trade_value=settings.MIN_TRADE_VALUE,
            auto_rebalance=auto_rebalance,
            paper_trading=paper_trading,
            created_at=now,
            updated_at=now
        )
        
        return self.db.save_rebalance_settings(settings_obj) > 0
    
    def get_portfolio_allocation_chart_data(self, portfolio_id: int) -> Dict:
        \"\"\"Get data for portfolio allocation charts\"\"\"
        
        portfolio = self.db.get_portfolio(portfolio_id)
        if not portfolio:
            return {}
        
        current_balances = self._get_current_balances(portfolio_id)
        portfolio_data = market_data.calculate_portfolio_value(current_balances)
        
        # Prepare data for pie chart
        chart_data = {
            'labels': [],
            'values': [],
            'target_allocation': [],
            'colors': []
        }
        
        color_palette = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
            '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43'
        ]
        
        for i, (token, balance) in enumerate(current_balances.items()):
            if token in portfolio_data['asset_values']:
                value = portfolio_data['asset_values'][token]['value']
                if value > 0:
                    chart_data['labels'].append(token)
                    chart_data['values'].append(value)
                    chart_data['target_allocation'].append(portfolio.allocation.get(token, 0))
                    chart_data['colors'].append(color_palette[i % len(color_palette)])
        
        return chart_data
    
    def _validate_allocation(self, allocation: Dict[str, float]) -> bool:
        \"\"\"Validate that allocation percentages sum to 100\"\"\"
        total = sum(allocation.values())
        return abs(total - 100.0) < 0.01  # Allow for small floating point errors
    
    def _get_current_balances(self, portfolio_id: int) -> Dict[str, float]:
        \"\"\"Get current token balances for a portfolio\"\"\"
        # This would normally come from the Nexo API
        # For now, we'll use mock data or calculate from transactions
        
        portfolio = self.db.get_portfolio(portfolio_id)
        if not portfolio:
            return {}
        
        # Mock balances based on target allocation
        # In production, this would fetch real balances from Nexo API
        mock_total_value = 10000  # $10,000 portfolio
        prices = market_data.get_current_prices(list(portfolio.allocation.keys()))
        
        balances = {}
        for token, target_percent in portfolio.allocation.items():
            if token in prices and prices[token] > 0:
                target_value = (target_percent / 100) * mock_total_value
                balances[token] = target_value / prices[token]
            else:
                balances[token] = 0
        
        return balances
    
    def _take_portfolio_snapshot(self, portfolio_id: int):
        \"\"\"Take a snapshot of current portfolio state\"\"\"
        
        current_balances = self._get_current_balances(portfolio_id)
        portfolio_data = market_data.calculate_portfolio_value(current_balances)
        
        snapshot = PortfolioSnapshot(
            id=0,
            portfolio_id=portfolio_id,
            balances=current_balances,
            prices=portfolio_data['prices'],
            total_value=portfolio_data['total_value'],
            timestamp=datetime.now()
        )
        
        self.db.save_portfolio_snapshot(snapshot)
    
    def get_cost_analysis(self, portfolio_id: int) -> Dict:
        \"\"\"Analyze trading costs across platforms\"\"\"
        
        transactions = self.db.get_portfolio_transactions(portfolio_id, limit=100)
        
        nexo_transactions = [t for t in transactions if t.platform == 'nexo']
        nexo_pro_transactions = [t for t in transactions if t.platform == 'nexo_pro']
        
        nexo_total_cost = sum(t.fee for t in nexo_transactions)
        nexo_pro_total_cost = sum(t.fee for t in nexo_pro_transactions)
        
        nexo_total_volume = sum(t.quantity * t.price for t in nexo_transactions)
        nexo_pro_total_volume = sum(t.quantity * t.price for t in nexo_pro_transactions)
        
        return {
            'nexo': {
                'total_cost': nexo_total_cost,
                'total_volume': nexo_total_volume,
                'average_fee_rate': nexo_total_cost / nexo_total_volume if nexo_total_volume > 0 else 0,
                'transaction_count': len(nexo_transactions)
            },
            'nexo_pro': {
                'total_cost': nexo_pro_total_cost,
                'total_volume': nexo_pro_total_volume,
                'average_fee_rate': nexo_pro_total_cost / nexo_pro_total_volume if nexo_pro_total_volume > 0 else 0,
                'transaction_count': len(nexo_pro_transactions)
            },
            'total_savings': nexo_total_cost - nexo_pro_total_cost if nexo_total_cost > nexo_pro_total_cost else 0
        }
"""

with open("nexo_portfolio_manager/app/components/portfolio.py", "w") as f:
    f.write(portfolio_content.strip())

# Create app/utils/helpers.py
helpers_content = """import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from datetime import datetime

def format_currency(amount: float, currency: str = "USD") -> str:
    \"\"\"Format currency with proper symbols\"\"\"
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "BTC":
        return f"₿{amount:.8f}"
    elif currency == "ETH":
        return f"Ξ{amount:.6f}"
    else:
        return f"{amount:.4f} {currency}"

def format_percentage(value: float) -> str:
    \"\"\"Format percentage with color coding\"\"\"
    color = "green" if value >= 0 else "red"
    return f"<span style='color: {color}'>{value:+.2f}%</span>"

def create_allocation_pie_chart(chart_data: Dict) -> go.Figure:
    \"\"\"Create portfolio allocation pie chart\"\"\"
    
    fig = go.Figure(data=[
        go.Pie(
            labels=chart_data['labels'],
            values=chart_data['values'],
            hole=0.3,
            marker_colors=chart_data['colors'],
            textinfo='label+percent',
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Current Portfolio Allocation",
        showlegend=True,
        height=500,
        margin=dict(t=50, b=0, l=0, r=0)
    )
    
    return fig

def create_performance_chart(snapshots: List[Dict]) -> go.Figure:
    \"\"\"Create portfolio performance line chart\"\"\"
    
    if not snapshots:
        return go.Figure()
    
    dates = [snapshot['date'] for snapshot in snapshots]
    values = [snapshot['value'] for snapshot in snapshots]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Portfolio Performance",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (USD)",
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    return fig

def create_rebalance_comparison_chart(current_allocation: Dict, target_allocation: Dict) -> go.Figure:
    \"\"\"Create comparison chart for current vs target allocation\"\"\"
    
    tokens = list(set(current_allocation.keys()) | set(target_allocation.keys()))
    
    current_values = [current_allocation.get(token, 0) for token in tokens]
    target_values = [target_allocation.get(token, 0) for token in tokens]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Current',
        x=tokens,
        y=current_values,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Target',
        x=tokens,
        y=target_values,
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title="Current vs Target Allocation",
        xaxis_title="Tokens",
        yaxis_title="Allocation (%)",
        barmode='group',
        height=400
    )
    
    return fig

def create_metrics_dashboard(metrics: Dict) -> None:
    \"\"\"Create metrics dashboard with columns\"\"\"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Annual Return",
            value=f"{metrics.get('annual_return', 0)*100:.2f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Volatility",
            value=f"{metrics.get('annual_volatility', 0)*100:.2f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Sharpe Ratio",
            value=f"{metrics.get('sharpe_ratio', 0):.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Max Drawdown",
            value=f"{metrics.get('max_drawdown', 0)*100:.2f}%",
            delta=None
        )

def display_portfolio_summary(portfolio_data: Dict) -> None:
    \"\"\"Display portfolio summary information\"\"\"
    
    st.subheader(f"Portfolio: {portfolio_data['portfolio_name']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Total Portfolio Value",
            value=format_currency(portfolio_data['current_value']),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Diversification Ratio",
            value=f"{portfolio_data['diversification_ratio']:.2f}",
            delta=None
        )

def create_transaction_history_table(transactions: List[Dict]) -> pd.DataFrame:
    \"\"\"Create formatted transaction history table\"\"\"
    
    if not transactions:
        return pd.DataFrame()
    
    df = pd.DataFrame(transactions)
    
    # Format columns
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    df['quantity'] = df['quantity'].apply(lambda x: f"{x:.6f}")
    df['price'] = df['price'].apply(lambda x: format_currency(x))
    df['fee'] = df['fee'].apply(lambda x: format_currency(x))
    
    # Reorder columns
    column_order = ['timestamp', 'token', 'transaction_type', 'quantity', 'price', 'fee', 'platform']
    df = df[column_order]
    
    # Rename columns for display
    df.columns = ['Date', 'Token', 'Type', 'Quantity', 'Price', 'Fee', 'Platform']
    
    return df

def validate_allocation_input(allocation: Dict[str, float]) -> Tuple[bool, str]:
    \"\"\"Validate user allocation input\"\"\"
    
    if not allocation:
        return False, "Allocation cannot be empty"
    
    # Check if all values are non-negative
    for token, percent in allocation.items():
        if percent < 0:
            return False, f"Allocation for {token} cannot be negative"
    
    # Check if total sums to 100%
    total = sum(allocation.values())
    if abs(total - 100) > 0.01:
        return False, f"Total allocation must equal 100%. Current total: {total:.2f}%"
    
    return True, "Valid allocation"

def get_preset_allocations() -> Dict[str, Dict[str, float]]:
    \"\"\"Get preset portfolio allocations\"\"\"
    
    return {
        "Conservative": {
            "BTC": 40.0,
            "ETH": 30.0,
            "USDT": 20.0,
            "USDC": 10.0
        },
        "Moderate": {
            "BTC": 35.0,
            "ETH": 25.0,
            "ADA": 15.0,
            "DOT": 10.0,
            "LINK": 10.0,
            "USDT": 5.0
        },
        "Aggressive": {
            "BTC": 30.0,
            "ETH": 25.0,
            "SOL": 15.0,
            "AVAX": 10.0,
            "MATIC": 10.0,
            "UNI": 10.0
        },
        "DeFi Focus": {
            "ETH": 40.0,
            "UNI": 20.0,
            "LINK": 15.0,
            "MATIC": 15.0,
            "AVAX": 10.0
        }
    }

class SessionState:
    \"\"\"Manage session state for the application\"\"\"
    
    @staticmethod
    def initialize():
        \"\"\"Initialize session state variables\"\"\"
        if 'current_portfolio_id' not in st.session_state:
            st.session_state.current_portfolio_id = None
        
        if 'paper_trading' not in st.session_state:
            st.session_state.paper_trading = False
        
        if 'last_rebalance_check' not in st.session_state:
            st.session_state.last_rebalance_check = datetime.now()
    
    @staticmethod
    def get_current_portfolio_id():
        return st.session_state.get('current_portfolio_id')
    
    @staticmethod
    def set_current_portfolio_id(portfolio_id: int):
        st.session_state.current_portfolio_id = portfolio_id
"""

with open("nexo_portfolio_manager/app/utils/helpers.py", "w") as f:
    f.write(helpers_content.strip())

print("Created portfolio management and utility components!")