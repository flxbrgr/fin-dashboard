import pyotp
import qrcode
import os
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("MASTER_TOTP_SECRET")

if not secret:
    print("Error: MASTER_TOTP_SECRET not found in .env")
    exit(1)

totp = pyotp.TOTP(secret)
uri = totp.provisioning_uri(name="Felix", issuer_name="FinDash")

print(f"TOTP URI: {uri}")
print("\nScan this QR code in your Authenticator App:")

qr = qrcode.QRCode()
qr.add_data(uri)
qr.print_ascii()
