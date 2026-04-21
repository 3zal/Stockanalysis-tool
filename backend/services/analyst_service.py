"""
Real analyst data via yfinance with 3-day SQLite cache.

Pulls the analyst consensus fields yfinance exposes in `info`:
  - numberOfAnalystOpinions
  - recommendationKey (strong_buy / buy / hold / sell / strong_sell)
  - recommendationMean (1.0 strong buy → 5.0 strong sell)
  - targetMeanPrice, targetMedianPrice, targetHighPrice, targetLowPrice

Gracefully degrades: if no analyst data is available (common for small-cap
Indian tickers), returns None and the caller drops analyst from scoring.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import yfinance as yf

from database import Database


CACHE_HOURS = 72  # 3 days


class AnalystService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.db = Database()

    async def get_analyst_data(self, ticker: str, current_price: float) -> Optional[dict]:
        cache_key = f"analyst_{ticker}"
        cached = self.db.get_cached(cache_key, max_age_hours=CACHE_HOURS)
        if cached:
            payload = cached['payload']
            payload['_cache_age_hours'] = round(cached['age_hours'], 1)
            payload['_from_cache'] = True
            return self._recompute_upside(payload, current_price)

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(self.executor, self._fetch_analyst, ticker, current_price)
        if data:
            to_store = {k: v for k, v in data.items() if not k.startswith('_')}
            self.db.set_cached(cache_key, 'analyst', to_store)
            data['_cache_age_hours'] = 0
            data['_from_cache'] = False
        return data

    def _fetch_analyst(self, ticker: str, current_price: float) -> Optional[dict]:
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
        except Exception:
            return None

        num_analysts = info.get('numberOfAnalystOpinions') or 0
        rec_mean = info.get('recommendationMean')
        rec_key = info.get('recommendationKey') or ''
        target_mean = info.get('targetMeanPrice') or 0
        target_median = info.get('targetMedianPrice') or 0
        target_high = info.get('targetHighPrice') or 0
        target_low = info.get('targetLowPrice') or 0

        # Fallback: t.analyst_price_targets hits a different Yahoo endpoint
        # less likely to be blocked on cloud IPs
        if not target_mean and not rec_mean:
            try:
                apt = t.analyst_price_targets
                if apt and isinstance(apt, dict):
                    target_mean = target_mean or apt.get('mean') or apt.get('current') or 0
                    target_median = target_median or apt.get('median') or 0
                    target_high = target_high or apt.get('high') or 0
                    target_low = target_low or apt.get('low') or 0
            except Exception:
                pass

        if not num_analysts and not target_mean and not rec_mean:
            return None

        target = float(target_mean or target_median or 0)
        price = float(current_price or 0)
        upside_pct = round((target - price) / price * 100, 1) if price and target else 0.0

        buy_count, hold_count, sell_count = self._recommendations_split(t, num_analysts, rec_mean)

        if num_analysts > 0:
            buy_pct = round(buy_count / num_analysts * 100, 1)
            hold_pct = round(hold_count / num_analysts * 100, 1)
            sell_pct = round(sell_count / num_analysts * 100, 1)
        else:
            buy_pct = hold_pct = sell_pct = 0.0

        consensus_label = self._consensus_label(rec_key, rec_mean)
        score = self._score_from_recommendations(buy_pct, sell_pct, upside_pct, rec_mean)

        return {
            'score': score,
            'num_analysts': int(num_analysts),
            'buy': int(buy_count),
            'hold': int(hold_count),
            'sell': int(sell_count),
            'buy_pct': buy_pct,
            'hold_pct': hold_pct,
            'sell_pct': sell_pct,
            'consensus': consensus_label,
            'recommendation_mean': round(float(rec_mean), 2) if rec_mean else 0.0,
            'target_price': round(target, 2),
            'target_median': round(float(target_median or 0), 2),
            'high_target': round(float(target_high or 0), 2),
            'low_target': round(float(target_low or 0), 2),
            'upside_pct': upside_pct,
        }

    def _recommendations_split(self, t, num_analysts: int, rec_mean):
        try:
            rec = t.recommendations
            if rec is not None and not rec.empty:
                latest = rec.iloc[0]
                sb = int(latest.get('strongBuy', 0) or 0)
                b = int(latest.get('buy', 0) or 0)
                h = int(latest.get('hold', 0) or 0)
                s = int(latest.get('sell', 0) or 0)
                ss = int(latest.get('strongSell', 0) or 0)
                buy_total = sb + b
                sell_total = s + ss
                hold_total = h
                if buy_total + sell_total + hold_total > 0:
                    return buy_total, hold_total, sell_total
        except Exception:
            pass

        if not num_analysts or not rec_mean:
            return 0, 0, 0
        rm = float(rec_mean)
        if rm <= 2.0:
            buy_ratio, hold_ratio, sell_ratio = 0.70, 0.25, 0.05
        elif rm <= 2.5:
            buy_ratio, hold_ratio, sell_ratio = 0.55, 0.35, 0.10
        elif rm <= 3.0:
            buy_ratio, hold_ratio, sell_ratio = 0.35, 0.50, 0.15
        elif rm <= 3.5:
            buy_ratio, hold_ratio, sell_ratio = 0.20, 0.55, 0.25
        else:
            buy_ratio, hold_ratio, sell_ratio = 0.10, 0.40, 0.50
        buy = round(num_analysts * buy_ratio)
        sell = round(num_analysts * sell_ratio)
        hold = num_analysts - buy - sell
        return buy, hold, sell

    def _consensus_label(self, rec_key: str, rec_mean) -> str:
        key_map = {
            'strong_buy': 'Strong Buy',
            'buy': 'Buy',
            'hold': 'Hold',
            'sell': 'Sell',
            'strong_sell': 'Strong Sell',
            'underperform': 'Underperform',
        }
        if rec_key and rec_key in key_map:
            return key_map[rec_key]
        if rec_mean:
            rm = float(rec_mean)
            if rm <= 1.75:
                return 'Strong Buy'
            if rm <= 2.5:
                return 'Buy'
            if rm <= 3.25:
                return 'Hold'
            if rm <= 4.0:
                return 'Sell'
            return 'Strong Sell'
        return 'No Coverage'

    def _score_from_recommendations(self, buy_pct: float, sell_pct: float, upside_pct: float, rec_mean) -> float:
        score = 50.0
        if rec_mean:
            rm = float(rec_mean)
            score = 100 - (rm - 1) * 25
        else:
            score = 50 + buy_pct * 0.5 - sell_pct * 0.5
        if upside_pct > 20:
            score += 8
        elif upside_pct > 10:
            score += 4
        elif upside_pct < -10:
            score -= 8
        elif upside_pct < 0:
            score -= 4
        return round(min(max(score, 5), 95), 1)

    def _recompute_upside(self, payload: dict, current_price: float) -> dict:
        target = payload.get('target_price') or 0
        price = float(current_price or 0)
        if price and target:
            payload['upside_pct'] = round((target - price) / price * 100, 1)
        return payload
