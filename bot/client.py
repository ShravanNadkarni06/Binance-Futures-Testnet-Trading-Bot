import hashlib
import hmac
import json
import logging
import os
import time
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .exceptions import BinanceAPIError, BinanceNetworkError

logger = logging.getLogger(__name__)

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceFuturesClient:
    """Small REST client for Binance USDT-M Futures Testnet."""

    def __init__(self, base_url: str = FUTURES_TESTNET_BASE_URL):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.base_url = base_url.rstrip("/")

        if not self.api_key or not self.api_secret:
            logger.error("API keys missing from environment variables")
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET environment variables are required.")

        logger.info("Initialized Binance Futures Testnet REST client at %s", self.base_url)

    def get_server_time(self) -> int:
        payload = self._request("GET", "/fapi/v1/time")
        return int(payload["serverTime"])

    def create_order(self, **params) -> dict:
        return self._signed_request("POST", "/fapi/v1/order", params)

    def create_algo_order(self, **params) -> dict:
        return self._signed_request("POST", "/fapi/v1/algoOrder", params)

    def _signed_request(self, method: str, path: str, params: dict) -> dict:
        signed_params = dict(params)
        signed_params["timestamp"] = self.get_server_time()
        signed_params["recvWindow"] = 10000
        query = urlencode(signed_params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return self._request(method, path, data=f"{query}&signature={signature}")

    def _request(self, method: str, path: str, data: Optional[str] = None) -> dict:
        url = f"{self.base_url}{path}"
        started = time.monotonic()
        body = data.encode("utf-8") if data is not None else None
        headers = {"X-MBX-APIKEY": self.api_key}
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = Request(url, data=body, method=method, headers=headers)

        try:
            with urlopen(request, timeout=30) as response:
                payload = response.read().decode("utf-8")
                elapsed_ms = round((time.monotonic() - started) * 1000)
                logger.info("Binance %s %s -> %s in %sms", method, path, response.status, elapsed_ms)
                return json.loads(payload)
        except HTTPError as exc:
            payload = exc.read().decode("utf-8")
            elapsed_ms = round((time.monotonic() - started) * 1000)
            logger.info("Binance %s %s -> %s in %sms", method, path, exc.code, elapsed_ms)
            raise BinanceAPIError(exc.code, payload) from exc
        except URLError as exc:
            logger.exception("Network failure calling Binance %s %s", method, path)
            raise BinanceNetworkError(str(exc)) from exc
