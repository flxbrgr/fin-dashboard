import yfinance as yf
import asyncio
from typing import Dict, Any, List

class StockScanner:
    """Handles fundamental filtering and scanning based on yfinance data."""
    
    async def filter_stocks(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filters stocks based on dynamic fundamental criteria."""
        return await asyncio.to_thread(self._filter_stocks_sync, criteria)

    def _filter_stocks_sync(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        sector = criteria.get("sector")
        pe_max = criteria.get("trailing_pe_max")
        mc_min = criteria.get("market_cap_min")
        mc_max = criteria.get("market_cap_max")
        dy_min = criteria.get("dividend_yield_min")
        pb_max = criteria.get("price_to_book_max")
        pm_min = criteria.get("profit_margins_min")
        
        universe = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "INTC", "AMD",
            "JPM", "V", "MA", "UNH", "HD", "PG", "DIS", "PYPL", "NFLX", "ADBE"
        ]
        
        for symbol in universe:
            try:
                t = yf.Ticker(symbol)
                info = t.info
                match = True
                
                if sector and info.get("sector") != sector: match = False
                if pe_max and (info.get("trailingPE") or 9999) > pe_max: match = False
                if mc_min and (info.get("marketCap") or 0) < mc_min: match = False
                if mc_max and (info.get("marketCap") or float('inf')) > mc_max: match = False
                if dy_min and (info.get("dividendYield") or 0) < dy_min: match = False
                if pb_max and (info.get("priceToBook") or 9999) > pb_max: match = False
                if pm_min and (info.get("profitMargins") or 0) < pm_min: match = False
                
                if match:
                    results.append({
                        "symbol": symbol,
                        "name": info.get("longName"),
                        "sector": info.get("sector"),
                        "price": info.get("currentPrice"),
                        "market_cap": info.get("marketCap"),
                        "pe": info.get("trailingPE"),
                        "div_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
                    })
            except Exception as e:
                print(f"Filter error {symbol}: {e}")
        return results
