"""
================================================================================
  Quantum Trade Oracle v2 — Script d'Exemple Complet
================================================================================
  Démonstration pas à pas de toutes les fonctionnalités du système.

  Exécuter avec :
    python example_run.py

  Ou cibler un exemple précis :
    python example_run.py --example basic
    python example_run.py --example backtest
    python example_run.py --example sentiment
================================================================================
"""

import sys
import time
import argparse

# Désactiver les warnings TensorFlow / HuggingFace au démarrage
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def example_basic():
    """
    ─────────────────────────────────────────────────────────
    EXEMPLE 1 : Pipeline complet de base
    ─────────────────────────────────────────────────────────
    Collecte → Features → Entraînement → Prédiction

    Temps estimé : 2-5 minutes (sans GPU)
    """
    print("\n" + "═"*60)
    print("  EXEMPLE 1 : Pipeline Complet de Base")
    print("═"*60 + "\n")

    from main import QuantumTradeOracle

    # 1. Initialiser l'Oracle
    oracle = QuantumTradeOracle()

    # 2. Lancer le pipeline complet
    results = oracle.run_full_pipeline(
        symbols=["BTC-USD"],
        force_retrain=False,    # True = ré-entraîner même si modèles existent
    )

    print("\n✅ Pipeline terminé !")
    print(f"   Signaux générés : {oracle.snapshot()['n_signals']}")
    return results


def example_step_by_step():
    """
    ─────────────────────────────────────────────────────────
    EXEMPLE 2 : Contrôle étape par étape
    ─────────────────────────────────────────────────────────
    Démo de chaque module individuellement.
    """
    print("\n" + "═"*60)
    print("  EXEMPLE 2 : Contrôle Étape par Étape")
    print("═"*60 + "\n")

    from main import QuantumTradeOracle

    oracle = QuantumTradeOracle()

    # ── ÉTAPE 1 : Collecte de données ─────────────────────────────────────
    print("ÉTAPE 1 — Collecte de données de marché")
    print("-" * 40)
    raw_data = oracle.collect_data(
        symbols=["BTC-USD", "ETH-USD"],
        period="1y",
        interval="1d",
    )
    for sym, df in raw_data.items():
        print(f"  {sym}: {len(df)} jours | close=${df['close'].iloc[-1]:.2f}")

    # ── ÉTAPE 2 : Feature Engineering ─────────────────────────────────────
    print("\nÉTAPE 2 — Calcul des indicateurs techniques")
    print("-" * 40)
    feat_data = oracle.build_features()
    for sym, df in feat_data.items():
        latest = df.iloc[-1]
        print(f"  {sym}:")
        print(f"    RSI     = {latest.get('rsi', 0):.2f}")
        print(f"    MACD    = {latest.get('macd', 0):.6f}")
        print(f"    BB%B    = {latest.get('bb_pct_b', 0.5):.3f}")
        print(f"    ATR     = {latest.get('atr', 0):.4f}")
        print(f"    Volume  = {latest.get('volume_ratio', 1):.2f}x sa moyenne")

    # ── ÉTAPE 3 : Analyse Sentiment ───────────────────────────────────────
    print("\nÉTAPE 3 — Analyse de sentiment")
    print("-" * 40)
    from sentiment_engine.sentiment_engine import SentimentEngine

    engine = SentimentEngine(use_finbert=False)   # VADER pour la démo

    test_texts = [
        "Bitcoin surges to new all-time high as institutional adoption accelerates",
        "Crypto market crashes 20% amid regulatory fears and panic selling",
        "SEC delays decision on spot Bitcoin ETF approval",
        "Ethereum completes successful upgrade, network efficiency improves dramatically",
    ]

    for text in test_texts:
        result = engine.analyze_text(text)
        icon = "🟢" if result["score"] > 0.1 else "🔴" if result["score"] < -0.1 else "⚪"
        print(f"  {icon} {result['label']:20s} ({result['score']:+.3f})  {text[:55]}…")

    # ── ÉTAPE 4 : Entraînement ─────────────────────────────────────────────
    print("\nÉTAPE 4 — Entraînement des modèles IA")
    print("-" * 40)
    train_results = oracle.train("BTC-USD", force_retrain=False)
    print(f"  Statut : {train_results.get('status', 'entraîné')}")

    # ── ÉTAPE 5 : Prédiction ──────────────────────────────────────────────
    print("\nÉTAPE 5 — Génération de signal")
    print("-" * 40)
    signal = oracle.predict("BTC-USD", include_news=True)
    oracle._print_signal_summary("BTC-USD", signal)

    return signal


