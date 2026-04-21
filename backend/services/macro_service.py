"""
Real India macro data with 3-day SQLite cache.

Sources:
  - World Bank API (free, no key) for GDP growth and CPI inflation
  - Yahoo Finance for NIFTY 50 trend + INDIA VIX (as a risk-on/off signal)

Gracefully degrades: if World Bank is unreachable, falls back to the last
cached snapshot regardless of age. Returns None only if there is truly
nothing to show.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import requests
import yfinance as yf

from database import Database


CACHE_HOURS = 72  # 3 days
WB_BASE = 'https://api.worldbank.org/v2/country/IN/indicator'


class MacroService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.db = Database()

    async def get_macro_data(self) -> Optional[dict]:
        cache_key = "macro_india"
        cached = self.db.get_cached(cache_key, max_age_hours=CACHE_HOURS)
        if cached:
            payload = cached['payload']
            payload['_cache_age_hours'] = round(cached['age_hours'], 1)
            payload['_from_cache'] = True
            return payload

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(self.executor, self._fetch_macro)
        if data:
            to_store = {k: v for k, v in data.items() if not k.startswith('_')}
            self.db.set_cached(cache_key, 'macro', to_store)
            data['_cache_age_hours'] = 0
            data['_from_cache'] = False
            return data

        stale = self.db.get_cached(cache_key, max_age_hours=24 * 365)
        if stale:
            payload = stale['payload']
            payload['_cache_age_hours'] = round(stale['age_hours'], 1)
            payload['_from_cache'] = True
            payload['_stale'] = True
            return payload
        return None

    def _fetch_macro(self) -> Optional[dict]:
        gdp = self._wb_latest('NY.GDP.MKTP.KD.ZG')
        cpi = self._wb_latest('FP.CPI.TOTL.ZG')
        nifty = self._nifty_snapshot()
        vix = self._vix_snapshot()

        if not (gdp or cpi or nifty):
            return None

        signals = []
        if gdp and gdp['value'] is not None:
            v = gdp['value']
            sig = 'positive' if v >= 6 else 'neutral' if v >= 4 else 'negative'
            signals.append({
                'label': 'India GDP growth',
                'value': f"{v:.1f}%",
                'signal': sig,
                'year': gdp['year'],
                'source': 'World Bank',
            })
        if cpi and cpi['value'] is not None:
            v = cpi['value']
            sig = 'positive' if v <= 4.5 else 'neutral' if v <= 6 else 'negative'
            signals.append({
                'label': 'CPI inflation',
                'value': f"{v:.1f}%",
                'signal': sig,
                'year': cpi['year'],
                'source': 'World Bank',
            })
        if nifty:
            sig = 'positive' if nifty['change_pct'] >= 0 else 'negative'
            signals.append({
                'label': 'NIFTY 50 (today)',
                'value': f"{nifty['change_pct']:+.2f}%",
                'signal': sig,
                'year': None,
                'source': 'NSE',
            })
            signals.append({
                'label': 'NIFTY vs 200-day',
                'value': f"{nifty['vs_ma200']:+.1f}%",
                'signal': 'positive' if nifty['vs_ma200'] > 0 else 'negative',
                'year': None,
                'source': 'NSE',
            })
        if vix:
            lvl = vix['price']
            sig = 'positive' if lvl < 14 else 'neutral' if lvl < 20 else 'negative'
            signals.append({
                'label': 'India VIX',
                'value': f"{lvl:.2f}",
                'signal': sig,
                'year': None,
                'source': 'NSE',
            })

        score = self._composite_score(gdp, cpi, nifty, vix)

        return {
            'score': score,
            'signals': signals,
            'gdp_growth': gdp['value'] if gdp else None,
            'gdp_year': gdp['year'] if gdp else None,
            'cpi': cpi['value'] if cpi else None,
            'cpi_year': cpi['year'] if cpi else None,
            'nifty_change_pct': nifty['change_pct'] if nifty else None,
            'nifty_vs_ma200': nifty['vs_ma200'] if nifty else None,
            'vix': vix['price'] if vix else None,
        }

    def _wb_latest(self, indicator: str) -> Optional[dict]:
        try:
            resp = requests.get(
                f"{WB_BASE}/{indicator}",
                params={'format': 'json', 'per_page': 60, 'mrnev': 5},
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not isinstance(data, list) or len(data) < 2:
                return None
            rows = data[1] or []
            for row in rows:
                val = row.get('value')
                if val is not None:
                    return {'value': float(val), 'year': row.get('date')}
            return None
        except Exception:
            return None

    def _nifty_snapshot(self) -> Optional[dict]:
        try:
            t = yf.Ticker('^NSEI')
            fi = t.fast_info
            price = float(fi.last_price or 0)
            prev = float(fi.previous_close or price)
            if not price:
                return None
            change_pct = round((price - prev) / prev * 100, 2) if prev else 0

            hist = t.history(period='1y', auto_adjust=False)
            if hist is None or hist.empty or len(hist) < 10:
                return {'price': price, 'change_pct': change_pct, 'vs_ma200': 0.0}
            closes = hist['Close'].astype(float)
            window = min(200, len(closes))
            ma = float(closes.rolling(window).mean().iloc[-1])
            vs_ma200 = round((price - ma) / ma * 100, 2) if ma else 0
            return {'price': price, 'change_pct': change_pct, 'vs_ma200': vs_ma200}
        except Exception:
            return None

    def _vix_snapshot(self) -> Optional[dict]:
        try:
            t = yf.Ticker('^INDIAVIX')
            fi = t.fast_info
            price = float(fi.last_price or 0)
            if not price:
                return None
            return {'price': round(price, 2)}
        except Exception:
            return None

    def _composite_score(self, gdp, cpi, nifty, vix) -> float:
        score = 50.0
        count = 0

        if gdp and gdp['value'] is not None:
            v = gdp['value']
            if v >= 7:
                score += 15
            elif v >= 6:
                score += 10
            elif v >= 4:
                score += 2
            elif v >= 2:
                score -= 8
            else:
                score -= 15
            count += 1

        if cpi and cpi['value'] is not None:
            v = cpi['value']
            if v <= 4:
                score += 10
            elif v <= 5:
                score += 4
            elif v <= 6:
                score -= 2
            elif v <= 8:
                score -= 8
            else:
                score -= 15
            count += 1

        if nifty:
            if nifty['vs_ma200'] > 5:
                score += 8
            elif nifty['vs_ma200'] > 0:
                score += 4
            elif nifty['vs_ma200'] < -5:
                score -= 8
            elif nifty['vs_ma200'] < 0:
                score -= 4
            count += 1

        if vix:
            v = vix['price']
            if v < 12:
                score += 5
            elif v < 16:
                score += 2
            elif v < 22:
                pass
            else:
                score -= 8
            count += 1

        if count == 0:
            return 50.0
        return round(min(max(score, 5), 95), 1)
