"""
================================================================================
  Quantum Trade Oracle — Ensemble de Modèles
================================================================================
  Combine les prédictions de 4 modèles avec pondération configurable.

  Modèles intégrés :
  ┌─────────────────────┬────────┬─────────────────────────────────┐
  │ Modèle              │ Poids  │ Point fort                      │
  ├─────────────────────┼────────┼─────────────────────────────────┤
  │ RandomForest        │  20%   │ Robustesse, résistant au bruit  │
  │ GradientBoosting    │  20%   │ Précision sur données tabulaires│
  │ LSTM                │  35%   │ Dépendances temporelles         │
  │ Transformer         │  25%   │ Patterns complexes, long-range  │
  └─────────────────────┴────────┴─────────────────────────────────┘

  Stratégies disponibles :
  1. Weighted Average  → Moyenne pondérée fixe
  2. Confidence-Based  → Poids proportionnel à la confiance
  3. Stacking          → Méta-modèle apprend les poids optimaux
================================================================================
"""

from sklearn.metrics import roc_auc_score, accuracy_score
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression

from utils.logger import get_logger
from ai_models.classical_models import ClassicalMLModel
from ai_models.lstm_model import LSTMModel
from ai_models.transformer_model import TransformerModel

log = get_logger("ModelEnsemble")


