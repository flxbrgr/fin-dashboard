from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from ..database import get_session
from ..models import User
from ..auth import get_active_username, validate_master_totp

router = APIRouter(prefix="/user", tags=["User Settings"], dependencies=[Depends(validate_master_totp)])

@router.post("/settings")
async def update_settings(
    gemini_api_key: Optional[str] = None, 
    daily_limit: Optional[int] = None,
    username: str = Depends(get_active_username), 
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if gemini_api_key is not None:
        user.gemini_api_key = gemini_api_key
    if daily_limit is not None:
        user.daily_api_limit = daily_limit
        
    session.add(user)
    session.commit()
    return {"message": "Settings updated"}

@router.get("/settings")
async def get_settings(username: str = Depends(get_active_username), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    return {
        "gemini_api_key": user.gemini_api_key,
        "daily_api_limit": user.daily_api_limit,
        "api_calls_today": user.api_calls_today
    }
