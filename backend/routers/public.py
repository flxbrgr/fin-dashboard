from fastapi import APIRouter
from ..data_fetcher import DataFetcher

router = APIRouter(tags=["Public Data"])

@router.get("/market-overview")
async def market_overview():
    """Returns current data for major indices and popular stocks. No auth required."""
    import asyncio
    return await asyncio.to_thread(_fetch_market_overview)

def _fetch_market_overview():
    import yfinance as yf
    
    names = {
        "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ",
        "^GDAXI": "DAX", "^FTSE": "FTSE 100",
        "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA",
        "TSLA": "Tesla", "AMZN": "Amazon", "GOOGL": "Alphabet"
    }
    currencies = {"^GDAXI": "EUR", "^FTSE": "GBP"}
    index_syms = ["^GSPC", "^DJI", "^IXIC", "^GDAXI", "^FTSE"]
    stock_syms = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"]
    all_syms = index_syms + stock_syms
    
    result = {"indices": [], "popular": []}
    try:
        # download is synchronous, so we run it in a thread (called via asyncio.to_thread above)
        data = yf.download(all_syms, period="2d", group_by="ticker", threads=True, progress=False)
        for sym in all_syms:
            try:
                closes = data[sym]["Close"].dropna()
                if len(closes) >= 2:
                    prev, curr = float(closes.iloc[-2]), float(closes.iloc[-1])
                    change = ((curr - prev) / prev) * 100
                    entry = {
                        "symbol": sym, "name": names.get(sym, sym),
                        "price": round(curr, 2), "change_pct": round(change, 2),
                        "currency": currencies.get(sym, "USD")
                    }
                    if sym in index_syms:
                        result["indices"].append(entry)
                    else:
                        result["popular"].append(entry)
            except Exception as e:
                print(f"Market parse error {sym}: {e}")
    except Exception as e:
        print(f"Market download error: {e}")
    
    return result

@router.get("/search-public")
def search_public(query: str):
    """Public search endpoint - no auth required."""
    fetcher = DataFetcher()
    return fetcher.search(query)

@router.get("/chart-data")
async def chart_data(symbol: str, period: str = "3mo"):
    """Returns OHLC candlestick data for TradingView charts. No auth required."""
    import asyncio
    return await asyncio.to_thread(_fetch_chart_data, symbol, period)

def _fetch_chart_data(symbol: str, period: str):
    import yfinance as yf
    t = yf.Ticker(symbol)
    hist = t.history(period=period)
    data = []
    for idx, row in hist.iterrows():
        data.append({
            "time": idx.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
        })
    return data
