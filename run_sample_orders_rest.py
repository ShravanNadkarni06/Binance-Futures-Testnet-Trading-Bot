import hashlib
import hmac
import json
import logging
import time
from typing import Optional
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://testnet.binancefuture.com"
ROOT = Path(__file__).resolve().parent


def load_env() -> dict:
    env_path = ROOT / ".env"
    values = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def configure_logger(name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(ROOT / filename, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger


def public_get(path: str, params: Optional[dict] = None) -> dict:
    query = f"?{urlencode(params or {})}" if params else ""
    with urlopen(f"{BASE_URL}{path}{query}", timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def signed_post(path: str, params: dict, api_key: str, api_secret: str) -> dict:
    params = {
        **params,
        "timestamp": int(time.time() * 1000),
        "recvWindow": 10000,
    }
    query = urlencode(params)
    signature = hmac.new(api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    body = f"{query}&signature={signature}".encode("utf-8")
    request = Request(
        f"{BASE_URL}{path}",
        data=body,
        method="POST",
        headers={
            "X-MBX-APIKEY": api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        payload = exc.read().decode("utf-8")
        raise RuntimeError(f"Binance API error {exc.code}: {payload}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc


def log_order_case(name: str, filename: str, params: dict, api_key: str, api_secret: str) -> None:
    logger = configure_logger(name, filename)
    logger.info("Order request: %s", params)
    try:
        response = signed_post("/fapi/v1/order", params, api_key, api_secret)
        logger.info("Order response: %s", response)
        logger.info(
            "Order success: orderId=%s status=%s executedQty=%s avgPrice=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice"),
        )
        print(f"{name}: success orderId={response.get('orderId')} status={response.get('status')}")
    except Exception:
        logger.exception("Order failed")
        print(f"{name}: failed; see {filename}")


def main() -> None:
    env = load_env()
    api_key = env["BINANCE_API_KEY"]
    api_secret = env["BINANCE_API_SECRET"]

    ticker = public_get("/fapi/v1/ticker/price", {"symbol": "BTCUSDT"})
    btc_price = float(ticker["price"])
    limit_price = round(btc_price * 1.05, 1)

    log_order_case(
        "market_order",
        "market_order.log",
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": "0.001",
        },
        api_key,
        api_secret,
    )
    log_order_case(
        "limit_order",
        "limit_order.log",
        {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "quantity": "0.001",
            "price": str(limit_price),
            "timeInForce": "GTC",
        },
        api_key,
        api_secret,
    )


if __name__ == "__main__":
    main()
