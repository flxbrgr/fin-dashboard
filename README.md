# Lokales Dashboard für Watchlisten

Dashboard für die "Overnight Overreaction" Strategie.

## Features
- **Intelligente Suche**: Finde Aktien und Kryptos blitzschnell.
- **Sprachsteuerung**: NLP für intelligente Umwandlung von natürlicher Sprache in konkrete Filter.
- **Sicherheit**: JWT Login und Google Authenticator (2FA) Support.
- **Multi-Watchlists**: Organisiere deine Favoriten in verschiedenen Listen.
- **Ideen & Strategien**: Multi-Tabbed Dashboard für quantitative Aktienanalysen (z.B. Dividenden-Studien, Abnormale Renditen).

## Setup
1. Kopiere `.env.example` zu `.env` und trage deine Keys ein.
2. Installiere Abhängigkeiten: `pip install -r requirements.txt`
3. Starte den Server: `uvicorn backend.main:app --reload`
4. Öffne `frontend/index.html`.

## Tech Stack
- **Backend**: Python, FastAPI, SQLModel (SQLite).
- **Frontend**: Vanilla HTML/JS, CSS3, TradingView Charts.
- **AI**: Google Gemini 1.5 Flash.
