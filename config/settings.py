"""
================================================================================
  Quantum Trade Oracle — Configuration Centralisée
================================================================================
  Source unique de vérité pour tous les paramètres du système.
  Utilise python-dotenv pour les secrets (clés API).
  Toutes les valeurs ont des defaults raisonnables pour un démarrage rapide.
================================================================================
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger le fichier .env à la racine du projet
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


# ══════════════════════════════════════════════════════════════════════════════
#  CHEMINS DU PROJET
# ══════════════════════════════════════════════════════════════════════════════

PATHS = {
    "root":       ROOT_DIR,
    "data":       ROOT_DIR / "data",
    "raw":        ROOT_DIR / "data" / "raw",
    "processed":  ROOT_DIR / "data" / "processed",
    "models":     ROOT_DIR / "data" / "models",
    "logs":       ROOT_DIR / "logs",
    "reports":    ROOT_DIR / "reports",
}

# Créer les répertoires si nécessaire
for path in PATHS.values():
    Path(path).mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CLÉS API  (définies dans le fichier .env)
# ══════════════════════════════════════════════════════════════════════════════

API_KEYS = {
    "news_api":           os.getenv("NEWS_API_KEY", ""),
    "alpha_vantage":      os.getenv("ALPHA_VANTAGE_KEY", ""),
    "reddit_client_id":   os.getenv("REDDIT_CLIENT_ID", ""),
    "reddit_secret":      os.getenv("REDDIT_CLIENT_SECRET", ""),
    "twitter_bearer":     os.getenv("TWITTER_BEARER_TOKEN", ""),
}


# ══════════════════════════════════════════════════════════════════════════════
#  MARCHÉ
# ══════════════════════════════════════════════════════════════════════════════

MARKET = {
    # Symboles à surveiller (format yfinance pour actions, ou crypto)
    "symbols":        ["BTC-USD", "ETH-USD", "SPY", "QQQ"],
    "crypto_symbols": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "stock_symbols":  ["AAPL", "TSLA", "NVDA", "SPY"],

    # Paramètres temporels
    "default_period":    "1y",      # Historique pour entraînement
    "default_interval":  "1d",      # Granularité
    "lookback_days":     365,

    # Heures de marché (UTC)
    "market_open_utc":  "13:30",
    "market_close_utc": "20:00",
}


# ══════════════════════════════════════════════════════════════════════════════
#  FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════

FEATURES = {
    # Fenêtres pour les moyennes mobiles
    "ma_windows":        [7, 14, 21, 50, 200],

    # RSI
    "rsi_period":        14,
    "rsi_overbought":    70,
    "rsi_oversold":      30,

    # Bollinger Bands
    "bb_period":         20,
    "bb_std":            2,

    # MACD
    "macd_fast":         12,
    "macd_slow":         26,
    "macd_signal":       9,

    # ATR
    "atr_period":        14,

    # Fenêtres de rendements
    "return_windows":    [1, 3, 5, 10, 20],

    # Fenêtre LSTM (nombre de jours en entrée)
    "sequence_length":   60,

    # Horizon de prédiction (jours)
    "prediction_horizon": 1,

    # Seuil pour classer "hausse" vs "baisse"
    "threshold_pct":     0.005,     # 0.5%
}


# ══════════════════════════════════════════════════════════════════════════════
#  MODÈLES IA
# ══════════════════════════════════════════════════════════════════════════════

MODELS = {
    # ── RandomForest ──────────────────────────────────────────────────────────
    "rf": {
        "n_estimators":  300,
        "max_depth":     None,
        "min_samples_split": 5,
        "random_state":  42,
        "n_jobs":        -1,
        "class_weight":  "balanced",
    },

    # ── GradientBoosting ──────────────────────────────────────────────────────
    "gb": {
        "n_estimators":  200,
        "max_depth":     4,
        "learning_rate": 0.05,
        "subsample":     0.8,
        "random_state":  42,
    },

    # ── LSTM (PyTorch) ────────────────────────────────────────────────────────
    "lstm": {
        "hidden_size":   128,
        "num_layers":    2,
        "dropout":       0.3,
        "epochs":        50,
        "batch_size":    32,
        "learning_rate": 0.001,
        "patience":      10,          # Early stopping
    },

    # ── Transformer (PyTorch) ─────────────────────────────────────────────────
    "transformer": {
        "d_model":       64,
        "nhead":         4,
        "num_layers":    2,
        "dim_feedforward": 256,
        "dropout":       0.1,
        "epochs":        40,
        "batch_size":    32,
        "learning_rate": 0.0005,
        "patience":      8,
    },

    # ── Poids de l'ensemble ───────────────────────────────────────────────────
    "ensemble_weights": {
        "random_forest":     0.20,
        "gradient_boosting": 0.20,
        "lstm":              0.35,
        "transformer":       0.25,
    },

    # Seuil minimum de confiance pour générer un signal
    "min_confidence":    0.60,

    # Split train/test (temporel)
    "train_ratio":       0.80,
}


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYSE DE SENTIMENT
# ══════════════════════════════════════════════════════════════════════════════

SENTIMENT = {
    # Modèle HuggingFace pour le sentiment financier
    "model_name":    "ProsusAI/finbert",
    "fallback_model": "distilbert-base-uncased-finetuned-sst-2-english",

    # Nombre max d'articles à analyser
    "max_articles":  50,
    "max_posts":     100,

    # Poids dans le score global
    "news_weight":   0.60,
    "reddit_weight": 0.40,

    # Subreddits à scraper
    "subreddits":    ["CryptoCurrency", "Bitcoin", "investing", "stocks", "wallstreetbets"],
}


# ══════════════════════════════════════════════════════════════════════════════
#  STRATÉGIE DE TRADING
# ══════════════════════════════════════════════════════════════════════════════

STRATEGY = {
    # Seuils pour les signaux
    "buy_threshold":     0.65,    # Probabilité hausse > 65% → BUY
    "sell_threshold":    0.35,    # Probabilité hausse < 35% → SELL

    # Poids dans la décision finale
    "weights": {
        "ai_prediction":   0.50,
        "sentiment":       0.30,
        "technical":       0.20,
    },

    # Gestion du risque
    "risk": {
        "max_position_pct":   0.05,   # 5% du capital par position
        "stop_loss_pct":      0.03,   # Stop-loss à -3%
        "take_profit_pct":    0.06,   # Take-profit à +6%
        "max_open_positions": 5,
        "risk_per_trade_pct": 0.02,   # 2% du capital risqué par trade
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  BACKTESTING
# ══════════════════════════════════════════════════════════════════════════════

BACKTEST = {
    "initial_capital":   10_000.0,   # Capital de départ
    "commission_pct":    0.001,      # 0.1% par trade
    "slippage_pct":      0.0005,     # 0.05% de slippage
    "start_date":        "2023-01-01",
    "end_date":          None,       # None = aujourd'hui
}


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTÈME
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM = {
    "debug":       os.getenv("DEBUG", "false").lower() == "true",
    "log_level":   os.getenv("LOG_LEVEL", "INFO"),
    "timezone":    "UTC",
    "random_seed": 42,
}
