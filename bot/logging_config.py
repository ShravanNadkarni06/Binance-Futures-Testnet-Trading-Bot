import logging
from pathlib import Path


def setup_logging():
    """Configure logging for the bot."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file = Path(__file__).resolve().parents[1] / "trading_bot.log"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.FileHandler(log_file, encoding="utf-8")],
        force=True,
    )
