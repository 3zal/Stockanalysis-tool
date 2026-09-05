from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional
import asyncio
import json
import logging
import math
import os
import re
import threading
import time
from collections import deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from database import Database
from services.stock_service import StockService
from services.news_service import NewsService
from services.scoring_service import ScoringService
from services.competitor_service import CompetitorService
from services.analyst_service import AnalystService
from services.macro_service import MacroService


TICKER_ALIASES = {
    "TATAMOTORS": "TMPV",
}


def _resolve_alias(ticker: str) -> str:
    base = ticker.replace(".NS", "").replace(".BO", "")
    return TICKER_ALIASES.get(base, base)


def _sanitize(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return value


class SafeJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            _sanitize(content),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")


logger = logging.getLogger("investr")

app = FastAPI(
    title="investr.info API",
    version="1.0.0",
    default_response_class=SafeJSONResponse,
    # Public read-only API; the interactive docs only advertised the surface to scanners.
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

_default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
_env_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
# Production sets CORS_ORIGINS; the localhost defaults are for a bare local run only.
_allowed_origins = _env_origins if _env_origins else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    # No cookies or sessions anywhere in this API, so nothing needs credentialed CORS.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
stock_svc = StockService()
news_svc = NewsService()
scoring_svc = ScoringService()
competitor_svc = CompetitorService()
analyst_svc = AnalystService()
macro_svc = MacroService()


# ── Abuse limits ──────────────────────────────────────────────────────────────
# Every /api/stocks/* call can cost seconds of upstream fetching (Yahoo → Twelve Data → NSE
# fallback chains). Without a limit a single client could pin the worker pools for everyone.
# Sliding one-minute window per client IP; in-process, which is enough for one replica.
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "240"))
_RATE_WINDOW_S = 60
_rate_hits: dict = {}
_rate_lock = threading.Lock()
_rate_last_sweep = 0.0


def _client_ip(request: Request) -> str:
    # Railway's edge proxy sets X-Forwarded-For; the left-most entry is the client.
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/stocks"):
            now = time.time()
            ip = _client_ip(request)
            with _rate_lock:
                global _rate_last_sweep
                if now - _rate_last_sweep > _RATE_WINDOW_S:
                    # Drop idle clients so the table cannot grow without bound.
                    for k in [k for k, q in _rate_hits.items() if not q or now - q[-1] > _RATE_WINDOW_S]:
                        _rate_hits.pop(k, None)
                    _rate_last_sweep = now
                q = _rate_hits.setdefault(ip, deque())
                while q and now - q[0] > _RATE_WINDOW_S:
                    q.popleft()
                if len(q) >= RATE_LIMIT_PER_MIN:
                    return SafeJSONResponse(
                        {"detail": "Too many requests. Try again in a minute."},
                        status_code=429,
                        headers={"Retry-After": "60"},
                    )
                q.append(now)
        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

# NSE/BSE symbols: letters, digits, '&' (M&M), '-' (BAJAJ-AUTO), optional exchange suffix.
_TICKER_RE = re.compile(r"^[A-Z0-9&\-]{1,20}(\.NS|\.BO)?$")


def _clean_ticker(raw: str) -> str:
    """Normalise a user-supplied ticker and refuse anything that is not shaped like one,
    before it can reach an upstream fetch or the database."""
    ticker = raw.upper().strip()
    if not _TICKER_RE.match(ticker):
        raise HTTPException(status_code=400, detail="Invalid ticker symbol.")
    suffix = ticker[-3:] if ticker.endswith((".NS", ".BO")) else ".NS"
    return _resolve_alias(ticker) + suffix


@app.on_event("startup")
async def startup():
    db.init_db()


@app.get("/health")
async def root_health(request: Request):
    body = {"status": "ok", "build": "yearly-v2"}
    # Operator aid: with DEBUG_FORWARDING=1 the caller sees the forwarding headers the edge
    # delivered for their own request (only their own IPs), to tune proxy trust settings.
    if os.getenv("DEBUG_FORWARDING") == "1":
        body["forwarding"] = {k: v for k, v in request.headers.items()
                              if k.startswith("x-forwarded") or k in ("x-real-ip", "x-envoy-external-address", "cf-connecting-ip", "true-client-ip")}
        body["client"] = request.client.host if request.client else None
    return body


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "investr.info", "build": "yearly-v2"}


