# Binance Futures Trading Bot (Testnet)

A structured, modular cryptocurrency trading bot that interacts with the Binance Futures Testnet (USDT-M). It places `MARKET`, `LIMIT`, and stop-limit orders, validates user input, handles exceptions robustly, and logs useful request/response details.

## Features
- Bonus features: `STOP_LIMIT` orders, enhanced CLI prompts, and a lightweight web UI.
- Robust validation: strict input validation before any API calls are made.
- Exception handling: gracefully catches network errors, invalid inputs, and API exceptions.
- Logging: detailed file-based logging (`trading_bot.log`).
- Explicit REST endpoint: direct signed REST calls to `https://testnet.binancefuture.com`.

## Project Structure
- bot/
-  __init__.py
-  client.py
-  orders.py
-  validators.py
-  logging_config.py
- cli.py
- README.md
- requirements.txt


## Setup Steps

1. No extra dependencies are required. The bot uses only the Python standard library.

2. Configure API keys.
   ```bash
   cp .env.example .env
   ```
   Open `.env` and insert your Binance Futures Testnet API key and secret.

3. Check API permissions.
   The key must be created on Binance Futures Testnet, not the live exchange. Make sure Futures trading permissions are enabled and any IP restrictions allow your machine.

## How to Run Examples

### Interactive CLI
```bash
python cli.py
```

### Market Order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Limit Order
```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.05 --price 2500.50
```

### Stop-Limit Order
```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.002 --price 77900 --stop-price 78000
```

### Lightweight UI
```bash
python ui.py
```
Open `http://127.0.0.1:8000` in a browser. The UI uses the same validation and order placement code as the CLI.

### Generate Required Sample Logs
```bash
python run_sample_orders_rest.py
```

This writes:
- `market_order.log`
- `limit_order.log`

With valid Futures Testnet credentials, these logs include `orderId`, `status`, `executedQty`, and `avgPrice` when Binance returns it. If Binance rejects the credentials or permissions, the logs capture the request summary and API error response for troubleshooting.

## Assumptions
- Futures Testnet only. The bot does not execute live trades.
- Base URL is `https://testnet.binancefuture.com`.
- The app signs direct REST requests to `/fapi/v1/order`.
- `STOP_LIMIT` uses Binance Futures Algo Order API (`/fapi/v1/algoOrder`) with `algoType=CONDITIONAL`, order type `STOP`, `price`, `triggerPrice`, and `GTC`.
- Limit orders use a default `timeInForce` of `GTC`.
- Environment variables `BINANCE_API_KEY` and `BINANCE_API_SECRET` must be present in `.env` or the shell environment.
