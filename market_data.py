import yfinance as yf
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class MarketDataProvider:
    def __init__(self):
        # Map of crypto symbols to their most common trading pairs
        self.crypto_symbols = {
            # Major cryptocurrencies with direct USD pairs
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD',
            'ADA': 'ADA-USD',
            'DOT': 'DOT-USD',
            'MATIC': 'MATIC-USD',
            'LINK': 'LINK-USD',
            'UNI': 'UNI-USD',
            'SOL': 'SOL-USD',
            'AVAX': 'AVAX-USD',
            
            # NEXO is typically traded against USDT or BTC
            'NEXO': 'NEXO-USDT',
            
            # Stablecoins
            'USDT': 'USDT-USD',
            'USDC': 'USDC-USD',
            'DAI': 'DAI-USD',
            'BUSD': 'BUSD-USD',
            
            # Other common altcoins
            'XRP': 'XRP-USD',
            'DOGE': 'DOGE-USD',
            'LTC': 'LTC-USD',
            'ATOM': 'ATOM-USD',
            'XLM': 'XLM-USD',
            'ALGO': 'ALGO-USD',
            'ETC': 'ETC-USD',
            'XMR': 'XMR-USD',
            'ZEC': 'ZEC-USD',
            'DASH': 'DASH-USD'
        }
        self.stablecoin_price = 1.0

    def _create_session(self):
        """Create a requests session with retry logic"""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def _get_price_from_yahoo(self, symbol: str) -> Optional[float]:
        """Get price from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty and 'Close' in hist.columns:
                return float(hist['Close'].iloc[-1])
        except Exception as e:
            print(f"Yahoo Finance error for {symbol}: {e}")
        return None

    def _get_price_from_coingecko(self, token_id: str) -> Optional[float]:
        """Get price from CoinGecko API"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd"
            session = self._create_session()
            response = session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get(token_id, {}).get('usd')
        except Exception as e:
            print(f"CoinGecko API error for {token_id}: {e}")
        return None

    def get_current_prices(self, tokens: List[str]) -> Dict[str, float]:
        """Get current prices for list of tokens using multiple data sources"""
        prices = {}
        
        # Map of token symbols to their CoinGecko IDs
        coingecko_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'MATIC': 'polygon',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'SOL': 'solana',
            'AVAX': 'avalanche-2',
            'NEXO': 'nexo',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'DAI': 'dai',
            'BUSD': 'binance-usd',
            'XRP': 'ripple',
            'DOGE': 'dogecoin',
            'LTC': 'litecoin',
            'ATOM': 'cosmos',
            'XLM': 'stellar',
            'ALGO': 'algorand',
            'ETC': 'ethereum-classic',
            'XMR': 'monero',
            'ZEC': 'zcash',
            'DASH': 'dash'
        }

        for token in tokens:
            price = None
            
            # Skip if already processed
            if token in prices:
                continue
                
            # Handle stablecoins
            if token in ['USDT', 'USDC', 'DAI', 'BUSD']:
                prices[token] = self.stablecoin_price
                continue
                
            # Try Yahoo Finance first
            if token in self.crypto_symbols:
                price = self._get_price_from_yahoo(self.crypto_symbols[token])
            
            # If Yahoo fails, try CoinGecko
            if price is None and token in coingecko_ids:
                print(f"Trying CoinGecko for {token}...")
                price = self._get_price_from_coingecko(coingecko_ids[token])
            
            # If both APIs fail, use mock price
            if price is None:
                print(f"Using mock price for {token}")
                price = self._get_mock_price(token)
            
            prices[token] = price
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.2)
            
        return prices

    def get_historical_prices(self, token: str, days: int = 30) -> Dict[str, List]:
        """Get historical prices for a token"""
        if token in ['USDT', 'USDC']:
            dates = []
            prices = []
            for i in range(days):
                date = datetime.now() - timedelta(days=days-i)
                dates.append(date.strftime('%Y-%m-%d'))
                prices.append(self.stablecoin_price)
            return {'dates': dates, 'prices': prices}

        if token in self.crypto_symbols:
            try:
                ticker = yf.Ticker(self.crypto_symbols[token])
                hist = ticker.history(period=f"{days}d")

                dates = [date.strftime('%Y-%m-%d') for date in hist.index]
                prices = [float(price) for price in hist['Close']]

                return {'dates': dates, 'prices': prices}
            except Exception as e:
                print(f"Error fetching historical data for {token}: {e}")
                return self._get_mock_historical_data(token, days)

        return self._get_mock_historical_data(token, days)

    def _get_mock_price(self, token: str) -> float:
        """Get mock price for testing"""
        mock_prices = {
            'BTC': 45000.0,
            'ETH': 3000.0,
            'ADA': 0.5,
            'DOT': 7.0,
            'MATIC': 0.8,
            'LINK': 15.0,
            'UNI': 6.0,
            'SOL': 100.0,
            'AVAX': 35.0,
            'NEXO': 1.2,
            'USDT': 1.0,
            'USDC': 1.0
        }
        return mock_prices.get(token, 1.0)

    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a trading pair (e.g., 'BTCUSDT')
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Current price as float, or 0.0 if not found
        """
        # Handle stablecoin pairs first
        stable_pairs = {
            'USDTUSD': 1.0,
            'USDCUSD': 1.0,
            'DAIUSD': 1.0,
            'BUSDUSD': 1.0,
            'USDTUSDT': 1.0,
            'USDCUSDT': 1.0,
            'DAIUSDT': 1.0,
            'BUSDUSDT': 1.0
        }
        
        if symbol in stable_pairs:
            return stable_pairs[symbol]
            
        # Extract base and quote currency (e.g., 'BTC' and 'USDT' from 'BTCUSDT')
        if len(symbol) < 4:  # Minimum length for a valid pair like 'BTCUSDT'
            return 0.0
            
        # Normalize symbol (e.g., 'NEXOUSD' -> 'NEXO-USDT')
        base_asset = symbol[:-3]  # Get the base asset (e.g., 'BTC' from 'BTCUSDT')
        
        # Special case for NEXO and other problematic assets
        if base_asset in ['NEXO', 'NEXO2', 'NEXO3']:  # Common variations
            try:
                import requests
                # Try CoinGecko first
                cg_url = "https://api.coingecko.com/api/v3/simple/price"
                params = {'ids': 'nexo', 'vs_currencies': 'usd'}
                response = requests.get(cg_url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'nexo' in data and 'usd' in data['nexo']:
                        return float(data['nexo']['usd'])
                        
                # Fallback to Binance API
                binance_url = "https://api.binance.com/api/v3/ticker/price"
                params = {'symbol': 'NEXOUSDT'}
                response = requests.get(binance_url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'price' in data:
                        return float(data['price'])
                        
            except Exception as e:
                print(f"Warning: Could not fetch NEXO price from APIs: {e}")
            
            # Final fallback to a hardcoded price if all else fails
            return 1.2  # Example price, should be updated to current market price
            
        # Try common quote currencies (longest first to match USDT before USD)
        quote_currencies = ['USDT', 'USDC', 'BUSD', 'DAI', 'BTC', 'ETH', 'USD']
        
        for quote in quote_currencies:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                if not base:
                    continue
                    
                # Check if we have a direct mapping
                yf_symbol = f"{base}-{quote}" if quote != 'USD' else f"{base}-{quote}"
                
                try:
                    ticker = yf.Ticker(yf_symbol)
                    hist = ticker.history(period="1d")
                    if not hist.empty and not hist['Close'].isna().all():
                        price = float(hist['Close'].iloc[-1])
                        if price > 0:  # Only return if we got a valid price
                            return price
                except Exception as e:
                    # Silently try the next quote currency
                    continue
        
        # If we get here, try to find any trading pair for the base asset
        base = symbol[:3]  # Try first 3 characters as base
        if base in self.crypto_symbols:
            try:
                ticker = yf.Ticker(self.crypto_symbols[base])
                hist = ticker.history(period="1d")
                if not hist.empty and not hist['Close'].isna().all():
                    return float(hist['Close'].iloc[-1])
            except Exception as e:
                print(f"Warning: Could not fetch price for {base} using any available pairs")
        
        # Fallback to mock price if not found
        return self._get_mock_price(base if 'base' in locals() else symbol[:3])

    def _get_mock_historical_data(self, token: str, days: int) -> Dict[str, List]:
        """Generate mock historical data"""
        base_price = self._get_mock_price(token)
        dates = []
        prices = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            dates.append(date.strftime('%Y-%m-%d'))

            # Add some random variation
            import random
            variation = random.uniform(0.9, 1.1)
            prices.append(base_price * variation)

        return {'dates': dates, 'prices': prices}

    def calculate_portfolio_value(self, balances: Dict[str, float]) -> Dict:
        """Calculate total portfolio value"""
        tokens = list(balances.keys())
        prices = self.get_current_prices(tokens)

        total_value = 0
        asset_values = {}

        for token, balance in balances.items():
            if token in prices:
                value = balance * prices[token]
                asset_values[token] = {
                    'balance': balance,
                    'price': prices[token],
                    'value': value
                }
                total_value += value

        return {
            'total_value': total_value,
            'asset_values': asset_values,
            'prices': prices
        }

# Global market data provider
market_data = MarketDataProvider()