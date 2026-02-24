import yfinance as yf
from typing import List, Dict

class NewsAPI:
    def __init__(self):
        # No API key needed for yfinance news
        pass

    def get_market_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """
        Fetches news from Yahoo Finance via yfinance.
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            # yfinance news is a list of dicts with 'title', 'publisher', 'link', 'providerPublishTime', etc.
            return news[:limit]
        except Exception as e:
            print(f"Error fetching yfinance news for {symbol}: {e}")
            return []

    def get_traffic_light(self, symbol: str) -> str:
        """
        Signals "Red" if news are found for the jump, 
        "Green" if no major news are found (technical trade).
        """
        news = self.get_market_news(symbol, limit=3)
        # If there's recent news, we flag it as 'red' (news-driven)
        if news and len(news) > 0:
            return "red"
        return "green"
