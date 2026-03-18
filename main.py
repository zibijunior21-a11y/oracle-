"""
================================================================================
  Quantum Trade Oracle — Orchestrateur Principal
================================================================================
  Coordonne l'ensemble du pipeline de A à Z :

  1. Collecte → 2. Features → 3. Entraînement IA
                    ↓
  4. Analyse Sentiment → 5. Prédiction Ensemble
                    ↓
  6. Signal de Trading → 7. Backtesting
                    ↓
  8. Rapport & Dashboard

  Usage rapide :
  ─────────────────────────────────────────────────────
  from main import QuantumTradeOracle

  oracle = QuantumTradeOracle()
  oracle.setup(symbols=["BTC-USD"])
  oracle.train()
  signal = oracle.predict("BTC-USD")
  report = oracle.backtest("BTC-USD")
================================================================================
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ── Imports du projet ─────────────────────────────────────────────────────────
from config.settings import PATHS, MARKET, FEATURES, MODELS, SENTIMENT, STRATEGY, BACKTEST, API_KEYS, SYSTEM
from data_collectors.market_collector import MarketDataCollector
from news_scrapers.news_scraper import NewsScraper
from sentiment_engine.sentiment_engine import SentimentEngine
from feature_engineering.feature_engineer import FeatureEngineer
from ai_models.model_ensemble import ModelEnsemble
from strategy_engine.strategy_engine import StrategyEngine
from backtesting.backtester import Backtester
from utils.logger import get_logger

log = get_logger("QuantumTradeOracle")


class QuantumTradeOracle:
    """
    Système complet de trading algorithmique IA.

    Encapsule tout le pipeline de collecte → prédiction → signal → backtest.

    Attributes:
        market_collector: Collecteur de données OHLCV
        news_scraper:     Scraper de news financières
        sentiment_engine: Analyseur NLP de sentiment
        feature_engineer: Pipeline de feature engineering
        model_ensemble:   Ensemble de 4 modèles IA
        strategy_engine:  Générateur de signaux de trading
        backtester:       Moteur de backtesting
    """

    def __init__(self):
        log.info("═" * 65)
        log.info("  🔮  QUANTUM TRADE ORACLE  v2.0")
        log.info("  Système de Trading Algorithmique IA")
        log.info("═" * 65)

        # ── Composants ────────────────────────────────────────────────────
        self.market_collector  = MarketDataCollector()
        self.news_scraper      = NewsScraper(api_key=API_KEYS.get("news_api", ""))
        self.sentiment_engine  = SentimentEngine(use_finbert=False)   # VADER seul par défaut
        self.feature_engineer  = FeatureEngineer(
            prediction_horizon=FEATURES["prediction_horizon"],
            threshold_pct=FEATURES["threshold_pct"],
            sequence_length=FEATURES["sequence_length"],
        )
        self.model_ensemble    = ModelEnsemble(models_dir=str(PATHS["models"]))
        self.strategy_engine   = StrategyEngine(
            buy_threshold=STRATEGY["buy_threshold"],
            sell_threshold=STRATEGY["sell_threshold"],
            weights=STRATEGY["weights"],
        )
        self.backtester        = Backtester(
            initial_capital=BACKTEST["initial_capital"],
            commission_pct=BACKTEST["commission_pct"],
            slippage_pct=BACKTEST["slippage_pct"],
        )

        # ── État ──────────────────────────────────────────────────────────
        self._raw_data:       Dict[str, pd.DataFrame] = {}
        self._feature_data:   Dict[str, pd.DataFrame] = {}
        self._is_trained:     bool = False
        self._signal_history: List[Dict] = []

        log.info("✅ Tous les composants initialisés")

    # ══════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 1 : COLLECTE DE DONNÉES
    # ══════════════════════════════════════════════════════════════════════════

    def collect_data(
        self,
        symbols: Optional[List[str]] = None,
        period: str = "2y",
        interval: str = "1d",
    ) -> Dict[str, pd.DataFrame]:
        """
        Collecte les données OHLCV pour tous les symboles configurés.

        Args:
            symbols:  Liste de tickers (None = config.MARKET.symbols)
            period:   Période historique
            interval: Granularité

        Returns:
            Dict {symbol: DataFrame OHLCV}
        """
        symbols = symbols or MARKET["symbols"]
        log.info("📡 Collecte OHLCV — %d symboles | period=%s", len(symbols), period)

        self._raw_data = self.market_collector.fetch_multiple(
            symbols, period=period, interval=interval
        )

        log.info("✅ Données collectées : %s",
                 {s: len(df) for s, df in self._raw_data.items()})
        return self._raw_data

    # ══════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 2 : FEATURE ENGINEERING
    # ══════════════════════════════════════════════════════════════════════════

    def build_features(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Calcule tous les indicateurs techniques et features pour chaque symbole.

        Args:
            symbols: Symboles à traiter (None = tous les symboles collectés)

        Returns:
            Dict {symbol: DataFrame avec features}
        """
        symbols = symbols or list(self._raw_data.keys())
        log.info("⚙️ Feature engineering pour %d symboles…", len(symbols))

        self._feature_data = {}
        for symbol in symbols:
            if symbol not in self._raw_data:
                log.warning("Données manquantes pour %s — ignoré", symbol)
                continue
            df_feat = self.feature_engineer.build_features(self._raw_data[symbol])
            self._feature_data[symbol] = df_feat
            log.info("  %s — %d lignes, %d features", symbol, len(df_feat), len(df_feat.columns))

        return self._feature_data

    # ══════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 3 : ENTRAÎNEMENT
    # ══════════════════════════════════════════════════════════════════════════

    def train(
        self,
        symbol: Optional[str] = None,
        force_retrain: bool = False,
    ) -> Dict:
        """
        Entraîne l'ensemble de modèles IA sur les données historiques.

        S'il existe des modèles sauvegardés, les charge directement
        sauf si force_retrain=True.

        Args:
            symbol:        Symbole d'entraînement (None = premier disponible)
            force_retrain: Forcer le ré-entraînement même si modèles existent

        Returns:
            Dict avec métriques d'entraînement par modèle
        """
        # Essayer de charger les modèles existants
        if not force_retrain:
            if self.model_ensemble.load_all():
                log.info("✅ Modèles chargés depuis le disque")
                self._is_trained = True
                return {"status": "loaded_from_disk"}

        # Sélectionner le symbole d'entraînement
        if not self._feature_data:
            self.collect_data()
            self.build_features()

        symbol = symbol or next(iter(self._feature_data))
        df = self._feature_data.get(symbol)

        if df is None or len(df) < 200:
            raise ValueError(f"Données insuffisantes pour l'entraînement ({symbol})")

        log.info("🧠 Entraînement sur %s (%d lignes)…", symbol, len(df))

        # ── Préparation des données tabulaires (RF, GB) ────────────────────
        X_tab_train, X_tab_test, y_train, y_test = \
            self.feature_engineer.train_test_split(df, MODELS["train_ratio"])

        feature_names = self.feature_engineer.feature_names

        # ── Préparation des séquences (LSTM, Transformer) ──────────────────
        try:
            X_seq_train, X_seq_test, y_seq_train, y_seq_test = \
                self.feature_engineer.to_sequences(df, FEATURES["sequence_length"], MODELS["train_ratio"])
        except Exception as e:
            log.warning("Séquences non disponibles: %s", str(e))
            X_seq_train = X_seq_test = y_seq_train = y_seq_test = None

        # ── Entraînement de l'ensemble ─────────────────────────────────────
        train_results = self.model_ensemble.train_all(
            X_tab_train=X_tab_train.values,
            y_train=y_train.values,
            X_seq_train=X_seq_train,
            feature_names=feature_names,
        )

        # ── Évaluation sur le test set ─────────────────────────────────────
        eval_results = self.model_ensemble.evaluate_all(
            X_tab_test.values, y_test.values,
            X_seq_test,
        )

        log.info("📊 Performances sur le test set :")
        for model_name, metrics in eval_results.items():
            log.info("  %s — acc=%.4f | auc=%.4f",
                     model_name,
                     metrics.get("accuracy", 0),
                     metrics.get("roc_auc", 0))

        # Sauvegarder les modèles
        self.model_ensemble.save_all()

        self._is_trained = True
        return {
            "training": train_results,
            "evaluation": eval_results,
            "symbol": symbol,
            "n_samples": len(df),
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 4 : PRÉDICTION & SIGNAL
    # ══════════════════════════════════════════════════════════════════════════

    def predict(
        self,
        symbol: str,
        include_news: bool = True,
    ) -> Dict:
        """
        Génère un signal de trading complet pour un symbole.

        Pipeline :
        1. Vérifier / télécharger les données récentes
        2. Calculer les features
        3. Prédire avec l'ensemble IA
        4. Analyser le sentiment des news
        5. Combiner et générer le signal final

        Args:
            symbol:       Symbole à analyser
            include_news: Inclure l'analyse de news (ralentit légèrement)

        Returns:
            Dict complet avec signal, risque, probabilités, contexte
        """
        if not self._is_trained:
            log.info("Modèles non entraînés — tentative de chargement…")
            if not self.model_ensemble.load_all():
                raise RuntimeError("Modèles non disponibles. Appeler train() d'abord.")
            self._is_trained = True

        log.info("━" * 55)
        log.info("🔍 Analyse : %s", symbol)
        log.info("━" * 55)
        t0 = time.time()

        # ── 1. Données récentes ────────────────────────────────────────────
        if symbol not in self._feature_data:
            df_raw = self.market_collector.fetch(symbol, period="6mo")
            if df_raw.empty:
                return {"error": f"Impossible de télécharger les données pour {symbol}"}
            df_feat = self.feature_engineer.build_features(df_raw)
            self._feature_data[symbol] = df_feat

        df = self._feature_data[symbol]
        if len(df) < FEATURES["sequence_length"] + 10:
            return {"error": "Données insuffisantes pour la prédiction"}

        feature_cols = self.feature_engineer.get_feature_columns(df)

        # ── 2. Features pour les modèles tabulaires ────────────────────────
        x_tab_raw = df[feature_cols].iloc[-1].values
        if self.feature_engineer._fitted:
            x_tab = self.feature_engineer.scaler.transform(x_tab_raw.reshape(1, -1))[0]
        else:
            x_tab = x_tab_raw

        # ── 3. Séquence pour LSTM/Transformer ─────────────────────────────
        try:
            x_seq = self.feature_engineer.transform_latest(df, FEATURES["sequence_length"])
            x_seq = x_seq[-FEATURES["sequence_length"]:].reshape(
                1, FEATURES["sequence_length"], -1
            )
        except Exception:
            x_seq = None

        # ── 4. Prédiction ensemble ─────────────────────────────────────────
        ensemble_result = self.model_ensemble.predict(
            x_tabular=x_tab,
            x_sequence=x_seq.squeeze(0) if x_seq is not None else None,
            strategy="confidence_weighted",
        )

        # ── 5. Analyse du sentiment ────────────────────────────────────────
        sentiment_result = {"ssgm_score": 0.0, "label": "NEUTRAL", "signal": "HOLD"}
        if include_news:
            base_sym = symbol.replace("-USD", "").replace("-USDT", "")
            articles = self.news_scraper.fetch_all([base_sym], hours_back=24, max_per_source=20)
            if articles:
                sentiment_result = self.sentiment_engine.market_sentiment_score(articles)

        # ── 6. Générer le signal ───────────────────────────────────────────
        signal = self.strategy_engine.generate_signal(
            ensemble_result=ensemble_result,
            sentiment_result=sentiment_result,
            df_latest=df.tail(50),
            symbol=symbol,
        )

        elapsed = round(time.time() - t0, 2)
        signal["_analysis_time_sec"] = elapsed
        self._signal_history.append(signal)

        log.info("⏱️  Analyse terminée en %.2fs", elapsed)
        return signal

    # ══════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 5 : BACKTESTING
    # ══════════════════════════════════════════════════════════════════════════

    def backtest(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """
        Lance le backtesting de la stratégie sur des données historiques.

        Le backtesting rejoue les signaux générés par le pipeline complet
        sur chaque jour de l'historique, et évalue les performances.

        Args:
            symbol:     Symbole à backtester
            start_date: Date de début ISO (None = début des données)
            end_date:   Date de fin ISO (None = fin des données)

        Returns:
            Dict avec equity_curve, trades, métriques, rapport
        """
        log.info("═" * 55)
        log.info("  BACKTESTING : %s", symbol)
        log.info("═" * 55)

        if not self._is_trained:
            log.info("Chargement des modèles pour le backtesting…")
            self.model_ensemble.load_all()
            self._is_trained = True

        if symbol not in self._feature_data:
            df_raw = self.market_collector.fetch(
                symbol,
                start=start_date or BACKTEST["start_date"],
                end=end_date,
            )
            df = self.feature_engineer.build_features(df_raw)
            self._feature_data[symbol] = df
        else:
            df = self._feature_data[symbol]

        # Filtrer par dates
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        log.info("Génération des signaux pour %d jours…", len(df))

        # ── Générer les signaux pour chaque jour ───────────────────────────
        # (simulation sans lookahead bias)
        signals = []
        feature_cols = self.feature_engineer.get_feature_columns(df)
        seq_len = FEATURES["sequence_length"]

        for i in range(seq_len, len(df)):
            df_window = df.iloc[:i + 1]   # Données disponibles jusqu'au jour i
            try:
                x_tab = df_window[feature_cols].iloc[-1].values
                if self.feature_engineer._fitted:
                    x_tab = self.feature_engineer.scaler.transform(x_tab.reshape(1, -1))[0]

                x_seq_raw = self.feature_engineer.scaler.transform(
                    df_window[feature_cols].tail(seq_len).values
                )
                x_seq = x_seq_raw.reshape(1, seq_len, -1).squeeze(0)

                pred = self.model_ensemble.predict(x_tab, x_seq, strategy="confidence_weighted")

                # Signal simplifié pour le backtest (sans news en temps réel)
                sentiment_dummy = {"ssgm_score": 0.0, "label": "NEUTRAL", "signal": "HOLD"}
                sig = self.strategy_engine.generate_signal(
                    pred, sentiment_dummy, df_window.tail(20), symbol
                )
                sig["timestamp"] = str(df_window.index[-1])
                signals.append(sig)

            except Exception as e:
                log.debug("Erreur signal jour %d: %s", i, str(e))
                continue

        log.info("✅ %d signaux générés", len(signals))

        # ── Exécuter le backtest ───────────────────────────────────────────
        results = self.backtester.run(df, signals, symbol)
        report  = self.backtester.generate_report(results)
        results["report"] = report

        # Afficher le rapport
        print(report)

        # Sauvegarder
        self._save_backtest_results(results, symbol)

        return results

    # ══════════════════════════════════════════════════════════════════════════
    #  PIPELINE COMPLET (setup → train → predict)
    # ══════════════════════════════════════════════════════════════════════════

    def run_full_pipeline(
        self,
        symbols: Optional[List[str]] = None,
        force_retrain: bool = False,
    ) -> Dict[str, Dict]:
        """
        Exécute le pipeline complet de bout en bout.

        Étapes :
        1. Collecte OHLCV
        2. Feature Engineering
        3. Entraînement IA
        4. Prédiction + Signal pour chaque symbole
        5. Affichage des résultats

        Args:
            symbols:       Symboles à analyser
            force_retrain: Forcer le ré-entraînement des modèles

        Returns:
            Dict {symbol: signal}
        """
        symbols = symbols or MARKET["symbols"][:2]   # Limiter pour la démo

        log.info("🚀 Pipeline complet — %d symboles", len(symbols))

        # Étapes 1 & 2
        self.collect_data(symbols)
        self.build_features(symbols)

        # Étape 3
        train_sym = symbols[0]
        self.train(train_sym, force_retrain=force_retrain)

        # Étape 4
        results = {}
        for symbol in symbols:
            try:
                signal = self.predict(symbol)
                results[symbol] = signal
                self._print_signal_summary(symbol, signal)
            except Exception as e:
                log.error("Erreur prédiction %s: %s", symbol, str(e))
                results[symbol] = {"error": str(e)}

        return results

    # ══════════════════════════════════════════════════════════════════════════
    #  UTILITAIRES
    # ══════════════════════════════════════════════════════════════════════════

    def _print_signal_summary(self, symbol: str, signal: Dict):
        """Affiche un résumé visuel du signal."""
        action = signal.get("action", "N/A")
        scores = signal.get("scores", {})
        risk   = signal.get("risk_management", {})

        icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(action, "❓")

        print(f"\n{'─'*55}")
        print(f"  {icon}  {symbol}  →  {action}")
        print(f"{'─'*55}")
        print(f"  Composite  : {scores.get('composite', 0):+.4f}")
        print(f"  Bull/Bear  : {signal.get('bullish_probability', 0)*100:.1f}% / {signal.get('bearish_probability', 0)*100:.1f}%")
        print(f"  Confiance  : {signal.get('ai_confidence', 0)*100:.0f}%")
        print(f"  Accord mods: {signal.get('models_agreement', 0)*100:.0f}%")
        print(f"  Sentiment  : {signal.get('sentiment', {}).get('label', 'N/A')}")
        if action != "HOLD" and risk:
            print(f"  Entrée     : ${risk.get('entry_price', 0):,.4f}")
            print(f"  Stop-Loss  : ${risk.get('stop_loss', 0):,.4f}  (-{risk.get('sl_pct', 0):.1f}%)")
            print(f"  Take-Profit: ${risk.get('take_profit', 0):,.4f}  (+{risk.get('tp_pct', 0):.1f}%)")
            print(f"  R/R        : {risk.get('risk_reward', 0):.2f}:1  |  Risque: {risk.get('risk_score', 'N/A')}")
        print(f"  {signal.get('interpretation', '')}")
        print(f"{'─'*55}\n")

    def _save_backtest_results(self, results: Dict, symbol: str):
        """Sauvegarde les résultats du backtest en JSON."""
        report_dir = PATHS["reports"]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = report_dir / f"backtest_{symbol.replace('/', '_')}_{ts}.json"

        # Serializer les DataFrames
        output = {
            "symbol":          results["symbol"],
            "initial_capital": results["initial_capital"],
            "final_capital":   results["final_capital"],
            "metrics":         results["metrics"],
            "n_trades":        len(results["closed_trades"]),
            "trades_sample":   results["closed_trades"][:10],
        }

        with open(path, "w") as f:
            json.dump(output, f, indent=2, default=str)

        log.info("💾 Résultats backtesting sauvegardés : %s", path)

    def get_signal_history(self) -> List[Dict]:
        """Retourne l'historique des signaux générés."""
        return self._signal_history

    def snapshot(self) -> Dict:
        """Retourne l'état actuel du système."""
        return {
            "is_trained":       self._is_trained,
            "symbols_loaded":   list(self._raw_data.keys()),
            "symbols_featured": list(self._feature_data.keys()),
            "n_signals":        len(self._signal_history),
            "timestamp":        datetime.now(timezone.utc).isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="🔮 Quantum Trade Oracle v2 — Système de Trading IA"
    )
    parser.add_argument("--symbols",    nargs="+", default=["BTC-USD"],
                        help="Symboles à analyser (ex: BTC-USD ETH-USD AAPL)")
    parser.add_argument("--mode",       choices=["predict", "train", "backtest", "full"],
                        default="full", help="Mode d'exécution")
    parser.add_argument("--retrain",    action="store_true",
                        help="Forcer le ré-entraînement des modèles")
    parser.add_argument("--symbol",     default="BTC-USD",
                        help="Symbole pour le mode predict/backtest")
    parser.add_argument("--no-news",    action="store_true",
                        help="Désactiver l'analyse de news (plus rapide)")
    args = parser.parse_args()

    # Lancer l'Oracle
    oracle = QuantumTradeOracle()

    if args.mode == "full":
        oracle.run_full_pipeline(args.symbols, force_retrain=args.retrain)

    elif args.mode == "train":
        oracle.collect_data(args.symbols)
        oracle.build_features(args.symbols)
        metrics = oracle.train(args.symbols[0], force_retrain=args.retrain)
        print("\n✅ Entraînement terminé :", metrics)

    elif args.mode == "predict":
        oracle.collect_data([args.symbol])
        oracle.build_features([args.symbol])
        signal = oracle.predict(args.symbol, include_news=not args.no_news)
        oracle._print_signal_summary(args.symbol, signal)

    elif args.mode == "backtest":
        oracle.collect_data([args.symbol])
        oracle.build_features([args.symbol])
        oracle.train(args.symbol, force_retrain=args.retrain)
        results = oracle.backtest(args.symbol)
