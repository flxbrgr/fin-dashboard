import os
import json
from typing import Optional, Dict, Any
from google import genai

class GeminiNLP:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not set")

    def process_command(self, text: str, api_key: Optional[str] = None):
        """
        Translates German commands to structured actions.
        Uses provided api_key or falls back to environment variable.
        """
        key_to_use = api_key or self.api_key
        if not key_to_use:
            return {"error": "Gemini API key not configured"}
            
        client = genai.Client(api_key=key_to_use)
        model_id = "gemini-1.5-flash"
        
        prompt = f"""
        Handle als Trading-Assistent für FinDash. Übersetze den folgenden deutschen Befehl in ein JSON-Format.
        Nutze das folgende 'yfinance Capability Manual' zur Auswahl der richtigen Filterkeys.

        ### yfinance Capability Manual (Kriterien mapping):
        - Marktkapitalisierung: 'market_cap' (in USD)
        - KGV (Kurs-Gewinn-Verhältnis): 'trailing_pe'
        - Dividendenrendite (z.B. 0.05 für 5%): 'dividend_yield'
        - Kurs-Buch-Verhältnis: 'price_to_book'
        - Nettomarge: 'profit_margins' (z.B. 0.2 für 20%)
        - Sektor/Branche: 'sector' (z.B. 'Technology', 'Financial Services', 'Healthcare')
        - Preis: 'current_price'

        Mögliche Aktionen: 'scan', 'trade', 'status', 'filter', 'research'.

        Befehl: "{text}"

        JSON-Format Beispiele:
        - "Zeig mir Verlierer > 5%": {{"action": "scan", "filters": {{"threshold": 5, "type": "losers"}}}}
        - "Kauf 10 AAPL": {{"action": "trade", "symbol": "AAPL", "side": "buy", "quantity": 10}}
        - "Status meiner Trades": {{"action": "status"}}
        - "Filtere Tech Aktien mit KGV unter 25 und Dividende über 2%": {{"action": "filter", "criteria": {{"sector": "Technology", "trailing_pe_max": 25, "dividend_yield_min": 0.02}}}}
        - "Ich möchte testen ob Dividenden-Aktien weniger Schwankungen haben": {{"action": "research", "title": "Dividende vs Volatilität", "suggested_symbols": ["JNJ", "PG", "KO", "PEP", "XOM"], "hypothesis": "high_div_low_vol"}}
        - "Abnormal returns after div-ex?": {{"action": "research", "title": "Abnormale Renditen (Ex-Div)", "suggested_symbols": ["AAPL", "T", "VZ", "MAIN"], "hypothesis": "ex_div_returns"}}

        Antworte NUR mit dem JSON.
        """
        
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            # Basic cleanup of markdown code blocks if present
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
        except Exception as e:
            print(f"Gemini error: {e}")
            return {"error": str(e)}
