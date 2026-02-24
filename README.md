# FinDash - AI-Native Trading Dashboard

Premium Dashboard für die "Overnight Overreaction" Strategie.

## Features
- **Intelligente Suche**: Finde Aktien und Kryptos blitzschnell.
- **Sprachsteuerung**: Führe Scans und Trades mit einfachen deutschen Befehlen aus.
- **Strategie-Scanner**: Erkennt automatisch heftige Kursbewegungen (+/- 5%).
- **Sicherheit**: JWT Login und Google Authenticator (2FA) Support.
- **Multi-Watchlists**: Organisiere deine Favoriten in verschiedenen Listen.

## Setup
1. Kopiere `.env.example` zu `.env` und trage deine Keys ein.
2. Installiere Abhängigkeiten: `pip install -r requirements.txt`
3. Starte den Server: `uvicorn backend.main:app --reload`
4. Öffne `frontend/index.html`.

## Tech Stack
- **Backend**: Python, FastAPI, SQLModel (SQLite).
- **Frontend**: Vanilla HTML/JS, CSS3, TradingView Charts.
- **AI**: Google Gemini 1.5 Flash.
