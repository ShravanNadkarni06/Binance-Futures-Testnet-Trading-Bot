def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValueError("Symbol cannot be empty")
    symbol = symbol.upper().strip()
    if not symbol.isalnum():
        raise ValueError("Symbol must contain only letters and numbers, e.g. BTCUSDT.")
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValueError("Side cannot be empty")
    side = side.upper().strip()
    if side not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid side '{side}'. Must be BUY or SELL.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValueError("Order type cannot be empty")
    order_type = order_type.upper().strip().replace("-", "_")
    if order_type not in ["MARKET", "LIMIT", "STOP_LIMIT"]:
        raise ValueError("Invalid order type. Must be MARKET, LIMIT, or STOP_LIMIT.")
    return order_type


def validate_quantity(quantity: float) -> float:
    if quantity is None:
        raise ValueError("Quantity is required.")
    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than 0. Got {quantity}.")
    return quantity


def validate_price(price: float, order_type: str) -> float:
    if order_type in ["LIMIT", "STOP_LIMIT"] and (price is None or price <= 0):
        raise ValueError(f"Price must be greater than 0 for {order_type} orders.")
    return price


def validate_stop_price(stop_price: float, order_type: str) -> float:
    if order_type == "STOP_LIMIT" and (stop_price is None or stop_price <= 0):
        raise ValueError("Stop price must be greater than 0 for STOP_LIMIT orders.")
    return stop_price
