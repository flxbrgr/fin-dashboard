from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Dict, Any
from ..database import get_session
from ..models import Ticker, Trade, User
from ..data_fetcher import DataFetcher
from ..strategy import Strategy
from ..news_api import NewsAPI
from ..gemini_nlp import GeminiNLP
from ..auth import get_active_username, validate_master_totp
import datetime

router = APIRouter(tags=["Trading & NLP"], dependencies=[Depends(validate_master_totp)])

@router.post("/scan")
async def scan_market(username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    fetcher = DataFetcher()
    news = NewsAPI()
    data = await fetcher.fetch_all_data()
    strategy = Strategy(session)
    candidates = strategy.find_overreactions(data)
    
    # Enrich with news traffic light
    result = []
    for cand in candidates:
        light = news.get_traffic_light(cand.symbol)
        result.append({
            "ticker": cand,
            "traffic_light": light
        })
    return result

@router.post("/command")
async def process_nlp_command(text: str, username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    
    # Rate Limiting Logic
    today = datetime.date.today().isoformat()
    if user.last_call_date != today:
        user.api_calls_today = 0
        user.last_call_date = today
    
    if user.api_calls_today >= user.daily_api_limit:
        raise HTTPException(status_code=429, detail="Daily NLP limit reached")
    
    nlp = GeminiNLP()
    action = nlp.process_command(text, api_key=user.gemini_api_key)
    
    if "error" in action:
        return action
        
    user.api_calls_today += 1
    session.add(user)
    session.commit()
        
    if action["action"] == "scan":
        return await scan_market(username, session)
    elif action["action"] == "trade":
        strategy = Strategy(session)
        fetcher = DataFetcher()
        ticker_data = await fetcher.fetch_stocks([action["symbol"]])
        if not ticker_data:
             ticker_data = await fetcher.fetch_crypto([action["symbol"]])
             
        if action["symbol"] in ticker_data:
            price = ticker_data[action["symbol"]]["price"]
            trade = strategy.execute_paper_trade(
                action["symbol"], 
                action["quantity"], 
                price, 
                action["side"]
            )
            return {"message": "Trade executed", "trade": trade}
        return {"error": "Symbol not found"}
    elif action["action"] == "status":
        from .auth import router as auth_router # Local import to avoid circular if needed, but standard is using get_trades
        # Actually main.py had a direct call to get_trades. 
        # For simplicity, we can just query the trades here or import the trades logic.
        return session.query(Trade).all()
    elif action["action"] == "filter":
        criteria = action.get("criteria", {})
        fetcher = DataFetcher()
        filtered = await fetcher.filter_stocks(criteria)
        return {"action": "filter", "results": filtered}
        
    return {"error": "Unknown action"}

@router.get("/tickers", response_model=List[Ticker])
def get_tickers(username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    return session.query(Ticker).all()

@router.get("/trades", response_model=List[Trade])
def get_trades(username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    return session.query(Trade).all()
