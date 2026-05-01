"""Input validation utilities"""

import re
from decimal import Decimal, InvalidOperation


def validate_symbol(symbol: str) -> bool:
    """
    Validate trading symbol format
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
    
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[A-Z]{2,10}USDT$'
    return bool(re.match(pattern, symbol))


def validate_side(side: str) -> bool:
    """
    Validate order side
    
    Args:
        side: BUY or SELL
    
    Returns:
        bool: True if valid, False otherwise
    """
    return side.upper() in ['BUY', 'SELL']


def validate_order_type(order_type: str) -> bool:
    """
    Validate order type
    
    Args:
        order_type: MARKET or LIMIT
    
    Returns:
        bool: True if valid, False otherwise
    """
    return order_type.upper() in ['MARKET', 'LIMIT']


def validate_quantity(quantity: str) -> tuple[bool, float | None]:
    """
    Validate and parse quantity
    
    Args:
        quantity: Quantity as string
    
    Returns:
        tuple: (is_valid, parsed_quantity)
    """
    try:
        qty = float(quantity)
        if qty <= 0:
            return False, None
        if qty > 1000:  
            return False, None
        return True, qty
    except (ValueError, TypeError):
        return False, None


def validate_price(price: str, order_type: str) -> tuple[bool, float | None]:
    """
    Validate and parse price
    
    Args:
        price: Price as string
        order_type: Order type (required for LIMIT orders)
    
    Returns:
        tuple: (is_valid, parsed_price)
    """
    if order_type.upper() == 'MARKET':
        return True, None
    
    try:
        p = float(price)
        if p <= 0:
            return False, None
        if p > 1000000:  # Reasonable limit for testnet
            return False, None
        return True, p
    except (ValueError, TypeError):
        return False, None


def validate_cli_input(symbol: str, side: str, order_type: str, 
                       quantity: str, price: str = None) -> dict:
    """
    Validate all CLI inputs
    
    Args:
        symbol: Trading symbol
        side: BUY/SELL
        order_type: MARKET/LIMIT
        quantity: Order quantity
        price: Price (required for LIMIT)
    
    Returns:
        dict: Validation result with status and message
    
    Raises:
        ValueError: If validation fails
    """
    errors = []
    
    
    if not validate_symbol(symbol):
        errors.append(f"Invalid symbol '{symbol}'. Must be like 'BTCUSDT'")
    
   
    if not validate_side(side):
        errors.append(f"Invalid side '{side}'. Must be BUY or SELL")
    
   
    if not validate_order_type(order_type):
        errors.append(f"Invalid order type '{order_type}'. Must be MARKET or LIMIT")
    
   
    is_valid_qty, qty = validate_quantity(quantity)
    if not is_valid_qty:
        errors.append(f"Invalid quantity '{quantity}'. Must be positive number > 0")
    
    
    if order_type.upper() == 'LIMIT':
        if price is None:
            errors.append("Price is required for LIMIT orders")
        else:
            is_valid_price, _ = validate_price(price, order_type)
            if not is_valid_price:
                errors.append(f"Invalid price '{price}'. Must be positive number > 0")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return {
        'valid': True,
        'symbol': symbol.upper(),
        'side': side.upper(),
        'order_type': order_type.upper(),
        'quantity': float(quantity),
        'price': float(price) if price and order_type.upper() == 'LIMIT' else None
    }