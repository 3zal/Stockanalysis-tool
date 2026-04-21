from typing import Optional


class ScoringService:
    """
    Weighted investment scoring system (0-100).

    Base weights when every signal is available:
      Fundamentals     30%
      Technicals       20%
      News sentiment   15%
      Market sentiment 10%
      Analyst coverage 15%
      India macro      10%

    Whenever analyst or macro data is unavailable (common for small-cap
    tickers with no analyst coverage, or when the World Bank API is down),
    that weight is redistributed proportionally across the remaining signals
    so the composite stays on a 0-100 scale.
    """

    BASE_WEIGHTS = {
        'fundamentals': 0.30,
        'technicals': 0.20,
        'news_sentiment': 0.15,
        'market_sentiment': 0.10,
        'analyst': 0.15,
        'macro': 0.10,
    }

    def calculate_score(self, quote: dict, fundamentals: dict, technicals: dict,
                        news: list, analyst: Optional[dict] = None,
                        macro: Optional[dict] = None) -> dict:
        fund_score = self._score_fundamentals(fundamentals, quote)
        tech_score = self._score_technicals(technicals)
        news_score = self._score_news_sentiment(news)
        market_score = self._score_market_sentiment(quote, technicals)
        analyst_score = float(analyst['score']) if analyst and analyst.get('score') is not None else None
        macro_score = float(macro['score']) if macro and macro.get('score') is not None else None

        weights = self._resolve_weights(analyst_score is not None, macro_score is not None)

        total = (
            fund_score * weights['fundamentals'] +
            tech_score * weights['technicals'] +
            news_score * weights['news_sentiment'] +
            market_score * weights['market_sentiment']
        )
        if analyst_score is not None:
            total += analyst_score * weights['analyst']
        if macro_score is not None:
            total += macro_score * weights['macro']
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
        if analyst_score is not None:
            scores.append(analyst_score)
        if macro_score is not None:
            scores.append(macro_score)

        if recommendation == 'BUY':
            agreeing = sum(1 for s in scores if s >= 55)
        elif recommendation == 'SELL':
            agreeing = sum(1 for s in scores if s <= 45)
        else:
            agreeing = sum(1 for s in scores if 35 <= s <= 65)
        confidence = round(40 + (agreeing / len(scores)) * 55)

        reasoning = self._generate_reasoning(
            total, fund_score, tech_score, news_score, market_score,
            analyst_score, macro_score, fundamentals, technicals, news, quote,
        )

        components = {
            'fundamentals': {
                'score': round(fund_score, 1),
                'weight': round(weights['fundamentals'], 3),
                'label': 'Fundamentals',
                'details': self._fundamentals_details(fundamentals),
            },
            'technicals': {
                'score': round(tech_score, 1),
                'weight': round(weights['technicals'], 3),
                'label': 'Technicals',
                'details': self._technicals_details(technicals),
            },
            'news_sentiment': {
                'score': round(news_score, 1),
                'weight': round(weights['news_sentiment'], 3),
                'label': 'News Sentiment',
                'details': self._news_details(news),
            },
            'market_sentiment': {
                'score': round(market_score, 1),
                'weight': round(weights['market_sentiment'], 3),
                'label': 'Market Sentiment',
                'details': self._market_sentiment_details(quote, technicals),
            },
        }

        if analyst_score is not None and analyst:
            components['analyst'] = {
                'score': round(analyst_score, 1),
                'weight': round(weights['analyst'], 3),
                'label': 'Analyst ratings',
                'details': analyst,
            }
        if macro_score is not None and macro:
            components['macro'] = {
                'score': round(macro_score, 1),
                'weight': round(weights['macro'], 3),
                'label': 'India macro',
                'details': macro,
            }

        return {
            'total': total,
            'recommendation': recommendation,
            'rec_color': rec_color,
            'confidence': confidence,
            'reasoning': reasoning,
            'components': components,
        }

    def _resolve_weights(self, has_analyst: bool, has_macro: bool) -> dict:
        weights = dict(self.BASE_WEIGHTS)
        dropped = 0.0
        if not has_analyst:
            dropped += weights.pop('analyst', 0)
        if not has_macro:
            dropped += weights.pop('macro', 0)
        if dropped > 0:
            remaining_total = sum(weights.values())
            if remaining_total > 0:
                for k in list(weights.keys()):
                    weights[k] = weights[k] + (weights[k] / remaining_total) * dropped
        return weights

    def _score_fundamentals(self, f: dict, q: dict) -> float:
        if not f:
            return 50.0

        score = 50.0

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

        cr = f.get('current_ratio') or 0
        if cr:
            if cr >= 1.5:
                score += 5
            elif cr >= 1.0:
                score += 2
            else:
                score -= 5

        return round(min(max(score, 5), 95), 1)

    def _score_technicals(self, t: dict) -> float:
        if not t:
            return 50.0

        score = 50.0
        rsi = t.get('rsi', 50)
        if rsi < 30:
            score += 18
        elif rsi < 45:
            score += 8
        elif rsi <= 60:
            score += 2
        elif rsi <= 70:
            score -= 5
        else:
            score -= 15

        if t.get('macd_bullish', False):
            score += 12
        else:
            score -= 8

        macd_hist = t.get('macd_hist', 0)
        if macd_hist > 0:
            score += 5
        else:
            score -= 5

        vs_ma200 = t.get('price_vs_ma200', 0)
        if vs_ma200 > 5:
            score += 10
        elif vs_ma200 > 0:
            score += 5
        elif vs_ma200 > -5:
            score -= 3
        else:
            score -= 10

        vs_ma50 = t.get('price_vs_ma50', 0)
        if vs_ma50 > 3:
            score += 5
        elif vs_ma50 > 0:
            score += 2
        else:
            score -= 5

        bb_pos = t.get('bb_position', 50)
        if bb_pos < 20:
            score += 8
        elif bb_pos > 80:
            score -= 5

        vol_ratio = t.get('volume_ratio', 1)
        if vol_ratio > 1.5:
            score += 3

        return round(min(max(score, 5), 95), 1)

    def _score_news_sentiment(self, news: list) -> float:
        if not news:
            return 50.0

        total_weight = 0
        weighted_score = 0
        for i, article in enumerate(news[:8]):
            weight = 1 / (i + 1)
            compound = article.get('sentiment_score', 0)
            normalized = (compound + 1) / 2 * 100
            if article.get('impact') == 'high':
                weight *= 1.5
            weighted_score += normalized * weight
            total_weight += weight

        if total_weight == 0:
            return 50.0
        return round(min(max(weighted_score / total_weight, 5), 95), 1)

    def _score_market_sentiment(self, quote: dict, technicals: dict) -> float:
        score = 50.0
        change_pct = quote.get('change_pct', 0)
        if change_pct > 3:
            score += 12
        elif change_pct > 1:
            score += 6
        elif change_pct < -3:
            score -= 12
        elif change_pct < -1:
            score -= 6

        vol_ratio = technicals.get('volume_ratio', 1)
        if vol_ratio > 2 and change_pct > 0:
            score += 8
        elif vol_ratio > 2 and change_pct < 0:
            score -= 8

        if technicals.get('trend') == 'bullish':
            score += 8
        else:
            score -= 5

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

    def _generate_reasoning(self, total, fund, tech, news, mkt, analyst, macro,
                            fundamentals, technicals, news_list, quote) -> str:
        parts = []
        name = quote.get('name', 'This stock')

        roe = fundamentals.get('roe') or 0
        if fund >= 65:
            parts.append(f"strong fundamentals with an ROE of {roe:.1f}%" if roe else "strong fundamentals")
        elif fund <= 40:
            parts.append("weak fundamentals that warrant caution")
        else:
            parts.append("moderate fundamentals")

        rsi = technicals.get('rsi', 50)
        if tech >= 65:
            parts.append(f"bullish technical setup (RSI: {rsi:.0f}, above key moving averages)")
        elif tech <= 40:
            parts.append(f"bearish technical indicators (RSI: {rsi:.0f})")
        else:
            parts.append(f"neutral technicals (RSI: {rsi:.0f})")

        if news_list:
            pos = sum(1 for n in news_list if n.get('sentiment') == 'positive')
            neg = sum(1 for n in news_list if n.get('sentiment') == 'negative')
            if pos > neg:
                parts.append("predominantly positive recent news coverage")
            elif neg > pos:
                parts.append("concerning negative news sentiment")
            else:
                parts.append("mixed news sentiment")

        if analyst is not None:
            if analyst >= 65:
                parts.append("constructive analyst coverage")
            elif analyst <= 40:
                parts.append("cautious analyst view")

        rec = 'Buy' if total >= 61 else 'Hold' if total >= 31 else 'Sell'
        summary = f"{name} scores {total:.0f}/100, a {rec} signal. The analysis shows {', '.join(parts[:2])}"
        if len(parts) > 2:
            summary += f", along with {parts[2]}"
        if len(parts) > 3:
            summary += f" and {parts[3]}"
        summary += "."
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
