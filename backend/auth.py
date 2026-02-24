from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
import os

# Configuration (should be in .env ideally)
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_username(token: str = Depends(oauth2_scheme)):
    """
    Standard JWT auth. Falls back to 'guest' if in stateless mode
    and validate_master_totp would pass.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username:
            return username
    except Exception:
        pass
    
    # If JWT fails, we check if we are in stateless mode (handled by routers)
    # Returning None here allows the router to decide.
    return None

def validate_master_totp(x_totp_code: str = Header(None)):
    """
    Stateless check for Master TOTP code.
    Passes if x_totp_code is valid for the MASTER_TOTP_SECRET.
    """
    master_secret = os.getenv("MASTER_TOTP_SECRET")
    if not master_secret:
        return True
        
    import pyotp
    totp = pyotp.TOTP(master_secret)
    if x_totp_code and totp.verify(x_totp_code):
        return True
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing TOTP code (X-TOTP-Code header)",
        headers={"WWW-Authenticate": "TOTP"},
    )

def get_guest_user(is_valid: bool = Depends(validate_master_totp), session: Session = Depends(get_session)):
    """
    Returns a 'guest' user from DB or creates one if missing.
    Used for stateless operation while keeping logic compatible with User model.
    """
    from .models import User
    guest = session.exec(select(User).where(User.username == "guest")).first()
    if not guest:
        guest = User(username="guest", hashed_password="STATLESS_MODE_ACTIVE")
        session.add(guest)
        session.commit()
        session.refresh(guest)
    return guest

async def get_active_username(
    username: Optional[str] = Depends(get_current_user_username),
    totp_valid: bool = Depends(validate_master_totp)
):
    """
    Unified dependency: Returns JWT username if available, 
    otherwise returns 'guest' if TOTP is valid.
    """
    return username or "guest"
