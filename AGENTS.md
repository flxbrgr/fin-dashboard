# AGENTS.md - FinDash AI Context

## 🎯 Vitals
- **Project**: FinDash (Trading Dashboard)
- **Stack**: FastAPI (Python), SQLModel (SQLite), Vanilla JS/HTML/CSS
- **Core Strategy**: Overnight Overreaction (+/- 5% Price Jump)
- **Primary APIs**: yfinance (Stocks), python-binance (Crypto - Read only), Gemini (NLP)

## 🏗 Architecture
- `backend/`: FastAPI application
    - `main.py`: Entry point and API routing
    - `models.py`: SQLModel schemas (User, Watchlist, Ticker, Trade)
    - `gemini_nlp.py`: Natural language command translation
    - `idea_analyst.py`: Quantitative research and strategy service
    - `data_fetcher.py`: yfinance/Binance abstraction layer
- `frontend/`: Vanilla web app
    - `index.html`: Dashboard layout
    - `app.js`: UI logic, Auth flow, TradingView Charts

## 🛠 Dev Commands
- Install: `pip install -r requirements.txt`
- Run local: `uvicorn backend.main:app --reload`
- Test NLP: `POST /command?text=...`

## 📜 Coding Standards
- **German First**: Natural language commands are primarily in German.
- **Security**: Mandatory JWT auth and TOTP 2FA.
- **Lean**: No heavy frontend frameworks; standard DOM manipulation.
- **API Keys**: Stored in .env (GEMINI_API_KEY, JWT_SECRET, AUTH_2FA_SECRET).

## 🚀 Deployment
- Target: `fin.felixberger.xyz` (Uberspace)
- Web Server: Apache (Uberspace default) proxying to Uvicorn/Gunicorn.
