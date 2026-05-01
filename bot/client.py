"""Binance Futures Testnet client wrapper"""

import time
import hashlib
import hmac
import requests
from urllib.parse import urlencode
from typing import Dict, Optional, Any
from decimal import Decimal
from bot.logging_config import get_logger

logger = get_logger(__name__)


class BinanceFuturesClient:
    """Client for interacting with Binance Futures Testnet API"""
    
    BASE_URL = "https://testnet.binancefuture.com"
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize the Binance Futures client
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
        
       
        self._test_connectivity()
    
    def _test_connectivity(self):
        """Test connection to Binance API"""
        try:
            response = self.session.get(f"{self.BASE_URL}/fapi/v1/ping", timeout=10)
            if response.status_code == 200:
                logger.info("Successfully connected to Binance Futures Testnet")
            else:
                logger.warning(f"Connectivity test returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Binance Futures Testnet: {e}")
            raise ConnectionError(f"Cannot connect to Binance API: {e}")
    
    def _generate_signature(self, params: Dict) -> str:
        """
        Generate HMAC SHA256 signature for API request
        
        Args:
            params: Request parameters
        
        Returns:
            str: Signature string
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                 signed: bool = False) -> Dict[str, Any]:
        """
        Make API request to Binance
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request requires signature
        
        Returns:
            Dict: Response JSON
        
        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            signature = self._generate_signature(params)
            params['signature'] = signature
        
        logger.debug(f"Request: {method} {endpoint} | Params: {params}")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.debug(f"Response Status: {response.status_code}")
            logger.debug(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json()
                error_msg = f"API Error {response.status_code}: {error_data.get('msg', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            raise Exception("Request timeout - API did not respond")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_account_info(self) -> Dict:
        """
        Get futures account information
        
        Returns:
            Dict: Account information
        """
        return self._request('GET', '/fapi/v2/account', signed=True)
    
    def get_symbol_price(self, symbol: str) -> float:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading pair
        
        Returns:
            float: Current price
        """
        try:
            response = self._request('GET', '/fapi/v1/ticker/price', 
                                    params={'symbol': symbol})
            return float(response['price'])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: Optional[float] = None) -> Dict:
        """
        Place an order on Binance Futures
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            order_type: MARKET or LIMIT
            quantity: Order quantity
            price: Price for LIMIT orders
        
        Returns:
            Dict: Order response
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': float(quantity)
        }
        
        if order_type == 'LIMIT':
            if price is None:
                raise ValueError("Price is required for LIMIT orders")
            params['price'] = str(price)
            params['timeInForce'] = 'GTC'  # Good Till Cancel
        
        logger.info(f"Placing {order_type} {side} order for {quantity} {symbol}")
        if price:
            logger.info(f"Limit price: {price}")
        
        response = self._request('POST', '/fapi/v1/order', params=params, signed=True)
        logger.info(f"Order placed successfully. Order ID: {response.get('orderId')}")
        
        return response
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict:
        """
        Get order status
        
        Args:
            symbol: Trading pair
            order_id: Order ID
        
        Returns:
            Dict: Order information
        """
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('GET', '/fapi/v1/order', params=params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        Cancel an order
        
        Args:
            symbol: Trading pair
            order_id: Order ID
        
        Returns:
            Dict: Cancellation response
        """
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        logger.info(f"Cancelling order {order_id} for {symbol}")
        return self._request('DELETE', '/fapi/v1/order', params=params, signed=True)