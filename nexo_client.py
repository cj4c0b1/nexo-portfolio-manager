import requests
import time
import hashlib
import hmac
import json
from typing import Dict, List, Optional
from datetime import datetime

from settings import settings

class NexoProClient:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or settings.NEXO_PUBLIC_KEY
        self.api_secret = api_secret or settings.NEXO_SECRET_KEY
        self.base_url = "https://api.nexo.io"  # Correct base URL for Nexo API
        self.api_version = "v1"  # API version

        if not self.api_key or not self.api_secret:
            raise ValueError("Nexo Pro API credentials not provided")
            
        # Print debug info
        print(f"Initialized NexoProClient with base URL: {self.base_url}")
        print(f"Using API key: {self.api_key[:5]}...{self.api_key[-5:]}" if self.api_key else "No API key provided")

    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC signature for Nexo Pro API"""
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, max_retries: int = 3) -> Dict:
        """
        Make authenticated request to Nexo Pro API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without the /v1/ prefix)
            params: Query parameters
            data: Request body data
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict containing the API response
            
        Raises:
            requests.exceptions.RequestException: If all retry attempts fail
        """
        timestamp = str(int(time.time() * 1000))
        # Ensure endpoint starts with a slash and includes the API version
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        if not endpoint.startswith(f'/{self.api_version}/'):
            endpoint = f'/{self.api_version}{endpoint}'
            
        path = endpoint  # Path for signature should include the API version
        last_exception = None

        # Prepare request data
        if method.upper() == "GET" and params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            path += f"?{query_string}"
            body = ""
        else:
            body = json.dumps(data) if data else ""

        # Generate signature
        signature = self._generate_signature(timestamp, method, path, body)

        headers = {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
            "Content-Type": "application/json",
            "User-Agent": "NexoPortfolioManager/1.0"
        }

        url = f"{self.base_url}{endpoint}"
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                # Add a small delay between retries (exponential backoff)
                if attempt > 0:
                    time.sleep(2 ** attempt)  # 2, 4, 8 seconds, etc.
                
                # Make the request
                if method.upper() == "GET":
                    response = requests.get(
                        url, 
                        headers=headers, 
                        params=params,
                        timeout=10  # 10 seconds timeout
                    )
                elif method.upper() == "POST":
                    response = requests.post(
                        url, 
                        headers=headers, 
                        json=data,
                        timeout=10  # 10 seconds timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check for HTTP errors
                response.raise_for_status()
                return response.json()
                
            except (requests.exceptions.ConnectionError, 
                   requests.exceptions.Timeout) as e:
                last_exception = e
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise requests.exceptions.RequestException(
                        f"Failed to connect to Nexo API after {max_retries} attempts: {str(e)}"
                    ) from e
                continue
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                if e.response.status_code == 401:
                    raise requests.exceptions.RequestException(
                        "Authentication failed. Please check your API credentials."
                    ) from e
                elif e.response.status_code >= 500:
                    print(f"Server error (attempt {attempt + 1}): {str(e)}")
                    if attempt == max_retries - 1:
                        raise requests.exceptions.RequestException(
                            f"Nexo API server error: {e.response.status_code} - {e.response.text}"
                        ) from e
                    continue
                else:
                    raise requests.exceptions.RequestException(
                        f"API request failed with status {e.response.status_code}: {e.response.text}"
                    ) from e
                    
            except Exception as e:
                last_exception = e
                print(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    raise requests.exceptions.RequestException(
                        f"Request failed after {max_retries} attempts: {str(e)}"
                    ) from e
                continue
        
        # This should never be reached due to the raises above, but just in case
        raise requests.exceptions.RequestException(
            f"Failed to complete request: {str(last_exception) if last_exception else 'Unknown error'}"
        )



    def get_account_summary(self) -> Dict:
        """
        Get account balances and summary using the Nexo Pro API.
        
        Returns:
            Dict containing account balances in the format:
            {
                'balances': [
                    {
                        'asset': str,  # e.g. 'BTC'
                        'total': float,  # total balance
                        'available': float,  # available balance
                        'in_orders': float,  # amount in orders
                        'usd_value': float  # USD value of the balance
                    },
                    ...
                ]
            }
        """
        try:
            # Try to get balances using the main API endpoint
            response = self._make_request("GET", "/account/balances")
            
            # Process the response based on its format
            if isinstance(response, list):
                # Format: [{'currency': 'BTC', 'balance': '0.1', ...}, ...]
                return {
                    'balances': [
                        {
                            'asset': item.get('currency', '').upper(),
                            'total': float(item.get('balance', 0)),
                            'available': float(item.get('available', 0)),
                            'in_orders': float(item.get('in_orders', 0)),
                            'usd_value': float(item.get('usd_value', 0))
                        }
                        for item in response
                        if isinstance(item, dict) and 'currency' in item
                    ]
                }
            elif isinstance(response, dict):
                # Format: {'balances': [...]}
                if 'balances' in response:
                    return response
                
                # Format: {'BTC': {'available': 0.1, ...}, ...}
                return {
                    'balances': [
                        {
                            'asset': asset.upper(),
                            'total': float(bal.get('total', 0)),
                            'available': float(bal.get('available', 0)),
                            'in_orders': float(bal.get('in_orders', 0)),
                            'usd_value': float(bal.get('usd_value', 0))
                        }
                        for asset, bal in response.items()
                        if isinstance(bal, dict)
                    ]
                }
                
            # If we get here, the format is unexpected
            print(f"Unexpected API response format: {response}")
            return {'balances': []}
            
        except Exception as e:
            print(f"Error in get_account_summary: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"API response: {e.response.text}")
            return {'balances': []}

    def get_pairs(self) -> List[Dict]:
        """Get available trading pairs"""
        return self._make_request("GET", "/pairs")

    def get_quote(self, pair: str, amount: float, side: str) -> Dict:
        """Get price quote for a trade"""
        params = {
            "pair": pair,
            "amount": amount,
            "side": side
        }
        return self._make_request("GET", "/quote", params=params)

    def place_order(self, pair: str, side: str, quantity: float, order_type: str = "market") -> Dict:
        """Place a trading order"""
        data = {
            "pair": pair,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }
        return self._make_request("POST", "/orders", data=data)

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an existing order"""
        data = {"orderId": order_id}
        return self._make_request("POST", "/orders/cancel", data=data)

    def get_order_history(self, pairs: List[str] = None, limit: int = 100) -> List[Dict]:
        """Get order history"""
        params = {"pageSize": limit}
        if pairs:
            params["pairs"] = ",".join(pairs)

        return self._make_request("GET", "/orders", params=params)

    def get_trades(self, pairs: List[str] = None, limit: int = 100) -> List[Dict]:
        """Get trade history"""
        params = {"pageSize": limit}
        if pairs:
            params["pairs"] = ",".join(pairs)

        return self._make_request("GET", "/trades", params=params)

