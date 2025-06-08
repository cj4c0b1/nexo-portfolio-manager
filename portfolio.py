from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd

from database import DatabaseManager
from models import Portfolio, PortfolioSnapshot, RebalanceSettings
from market_data import market_data
from rebalancer import PortfolioRebalancer, RiskAnalyzer
from settings import settings
import nexo
from settings import settings
from typing import Dict, Any

class PortfolioManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.risk_analyzer = RiskAnalyzer()
        
        # Initialize Nexo clients with proper error handling
        self.nexo_client = None
        self.nexo_pro_client = None
        
        try:
            from nexo_client import NexoProClient  # Import here to avoid circular imports
            self.nexo_client = NexoProClient()
            self.nexo_pro_client = self.nexo_client  # Alias for compatibility
        except ImportError as e:
            print(f"Warning: Could not import Nexo client: {e}")
        except Exception as e:
            print(f"Warning: Could not initialize Nexo client: {e}")

    def create_portfolio(self, name: str, allocation: Dict[str, float]) -> Portfolio:
        """Create a new portfolio with validation"""

        # Validate allocation
        if not self._validate_allocation(allocation):
            raise ValueError("Invalid allocation: must sum to 100%")

        # Check for supported tokens
        unsupported_tokens = set(allocation.keys()) - set(settings.SUPPORTED_TOKENS)
        if unsupported_tokens:
            raise ValueError(f"Unsupported tokens: {unsupported_tokens}")

        return self.db.create_portfolio(name, allocation)

    def get_portfolio_performance(self, portfolio_id: int, days: int = 30) -> Dict:
        """Get comprehensive portfolio performance metrics"""

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
        """Get rebalancing suggestions for a portfolio"""

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
        """Execute portfolio rebalancing"""

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
        """Update portfolio target allocation"""

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
        """Set or update rebalancing settings for a portfolio"""

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
        """Get data for portfolio allocation charts"""

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
        """Validate that allocation percentages sum to 100"""
        total = sum(allocation.values())
        return abs(total - 100.0) < 0.01  # Allow for small floating point errors

    def get_real_balances(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch real account balances from Nexo API using python-nexo library.
        
        Returns:
            Dict containing token balances with structure:
            {
                'BTC': {'available': float, 'total': float, 'in_orders': float, 'usd_value': float},
                'ETH': {...},
                ...
            }
            
            Returns an empty dict if there's an error or no balances found.
        """
        try:
            # Initialize the Nexo client with API keys from settings
            # Note: The python-nexo library uses 'api_key' and 'api_secret' as parameter names
            client = nexo.Client(
                api_key=settings.NEXO_PUBLIC_KEY,
                api_secret=settings.NEXO_SECRET_KEY
            )
            
            # Get account balances from Nexo
            balances_data = client.get_account_balances()
            
            if not balances_data or 'balances' not in balances_data:
                print("Warning: Could not fetch account balances. Please check your API credentials.")
                return {}
                
            # Process the balances
            balances = {}
            for balance in balances_data['balances']:
                try:
                    asset = balance.get('assetName')
                    if not asset:
                        continue
                        
                    total = float(balance.get('totalBalance', 0))
                    available = float(balance.get('availableBalance', 0))
                    locked = float(balance.get('lockedBalance', 0))
                    
                    # Skip zero balances to keep the response clean
                    if total <= 0 and available <= 0 and locked <= 0:
                        continue
                        
                    # Calculate USD value (if not provided)
                    usd_value = 0.0
                    if asset == 'USDT' or asset == 'USDC':
                        usd_value = available
                    else:
                        try:
                            # Try to get price from market data if available
                            if hasattr(market_data, 'get_current_price'):
                                price = market_data.get_current_price(f"{asset}USDT") or 0
                                usd_value = available * price
                            else:
                                # Fallback: Use 0 value for non-stablecoin assets if we can't get price
                                print(f"Warning: Could not get price for {asset}, using 0 value")
                                usd_value = 0.0
                        except Exception as e:
                            print(f"Warning: Error getting price for {asset}: {str(e)}")
                            usd_value = 0.0
                    
                    balances[asset] = {
                        'available': available,
                        'total': total,
                        'in_orders': locked,  # Using locked balance as in_orders
                        'usd_value': usd_value
                    }
                    
                except (KeyError, ValueError) as ve:
                    print(f"Warning: Error processing balance for asset {asset}: {str(ve)}")
                    continue
            
            return balances
            
        except Exception as e:
            print(f"Error fetching balances from Nexo: {str(e)}")
            # Return empty dict on error
            return {}

    def _get_mock_balances(self) -> Dict[str, Dict[str, float]]:
        """Get mock balances for testing and development."""
        return {
            'BTC': {'available': 0.1, 'in_orders': 0.01, 'total': 0.11, 'usd_value': 4950.0},  # 0.11 * 45000
            'ETH': {'available': 2.5, 'in_orders': 0.5, 'total': 3.0, 'usd_value': 9000.0},    # 3.0 * 3000
            'ADA': {'available': 1000, 'in_orders': 200, 'total': 1200, 'usd_value': 600.0},   # 1200 * 0.5
            'USDT': {'available': 5000, 'in_orders': 0, 'total': 5000, 'usd_value': 5000.0},   # 5000 * 1.0
            'NEXO': {'available': 1000, 'in_orders': 0, 'total': 1000, 'usd_value': 1200.0}    # 1000 * 1.2
        }
        
    def _process_balances(self, account_summary: Dict) -> Dict[str, Dict[str, float]]:
        """Process account summary into a standardized balance format.
        
        Args:
            account_summary: Raw account summary from Nexo Pro API
            
        Returns:
            Dict containing processed balances or None if processing fails
        """
        processed = {}
        
        try:
            # Handle different response formats
            if isinstance(account_summary, list):
                # If it's a list, assume it's a list of balance objects
                for item in account_summary:
                    try:
                        asset = item.get('currency')
                        if not asset:
                            continue
                            
                        available = float(item.get('available', 0))
                        in_orders = float(item.get('in_orders', 0))
                        total = available + in_orders
                        
                        # Skip zero balances
                        if total <= 0:
                            continue
                            
                        # Get current price for the asset
                        price = getattr(market_data, 'get_current_price', lambda x: 0.0)(f"{asset}USDT")
                        usd_value = total * price
                        
                        processed[asset] = {
                            'available': available,
                            'in_orders': in_orders,
                            'total': total,
                            'usd_value': usd_value
                        }
                    except (ValueError, TypeError, AttributeError) as e:
                        print(f"Error processing balance item: {e}")
                        continue
                        
            elif isinstance(account_summary, dict):
                # If it's a dict, look for a 'balances' key
                balances = account_summary.get('balances', {})
                if not isinstance(balances, dict):
                    print(f"Unexpected balances format: {type(balances)}")
                    return None
                    
                for asset, data in balances.items():
                    try:
                        if not asset:
                            continue
                            
                        available = float(data.get('available', 0))
                        in_orders = float(data.get('in_orders', 0))
                        total = available + in_orders
                        
                        # Skip zero balances
                        if total <= 0:
                            continue
                            
                        # Get current price for the asset
                        price = getattr(market_data, 'get_current_price', lambda x: 0.0)(f"{asset}USDT")
                        usd_value = total * price
                        
                        processed[asset] = {
                            'available': available,
                            'in_orders': in_orders,
                            'total': total,
                            'usd_value': usd_value
                        }
                    except (ValueError, TypeError, AttributeError) as e:
                        print(f"Error processing balance for {asset}: {e}")
                        continue
            else:
                print(f"Unexpected account summary format: {type(account_summary)}")
                return None
                
            return processed if processed else None
            
        except Exception as e:
            print(f"Unexpected error in _process_balances: {e}")
            return None
        
    def get_balances(self) -> Dict[str, Dict[str, float]]:
        """Get current balances from Nexo Pro."""
        # Check if we should use mock data (for testing or when API is unavailable)
        use_mock = getattr(settings, 'USE_MOCK_DATA', True)
        
        if use_mock:
            print("Using mock balance data (USE_MOCK_DATA is True)")
            return self._get_mock_balances()
            
        if not self.nexo_pro_client:
            print("No Nexo Pro client available, using mock data")
            return self._get_mock_balances()
            
        try:
            # Try to get real balances from Nexo Pro
            print("Fetching real balances from Nexo Pro API...")
            account_summary = self.nexo_pro_client.get_account_summary()
            
            if not account_summary:
                print("No data returned from Nexo Pro API, using mock data")
                return self._get_mock_balances()
                
            # Process the account summary
            processed = self._process_balances(account_summary)
            
            if not processed:
                print("No valid balance data processed, using mock data")
                return self._get_mock_balances()
                
            print(f"Successfully fetched balances for {len(processed)} assets")
            return processed
            
        except Exception as e:
            print(f"Error in get_balances: {str(e)}")
            print("Falling back to mock data")
            return self._get_mock_balances()

    def get_deposit_address(self, asset: str) -> Optional[str]:
        """
        Get deposit address for a specific asset on Nexo Pro.
        
        Args:
            asset: The asset to get deposit address for (e.g., 'BTC', 'ETH')
            
        Returns:
            str: Deposit address or None if not found
        """
        try:
            # This would be replaced with actual Nexo Pro API call
            # For now, return a mock address
            return f"nexo_pro_deposit_address_for_{asset.lower()}"
        except Exception as e:
            print(f"Error getting deposit address for {asset}: {e}")
            return None

    def transfer_to_nexo(self, asset: str, amount: float) -> bool:
        """
        Transfer assets from Nexo Pro to Nexo.
        
        Args:
            asset: The asset to transfer (e.g., 'BTC', 'ETH')
            amount: Amount to transfer
            
        Returns:
            bool: True if transfer was successful, False otherwise
        """
        try:
            # This would be replaced with actual Nexo Pro API call
            print(f"Transferring {amount} {asset} from Nexo Pro to Nexo")
            # Mock implementation - in a real app, this would make an API call
            return True
        except Exception as e:
            print(f"Error transferring {amount} {asset} to Nexo: {e}")
            return False

    def _get_current_balances(self, portfolio_id: int) -> Dict[str, float]:
        """
        Get current token balances for a portfolio.
        
        This method gets real balances from Nexo and returns them in the expected format.
        """
        # Get real balances from Nexo
        real_balances = self.get_real_balances()
        
        # Return available balances in the expected format
        return {asset: data['available'] for asset, data in real_balances.items()}

    def _take_portfolio_snapshot(self, portfolio_id: int):
        """Take a snapshot of current portfolio state"""

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
        """Analyze trading costs across platforms"""

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