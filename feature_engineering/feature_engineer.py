"""
================================================================================
  Quantum Trade Oracle — Feature Engineering
================================================================================
  Transforme les données OHLCV brutes en features prêtes pour les modèles ML.

  Indicateurs calculés :
  ┌─────────────────────────────────────────────────────┐
  │ Tendance     │ MA(7/14/21/50/200), EMA, MACD        │
  │ Momentum     │ RSI, ROC, Williams %R, Stochastic    │
  │ Volatilité   │ Bollinger Bands, ATR, Keltner Channel│
  │ Volume       │ OBV, Volume SMA, Volume Ratio        │
  │ Prix         │ Returns (1/3/5/10/20j), Log-returns  │
  │ Structure    │ Higher-Highs, Lower-Lows, Gaps       │
  └─────────────────────────────────────────────────────┘

  Sorties :
  • X : DataFrame de features normalisées
  • y : Série de labels binaires (1 = hausse, 0 = baisse)
  • X_seq : Array 3D pour LSTM/Transformer (samples, steps, features)
================================================================================
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

from utils.logger import get_logger

log = get_logger("FeatureEngineering")


class FeatureEngineer:
    """
    Pipeline de feature engineering pour séries temporelles financières.

    Usage:
        fe = FeatureEngineer()
        df_feat = fe.build_features(df_ohlcv)
        X_train, X_test, y_train, y_test = fe.train_test_split(df_feat)
        X_seq, y_seq = fe.to_sequences(df_feat, sequence_length=60)
    """

    def __init__(
        self,
        prediction_horizon: int = 1,
        threshold_pct: float = 0.005,
        sequence_length: int = 60,
    ):
        """
        Args:
            prediction_horizon: Nombre de périodes en avance à prédire
            threshold_pct:      Seuil de retour pour définir hausse/baisse
            sequence_length:    Longueur des séquences pour LSTM/Transformer
        """
        self.prediction_horizon = prediction_horizon
        self.threshold_pct = threshold_pct
        self.sequence_length = sequence_length
        self.scaler = RobustScaler()
        self.feature_names: List[str] = []
        self._fitted = False

    # ──────────────────────────────────────────────────────────────────────────
    #  PIPELINE PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────────

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule tous les indicateurs techniques et features dérivées.

        Args:
            df: DataFrame OHLCV avec colonnes open/high/low/close/volume

        Returns:
            DataFrame enrichi avec tous les indicateurs + target
        """
        df = df.copy()

        # S'assurer que les colonnes sont en minuscules
        df.columns = [c.lower() for c in df.columns]

        # Vérification des colonnes requises
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Colonnes manquantes : {missing}")

        log.info("Calcul des indicateurs pour %d lignes…", len(df))

        # ── Indicateurs de tendance ───────────────────────────────────────
        df = self._add_moving_averages(df)
        df = self._add_macd(df)

        # ── Indicateurs de momentum ───────────────────────────────────────
        df = self._add_rsi(df)
        df = self._add_stochastic(df)
        df = self._add_roc(df)

        # ── Indicateurs de volatilité ─────────────────────────────────────
        df = self._add_bollinger_bands(df)
        df = self._add_atr(df)

        # ── Indicateurs de volume ─────────────────────────────────────────
        df = self._add_volume_indicators(df)

        # ── Features de prix ──────────────────────────────────────────────
        df = self._add_price_features(df)

        # ── Target (variable cible) ───────────────────────────────────────
        df = self._add_target(df)

        # Supprimer les NaN (causés par les fenêtres glissantes)
        n_before = len(df)
        df.dropna(inplace=True)
        log.info("Features calculées : %d colonnes, %d lignes (%d supprimées pour NaN)",
                 len(df.columns), len(df), n_before - len(df))

        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  INDICATEURS DE TENDANCE
    # ──────────────────────────────────────────────────────────────────────────

    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Moyennes mobiles simples et exponentielles."""
        windows = [7, 14, 21, 50, 200]
        for w in windows:
            df[f"sma_{w}"]  = df["close"].rolling(w).mean()
            df[f"ema_{w}"]  = df["close"].ewm(span=w, adjust=False).mean()
            # Ratio prix / MA (position relative)
            df[f"close_sma{w}_ratio"] = df["close"] / df[f"sma_{w}"] - 1

        # Croisements EMA : golden cross / death cross
        df["ema_cross_7_21"]   = (df["ema_7"] > df["ema_21"]).astype(int)
        df["ema_cross_50_200"] = (df["ema_50"] > df["ema_200"]).astype(int)

        return df

    def _add_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:
        """MACD (Moving Average Convergence Divergence)."""
        ema_fast   = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow   = df["close"].ewm(span=slow, adjust=False).mean()
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
        df["macd_hist"]   = df["macd"] - df["macd_signal"]
        # Signe de l'histogramme (direction du MACD)
        df["macd_positive"] = (df["macd_hist"] > 0).astype(int)
        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  INDICATEURS DE MOMENTUM
    # ──────────────────────────────────────────────────────────────────────────

    def _add_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """RSI (Relative Strength Index) via méthode Wilder."""
        delta = df["close"].diff()
        gain  = delta.clip(lower=0)
        loss  = (-delta).clip(lower=0)

        avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))

        # Zones de surachat / survente
        df["rsi_overbought"] = (df["rsi"] > 70).astype(int)
        df["rsi_oversold"]   = (df["rsi"] < 30).astype(int)

        return df

    def _add_stochastic(
        self,
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
    ) -> pd.DataFrame:
        """Oscillateur Stochastique %K et %D."""
        low_min  = df["low"].rolling(k_period).min()
        high_max = df["high"].rolling(k_period).max()

        df["stoch_k"] = 100 * (df["close"] - low_min) / (high_max - low_min + 1e-10)
        df["stoch_d"] = df["stoch_k"].rolling(d_period).mean()
        df["stoch_cross"] = (df["stoch_k"] > df["stoch_d"]).astype(int)

        return df

    def _add_roc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rate of Change sur différentes fenêtres."""
        for w in [3, 5, 10, 20]:
            df[f"roc_{w}"] = df["close"].pct_change(w) * 100
        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  INDICATEURS DE VOLATILITÉ
    # ──────────────────────────────────────────────────────────────────────────

    def _add_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> pd.DataFrame:
        """Bandes de Bollinger et position relative du prix."""
        sma  = df["close"].rolling(period).mean()
        std  = df["close"].rolling(period).std()

        df["bb_upper"]  = sma + std_dev * std
        df["bb_middle"] = sma
        df["bb_lower"]  = sma - std_dev * std
        df["bb_width"]  = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]

        # Position du prix dans la bande [0, 1]
        band_range = df["bb_upper"] - df["bb_lower"]
        df["bb_pct_b"] = (df["close"] - df["bb_lower"]) / band_range.replace(0, np.nan)

        # Squeeze : bandes très étroites = explosion potentielle
        df["bb_squeeze"] = (df["bb_width"] < df["bb_width"].rolling(50).mean() * 0.5).astype(int)

        return df

    def _add_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """ATR (Average True Range) — mesure de volatilité."""
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift()).abs(),
            (df["low"] - df["close"].shift()).abs(),
        ], axis=1).max(axis=1)

        df["atr"] = tr.ewm(com=period - 1, adjust=False).mean()
        # ATR normalisé par le prix
        df["atr_pct"] = df["atr"] / df["close"] * 100

        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  INDICATEURS DE VOLUME
    # ──────────────────────────────────────────────────────────────────────────

    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """OBV, Volume Ratio, VWAP approximé."""
        # OBV (On-Balance Volume)
        direction  = np.sign(df["close"].diff())
        df["obv"]  = (df["volume"] * direction).cumsum()
        df["obv_ema"] = df["obv"].ewm(span=20, adjust=False).mean()

        # Volume par rapport à sa moyenne
        vol_sma = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / vol_sma.replace(0, np.nan)

        # Anomalie de volume (spike)
        df["volume_spike"] = (df["volume_ratio"] > 2.0).astype(int)

        # VWAP journalier approximé (fenêtre glissante 14 jours)
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        df["vwap_14"] = (typical_price * df["volume"]).rolling(14).sum() / df["volume"].rolling(14).sum()
        df["price_above_vwap"] = (df["close"] > df["vwap_14"]).astype(int)

        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  FEATURES DE PRIX
    # ──────────────────────────────────────────────────────────────────────────

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Returns, log-returns, ratios OHLC."""
        # Rendements sur différentes fenêtres
        for w in [1, 3, 5, 10, 20]:
            df[f"return_{w}d"] = df["close"].pct_change(w)

        # Log-returns (distribution plus normale)
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))

        # Ratios OHLC
        df["hl_ratio"]   = (df["high"] - df["low"]) / df["close"]
        df["co_ratio"]   = (df["close"] - df["open"]) / df["open"]
        df["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]
        df["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]

        # Momentum directionnel : jours consécutifs en hausse
        daily_dir = (df["close"] > df["close"].shift(1)).astype(int)
        df["up_streak"] = daily_dir.groupby((daily_dir != daily_dir.shift()).cumsum()).cumsum()

        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  TARGET (VARIABLE CIBLE)
    # ──────────────────────────────────────────────────────────────────────────

    def _add_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée la variable cible pour la classification.

        Règle :
        • target = 1  si return(t → t+horizon) > threshold
        • target = 0  sinon (baisse ou mouvement trop faible)

        Args:
            df: DataFrame avec colonne 'close'

        Returns:
            DataFrame avec colonnes 'future_return' et 'target'
        """
        future_price = df["close"].shift(-self.prediction_horizon)
        df["future_return"] = (future_price - df["close"]) / df["close"]
        df["target"] = (df["future_return"] > self.threshold_pct).astype(int)

        # Supprimer les dernières lignes sans futur
        df = df.iloc[:-self.prediction_horizon]

        pos_rate = df["target"].mean()
        log.info("Target créé : %.1f%% haussier | %.1f%% baissier",
                 pos_rate * 100, (1 - pos_rate) * 100)

        return df

    # ──────────────────────────────────────────────────────────────────────────
    #  SPLIT ET NORMALISATION
    # ──────────────────────────────────────────────────────────────────────────

    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Retourne la liste des colonnes de features (exclut target et OHLCV raw)."""
        exclude = {"open", "high", "low", "close", "volume", "symbol",
                   "target", "future_return", "adj_close"}
        cols = [c for c in df.columns if c not in exclude and df[c].dtype in [float, int, np.float64, np.int64]]
        self.feature_names = cols
        return cols

    def train_test_split(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.80,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split temporel (pas random !) en train et test sets.

        Un split aléatoire causerait du "data leakage" sur une série temporelle.

        Returns:
            X_train, X_test, y_train, y_test
        """
        feature_cols = self.get_feature_columns(df)
        split_idx = int(len(df) * train_ratio)

        X = df[feature_cols]
        y = df["target"]

        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Normalisation (fit sur train, transform sur test)
        X_train_sc = pd.DataFrame(
            self.scaler.fit_transform(X_train),
            columns=feature_cols,
            index=X_train.index,
        )
        X_test_sc = pd.DataFrame(
            self.scaler.transform(X_test),
            columns=feature_cols,
            index=X_test.index,
        )
        self._fitted = True

        log.info("Split : train=%d | test=%d | features=%d",
                 len(X_train), len(X_test), len(feature_cols))

        return X_train_sc, X_test_sc, y_train, y_test

    def to_sequences(
        self,
        df: pd.DataFrame,
        sequence_length: Optional[int] = None,
        train_ratio: float = 0.80,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Transforme le DataFrame en séquences 3D pour LSTM/Transformer.

        Shape des séquences :
        X : (samples, sequence_length, n_features)
        y : (samples,)

        Args:
            df:              DataFrame avec features et target
            sequence_length: Longueur des fenêtres temporelles
            train_ratio:     Ratio train/test

        Returns:
            X_train_seq, X_test_seq, y_train_seq, y_test_seq
        """
        seq_len = sequence_length or self.sequence_length
        feature_cols = self.get_feature_columns(df)

        # Normaliser
        X_raw = self.scaler.fit_transform(df[feature_cols])
        self._fitted = True
        y_raw = df["target"].values

        # Créer les séquences glissantes
        X_seq, y_seq = [], []
        for i in range(seq_len, len(X_raw)):
            X_seq.append(X_raw[i - seq_len : i])
            y_seq.append(y_raw[i])

        X_seq = np.array(X_seq, dtype=np.float32)
        y_seq = np.array(y_seq, dtype=np.float32)

        # Split temporel
        split = int(len(X_seq) * train_ratio)
        X_train = X_seq[:split]
        X_test  = X_seq[split:]
        y_train = y_seq[:split]
        y_test  = y_seq[split:]

        log.info("Séquences : seq_len=%d | X_train=%s | X_test=%s | features=%d",
                 seq_len, X_train.shape, X_test.shape, len(feature_cols))

        return X_train, X_test, y_train, y_test

    def transform_latest(self, df: pd.DataFrame, n_recent: int = None) -> np.ndarray:
        """
        Transforme les N dernières lignes pour l'inférence temps réel.

        Args:
            df:       DataFrame de features (complet)
            n_recent: Nombre de lignes récentes à utiliser

        Returns:
            Array normalisé prêt pour la prédiction
        """
        if not self._fitted:
            raise RuntimeError("Le scaler n'est pas encore entraîné. Appeler train_test_split d'abord.")

        feature_cols = self.feature_names or self.get_feature_columns(df)
        data = df[feature_cols]

        if n_recent:
            data = data.tail(n_recent)

        return self.scaler.transform(data)
