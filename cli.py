import argparse
import sys
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        env_path = Path(__file__).resolve().parent / ".env"
        if not env_path.exists():
            return
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            import os
            os.environ.setdefault(key.strip(), value.strip())

from bot.logging_config import setup_logging
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price
)
from bot.orders import place_order
from bot.exceptions import BinanceAPIError, BinanceNetworkError

try:
    from rich.console import Console
    from rich.prompt import Prompt, FloatPrompt
    from rich.panel import Panel
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

def print_message(msg, style=""):
    if HAS_RICH:
        console.print(msg, style=style)
    else:
        print(msg)

def plain_prompt(label):
    return input(f"{label}: ").strip()

def interactive_prompt():
    """Interactive prompt for order details"""
    print_message("\n--- Binance Futures Interactive Menu ---", "bold cyan")
    
    while True:
        try:
            symbol = Prompt.ask("Enter Symbol (e.g., BTCUSDT)") if HAS_RICH else plain_prompt("Enter Symbol (e.g., BTCUSDT)")
            symbol = validate_symbol(symbol)
            break
        except ValueError as e:
            print_message(f"Error: {e}", "bold red")

    while True:
        try:
            side = Prompt.ask("Enter Side", choices=["BUY", "SELL"], default="BUY") if HAS_RICH else plain_prompt("Enter Side (BUY/SELL)") or "BUY"
            side = validate_side(side)
            break
        except ValueError as e:
            print_message(f"Error: {e}", "bold red")

    while True:
        try:
            order_type = Prompt.ask("Enter Order Type", choices=["MARKET", "LIMIT", "STOP_LIMIT"], default="MARKET") if HAS_RICH else plain_prompt("Enter Order Type (MARKET/LIMIT/STOP_LIMIT)") or "MARKET"
            order_type = validate_order_type(order_type)
            break
        except ValueError as e:
            print_message(f"Error: {e}", "bold red")

    while True:
        try:
            quantity = FloatPrompt.ask("Enter Quantity") if HAS_RICH else float(plain_prompt("Enter Quantity"))
            quantity = validate_quantity(quantity)
            break
        except ValueError as e:
            print_message(f"Error: {e}", "bold red")

    price = None
    if order_type in ["LIMIT", "STOP_LIMIT"]:
        while True:
            try:
                price = FloatPrompt.ask("Enter Price") if HAS_RICH else float(plain_prompt("Enter Price"))
                price = validate_price(price, order_type)
                break
            except ValueError as e:
                print_message(f"Error: {e}", "bold red")

    stop_price = None
    if order_type == "STOP_LIMIT":
        while True:
            try:
                stop_price = FloatPrompt.ask("Enter Stop Price") if HAS_RICH else float(plain_prompt("Enter Stop Price"))
                stop_price = validate_stop_price(stop_price, order_type)
                break
            except ValueError as e:
                print_message(f"Error: {e}", "bold red")

    return symbol, side, order_type, quantity, price, stop_price

