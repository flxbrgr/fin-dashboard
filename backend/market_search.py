import requests
from binance.client import Client
from typing import List, Dict

class MarketSearch:
    """Handles searching for tickers across Yahoo Finance and Binance."""
    
    def __init__(self, binance_client: Client):
        self.binance_client = binance_client

    def search(self, query: str) -> List[Dict[str, str]]:
        results = []
        
        # Search Stocks (Yahoo)
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5&newsCount=0"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            quotes = res.json().get('quotes', [])
            for q in quotes:
                results.append({
                    "symbol": q.get("symbol"),
                    "name": q.get("shortname") or q.get("longname"),
                    "type": "stock"
                })
        except Exception as e:
            print(f"Yahoo Search error: {e}")

        # Search Crypto (Binance)
        try:
            info = self.binance_client.get_exchange_info()
            symbols = [s['symbol'] for s in info['symbols']]
            matches = [s for s in symbols if query.upper() in s]
            for m in matches[:5]:
                results.append({
                    "symbol": m,
                    "name": m,
                    "type": "crypto"
                })
        except Exception as e:
            print(f"Binance Search error: {e}")
            
        return results
