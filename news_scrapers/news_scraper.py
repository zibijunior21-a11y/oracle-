"""
================================================================================
  Quantum Trade Oracle — Scraper de News Financières
================================================================================
  Collecte des actualités financières depuis plusieurs sources :

  1. NewsAPI.org         — API structurée (clé gratuite disponible)
  2. CryptoCompare News  — Agrégateur crypto (sans clé)
  3. Yahoo Finance RSS   — Flux RSS (sans clé)

  Chaque article est normalisé dans un format unifié et prêt
  pour l'analyse NLP.
================================================================================
"""

import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from utils.logger import get_logger

log = get_logger("NewsScraper")


# Schéma unifié pour tous les articles
ARTICLE_SCHEMA = {
    "id":           str,    # Hash MD5 de l'URL
    "source":       str,    # Nom de la source
    "symbol":       str,    # Ticker associé
    "title":        str,    # Titre de l'article
    "description":  str,    # Résumé (max 500 chars)
    "url":          str,    # URL complète
    "published_at": str,    # ISO 8601
    "sentiment":    None,   # Rempli par SentimentEngine
}


class NewsScraper:
    """
    Collecte et normalise les actualités financières depuis plusieurs sources.

    Usage:
        scraper = NewsScraper(api_key="votre_newsapi_key")
        articles = scraper.fetch_all(symbols=["BTC", "AAPL"])
    """

    YAHOO_RSS_BASE = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories={cats}"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "QuantumTradeOracle/2.0 (research bot)",
            "Accept":     "application/json, text/html",
        })
        self._seen_ids: set = set()   # Déduplication globale

    # ──────────────────────────────────────────────────────────────────────────
    #  POINT D'ENTRÉE PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────────

    def fetch_all(
        self,
        symbols: List[str],
        hours_back: int = 24,
        max_per_source: int = 30,
    ) -> List[Dict]:
        """
        Agrège les articles de toutes les sources disponibles.

        Args:
            symbols:        Liste de tickers (ex: ['BTC', 'AAPL'])
            hours_back:     Fenêtre temporelle en heures
            max_per_source: Articles maximum par source

        Returns:
            Liste d'articles normalisés, triés par date décroissante,
            sans doublons inter-sources.
        """
        self._seen_ids.clear()
        all_articles: List[Dict] = []

        for symbol in symbols:
            # ── NewsAPI ────────────────────────────────────────────────────────
            if self.api_key:
                articles = self._fetch_newsapi(symbol, hours_back, max_per_source)
                all_articles.extend(articles)

            # ── Yahoo Finance RSS ─────────────────────────────────────────────
            rss_articles = self._fetch_yahoo_rss(symbol, max_per_source)
            all_articles.extend(rss_articles)

            # ── CryptoCompare (pour les cryptos uniquement) ───────────────────
            crypto_symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"]
            if symbol.upper() in crypto_symbols:
                cc_articles = self._fetch_cryptocompare(symbol, max_per_source)
                all_articles.extend(cc_articles)

            time.sleep(0.3)   # Rate limiting

        # Tri par date décroissante
        all_articles.sort(
            key=lambda x: x.get("published_at", ""), reverse=True
        )

        log.info("📰 %d articles collectés pour %s", len(all_articles), symbols)
        return all_articles

    # ──────────────────────────────────────────────────────────────────────────
    #  SOURCE 1 : NewsAPI
    # ──────────────────────────────────────────────────────────────────────────

    def _fetch_newsapi(
        self,
        symbol: str,
        hours_back: int,
        limit: int,
    ) -> List[Dict]:
        """Récupère depuis NewsAPI.org (nécessite une clé API)."""
        if not self.api_key:
            return []

        from_dt = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()

        # Construire une query lisible pour le symbole
        query_map = {
            "BTC": "bitcoin OR crypto",
            "ETH": "ethereum OR crypto",
            "AAPL": "Apple stock",
            "TSLA": "Tesla stock",
            "SPY":  "S&P 500 OR stock market",
        }
        query = query_map.get(symbol.upper(), f"{symbol} finance")

        url = "https://newsapi.org/v2/everything"
        params = {
            "q":        query,
            "from":     from_dt,
            "sortBy":   "publishedAt",
            "language": "en",
            "pageSize": min(limit, 100),
            "apiKey":   self.api_key,
        }

        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            articles = []
            for item in data.get("articles", []):
                a = self._normalize_newsapi(item, symbol)
                if a and a["id"] not in self._seen_ids:
                    self._seen_ids.add(a["id"])
                    articles.append(a)

            log.debug("NewsAPI: %d articles pour %s", len(articles), symbol)
            return articles

        except requests.RequestException as e:
            log.warning("NewsAPI échec pour %s: %s", symbol, str(e))
            return []

    def _normalize_newsapi(self, item: Dict, symbol: str) -> Optional[Dict]:
        """Normalise un article brut NewsAPI."""
        title = item.get("title") or ""
        desc  = item.get("description") or ""
        url   = item.get("url") or ""

        if not title or title.strip() == "[Removed]" or not url:
            return None

        return {
            "id":           self._make_id(url),
            "source":       f"newsapi:{item.get('source', {}).get('name', 'unknown')}",
            "symbol":       symbol,
            "title":        title.strip(),
            "description":  desc.strip()[:500],
            "url":          url,
            "published_at": item.get("publishedAt", datetime.utcnow().isoformat()),
            "sentiment":    None,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  SOURCE 2 : Yahoo Finance RSS
    # ──────────────────────────────────────────────────────────────────────────

    def _fetch_yahoo_rss(self, symbol: str, limit: int) -> List[Dict]:
        """
        Scrape le flux RSS de Yahoo Finance.
        Fonctionne sans clé API.
        """
        url = self.YAHOO_RSS_BASE.format(symbol=quote(symbol))

        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")[:limit]

            articles = []
            for item in items:
                title = item.find("title")
                link  = item.find("link")
                desc  = item.find("description")
                pubdt = item.find("pubDate")

                if not title or not link:
                    continue

                title_text = title.get_text(strip=True)
                link_text  = link.get_text(strip=True)
                desc_text  = desc.get_text(strip=True)[:500] if desc else ""

                article_id = self._make_id(link_text)
                if article_id in self._seen_ids:
                    continue
                self._seen_ids.add(article_id)

                # Parser la date RSS
                published = self._parse_rss_date(pubdt.get_text() if pubdt else "")

                articles.append({
                    "id":           article_id,
                    "source":       "yahoo_finance",
                    "symbol":       symbol,
                    "title":        title_text,
                    "description":  desc_text,
                    "url":          link_text,
                    "published_at": published,
                    "sentiment":    None,
                })

            log.debug("Yahoo RSS: %d articles pour %s", len(articles), symbol)
            return articles

        except Exception as e:
            log.warning("Yahoo RSS échoué pour %s: %s", symbol, str(e))
            return []

    # ──────────────────────────────────────────────────────────────────────────
    #  SOURCE 3 : CryptoCompare
    # ──────────────────────────────────────────────────────────────────────────

    def _fetch_cryptocompare(self, symbol: str, limit: int) -> List[Dict]:
        """
        Récupère les news depuis CryptoCompare.
        API publique, pas de clé nécessaire.
        """
        categories_map = {
            "BTC": "BTC,Blockchain",
            "ETH": "ETH,Blockchain",
            "SOL": "SOL",
        }
        categories = categories_map.get(symbol.upper(), symbol)
        url = self.CRYPTOCOMPARE_URL.format(cats=categories)

        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("Data", [])

            articles = []
            for item in data[:limit]:
                title = item.get("title", "")
                body  = item.get("body", "")[:500]
                link  = item.get("url", "")
                ts    = item.get("published_on", 0)

                if not title or not link:
                    continue

                article_id = self._make_id(link)
                if article_id in self._seen_ids:
                    continue
                self._seen_ids.add(article_id)

                published = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""

                articles.append({
                    "id":           article_id,
                    "source":       f"cryptocompare:{item.get('source', '')}",
                    "symbol":       symbol,
                    "title":        title,
                    "description":  body,
                    "url":          link,
                    "published_at": published,
                    "sentiment":    None,
                })

            log.debug("CryptoCompare: %d articles pour %s", len(articles), symbol)
            return articles

        except Exception as e:
            log.warning("CryptoCompare échec pour %s: %s", symbol, str(e))
            return []

    # ──────────────────────────────────────────────────────────────────────────
    #  UTILITAIRES
    # ──────────────────────────────────────────────────────────────────────────

    def _make_id(self, url: str) -> str:
        """Génère un ID stable à partir d'une URL (MD5)."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _parse_rss_date(self, date_str: str) -> str:
        """Parse une date au format RSS (RFC 2822) en ISO 8601."""
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.astimezone(timezone.utc).isoformat()
            except ValueError:
                continue
        return datetime.utcnow().isoformat()
