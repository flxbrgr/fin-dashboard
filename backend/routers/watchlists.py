from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from ..database import get_session
from ..models import Watchlist, WatchlistTickerLink, Ticker, User
from ..auth import get_active_username, validate_master_totp

router = APIRouter(prefix="/watchlists", tags=["Watchlists"], dependencies=[Depends(validate_master_totp)])

@router.get("", response_model=List[Watchlist])
async def list_watchlists(username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    return user.watchlists

@router.post("", response_model=Watchlist)
async def create_watchlist(name: str, username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    new_watchlist = Watchlist(name=name, user_id=user.id)
    session.add(new_watchlist)
    session.commit()
    session.refresh(new_watchlist)
    return new_watchlist

@router.delete("/{watchlist_id}")
async def delete_watchlist(watchlist_id: int, username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist or watchlist.user_id != user.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    session.delete(watchlist)
    session.commit()
    return {"message": "Watchlist deleted"}

@router.post("/{watchlist_id}/tickers")
async def add_ticker_to_watchlist(
    watchlist_id: int, 
    symbol: str, 
    name: Optional[str] = None, 
    ticker_type: str = "stock",
    username: str = Depends(get_active_username), 
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == username)).first()
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist or watchlist.user_id != user.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    ticker = session.exec(select(Ticker).where(Ticker.symbol == symbol)).first()
    if not ticker:
        ticker = Ticker(symbol=symbol, name=name, type=ticker_type)
        session.add(ticker)
        session.commit()
        session.refresh(ticker)
    
    link = session.exec(select(WatchlistTickerLink).where(
        WatchlistTickerLink.watchlist_id == watchlist_id,
        WatchlistTickerLink.ticker_id == ticker.id
    )).first()
    
    if not link:
        watchlist.tickers.append(ticker)
        session.add(watchlist)
        session.commit()
        
    return {"message": "Ticker added to watchlist"}

@router.get("/{watchlist_id}/tickers", response_model=List[Ticker])
async def get_watchlist_tickers(watchlist_id: int, username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist or watchlist.user_id != user.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist.tickers
