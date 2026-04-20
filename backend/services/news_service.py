import asyncio
from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
from typing import Optional
import re

from services.nse_client import get_session

_news_cache = TTLCache(maxsize=200, ttl=1800)
_analyzer = SentimentIntensityAnalyzer()

FINANCE_LEXICON = {
    'downgrade': -2.5, 'upgrade': 2.5, 'beat': 2.0, 'miss': -2.0,
    'outperform': 2.0, 'underperform': -2.0, 'buyback': 2.0,
    'dividend': 2.0, 'default': -3.0, 'fraud': -4.0, 'acquisition': 1.5,
    'merger': 1.5, 'revenue': 0.5, 'profit': 2.0, 'loss': -2.0,
    'growth': 1.5, 'decline': -1.5, 'rally': 2.0, 'crash': -3.0,
    'surge': 2.0, 'plunge': -2.5, 'soar': 2.5, 'tumble': -2.5,
    'strong': 1.5, 'weak': -1.5, 'robust': 1.5, 'disappointing': -2.0,
    'record': 1.5, 'deal': 1.5, 'contract': 1.2, 'partnership': 1.5,
    'wins': 1.5, 'launches': 1.0, 'expands': 1.2, 'layoffs': -2.0,
    'order': 1.0, 'allotment': 0.5, 'board': 0.3, 'esop': 0.5,
    'results': 1.0, 'financial': 0.3, 'quarterly': 0.3,
}
for word, score in FINANCE_LEXICON.items():
    _analyzer.lexicon[word] = score

# Impact priority for announcement types
ANNOUNCEMENT_IMPACT = {
    'Outcome of Board Meeting': 'high',
    'Financial Results': 'high',
    'Dividend': 'high',
    'Buyback': 'high',
    'Acquisition': 'high',
    'Merger': 'high',
    'Analysts/Institutional Investor Meet/Con. Call Updates': 'high',
    'Allotment of Securities': 'medium',
    'ESOP/ESOS/ESPS': 'medium',
    'Copy of Newspaper Publication': 'medium',
    'Updates': 'medium',
    'General Updates': 'medium',
    'Post Buyback Public Announcement': 'high',
    'Change in Directors/ Key Managerial Personnel/ Auditor/ Compliance Officer/Share Transfer Agent': 'medium',
    'Disclosure under SEBI Takeover Regulations': 'low',
    'Certificate under SEBI (Depositories and Participants) Regulations, 2018': 'low',
}


def _get_impact(desc: str) -> str:
    for key, impact in ANNOUNCEMENT_IMPACT.items():
        if key.lower() in desc.lower():
            return impact
    return 'low'


class NewsService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=8)

    async def get_news(self, company_name: str, ticker: str, sector: str = '') -> list:
        cache_key = f"news_{ticker}"
        if cache_key in _news_cache:
            return _news_cache[cache_key]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self._fetch_and_analyze_news, company_name, ticker, sector
        )
        _news_cache[cache_key] = result
        return result

    def _fetch_and_analyze_news(self, company_name: str, ticker: str, sector: str = '') -> list:
        base_ticker = ticker.replace('.NS', '').replace('.BO', '')
        articles = []

        try:
            sess = get_session()
            resp = sess.get(
                f'https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={base_ticker}',
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                articles = self._parse_announcements(data, company_name, base_ticker)
        except Exception:
            pass

        return articles

    def _parse_announcements(self, data: list, company_name: str, ticker: str) -> list:
        articles = []
        seen = set()

        for item in data:
            desc = item.get('desc', '').strip()
            text = item.get('attchmntText', '').strip()
            sort_date = item.get('sort_date', '')
            an_dt = item.get('an_dt', '')
            attach_url = item.get('attchmntFile', '')

            if not desc:
                continue

            # Build a meaningful title from the description + text
            if text and len(text) > 10:
                # Use the attchmntText as the headline (it's already a real sentence)
                title = text[:150].rstrip('.')
                if len(text) > 150:
                    title += '...'
            else:
                title = f"{company_name}: {desc}"

            # Deduplicate
            norm = re.sub(r'[^a-z0-9]', '', title.lower())[:80]
            if norm in seen:
                continue
            seen.add(norm)

            # Parse date
            pub_date = self._parse_nse_date(sort_date)
            if pub_date and (datetime.now() - pub_date).days > 30:
                continue

            # Sentiment on title + full text
            sentiment_text = f"{title}. {text[:300]}"
            scores = _analyzer.polarity_scores(sentiment_text)
            compound = scores['compound']
            sentiment = ('positive' if compound >= 0.05
                         else 'negative' if compound <= -0.05
                         else 'neutral')

            impact = _get_impact(desc)

            articles.append({
                'title': title,
                'url': attach_url or f'https://www.nseindia.com/companies-listing/corporate-filings-announcements',
                'source': 'NSE India',
                'published': pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                'published_relative': self._relative_time(pub_date),
                'summary': text[:300] if text else desc,
                'sentiment': sentiment,
                'sentiment_score': round(compound, 3),
                'sentiment_details': {
                    'positive': round(scores['pos'], 3),
                    'negative': round(scores['neg'], 3),
                    'neutral':  round(scores['neu'], 3),
                },
                'impact': impact,
                'category': desc,
            })

            if len(articles) >= 30:
                break

        # Sort: high impact first, then most recent
        articles.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['impact']])
        return articles[:15]

    def _parse_nse_date(self, sort_date: str) -> Optional[datetime]:
        # Format: "2026-04-10 11:42:48"
        try:
            return datetime.strptime(sort_date, '%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        return datetime.now()

    def _relative_time(self, dt: Optional[datetime]) -> str:
        if not dt:
            return "Recently"
        diff = datetime.now() - dt
        if diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() // 60)
            return f"{mins}m ago" if mins > 0 else "Just now"
        if diff.days == 0:
            return f"{int(diff.total_seconds() // 3600)}h ago"
        if diff.days == 1:
            return "Yesterday"
        return f"{diff.days}d ago"

    def get_aggregate_sentiment(self, articles: list) -> dict:
        if not articles:
            return {'label': 'neutral', 'score': 0.5, 'positive': 0, 'negative': 0, 'neutral': 0}
        scores = [a['sentiment_score'] for a in articles]
        avg = sum(scores) / len(scores)
        pos = sum(1 for a in articles if a['sentiment'] == 'positive')
        neg = sum(1 for a in articles if a['sentiment'] == 'negative')
        neu = sum(1 for a in articles if a['sentiment'] == 'neutral')
        label = 'positive' if avg >= 0.05 else 'negative' if avg <= -0.05 else 'neutral'
        return {
            'label': label,
            'score': round((avg + 1) / 2, 3),
            'avg_compound': round(avg, 3),
            'positive': pos, 'negative': neg, 'neutral': neu,
            'total': len(articles),
        }
