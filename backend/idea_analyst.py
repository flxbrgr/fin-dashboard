import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import asyncio

class IdeaAnalyst:
    """
    Analyzes trading ideas and hypotheses using yfinance data.
    """

    def __init__(self):
        pass

    async def analyze(self, hypothesis: str, symbols: List[str]) -> Dict[str, Any]:
        if hypothesis == "high_div_low_vol":
            return await self._analyze_div_vs_vol(symbols)
        elif hypothesis == "ex_div_returns":
            return await self._analyze_ex_div_returns(symbols)
        else:
            return await self._generic_research(symbols)

    async def _analyze_div_vs_vol(self, symbols: List[str]) -> Dict[str, Any]:
        results = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                # Fetch 1 year of data for volatility
                hist = await asyncio.to_thread(ticker.history, period="1y")
                info = ticker.info
                
                if not hist.empty:
                    # Calculate annualized volatility
                    returns = hist['Close'].pct_change().dropna()
                    vol = returns.std() * np.sqrt(252) * 100
                    
                    div_yield = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
                    
                    results.append({
                        "symbol": symbol,
                        "name": info.get("longName", symbol),
                        "price": info.get("currentPrice"),
                        "div_yield": round(div_yield, 2),
                        "volatility": round(vol, 2),
                        "market_cap": info.get("marketCap")
                    })
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                
        return {
            "summary": "Vergleich von Dividendenrendite und annualisierter Volatilität (1J).",
            "columns": [
                {"key": "symbol", "label": "Symbol"},
                {"key": "name", "label": "Name"},
                {"key": "price", "label": "Preis"},
                {"key": "div_yield", "label": "Div Rendite %"},
                {"key": "volatility", "label": "Volatilität %"}
            ],
            "data": results
        }

    async def _analyze_ex_div_returns(self, symbols: List[str]) -> Dict[str, Any]:
        results = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                actions = await asyncio.to_thread(lambda: ticker.actions)
                if actions is None or actions.empty:
                    continue
                
                divs = actions[actions['Dividends'] > 0]
                if divs.empty:
                    continue
                
                # Get last ex-div date
                last_ex_div = divs.index[-1]
                
                # Fetch history around that date
                start_date = (last_ex_div - pd.Timedelta(days=10)).strftime('%Y-%m-%d')
                end_date = (last_ex_div + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
                hist = await asyncio.to_thread(ticker.history, start=start_date, end=end_date)
                
                if not hist.empty:
                    # Calculate return 5 days before to 5 days after
                    # This is a simplified "abnormal return" proxy
                    # For a real one we'd need a benchmark, but let's keep it simple for now as requested
                    try:
                        price_before = hist['Close'].iloc[0]
                        price_after = hist['Close'].iloc[-1]
                        total_return = ((price_after - price_before) / price_before) * 100
                        
                        results.append({
                            "symbol": symbol,
                            "last_ex_div": last_ex_div.strftime('%Y-%m-%d'),
                            "period_return": round(total_return, 2),
                            "current_price": yf.Ticker(symbol).info.get("currentPrice")
                        })
                    except:
                        pass
                        
            except Exception as e:
                print(f"Error analyzing ex-div for {symbol}: {e}")

        return {
            "summary": "Kursbewegung (+/- 10 Tage) um den letzten Ex-Dividenden-Tag.",
            "columns": [
                {"key": "symbol", "label": "Symbol"},
                {"key": "last_ex_div", "label": "Ex-Tag"},
                {"key": "period_return", "label": "Rendite %"},
                {"key": "current_price", "label": "Preis"}
            ],
            "data": results
        }

    async def _generic_research(self, symbols: List[str]) -> Dict[str, Any]:
        results = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                results.append({
                    "symbol": symbol,
                    "name": info.get("longName", symbol),
                    "price": info.get("currentPrice"),
                    "market_cap": info.get("marketCap"),
                    "sector": info.get("sector")
                })
            except:
                pass
        return {
            "summary": "Allgemeine Marktdaten für die angefragten Symbole.",
            "columns": [
                {"key": "symbol", "label": "Symbol"},
                {"key": "name", "label": "Name"},
                {"key": "price", "label": "Preis"},
                {"key": "market_cap", "label": "Market Cap"}
            ],
            "data": results
        }
