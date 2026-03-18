"""
================================================================================
  Quantum Trade Oracle — Modèle LSTM (PyTorch)
================================================================================
  Réseau de neurones récurrents LSTM bidirectionnel pour capturer les
  dépendances temporelles à long terme dans les séries de prix.

  Architecture :
  ┌──────────────────────────────────────────────────────────┐
  │  Input     (batch, seq_len, n_features)                  │
  │     │                                                    │
  │     ▼                                                    │
  │  Bidirectionnel LSTM ×2 couches + Dropout                │
  │     │  Capture les patterns passés ET contextuels        │
  │     │                                                    │
  │     ▼                                                    │
  │  Attention (pondération des timesteps importants)        │
  │     │                                                    │
  │     ▼                                                    │
  │  Dense (128 → 64 → 1) + BatchNorm + Dropout              │
  │     │                                                    │
  │     ▼                                                    │
  │  Sigmoid → P(hausse) ∈ [0, 1]                           │
  └──────────────────────────────────────────────────────────┘

  Points clés :
  • LSTM bidirectionnel : lit la séquence dans les 2 sens
  • Mécanisme d'attention : poids différents selon les timesteps
  • Early stopping : évite l'overfitting
  • Scheduler de LR : ReduceLROnPlateau
================================================================================
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from utils.logger import get_logger

log = get_logger("LSTMModel")


# ──────────────────────────────────────────────────────────────────────────────
#  ARCHITECTURE PYTORCH
# ──────────────────────────────────────────────────────────────────────────────

def _build_lstm_network(n_features: int, hidden_size: int, num_layers: int, dropout: float):
    """Construit le réseau LSTM avec PyTorch."""
    try:
        import torch
        import torch.nn as nn

        class AttentionLSTM(nn.Module):
            """
            LSTM bidirectionnel avec mécanisme d'attention.

            L'attention permet au modèle de se concentrer sur les
            timesteps les plus informatifs de la séquence.
            """

            def __init__(self):
                super().__init__()

                # LSTM bidirectionnel
                self.lstm = nn.LSTM(
                    input_size=n_features,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    batch_first=True,
                    bidirectional=True,     # Lit la séquence dans les 2 sens
                    dropout=dropout if num_layers > 1 else 0.0,
                )

                # Couche d'attention (apprise durant l'entraînement)
                self.attention = nn.Sequential(
                    nn.Linear(hidden_size * 2, hidden_size),
                    nn.Tanh(),
                    nn.Linear(hidden_size, 1),
                    nn.Softmax(dim=1),      # Poids normalisés sur la séquence
                )

                # Couches de classification
                self.classifier = nn.Sequential(
                    nn.Linear(hidden_size * 2, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(dropout),

                    nn.Linear(128, 64),
                    nn.BatchNorm1d(64),
                    nn.ReLU(),
                    nn.Dropout(dropout / 2),

                    nn.Linear(64, 1),
                    nn.Sigmoid(),           # Sortie probabilité [0, 1]
                )

            def forward(self, x):
                # x : (batch, seq_len, n_features)
                lstm_out, _ = self.lstm(x)
                # lstm_out : (batch, seq_len, hidden_size * 2)

                # Calcul des poids d'attention
                attn_weights = self.attention(lstm_out)
                # attn_weights : (batch, seq_len, 1)

                # Contexte pondéré
                context = (lstm_out * attn_weights).sum(dim=1)
                # context : (batch, hidden_size * 2)

                # Classification
                out = self.classifier(context)
                return out.squeeze(-1)   # (batch,)

        return AttentionLSTM()

    except ImportError:
        return None


# ──────────────────────────────────────────────────────────────────────────────
#  WRAPPER DE HAUT NIVEAU
# ──────────────────────────────────────────────────────────────────────────────

class LSTMModel:
    """
    Modèle LSTM bidirectionnel avec attention pour la prédiction de marché.

    Usage:
        model = LSTMModel(n_features=50)
        model.train(X_train, y_train)
        proba = model.predict_proba(X_test)
    """

    def __init__(
        self,
        n_features: int = 50,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        patience: int = 10,
        models_dir: str = "./data/models",
    ):
        """
        Args:
            n_features:    Nombre de features d'entrée
            hidden_size:   Taille des cellules LSTM
            num_layers:    Nombre de couches LSTM empilées
            dropout:       Taux de dropout pour la régularisation
            epochs:        Nombre d'époques max (early stopping possible)
            batch_size:    Taille des mini-batches
            learning_rate: Taux d'apprentissage initial
            patience:      Epochs sans amélioration avant early stopping
            models_dir:    Répertoire de sauvegarde
        """
        self.n_features    = n_features
        self.hidden_size   = hidden_size
        self.num_layers    = num_layers
        self.dropout       = dropout
        self.epochs        = epochs
        self.batch_size    = batch_size
        self.learning_rate = learning_rate
        self.patience      = patience
        self.models_dir    = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.network       = None
        self.device        = None
        self.is_trained    = False
        self.training_history: List[Dict] = []

        self._init_torch()

    def _init_torch(self):
        """Initialise PyTorch et détecte le device (GPU/CPU)."""
        try:
            import torch
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            log.info("PyTorch disponible — device: %s", self.device)
        except ImportError:
            log.warning("⚠️ PyTorch non installé. pip install torch")
            self.device = None

    def _build(self):
        """Construit le réseau si pas encore créé."""
        if self.network is None:
            self.network = _build_lstm_network(
                self.n_features, self.hidden_size, self.num_layers, self.dropout
            )
            if self.network and self.device:
                self.network = self.network.to(self.device)

    # ──────────────────────────────────────────────────────────────────────────
    #  ENTRAÎNEMENT
    # ──────────────────────────────────────────────────────────────────────────

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Entraîne le LSTM avec validation et early stopping.

        Args:
            X_train: Array (n_samples, seq_len, n_features)
            y_train: Array (n_samples,) — labels 0/1
            X_val:   Array de validation (optionnel, sinon 20% du train)
            y_val:   Labels de validation

        Returns:
            Dict avec métriques d'entraînement
        """
        if self.device is None:
            log.error("PyTorch non disponible — entraînement LSTM impossible")
            return {"error": "pytorch_not_available"}

        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        # Mettre à jour n_features si besoin
        if X_train.ndim == 3:
            self.n_features = X_train.shape[2]

        self._build()

        log.info("Entraînement LSTM — samples=%d | seq=%d | features=%d | device=%s",
                 X_train.shape[0], X_train.shape[1], X_train.shape[2], self.device)

        # ── Créer les jeux de données ──────────────────────────────────────
        if X_val is None:
            split = int(len(X_train) * 0.85)
            X_val, y_val = X_train[split:], y_train[split:]
            X_train, y_train = X_train[:split], y_train[:split]

        def to_tensor_dataset(X, y):
            return TensorDataset(
                torch.FloatTensor(X).to(self.device),
                torch.FloatTensor(y).to(self.device),
            )

        train_ds = to_tensor_dataset(X_train, y_train)
        val_ds   = to_tensor_dataset(X_val, y_val)

        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=False)
        val_loader   = DataLoader(val_ds,   batch_size=self.batch_size, shuffle=False)

        # ── Optimizer, loss, scheduler ────────────────────────────────────
        optimizer = torch.optim.AdamW(
            self.network.parameters(),
            lr=self.learning_rate,
            weight_decay=1e-4,
        )
        # Gestion du déséquilibre de classes
        pos_weight = torch.tensor(
            [(1 - y_train.mean()) / (y_train.mean() + 1e-6)]
        ).to(self.device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, patience=5, factor=0.5, min_lr=1e-6
        )

        # ── Boucle d'entraînement ─────────────────────────────────────────
        best_val_loss  = float("inf")
        best_state     = None
        patience_count = 0
        self.training_history = []

        for epoch in range(1, self.epochs + 1):
            # Phase d'entraînement
            self.network.train()
            train_losses = []

            for X_batch, y_batch in train_loader:
                optimizer.zero_grad()
                logits = self.network(X_batch)
                loss   = criterion(logits, y_batch)
                loss.backward()
                # Gradient clipping pour stabilité
                nn.utils.clip_grad_norm_(self.network.parameters(), max_norm=1.0)
                optimizer.step()
                train_losses.append(loss.item())

            # Phase de validation
            self.network.eval()
            val_losses, val_preds, val_labels = [], [], []

            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    logits = self.network(X_batch)
                    val_losses.append(criterion(logits, y_batch).item())
                    probs = torch.sigmoid(logits).cpu().numpy()
                    val_preds.extend(probs)
                    val_labels.extend(y_batch.cpu().numpy())

            train_loss = np.mean(train_losses)
            val_loss   = np.mean(val_losses)

            # Accuracy de validation
            val_preds_bin = (np.array(val_preds) > 0.5).astype(int)
            from sklearn.metrics import accuracy_score
            val_acc = accuracy_score(val_labels, val_preds_bin)

            scheduler.step(val_loss)
            current_lr = optimizer.param_groups[0]["lr"]

            self.training_history.append({
                "epoch": epoch, "train_loss": train_loss,
                "val_loss": val_loss, "val_acc": val_acc, "lr": current_lr,
            })

            if epoch % 10 == 0 or epoch == 1:
                log.info("Epoch %3d/%d | train_loss=%.4f | val_loss=%.4f | val_acc=%.4f | lr=%.6f",
                         epoch, self.epochs, train_loss, val_loss, val_acc, current_lr)

            # Early stopping
            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                best_state    = {k: v.clone() for k, v in self.network.state_dict().items()}
                patience_count = 0
            else:
                patience_count += 1
                if patience_count >= self.patience:
                    log.info("Early stopping à l'epoch %d", epoch)
                    break

        # Restaurer le meilleur état
        if best_state:
            self.network.load_state_dict(best_state)

        self.is_trained = True

        best = min(self.training_history, key=lambda x: x["val_loss"])
        metrics = {
            "best_epoch":    best["epoch"],
            "best_val_loss": round(best["val_loss"], 6),
            "best_val_acc":  round(best["val_acc"], 4),
            "total_epochs":  len(self.training_history),
        }
        log.info("✅ LSTM entraîné — best_epoch=%d val_acc=%.4f",
                 metrics["best_epoch"], metrics["best_val_acc"])
        return metrics

    # ──────────────────────────────────────────────────────────────────────────
    #  PRÉDICTION
    # ──────────────────────────────────────────────────────────────────────────

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Retourne les probabilités P(hausse) pour chaque sample.

        Args:
            X: Array (n_samples, seq_len, n_features)

        Returns:
            Array (n_samples, 2) — [P(baisse), P(hausse)]
        """
        if not self.is_trained:
            raise RuntimeError("Le LSTM n'est pas encore entraîné.")

        import torch

        self.network.eval()
        probs = []

        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            # Traitement par batch pour éviter les OOM
            for i in range(0, len(X_tensor), 64):
                batch = X_tensor[i : i + 64]
                logits = self.network(batch)
                p = torch.sigmoid(logits).cpu().numpy()
                probs.extend(p)

        probs = np.array(probs)
        return np.column_stack([1 - probs, probs])   # [P(baisse), P(hausse)]

    def predict_single(self, x: np.ndarray) -> Dict:
        """Prédit pour une séquence unique."""
        x = x.reshape(1, *x.shape) if x.ndim == 2 else x
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
            "bullish_prob": round(bullish_prob, 4),
            "bearish_prob": round(bearish_prob, 4),
            "prediction":   prediction,
            "confidence":   round(max(bullish_prob, bearish_prob), 4),
            "model":        "lstm",
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  PERSISTANCE
    # ──────────────────────────────────────────────────────────────────────────

    def save(self, filename: str = "lstm_model.pt") -> str:
        """Sauvegarde le modèle PyTorch."""
        if not self.is_trained:
            raise RuntimeError("Modèle non entraîné.")

        import torch

        path = self.models_dir / filename
        torch.save({
            "state_dict":   self.network.state_dict(),
            "config": {
                "n_features":  self.n_features,
                "hidden_size": self.hidden_size,
                "num_layers":  self.num_layers,
                "dropout":     self.dropout,
            },
            "history": self.training_history,
        }, path)
        log.info("💾 LSTM sauvegardé : %s", path)
        return str(path)

    def load(self, filename: str = "lstm_model.pt") -> bool:
        """Charge le modèle PyTorch."""
        import torch

        path = self.models_dir / filename
        if not path.exists():
            log.warning("Fichier LSTM non trouvé : %s", path)
            return False
        try:
            checkpoint = torch.load(path, map_location=self.device)
            cfg = checkpoint["config"]
            self.n_features  = cfg["n_features"]
            self.hidden_size = cfg["hidden_size"]
            self.num_layers  = cfg["num_layers"]
            self.dropout     = cfg["dropout"]
            self._build()
            self.network.load_state_dict(checkpoint["state_dict"])
            self.training_history = checkpoint.get("history", [])
            self.is_trained = True
            log.info("✅ LSTM chargé : %s", path)
            return True
        except Exception as e:
            log.error("Erreur chargement LSTM : %s", str(e))
            return False
