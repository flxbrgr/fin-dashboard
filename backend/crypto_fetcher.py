from binance.client import Client
from typing import Dict, Any

class CryptoFetcher:
    """Handles live crypto prices and performance data using Binance."""
    
    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.client = Client(api_key, api_secret)

    async def fetch_crypto(self, symbols: list) -> Dict[str, Any]:
        data = {}
        for symbol in symbols:
            try:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                # 24h stats for priceChangePercent
                stats = self.client.get_ticker(symbol=symbol)
                data[symbol] = {
                    "price": float(ticker['price']),
                    "change": float(stats['priceChangePercent']),
                    "type": "crypto"
                }
            except Exception as e:
                print(f"Error fetching crypto {symbol}: {e}")
        return data
