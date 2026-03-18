"""
================================================================================
  Quantum Trade Oracle — Moteur de Stratégie de Trading
================================================================================
  Fusionne les prédictions IA + sentiment + indicateurs techniques
  pour générer des signaux de trading actionnables avec gestion du risque.

  Pipeline de décision :
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  Prédiction IA ──────────────────┐                       │
  │  (bullish_prob, bearish_prob)    │                       │
  │                                  │                       │
  │  Score de Sentiment ─────────────┤──► Score Composite    │
  │  (SSGM: -1 à +1)                 │       │               │
  │                                  │       │               │
  │  Signal Technique ───────────────┘       │               │
  │  (RSI, MACD, BB position)                │               │
  │                                          ▼               │
  │                                   BUY / SELL / HOLD      │
  │                                          │               │
  │                                          ▼               │
  │                              Gestion du Risque           │
  │                              ├─ Taille de position       │
  │                              ├─ Stop-Loss (ATR-based)    │
  │                              └─ Take-Profit              │
  │                                          │               │
  │                                          ▼               │
  │                                   Signal Final           │
  └──────────────────────────────────────────────────────────┘
================================================================================
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.logger import get_logger

log = get_logger("StrategyEngine")


class TechnicalSignalAnalyzer:
    """
    Analyse les indicateurs techniques pour générer un signal composite.
    Retourne un score entre -1 (très baissier) et +1 (très haussier).
    """

    def analyze(self, row: pd.Series) -> Dict:
        """
        Analyse une ligne de features (indicateurs déjà calculés).

        Args:
            row: pd.Series avec les indicateurs techniques

        Returns:
            Dict avec score technique [-1, +1] et signaux individuels
        """
        signals = {}
        scores  = []

        # ── RSI ────────────────────────────────────────────────────────────
        if "rsi" in row:
            rsi = float(row["rsi"])
            if rsi < 30:
                signals["rsi"] = ("OVERSOLD — Signal d'achat", +1.0)
            elif rsi > 70:
                signals["rsi"] = ("OVERBOUGHT — Signal de vente", -1.0)
            elif rsi < 45:
                signals["rsi"] = ("Légèrement sous-acheté", +0.3)
            elif rsi > 55:
                signals["rsi"] = ("Légèrement sur-acheté", -0.3)
            else:
                signals["rsi"] = ("Neutre", 0.0)
            scores.append(signals["rsi"][1])

        # ── MACD ───────────────────────────────────────────────────────────
        if "macd_positive" in row:
            macd_positive = bool(row["macd_positive"])
            macd_hist     = float(row.get("macd_hist", 0))
            if macd_positive and macd_hist > 0:
                signals["macd"] = ("MACD haussier + histogramme positif", +0.8)
            elif macd_positive:
                signals["macd"] = ("MACD haussier", +0.4)
            elif not macd_positive and macd_hist < 0:
                signals["macd"] = ("MACD baissier + histogramme négatif", -0.8)
            else:
                signals["macd"] = ("MACD baissier", -0.4)
            scores.append(signals["macd"][1])

        # ── Bollinger Bands ────────────────────────────────────────────────
        if "bb_pct_b" in row:
            bb = float(row["bb_pct_b"])
            if bb < 0.05:
                signals["bollinger"] = ("Prix proche de la bande basse — rebond possible", +0.7)
            elif bb > 0.95:
                signals["bollinger"] = ("Prix proche de la bande haute — résistance", -0.7)
            elif bb < 0.35:
                signals["bollinger"] = ("Bande basse — légèrement haussier", +0.3)
            elif bb > 0.65:
                signals["bollinger"] = ("Bande haute — légèrement baissier", -0.3)
            else:
                signals["bollinger"] = ("Zone centrale — neutre", 0.0)
            scores.append(signals["bollinger"][1])

        # ── EMA Crossover ──────────────────────────────────────────────────
        if "ema_cross_50_200" in row:
            cross = bool(row["ema_cross_50_200"])
            if cross:
                signals["ema_trend"] = ("Golden Cross — tendance haussière long-terme", +0.6)
            else:
                signals["ema_trend"] = ("Death Cross — tendance baissière long-terme", -0.6)
            scores.append(signals["ema_trend"][1])

        # ── Volume ─────────────────────────────────────────────────────────
        if "volume_spike" in row and "co_ratio" in row:
            is_spike  = bool(row["volume_spike"])
            co        = float(row["co_ratio"])   # Ratio close/open
            if is_spike and co > 0:
                signals["volume"] = ("Volume spike haussier — confirmation", +0.5)
                scores.append(0.5)
            elif is_spike and co < 0:
                signals["volume"] = ("Volume spike baissier — confirmation", -0.5)
                scores.append(-0.5)

        # ── Stochastique ───────────────────────────────────────────────────
        if "stoch_k" in row:
            stoch = float(row["stoch_k"])
            cross = bool(row.get("stoch_cross", False))
            if stoch < 20 and cross:
                signals["stoch"] = ("Stoch survente + croisement haussier", +0.6)
                scores.append(0.6)
            elif stoch > 80 and not cross:
                signals["stoch"] = ("Stoch surachat + croisement baissier", -0.6)
                scores.append(-0.6)

        # ── Score composite ────────────────────────────────────────────────
        tech_score = float(np.mean(scores)) if scores else 0.0
        tech_score = float(np.clip(tech_score, -1.0, 1.0))

        return {
            "technical_score": round(tech_score, 4),
            "signals":         {k: v[0] for k, v in signals.items()},
            "n_signals":       len(scores),
        }


class RiskManager:
    """
    Gère le dimensionnement des positions et les niveaux de stop-loss/take-profit.
    """

    def __init__(
        self,
        capital: float = 10_000.0,
        max_risk_pct: float = 0.02,
        max_position_pct: float = 0.05,
        stop_loss_pct: float = 0.03,
        take_profit_pct: float = 0.06,
    ):
        self.capital          = capital
        self.max_risk_pct     = max_risk_pct
        self.max_position_pct = max_position_pct
        self.stop_loss_pct    = stop_loss_pct
        self.take_profit_pct  = take_profit_pct

    def calculate(
        self,
        action: str,
        entry_price: float,
        atr: Optional[float] = None,
        confidence: float = 0.6,
    ) -> Dict:
        """
        Calcule les paramètres de gestion du risque pour un trade.

        Stratégie ATR-based :
        • Stop-loss  = entry ± ATR × 1.5
        • Take-profit = entry ± ATR × 3.0   (Risk/Reward = 2:1 minimum)

        Args:
            action:      'BUY' ou 'SELL'
            entry_price: Prix d'entrée estimé
            atr:         Average True Range (volatilité adaptative)
            confidence:  Confiance du signal (0-1) — influence la taille

        Returns:
            Dict avec stop_loss, take_profit, position_size, risk_amount
        """
        # Adapter le SL/TP à la volatilité via l'ATR
        if atr and atr > 0:
            sl_distance = atr * 1.5
            tp_distance = atr * 3.0
        else:
            sl_distance = entry_price * self.stop_loss_pct
            tp_distance = entry_price * self.take_profit_pct

        if action == "BUY":
            stop_loss   = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        elif action == "SELL":
            stop_loss   = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        else:
            return {"action": "HOLD"}

        # Taille de position (Kelly-fraction simplifiée)
        # Ajuster selon la confiance : plus confiant → position plus grande
        confidence_factor = max(0.5, min(1.0, confidence))
        risk_amount   = self.capital * self.max_risk_pct * confidence_factor
        risk_per_unit = abs(entry_price - stop_loss)

        position_size = risk_amount / risk_per_unit if risk_per_unit > 0 else 0
        position_value = position_size * entry_price

        # Cap à max_position_pct du capital
        max_value = self.capital * self.max_position_pct
        if position_value > max_value:
            position_size  = max_value / entry_price
            position_value = max_value

        rr_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)

        return {
            "action":         action,
            "entry_price":    round(entry_price, 6),
            "stop_loss":      round(stop_loss, 6),
            "take_profit":    round(take_profit, 6),
            "position_size":  round(position_size, 6),
            "position_value": round(position_value, 2),
            "risk_amount":    round(risk_amount, 2),
            "risk_reward":    round(rr_ratio, 2),
            "sl_pct":         round(sl_distance / entry_price * 100, 2),
            "tp_pct":         round(tp_distance / entry_price * 100, 2),
            "risk_score":     self._risk_score(rr_ratio, confidence),
        }

    def _risk_score(self, rr_ratio: float, confidence: float) -> str:
        """Évalue le niveau de risque global du trade."""
        score = rr_ratio * confidence
        if score >= 1.5:   return "FAIBLE"
        if score >= 0.8:   return "MODÉRÉ"
        return "ÉLEVÉ"


class StrategyEngine:
    """
    Orchestre la fusion des signaux et génère les recommandations finales.

    Usage:
        engine = StrategyEngine()
        signal = engine.generate_signal(
            ensemble_result, sentiment_result, df_latest, symbol
        )
    """

    def __init__(
        self,
        buy_threshold: float = 0.65,
        sell_threshold: float = 0.35,
        weights: Optional[Dict] = None,
        risk_params: Optional[Dict] = None,
    ):
        self.buy_threshold  = buy_threshold
        self.sell_threshold = sell_threshold
        self.weights = weights or {
            "ai_prediction": 0.50,
            "sentiment":     0.30,
            "technical":     0.20,
        }
        self.tech_analyzer = TechnicalSignalAnalyzer()
        self.risk_manager  = RiskManager(**(risk_params or {}))
        self.signal_history: List[Dict] = []

    def generate_signal(
        self,
        ensemble_result: Dict,
        sentiment_result: Dict,
        df_latest: pd.DataFrame,
        symbol: str = "UNKNOWN",
    ) -> Dict:
        """
        Génère un signal de trading complet.

        Args:
            ensemble_result:  Résultat de ModelEnsemble.predict()
            sentiment_result: Résultat de SentimentEngine.market_sentiment_score()
            df_latest:        DataFrame avec les dernières données + indicateurs
            symbol:           Ticker à trader

        Returns:
            Signal complet avec action, prix, stop-loss, take-profit, risk
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # ── 1. Score IA ────────────────────────────────────────────────────
        ai_bull  = ensemble_result.get("bullish_prob", 0.5)
        ai_bear  = ensemble_result.get("bearish_prob", 0.5)
        ai_conf  = ensemble_result.get("confidence", 0.5)
        ai_agree = ensemble_result.get("agreement", 0.5)

        # Score IA normalisé [-1, +1]
        ai_score = ai_bull - ai_bear

        # ── 2. Score sentiment ─────────────────────────────────────────────
        ssgm = sentiment_result.get("ssgm_score", 0.0)

        # ── 3. Score technique ─────────────────────────────────────────────
        tech_result = {}
        tech_score  = 0.0
        if not df_latest.empty:
            latest_row = df_latest.iloc[-1]
            tech_result = self.tech_analyzer.analyze(latest_row)
            tech_score  = tech_result.get("technical_score", 0.0)

        # ── 4. Score composite pondéré ─────────────────────────────────────
        w = self.weights
        composite = (
            ai_score  * w["ai_prediction"] +
            ssgm      * w["sentiment"]     +
            tech_score * w["technical"]
        )
        composite = float(np.clip(composite, -1.0, 1.0))

        # Convertir en probabilité [0, 1]
        bullish_composite = (composite + 1) / 2

        # ── 5. Déterminer l'action ─────────────────────────────────────────
        if bullish_composite >= self.buy_threshold and ai_conf >= 0.55:
            action = "BUY"
        elif bullish_composite <= self.sell_threshold and ai_conf >= 0.55:
            action = "SELL"
        else:
            action = "HOLD"

        # Filtre d'accord : si les modèles ne sont pas d'accord, réduire la conviction
        if ai_agree < 0.6:
            action = "HOLD"
            log.info("Signal réduit à HOLD — désaccord entre modèles (%.0f%%)", ai_agree * 100)

        # ── 6. Gestion du risque ───────────────────────────────────────────
        entry_price = float(df_latest["close"].iloc[-1]) if "close" in df_latest.columns else 0.0
        atr = float(df_latest["atr"].iloc[-1]) if "atr" in df_latest.columns else None

        risk = self.risk_manager.calculate(action, entry_price, atr, ai_conf)

        # ── 7. Construire le signal ────────────────────────────────────────
        signal = {
            "id":         f"{symbol}_{int(datetime.now().timestamp())}",
            "timestamp":  timestamp,
            "symbol":     symbol,
            "action":     action,

            # Scores détaillés
            "scores": {
                "composite":    round(composite, 4),
                "bullish_pct":  round(bullish_composite * 100, 1),
                "ai":           round(ai_score, 4),
                "sentiment":    round(ssgm, 4),
                "technical":    round(tech_score, 4),
            },

            # Confiance et accord
            "ai_confidence":    round(ai_conf, 4),
            "models_agreement": round(ai_agree, 4),

            # Probas des modèles
            "bullish_probability": round(ai_bull, 4),
            "bearish_probability": round(ai_bear, 4),

            # Gestion du risque
            "risk_management": risk,

            # Signaux techniques individuels
            "technical_signals": tech_result.get("signals", {}),

            # Sentiment
            "sentiment": {
                "ssgm_score": ssgm,
                "label":      sentiment_result.get("label", "NEUTRAL"),
                "signal":     sentiment_result.get("signal", "HOLD"),
            },

            # Interprétation textuelle
            "interpretation": self._interpret(action, bullish_composite, ai_conf, composite),
        }

        self.signal_history.append(signal)
        self._log_signal(signal)
        return signal

    def _interpret(
        self,
        action: str,
        bull_pct: float,
        confidence: float,
        composite: float,
    ) -> str:
        """Génère un texte d'interprétation du signal."""
        if action == "BUY":
            return (
                f"Signal d'ACHAT — probabilité haussière {bull_pct*100:.1f}% "
                f"avec une confiance de {confidence*100:.0f}%. "
                f"Score composite: {composite:+.3f}."
            )
        if action == "SELL":
            return (
                f"Signal de VENTE — probabilité baissière {(1-bull_pct)*100:.1f}% "
                f"avec une confiance de {confidence*100:.0f}%. "
                f"Score composite: {composite:+.3f}."
            )
        return (
            f"CONSERVATION recommandée — signal insuffisant "
            f"(composite: {composite:+.3f}, confiance: {confidence*100:.0f}%)."
        )

    def _log_signal(self, signal: Dict):
        """Log formaté du signal."""
        action = signal["action"]
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(action, "⚪")
        risk  = signal.get("risk_management", {})

        log.info("━" * 55)
        log.info("%s SIGNAL : %s | %s", emoji, action, signal["symbol"])
        log.info("  Composite : %+.4f | Confiance : %.0f%%",
                 signal["scores"]["composite"],
                 signal["ai_confidence"] * 100)
        log.info("  Bull prob : %.1f%% | Bear prob : %.1f%%",
                 signal["bullish_probability"] * 100,
                 signal["bearish_probability"] * 100)
        if action != "HOLD" and risk:
            log.info("  Entrée : %.4f | SL : %.4f | TP : %.4f",
                     risk.get("entry_price", 0),
                     risk.get("stop_loss", 0),
                     risk.get("take_profit", 0))
            log.info("  Taille : %.4f | R/R : %.1f | Risque : %s",
                     risk.get("position_size", 0),
                     risk.get("risk_reward", 0),
                     risk.get("risk_score", "N/A"))
        log.info("━" * 55)

    def get_recent_signals(self, n: int = 10) -> List[Dict]:
        """Retourne les N derniers signaux."""
        return self.signal_history[-n:]
