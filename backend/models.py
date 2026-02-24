from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    two_fa_enabled: bool = Field(default=False)
    two_fa_secret: Optional[str] = None
    
    # Relationships
    watchlists: List["Watchlist"] = Relationship(back_populates="user")
    
    # NLP & Personalization
    gemini_api_key: Optional[str] = None
    daily_api_limit: int = Field(default=50) # Default limit of 50 calls per day
    api_calls_today: int = Field(default=0)
    last_call_date: Optional[str] = None # To reset the counter daily

class WatchlistTickerLink(SQLModel, table=True):
    watchlist_id: Optional[int] = Field(
        default=None, foreign_key="watchlist.id", primary_key=True
    )
    ticker_id: Optional[int] = Field(
        default=None, foreign_key="ticker.id", primary_key=True
    )

class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="watchlists")
    tickers: List["Ticker"] = Relationship(back_populates="watchlists", link_model=WatchlistTickerLink)

class TickerBase(SQLModel):
    symbol: str = Field(index=True)
    name: Optional[str] = None
    last_price: float
    change_pct: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Ticker(TickerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    watchlists: List["Watchlist"] = Relationship(back_populates="tickers", link_model=WatchlistTickerLink)

class TradeBase(SQLModel):
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime = Field(default_factory=datetime.utcnow)
    side: str  # 'buy' or 'sell'
    fees: float
    status: str = "open"  # 'open', 'closed'

class Trade(TradeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    p_and_l: Optional[float] = None
