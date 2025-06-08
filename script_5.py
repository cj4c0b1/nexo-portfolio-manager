# Create app/components/rebalancer.py
rebalancer_content = """import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from app.api.nexo_client import get_nexo_client
from app.api.market_data import market_data
from app.db.models import Transaction, RebalanceEvent
from config.settings import settings

class PortfolioRebalancer:
    def __init__(self, portfolio_id: int, use_mock: bool = True):
        self.portfolio_id = portfolio_id
        self.nexo_client = get_nexo_client(use_mock=use_mock)
        self.min_trade_value = settings.MIN_TRADE_VALUE
    
    def calculate_rebalance_trades(self, 
                                 current_balances: Dict[str, float],
                                 target_allocation: Dict[str, float],
                                 total_portfolio_value: float) -> List[Dict]:
        \"\"\"Calculate trades needed to rebalance portfolio\"\"\"
        
        # Get current prices
        tokens = list(current_balances.keys())
        prices = market_data.get_current_prices(tokens)
        
        # Calculate current allocation percentages
        current_allocation = {}
        for token, balance in current_balances.items():
            if token in prices and total_portfolio_value > 0:
                current_value = balance * prices[token]
                current_allocation[token] = (current_value / total_portfolio_value) * 100
            else:
                current_allocation[token] = 0
        
        # Calculate required trades
        trades = []
        
        for token in target_allocation:
            if token not in current_allocation:
                current_allocation[token] = 0
            
            target_percent = target_allocation[token]
            current_percent = current_allocation[token]
            
            # Calculate difference
            percent_diff = target_percent - current_percent
            
            if abs(percent_diff) > 0.1:  # Only trade if difference > 0.1%
                target_value = (target_percent / 100) * total_portfolio_value
                current_value = (current_percent / 100) * total_portfolio_value
                value_diff = target_value - current_value
                
                if token in prices and prices[token] > 0:
                    quantity_diff = value_diff / prices[token]
                    
                    if abs(value_diff) >= self.min_trade_value:
                        trade = {
                            'token': token,
                            'side': 'buy' if quantity_diff > 0 else 'sell',
                            'quantity': abs(quantity_diff),
                            'estimated_value': abs(value_diff),
                            'current_percent': current_percent,
                            'target_percent': target_percent,
                            'price': prices[token]
                        }
                        trades.append(trade)
        
        return trades
    
    def execute_rebalance(self, 
                         trades: List[Dict], 
                         paper_trading: bool = True) -> Tuple[List[Transaction], float]:
        \"\"\"Execute rebalance trades\"\"\"
        executed_transactions = []
        total_cost = 0
        
        for trade in trades:
            try:
                if paper_trading:
                    # Simulate the trade
                    transaction = Transaction(
                        id=0,  # Will be set by database
                        portfolio_id=self.portfolio_id,
                        token=trade['token'],
                        transaction_type='rebalance',
                        quantity=trade['quantity'],
                        price=trade['price'],
                        fee=trade['estimated_value'] * 0.002,  # 0.2% fee estimate
                        platform='nexo_pro_mock',
                        timestamp=datetime.now()
                    )
                    total_cost += transaction.fee
                    executed_transactions.append(transaction)
                    
                else:
                    # Execute real trade
                    pair = f"{trade['token']}/USDT"
                    
                    if pair in settings.NEXO_PRO_PAIRS:
                        response = self.nexo_client.place_order(
                            pair=pair,
                            side=trade['side'],
                            quantity=trade['quantity']
                        )
                        
                        if response.get('status') == 'filled':
                            transaction = Transaction(
                                id=0,
                                portfolio_id=self.portfolio_id,
                                token=trade['token'],
                                transaction_type='rebalance',
                                quantity=trade['quantity'],
                                price=response.get('price', trade['price']),
                                fee=response.get('fee', 0),
                                platform='nexo_pro',
                                timestamp=datetime.now()
                            )
                            total_cost += transaction.fee
                            executed_transactions.append(transaction)
                        
            except Exception as e:
                print(f"Error executing trade for {trade['token']}: {e}")
                continue
        
        return executed_transactions, total_cost
    
    def should_rebalance(self, 
                        current_balances: Dict[str, float],
                        target_allocation: Dict[str, float],
                        threshold: float) -> Tuple[bool, Dict[str, float]]:
        \"\"\"Check if portfolio should be rebalanced based on threshold\"\"\"
        
        portfolio_data = market_data.calculate_portfolio_value(current_balances)
        total_value = portfolio_data['total_value']
        
        if total_value == 0:
            return False, {}
        
        # Calculate current allocation percentages
        current_allocation = {}
        deviations = {}
        
        for token, balance in current_balances.items():
            if token in portfolio_data['asset_values']:
                asset_value = portfolio_data['asset_values'][token]['value']
                current_percent = (asset_value / total_value) * 100
                current_allocation[token] = current_percent
                
                target_percent = target_allocation.get(token, 0)
                deviation = abs(current_percent - target_percent)
                deviations[token] = deviation
        
        # Check if any asset exceeds threshold
        max_deviation = max(deviations.values()) if deviations else 0
        should_rebalance = max_deviation > threshold
        
        return should_rebalance, deviations
    
    def optimize_trade_platform(self, trade_value: float) -> str:
        \"\"\"Determine optimal platform for trade based on costs\"\"\"
        
        # Nexo traditional: ~1-1.5% spread, no explicit fees
        nexo_cost = trade_value * 0.0125  # Average 1.25% spread
        
        # Nexo Pro: ~0.05% spread + 0.2% fee
        nexo_pro_cost = trade_value * 0.0025  # 0.05% spread + 0.2% fee
        
        if trade_value > 100 and nexo_pro_cost < nexo_cost:
            return 'nexo_pro'
        else:
            return 'nexo'
    
    def calculate_rebalance_frequency_score(self, 
                                          frequency: str, 
                                          portfolio_volatility: float) -> float:
        \"\"\"Calculate optimal rebalancing frequency based on portfolio characteristics\"\"\"
        
        base_scores = {
            'daily': 1.0,
            'weekly': 0.8,
            'monthly': 0.6,
            'quarterly': 0.4
        }
        
        volatility_adjustment = portfolio_volatility / 20  # Normalize volatility
        
        return base_scores.get(frequency, 0.5) + volatility_adjustment

class RiskAnalyzer:
    @staticmethod
    def calculate_portfolio_metrics(snapshots: List) -> Dict:
        \"\"\"Calculate portfolio risk metrics\"\"\"
        if len(snapshots) < 2:
            return {}
        
        values = [snapshot.total_value for snapshot in snapshots]
        returns = []
        
        for i in range(1, len(values)):
            daily_return = (values[i] - values[i-1]) / values[i-1]
            returns.append(daily_return)
        
        if not returns:
            return {}
        
        returns_array = np.array(returns)
        
        # Calculate metrics
        mean_return = np.mean(returns_array)
        volatility = np.std(returns_array)
        
        # Annualized metrics (assuming daily data)
        annual_return = mean_return * 365
        annual_volatility = volatility * np.sqrt(365)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
        
        # Maximum drawdown
        peak = values[0]
        max_drawdown = 0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_return': (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
        }
    
    @staticmethod
    def calculate_diversification_ratio(allocation: Dict[str, float]) -> float:
        \"\"\"Calculate portfolio diversification ratio\"\"\"
        weights = list(allocation.values())
        if not weights:
            return 0
        
        # Herfindahl-Hirschman Index (lower is more diversified)
        hhi = sum(w**2 for w in weights)
        
        # Convert to diversification ratio (higher is more diversified)
        diversification_ratio = 1 / hhi if hhi > 0 else 0
        
        return min(diversification_ratio, 1.0)
"""

with open("nexo_portfolio_manager/app/components/rebalancer.py", "w") as f:
    f.write(rebalancer_content.strip())

print("Created portfolio rebalancer component!")