class ModelEnsemble:
    """
    Ensemble qui agrège les prédictions de tous les modèles.

    Usage:
        ensemble = ModelEnsemble()
        ensemble.train_all(X_tab, y_tab, X_seq, y_seq)
        result = ensemble.predict(x_tabular, x_sequence)
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        models_dir: str = "./data/models",
    ):
        """
        Args:
            weights:    Poids par modèle (None = defaults)
            models_dir: Répertoire de sauvegarde
        """
        self.weights = weights or {
            "random_forest":     0.20,
            "gradient_boosting": 0.20,
            "lstm":              0.35,
            "transformer":       0.25,
        }

        # Normaliser les poids pour sommer à 1
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

        # Instancier les modèles
        self.rf          = ClassicalMLModel("random_forest",     models_dir=models_dir)
        self.gb          = ClassicalMLModel("gradient_boosting", models_dir=models_dir)
        self.lstm        = LSTMModel(models_dir=models_dir)
        self.transformer = TransformerModel(models_dir=models_dir)

        # Méta-modèle pour le stacking
        self.meta_model  = LogisticRegression(random_state=42)
        self._meta_fitted = False

        self.is_trained  = False
        log.info("Ensemble initialisé — poids: %s", self.weights)

    # ──────────────────────────────────────────────────────────────────────────
    #  ENTRAÎNEMENT
    # ──────────────────────────────────────────────────────────────────────────

    def train_all(
        self,
        X_tab_train: np.ndarray,
        y_train: np.ndarray,
        X_seq_train: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Dict]:
        """
        Entraîne tous les modèles de l'ensemble.

        Les modèles tabulaires (RF, GB) utilisent X_tab_train (2D).
        Les modèles séquentiels (LSTM, Transformer) utilisent X_seq_train (3D).

        Args:
            X_tab_train:  Features tabulaires (n_samples, n_features)
            y_train:      Labels (n_samples,)
            X_seq_train:  Séquences 3D (n_samples, seq_len, n_features)
            feature_names: Noms des features (pour importance RF/GB)

        Returns:
            Dict {nom_modele: métriques}
        """
        results = {}
        log.info("═" * 60)
        log.info("  Démarrage de l'entraînement de l'ensemble")
        log.info("═" * 60)

        # ── RandomForest ───────────────────────────────────────────────────
        log.info("▶ RandomForest…")
        try:
            r = self.rf.train(X_tab_train, y_train, feature_names)
            results["random_forest"] = r
            log.info("  ✅ RF — AUC: %.4f", r.get("cv_auc", 0))
        except Exception as e:
            log.error("  ❌ RF échoué: %s", str(e))
            results["random_forest"] = {"error": str(e)}

        # ── GradientBoosting ───────────────────────────────────────────────
        log.info("▶ GradientBoosting…")
        try:
            r = self.gb.train(X_tab_train, y_train, feature_names)
            results["gradient_boosting"] = r
            log.info("  ✅ GB — AUC: %.4f", r.get("cv_auc", 0))
        except Exception as e:
            log.error("  ❌ GB échoué: %s", str(e))
            results["gradient_boosting"] = {"error": str(e)}

        # ── LSTM ───────────────────────────────────────────────────────────
        if X_seq_train is not None:
            log.info("▶ LSTM (PyTorch)…")
            try:
                self.lstm.n_features = X_seq_train.shape[2]
                r = self.lstm.train(X_seq_train, y_train)
                results["lstm"] = r
                log.info("  ✅ LSTM — val_acc: %.4f", r.get("best_val_acc", 0))
            except Exception as e:
                log.error("  ❌ LSTM échoué: %s", str(e))
                results["lstm"] = {"error": str(e)}

            # ── Transformer ────────────────────────────────────────────────
            log.info("▶ Transformer (PyTorch)…")
            try:
                self.transformer.n_features = X_seq_train.shape[2]
                r = self.transformer.train(X_seq_train, y_train)
                results["transformer"] = r
                log.info("  ✅ Transformer — val_acc: %.4f", r.get("best_val_acc", 0))
            except Exception as e:
                log.error("  ❌ Transformer échoué: %s", str(e))
                results["transformer"] = {"error": str(e)}

        self.is_trained = True
        log.info("═" * 60)
        log.info("  Ensemble entraîné avec succès")
        log.info("═" * 60)
        return results

    # ──────────────────────────────────────────────────────────────────────────
    #  PRÉDICTION
    # ──────────────────────────────────────────────────────────────────────────

    def predict(
        self,
        x_tabular: np.ndarray,
        x_sequence: Optional[np.ndarray] = None,
        strategy: str = "confidence_weighted",
    ) -> Dict:
        """
        Génère une prédiction ensemble agrégée.

        Args:
            x_tabular:  Vecteur de features 1D ou 2D (n_features,)
            x_sequence: Séquence 2D ou 3D (seq_len, n_features)
            strategy:   'weighted' | 'confidence_weighted' | 'stacking'

        Returns:
            Dict avec:
            - bullish_prob  : Probabilité de hausse [0, 1]
            - bearish_prob  : Probabilité de baisse [0, 1]
            - prediction    : 'BUY' | 'SELL' | 'HOLD'
            - confidence    : Score de confiance[0, 1]
            - models        : Détail par modèle
            - agreement     : Niveau d'accord entre les modèles
        """
        individual: Dict[str, Dict] = {}

        # ── RandomForest ───────────────────────────────────────────────────
        if self.rf.is_trained:
            x = x_tabular.reshape(1, -1) if x_tabular.ndim == 1 else x_tabular
            try:
                individual["random_forest"] = self.rf.predict_single(x)
            except Exception as e:
                log.debug("RF prediction error: %s", str(e))

        # ── GradientBoosting ───────────────────────────────────────────────
        if self.gb.is_trained:
            x = x_tabular.reshape(1, -1) if x_tabular.ndim == 1 else x_tabular
            try:
                individual["gradient_boosting"] = self.gb.predict_single(x)
            except Exception as e:
                log.debug("GB prediction error: %s", str(e))

        # ── LSTM ───────────────────────────────────────────────────────────
        if self.lstm.is_trained and x_sequence is not None:
            try:
                individual["lstm"] = self.lstm.predict_single(x_sequence)
            except Exception as e:
                log.debug("LSTM prediction error: %s", str(e))

        # ── Transformer ────────────────────────────────────────────────────
        if self.transformer.is_trained and x_sequence is not None:
            try:
                individual["transformer"] = self.transformer.predict_single(x_sequence)
            except Exception as e:
                log.debug("Transformer prediction error: %s", str(e))

        if not individual:
            return self._neutral_result()

        # ── Agrégation ─────────────────────────────────────────────────────
        if strategy == "confidence_weighted":
            final = self._confidence_weighted(individual)
        elif strategy == "stacking" and self._meta_fitted:
            final = self._stacking_predict(individual)
        else:
            final = self._fixed_weighted(individual)

        # ── Décision finale ────────────────────────────────────────────────
        bull = final["bullish_prob"]
        bear = final["bearish_prob"]

        if bull >= 0.60:
            prediction = "BUY"
        elif bear >= 0.60:
            prediction = "SELL"
        else:
            prediction = "HOLD"

        # Accord entre les modèles (0 = désaccord total, 1 = consensus)
        predictions =[d.get("prediction", "HOLD") for d in individual.values()]
        agreement = predictions.count(prediction) / len(predictions)

        return {
            "bullish_prob":  round(bull, 4),
            "bearish_prob":  round(bear, 4),
            "prediction":    prediction,
            "confidence":    round(max(bull, bear), 4),
            "agreement":     round(agreement, 4),
            "models":        individual,
            "n_models_used": len(individual),
            "strategy":      strategy,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  STRATÉGIES D'AGRÉGATION
    # ──────────────────────────────────────────────────────────────────────────

    def _fixed_weighted(self, preds: Dict) -> Dict:
        """Moyenne pondérée fixe selon self.weights."""
        total_w = 0.0
        w_bull = w_bear = 0.0

        for name, pred in preds.items():
            w = self.weights.get(name, 0.1)
            total_w += w
            w_bull  += pred.get("bullish_prob", 0.5) * w
            w_bear  += pred.get("bearish_prob", 0.5) * w

        return {
            "bullish_prob": float(np.clip(w_bull / total_w, 0, 1)),
            "bearish_prob": float(np.clip(w_bear / total_w, 0, 1)),
        }

    def _confidence_weighted(self, preds: Dict) -> Dict:
        """Pondère chaque modèle par (poids_fixe × confiance)."""
        total_w = 0.0
        w_bull = w_bear = 0.0

        for name, pred in preds.items():
            base_w = self.weights.get(name, 0.1)
            conf   = pred.get("confidence", 0.5)
            w      = base_w * conf    # Plus confiant = plus de poids
            total_w += w
            w_bull  += pred.get("bullish_prob", 0.5) * w
            w_bear  += pred.get("bearish_prob", 0.5) * w

        if total_w == 0:
            return {"bullish_prob": 0.5, "bearish_prob": 0.5}

        return {
            "bullish_prob": float(np.clip(w_bull / total_w, 0, 1)),
            "bearish_prob": float(np.clip(w_bear / total_w, 0, 1)),
        }

    def _stacking_predict(self, preds: Dict) -> Dict:
        """Utilise le méta-modèle de stacking."""
        features = []
        for name in ["random_forest", "gradient_boosting", "lstm", "transformer"]:
            p = preds.get(name, {})
            features.extend([p.get("bullish_prob", 0.5), p.get("bearish_prob", 0.5)])

        x = np.array(features).reshape(1, -1)
        proba = self.meta_model.predict_proba(x)[0]
        return {"bullish_prob": float(proba[1]), "bearish_prob": float(proba[0])}

    # ==========================
    # CORRECTIONS À PARTIR D'ICI
    # ==========================
    
    def evaluate_all(self, X_tab_test, y_test, X_seq_test=None) -> Dict:
        """Évalue tous les modèles sur le jeu de test."""
        results = {}

        if self.rf.is_trained:
            results["random_forest"] = self.rf.evaluate(X_tab_test, y_test)
        if self.gb.is_trained:
            results["gradient_boosting"] = self.gb.evaluate(X_tab_test, y_test)
            
        if self.lstm.is_trained and X_seq_test is not None:
            proba = self.lstm.predict_proba(X_seq_test)[:, 1]
            preds = (proba > 0.5).astype(int)
            min_len = min(len(y_test), len(preds))
            
            # Utilisation de result["lstm"] au lieu d'écraser la variable "results ="
            results["lstm"] = {
                "accuracy": round(float(accuracy_score(y_test[:min_len], preds[:min_len])), 4)
            }
            
        if self.transformer.is_trained and X_seq_test is not None:
            proba = self.transformer.predict_proba(X_seq_test)[:, 1]
            preds = (proba > 0.5).astype(int)
            min_len = min(len(y_test), len(preds), len(proba))

            # Exécution propre au transformer pour éviter les copier-coller ratés 
            results["transformer"] = {
                "samples_used": min_len,
                "roc_auc": round(float(roc_auc_score(y_test[:min_len], proba[:min_len])), 4),
            }

        return results


    def save_all(self):
        """Sauvegarde tous les modèles."""
        if self.rf.is_trained:          self.rf.save()
        if self.gb.is_trained:          self.gb.save()
        if self.lstm.is_trained:        self.lstm.save()
        if self.transformer.is_trained: self.transformer.save()

    def load_all(self) -> bool:
        """Charge tous les modèles depuis le disque."""
        ok = (
            self.rf.load() |
            self.gb.load() |
            self.lstm.load() |
            self.transformer.load()
        )
        if ok:
            self.is_trained = True
        return ok

    def _neutral_result(self) -> Dict:
        return {
            "bullish_prob":  0.5,    
            "bearish_prob":  0.5,
            "prediction":    "HOLD", 
            "confidence":    0.5,
            "agreement":     0.0,    
            "models":        {},
            "n_models_used": 0,      
            "strategy":      "none",
        }