class MockNexoClient:
    """Mock client for testing and development"""

    def __init__(self):
        self.mock_balances = {
            "BTC": {"balance": 0.1, "price": 45000},
            "ETH": {"balance": 2.5, "price": 3000},
            "ADA": {"balance": 1000, "price": 0.5},
            "USDT": {"balance": 5000, "price": 1.0}
        }

    def get_account_summary(self) -> Dict:
        """Mock account summary"""
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
        """Mock trading pairs"""
        return [
            {"pair": "BTC/USDT", "minAmount": 0.001, "maxAmount": 100},
            {"pair": "ETH/USDT", "minAmount": 0.01, "maxAmount": 1000},
            {"pair": "ADA/USDT", "minAmount": 1, "maxAmount": 100000}
        ]

    def get_quote(self, pair: str, amount: float, side: str) -> Dict:
        """Mock price quote"""
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
        """Mock order placement"""
        return {
            "orderId": f"mock-{int(time.time())}",
            "pair": pair,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "status": "filled",
            "timestamp": datetime.now().isoformat()
        }

def get_nexo_client(use_mock: bool = None):
    """
    Get Nexo client instance.
    
    Args:
        use_mock: If True, use mock client. If None, auto-detect connection issues.
    """
    if use_mock is None:
        # Try to use real client first, fall back to mock if connection fails
        try:
            client = NexoProClient()
            # Test the connection with a simple API call
            client.get_account_summary()
            return client
        except Exception as e:
            print(f"Warning: Could not connect to Nexo API, falling back to mock data: {str(e)}")
            return MockNexoClient()
    elif use_mock:
        return MockNexoClient()
    return NexoProClient()