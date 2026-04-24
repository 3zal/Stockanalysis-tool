import asyncio
from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache
import yfinance as yf

from services.nse_client import get_session, NSE_BASE

_comp_cache = TTLCache(maxsize=100, ttl=3600)

# Sector → competitor map (NSE base symbols, no suffix)
SECTOR_PEERS = {
    'Technology':             ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'MPHASIS'],
    'Financial Services':     ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN', 'INDUSINDBK', 'BANKBARODA'],
    'Consumer Cyclical':      ['TITAN', 'BAJAJFINSV', 'MARUTI', 'TMPV', 'M&M', 'EICHERMOT'],
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
    # IT
    'Software': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'MPHASIS', 'PERSISTENT', 'COFORGE'],
    'Information Technology Services': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM'],
    # Banking & Finance
    'Banks': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN', 'INDUSINDBK'],
    'Banks—Regional': ['SBIN', 'BANKBARODA', 'PNB', 'CANBK', 'UNIONBANK'],
    'Capital Markets': ['BAJFINANCE', 'BAJAJFINSV', 'CHOLAFIN', 'MUTHOOTFIN', 'M&MFIN'],
    'Insurance': ['HDFCLIFE', 'SBILIFE', 'ICICIPRULI', 'ICICIGI', 'MAXFIN'],
    'NBFC': ['BAJFINANCE', 'CHOLAFIN', 'MUTHOOTFIN', 'M&MFIN', 'LICHSGFIN'],
    # Auto
    'Auto Manufacturers': ['MARUTI', 'TMPV', 'M&M', 'EICHERMOT', 'TVSMOTOR', 'BAJAJ-AUTO', 'HEROMOTOCO'],
    'Auto Parts': ['BOSCHLTD', 'MOTHERSON', 'BHARATFORG', 'BALKRISIND', 'EXIDEIND', 'MRF', 'APOLLOTYRE'],
    'Two-Wheelers': ['BAJAJ-AUTO', 'HEROMOTOCO', 'TVSMOTOR', 'EICHERMOT'],
    # Pharma & Healthcare
    'Drug Manufacturers': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'DIVISLAB', 'TORNTPHARM', 'AUROPHARMA'],
    'Healthcare': ['APOLLOHOSP', 'MAXHEALTH', 'FORTIS', 'NH', 'METROPOLIS'],
    # FMCG
    'Packaged Foods': ['NESTLEIND', 'BRITANNIA', 'TATACONSUM', 'VARUN', 'HINDUNILVR'],
    'Personal Products': ['HINDUNILVR', 'DABUR', 'MARICO', 'COLPAL', 'GODREJCP', 'EMAMILTD'],
    'Tobacco': ['ITC', 'GODFRYPHLP', 'VST'],
    'Beverages': ['VBL', 'UBL', 'TATACONSUM'],
    # Cement & Building Materials
    'Cement': ['ULTRACEMCO', 'SHREECEM', 'AMBUJACEM', 'ACC', 'DALBHARAT', 'JKCEMENT', 'RAMCOCEM'],
    'Building Materials': ['ULTRACEMCO', 'AMBUJACEM', 'PIDILITIND', 'KAJARIACER', 'CENTURYPLY'],
    'Construction Materials': ['ULTRACEMCO', 'SHREECEM', 'AMBUJACEM', 'ACC', 'JKCEMENT'],
    # Paints
    'Paints': ['ASIANPAINT', 'BERGEPAINT', 'KANSAINER', 'AKZOINDIA', 'INDIGOPNTS'],
    # Metals & Mining
    'Steel': ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'JINDALSTEL', 'NMDC'],
    'Aluminum': ['HINDALCO', 'NALCO', 'VEDL'],
    'Copper': ['HINDCOPPER', 'VEDL', 'HINDALCO'],
    'Mining': ['COALINDIA', 'NMDC', 'VEDL', 'HINDZINC'],
    # Energy
    'Oil & Gas': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'GAIL', 'OIL', 'PETRONET'],
    'Refining': ['RELIANCE', 'BPCL', 'IOC', 'HINDPETRO'],
    'Power': ['NTPC', 'POWERGRID', 'TATAPOWER', 'ADANIPOWER', 'JSWENERGY', 'NHPC'],
    'Renewable Energy': ['ADANIGREEN', 'TATAPOWER', 'JSWENERGY', 'NHPC', 'SJVN'],
    # Capital Goods & Industrials
    'Capital Goods': ['LT', 'SIEMENS', 'ABB', 'BHEL', 'CUMMINSIND', 'THERMAX', 'HAVELLS'],
    'Aerospace & Defense': ['HAL', 'BEL', 'BDL', 'COCHINSHIP', 'MAZAGON'],
    'Engineering': ['LT', 'SIEMENS', 'ABB', 'BHEL', 'CUMMINSIND'],
    # Retail & Consumer
    'Specialty Retail': ['DMART', 'TRENT', 'TITAN', 'ADITYA BIRLA FASHION', 'SHOPERSTOP'],
    'Discount Stores': ['DMART', 'TRENT', 'VMART'],
    'Restaurants': ['JUBLFOOD', 'WESTLIFE', 'DEVYANI', 'SAPPHIRE'],
    # Telecom
    'Telecom': ['BHARTIARTL', 'IDEA', 'TATACOMM', 'INDUSTOWER'],
    # Real Estate
    'Real Estate': ['DLF', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE', 'BRIGADE', 'PHOENIXLTD'],
    # Specialty Chemicals
    'Specialty Chemicals': ['PIDILITIND', 'SRF', 'AARTIIND', 'PIIND', 'GUJFLUORO', 'DEEPAKNTR'],
    'Chemicals': ['PIDILITIND', 'SRF', 'AARTIIND', 'TATACHEM', 'GHCL'],
    'Fertilizers': ['COROMANDEL', 'CHAMBLFERT', 'GNFC', 'RCF', 'NFL'],
    # Logistics & Transport
    'Logistics': ['ADANIPORTS', 'CONCOR', 'BLUEDART', 'TCI', 'GATI'],
    'Airlines': ['INDIGO', 'SPICEJET'],
    'Shipping': ['SCI', 'GESHIP', 'COCHINSHIP'],
    # Hospitality
    'Hotels': ['INDHOTEL', 'EIHOTEL', 'CHALET', 'LEMONTREE'],
    # Media
    'Media': ['ZEEL', 'SUNTV', 'PVRINOX', 'TV18BRDCST'],
    # Textiles
    'Textiles': ['PAGEIND', 'TRIDENT', 'WELSPUNIND', 'RAYMOND', 'KPR'],
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
        industry_l = (industry or '').lower().strip()
        sector_l = (sector or '').lower().strip()

        # Industry-level: bidirectional substring match
        if industry_l:
            for key, peers in INDUSTRY_PEERS.items():
                key_l = key.lower()
                if industry_l in key_l or key_l in industry_l:
                    filtered = [p for p in peers if p != base]
                    if filtered:
                        return filtered[:5]

        # Sector-level: same bidirectional match
        if sector_l:
            for key, peers in SECTOR_PEERS.items():
                key_l = key.lower()
                if sector_l in key_l or key_l in sector_l:
                    filtered = [p for p in peers if p != base]
                    if filtered:
                        return filtered[:5]

        # Default bluechips
        defaults = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
        return [p for p in defaults if p != base][:5]

    def _fetch_peer(self, symbol: str) -> dict:
        """Fetch basic metrics for a peer using yfinance."""
        try:
            ticker = f'{symbol}.NS'
            t = yf.Ticker(ticker)
            fi = t.fast_info
            price = float(fi.last_price or 0)
            if not price:
                return {}

            prev = float(fi.previous_close or price)
            change = round(price - prev, 2)
            chg_pct = round((change / prev * 100) if prev else 0, 2)

            info = {}
            try:
                info = t.info or {}
            except Exception:
                pass

            name = info.get('longName') or info.get('shortName') or symbol
            market_cap = int(info.get('marketCap') or 0)
            pe = float(info.get('trailingPE') or 0)
            pb = float(info.get('priceToBook') or 0)
            roe = float(info.get('returnOnEquity') or 0)
            margin = float(info.get('profitMargins') or 0)
            rev_growth = float(info.get('revenueGrowth') or 0)
            beta = float(info.get('beta') or 1.0)

            # P/B fallback: derive from bookValue if priceToBook missing
            if not pb:
                book = float(info.get('bookValue') or 0)
                if book and price:
                    pb = round(price / book, 2)

            return {
                'ticker':         ticker,
                'name':           str(name),
                'price':          round(price, 2),
                'change_pct':     chg_pct,
                'market_cap':     market_cap,
                'pe_ratio':       round(pe, 1),
                'price_to_book':  round(pb, 2),
                'roe':            round(roe, 4),
                'profit_margin':  round(margin, 4),
                'revenue_growth': round(rev_growth, 4),
                'week_52_high':   float(getattr(fi, 'year_high', 0) or price),
                'week_52_low':    float(getattr(fi, 'year_low', 0) or price),
                'beta':           round(beta, 2),
            }
        except Exception:
            return {}
