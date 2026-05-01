
"""CLI entry point for the trading bot"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv


sys.path.insert(0, str(Path(__file__).parent))

from bot.client import BinanceFuturesClient
from bot.orders import OrderManager
from bot.validators import validate_cli_input
from bot.logging_config import setup_logging, get_logger


load_dotenv()


setup_logging()
logger = get_logger(__name__)


def print_order_summary(symbol: str, side: str, order_type: str, 
                        quantity: float, price: float = None):
    """Print order summary before placing"""
    print("\n" + "=" * 60)
    print("ORDER SUMMARY")
    print("=" * 60)
    print(f"Symbol:        {symbol}")
    print(f"Side:          {side}")
    print(f"Type:          {order_type}")
    print(f"Quantity:      {quantity}")
    if price:
        print(f"Price:         {price}")
    print("=" * 60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Place a MARKET BUY order
  python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  
  # Place a LIMIT SELL order
  python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 2000
  
  # Use environment variables for API credentials
  export BINANCE_API_KEY=your_key
  export BINANCE_API_SECRET=your_secret
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
        """
    )
    
    
    parser.add_argument('--api-key', help='Binance API Key', 
                       default=os.getenv('BINANCE_API_KEY'))
    parser.add_argument('--api-secret', help='Binance API Secret',
                       default=os.getenv('BINANCE_API_SECRET'))
    
    
    parser.add_argument('--symbol', required=True, help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--side', required=True, choices=['BUY', 'SELL'], 
                       help='Order side: BUY or SELL')
    parser.add_argument('--type', required=True, choices=['MARKET', 'LIMIT'],
                       help='Order type: MARKET or LIMIT')
    parser.add_argument('--quantity', required=True, type=float,
                       help='Order quantity')
    parser.add_argument('--price', type=float,
                       help='Price for LIMIT orders (required for LIMIT type)')
    
    args = parser.parse_args()
    
    
    if not args.api_key or not args.api_secret:
        logger.error("API credentials missing. Provide via --api-key/--api-secret or environment variables")
        print("\n ERROR: API credentials required")
        print("Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        print("Or use --api-key and --api-secret arguments")
        sys.exit(1)
    
    
    try:
        validated = validate_cli_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=str(args.quantity),
            price=str(args.price) if args.price else None
        )
    except ValueError as e:
        logger.error(f"Input validation failed: {e}")
        print(f"\n Validation Error:\n{e}")
        sys.exit(1)
    
   
    print_order_summary(
        symbol=validated['symbol'],
        side=validated['side'],
        order_type=validated['order_type'],
        quantity=validated['quantity'],
        price=validated.get('price')
    )
    
    
    try:
        logger.info("Initializing Binance Futures client...")
        client = BinanceFuturesClient(args.api_key, args.api_secret)
        order_manager = OrderManager(client)
        
        
        if validated['order_type'] == 'MARKET':
            logger.info(f"Placing MARKET {validated['side']} order...")
            response = order_manager.place_market_order(
                symbol=validated['symbol'],
                side=validated['side'],
                quantity=validated['quantity']
            )
        else:  
            if not validated.get('price'):
                logger.error("Price required for LIMIT order")
                print("\n❌ ERROR: Price is required for LIMIT orders")
                sys.exit(1)
            
            logger.info(f"Placing LIMIT {validated['side']} order...")
            response = order_manager.place_limit_order(
                symbol=validated['symbol'],
                side=validated['side'],
                quantity=validated['quantity'],
                price=validated['price']
            )
        
        
        print("\n ORDER PLACED SUCCESSFULLY!")
        print(order_manager.format_order_response(response))
        
        logger.info(f"Order completed successfully. Order ID: {response.get('orderId')}")
        
    except ConnectionError as e:
        logger.error(f"Network error: {e}")
        print(f"\n Network Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to place order: {e}")
        print(f"\n Order Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()