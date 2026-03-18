"""
================================================================================
  Quantum Trade Oracle — Modèles ML Classiques
================================================================================
  Implémente RandomForest et GradientBoosting pour la classification binaire
  de direction de marché.

  Ces modèles "basiques" sont en réalité souvent très compétitifs sur des
  données financières tabulaires. Ils servent de baseline solide dans l'ensemble.

  Features importantes :
  • Traitement natif des features tabulaires (pas de normalisation stricte)
  • Mesure d'importance des features pour l'interprétabilité
  • Validation croisée temporelle (TimeSeriesSplit)
  • Calibration des probabilités (CalibratedClassifierCV)
================================================================================
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit

from utils.logger import get_logger

log = get_logger("ClassicalModels")


class ClassicalMLModel:
    """
    Wrapper unifié pour RandomForest et GradientBoosting.

    Usage:
        model = ClassicalMLModel("random_forest")
        model.train(X_train, y_train)
        proba = model.predict_proba(X_test)
        result = model.evaluate(X_test, y_test)
    """

    SUPPORTED_MODELS = {
        "random_forest":     RandomForestClassifier,
        "gradient_boosting": GradientBoostingClassifier,
    }

    def __init__(
        self,
        model_type: str = "random_forest",
        params: Optional[Dict] = None,
        models_dir: str = "./data/models",
        calibrate: bool = True,
    ):
        """
        Args:
            model_type:  'random_forest' ou 'gradient_boosting'
            params:      Hyperparamètres (None = defaults sensés)
            models_dir:  Répertoire de sauvegarde
            calibrate:   Calibrer les probabilités (Platt scaling)
        """
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(f"model_type doit être dans {list(self.SUPPORTED_MODELS)}")

        self.model_type = model_type
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Paramètres par défaut selon le type
        default_params = self._default_params(model_type)
        self.params = {**default_params, **(params or {})}

        # Instancier le modèle de base
        base_model = self.SUPPORTED_MODELS[model_type](**self.params)

        # Calibrer les probabilités pour avoir des probas fiables
        if calibrate:
            self.model = CalibratedClassifierCV(
                base_model,
                method="sigmoid",   # Platt scaling — efficace pour arbres
                cv=3,
            )
        else:
            self.model = base_model

        self.feature_names: List[str] = []
        self.feature_importances: Dict[str, float] = {}
        self.is_trained = False
        self.training_metrics: Dict = {}

        log.info("Modèle initialisé : %s", model_type)

    def _default_params(self, model_type: str) -> Dict:
        """Paramètres par défaut testés et optimisés."""
        defaults = {
            "random_forest": {
                "n_estimators":    300,
                "max_depth":       None,
                "min_samples_split": 10,
                "min_samples_leaf": 5,
                "max_features":    "sqrt",
                "class_weight":    "balanced",
                "random_state":    42,
                "n_jobs":          -1,
            },
            "gradient_boosting": {
                "n_estimators":    200,
                "max_depth":       4,
                "learning_rate":   0.05,
                "subsample":       0.8,
                "min_samples_leaf": 10,
                "random_state":    42,
            },
        }
        return defaults[model_type]

    # ──────────────────────────────────────────────────────────────────────────
    #  ENTRAÎNEMENT
    # ──────────────────────────────────────────────────────────────────────────

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[List[str]] = None,
        cv_splits: int = 5,
    ) -> Dict:
        """
        Entraîne le modèle avec validation croisée temporelle.

        La validation croisée temporelle (TimeSeriesSplit) est cruciale :
        elle évite de "regarder dans le futur" lors de la validation.

        Args:
            X_train:      Features d'entraînement (n_samples, n_features)
            y_train:      Labels (n_samples,) — 0 ou 1
            feature_names: Noms des features pour l'importance
            cv_splits:    Nombre de folds pour la CV temporelle

        Returns:
            Dict avec métriques d'entraînement
        """
        X = X_train if isinstance(X_train, np.ndarray) else X_train.values
        y = y_train if isinstance(y_train, np.ndarray) else y_train.values

        self.feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]

        log.info("Entraînement %s sur %d samples, %d features…",
                 self.model_type, len(X), X.shape[1])

        # ── Validation croisée temporelle ─────────────────────────────────
        tscv = TimeSeriesSplit(n_splits=cv_splits)
        cv_scores = {"accuracy": [], "f1": [], "auc": []}

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train, y_fold_val = y[train_idx], y[val_idx]

            # Cloner le modèle pour chaque fold
            from sklearn.base import clone
            fold_model = clone(self.model)
            fold_model.fit(X_fold_train, y_fold_train)

            y_pred    = fold_model.predict(X_fold_val)
            y_proba   = fold_model.predict_proba(X_fold_val)[:, 1]

            cv_scores["accuracy"].append(accuracy_score(y_fold_val, y_pred))
            cv_scores["f1"].append(f1_score(y_fold_val, y_pred, zero_division=0))
            cv_scores["auc"].append(roc_auc_score(y_fold_val, y_proba))

            log.debug("Fold %d — acc=%.3f f1=%.3f auc=%.3f",
                      fold + 1,
                      cv_scores["accuracy"][-1],
                      cv_scores["f1"][-1],
                      cv_scores["auc"][-1])

        # ── Entraînement final sur toutes les données ─────────────────────
        self.model.fit(X, y)
        self.is_trained = True

        # ── Importance des features ───────────────────────────────────────
        self._extract_feature_importance()

        self.training_metrics = {
            "cv_accuracy":  float(np.mean(cv_scores["accuracy"])),
            "cv_f1":        float(np.mean(cv_scores["f1"])),
            "cv_auc":       float(np.mean(cv_scores["auc"])),
            "cv_accuracy_std": float(np.std(cv_scores["accuracy"])),
            "n_samples":    len(X),
            "n_features":   X.shape[1],
        }

        log.info("✅ %s entraîné — CV AUC: %.4f ± %.4f",
                 self.model_type,
                 self.training_metrics["cv_auc"],
                 float(np.std(cv_scores["auc"])))

        return self.training_metrics

    def _extract_feature_importance(self):
        """Extrait l'importance des features depuis le modèle calibré."""
        try:
            # CalibratedClassifierCV encapsule le modèle de base
            base = self.model
            if hasattr(base, "estimators_"):  # CalibratedCV
                estimators = [e.estimator for e in base.estimators_
                              if hasattr(e, "estimator")]
                if estimators and hasattr(estimators[0], "feature_importances_"):
                    importances = np.mean(
                        [e.feature_importances_ for e in estimators], axis=0
                    )
                    self.feature_importances = dict(
                        sorted(zip(self.feature_names, importances),
                               key=lambda x: x[1], reverse=True)
                    )
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    #  PRÉDICTION
    # ──────────────────────────────────────────────────────────────────────────

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Retourne les probabilités de classe pour chaque sample.

        Returns:
            Array (n_samples, 2) où col[1] = P(hausse)
        """
        self._check_trained()
        X = X if isinstance(X, np.ndarray) else X.values
        return self.model.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Retourne les labels prédits (0 ou 1)."""
        self._check_trained()
        X = X if isinstance(X, np.ndarray) else X.values
        return self.model.predict(X)

    def predict_single(self, x: np.ndarray) -> Dict:
        """
        Prédit pour un seul vecteur de features.

        Returns:
            Dict avec:
            - bullish_prob  : P(hausse)
            - bearish_prob  : P(baisse)
            - prediction    : 'BUY' | 'SELL' | 'HOLD'
            - confidence    : max(P(hausse), P(baisse))
        """
        self._check_trained()
        x = x.reshape(1, -1) if x.ndim == 1 else x
        proba = self.predict_proba(x)[0]

        bullish_prob = float(proba[1])
        bearish_prob = float(proba[0])

        if bullish_prob > 0.60:
            prediction = "BUY"
        elif bearish_prob > 0.60:
            prediction = "SELL"
        else:
            prediction = "HOLD"

        return {
            "bullish_prob":  round(bullish_prob, 4),
            "bearish_prob":  round(bearish_prob, 4),
            "prediction":    prediction,
            "confidence":    round(max(bullish_prob, bearish_prob), 4),
            "model":         self.model_type,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  ÉVALUATION
    # ──────────────────────────────────────────────────────────────────────────

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Évalue le modèle sur le jeu de test.

        Returns:
            Dict avec accuracy, f1, auc, rapport complet
        """
        self._check_trained()
        X = X_test if isinstance(X_test, np.ndarray) else X_test.values
        y = y_test if isinstance(y_test, np.ndarray) else y_test.values

        y_pred  = self.predict(X)
        y_proba = self.predict_proba(X)[:, 1]

        metrics = {
            "accuracy":    round(float(accuracy_score(y, y_pred)), 4),
            "f1_score":    round(float(f1_score(y, y_pred, zero_division=0)), 4),
            "roc_auc":     round(float(roc_auc_score(y, y_proba)), 4),
            "report":      classification_report(y, y_pred, target_names=["BAISSE", "HAUSSE"]),
            "n_test":      len(y),
        }

        log.info("%s Test — acc=%.4f f1=%.4f auc=%.4f",
                 self.model_type, metrics["accuracy"], metrics["f1_score"], metrics["roc_auc"])

        return metrics

    def top_features(self, n: int = 20) -> List[Tuple[str, float]]:
        """Retourne les N features les plus importantes."""
        return list(self.feature_importances.items())[:n]

    # ──────────────────────────────────────────────────────────────────────────
    #  PERSISTANCE
    # ──────────────────────────────────────────────────────────────────────────

    def save(self, filename: Optional[str] = None) -> str:
        """Sauvegarde le modèle en pickle."""
        self._check_trained()
        fname = filename or f"{self.model_type}.pkl"
        path = self.models_dir / fname
        state = {
            "model":               self.model,
            "feature_names":       self.feature_names,
            "feature_importances": self.feature_importances,
            "training_metrics":    self.training_metrics,
            "params":              self.params,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)
        log.info("💾 Modèle sauvegardé : %s", path)
        return str(path)

    def load(self, filename: Optional[str] = None) -> bool:
        """Charge le modèle depuis le disque."""
        fname = filename or f"{self.model_type}.pkl"
        path = self.models_dir / fname
        if not path.exists():
            log.warning("Modèle non trouvé : %s", path)
            return False
        try:
            with open(path, "rb") as f:
                state = pickle.load(f)
            self.model               = state["model"]
            self.feature_names       = state["feature_names"]
            self.feature_importances = state["feature_importances"]
            self.training_metrics    = state["training_metrics"]
            self.is_trained          = True
            log.info("✅ Modèle chargé : %s", path)
            return True
        except Exception as e:
            log.error("Erreur chargement : %s", str(e))
            return False

    def _check_trained(self):
        if not self.is_trained:
            raise RuntimeError(f"Le modèle '{self.model_type}' n'est pas encore entraîné.")