@app.get("/api/stocks/search")
async def search_stocks(q: str = Query(..., min_length=1, max_length=64)):
    """Search stocks by name or ticker symbol"""
    results = await stock_svc.search_stocks(q)
    return {"results": results}


@app.get("/api/stocks/{ticker}")
async def get_stock_analysis(ticker: str):
    """Get comprehensive stock analysis"""
    ticker = _clean_ticker(ticker)

    try:
        # Fetch quote first to validate ticker
        quote = await stock_svc.get_quote(ticker)
        if not quote:
            # Try BSE fallback
            ticker_bo = ticker.replace(".NS", ".BO")
            quote = await stock_svc.get_quote(ticker_bo)
            if quote:
                ticker = ticker_bo
            else:
                raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found. Try adding .NS or .BO suffix.")

        # Fetch all data in parallel
        fundamentals, technicals, history, news, analyst, macro = await asyncio.gather(
            stock_svc.get_fundamentals(ticker),
            stock_svc.get_technicals(ticker),
            stock_svc.get_history(ticker),
            news_svc.get_news(quote.get("name", ticker), ticker, quote.get("sector", "")),
            analyst_svc.get_analyst_data(ticker, quote.get("price", 0)),
            macro_svc.get_macro_data(),
            return_exceptions=True,
        )

        # Sanitize exceptions
        if isinstance(fundamentals, Exception):
            fundamentals = {}
        if isinstance(technicals, Exception):
            technicals = {}
        if isinstance(history, Exception):
            history = []
        if isinstance(news, Exception):
            news = []
        if isinstance(analyst, Exception):
            analyst = None
        if isinstance(macro, Exception):
            macro = None

        # Calculate score
        score_data = scoring_svc.calculate_score(
            quote=quote,
            fundamentals=fundamentals,
            technicals=technicals,
            news=news,
            analyst=analyst,
            macro=macro,
        )

        # Get competitors (non-blocking)
        try:
            competitors = await competitor_svc.get_competitors(
                ticker, quote.get("sector", ""), quote.get("industry", "")
            )
        except Exception:
            competitors = []

        # Check watchlist status
        in_watchlist = db.is_in_watchlist(ticker)

        # Save to search history
        db.add_search_history(ticker, quote.get("name", ticker))

        return {
            "ticker": ticker,
            "quote": quote,
            "fundamentals": fundamentals,
            "technicals": technicals,
            "history": history,
            "news": news,
            "score": score_data,
            "competitors": competitors,
            "in_watchlist": in_watchlist,
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("analysis failed for %s", ticker)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")


@app.get("/api/stocks/{ticker}/yearly-performance")
async def get_yearly_performance(ticker: str):
    ticker = _clean_ticker(ticker)
    data = await stock_svc.get_yearly_performance(ticker)
    return {"yearly_performance": data}


@app.get("/api/stocks/{ticker}/history")
async def get_stock_history(ticker: str, period: str = "6mo"):
    ticker = _clean_ticker(ticker)
    valid_periods = ["1wk", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
    if period not in valid_periods:
        period = "6mo"
    history = await stock_svc.get_history(ticker, period)
    return {"history": history}


@app.get("/api/market/overview")
async def get_market_overview():
    """Get major Indian market indices"""
    indices = await stock_svc.get_market_overview()
    return {"indices": indices}


# Watchlist endpoints
@app.get("/api/watchlist")
async def get_watchlist():
    items = db.get_watchlist()
    return {"items": items}


class WatchlistItem(BaseModel):
    ticker: str = ""
    name: str = ""


# The watchlist table has no user column — it was one global list shared by every visitor, and
# these endpoints let anyone write to it. investr.info's own backend owns per-account watchlists
# now, so the writes are retired rather than hardened. GET stays for old clients (read-only).
_GONE = {"detail": "This endpoint has been retired. Watchlists live in the investr.info app backend."}


@app.post("/api/watchlist")
async def add_to_watchlist(item: WatchlistItem):
    return SafeJSONResponse(_GONE, status_code=410)


@app.delete("/api/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str):
    return SafeJSONResponse(_GONE, status_code=410)


# Search history endpoints
@app.get("/api/search-history")
async def get_search_history():
    items = db.get_search_history()
    return {"items": items}


@app.delete("/api/search-history")
async def clear_search_history():
    return SafeJSONResponse(_GONE, status_code=410)
