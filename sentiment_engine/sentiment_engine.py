"""
================================================================================
  Quantum Trade Oracle — Moteur d'Analyse de Sentiment
================================================================================
  Évalue le sentiment du marché à partir de textes financiers (news, posts).

  Architecture multi-couches :
  ┌──────────────────────────────────────────────────────────┐
  │  Textes bruts                                            │
  │     │                                                    │
  │     ▼                                                    │
  │  Prétraitement (nettoyage, truncation)                   │
  │     │                                                    │
  │     ├──► FinBERT (modèle finance HuggingFace)            │
  │     │         positive / negative / neutral (proba)      │
  │     │                                                    │
  │     └──► VADER (lexique financier enrichi)               │
  │               compound score [-1, +1]                    │
  │                       │                                  │
  │     ▼                                                    │
  │  Ensemble pondéré → Score final [-1, +1]                 │
  │     │                                                    │
  │     ▼                                                    │
  │  Score de Sentiment Global du Marché                     │
  └──────────────────────────────────────────────────────────┘

  Score de sortie :
    +1.0 → Sentiment très haussier (bullish)
     0.0 → Neutre
    -1.0 → Sentiment très baissier (bearish)
================================================================================
"""

import re
from typing import Dict, List, Optional, Tuple

import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from utils.logger import get_logger

log = get_logger("SentimentEngine")


