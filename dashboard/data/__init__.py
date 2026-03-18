"""
================================================================================
  Quantum Trade Oracle — Base de Données Complète
================================================================================
  Fichier : database/database.py
  Moteur  : SQLite (zero config, fichier local, production-ready pour usage solo)

  Tables :
  ┌─────────────────────────────────────────────────────────┐
  │  market_data     │ Prix OHLCV historiques               │
  │  signals         │ Signaux BUY/SELL/HOLD générés        │
  │  news            │ Articles de news collectés           │
  │  sentiment       │ Scores de sentiment par symbole      │
  │  backtest_runs   │ Sessions de backtesting              │
  │  backtest_trades │ Chaque trade simulé                  │
  │  model_metrics   │ Performances des modèles IA          │
  └─────────────────────────────────────────────────────────┘

  Usage rapide :
  ─────────────────────────────────────────────────────────
  from database.database import Database

  db = Database()                          # Crée quantum_trade.db
  db.save_market_data("BTC-USD", df)       # Sauvegarder OHLCV
  db.save_signal(signal_dict)              # Sauvegarder un signal
  df = db.get_market_data("BTC-USD")       # Charger OHLCV
  signals = db.get_signals("BTC-USD", 10) # 10 derniers signaux
================================================================================
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from ...utils.logger import get_logger

log = get_logger("Database")


# ══════════════════════════════════════════════════════════════════════════════
#  SCHÉMA SQL
# ══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
-- ── Données de marché OHLCV ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS market_data (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT    NOT NULL,
    timestamp   TEXT    NOT NULL,
    open        REAL    NOT NULL,
    high        REAL    NOT NULL,
    low         REAL    NOT NULL,
    close       REAL    NOT NULL,
    volume      REAL    NOT NULL,
    interval    TEXT    DEFAULT '1d',
    created_at  TEXT    DEFAULT (datetime('now')),
    UNIQUE(symbol, timestamp, interval)
);
CREATE INDEX IF NOT EXISTS idx_market_symbol ON market_data(symbol, timestamp);

-- ── Signaux de trading ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id            TEXT    UNIQUE,
    symbol               TEXT    NOT NULL,
    timestamp            TEXT    NOT NULL,
    action               TEXT    NOT NULL,    -- BUY / SELL / HOLD
    bullish_probability  REAL,
    bearish_probability  REAL,
    confidence           REAL,
    composite_score      REAL,
    models_agreement     REAL,
    ai_score             REAL,
    sentiment_score      REAL,
    technical_score      REAL,
    -- Gestion du risque
    entry_price          REAL,
    stop_loss            REAL,
    take_profit          REAL,
    risk_reward          REAL,
    position_size        REAL,
    capital_at_risk      REAL,
    risk_level           TEXT,
    -- Contexte
    interpretation       TEXT,
    raw_json             TEXT,    -- Signal complet en JSON
    created_at           TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol, timestamp);

-- ── Articles de news ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS news (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id   TEXT    UNIQUE,
    symbol       TEXT,
    source       TEXT,
    title        TEXT    NOT NULL,
    description  TEXT,
    url          TEXT,
    published_at TEXT,
    sentiment_score  REAL,
    sentiment_label  TEXT,
    created_at   TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_news_symbol ON news(symbol, published_at);

-- ── Scores de sentiment ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL,
    ssgm_score      REAL,
    label           TEXT,
    news_bullish_pct REAL,
    news_bearish_pct REAL,
    fear_greed_index INTEGER,
    fear_greed_label TEXT,
    raw_json         TEXT,
    created_at       TEXT   DEFAULT (datetime('now')),
    UNIQUE(symbol, timestamp)
);
CREATE INDEX IF NOT EXISTS idx_sentiment_symbol ON sentiment_scores(symbol, timestamp);

-- ── Sessions de backtesting ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS backtest_runs (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id               TEXT    UNIQUE,
    symbol               TEXT    NOT NULL,
    start_date           TEXT,
    end_date             TEXT,
    initial_capital      REAL,
    final_capital        REAL,
    total_return_pct     REAL,
    cagr_pct             REAL,
    sharpe_ratio         REAL,
    sortino_ratio        REAL,
    max_drawdown_pct     REAL,
    win_rate_pct         REAL,
    profit_factor        REAL,
    n_trades             INTEGER,
    buy_hold_return_pct  REAL,
    alpha_pct            REAL,
    report_text          TEXT,
    created_at           TEXT    DEFAULT (datetime('now'))
);

-- ── Trades du backtest ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS backtest_trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    REFERENCES backtest_runs(run_id),
    symbol      TEXT,
    action      TEXT,
    entry_date  TEXT,
    exit_date   TEXT,
    entry_price REAL,
    exit_price  REAL,
    size        REAL,
    pnl         REAL,
    pnl_pct     REAL,
    exit_reason TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_trades_run ON backtest_trades(run_id);

-- ── Métriques des modèles IA ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_metrics (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name   TEXT    NOT NULL,
    symbol       TEXT,
    accuracy     REAL,
    roc_auc      REAL,
    f1_score     REAL,
    cv_auc       REAL,
    n_samples    INTEGER,
    n_features   INTEGER,
    trained_at   TEXT    DEFAULT (datetime('now'))
);

-- ── Watchlist ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS watchlist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT    UNIQUE NOT NULL,
    name        TEXT,
    asset_type  TEXT    DEFAULT 'crypto',   -- crypto / stock / etf
    added_at    TEXT    DEFAULT (datetime('now')),
    notes       TEXT
);
"""


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

