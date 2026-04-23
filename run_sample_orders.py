import logging
from pathlib import Path

from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.orders import place_order


def configure_case_logger(name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_path = Path(__file__).resolve().parent / filename
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger


def run_case(name: str, filename: str, order: dict) -> None:
    case_logger = configure_case_logger(name, filename)
    case_logger.info("Sample order request: %s", order)
    try:
        response = place_order(**order)
        case_logger.info("Sample order response: %s", response)
        case_logger.info(
            "Sample order success: orderId=%s status=%s executedQty=%s avgPrice=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice"),
        )
        print(f"{name}: success orderId={response.get('orderId')} status={response.get('status')}")
    except Exception:
        case_logger.exception("Sample order failed")
        raise


def main() -> None:
    load_dotenv()
    setup_logging()

    run_case(
        "sample_market_order",
        "market_order.log",
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 0.001,
        },
    )
    run_case(
        "sample_limit_order",
        "limit_order.log",
        {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "order_type": "LIMIT",
            "quantity": 0.001,
            "price": 120000,
        },
    )


if __name__ == "__main__":
    main()
