import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
from datetime import datetime

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency with proper symbols"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "BTC":
        return f"₿{amount:.8f}"
    elif currency == "ETH":
        return f"Ξ{amount:.6f}"
    else:
        return f"{amount:.4f} {currency}"

def format_percentage(value: float) -> str:
    """Format percentage with color coding"""
    color = "green" if value >= 0 else "red"
    return f"<span style='color: {color}'>{value:+.2f}%</span>"

def create_allocation_pie_chart(chart_data: Dict) -> go.Figure:
    """Create portfolio allocation pie chart"""

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
    """Create portfolio performance line chart"""

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
    """Create comparison chart for current vs target allocation"""

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
    """Create metrics dashboard with columns"""

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
    """Display portfolio summary information"""

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
    """Create formatted transaction history table"""

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
    """Validate user allocation input"""

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
    """Get preset portfolio allocations"""

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
    """Manage session state for the application"""

    @staticmethod
    def initialize():
        """Initialize session state variables"""
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