from typing import Dict, Any, List
from .stock_fetcher import StockFetcher
from .crypto_fetcher import CryptoFetcher
from .stock_scanner import StockScanner
from .market_search import MarketSearch

class DataFetcher:
    """
    Lean orchestrator that delegates data fetching, scanning, and search 
    to specialized modules. Follows 'One File, One Purpose' guidelines.
    """
    
    def __init__(self):
        # Initialize specialized modules
        self.stock_fetcher = StockFetcher()
        self.crypto_fetcher = CryptoFetcher()
        self.stock_scanner = StockScanner()
        # MarketSearch needs the binance client from CryptoFetcher
        self.market_search = MarketSearch(self.crypto_fetcher.client)

    async def fetch_stocks(self, symbols: list):
        """Delegates to StockFetcher."""
        return await self.stock_fetcher.fetch_stocks(symbols)

    async def fetch_crypto(self, symbols: list):
        """Delegates to CryptoFetcher."""
        return await self.crypto_fetcher.fetch_crypto(symbols)

    async def fetch_all_data(self):
        """Orchestrates combined data fetch."""
        stocks = ["AAPL", "TSLA", "NVDA", "MSFT"]
        cryptos = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        stock_data = await self.fetch_stocks(stocks)
        crypto_data = await self.fetch_crypto(cryptos)
        
        return {**stock_data, **crypto_data}

    async def filter_stocks(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Delegates to StockScanner."""
        return await self.stock_scanner.filter_stocks(criteria)

    def search(self, query: str) -> List[Dict[str, str]]:
        """Delegates to MarketSearch."""
        return self.market_search.search(query)
