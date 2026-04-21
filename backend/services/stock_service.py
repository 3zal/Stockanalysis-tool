import requests
import pandas as pd
import numpy as np
import json
import os
import asyncio
import time
import io
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache
from typing import Optional
from datetime import datetime, timedelta

from services.nse_client import get_session, NSE_BASE

# ── Cache layers ───────────────────────────────────────────────────────────────
_quote_cache       = TTLCache(maxsize=200, ttl=300)    # 5 min
_fundamentals_cache = TTLCache(maxsize=200, ttl=3600)  # 1 hour
_technicals_cache  = TTLCache(maxsize=200, ttl=900)    # 15 min
_history_cache     = TTLCache(maxsize=100, ttl=1800)   # 30 min

STOCKS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks.json')

# Map frontend period strings → approximate calendar days to request
PERIOD_DAYS = {
    '1wk': 12, '1mo': 40, '3mo': 105,
    '6mo': 210, '1y': 390, '2y': 780, '5y': 1900,
}


def _load_stocks_db() -> list:
    try:
        with open(STOCKS_FILE) as f:
            return json.load(f).get('stocks', [])
    except Exception:
        return []


STOCKS_DB = _load_stocks_db()


class StockService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)

    # ── Search ─────────────────────────────────────────────────────────────────

    async def search_stocks(self, query: str) -> list:
        query_upper = query.upper().strip()
        query_lower = query.lower().strip()
        seen: set = set()
        results: list = []

        for stock in STOCKS_DB:
            sym = stock['symbol']
            if sym == query_upper and sym not in seen:
                seen.add(sym)
                results.append(self._fmt_search(stock))

        for stock in STOCKS_DB:
            sym = stock['symbol']
            if sym.startswith(query_upper) and sym not in seen:
                seen.add(sym)
                results.append(self._fmt_search(stock))
                if len(results) >= 8:
                    break

        if len(results) < 10:
            for stock in STOCKS_DB:
                sym = stock['symbol']
                if query_lower in stock['name'].lower() and sym not in seen:
                    seen.add(sym)
                    results.append(self._fmt_search(stock))
                    if len(results) >= 10:
                        break

        return results[:10]

    def _fmt_search(self, stock: dict) -> dict:
        return {
            'symbol': stock['symbol'],
            'ticker': f"{stock['symbol']}.NS",
            'ticker_bse': f"{stock['symbol']}.BO",
            'name': stock['name'],
            'exchange': stock.get('exchange', 'NSE'),
            'sector': stock.get('sector', ''),
        }

    # ── Quote ──────────────────────────────────────────────────────────────────

    async def get_quote(self, ticker: str) -> Optional[dict]:
        if ticker in _quote_cache:
            return _quote_cache[ticker]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self._fetch_quote, ticker)
        if result:
            _quote_cache[ticker] = result
        return result

    def _fetch_quote_yfinance(self, ticker: str, symbol: str, exchange: str) -> Optional[dict]:
        try:
            t = yf.Ticker(ticker)
            fi = t.fast_info
            price = float(fi.last_price or 0)
            if not price:
                return None
            prev = float(fi.previous_close or price)
            change = round(price - prev, 2)
            change_pct = round((change / prev * 100) if prev else 0, 2)

            name = symbol
            sector = ''
            industry = ''
            website = ''
            description = ''
            market_cap = 0
            try:
                info = t.info or {}
                name = info.get('longName') or info.get('shortName') or symbol
                sector = info.get('sector') or ''
                industry = info.get('industry') or ''
                website = info.get('website') or ''
                description = info.get('longBusinessSummary') or ''
                market_cap = int(info.get('marketCap') or 0)
            except Exception:
                pass

            return {
                'ticker':       ticker,
                'name':         str(name),
                'price':        round(price, 2),
                'change':       change,
                'change_pct':   change_pct,
                'volume':       int(fi.last_volume or 0),
                'avg_volume':   int(getattr(fi, 'three_month_average_volume', 0) or 0),
                'market_cap':   market_cap,
                'week_52_high': float(fi.year_high or price),
                'week_52_low':  float(fi.year_low or price),
                'day_high':     float(fi.day_high or price),
                'day_low':      float(fi.day_low or price),
                'open':         float(fi.open or price),
                'currency':     str(fi.currency or 'INR'),
                'exchange':     exchange,
                'sector':       str(sector),
                'industry':     str(industry),
                'website':      str(website),
                'description':  str(description),
            }
        except Exception:
            return None

    def _fetch_quote(self, ticker: str) -> Optional[dict]:
        if ticker.endswith('.NS'):
            symbol, exchange = ticker[:-3], 'NSE'
        elif ticker.endswith('.BO'):
            symbol, exchange = ticker[:-3], 'BSE'
        else:
            symbol, exchange = ticker, 'NSE'

        # Primary: Yahoo Finance via yfinance
        yf_quote = self._fetch_quote_yfinance(ticker, symbol, exchange)
        if yf_quote:
            return yf_quote

        # Fallback: Twelve Data
        td_quote = self._fetch_quote_twelvedata(ticker, symbol, exchange)
        if td_quote:
            return td_quote

        # Fallback: NSE India
        try:
            sess = get_session()
            resp = sess.get(
                f'{NSE_BASE}/api/quote-equity',
                params={'symbol': symbol},
                timeout=12,
            )
            if resp.status_code != 200:
                return None
            try:
                data = resp.json()
            except Exception:
                return None

            price_info    = data.get('priceInfo', {})
            industry_info = data.get('industryInfo', {})
            info          = data.get('info', {})
            metadata      = data.get('metadata', {})

            price = price_info.get('lastPrice') or price_info.get('close') or 0
            if not price:
                return None

            price      = float(price)
            prev_close = float(price_info.get('previousClose') or price)
            change     = float(price_info.get('change',
                                              round(price - prev_close, 2)))
            change_pct = float(price_info.get('pChange',
                                              round(change / prev_close * 100, 2)
                                              if prev_close else 0))

            intraday = price_info.get('intraDayHighLow', {})
            week     = price_info.get('weekHighLow', {})

            vol = (price_info.get('totalTradedVolume')
                   or price_info.get('quantityTraded')
                   or 0)

            name = (info.get('companyName')
                    or metadata.get('companyName')
                    or symbol)

            return {
                'ticker':       ticker,
                'name':         str(name),
                'price':        round(price, 2),
                'change':       round(change, 2),
                'change_pct':   round(change_pct, 2),
                'volume':       int(vol or 0),
                'avg_volume':   0,
                'market_cap':   0,
                'week_52_high': float(week.get('max') or price),
                'week_52_low':  float(week.get('min') or price),
                'day_high':     float(intraday.get('max')
                                      or price_info.get('high') or price),
                'day_low':      float(intraday.get('min')
                                      or price_info.get('low') or price),
                'open':         float(price_info.get('open') or price),
                'currency':     'INR',
                'exchange':     exchange,
                'sector':       str(industry_info.get('sector')
                                    or industry_info.get('macro') or ''),
                'industry':     str(industry_info.get('industry')
                                    or industry_info.get('basicIndustry') or ''),
                'website':      '',
                'description':  '',
            }
        except Exception:
            return None

    # ── Fundamentals ───────────────────────────────────────────────────────────

    async def get_fundamentals(self, ticker: str) -> dict:
        ck = f"fund_{ticker}"
        if ck in _fundamentals_cache:
            return _fundamentals_cache[ck]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self._fetch_fundamentals, ticker)
        _fundamentals_cache[ck] = result
        return result

    def _fetch_fundamentals_yfinance(self, ticker: str) -> dict:
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            if not info or not info.get('regularMarketPrice') and not info.get('currentPrice'):
                return {}
            return {
                'pe_ratio':          self._sf(info.get('trailingPE')),
                'forward_pe':        self._sf(info.get('forwardPE')),
                'peg_ratio':         self._sf(info.get('pegRatio') or info.get('trailingPegRatio')),
                'eps':               self._sf(info.get('trailingEps')),
                'eps_growth':        self._sf(info.get('earningsGrowth')) * 100,
                'revenue_growth':    self._sf(info.get('revenueGrowth')) * 100,
                'roe':               self._sf(info.get('returnOnEquity')) * 100,
                'roa':               self._sf(info.get('returnOnAssets')) * 100,
                'debt_to_equity':    self._sf(info.get('debtToEquity')),
                'current_ratio':     self._sf(info.get('currentRatio')),
                'quick_ratio':       self._sf(info.get('quickRatio')),
                'profit_margin':     self._sf(info.get('profitMargins')) * 100,
                'operating_margin':  self._sf(info.get('operatingMargins')) * 100,
                'gross_margin':      self._sf(info.get('grossMargins')) * 100,
                'dividend_yield':    self._sf(info.get('dividendYield')) * 100,
                'dividend_rate':     self._sf(info.get('dividendRate')),
                'book_value':        self._sf(info.get('bookValue')),
                'price_to_book':     self._sf(info.get('priceToBook')),
                'price_to_sales':    self._sf(info.get('priceToSalesTrailing12Months')),
                'ev_to_ebitda':      self._sf(info.get('enterpriseToEbitda')),
                'ev_to_revenue':     self._sf(info.get('enterpriseToRevenue')),
                'beta':              self._sf(info.get('beta'), 1.0),
                'float_shares':      int(info.get('floatShares') or 0),
                'shares_outstanding': int(info.get('sharesOutstanding') or 0),
                'free_cashflow':     int(info.get('freeCashflow') or 0),
                'total_cash':        int(info.get('totalCash') or 0),
                'total_debt':        int(info.get('totalDebt') or 0),
                'sector':            str(info.get('sector') or ''),
                'employees':         int(info.get('fullTimeEmployees') or 0),
            }
        except Exception:
            return {}

    def _fetch_fundamentals(self, ticker: str) -> dict:
        yf_fund = self._fetch_fundamentals_yfinance(ticker)
        if yf_fund:
            return yf_fund
        try:
            symbol = ticker.replace('.NS', '').replace('.BO', '')
            sess   = get_session()
            resp   = sess.get(
                f'{NSE_BASE}/api/quote-equity',
                params={'symbol': symbol},
                timeout=12,
            )
            if resp.status_code != 200:
                return {}
            try:
                data = resp.json()
            except Exception:
                return {}

            metadata      = data.get('metadata', {})
            security_info = data.get('securityInfo', {})
            price_info    = data.get('priceInfo', {})
            industry_info = data.get('industryInfo', {})

            price = float(price_info.get('lastPrice') or 0)
            pe    = self._sf(metadata.get('pdSymbolPe'))
            pb    = self._sf(metadata.get('pdSectorPb')
                             or metadata.get('pdSymbolPb'))
            eps   = round(price / pe, 2) if pe and pe > 0 and price else 0.0

            return {
                'pe_ratio':          pe,
                'forward_pe':        0.0,
                'peg_ratio':         0.0,
                'eps':               eps,
                'eps_growth':        0.0,
                'revenue_growth':    0.0,
                'roe':               0.0,
                'roa':               0.0,
                'debt_to_equity':    0.0,
                'current_ratio':     0.0,
                'quick_ratio':       0.0,
                'profit_margin':     0.0,
                'operating_margin':  0.0,
                'gross_margin':      0.0,
                'dividend_yield':    self._sf(security_info.get('dividendPerShare')),
                'dividend_rate':     self._sf(security_info.get('dividendPerShare')),
                'book_value':        0.0,
                'price_to_book':     pb,
                'price_to_sales':    0.0,
                'ev_to_ebitda':      0.0,
                'ev_to_revenue':     0.0,
                'beta':              1.0,
                'float_shares':      0,
                'shares_outstanding': int(security_info.get('issuedSize') or 0),
                'free_cashflow':     0,
                'total_cash':        0,
                'total_debt':        0,
                'sector':            str(industry_info.get('sector') or ''),
                'employees':         0,
            }
        except Exception:
            return {}

    # ── Technicals ─────────────────────────────────────────────────────────────

    async def get_technicals(self, ticker: str) -> dict:
        ck = f"tech_{ticker}"
        if ck in _technicals_cache:
            return _technicals_cache[ck]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self._calculate_technicals, ticker)
        _technicals_cache[ck] = result
        return result

    def _calculate_technicals(self, ticker: str) -> dict:
        try:
            # Prefer already-cached history to avoid an extra network call
            hist: Optional[list] = None
            for p in ('1y', '6mo', '3mo'):
                cached = _history_cache.get(f"hist_{ticker}_{p}")
                if cached and len(cached) >= 30:
                    hist = cached
                    break

            if not hist:
                hist = self._fetch_history(ticker, '1y')
                if hist:
                    _history_cache[f"hist_{ticker}_1y"] = hist

            if not hist or len(hist) < 20:
                return {}

            df      = pd.DataFrame(hist)
            close   = pd.Series(df['close'].astype(float).values)
            volume  = pd.Series(df['volume'].astype(float).values)
            high    = pd.Series(df['high'].astype(float).values)
            low     = pd.Series(df['low'].astype(float).values)
            cur     = float(close.iloc[-1])

            # RSI-14
            delta  = close.diff()
            gain   = delta.where(delta > 0, 0.0).rolling(14).mean()
            loss   = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
            rsi    = float((100 - 100 / (1 + gain / (loss + 1e-10))).iloc[-1])

            # MACD (12, 26, 9)
            ema12  = close.ewm(span=12, adjust=False).mean()
            ema26  = close.ewm(span=26, adjust=False).mean()
            macd_l = ema12 - ema26
            sig_l  = macd_l.ewm(span=9, adjust=False).mean()
            c_macd = float(macd_l.iloc[-1])
            c_sig  = float(sig_l.iloc[-1])
            c_hist = float((macd_l - sig_l).iloc[-1])

            # Moving averages
            n = len(close)
            ma20  = float(close.rolling(20).mean().iloc[-1]) if n >= 20  else cur
            ma50  = float(close.rolling(50).mean().iloc[-1]) if n >= 50  else cur
            ma200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else cur

            # Bollinger Bands (20, ±2σ)
            bb_mid = close.rolling(20).mean()
            bb_std = close.rolling(20).std()
            bb_up  = float((bb_mid + 2 * bb_std).iloc[-1])
            bb_dn  = float((bb_mid - 2 * bb_std).iloc[-1])
            bb_pos = (cur - bb_dn) / (bb_up - bb_dn + 1e-10) * 100

            # Volume
            avg_vol = float(volume.rolling(20).mean().iloc[-1]) if not volume.empty else 1
            cur_vol = float(volume.iloc[-1]) if not volume.empty else 0
            vol_r   = cur_vol / (avg_vol + 1e-10)

            # ATR-proxy (price range)
            p_range = float((high - low).rolling(14).mean().iloc[-1]) if len(high) else 0

            return {
                'rsi':             round(rsi, 2),
                'rsi_signal':      'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral',
                'macd':            round(c_macd, 4),
                'macd_signal':     round(c_sig, 4),
                'macd_hist':       round(c_hist, 4),
                'macd_bullish':    c_macd > c_sig,
                'ma20':            round(ma20, 2),
                'ma50':            round(ma50, 2),
                'ma200':           round(ma200, 2),
                'price_vs_ma20':   round((cur - ma20)  / ma20  * 100, 2),
                'price_vs_ma50':   round((cur - ma50)  / ma50  * 100, 2),
                'price_vs_ma200':  round((cur - ma200) / ma200 * 100, 2),
                'bb_upper':        round(bb_up, 2),
                'bb_lower':        round(bb_dn, 2),
                'bb_position':     round(bb_pos, 1),
                'volume_ratio':    round(vol_r, 2),
                'avg_volume_20d':  int(avg_vol),
                'trend':           'bullish' if cur > ma200 else 'bearish',
                'momentum':        'positive' if cur > ma50 else 'negative',
                'price_range_14d': round(p_range, 2),
            }
        except Exception:
            return {}

    # ── History ────────────────────────────────────────────────────────────────

    async def get_history(self, ticker: str, period: str = '6mo') -> list:
        ck = f"hist_{ticker}_{period}"
        if ck in _history_cache:
            return _history_cache[ck]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self._fetch_history, ticker, period)
        _history_cache[ck] = result
        return result

    def _fetch_history(self, ticker: str, period: str = '6mo') -> list:
        days    = PERIOD_DAYS.get(period, 210)
        symbol  = ticker.replace('.NS', '').replace('.BO', '')

        # Primary: Yahoo Finance via yfinance
        result = self._history_yfinance(ticker, period)
        if result and len(result) >= 5:
            return result

        # Fallback: Twelve Data API
        result = self._history_twelvedata(symbol, days)
        if result and len(result) >= 5:
            return result

        # Fallback: NSE historical API
        to_dt   = datetime.now()
        from_dt = to_dt - timedelta(days=days)
        result = self._history_nse(symbol, from_dt, to_dt)
        if result and len(result) >= 5:
            return result

        return []

    def _history_yfinance(self, ticker: str, period: str) -> list:
        try:
            t = yf.Ticker(ticker)
            df = t.history(period=period, auto_adjust=False)
            if df is None or df.empty:
                return []
            result = []
            for idx, row in df.iterrows():
                try:
                    result.append({
                        'date':   idx.strftime('%Y-%m-%d'),
                        'open':   round(float(row['Open']), 2),
                        'high':   round(float(row['High']), 2),
                        'low':    round(float(row['Low']), 2),
                        'close':  round(float(row['Close']), 2),
                        'volume': int(row['Volume']),
                    })
                except Exception:
                    continue
            return result
        except Exception:
            return []

    def _history_nse(self, symbol: str,
                     from_dt: datetime, to_dt: datetime) -> list:
        try:
            sess = get_session()
            # Warm-up: visit the equity quote page so NSE grants historical access
            try:
                sess.get(
                    f'{NSE_BASE}/get-quotes/equity',
                    params={'symbol': symbol},
                    timeout=8,
                )
                time.sleep(0.2)
            except Exception:
                pass

            resp = sess.get(
                f'{NSE_BASE}/api/historical/cm/equity',
                params={
                    'symbol': symbol,
                    'series': '["EQ"]',
                    'from':   from_dt.strftime('%d-%m-%Y'),
                    'to':     to_dt.strftime('%d-%m-%Y'),
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return []
            try:
                data = resp.json()
            except Exception:
                return []

            rows = data.get('data', [])
            if not rows:
                return []

            result = []
            for row in reversed(rows):   # NSE returns newest-first
                ts = str(row.get('CH_TIMESTAMP', ''))[:10]
                if not ts:
                    continue
                try:
                    result.append({
                        'date':   ts,
                        'open':   round(float(row.get('CH_OPENING_PRICE')  or 0), 2),
                        'high':   round(float(row.get('CH_TRADE_HIGH_PRICE') or 0), 2),
                        'low':    round(float(row.get('CH_TRADE_LOW_PRICE')  or 0), 2),
                        'close':  round(float(row.get('CH_CLOSING_PRICE')   or 0), 2),
                        'volume': int(row.get('CH_TOT_TRADED_QTY') or 0),
                    })
                except Exception:
                    continue
            return result
        except Exception:
            return []

    # ── Yearly Performance ─────────────────────────────────────────────────────

    async def get_yearly_performance(self, ticker: str) -> list:
        ck = f"yearly_{ticker}"
        if ck in _history_cache:
            return _history_cache[ck]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self._calc_yearly, ticker)
        _history_cache[ck] = result
        return result

    def _calc_yearly(self, ticker: str) -> list:
        try:
            t = yf.Ticker(ticker)
            df = t.history(period='max', auto_adjust=True)
            if df is None or df.empty:
                return []

            # Normalise index to timezone-naive midnight
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()

            today = pd.Timestamp.now().normalize()

            # Indian FY: April 1 → March 31; FY year = year of March 31
            # e.g. FY2025 = Apr 1 2024 – Mar 31 2025
            current_fy = today.year + 1 if today.month >= 4 else today.year

            results = []
            for fy in range(current_fy - 10, current_fy + 1):
                fy_start = pd.Timestamp(fy - 1, 4, 1)
                fy_end_natural = pd.Timestamp(fy, 3, 31)
                is_partial = fy_end_natural > today
                fy_end = today if is_partial else fy_end_natural

                mask = (df.index >= fy_start) & (df.index <= fy_end)
                period_df = df.loc[mask]

                if len(period_df) < 5:
                    continue

                start_price = float(period_df['Close'].iloc[0])
                end_price   = float(period_df['Close'].iloc[-1])
                if start_price <= 0:
                    continue

                return_pct = round((end_price - start_price) / start_price * 100, 1)
                results.append({
                    'fy':          f'FY{fy}' + (' YTD' if is_partial else ''),
                    'fy_year':     fy,
                    'return_pct':  return_pct,
                    'start_price': round(start_price, 2),
                    'end_price':   round(end_price, 2),
                    'is_partial':  is_partial,
                })

            return results
        except Exception:
            return []

    TWELVEDATA_KEY = os.getenv('TWELVEDATA_KEY', '3a0890ff4a5b47079d3ccab4a68d47fd')

    def _fetch_quote_twelvedata(self, ticker: str, symbol: str, exchange: str) -> Optional[dict]:
        """Fetch quote from Twelve Data API."""
        try:
            tw_exchange = 'NSE' if exchange == 'NSE' else 'BSE'
            resp = requests.get(
                'https://api.twelvedata.com/quote',
                params={
                    'symbol':   symbol,
                    'exchange': tw_exchange,
                    'apikey':   self.TWELVEDATA_KEY,
                },
                timeout=12,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get('status') == 'error':
                return None

            price = float(data.get('close') or 0)
            if not price:
                return None
            prev = float(data.get('previous_close') or price)
            change = round(price - prev, 2)
            change_pct = round(float(data.get('percent_change') or 0), 2)

            fifty_two = data.get('fifty_two_week') or {}

            return {
                'ticker':       ticker,
                'name':         str(data.get('name') or symbol),
                'price':        round(price, 2),
                'change':       change,
                'change_pct':   change_pct,
                'volume':       int(float(data.get('volume') or 0)),
                'avg_volume':   int(float(data.get('average_volume') or 0)),
                'market_cap':   0,
                'week_52_high': float(fifty_two.get('high') or price),
                'week_52_low':  float(fifty_two.get('low') or price),
                'day_high':     float(data.get('high') or price),
                'day_low':      float(data.get('low') or price),
                'open':         float(data.get('open') or price),
                'currency':     str(data.get('currency') or 'INR'),
                'exchange':     exchange,
                'sector':       '',
                'industry':     '',
                'website':      '',
                'description':  '',
            }
        except Exception:
            return None

    def _history_twelvedata(self, symbol: str, days: int) -> list:
        """Fetch daily OHLCV from Twelve Data API."""
        try:
            outputsize = min(days, 5000)
            resp = requests.get(
                'https://api.twelvedata.com/time_series',
                params={
                    'symbol':     symbol,
                    'exchange':   'NSE',
                    'interval':   '1day',
                    'outputsize': outputsize,
                    'apikey':     self.TWELVEDATA_KEY,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            if data.get('status') == 'error':
                return []

            values = data.get('values', [])
            if not values:
                return []

            result = []
            for row in reversed(values):  # oldest first
                try:
                    result.append({
                        'date':   row['datetime'][:10],
                        'open':   round(float(row.get('open', 0)), 2),
                        'high':   round(float(row.get('high', 0)), 2),
                        'low':    round(float(row.get('low', 0)), 2),
                        'close':  round(float(row.get('close', 0)), 2),
                        'volume': int(float(row.get('volume', 0))),
                    })
                except Exception:
                    continue
            return result
        except Exception:
            return []

    # ── Market Overview ────────────────────────────────────────────────────────

    async def get_market_overview(self) -> list:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._fetch_market_overview)

    def _fetch_market_overview(self) -> list:
        # Primary: Yahoo Finance indices
        INDICES_YF = [
            ('^NSEI',     'NIFTY 50'),
            ('^NSEBANK',  'NIFTY BANK'),
            ('^CNXIT',    'NIFTY IT'),
            ('^NSMIDCP',  'NIFTY MIDCAP 50'),
            ('^INDIAVIX', 'INDIA VIX'),
        ]
        results = []
        for yf_sym, label in INDICES_YF:
            try:
                t = yf.Ticker(yf_sym)
                fi = t.fast_info
                last = float(fi.last_price or 0)
                prev = float(fi.previous_close or last)
                if not last:
                    continue
                chg = round(last - prev, 2)
                chg_pct = round((chg / prev * 100) if prev else 0, 2)
                results.append({
                    'ticker':       label,
                    'name':         label,
                    'index_name':   label,
                    'price':        round(last, 2),
                    'change':       chg,
                    'change_pct':   chg_pct,
                    'open':         float(fi.open or last),
                    'day_high':     float(fi.day_high or last),
                    'day_low':      float(fi.day_low or last),
                    'week_52_high': float(fi.year_high or last),
                    'week_52_low':  float(fi.year_low or last),
                    'volume':       0,
                    'market_cap':   0,
                    'currency':     'INR',
                    'exchange':     'NSE',
                    'sector':       '',
                    'industry':     '',
                    'pe':           0.0,
                })
            except Exception:
                continue

        if results:
            return results

        # Fallback: NSE
        try:
            sess = get_session()
            resp = sess.get(f'{NSE_BASE}/api/allIndices', timeout=12)
            if resp.status_code != 200:
                return []
            try:
                data = resp.json()
            except Exception:
                return []

            items = data.get('data', [])
            WANT  = ['NIFTY 50', 'NIFTY BANK', 'NIFTY IT',
                     'NIFTY MIDCAP 50', 'INDIA VIX']

            results = []
            for target in WANT:
                for item in items:
                    if item.get('index', '').upper() == target.upper():
                        last    = float(item.get('last') or item.get('lastPrice') or 0)
                        prev    = float(item.get('previousClose') or last)
                        chg     = float(item.get('change')
                                        or round(last - prev, 2))
                        chg_pct = float(item.get('percentChange')
                                        or (round(chg / prev * 100, 2) if prev else 0))
                        results.append({
                            'ticker':       target,
                            'name':         item.get('index', target),
                            'index_name':   item.get('index', target),
                            'price':        round(last, 2),
                            'change':       round(chg, 2),
                            'change_pct':   round(chg_pct, 2),
                            'open':         float(item.get('open') or last),
                            'day_high':     float(item.get('high') or last),
                            'day_low':      float(item.get('low') or last),
                            'week_52_high': float(item.get('yearHigh') or last),
                            'week_52_low':  float(item.get('yearLow') or last),
                            'volume':       0,
                            'market_cap':   0,
                            'currency':     'INR',
                            'exchange':     'NSE',
                            'sector':       '',
                            'industry':     '',
                            'pe':           float(item.get('pe') or 0),
                        })
                        break
            return results
        except Exception:
            return []

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _sf(self, val, default: float = 0.0) -> float:
        """Safe float conversion."""
        try:
            if val is None:
                return default
            f = float(val)
            return default if (f != f) else f   # NaN check
        except Exception:
            return default
