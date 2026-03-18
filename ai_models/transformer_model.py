"""
================================================================================
  Quantum Trade Oracle — Modèle Transformer (PyTorch)
================================================================================
  Transformer adapté pour les séries temporelles financières.
  Inspiré du papier "Temporal Fusion Transformer" et "Informer".

  Architecture :
  ┌──────────────────────────────────────────────────────────┐
  │  Input     (batch, seq_len, n_features)                  │
  │     │                                                    │
  │     ▼                                                    │
  │  Linear Projection → d_model                            │
  │     │                                                    │
  │     ▼                                                    │
  │  Positional Encoding (sinusoïdal)                        │
  │     │  Injecte l'information temporelle                  │
  │     │                                                    │
  │     ▼                                                    │
  │  Transformer Encoder ×N couches                          │
  │     │  Multi-Head Self-Attention + FFN + LayerNorm       │
  │     │                                                    │
  │     ▼                                                    │
  │  Global Average Pooling (agrège la séquence)            │
  │     │                                                    │
  │     ▼                                                    │
  │  Dense → Sigmoid → P(hausse) ∈ [0, 1]                   │
  └──────────────────────────────────────────────────────────┘

  Avantages vs LSTM :
  • Attention parallélisable (plus rapide à entraîner)
  • Capture les dépendances à longue distance sans dégradation
  • Interprétabilité via les poids d'attention
================================================================================
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from utils.logger import get_logger

log = get_logger("TransformerModel")


# ──────────────────────────────────────────────────────────────────────────────
#  ARCHITECTURE PYTORCH
# ──────────────────────────────────────────────────────────────────────────────

def _build_transformer_network(
    n_features: int,
    d_model: int,
    nhead: int,
    num_layers: int,
    dim_feedforward: int,
    dropout: float,
):
    """Construit le réseau Transformer avec PyTorch."""
    try:
        import torch
        import torch.nn as nn
        import math

        class PositionalEncoding(nn.Module):
            """
            Encodage positionnel sinusoïdal (Vaswani et al., 2017).
            Injecte l'information sur la position temporelle de chaque timestep.
            """

            def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
                super().__init__()
                self.dropout = nn.Dropout(p=dropout)

                # Matrice d'encodage positionnel
                pe = torch.zeros(max_len, d_model)
                position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
                div_term = torch.exp(
                    torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
                )
                pe[:, 0::2] = torch.sin(position * div_term)
                pe[:, 1::2] = torch.cos(position * div_term)
                pe = pe.unsqueeze(0)   # (1, max_len, d_model)
                self.register_buffer("pe", pe)

            def forward(self, x):
                # x : (batch, seq_len, d_model)
                x = x + self.pe[:, : x.size(1), :]
                return self.dropout(x)

        class FinancialTransformer(nn.Module):
            """
            Transformer encoder pour la classification de séries temporelles.
            """

            def __init__(self):
                super().__init__()

                # Projection des features vers l'espace d_model
                self.input_projection = nn.Linear(n_features, d_model)
                self.input_norm       = nn.LayerNorm(d_model)

                # Encodage positionnel
                self.pos_encoding = PositionalEncoding(d_model, dropout=dropout)

                # Couches du Transformer Encoder
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model=d_model,
                    nhead=nhead,
                    dim_feedforward=dim_feedforward,
                    dropout=dropout,
                    activation="gelu",   # GELU > ReLU pour les transformers
                    batch_first=True,    # (batch, seq, features) plutôt que (seq, batch, features)
                )
                self.transformer_encoder = nn.TransformerEncoder(
                    encoder_layer,
                    num_layers=num_layers,
                    norm=nn.LayerNorm(d_model),
                )

                # Tête de classification
                self.classifier = nn.Sequential(
                    nn.Linear(d_model, d_model // 2),
                    nn.GELU(),
                    nn.Dropout(dropout),
                    nn.Linear(d_model // 2, 1),
                    # Pas de Sigmoid ici : on utilise BCEWithLogitsLoss
                )

            def forward(self, x, src_key_padding_mask=None):
                # x : (batch, seq_len, n_features)

                # Projection + normalisation
                x = self.input_projection(x)      # → (batch, seq_len, d_model)
                x = self.input_norm(x)

                # Encodage positionnel
                x = self.pos_encoding(x)

                # Transformer Encoder (self-attention)
                x = self.transformer_encoder(x)   # → (batch, seq_len, d_model)

                # Global Average Pooling (agréger toute la séquence)
                x = x.mean(dim=1)                 # → (batch, d_model)

                # Classification
                logits = self.classifier(x)       # → (batch, 1)
                return logits.squeeze(-1)          # → (batch,)

        return FinancialTransformer()

    except ImportError:
        return None


# ──────────────────────────────────────────────────────────────────────────────
#  WRAPPER DE HAUT NIVEAU
# ──────────────────────────────────────────────────────────────────────────────

class TransformerModel:
    """
    Modèle Transformer pour la prédiction de direction de marché.

    Usage:
        model = TransformerModel(n_features=50)
        model.train(X_train, y_train)
        proba = model.predict_proba(X_test)
    """

    def __init__(
        self,
        n_features: int = 50,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 256,
        dropout: float = 0.1,
        epochs: int = 40,
        batch_size: int = 32,
        learning_rate: float = 0.0005,
        patience: int = 8,
        models_dir: str = "./data/models",
    ):
        self.n_features      = n_features
        self.d_model         = d_model
        self.nhead           = nhead
        self.num_layers      = num_layers
        self.dim_feedforward = dim_feedforward
        self.dropout         = dropout
        self.epochs          = epochs
        self.batch_size      = batch_size
        self.learning_rate   = learning_rate
        self.patience        = patience
        self.models_dir      = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.network          = None
        self.device           = None
        self.is_trained       = False
        self.training_history: List[Dict] = []

        self._init_torch()

    def _init_torch(self):
        try:
            import torch
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            log.info("Transformer — device: %s | d_model=%d | heads=%d | layers=%d",
                     self.device, self.d_model, self.nhead, self.num_layers)
        except ImportError:
            log.warning("⚠️ PyTorch non installé")

    def _build(self):
        if self.network is None:
            self.network = _build_transformer_network(
                self.n_features, self.d_model, self.nhead,
                self.num_layers, self.dim_feedforward, self.dropout,
            )
            if self.network and self.device:
                self.network = self.network.to(self.device)
                n_params = sum(p.numel() for p in self.network.parameters() if p.requires_grad)
                log.info("Transformer construit — %d paramètres", n_params)

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
        """Entraîne le Transformer avec early stopping."""
        if self.device is None:
            return {"error": "pytorch_not_available"}

        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        if X_train.ndim == 3:
            self.n_features = X_train.shape[2]

        self._build()

        log.info("Entraînement Transformer — samples=%d | seq=%d | features=%d",
                 X_train.shape[0], X_train.shape[1], X_train.shape[2])

        # Validation split automatique si non fourni
        if X_val is None:
            split = int(len(X_train) * 0.85)
            X_val, y_val = X_train[split:], y_train[split:]
            X_train, y_train = X_train[:split], y_train[:split]

        def to_loader(X, y, shuffle=False):
            ds = TensorDataset(
                torch.FloatTensor(X).to(self.device),
                torch.FloatTensor(y).to(self.device),
            )
            return DataLoader(ds, batch_size=self.batch_size, shuffle=shuffle)

        train_loader = to_loader(X_train, y_train, shuffle=False)
        val_loader   = to_loader(X_val, y_val)

        # Utiliser AdamW + Cosine Annealing (populaire pour les Transformers)
        optimizer = torch.optim.AdamW(
            self.network.parameters(),
            lr=self.learning_rate,
            weight_decay=1e-3,
            betas=(0.9, 0.999),
        )
        criterion = nn.BCEWithLogitsLoss()
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=self.epochs, eta_min=1e-6
        )

        best_val_loss  = float("inf")
        best_state     = None
        patience_count = 0
        self.training_history = []

        for epoch in range(1, self.epochs + 1):
            # ── Train ──────────────────────────────────────────────────────
            self.network.train()
            train_losses = []
            for X_batch, y_batch in train_loader:
                optimizer.zero_grad()
                logits = self.network(X_batch)
                loss   = criterion(logits, y_batch)
                loss.backward()
                nn.utils.clip_grad_norm_(self.network.parameters(), 0.5)
                optimizer.step()
                train_losses.append(loss.item())

            # ── Validation ─────────────────────────────────────────────────
            self.network.eval()
            val_losses, preds, labels = [], [], []
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    logits = self.network(X_batch)
                    val_losses.append(criterion(logits, y_batch).item())
                    probs = torch.sigmoid(logits).cpu().numpy()
                    preds.extend(probs)
                    labels.extend(y_batch.cpu().numpy())

            scheduler.step()
            train_loss = np.mean(train_losses)
            val_loss   = np.mean(val_losses)

            from sklearn.metrics import accuracy_score
            val_acc = accuracy_score(labels, (np.array(preds) > 0.5).astype(int))

            self.training_history.append({
                "epoch": epoch, "train_loss": train_loss,
                "val_loss": val_loss, "val_acc": val_acc,
            })

            if epoch % 10 == 0 or epoch == 1:
                log.info("Epoch %3d/%d | train=%.4f | val=%.4f | acc=%.4f",
                         epoch, self.epochs, train_loss, val_loss, val_acc)

            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                best_state = {k: v.clone() for k, v in self.network.state_dict().items()}
                patience_count = 0
            else:
                patience_count += 1
                if patience_count >= self.patience:
                    log.info("Early stopping Transformer à l'epoch %d", epoch)
                    break

        if best_state:
            self.network.load_state_dict(best_state)

        self.is_trained = True
        best = min(self.training_history, key=lambda x: x["val_loss"])
        metrics = {
            "best_epoch":   best["epoch"],
            "best_val_acc": round(best["val_acc"], 4),
            "best_val_loss": round(best["val_loss"], 6),
            "total_epochs": len(self.training_history),
        }
        log.info("✅ Transformer entraîné — best_epoch=%d val_acc=%.4f",
                 metrics["best_epoch"], metrics["best_val_acc"])
        return metrics

    # ──────────────────────────────────────────────────────────────────────────
    #  PRÉDICTION
    # ──────────────────────────────────────────────────────────────────────────

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Retourne les probabilités P(hausse) pour chaque sample."""
        if not self.is_trained:
            raise RuntimeError("Le Transformer n'est pas encore entraîné.")

        import torch

        self.network.eval()
        all_probs = []

        with torch.no_grad():
            X_t = torch.FloatTensor(X).to(self.device)
            for i in range(0, len(X_t), 64):
                logits = self.network(X_t[i : i + 64])
                probs  = torch.sigmoid(logits).cpu().numpy()
                all_probs.extend(probs)

        probs = np.array(all_probs)
        return np.column_stack([1 - probs, probs])

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
            "model":        "transformer",
        }

    def save(self, filename: str = "transformer_model.pt") -> str:
        """Sauvegarde le modèle PyTorch."""
        import torch
        path = self.models_dir / filename
        torch.save({
            "state_dict": self.network.state_dict(),
            "config": {
                "n_features": self.n_features, "d_model": self.d_model,
                "nhead": self.nhead, "num_layers": self.num_layers,
                "dim_feedforward": self.dim_feedforward, "dropout": self.dropout,
            },
            "history": self.training_history,
        }, path)
        log.info("💾 Transformer sauvegardé : %s", path)
        return str(path)

    def load(self, filename: str = "transformer_model.pt") -> bool:
        """Charge le modèle PyTorch."""
        import torch
        path = self.models_dir / filename
        if not path.exists():
            return False
        try:
            ckpt = torch.load(path, map_location=self.device)
            cfg  = ckpt["config"]
            self.n_features = cfg["n_features"]
            self.d_model = cfg["d_model"]
            self.nhead = cfg["nhead"]
            self.num_layers = cfg["num_layers"]
            self.dim_feedforward = cfg["dim_feedforward"]
            self.dropout = cfg["dropout"]
            self._build()
            self.network.load_state_dict(ckpt["state_dict"])
            self.is_trained = True
            log.info("✅ Transformer chargé : %s", path)
            return True
        except Exception as e:
            log.error("Erreur chargement Transformer : %s", str(e))
            return False
