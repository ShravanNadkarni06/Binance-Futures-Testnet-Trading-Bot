import logging

from .client import BinanceFuturesClient
from .exceptions import BinanceAPIError, BinanceNetworkError

logger = logging.getLogger(__name__)


def place_order(symbol: str, side: str, order_type: str, quantity: float, price: float = None, stop_price: float = None):
    """Place a Futures Testnet order."""
    try:
        client = BinanceFuturesClient()

        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
        }

        if order_type == "MARKET":
            params["type"] = "MARKET"
            logger.info("Sending futures order request: %s", params)
            response = client.create_order(**params)

        elif order_type == "LIMIT":
            params["type"] = "LIMIT"
            params["timeInForce"] = "GTC"
            params["price"] = price
            logger.info("Sending futures order request: %s", params)
            response = client.create_order(**params)

        elif order_type == "STOP_LIMIT":
            params["type"] = "STOP"
            params["algoType"] = "CONDITIONAL"
            params["timeInForce"] = "GTC"
            params["price"] = price
            params["triggerPrice"] = stop_price
            params["workingType"] = "CONTRACT_PRICE"
            params["priceProtect"] = "FALSE"
            logger.info("Sending futures algo order request: %s", params)
            response = client.create_algo_order(**params)

        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        logger.info("Futures order response: %s", response)
        return response

    except BinanceAPIError as e:
        logger.exception("Binance API exception: %s", e)
        raise
    except BinanceNetworkError:
        logger.exception("Binance network exception")
        raise
    except Exception:
        logger.exception("Unexpected error during order placement")
        raise
