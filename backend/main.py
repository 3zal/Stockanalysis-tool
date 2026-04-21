from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional
import asyncio
import json
import math
import os

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


app = FastAPI(
    title="investr.info API",
    version="1.0.0",
    default_response_class=SafeJSONResponse,
)

_default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
_env_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _env_origins,
    allow_credentials=True,
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


@app.on_event("startup")
async def startup():
    db.init_db()


@app.get("/health")
async def root_health():
    return {"status": "ok", "build": "yearly-v2"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "investr.info", "build": "yearly-v2"}


@app.get("/api/stocks/search")
async def search_stocks(q: str = Query(..., min_length=1)):
    """Search stocks by name or ticker symbol"""
    results = await stock_svc.search_stocks(q)
    return {"results": results}


@app.get("/api/stocks/{ticker}")
async def get_stock_analysis(ticker: str):
    """Get comprehensive stock analysis"""
    ticker = ticker.upper().strip()
    suffix = ticker[-3:] if ticker.endswith((".NS", ".BO")) else ".NS"
    ticker = _resolve_alias(ticker) + suffix

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/stocks/{ticker}/yearly-performance")
async def get_yearly_performance(ticker: str):
    ticker = ticker.upper().strip()
    suffix = ticker[-3:] if ticker.endswith((".NS", ".BO")) else ".NS"
    ticker = _resolve_alias(ticker) + suffix
    data = await stock_svc.get_yearly_performance(ticker)
    return {"yearly_performance": data}


@app.get("/api/stocks/{ticker}/history")
async def get_stock_history(ticker: str, period: str = "6mo"):
    ticker = ticker.upper()
    suffix = ticker[-3:] if ticker.endswith((".NS", ".BO")) else ".NS"
    ticker = _resolve_alias(ticker) + suffix
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
    ticker: str
    name: str


@app.post("/api/watchlist")
async def add_to_watchlist(item: WatchlistItem):
    db.add_to_watchlist(item.ticker.upper(), item.name)
    return {"success": True, "message": f"{item.ticker} added to watchlist"}


@app.delete("/api/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str):
    db.remove_from_watchlist(ticker.upper())
    return {"success": True, "message": f"{ticker} removed from watchlist"}


# Search history endpoints
@app.get("/api/search-history")
async def get_search_history():
    items = db.get_search_history()
    return {"items": items}


@app.delete("/api/search-history")
async def clear_search_history():
    db.clear_search_history()
    return {"success": True}
