import pyotp
from typing import Optional

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(username: str, secret: str, issuer_name: str = "TradingDashboard") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)

def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.totp.TOTP(secret)
    return totp.verify(code)
    
def get_totp_instance(secret: str):
    return pyotp.totp.TOTP(secret)
