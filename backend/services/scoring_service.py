import hashlib
import random
from typing import Optional


class ScoringService:
    """
    Weighted investment scoring system (0-100):
      Fundamentals     40%
      Technicals       25%
      News Sentiment   20%
      Market Sentiment 15%
    """

    def calculate_score(self, quote: dict, fundamentals: dict, technicals: dict, news: list) -> dict:
        fund_score = self._score_fundamentals(fundamentals, quote)
        tech_score = self._score_technicals(technicals)
        news_score = self._score_news_sentiment(news)
        market_score = self._score_market_sentiment(quote, technicals)

        weights = {
            'fundamentals': 0.40,
            'technicals': 0.25,
            'news_sentiment': 0.20,
            'market_sentiment': 0.15,
        }

        total = (
            fund_score * weights['fundamentals'] +
            tech_score * weights['technicals'] +
            news_score * weights['news_sentiment'] +
            market_score * weights['market_sentiment']
        )
        total = round(min(max(total, 1), 99), 1)

        if total >= 61:
            recommendation = 'BUY'
            rec_color = 'green'
        elif total >= 31:
            recommendation = 'HOLD'
            rec_color = 'amber'
        else:
            recommendation = 'SELL'
            rec_color = 'red'

        scores = [fund_score, tech_score, news_score, market_score]
        if recommendation == 'BUY':
            agreeing = sum(1 for s in scores if s >= 55)
        elif recommendation == 'SELL':
            agreeing = sum(1 for s in scores if s <= 45)
        else:
            agreeing = sum(1 for s in scores if 35 <= s <= 65)

        confidence = round(40 + (agreeing / 4) * 55)

        reasoning = self._generate_reasoning(
            total, fund_score, tech_score, news_score,
            market_score, fundamentals, technicals, news, quote
        )

        return {
            'total': total,
            'recommendation': recommendation,
            'rec_color': rec_color,
            'confidence': confidence,
            'reasoning': reasoning,
            'components': {
                'fundamentals': {
                    'score': round(fund_score, 1),
                    'weight': weights['fundamentals'],
                    'label': 'Fundamentals',
                    'details': self._fundamentals_details(fundamentals),
                },
                'technicals': {
                    'score': round(tech_score, 1),
                    'weight': weights['technicals'],
                    'label': 'Technicals',
                    'details': self._technicals_details(technicals),
                },
                'news_sentiment': {
                    'score': round(news_score, 1),
                    'weight': weights['news_sentiment'],
                    'label': 'News Sentiment',
                    'details': self._news_details(news),
                },
                'market_sentiment': {
                    'score': round(market_score, 1),
                    'weight': weights['market_sentiment'],
                    'label': 'Market Sentiment',
                    'details': self._market_sentiment_details(quote, technicals),
                },
            },
        }

    def _score_fundamentals(self, f: dict, q: dict) -> float:
        if not f:
            return 50.0

        score = 50.0
        adjustments = 0
        count = 0

        # P/E Ratio (lower is better, but negative is bad)
        pe = f.get('pe_ratio') or 0
        if pe and pe > 0:
            if pe < 10:
                score += 15
            elif pe < 20:
                score += 10
            elif pe < 30:
                score += 3
            elif pe < 50:
                score -= 5
            else:
                score -= 15
            count += 1

        # ROE (higher is better)
        roe = f.get('roe') or 0
        if roe:
            if roe > 0.25:
                score += 12
            elif roe > 0.15:
                score += 7
            elif roe > 0.08:
                score += 2
            elif roe > 0:
                score -= 3
            else:
                score -= 10
            count += 1

        # Debt to Equity (lower is better)
        de = f.get('debt_to_equity') or 0
        if de >= 0:
            if de < 30:
                score += 8
            elif de < 80:
                score += 3
            elif de < 150:
                score -= 3
            else:
                score -= 10
            count += 1

        # EPS Growth (higher is better)
        eps_growth = f.get('eps_growth') or 0
        if eps_growth:
            if eps_growth > 0.25:
                score += 12
            elif eps_growth > 0.10:
                score += 7
            elif eps_growth > 0:
                score += 2
            else:
                score -= 8
            count += 1

        # Profit Margin
        pm = f.get('profit_margin') or 0
        if pm:
            if pm > 0.20:
                score += 8
            elif pm > 0.10:
                score += 4
            elif pm > 0:
                score += 1
            else:
                score -= 8
            count += 1

        # Current Ratio (liquidity)
        cr = f.get('current_ratio') or 0
        if cr:
            if cr >= 1.5:
                score += 5
            elif cr >= 1.0:
                score += 2
            else:
                score -= 5
            count += 1

        return round(min(max(score, 5), 95), 1)

    def _score_technicals(self, t: dict) -> float:
        if not t:
            return 50.0

        score = 50.0

        # RSI
        rsi = t.get('rsi', 50)
        if rsi < 30:          # Oversold → buy signal
            score += 18
        elif rsi < 45:
            score += 8
        elif rsi <= 60:
            score += 2
        elif rsi <= 70:
            score -= 5
        else:                  # Overbought → sell signal
            score -= 15

        # MACD
        if t.get('macd_bullish', False):
            score += 12
        else:
            score -= 8

        macd_hist = t.get('macd_hist', 0)
        if macd_hist > 0:
            score += 5
        else:
            score -= 5

        # Price vs MA200 (trend)
        vs_ma200 = t.get('price_vs_ma200', 0)
        if vs_ma200 > 5:
            score += 10
        elif vs_ma200 > 0:
            score += 5
        elif vs_ma200 > -5:
            score -= 3
        else:
            score -= 10

        # Price vs MA50 (momentum)
        vs_ma50 = t.get('price_vs_ma50', 0)
        if vs_ma50 > 3:
            score += 5
        elif vs_ma50 > 0:
            score += 2
        else:
            score -= 5

        # Bollinger Band position
        bb_pos = t.get('bb_position', 50)
        if bb_pos < 20:        # Near lower band → potential bounce
            score += 8
        elif bb_pos > 80:      # Near upper band → potential resistance
            score -= 5

        # Volume confirmation
        vol_ratio = t.get('volume_ratio', 1)
        if vol_ratio > 1.5:    # High volume confirms trend
            score += 3

        return round(min(max(score, 5), 95), 1)

    def _score_news_sentiment(self, news: list) -> float:
        if not news:
            return 50.0

        # Weight recent articles more
        total_weight = 0
        weighted_score = 0
        for i, article in enumerate(news[:8]):
            weight = 1 / (i + 1)  # More recent = higher weight
            compound = article.get('sentiment_score', 0)
            normalized = (compound + 1) / 2 * 100  # -1..1 → 0..100

            # High-impact articles count more
            if article.get('impact') == 'high':
                weight *= 1.5

            weighted_score += normalized * weight
            total_weight += weight

        if total_weight == 0:
            return 50.0

        return round(min(max(weighted_score / total_weight, 5), 95), 1)

    def _generate_analyst_consensus(self, quote: dict, fundamentals: dict) -> dict:
        """Generate deterministic analyst consensus seeded by ticker"""
        ticker = quote.get('ticker', 'STOCK')
        seed = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Base bias from fundamentals
        pe = fundamentals.get('pe_ratio') or 25
        roe = fundamentals.get('roe') or 0.12
        growth = fundamentals.get('eps_growth') or 0.08

        # Calculate fundamental bias
        if pe < 15 and roe > 0.15:
            buy_bias = 0.70
        elif pe < 25 and roe > 0.10:
            buy_bias = 0.58
        elif pe > 40 or roe < 0:
            buy_bias = 0.30
        else:
            buy_bias = 0.50

        # Add some randomness (±15%)
        buy_bias = min(0.90, max(0.10, buy_bias + rng.uniform(-0.12, 0.12)))
        sell_bias = max(0.05, min(0.40, 1 - buy_bias - rng.uniform(0.15, 0.35)))
        hold_bias = max(0.05, 1 - buy_bias - sell_bias)

        # Analyst count
        num_analysts = rng.randint(18, 52)
        buy_count = round(buy_bias * num_analysts)
        sell_count = round(sell_bias * num_analysts)
        hold_count = num_analysts - buy_count - sell_count

        # Target price (±25% from current)
        current = quote.get('price', 100)
        upside_factor = 1 + rng.uniform(-0.05, 0.30)
        target_price = round(current * upside_factor, 2)
        upside_pct = round((target_price - current) / current * 100, 1)

        # Score based on consensus
        buy_pct = buy_count / num_analysts
        sell_pct = sell_count / num_analysts
        consensus_score = round(buy_pct * 100 - sell_pct * 40 + 30)
        consensus_score = min(max(consensus_score, 5), 95)

        consensus_label = 'Strong Buy' if buy_pct > 0.65 else 'Buy' if buy_pct > 0.50 else 'Hold' if hold_count > buy_count else 'Underperform'

        return {
            'score': consensus_score,
            'num_analysts': num_analysts,
            'buy': buy_count,
            'hold': hold_count,
            'sell': sell_count,
            'buy_pct': round(buy_pct * 100, 1),
            'hold_pct': round(hold_count / num_analysts * 100, 1),
            'sell_pct': round(sell_pct * 100, 1),
            'consensus': consensus_label,
            'target_price': target_price,
            'upside_pct': upside_pct,
            'high_target': round(target_price * 1.15, 2),
            'low_target': round(target_price * 0.88, 2),
        }

    def _score_market_sentiment(self, quote: dict, technicals: dict) -> float:
        score = 50.0

        # Price change momentum
        change_pct = quote.get('change_pct', 0)
        if change_pct > 3:
            score += 12
        elif change_pct > 1:
            score += 6
        elif change_pct < -3:
            score -= 12
        elif change_pct < -1:
            score -= 6

        # Volume momentum
        vol_ratio = technicals.get('volume_ratio', 1)
        if vol_ratio > 2 and change_pct > 0:
            score += 8  # High volume rally
        elif vol_ratio > 2 and change_pct < 0:
            score -= 8  # High volume selloff

        # Trend alignment
        if technicals.get('trend') == 'bullish':
            score += 8
        else:
            score -= 5

        # Position in 52-week range
        current = quote.get('price', 0)
        high_52 = quote.get('week_52_high', current)
        low_52 = quote.get('week_52_low', current)
        if high_52 > low_52:
            range_pct = (current - low_52) / (high_52 - low_52)
            if range_pct > 0.85:
                score += 5
            elif range_pct > 0.60:
                score += 3
            elif range_pct < 0.25:
                score -= 5

        return round(min(max(score, 5), 95), 1)

    def _score_macro(self) -> float:
        """
        Static macro score based on current Indian economic outlook.
        In production, this could fetch RBI/MOSPI data.
        """
        # India macro fundamentals as of 2025-2026:
        # - GDP growth ~6.5-7% (positive)
        # - Inflation moderating ~4-5% (neutral-positive)
        # - RBI rates stable/cutting cycle (positive)
        # - INR stable (neutral)
        # - Strong FII inflows (positive)
        return 62.0

    def _generate_reasoning(self, total, fund, tech, news, mkt,
                            fundamentals, technicals, news_list, quote) -> str:
        parts = []
        name = quote.get('name', 'This stock')

        # Fundamental assessment
        pe = fundamentals.get('pe_ratio') or 0
        roe = fundamentals.get('roe') or 0
        if fund >= 65:
            parts.append(f"strong fundamentals with an ROE of {roe*100:.1f}%" if roe else "strong fundamentals")
        elif fund <= 40:
            parts.append("weak fundamentals that warrant caution")
        else:
            parts.append("moderate fundamentals")

        # Technical assessment
        rsi = technicals.get('rsi', 50)
        if tech >= 65:
            parts.append(f"bullish technical setup (RSI: {rsi:.0f}, above key moving averages)")
        elif tech <= 40:
            parts.append(f"bearish technical indicators (RSI: {rsi:.0f})")
        else:
            parts.append(f"neutral technicals (RSI: {rsi:.0f})")

        # News sentiment
        if news_list:
            pos = sum(1 for n in news_list if n.get('sentiment') == 'positive')
            neg = sum(1 for n in news_list if n.get('sentiment') == 'negative')
            if pos > neg:
                parts.append("predominantly positive recent news coverage")
            elif neg > pos:
                parts.append("concerning negative news sentiment")
            else:
                parts.append("mixed news sentiment")

        rec = 'Buy' if total >= 61 else 'Hold' if total >= 31 else 'Sell'
        confidence = round(40 + (sum(1 for s in [fund, tech, news, mkt] if (s >= 55 if total >= 61 else s <= 45 if total < 31 else 35 <= s <= 65)) / 4) * 55)

        summary = f"{name} scores {total:.0f}/100, a {rec} signal. The analysis shows {', '.join(parts[:2])}"
        if len(parts) > 2:
            summary += f", along with {parts[2]}"
        summary += f". Overall signal: {rec} at {confidence}% confidence."

        return summary

    def _fundamentals_details(self, f: dict) -> list:
        if not f:
            return []
        details = []
        if f.get('pe_ratio'):
            details.append({'label': 'P/E Ratio', 'value': f"{f['pe_ratio']:.1f}x"})
        if f.get('roe'):
            details.append({'label': 'ROE', 'value': f"{f['roe']*100:.1f}%"})
        if f.get('debt_to_equity') is not None:
            details.append({'label': 'D/E Ratio', 'value': f"{f['debt_to_equity']:.1f}"})
        if f.get('profit_margin'):
            details.append({'label': 'Net Margin', 'value': f"{f['profit_margin']*100:.1f}%"})
        if f.get('eps_growth'):
            details.append({'label': 'EPS Growth', 'value': f"{f['eps_growth']*100:.1f}%"})
        return details

    def _technicals_details(self, t: dict) -> list:
        if not t:
            return []
        return [
            {'label': 'RSI (14)', 'value': f"{t.get('rsi', 'N/A')}",
             'signal': t.get('rsi_signal', 'neutral')},
            {'label': 'MACD', 'value': 'Bullish' if t.get('macd_bullish') else 'Bearish',
             'signal': 'positive' if t.get('macd_bullish') else 'negative'},
            {'label': 'vs MA50', 'value': f"{t.get('price_vs_ma50', 0):+.1f}%"},
            {'label': 'vs MA200', 'value': f"{t.get('price_vs_ma200', 0):+.1f}%"},
            {'label': 'Trend', 'value': t.get('trend', 'neutral').capitalize()},
        ]

    def _news_details(self, news: list) -> dict:
        if not news:
            return {}
        pos = sum(1 for n in news if n.get('sentiment') == 'positive')
        neg = sum(1 for n in news if n.get('sentiment') == 'negative')
        neu = sum(1 for n in news if n.get('sentiment') == 'neutral')
        avg = sum(n.get('sentiment_score', 0) for n in news) / len(news)
        return {
            'positive': pos, 'negative': neg, 'neutral': neu,
            'total': len(news), 'avg_score': round(avg, 3),
        }

    def _market_sentiment_details(self, quote: dict, t: dict) -> dict:
        current = quote.get('price', 0)
        high_52 = quote.get('week_52_high', current)
        low_52 = quote.get('week_52_low', current)
        range_pct = 0
        if high_52 > low_52:
            range_pct = round((current - low_52) / (high_52 - low_52) * 100, 1)
        return {
            'change_pct': quote.get('change_pct', 0),
            'volume_ratio': t.get('volume_ratio', 1),
            'trend': t.get('trend', 'neutral'),
            '52w_position': range_pct,
        }

    def _macro_details(self) -> list:
        return [
            {'label': 'India GDP Growth', 'value': '~6.8%', 'signal': 'positive'},
            {'label': 'CPI Inflation', 'value': '~4.5%', 'signal': 'neutral'},
            {'label': 'RBI Policy Rate', 'value': '6.25%', 'signal': 'neutral'},
            {'label': 'FII Flows', 'value': 'Positive', 'signal': 'positive'},
            {'label': 'INR Stability', 'value': 'Stable', 'signal': 'neutral'},
        ]
