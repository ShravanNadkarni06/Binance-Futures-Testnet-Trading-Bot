class BinanceClientError(Exception):
    """Base exception for Binance client failures."""


class BinanceAPIError(BinanceClientError):
    """Raised when Binance returns an API error response."""

    def __init__(self, status_code: int, payload: str):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Binance API error {status_code}: {payload}")


class BinanceNetworkError(BinanceClientError):
    """Raised when the client cannot reach Binance."""
