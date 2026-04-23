import html
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from bot.exceptions import BinanceAPIError, BinanceNetworkError
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

ROOT = Path(__file__).resolve().parent
logger = logging.getLogger("UI")


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def render_page(message: str = "", is_error: bool = False) -> bytes:
    message_html = ""
    if message:
        css_class = "result error" if is_error else "result success"
        title = "Request Failed" if is_error else "Order Submitted"
        message_html = f'<section class="{css_class}"><h2>{title}</h2><pre>{html.escape(message)}</pre></section>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Binance Futures Testnet Bot</title>
  <style>
    :root {{
      --bg: #0b1220;
      --panel: #111827;
      --panel-2: #162033;
      --line: #263449;
      --text: #e5edf7;
      --muted: #91a4bd;
      --accent: #f0b90b;
      --accent-2: #2dd4bf;
      --danger: #fb7185;
      --success: #34d399;
      --shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      background:
        radial-gradient(circle at 15% 15%, rgba(45, 212, 191, 0.16), transparent 28%),
        radial-gradient(circle at 85% 5%, rgba(240, 185, 11, 0.14), transparent 26%),
        linear-gradient(135deg, #080d18 0%, var(--bg) 48%, #111827 100%);
      color: var(--text);
    }}
    main {{
      width: min(1080px, calc(100% - 32px));
      margin: 34px auto;
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 22px;
      align-items: start;
    }}
    .hero, .trade-card {{
      background: linear-gradient(180deg, rgba(22, 32, 51, 0.96), rgba(17, 24, 39, 0.98));
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }}
    .hero {{
      padding: 28px;
      min-height: 420px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .eyebrow {{
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 14px 0 12px;
      font-size: 36px;
      line-height: 1.05;
    }}
    .subcopy {{
      margin: 0;
      color: var(--muted);
      line-height: 1.6;
      max-width: 44ch;
    }}
    .stats {{
      display: grid;
      gap: 12px;
      margin-top: 28px;
    }}
    .stat {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 13px 14px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.07);
    }}
    .stat span:first-child {{ color: var(--muted); }}
    .stat span:last-child {{ font-weight: 800; color: var(--text); }}
    .trade-card {{ padding: 26px; }}
    .card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 22px;
    }}
    h2 {{ margin: 0; font-size: 20px; }}
    .badge {{
      padding: 7px 10px;
      color: #08111f;
      background: var(--accent);
      font-size: 12px;
      font-weight: 800;
    }}
    form {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    label {{
      display: grid;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }}
    label.full {{ grid-column: 1 / -1; }}
    input, select {{
      width: 100%;
      height: 44px;
      padding: 0 12px;
      color: var(--text);
      background: #0c1424;
      border: 1px solid #2c3b52;
      outline: none;
      font: inherit;
    }}
    input:focus, select:focus {{
      border-color: var(--accent-2);
      box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.14);
    }}
    input::placeholder {{ color: #5d7088; }}
    select option {{ background: #0c1424; color: var(--text); }}
    button {{
      grid-column: 1 / -1;
      height: 48px;
      margin-top: 4px;
      border: 0;
      color: #09111f;
      background: linear-gradient(90deg, var(--accent), #ffd166);
      font: inherit;
      font-weight: 900;
      cursor: pointer;
      box-shadow: 0 12px 28px rgba(240, 185, 11, 0.18);
    }}
    button:hover {{ filter: brightness(1.04); }}
    .result {{
      grid-column: 1 / -1;
      margin-top: 18px;
      padding: 16px;
      border-left: 4px solid;
      background: rgba(255, 255, 255, 0.045);
    }}
    .result h2 {{ margin-bottom: 10px; font-size: 16px; }}
    .success {{ border-color: var(--success); }}
    .success h2 {{ color: var(--success); }}
    .error {{ border-color: var(--danger); }}
    .error h2 {{ color: var(--danger); }}
    pre {{
      white-space: pre-wrap;
      margin: 0;
      color: var(--text);
      line-height: 1.55;
      font-family: "Cascadia Mono", Consolas, monospace;
      font-size: 13px;
    }}
    @media (max-width: 820px) {{
      main {{ grid-template-columns: 1fr; margin: 16px auto; }}
      .hero {{ min-height: auto; }}
      h1 {{ font-size: 30px; }}
      form {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <div class="eyebrow">USDT-M Futures Testnet</div>
        <h1>Trading Bot Console</h1>
        <p class="subcopy">Place Binance Futures Testnet orders with validation, signed REST requests, and clean execution logs.</p>
      </div>
      <div class="stats">
        <div class="stat"><span>Endpoint</span><span>Testnet</span></div>
        <div class="stat"><span>Symbols</span><span>USDT-M</span></div>
        <div class="stat"><span>Logging</span><span>Enabled</span></div>
      </div>
    </section>
    <section class="trade-card">
      <div class="card-header">
        <h2>New Order</h2>
        <span class="badge">Sandbox</span>
      </div>
      <form method="post">
        <label>Symbol <input name="symbol" value="BTCUSDT" required></label>
        <label>Side
          <select name="side">
            <option>BUY</option>
            <option>SELL</option>
          </select>
        </label>
        <label>Order Type
          <select name="order_type">
            <option>MARKET</option>
            <option>LIMIT</option>
            <option>STOP_LIMIT</option>
          </select>
        </label>
        <label>Quantity <input name="quantity" type="number" step="any" min="0" value="0.001" required></label>
        <label>Price <input name="price" type="number" step="any" min="0" placeholder="LIMIT / STOP_LIMIT"></label>
        <label>Stop Price <input name="stop_price" type="number" step="any" min="0" placeholder="STOP_LIMIT only"></label>
        <button type="submit">Place Testnet Order</button>
      </form>
      {message_html}
    </section>
  </main>
</body>
</html>""".encode("utf-8")


class TradingBotHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.respond(render_page())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))

        try:
            symbol = validate_symbol(form.get("symbol", [""])[0])
            side = validate_side(form.get("side", [""])[0])
            order_type = validate_order_type(form.get("order_type", [""])[0])
            quantity = validate_quantity(float(form.get("quantity", ["0"])[0]))
            raw_price = form.get("price", [""])[0]
            raw_stop = form.get("stop_price", [""])[0]
            price = validate_price(float(raw_price) if raw_price else None, order_type)
            stop_price = validate_stop_price(float(raw_stop) if raw_stop else None, order_type)

            logger.info(
                "UI order request summary: symbol=%s side=%s type=%s quantity=%s price=%s stopPrice=%s",
                symbol,
                side,
                order_type,
                quantity,
                price,
                stop_price,
            )
            response = place_order(symbol, side, order_type, quantity, price, stop_price)
            order_id = response.get("orderId") or response.get("algoId") or "N/A"
            status = response.get("status") or response.get("algoStatus") or "N/A"
            message = (
                "Order Success\n"
                f"order/algo id: {order_id}\n"
                f"status: {status}\n"
                f"executedQty: {response.get('executedQty', 'N/A')}\n"
                f"avgPrice: {response.get('avgPrice', 'N/A')}"
            )
            self.respond(render_page(message))
        except ValueError as exc:
            self.respond(render_page(f"Input Error: {exc}", True))
        except BinanceAPIError as exc:
            self.respond(render_page(f"API Error: {exc.payload}", True))
        except BinanceNetworkError as exc:
            self.respond(render_page(f"Network Error: {exc}", True))

    def respond(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    load_env()
    setup_logging()
    server = HTTPServer(("127.0.0.1", 8000), TradingBotHandler)
    print("Lightweight UI running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