class Database:
    """
    Interface complète avec la base de données SQLite du projet QTO.

    Thread-safe grâce à un lock et des connexions par thread.
    Connexion lazy (ouverte au premier appel).

    Usage:
        db = Database()                           # Crée quantum_trade.db
        db.save_market_data("BTC-USD", df_ohlcv)
        df = db.get_market_data("BTC-USD", days=30)
        db.save_signal(signal_dict)
        signals = db.get_signals("BTC-USD", limit=10)
    """

    def __init__(self, db_path: str = "./data/quantum_trade.db"):
        self.db_path  = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock    = threading.Lock()
        self._local   = threading.local()  # Connexion par thread
        self._init_db()
        log.info("✅ Base de données initialisée : %s", self.db_path)

    # ──────────────────────────────────────────────────────────────────────────
    #  CONNEXION
    # ──────────────────────────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Retourne la connexion SQLite du thread courant."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            self._local.conn.row_factory = sqlite3.Row
            # Optimisations SQLite
            self._local.conn.execute("PRAGMA journal_mode=WAL")   # Meilleure concurrence
            self._local.conn.execute("PRAGMA synchronous=NORMAL") # Plus rapide
            self._local.conn.execute("PRAGMA cache_size=10000")   # Cache 10MB
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    @contextmanager
    def _cursor(self):
        """Context manager pour les opérations DB avec commit auto."""
        conn = self._get_conn()
        cur  = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            log.error("Erreur DB : %s", str(e))
            raise
        finally:
            cur.close()

    def _init_db(self):
        """Crée toutes les tables si elles n'existent pas."""
        conn = self._get_conn()
        conn.executescript(SCHEMA)
        conn.commit()
        log.debug("Schéma DB initialisé")

    # ──────────────────────────────────────────────────────────────────────────
    #  DONNÉES DE MARCHÉ (OHLCV)
    # ──────────────────────────────────────────────────────────────────────────

    def save_market_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        interval: str = "1d",
    ) -> int:
        """
        Sauvegarde un DataFrame OHLCV dans la base.

        Utilise INSERT OR REPLACE pour éviter les doublons.

        Args:
            symbol:   Ticker (ex: 'BTC-USD')
            df:       DataFrame avec colonnes open/high/low/close/volume
            interval: Granularité ('1d', '1h', etc.)

        Returns:
            Nombre de lignes insérées
        """
        if df.empty:
            log.warning("DataFrame vide, rien à sauvegarder pour %s", symbol)
            return 0

        rows = []
        for ts, row in df.iterrows():
            rows.append((
                symbol,
                str(ts),
                float(row.get("open",   0)),
                float(row.get("high",   0)),
                float(row.get("low",    0)),
                float(row.get("close",  0)),
                float(row.get("volume", 0)),
                interval,
            ))

        sql = """
            INSERT OR REPLACE INTO market_data
                (symbol, timestamp, open, high, low, close, volume, interval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self._lock:
            with self._cursor() as cur:
                cur.executemany(sql, rows)
                count = cur.rowcount

        log.info("💾 market_data : %d lignes sauvegardées pour %s", len(rows), symbol)
        return len(rows)

    def get_market_data(
        self,
        symbol: str,
        days: int = 365,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Charge les données OHLCV depuis la base.

        Args:
            symbol:   Ticker
            days:     Nombre de jours à charger (depuis maintenant)
            interval: Granularité

        Returns:
            DataFrame OHLCV avec index DatetimeIndex (UTC)
        """
        sql = """
            SELECT timestamp, open, high, low, close, volume
            FROM market_data
            WHERE symbol = ? AND interval = ?
              AND timestamp >= datetime('now', ?)
            ORDER BY timestamp ASC
        """
        with self._cursor() as cur:
            cur.execute(sql, (symbol, interval, f"-{days} days"))
            rows = cur.fetchall()

        if not rows:
            log.debug("Aucune donnée en base pour %s (interval=%s)", symbol, interval)
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df.set_index("timestamp", inplace=True)
        df = df.astype(float)

        log.debug("📂 market_data : %d lignes chargées pour %s", len(df), symbol)
        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Retourne le dernier prix de clôture connu."""
        sql = "SELECT close FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
        with self._cursor() as cur:
            cur.execute(sql, (symbol,))
            row = cur.fetchone()
        return float(row[0]) if row else None

    # ──────────────────────────────────────────────────────────────────────────
    #  SIGNAUX DE TRADING
    # ──────────────────────────────────────────────────────────────────────────

    def save_signal(self, signal: Dict) -> int:
        """
        Sauvegarde un signal de trading complet.

        Args:
            signal: Dict généré par StrategyEngine.generate_signal()

        Returns:
            ID de la ligne insérée
        """
        scores = signal.get("scores", {})
        risk   = signal.get("risk_management", {})

        sql = """
            INSERT OR REPLACE INTO signals (
                signal_id, symbol, timestamp, action,
                bullish_probability, bearish_probability, confidence,
                composite_score, models_agreement,
                ai_score, sentiment_score, technical_score,
                entry_price, stop_loss, take_profit,
                risk_reward, position_size, capital_at_risk, risk_level,
                interpretation, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            signal.get("id"),
            signal.get("symbol"),
            signal.get("timestamp", datetime.utcnow().isoformat()),
            signal.get("action"),
            signal.get("bullish_probability"),
            signal.get("bearish_probability"),
            signal.get("ai_confidence"),
            scores.get("composite"),
            signal.get("models_agreement"),
            scores.get("ai"),
            scores.get("sentiment"),
            scores.get("technical"),
            risk.get("entry_price"),
            risk.get("stop_loss"),
            risk.get("take_profit"),
            risk.get("risk_reward_ratio"),
            risk.get("position_size"),
            risk.get("capital_at_risk"),
            risk.get("risk_level"),
            signal.get("interpretation"),
            json.dumps(signal, default=str),
        )

        with self._lock:
            with self._cursor() as cur:
                cur.execute(sql, params)
                row_id = cur.lastrowid

        log.info("💾 Signal sauvegardé : %s %s (id=%d)",
                 signal.get("action"), signal.get("symbol"), row_id)
        return row_id

    def get_signals(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
        action: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Charge les signaux depuis la base.

        Args:
            symbol: Filtrer par symbole (None = tous)
            limit:  Nombre maximum de résultats
            action: Filtrer par action ('BUY', 'SELL', 'HOLD')

        Returns:
            DataFrame des signaux, trié par date décroissante
        """
        conditions = []
        params     = []

        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol)
        if action:
            conditions.append("action = ?")
            params.append(action)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"""
            SELECT signal_id, symbol, timestamp, action,
                   bullish_probability, bearish_probability, confidence,
                   composite_score, entry_price, stop_loss, take_profit,
                   risk_reward, risk_level, interpretation, created_at
            FROM signals
            {where}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)

        with self._cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        if not rows:
            return pd.DataFrame()

        cols = ["signal_id", "symbol", "timestamp", "action",
                "bull_%", "bear_%", "confidence",
                "composite", "entry", "SL", "TP",
                "R/R", "risk_level", "interpretation", "created_at"]
        return pd.DataFrame(rows, columns=cols)

    def get_signal_stats(self, symbol: Optional[str] = None) -> Dict:
        """Statistiques agrégées des signaux."""
        where  = "WHERE symbol = ?" if symbol else ""
        params = (symbol,) if symbol else ()

        sql = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN action='BUY'  THEN 1 ELSE 0 END) as buys,
                SUM(CASE WHEN action='SELL' THEN 1 ELSE 0 END) as sells,
                SUM(CASE WHEN action='HOLD' THEN 1 ELSE 0 END) as holds,
                AVG(confidence) as avg_confidence,
                AVG(bullish_probability) as avg_bull_prob,
                MAX(created_at) as last_signal
            FROM signals {where}
        """
        with self._cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()

        if not row:
            return {}
        return {
            "total":          row[0],
            "buys":           row[1],
            "sells":          row[2],
            "holds":          row[3],
            "avg_confidence": round(row[4] or 0, 4),
            "avg_bull_prob":  round(row[5] or 0, 4),
            "last_signal":    row[6],
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  ARTICLES DE NEWS
    # ──────────────────────────────────────────────────────────────────────────

    def save_news(self, articles: List[Dict]) -> int:
        """Sauvegarde une liste d'articles en masse."""
        if not articles:
            return 0

        sql = """
            INSERT OR IGNORE INTO news
                (article_id, symbol, source, title, description, url,
                 published_at, sentiment_score, sentiment_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = [(
            a.get("id"),
            a.get("symbol"),
            a.get("source"),
            a.get("title", ""),
            a.get("description", ""),
            a.get("url", ""),
            a.get("published_at"),
            a.get("sentiment_score"),
            a.get("sentiment_label"),
        ) for a in articles]

        with self._lock:
            with self._cursor() as cur:
                cur.executemany(sql, rows)
                count = cur.rowcount

        log.debug("💾 news : %d articles sauvegardés", len(rows))
        return len(rows)

    def get_news(
        self,
        symbol: Optional[str] = None,
        hours_back: int = 48,
        limit: int = 50,
    ) -> List[Dict]:
        """Charge les articles récents."""
        where_parts = ["published_at >= datetime('now', ?)"]
        params      = [f"-{hours_back} hours"]

        if symbol:
            where_parts.append("symbol = ?")
            params.append(symbol)

        sql = f"""
            SELECT article_id, symbol, source, title, description, url,
                   published_at, sentiment_score, sentiment_label
            FROM news
            WHERE {' AND '.join(where_parts)}
            ORDER BY published_at DESC
            LIMIT ?
        """
        params.append(limit)

        with self._cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [dict(row) for row in rows]

    # ──────────────────────────────────────────────────────────────────────────
    #  SENTIMENT
    # ──────────────────────────────────────────────────────────────────────────

    def save_sentiment(self, symbol: str, sentiment: Dict) -> int:
        """Sauvegarde un score de sentiment."""
        sql = """
            INSERT OR REPLACE INTO sentiment_scores
                (symbol, timestamp, ssgm_score, label,
                 news_bullish_pct, news_bearish_pct,
                 fear_greed_index, fear_greed_label, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        ts = datetime.utcnow().isoformat()
        with self._lock:
            with self._cursor() as cur:
                cur.execute(sql, (
                    symbol, ts,
                    sentiment.get("ssgm_score"),
                    sentiment.get("label"),
                    sentiment.get("components", {}).get("news", {}).get("dist", {}).get("bullish_pct"),
                    sentiment.get("components", {}).get("news", {}).get("dist", {}).get("bearish_pct"),
                    None,
                    None,
                    json.dumps(sentiment, default=str),
                ))
                return cur.lastrowid

    def get_sentiment_history(
        self,
        symbol: str,
        days: int = 30,
    ) -> pd.DataFrame:
        """Historique des scores de sentiment pour un symbole."""
        sql = """
            SELECT timestamp, ssgm_score, label, news_bullish_pct, news_bearish_pct
            FROM sentiment_scores
            WHERE symbol = ? AND timestamp >= datetime('now', ?)
            ORDER BY timestamp ASC
        """
        with self._cursor() as cur:
            cur.execute(sql, (symbol, f"-{days} days"))
            rows = cur.fetchall()

        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=["timestamp", "ssgm_score", "label", "bull_%", "bear_%"])

    # ──────────────────────────────────────────────────────────────────────────
    #  BACKTEST
    # ──────────────────────────────────────────────────────────────────────────

    def save_backtest(self, results: Dict) -> str:
        """
        Sauvegarde les résultats complets d'un backtest.

        Args:
            results: Dict retourné par Backtester.run()

        Returns:
            run_id unique du backtest
        """
        import uuid
        run_id = str(uuid.uuid4())[:12]
        m = results.get("metrics", {})

        # Session principale
        sql_run = """
            INSERT INTO backtest_runs (
                run_id, symbol, initial_capital, final_capital,
                total_return_pct, cagr_pct, sharpe_ratio, sortino_ratio,
                max_drawdown_pct, win_rate_pct, profit_factor, n_trades,
                buy_hold_return_pct, alpha_pct, report_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params_run = (
            run_id,
            results.get("symbol"),
            results.get("initial_capital"),
            results.get("final_capital"),
            m.get("total_return_pct"),
            m.get("cagr_pct"),
            m.get("sharpe_ratio"),
            m.get("sortino_ratio"),
            m.get("max_drawdown_pct"),
            m.get("win_rate_pct"),
            m.get("profit_factor"),
            m.get("n_trades"),
            m.get("buy_hold_return_pct"),
            m.get("alpha_pct"),
            results.get("report"),
        )

        # Trades
        trades = results.get("closed_trades", [])
        sql_trade = """
            INSERT INTO backtest_trades
                (run_id, symbol, action, entry_date, exit_date,
                 entry_price, exit_price, size, pnl, pnl_pct, exit_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        trade_params = [(
            run_id,
            results.get("symbol"),
            t.get("action"),
            t.get("entry_date"),
            t.get("exit_date"),
            t.get("entry_price"),
            t.get("exit_price"),
            t.get("size"),
            t.get("pnl"),
            t.get("pnl_pct"),
            t.get("exit_reason"),
        ) for t in trades]

        with self._lock:
            with self._cursor() as cur:
                cur.execute(sql_run, params_run)
                cur.executemany(sql_trade, trade_params)

        log.info("💾 Backtest sauvegardé : run_id=%s | return=%.2f%% | trades=%d",
                 run_id, m.get("total_return_pct", 0), len(trades))
        return run_id

    def get_backtest_history(self, symbol: Optional[str] = None, limit: int = 20) -> pd.DataFrame:
        """Historique des backtests."""
        where = "WHERE symbol = ?" if symbol else ""
        sql = f"""
            SELECT run_id, symbol, created_at,
                   total_return_pct, sharpe_ratio, max_drawdown_pct,
                   win_rate_pct, n_trades, alpha_pct
            FROM backtest_runs {where}
            ORDER BY created_at DESC LIMIT ?
        """
        params = ([symbol, limit] if symbol else [limit])
        with self._cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        if not rows:
            return pd.DataFrame()
        cols = ["run_id", "symbol", "date", "return_%", "sharpe", "max_dd_%", "win_%", "trades", "alpha_%"]
        return pd.DataFrame(rows, columns=cols)

    def get_backtest_trades(self, run_id: str) -> pd.DataFrame:
        """Charge tous les trades d'un backtest."""
        sql = """
            SELECT action, entry_date, exit_date, entry_price,
                   exit_price, size, pnl, pnl_pct, exit_reason
            FROM backtest_trades
            WHERE run_id = ?
            ORDER BY entry_date
        """
        with self._cursor() as cur:
            cur.execute(sql, (run_id,))
            rows = cur.fetchall()

        if not rows:
            return pd.DataFrame()
        cols = ["action", "entry_date", "exit_date", "entry_price",
                "exit_price", "size", "P&L $", "P&L %", "raison"]
        return pd.DataFrame(rows, columns=cols)

    # ──────────────────────────────────────────────────────────────────────────
    #  MÉTRIQUES MODÈLES IA
    # ──────────────────────────────────────────────────────────────────────────

    def save_model_metrics(self, model_name: str, metrics: Dict, symbol: str = None) -> int:
        """Sauvegarde les métriques d'évaluation d'un modèle."""
        sql = """
            INSERT INTO model_metrics
                (model_name, symbol, accuracy, roc_auc, f1_score,
                 cv_auc, n_samples, n_features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._lock:
            with self._cursor() as cur:
                cur.execute(sql, (
                    model_name, symbol,
                    metrics.get("accuracy"),
                    metrics.get("roc_auc"),
                    metrics.get("f1_score"),
                    metrics.get("cv_auc"),
                    metrics.get("n_samples"),
                    metrics.get("n_features"),
                ))
                return cur.lastrowid

    def get_model_metrics(self) -> pd.DataFrame:
        """Historique des performances des modèles."""
        sql = """
            SELECT model_name, symbol, accuracy, roc_auc, f1_score, cv_auc, trained_at
            FROM model_metrics
            ORDER BY trained_at DESC
            LIMIT 50
        """
        with self._cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=["modèle", "symbole", "accuracy", "AUC", "F1", "CV_AUC", "entraîné le"])

    # ──────────────────────────────────────────────────────────────────────────
    #  WATCHLIST
    # ──────────────────────────────────────────────────────────────────────────

    def add_to_watchlist(self, symbol: str, name: str = "", asset_type: str = "crypto", notes: str = ""):
        """Ajoute un symbole à la watchlist."""
        sql = "INSERT OR IGNORE INTO watchlist (symbol, name, asset_type, notes) VALUES (?, ?, ?, ?)"
        with self._lock:
            with self._cursor() as cur:
                cur.execute(sql, (symbol, name, asset_type, notes))
        log.info("Watchlist : +%s", symbol)

    def get_watchlist(self) -> List[str]:
        """Retourne la liste des symboles surveillés."""
        with self._cursor() as cur:
            cur.execute("SELECT symbol FROM watchlist ORDER BY added_at")
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def remove_from_watchlist(self, symbol: str):
        """Retire un symbole de la watchlist."""
        with self._cursor() as cur:
            cur.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,))

    # ──────────────────────────────────────────────────────────────────────────
    #  UTILITAIRES
    # ──────────────────────────────────────────────────────────────────────────

    def get_db_stats(self) -> Dict:
        """Retourne les statistiques globales de la base."""
        tables = ["market_data", "signals", "news", "sentiment_scores",
                  "backtest_runs", "backtest_trades", "model_metrics", "watchlist"]
        stats = {}

        with self._cursor() as cur:
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cur.fetchone()[0]

        # Taille du fichier
        size_mb = self.db_path.stat().st_size / 1_048_576 if self.db_path.exists() else 0
        stats["db_size_mb"]  = round(size_mb, 2)
        stats["db_path"]     = str(self.db_path)
        return stats

    def export_to_csv(self, table: str, output_dir: str = "./data/exports") -> str:
        """Exporte une table en CSV."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with self._cursor() as cur:
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        df = pd.DataFrame(rows, columns=cols)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_path / f"{table}_{ts}.csv"
        df.to_csv(path, index=False)

        log.info("📤 Export CSV : %s (%d lignes)", path, len(df))
        return str(path)

    def vacuum(self):
        """Optimise et compacte la base de données."""
        conn = self._get_conn()
        conn.execute("VACUUM")
        conn.commit()
        log.info("🧹 VACUUM terminé")

    def close(self):
        """Ferme la connexion proprement."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
        log.debug("Connexion DB fermée")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ══════════════════════════════════════════════════════════════════════════════
#  TEST RAPIDE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    print("=== Test de la base de données QTO ===\n")

    with Database("./data/test_qto.db") as db:

        # ── Test market data ────────────────────────────────────────────────
        print("1. Test market_data…")
        dates = pd.date_range("2024-01-01", periods=100, freq="D", tz="UTC")
        df_test = pd.DataFrame({
            "open":   np.random.uniform(40000, 50000, 100),
            "high":   np.random.uniform(50000, 60000, 100),
            "low":    np.random.uniform(35000, 45000, 100),
            "close":  np.random.uniform(40000, 55000, 100),
            "volume": np.random.uniform(1e9, 5e9, 100),
        }, index=dates)

        n = db.save_market_data("BTC-USD", df_test)
        df_loaded = db.get_market_data("BTC-USD", days=200)
        print(f"   ✅ Sauvegardé : {n} | Chargé : {len(df_loaded)} lignes")

        # ── Test signal ────────────────────────────────────────────────────
        print("2. Test signals…")
        test_signal = {
            "id": "TEST_001",
            "symbol": "BTC-USD",
            "timestamp": datetime.utcnow().isoformat(),
            "action": "BUY",
            "bullish_probability": 0.72,
            "bearish_probability": 0.28,
            "ai_confidence": 0.68,
            "models_agreement": 0.75,
            "scores": {"composite": 0.35, "ai": 0.44, "sentiment": 0.2, "technical": 0.3},
            "risk_management": {
                "entry_price": 95000, "stop_loss": 92150, "take_profit": 100700,
                "risk_reward_ratio": 2.0, "position_size": 0.00105,
                "capital_at_risk": 200, "risk_level": "MODÉRÉ",
                "sl_pct": 3.0, "tp_pct": 6.0,
            },
            "interpretation": "Signal d'achat avec probabilité haussière de 72%.",
        }
        sig_id = db.save_signal(test_signal)
        signals = db.get_signals("BTC-USD")
        print(f"   ✅ Signal sauvegardé (id={sig_id}) | {len(signals)} signal(s) en base")

        # ── Stats ────────────────────────────────────────────────────────────
        print("3. Statistiques de la base…")
        stats = db.get_db_stats()
        for k, v in stats.items():
            print(f"   {k:25s} : {v}")

        print("\n✅ Tous les tests réussis !")