import asyncio
from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache

from services.nse_client import get_session, NSE_BASE

_comp_cache = TTLCache(maxsize=100, ttl=3600)

# Sector → competitor map (NSE base symbols, no suffix)
SECTOR_PEERS = {
    'Technology':             ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'MPHASIS'],
    'Financial Services':     ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN', 'INDUSINDBK', 'BANKBARODA'],
    'Consumer Cyclical':      ['TITAN', 'BAJAJFINSV', 'MARUTI', 'TATAMOTORS', 'M&M', 'EICHERMOT'],
    'Consumer Defensive':     ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'MARICO'],
    'Healthcare':             ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP', 'LUPIN'],
    'Energy':                 ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'NTPC', 'POWERGRID'],
    'Basic Materials':        ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'VEDL', 'COALINDIA', 'NMDC'],
    'Industrials':            ['LT', 'ULTRACEMCO', 'ADANIPORTS', 'SIEMENS', 'ABB', 'BHARTIARTL'],
    'Real Estate':            ['DLF', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE', 'BRIGADE'],
    'Communication Services': ['BHARTIARTL', 'RELIANCE', 'INDIAMART', 'IRCTC'],
    'Utilities':              ['NTPC', 'POWERGRID', 'TATAPOWER', 'ADANIGREEN', 'CESC'],
}

INDUSTRY_PEERS = {
    'Software—Application': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
    'Banks—Diversified':    ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'SBIN'],
    'Drug Manufacturers':   ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'DIVISLAB'],
    'Auto Manufacturers':   ['MARUTI', 'TATAMOTORS', 'M&M', 'EICHERMOT', 'BAJAJ-AUTO'],
    'Steel':                ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'HINDALCO', 'NMDC'],
    'Oil & Gas':            ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'GAIL'],
    'Telecom':              ['BHARTIARTL', 'IDEA', 'TATACOMM'],
}


class CompetitorService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=6)

    async def get_competitors(self, ticker: str, sector: str, industry: str) -> list:
        ck = f"comp_{ticker}"
        if ck in _comp_cache:
            return _comp_cache[ck]

        peers = self._peer_list(ticker, sector, industry)
        if not peers:
            return []

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self._fetch_peer, sym)
            for sym in peers[:5]
        ]
        raw = await asyncio.gather(*tasks, return_exceptions=True)

        result = [r for r in raw if isinstance(r, dict) and r][:5]
        _comp_cache[ck] = result
        return result

    def _peer_list(self, ticker: str, sector: str, industry: str) -> list:
        base = ticker.replace('.NS', '').replace('.BO', '')

        # Industry-level (more specific) first
        for key, peers in INDUSTRY_PEERS.items():
            if industry and industry.lower() in key.lower():
                return [p for p in peers if p != base][:5]

        # Sector-level fallback
        for key, peers in SECTOR_PEERS.items():
            if sector and key.lower() in sector.lower():
                return [p for p in peers if p != base][:5]

        # Default bluechips
        defaults = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
        return [p for p in defaults if p != base][:5]

    def _fetch_peer(self, symbol: str) -> dict:
        """Fetch basic metrics for a peer using the NSE quote endpoint."""
        try:
            sess = get_session()
            resp = sess.get(
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

            price_info = data.get('priceInfo', {})
            metadata   = data.get('metadata', {})
            info       = data.get('info', {})

            price = float(price_info.get('lastPrice') or 0)
            if not price:
                return {}

            prev      = float(price_info.get('previousClose') or price)
            change    = float(price_info.get('change') or round(price - prev, 2))
            chg_pct   = float(price_info.get('pChange')
                               or (round(change / prev * 100, 2) if prev else 0))
            week      = price_info.get('weekHighLow', {})
            name      = (info.get('companyName')
                         or metadata.get('companyName')
                         or symbol)
            pe        = float(metadata.get('pdSymbolPe') or 0)
            pb        = float(metadata.get('pdSectorPb')
                              or metadata.get('pdSymbolPb') or 0)

            return {
                'ticker':         f'{symbol}.NS',
                'name':           str(name),
                'price':          round(price, 2),
                'change_pct':     round(chg_pct, 2),
                'market_cap':     0,
                'pe_ratio':       round(pe, 1),
                'price_to_book':  round(pb, 2),
                'roe':            0.0,
                'profit_margin':  0.0,
                'revenue_growth': 0.0,
                'week_52_high':   float(week.get('max') or price),
                'week_52_low':    float(week.get('min') or price),
                'beta':           1.0,
            }
        except Exception:
            return {}
