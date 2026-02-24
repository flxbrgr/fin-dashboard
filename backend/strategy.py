from sqlmodel import Session, select
from .models import Ticker, Trade
from datetime import datetime
from typing import Dict, Any

class Strategy:
    def __init__(self, session: Session):
        self.session = session
        self.threshold = 5.0 # +/- 5%
        self.fee_rate = 0.002 # 0.20% round trip

    def find_overreactions(self, data: Dict[str, Any]):
        candidates = []
        for symbol, info in data.items():
            if abs(info['change']) >= self.threshold:
                ticker = self.update_or_create_ticker(symbol, info)
                candidates.append(ticker)
        self.session.commit()
        return candidates

    def update_or_create_ticker(self, symbol: str, info: Dict[str, Any]):
        statement = select(Ticker).where(Ticker.symbol == symbol)
        ticker = self.session.exec(statement).first()
        
        if ticker:
            ticker.last_price = info['price']
            ticker.change_pct = info['change']
            ticker.updated_at = datetime.utcnow()
        else:
            ticker = Ticker(
                symbol=symbol,
                last_price=info['price'],
                change_pct=info['change']
            )
            self.session.add(ticker)
        return ticker

    def execute_paper_trade(self, symbol: str, quantity: float, price: float, side: str):
        # Fees are 0.20% round trip, but usually split 0.1% entry 0.1% exit
        # Here we follow the user requirement: "abziehen 0,20% Round-Trip Gebühren"
        # I'll apply 0.20% as a total cost deduction from the capital or p&l
        fees = price * quantity * self.fee_rate
        trade = Trade(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            side=side,
            fees=fees,
            status="open"
        )
        self.session.add(trade)
        self.session.commit()
        return trade