def example_feature_engineering():
    """
    ─────────────────────────────────────────────────────────
    EXEMPLE 3 : Deep-dive Feature Engineering
    ─────────────────────────────────────────────────────────
    Exploration détaillée des indicateurs calculés.
    """
    print("\n" + "═"*60)
    print("  EXEMPLE 3 : Exploration des Features")
    print("═"*60 + "\n")

    import pandas as pd
    from data_collectors.market_collector import MarketDataCollector
    from feature_engineering.feature_engineer import FeatureEngineer

    # Collecter des données
    collector = MarketDataCollector()
    df_raw = collector.fetch("BTC-USD", period="6mo", interval="1d")

    # Calculer les features
    fe = FeatureEngineer()
    df_feat = fe.build_features(df_raw)

    print(f"DataFrame brut     : {df_raw.shape}")
    print(f"DataFrame enrichi  : {df_feat.shape}")
    print(f"Nouvelles features : {df_feat.shape[1] - df_raw.shape[1]}")

    print("\n5 dernières lignes (features sélectionnées) :")
    cols_to_show = ["close", "rsi", "macd", "bb_pct_b", "atr_pct", "volume_ratio", "target"]
    available = [c for c in cols_to_show if c in df_feat.columns]
    print(df_feat[available].tail(5).to_string())

    print("\nDistribution de la cible :")
    vc = df_feat["target"].value_counts()
    print(f"  Hausse (1) : {vc.get(1, 0):4d} jours ({vc.get(1, 0)/len(df_feat)*100:.1f}%)")
    print(f"  Baisse (0) : {vc.get(0, 0):4d} jours ({vc.get(0, 0)/len(df_feat)*100:.1f}%)")

    return df_feat


def example_backtest():
    """
    ─────────────────────────────────────────────────────────
    EXEMPLE 4 : Backtesting complet
    ─────────────────────────────────────────────────────────
    Évalue les performances de la stratégie sur l'historique.

    Note : peut prendre 5-15 minutes selon les données disponibles.
    """
    print("\n" + "═"*60)
    print("  EXEMPLE 4 : Backtesting de la Stratégie")
    print("═"*60 + "\n")

    from main import QuantumTradeOracle

    oracle = QuantumTradeOracle()
    oracle.collect_data(["BTC-USD"], period="2y")
    oracle.build_features(["BTC-USD"])
    oracle.train("BTC-USD")

    results = oracle.backtest(
        symbol="BTC-USD",
        start_date="2023-01-01",
    )

    m = results["metrics"]
    print("\n📊 Métriques clés :")
    print(f"  Rendement total : {m['total_return_pct']:+.2f}%")
    print(f"  Buy & Hold      : {m['buy_hold_return_pct']:+.2f}%")
    print(f"  Alpha           : {m['alpha_pct']:+.2f}%")
    print(f"  Sharpe          : {m['sharpe_ratio']:.4f}")
    print(f"  Max Drawdown    : {m['max_drawdown_pct']:.2f}%")
    print(f"  Win Rate        : {m['win_rate_pct']:.1f}%")

    return results


def example_sentiment_only():
    """
    ─────────────────────────────────────────────────────────
    EXEMPLE 5 : Module de Sentiment Seul
    ─────────────────────────────────────────────────────────
    Test du pipeline de sentiment sans les modèles ML.
    """
    print("\n" + "═"*60)
    print("  EXEMPLE 5 : Analyse de Sentiment")
    print("═"*60 + "\n")

    from news_scrapers.news_scraper import NewsScraper
    from sentiment_engine.sentiment_engine import SentimentEngine

    # Scraper
    scraper = NewsScraper()
    print("Collecte des news BTC/ETH…")
    articles = scraper.fetch_all(["BTC", "ETH"], hours_back=48, max_per_source=15)
    print(f"  {len(articles)} articles collectés\n")

    if articles:
        # Afficher les 5 premières
        print("Aperçu des articles :")
        for a in articles[:5]:
            print(f"  [{a['source']}] {a['title'][:70]}…")

    # Analyse sentiment
    engine = SentimentEngine(use_finbert=False)

    if articles:
        print("\nCalcul du Score de Sentiment Global du Marché (SSGM)…")
        ssgm = engine.market_sentiment_score(articles)

        print(f"\n  SSGM Score  : {ssgm['ssgm_score']:+.4f}")
        print(f"  Label       : {ssgm['label']}")
        print(f"  Signal      : {ssgm['signal']}")
        print(f"  Interprét.  : {ssgm.get('interpretation', '')}")

        dist = ssgm.get("components", {}).get("news", {}).get("dist", {})
        if dist:
            print(f"\n  Distribution :")
            print(f"    🟢 Bullish : {dist.get('bullish_pct', 0):.1f}%")
            print(f"    🔴 Bearish : {dist.get('bearish_pct', 0):.1f}%")

    return ssgm if articles else {}