class SentimentEngine:
    """
    Analyse le sentiment de textes financiers avec un ensemble de modèles NLP.

    Usage:
        engine = SentimentEngine(use_finbert=True)
        score = engine.analyze_text("Bitcoin surges past $100k!")
        report = engine.analyze_articles(articles_list)
        market_score = engine.market_sentiment_score(articles, reddit_posts)
    """

    # Termes financiers spécifiques pour enrichir VADER
    FINANCIAL_LEXICON = {
        # Bullish (+)
        "bullish": 3.0,  "moon": 2.5,  "surge": 2.5,  "rally": 2.5,
        "breakout": 2.5, "pump": 2.0,  "soar": 2.5,   "ath": 2.5,
        "accumulate": 1.5, "outperform": 2.0, "buy": 1.0, "hodl": 1.5,
        "adoption": 2.0, "upgrade": 1.5, "beat": 1.5, "record": 1.5,
        # Bearish (-)
        "bearish": -3.0, "crash": -3.5, "dump": -2.5, "rekt": -3.0,
        "selloff": -2.5, "capitulation": -3.0, "panic": -2.5, "scam": -3.5,
        "liquidated": -2.5, "correction": -1.5, "fear": -2.0, "fraud": -3.5,
        "hack": -3.0, "ban": -2.5, "downgrade": -2.0, "miss": -1.5,
        # Modifieurs de contexte
        "not":   -1.0,  "never":  -1.5, "no":   -0.8,
        "very":   0.5,  "highly":  0.5, "extremely": 0.8,
    }

    def __init__(self, use_finbert: bool = True, finbert_model: str = "ProsusAI/finbert"):
        """
        Args:
            use_finbert:    Utiliser FinBERT (recommandé, mais nécessite ~500MB)
            finbert_model:  Modèle HuggingFace à utiliser
        """
        # ── VADER avec lexique enrichi ─────────────────────────────────────
        self.vader = SentimentIntensityAnalyzer()
        self.vader.lexicon.update(self.FINANCIAL_LEXICON)
        log.info("VADER initialisé avec lexique financier (%d termes)", len(self.FINANCIAL_LEXICON))

        # ── FinBERT (optionnel) ────────────────────────────────────────────
        self.finbert = None
        self.use_finbert = use_finbert

        if use_finbert:
            self._load_finbert(finbert_model)

    def _load_finbert(self, model_name: str):
        """Charge le pipeline FinBERT (lazy loading)."""
        try:
            from transformers import pipeline
            log.info("Chargement de FinBERT : %s …", model_name)
            self.finbert = pipeline(
                task="text-classification",
                model=model_name,
                tokenizer=model_name,
                device=-1,            # -1 = CPU, 0 = GPU
                truncation=True,
                max_length=512,
                top_k=None,           # Retourner toutes les classes
            )
            log.info("✅ FinBERT chargé avec succès")
        except Exception as e:
            log.warning("FinBERT non disponible (%s) → VADER seul", str(e)[:100])
            self.use_finbert = False

    # ──────────────────────────────────────────────────────────────────────────
    #  ANALYSE D'UN TEXTE
    # ──────────────────────────────────────────────────────────────────────────

    def analyze_text(self, text: str) -> Dict:
        """
        Analyse le sentiment d'un seul texte.

        Args:
            text: Texte à analyser (titre, description, post…)

        Returns:
            Dict avec :
            - score        : float [-1, +1]
            - label        : "BULLISH" | "NEUTRAL" | "BEARISH"
            - confidence   : float [0, 1]
            - breakdown    : scores par modèle
        """
        if not text or not text.strip():
            return self._neutral()

        clean = self._preprocess(text)

        scores = {}

        # ── FinBERT ────────────────────────────────────────────────────────
        if self.use_finbert and self.finbert:
            fb_score = self._finbert_score(clean)
            if fb_score is not None:
                scores["finbert"] = (fb_score, 0.65)   # (score, poids)

        # ── VADER ──────────────────────────────────────────────────────────
        vader_score = self.vader.polarity_scores(clean)["compound"]
        vader_weight = 0.35 if scores else 0.80
        scores["vader"] = (vader_score, vader_weight)

        # ── Score pondéré final ────────────────────────────────────────────
        total_w = sum(w for _, w in scores.values())
        final = sum(s * w for s, w in scores.values()) / total_w
        final = float(np.clip(final, -1.0, 1.0))

        # Confiance = accord entre modèles (1 - std)
        score_vals = [s for s, _ in scores.values()]
        confidence = float(np.clip(1.0 - np.std(score_vals) * 2, 0.0, 1.0))

        return {
            "score":      round(final, 4),
            "label":      self._to_label(final),
            "confidence": round(confidence, 4),
            "breakdown":  {k: round(v[0], 4) for k, v in scores.items()},
        }

    def _finbert_score(self, text: str) -> Optional[float]:
        """Exécute FinBERT et retourne un score [-1, +1]."""
        try:
            results = self.finbert(text[:512])
            if not results:
                return None
            # results = [{"label": "positive", "score": 0.9}, …]
            if isinstance(results[0], list):
                results = results[0]

            probs = {r["label"].lower(): r["score"] for r in results}
            pos = probs.get("positive", 0.33)
            neg = probs.get("negative", 0.33)
            return pos - neg   # [-1, +1]
        except Exception:
            return None

    # ──────────────────────────────────────────────────────────────────────────
    #  ANALYSE D'UNE LISTE D'ARTICLES
    # ──────────────────────────────────────────────────────────────────────────

    def analyze_articles(
        self,
        articles: List[Dict],
        text_key: str = "title",
        weight_key: Optional[str] = None,
    ) -> Dict:
        """
        Analyse une liste d'articles et retourne un agrégat.

        Args:
            articles:   Liste de dicts (format NewsScraper)
            text_key:   Clé contenant le texte à analyser
            weight_key: Clé de pondération (ex: 'upvotes' pour Reddit)

        Returns:
            Dict avec :
            - aggregate_score  : float [-1, +1]
            - label            : str
            - distribution     : {bullish, neutral, bearish} counts
            - analyzed_items   : articles enrichis avec leur sentiment
        """
        if not articles:
            return {"aggregate_score": 0.0, "label": "NEUTRAL", "total": 0}

        analyzed = []
        for article in articles:
            text = article.get(text_key, "") or ""
            # Concaténer titre + description pour plus de contexte
            extra = article.get("description", "") or ""
            full_text = f"{text}. {extra[:200]}"

            result = self.analyze_text(full_text)
            weight = float(article.get(weight_key, 1)) if weight_key else 1.0
            weight = max(0.01, weight)

            analyzed.append({
                **article,
                "sentiment_score":  result["score"],
                "sentiment_label":  result["label"],
                "confidence":       result["confidence"],
                "_weight":          weight,
            })

        # Moyenne pondérée
        total_w = sum(a["_weight"] for a in analyzed)
        agg = sum(a["sentiment_score"] * a["_weight"] for a in analyzed) / total_w
        agg = float(np.clip(agg, -1.0, 1.0))

        # Distribution
        bullish = sum(1 for a in analyzed if a["sentiment_score"] > 0.1)
        bearish = sum(1 for a in analyzed if a["sentiment_score"] < -0.1)
        neutral = len(analyzed) - bullish - bearish

        return {
            "aggregate_score": round(agg, 4),
            "label":           self._to_label(agg),
            "total":           len(analyzed),
            "distribution": {
                "bullish": bullish,
                "neutral": neutral,
                "bearish": bearish,
                "bullish_pct": round(bullish / len(analyzed) * 100, 1),
                "bearish_pct": round(bearish / len(analyzed) * 100, 1),
            },
            "analyzed_items": analyzed,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  SCORE GLOBAL DU MARCHÉ
    # ──────────────────────────────────────────────────────────────────────────

    def market_sentiment_score(
        self,
        news_articles: List[Dict],
        reddit_posts: List[Dict] = None,
        fear_greed_value: Optional[float] = None,
        news_weight: float = 0.60,
        social_weight: float = 0.40,
    ) -> Dict:
        """
        Calcule le Score de Sentiment Global du Marché (SSGM).

        Combine :
        1. Sentiment des news (pondéré par recency)
        2. Sentiment des posts Reddit (pondéré par upvotes)
        3. Fear & Greed Index (si disponible)

        Args:
            news_articles:    Articles de news
            reddit_posts:     Posts Reddit (format: {title, score, ...})
            fear_greed_value: Valeur F&G (0-100), ou None
            news_weight:      Poids des news dans le score final
            social_weight:    Poids du social

        Returns:
            Dict avec ssgm_score, label, composants, signal de trading
        """
        components = {}

        # ── Sentiment News ─────────────────────────────────────────────────
        if news_articles:
            news_result = self.analyze_articles(news_articles, "title")
            components["news"] = {
                "score":  news_result["aggregate_score"],
                "weight": news_weight,
                "count":  news_result["total"],
                "dist":   news_result["distribution"],
            }

        # ── Sentiment Reddit ───────────────────────────────────────────────
        if reddit_posts:
            social_result = self.analyze_articles(
                reddit_posts, "title", weight_key="score"
            )
            components["reddit"] = {
                "score":  social_result["aggregate_score"],
                "weight": social_weight,
                "count":  social_result["total"],
            }

        # ── Score composite ────────────────────────────────────────────────
        if not components:
            return {"ssgm_score": 0.0, "label": "NEUTRAL", "signal": "HOLD"}

        total_w = sum(c["weight"] for c in components.values())
        ssgm = sum(c["score"] * c["weight"] for c in components.values()) / total_w

        # Ajustement Fear & Greed (biais contrarien)
        fng_adjustment = 0.0
        if fear_greed_value is not None:
            # F&G > 75 → légère pression baissière contrarien
            # F&G < 25 → légère pression haussière contrarien
            normalized = (fear_greed_value - 50) / 50   # [-1, +1]
            fng_adjustment = -normalized * 0.10          # Influence max ±10%
            components["fear_greed"] = {
                "raw_value": fear_greed_value,
                "adjustment": round(fng_adjustment, 4),
            }

        ssgm = float(np.clip(ssgm + fng_adjustment, -1.0, 1.0))

        # Interprétation trading
        if ssgm >= 0.30:
            signal = "BUY"
        elif ssgm <= -0.30:
            signal = "SELL"
        else:
            signal = "HOLD"

        result = {
            "ssgm_score":  round(ssgm, 4),
            "label":       self._to_label(ssgm),
            "signal":      signal,
            "components":  components,
            "interpretation": self._interpret_score(ssgm),
        }

        log.info("📊 SSGM: %.4f (%s) → Signal: %s", ssgm, result["label"], signal)
        return result

    # ──────────────────────────────────────────────────────────────────────────
    #  UTILITAIRES
    # ──────────────────────────────────────────────────────────────────────────

    def _preprocess(self, text: str) -> str:
        """Nettoie le texte pour l'analyse NLP."""
        text = re.sub(r"http\S+|www\S+", "", text)       # Supprimer URLs
        text = re.sub(r"@\w+", "", text)                  # Mentions
        text = re.sub(r"#(\w+)", r"\1", text)             # Hashtags → mots
        text = re.sub(r"[^\w\s\.\,\!\?\'\"$%]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:512]

    def _to_label(self, score: float) -> str:
        """Convertit un score numérique en label textuel."""
        if score >= 0.30:   return "BULLISH"
        if score <= -0.30:  return "BEARISH"
        return "NEUTRAL"

    def _interpret_score(self, score: float) -> str:
        """Retourne une interprétation textuelle du score SSGM."""
        if score >= 0.60:   return "Sentiment très positif — marché euphorique"
        if score >= 0.30:   return "Sentiment positif — optimisme modéré"
        if score >= 0.10:   return "Légèrement positif — prudence conseillée"
        if score >= -0.10:  return "Neutre — absence de signal clair"
        if score >= -0.30:  return "Légèrement négatif — incertitude"
        if score >= -0.60:  return "Sentiment négatif — pessimisme modéré"
        return "Sentiment très négatif — capitulation potentielle"

    def _neutral(self) -> Dict:
        return {"score": 0.0, "label": "NEUTRAL", "confidence": 0.5, "breakdown": {}}
