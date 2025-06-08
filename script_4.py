# Create app/api/nexo_client.py
nexo_client_content = """import requests
import time
import hashlib
import hmac
import json
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import settings

class NexoProClient:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or settings.NEXO_PUBLIC_KEY
        self.api_secret = api_secret or settings.NEXO_SECRET_KEY
        self.base_url = "https://api.nexo.io/pro/v1"
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Nexo Pro API credentials not provided")
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        \"\"\"Generate HMAC signature for Nexo Pro API\"\"\"
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        \"\"\"Make authenticated request to Nexo Pro API\"\"\"
        timestamp = str(int(time.time() * 1000))
        path = f"/pro/v1{endpoint}"
        
        if method.upper() == "GET" and params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            path += f"?{query_string}"
            body = ""
        else:
            body = json.dumps(data) if data else ""
        
        signature = self._generate_signature(timestamp, method, path, body)
        
        headers = {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
    
    def get_account_summary(self) -> Dict:
        \"\"\"Get account balances and summary\"\"\"
        return self._make_request("GET", "/accountSummary")
    
    def get_pairs(self) -> List[Dict]:
        \"\"\"Get available trading pairs\"\"\"
        return self._make_request("GET", "/pairs")
    
    def get_quote(self, pair: str, amount: float, side: str) -> Dict:
        \"\"\"Get price quote for a trade\"\"\"
        params = {
            "pair": pair,
            "amount": amount,
            "side": side
        }
        return self._make_request("GET", "/quote", params=params)
    
    def place_order(self, pair: str, side: str, quantity: float, order_type: str = "market") -> Dict:
        \"\"\"Place a trading order\"\"\"
        data = {
            "pair": pair,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }
        return self._make_request("POST", "/orders", data=data)
    
    def cancel_order(self, order_id: str) -> Dict:
        \"\"\"Cancel an existing order\"\"\"
        data = {"orderId": order_id}
        return self._make_request("POST", "/orders/cancel", data=data)
    
    def get_order_history(self, pairs: List[str] = None, limit: int = 100) -> List[Dict]:
        \"\"\"Get order history\"\"\"
        params = {"pageSize": limit}
        if pairs:
            params["pairs"] = ",".join(pairs)
        
        return self._make_request("GET", "/orders", params=params)
    
    def get_trades(self, pairs: List[str] = None, limit: int = 100) -> List[Dict]:
        \"\"\"Get trade history\"\"\"
        params = {"pageSize": limit}
        if pairs:
            params["pairs"] = ",".join(pairs)
        
        return self._make_request("GET", "/trades", params=params)

class MockNexoClient:
    \"\"\"Mock client for testing and development\"\"\"
    
    def __init__(self):
        self.mock_balances = {
            "BTC": {"balance": 0.1, "price": 45000},
            "ETH": {"balance": 2.5, "price": 3000},
            "ADA": {"balance": 1000, "price": 0.5},
            "USDT": {"balance": 5000, "price": 1.0}
        }
    
    def get_account_summary(self) -> Dict:
        \"\"\"Mock account summary\"\"\"
        balances = []
        total_value = 0
        
        for token, data in self.mock_balances.items():
            value = data["balance"] * data["price"]
            total_value += value
            balances.append({
                "asset": token,
                "balance": data["balance"],
                "priceUsd": data["price"],
                "valueUsd": value
            })
        
        return {
            "balances": balances,
            "totalValueUsd": total_value
        }
    
    def get_pairs(self) -> List[Dict]:
        \"\"\"Mock trading pairs\"\"\"
        return [
            {"pair": "BTC/USDT", "minAmount": 0.001, "maxAmount": 100},
            {"pair": "ETH/USDT", "minAmount": 0.01, "maxAmount": 1000},
            {"pair": "ADA/USDT", "minAmount": 1, "maxAmount": 100000}
        ]
    
    def get_quote(self, pair: str, amount: float, side: str) -> Dict:
        \"\"\"Mock price quote\"\"\"
        # Simplified mock - in reality this would be more complex
        base_token = pair.split("/")[0]
        if base_token in self.mock_balances:
            price = self.mock_balances[base_token]["price"]
            return {
                "pair": pair,
                "side": side,
                "amount": amount,
                "price": price,
                "total": amount * price,
                "fee": amount * price * 0.002  # 0.2% fee
            }
        return {}
    
    def place_order(self, pair: str, side: str, quantity: float, order_type: str = "market") -> Dict:
        \"\"\"Mock order placement\"\"\"
        return {
            "orderId": f"mock-{int(time.time())}",
            "pair": pair,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "status": "filled",
            "timestamp": datetime.now().isoformat()
        }

def get_nexo_client(use_mock: bool = False) -> NexoProClient:
    \"\"\"Get Nexo client instance\"\"\"
    if use_mock or not settings.NEXO_PUBLIC_KEY:
        return MockNexoClient()
    else:
        return NexoProClient()
"""

with open("nexo_portfolio_manager/app/api/nexo_client.py", "w") as f:
    f.write(nexo_client_content.strip())

# Create app/api/market_data.py
market_data_content = """import yfinance as yf
import requests
from typing import Dict, List
from datetime import datetime, timedelta
import time

class MarketDataProvider:
    def __init__(self):
        self.crypto_symbols = {
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD',
            'ADA': 'ADA-USD',
            'DOT': 'DOT-USD',
            'MATIC': 'MATIC-USD',
            'LINK': 'LINK-USD',
            'UNI': 'UNI-USD',
            'SOL': 'SOL-USD',
            'AVAX': 'AVAX-USD',
            'NEXO': 'NEXO-USD'
        }
        self.stablecoin_price = 1.0
    
    def get_current_prices(self, tokens: List[str]) -> Dict[str, float]:
        \"\"\"Get current prices for list of tokens\"\"\"
        prices = {}
        
        for token in tokens:
            if token in ['USDT', 'USDC']:
                prices[token] = self.stablecoin_price
            elif token in self.crypto_symbols:
                try:
                    ticker = yf.Ticker(self.crypto_symbols[token])
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        prices[token] = float(hist['Close'].iloc[-1])
                    else:
                        # Fallback to a mock price if no data
                        prices[token] = self._get_mock_price(token)
                except Exception as e:
                    print(f"Error fetching price for {token}: {e}")
                    prices[token] = self._get_mock_price(token)
            else:
                prices[token] = self._get_mock_price(token)
        
        return prices
    
    def get_historical_prices(self, token: str, days: int = 30) -> Dict[str, List]:
        \"\"\"Get historical prices for a token\"\"\"
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
        \"\"\"Get mock price for testing\"\"\"
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
    
    def _get_mock_historical_data(self, token: str, days: int) -> Dict[str, List]:
        \"\"\"Generate mock historical data\"\"\"
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
        \"\"\"Calculate total portfolio value\"\"\"
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
"""

with open("nexo_portfolio_manager/app/api/market_data.py", "w") as f:
    f.write(market_data_content.strip())

print("Created Nexo API client and market data files!")