# GEMINI.md - Project Context

## Overview
FinDash is a premium trading dashboard designed for the "Overnight Overreaction" strategy. It features a natural language interface for executing scans and trades.

## Key Workflows
- **NLP Execution**: User enters command -> Gemini translates to JSON -> Backend triggers scan/trade/status.
- **Watchlist Management**: Users can create multiple lists and search for tickers via yfinance search API.
- **Auth Flow**: Signup -> Login -> (Optional 2FA) -> Dashboard access via JWT.

## Conventions
- Use `SQLModel` for all database interactions.
- Frontend should remain framework-less for speed and simplicity.
- Charts use `Lightweight Charts` by TradingView.