def main():
    """CLI entry point"""
    load_dotenv()
    setup_logging()
    logger = logging.getLogger("CLI")
    
    parser = argparse.ArgumentParser(description="Binance Futures Trading Bot CLI (Testnet)")
    parser.add_argument("--symbol", help="Trading symbol (e.g., BTCUSDT)")
    parser.add_argument("--side", choices=['BUY', 'SELL', 'buy', 'sell'], help="Order side: BUY or SELL")
    parser.add_argument("--type", choices=['MARKET', 'LIMIT', 'STOP_LIMIT', 'market', 'limit', 'stop_limit', 'stop-limit'], help="Order type: MARKET, LIMIT, or STOP_LIMIT")
    parser.add_argument("--quantity", type=float, help="Order quantity")
    parser.add_argument("--price", type=float, help="Order price (Required for LIMIT and STOP_LIMIT orders)")
    parser.add_argument("--stop-price", type=float, help="Trigger price (Required for STOP_LIMIT orders)")
    
    args = parser.parse_args()
    
    # If no arguments provided, use interactive menu (Enhanced UX)
    if args.symbol is None and args.side is None and args.type is None and args.quantity is None:
        symbol, side, order_type, quantity, price, stop_price = interactive_prompt()
    else:
        # Check if all required args are present
        if args.symbol is None or args.side is None or args.type is None or args.quantity is None:
            print("Error: Missing required arguments. Please provide --symbol, --side, --type, and --quantity.")
            sys.exit(1)
            
        try:
            symbol = validate_symbol(args.symbol)
            side = validate_side(args.side)
            order_type = validate_order_type(args.type)
            quantity = validate_quantity(args.quantity)
            price = validate_price(args.price, order_type)
            stop_price = validate_stop_price(args.stop_price, order_type)
        except ValueError as ve:
            logger.error(f"Validation Error: {ve}")
            print(f"Input Error: {ve}")
            sys.exit(1)
            
    if HAS_RICH:
        summary = f"Symbol: [bold yellow]{symbol}[/]\nSide: [bold {'green' if side=='BUY' else 'red'}]{side}[/]\nType: [bold cyan]{order_type}[/]\nQuantity: [bold]{quantity}[/]"
        if order_type in ['LIMIT', 'STOP_LIMIT']:
            summary += f"\nPrice: [bold]{price}[/]"
        if order_type == 'STOP_LIMIT':
            summary += f"\nStop Price: [bold]{stop_price}[/]"
        console.print(Panel(summary, title="Order Request Summary", expand=False))
    else:
        print("\n--- Order Request Summary ---")
        print(f"Symbol:   {symbol}")
        print(f"Side:     {side}")
        print(f"Type:     {order_type}")
        print(f"Quantity: {quantity}")
        if order_type in ['LIMIT', 'STOP_LIMIT']:
            print(f"Price:    {price}")
        if order_type == 'STOP_LIMIT':
            print(f"Stop:     {stop_price}")
        print("-----------------------------\n")
        
    print_message("Placing order...", "bold yellow")
    try:
        response = place_order(symbol, side, order_type, quantity, price, stop_price)
        
        status_color = "green" if response.get('status') in ['FILLED', 'NEW'] else "yellow"
        order_id = response.get('orderId') or response.get('algoId') or 'N/A'
        status = response.get('status') or response.get('algoStatus') or 'N/A'
        executed_qty = response.get('executedQty', 'N/A')
        avg_price = response.get('avgPrice', 'N/A')
        
        if HAS_RICH:
            res_text = f"Order/Algo ID: [bold]{order_id}[/]\n"
            res_text += f"Status:        [bold {status_color}]{status}[/]\n"
            res_text += f"Executed Qty:  {executed_qty}\n"
            res_text += f"Average Price: {avg_price}"
        else:
            res_text = f"Order/Algo ID: {order_id}\n"
            res_text += f"Status:        {status}\n"
            res_text += f"Executed Qty:  {executed_qty}\n"
            res_text += f"Average Price: {avg_price}"
            
        if HAS_RICH:
            console.print(Panel(res_text, title="Order Success", border_style="green", expand=False))
        else:
            print("\n=== Order Success ===")
            print(res_text)
            print("=====================\n")
            
    except BinanceAPIError as e:
        logger.exception("API error while placing order")
        print_message(f"API Error: Failed to place order. {e.payload}", "bold red")
        print_message("Check trading_bot.log for details.")
        sys.exit(1)
    except BinanceNetworkError as e:
        logger.exception("Network error while placing order")
        print_message(f"Network Error: Could not connect to Binance API. {e}", "bold red")
        print_message("Check trading_bot.log for details.")
        sys.exit(1)
    except ValueError as e:
        logger.exception("Configuration error while placing order")
        print_message(f"Configuration Error: {e}", "bold red")
        print_message("Check trading_bot.log for details.")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error while placing order")
        print_message(f"Unexpected Error: {e}", "bold red")
        print_message("Check trading_bot.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
