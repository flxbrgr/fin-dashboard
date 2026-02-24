from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from ..database import get_session
from ..models import User
from ..auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user_username
)
from ..security_2fa import (
    generate_totp_secret, 
    get_totp_uri, 
    verify_totp_code
)

router = APIRouter(tags=["Authentication"])

@router.post("/signup")
async def signup(username: str, password: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    return {"message": "User created successfully"}

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if user.two_fa_enabled:
        return {"require_2fa": True, "username": user.username}

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/2fa/setup")
async def setup_2fa(username: str = Depends(get_current_user_username), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    secret = generate_totp_secret()
    user.two_fa_secret = secret
    session.add(user)
    session.commit()
    uri = get_totp_uri(username, secret)
    return {"secret": secret, "uri": uri}

@router.post("/2fa/verify")
async def verify_2fa(username: str, code: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.two_fa_secret:
        raise HTTPException(status_code=400, detail="2FA not setup")
    
    if verify_totp_code(user.two_fa_secret, code):
        user.two_fa_enabled = True
        session.add(user)
        session.commit()
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
