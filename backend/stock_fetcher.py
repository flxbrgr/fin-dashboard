import yfinance as yf
from typing import Dict, Any

class StockFetcher:
    """Handles live price and historical change data for stocks using Yahoo Finance."""
    
    async def fetch_stocks(self, symbols: list) -> Dict[str, Any]:
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    curr_price = hist['Close'].iloc[-1]
                    change_pct = ((curr_price - prev_close) / prev_close) * 100
                    data[symbol] = {
                        "price": curr_price,
                        "change": change_pct,
                        "type": "stock"
                    }
            except Exception as e:
                print(f"Error fetching stock {symbol}: {e}")
        return data
