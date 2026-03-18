"""
================================================================================
  Quantum Trade Oracle — Collecteur de Données de Marché
================================================================================
  Télécharge les données OHLCV historiques et en temps réel via yfinance.

  Supporte :
  • Actions (AAPL, TSLA, SPY…)
  • Crypto (BTC-USD, ETH-USD…)
  • ETFs, Indices

  Données collectées :
  • Open / High / Low / Close / Volume (OHLCV)
  • Données journalières, horaires, à la minute
================================================================================
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from utils.logger import get_logger

log = get_logger("MarketCollector")


class MarketDataCollector:
    """
    Collecte les données de marché historiques et temps réel.

    Usage:
        collector = MarketDataCollector()
        df = collector.fetch("BTC-USD", period="1y", interval="1d")
        snapshot = collector.live_snapshot(["BTC-USD", "ETH-USD"])
    """

    # Intervalles valides yfinance
    VALID_INTERVALS = ["1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"]

    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Args:
            cache_ttl_seconds: Durée de vie du cache en mémoire (secondes).
                               Évite les requêtes redondantes à l'API.
        """
        self._cache: Dict[str, Tuple[pd.DataFrame, float]] = {}
        self.cache_ttl = cache_ttl_seconds

    # ──────────────────────────────────────────────────────────────────────────
    #  FETCH PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────────

    def fetch(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Télécharge les données OHLCV pour un symbole.

        Args:
            symbol:    Ticker yfinance (ex: 'BTC-USD', 'AAPL')
            period:    Période globale ('1d','5d','1mo','3mo','6mo','1y','2y','5y','max')
            interval:  Granularité des bougies
            start:     Date de début ISO (priorité sur period si défini)
            end:       Date de fin ISO
            use_cache: Utiliser le cache en mémoire

        Returns:
            DataFrame avec colonnes : Open, High, Low, Close, Volume, Adj Close
            Index : DatetimeIndex (UTC)

        Raises:
            ValueError: Si le symbole est invalide ou les données vides
        """
        cache_key = f"{symbol}_{period}_{interval}_{start}_{end}"

        # ── Cache hit ─────────────────────────────────────────────────────────
        if use_cache and cache_key in self._cache:
            df_cached, ts = self._cache[cache_key]
            if time.time() - ts < self.cache_ttl:
                log.debug("Cache hit pour %s", symbol)
                return df_cached.copy()

        log.info("Téléchargement %s | period=%s | interval=%s", symbol, period, interval)

        try:
            ticker = yf.Ticker(symbol)

            if start:
                df = ticker.history(start=start, end=end, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                raise ValueError(f"Aucune donnée retournée pour '{symbol}'")

            df = self._clean(df, symbol)

            # Mise en cache
            self._cache[cache_key] = (df.copy(), time.time())

            log.info("✅ %s — %d lignes récupérées [%s → %s]",
                     symbol, len(df),
                     df.index[0].date(), df.index[-1].date())
            return df

        except Exception as e:
            log.error("Erreur pour %s : %s", symbol, str(e))
            return pd.DataFrame()

    # ──────────────────────────────────────────────────────────────────────────
    #  MULTI-SYMBOLES
    # ──────────────────────────────────────────────────────────────────────────

    def fetch_multiple(
        self,
        symbols: List[str],
        period: str = "1y",
        interval: str = "1d",
    ) -> Dict[str, pd.DataFrame]:
        """
        Télécharge les données pour une liste de symboles.

        Returns:
            Dict {symbol: DataFrame}
        """
        results = {}
        for symbol in symbols:
            df = self.fetch(symbol, period=period, interval=interval)
            if not df.empty:
                results[symbol] = df
            time.sleep(0.2)   # Respecter le rate limit Yahoo Finance

        log.info("Multi-fetch : %d/%d symboles OK", len(results), len(symbols))
        return results

    # ──────────────────────────────────────────────────────────────────────────
    #  SNAPSHOT TEMPS RÉEL
    # ──────────────────────────────────────────────────────────────────────────

    def live_snapshot(self, symbols: List[str]) -> pd.DataFrame:
        """
        Récupère les prix actuels pour une liste de symboles.

        Returns:
            DataFrame avec une ligne par symbole :
            symbol | price | change_pct | volume | market_cap
        """
        rows = []
        for symbol in symbols:
            try:
                info = yf.Ticker(symbol).fast_info
                rows.append({
                    "symbol":        symbol,
                    "price":         getattr(info, "last_price", None),
                    "prev_close":    getattr(info, "previous_close", None),
                    "volume":        getattr(info, "last_volume", None),
                    "market_cap":    getattr(info, "market_cap", None),
                    "timestamp":     datetime.utcnow().isoformat(),
                })
            except Exception as e:
                log.warning("Snapshot échoué pour %s : %s", symbol, str(e))

        df = pd.DataFrame(rows)
        if not df.empty and "price" in df and "prev_close" in df:
            df["change_pct"] = (df["price"] - df["prev_close"]) / df["prev_close"] * 100

        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  NETTOYAGE
    # ──────────────────────────────────────────────────────────────────────────

    def _clean(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Nettoie et normalise un DataFrame brut de yfinance.

        Opérations :
        1. Renommer les colonnes en minuscules
        2. Supprimer les lignes entièrement nulles
        3. Forward-fill les valeurs manquantes isolées
        4. Ajouter une colonne 'symbol'
        5. S'assurer que l'index est UTC

        Args:
            df:     DataFrame brut yfinance
            symbol: Ticker (pour la colonne 'symbol')

        Returns:
            DataFrame nettoyé
        """
        # Standardiser les noms de colonnes
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]

        # Assurer les colonnes de base
        required = {"open", "high", "low", "close", "volume"}
        available = required.intersection(df.columns)
        df = df[list(available)].copy()

        # Supprimer les lignes entièrement nulles
        df.dropna(how="all", inplace=True)

        # Forward-fill les trous isolés (fermetures de marché)
        df.ffill(inplace=True)
        df.dropna(inplace=True)

        # Assurer que les prix sont positifs
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                df = df[df[col] > 0]

        # Métadonnées
        df["symbol"] = symbol

        # Index UTC
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        df.sort_index(inplace=True)
        return df

    def clear_cache(self):
        """Vide le cache en mémoire."""
        self._cache.clear()
        log.debug("Cache vidé")