def example_model_deep_dive():
    """
    ─────────────────────────────────────────────────────────
    EXEMPLE 6 : Exploration des Modèles IA
    ─────────────────────────────────────────────────────────
    Entraîner et inspecter chaque modèle individuellement.
    """
    print("\n" + "═"*60)
    print("  EXEMPLE 6 : Modèles IA en Détail")
    print("═"*60 + "\n")

    import numpy as np
    from data_collectors.market_collector import MarketDataCollector
    from feature_engineering.feature_engineer import FeatureEngineer
    from ai_models.classical_models import ClassicalMLModel
    from ai_models.lstm_model import LSTMModel

    # Données
    collector = MarketDataCollector()
    df_raw = collector.fetch("BTC-USD", period="1y")
    fe = FeatureEngineer()
    df_feat = fe.build_features(df_raw)
    X_train, X_test, y_train, y_test = fe.train_test_split(df_feat)

    # ── RandomForest ──────────────────────────────────────────────────────
    print("1️⃣  RandomForest :")
    rf = ClassicalMLModel("random_forest")
    rf_metrics = rf.train(X_train.values, y_train.values, fe.feature_names)
    rf_eval = rf.evaluate(X_test.values, y_test.values)
    print(f"   AUC (CV)   : {rf_metrics.get('cv_auc', 0):.4f}")
    print(f"   AUC (Test) : {rf_eval.get('roc_auc', 0):.4f}")
    print(f"   Top features : {rf.top_features(5)[:5]}")

    # ── GradientBoosting ──────────────────────────────────────────────────
    print("\n2️⃣  GradientBoosting :")
    gb = ClassicalMLModel("gradient_boosting")
    gb_metrics = gb.train(X_train.values, y_train.values, fe.feature_names)
    gb_eval = gb.evaluate(X_test.values, y_test.values)
    print(f"   AUC (CV)   : {gb_metrics.get('cv_auc', 0):.4f}")
    print(f"   AUC (Test) : {gb_eval.get('roc_auc', 0):.4f}")

    # ── Prédiction sur le dernier jour ────────────────────────────────────
    print("\n🔮 Prédiction sur le dernier jour :")
    x_last = X_test.values[-1]
    rf_pred  = rf.predict_single(x_last)
    gb_pred  = gb.predict_single(x_last)
    print(f"   RandomForest    : {rf_pred['prediction']:4s} | Bull={rf_pred['bullish_prob']:.3f}")
    print(f"   GradientBoosting: {gb_pred['prediction']:4s} | Bull={gb_pred['bullish_prob']:.3f}")


# ── Mapping des exemples ──────────────────────────────────────────────────────

EXAMPLES = {
    "basic":     ("Pipeline complet (recommandé pour démarrer)",    example_basic),
    "steps":     ("Contrôle étape par étape",                       example_step_by_step),
    "features":  ("Exploration du feature engineering",             example_feature_engineering),
    "backtest":  ("Backtesting complet",                            example_backtest),
    "sentiment": ("Module de sentiment seul",                       example_sentiment_only),
    "models":    ("Exploration des modèles IA",                     example_model_deep_dive),
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🔮 Quantum Trade Oracle — Exemples")
    parser.add_argument(
        "--example",
        choices=list(EXAMPLES.keys()) + ["all"],
        default="basic",
        help="Exemple à exécuter",
    )
    args = parser.parse_args()

    print("\n" + "╔" + "═"*62 + "╗")
    print("║  🔮  QUANTUM TRADE ORACLE v2 — Exemples d'Utilisation       ║")
    print("╚" + "═"*62 + "╝")

    if args.example == "all":
        for name, (desc, fn) in EXAMPLES.items():
            print(f"\n{'━'*60}")
            print(f"  {name.upper()} : {desc}")
            fn()
    else:
        name, fn = args.example, EXAMPLES[args.example][1]
        fn()

    print("\n✅ Terminé.\n")
