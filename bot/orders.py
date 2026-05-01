"""Order placement logic"""

from typing import Dict, Optional
from bot.client import BinanceFuturesClient
from bot.logging_config import get_logger

logger = get_logger(__name__)


class OrderManager:
    """Manages order placement and execution"""
    
    def __init__(self, client: BinanceFuturesClient):
        """
        Initialize OrderManager
        
        Args:
            client: Binance Futures client instance
        """
        self.client = client
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        Place a market order
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
        
        Returns:
            Dict: Order response
        """
        try:
            
            current_price = self.client.get_symbol_price(symbol)
            logger.info(f"Current {symbol} price: {current_price}")
            
            # Place market order
            order = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )
            
            
            if order.get('orderId'):
                status = self.client.get_order_status(symbol, order['orderId'])
                return status
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price
        
        Returns:
            Dict: Order response
        """
        try:
            current_price = self.client.get_symbol_price(symbol)
            logger.info(f"Current {symbol} price: {current_price}")
            logger.info(f"Limit price: {price}")
            
            if side == 'BUY' and price > current_price:
                logger.warning(f"Buy limit price ({price}) is above current market price ({current_price})")
            elif side == 'SELL' and price < current_price:
                logger.warning(f"Sell limit price ({price}) is below current market price ({current_price})")
            
            order = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise
    
    def format_order_response(self, order: Dict) -> str:
        """
        Format order response for display
        
        Args:
            order: Order response dictionary
        
        Returns:
            str: Formatted response string
        """
        output = []
        output.append("=" * 60)
        output.append("ORDER RESPONSE")
        output.append("=" * 60)
        output.append(f"Order ID:      {order.get('orderId', 'N/A')}")
        output.append(f"Symbol:        {order.get('symbol', 'N/A')}")
        output.append(f"Side:          {order.get('side', 'N/A')}")
        output.append(f"Type:          {order.get('type', 'N/A')}")
        output.append(f"Status:        {order.get('status', 'N/A')}")
        output.append(f"Quantity:      {order.get('origQty', 'N/A')}")
        output.append(f"Executed Qty:  {order.get('executedQty', 'N/A')}")
        
        if order.get('price') and float(order.get('price', 0)) > 0:
            output.append(f"Limit Price:   {order.get('price', 'N/A')}")
        
        if order.get('avgPrice') and float(order.get('avgPrice', 0)) > 0:
            output.append(f"Avg Price:     {order.get('avgPrice', 'N/A')}")
        
        output.append(f"Time:          {order.get('updateTime', 'N/A')}")
        output.append("=" * 60)
        
        return "\n".join(output)