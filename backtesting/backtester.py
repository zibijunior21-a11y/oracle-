"""
================================================================================
  Quantum Trade Oracle — Module de Backtesting
================================================================================
  Évalue rigoureusement les performances de la stratégie sur données historiques.

  Métriques calculées :
  ┌──────────────────────────────────────────────────────────┐
  │ Performance   │ Total Return, CAGR, Sharpe, Sortino      │
  │ Risque        │ Max Drawdown, Volatilité, VaR 95%        │
  │ Trading       │ Win Rate, Profit Factor, Avg W/L         │
  │ Comparaison   │ Alpha, Beta vs Buy & Hold                │
  └──────────────────────────────────────────────────────────┘

  Le backtesting simule :
  • Commission (0.1% par défaut)
  • Slippage (0.05%)
  • Gestion réaliste des positions (pas de trading dans le futur)

  IMPORTANT : Les performances passées ne garantissent pas les performances futures.
================================================================================
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.logger import get_logger

log = get_logger("Backtester")


class Position:
    """Représente une position ouverte."""

    def __init__(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        size: float,
        stop_loss: float,
        take_profit: float,
        entry_date,
    ):
        self.symbol       = symbol
        self.action       = action       # 'BUY' ou 'SELL'
        self.entry_price  = entry_price
        self.size         = size
        self.stop_loss    = stop_loss
        self.take_profit  = take_profit
        self.entry_date   = entry_date
        self.exit_price   = None
        self.exit_date    = None
        self.exit_reason  = None
        self.pnl          = 0.0
        self.pnl_pct      = 0.0

    def close(self, exit_price: float, exit_date, reason: str):
        """Ferme la position et calcule le P&L."""
        self.exit_price  = exit_price
        self.exit_date   = exit_date
        self.exit_reason = reason

        if self.action == "BUY":
            self.pnl = (exit_price - self.entry_price) * self.size
        else:  # SELL (short)
            self.pnl = (self.entry_price - exit_price) * self.size

        self.pnl_pct = self.pnl / (self.entry_price * self.size)

    @property
    def is_open(self) -> bool:
        return self.exit_price is None

    def to_dict(self) -> Dict:
        return {
            "symbol":       self.symbol,
            "action":       self.action,
            "entry_date":   str(self.entry_date),
            "exit_date":    str(self.exit_date),
            "entry_price":  round(self.entry_price, 6),
            "exit_price":   round(self.exit_price, 6) if self.exit_price else None,
            "size":         round(self.size, 6),
            "pnl":          round(self.pnl, 4),
            "pnl_pct":      round(self.pnl_pct * 100, 3),
            "exit_reason":  self.exit_reason,
        }


class Backtester:
    """
    Moteur de backtesting événementiel pour la stratégie QTO.

    Il rejoue les signaux historiques sur les données de marché,
    simule l'exécution des trades et calcule les métriques de performance.

    Usage:
        backtester = Backtester(initial_capital=10_000)
        results = backtester.run(df_with_signals)
        report = backtester.generate_report(results)
    """

    def __init__(
        self,
        initial_capital: float = 10_000.0,
        commission_pct: float = 0.001,    # 0.1%
        slippage_pct: float = 0.0005,     # 0.05%
        max_open_positions: int = 3,
    ):
        self.initial_capital    = initial_capital
        self.commission_pct     = commission_pct
        self.slippage_pct       = slippage_pct
        self.max_open_positions = max_open_positions

    def run(
        self,
        df: pd.DataFrame,
        signals: List[Dict],
        symbol: str = "ASSET",
    ) -> Dict:
        """
        Exécute le backtesting sur une série de données et de signaux.

        Args:
            df:      DataFrame OHLCV avec indicateurs (index DatetimeIndex)
            signals: Liste de signaux générés par StrategyEngine
            symbol:  Nom du symbole

        Returns:
            Dict complet avec equity_curve, trades, métriques
        """
        capital    = self.initial_capital
        equity     = [capital]
        equity_dates = [df.index[0]]
        positions: List[Position] = []
        closed_trades: List[Position] = []

        # Indexer les signaux par date pour un accès rapide
        signal_by_date = {}
        for sig in signals:
            try:
                ts = pd.Timestamp(sig["timestamp"]).normalize()
                signal_by_date[ts] = sig
            except Exception:
                continue

        log.info("Démarrage du backtest — %d jours | %d signaux | capital: $%.0f",
                 len(df), len(signals), capital)

        for date, row in df.iterrows():
            date_norm = pd.Timestamp(date).normalize()
            price     = float(row.get("close", 0))
            if price <= 0:
                continue

            # ── 1. Vérifier les stop-loss et take-profit ──────────────────
            for pos in list(positions):
                if not pos.is_open:
                    continue

                should_close = False
                reason = ""

                if pos.action == "BUY":
                    if price <= pos.stop_loss:
                        should_close, reason = True, "STOP_LOSS"
                    elif price >= pos.take_profit:
                        should_close, reason = True, "TAKE_PROFIT"
                elif pos.action == "SELL":
                    if price >= pos.stop_loss:
                        should_close, reason = True, "STOP_LOSS"
                    elif price <= pos.take_profit:
                        should_close, reason = True, "TAKE_PROFIT"

                if should_close:
                    exit_price = price * (1 - self.slippage_pct if pos.action == "BUY"
                                         else 1 + self.slippage_pct)
                    commission = exit_price * pos.size * self.commission_pct
                    pos.close(exit_price, date, reason)
                    capital += pos.pnl - commission
                    positions.remove(pos)
                    closed_trades.append(pos)
                    log.debug("Position fermée [%s] %s @ %.4f | P&L: %+.2f$ (%s)",
                              symbol, pos.action, exit_price, pos.pnl, reason)

            # ── 2. Traiter le signal du jour ──────────────────────────────
            if date_norm in signal_by_date:
                sig = signal_by_date[date_norm]
                action = sig.get("action", "HOLD")
                risk   = sig.get("risk_management", {})

                if action in ("BUY", "SELL") and len(positions) < self.max_open_positions:
                    # Prix d'exécution avec slippage
                    entry_price = price * (1 + self.slippage_pct if action == "BUY"
                                           else 1 - self.slippage_pct)

                    # Taille de position
                    position_value = min(
                        capital * 0.05,                        # Max 5% du capital
                        risk.get("position_value", capital * 0.02),
                    )
                    size = position_value / entry_price if entry_price > 0 else 0

                    if size > 0 and capital >= position_value:
                        commission = entry_price * size * self.commission_pct
                        capital -= commission  # Déduire la commission d'entrée

                        sl = risk.get("stop_loss", entry_price * 0.97)
                        tp = risk.get("take_profit", entry_price * 1.06)

                        pos = Position(symbol, action, entry_price, size, sl, tp, date)
                        positions.append(pos)
                        log.debug("Position ouverte [%s] %s @ %.4f | size: %.4f | SL: %.4f | TP: %.4f",
                                  symbol, action, entry_price, size, sl, tp)

                elif action == "HOLD":
                    # Fermer toutes les positions BUY sur signal SELL (et vice versa)
                    for pos in list(positions):
                        if pos.is_open:
                            exit_price = price * (1 - self.slippage_pct)
                            commission = exit_price * pos.size * self.commission_pct
                            pos.close(exit_price, date, "SIGNAL_REVERSAL")
                            capital += pos.pnl - commission
                            positions.remove(pos)
                            closed_trades.append(pos)

            # ── 3. Calculer la valeur du portefeuille (mark-to-market) ─────
            open_pnl = sum(
                (price - pos.entry_price) * pos.size if pos.action == "BUY"
                else (pos.entry_price - price) * pos.size
                for pos in positions if pos.is_open
            )
            total_equity = capital + open_pnl
            equity.append(total_equity)
            equity_dates.append(date)

        # Fermer les positions restantes
        for pos in positions:
            if pos.is_open:
                final_price = float(df["close"].iloc[-1])
                pos.close(final_price, df.index[-1], "END_OF_BACKTEST")
                closed_trades.append(pos)

        # ── Construire l'equity curve ──────────────────────────────────────
        equity_series = pd.Series(equity, index=equity_dates, name="equity")
        equity_series = equity_series[~equity_series.index.duplicated(keep="last")]

        # ── Calculer les métriques ─────────────────────────────────────────
        metrics = self._calculate_metrics(
            equity_series, closed_trades, df["close"]
        )

        log.info("Backtest terminé — %d trades | Return: %+.2f%% | Sharpe: %.2f | MaxDD: %.2f%%",
                 len(closed_trades),
                 metrics.get("total_return_pct", 0),
                 metrics.get("sharpe_ratio", 0),
                 metrics.get("max_drawdown_pct", 0))

        return {
            "equity_curve":    equity_series,
            "closed_trades":   [t.to_dict() for t in closed_trades],
            "metrics":         metrics,
            "symbol":          symbol,
            "initial_capital": self.initial_capital,
            "final_capital":   equity[-1],
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  CALCUL DES MÉTRIQUES
    # ──────────────────────────────────────────────────────────────────────────

    def _calculate_metrics(
        self,
        equity: pd.Series,
        trades: List[Position],
        price_series: pd.Series,
    ) -> Dict:
        """Calcule toutes les métriques de performance."""
        # ── Rendements ────────────────────────────────────────────────────
        returns = equity.pct_change().dropna()

        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1

        # CAGR
        n_years = (equity.index[-1] - equity.index[0]).days / 365.25
        cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / max(n_years, 0.1)) - 1

        # ── Risque ────────────────────────────────────────────────────────
        ann_vol = float(returns.std() * np.sqrt(252))

        # Max Drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_drawdown = float(drawdown.min())

        # Sharpe Ratio (risk-free rate = 4% annualisé)
        risk_free = 0.04 / 252
        excess_returns = returns - risk_free
        sharpe = float(excess_returns.mean() / excess_returns.std() * np.sqrt(252)) \
                 if excess_returns.std() > 0 else 0

        # Sortino Ratio (pénalise seulement la volatilité négative)
        negative_returns = returns[returns < 0]
        downside_vol = float(negative_returns.std() * np.sqrt(252)) if len(negative_returns) > 0 else 0.001
        sortino = float(excess_returns.mean() * np.sqrt(252) / downside_vol)

        # VaR 95% (Value at Risk)
        var_95 = float(np.percentile(returns, 5)) if len(returns) > 0 else 0

        # ── Trades ────────────────────────────────────────────────────────
        n_trades    = len(trades)
        if n_trades > 0:
            pnls        = [t.pnl for t in trades]
            wins        = [t for t in trades if t.pnl > 0]
            losses      = [t for t in trades if t.pnl <= 0]

            win_rate    = len(wins) / n_trades
            avg_win     = float(np.mean([t.pnl for t in wins])) if wins else 0
            avg_loss    = float(np.mean([t.pnl for t in losses])) if losses else 0
            profit_factor = abs(sum(t.pnl for t in wins) / sum(t.pnl for t in losses)) \
                            if losses and sum(t.pnl for t in losses) != 0 else float("inf")
            expectancy  = win_rate * avg_win + (1 - win_rate) * avg_loss

            # Durée moyenne d'un trade
            durations = []
            for t in trades:
                if t.entry_date and t.exit_date:
                    try:
                        d = (pd.Timestamp(t.exit_date) - pd.Timestamp(t.entry_date)).days
                        durations.append(d)
                    except Exception:
                        pass
            avg_duration = float(np.mean(durations)) if durations else 0
        else:
            win_rate = avg_win = avg_loss = profit_factor = expectancy = avg_duration = 0

        # ── Buy & Hold (benchmark) ─────────────────────────────────────────
        bh_return = (price_series.iloc[-1] / price_series.iloc[0]) - 1
        alpha     = float(total_return) - float(bh_return)

        return {
            # Performance
            "total_return_pct":  round(total_return * 100, 3),
            "cagr_pct":          round(cagr * 100, 3),
            "final_capital":     round(equity.iloc[-1], 2),

            # Risque
            "max_drawdown_pct":  round(max_drawdown * 100, 3),
            "ann_volatility_pct": round(ann_vol * 100, 3),
            "var_95_pct":        round(var_95 * 100, 3),

            # Ratios
            "sharpe_ratio":      round(sharpe, 4),
            "sortino_ratio":     round(sortino, 4),

            # Trading
            "n_trades":          n_trades,
            "win_rate_pct":      round(win_rate * 100, 2),
            "avg_win_usd":       round(avg_win, 2),
            "avg_loss_usd":      round(avg_loss, 2),
            "profit_factor":     round(profit_factor, 3),
            "expectancy_usd":    round(expectancy, 2),
            "avg_trade_days":    round(avg_duration, 1),

            # Comparaison
            "buy_hold_return_pct": round(float(bh_return) * 100, 3),
            "alpha_pct":           round(alpha * 100, 3),
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  RAPPORT FORMATÉ
    # ──────────────────────────────────────────────────────────────────────────

    def generate_report(self, results: Dict) -> str:
        """Génère un rapport textuel complet du backtesting."""
        m = results["metrics"]
        sep = "═" * 60

        report = f"""
{sep}
  QUANTUM TRADE ORACLE — RAPPORT DE BACKTESTING
  Symbole : {results['symbol']}
{sep}

  CAPITAL
  ─────────────────────────────────────────────────
  Capital initial     : ${results['initial_capital']:>12,.2f}
  Capital final       : ${m['final_capital']:>12,.2f}
  Rendement total     : {m['total_return_pct']:>+11.2f} %
  CAGR                : {m['cagr_pct']:>+11.2f} %
  Alpha vs Buy&Hold   : {m['alpha_pct']:>+11.2f} %

  RISQUE
  ─────────────────────────────────────────────────
  Max Drawdown        : {m['max_drawdown_pct']:>11.2f} %
  Volatilité annuelle : {m['ann_volatility_pct']:>11.2f} %
  VaR 95%             : {m['var_95_pct']:>11.2f} %

  RATIOS DE QUALITÉ
  ─────────────────────────────────────────────────
  Ratio de Sharpe     : {m['sharpe_ratio']:>11.4f}
  Ratio de Sortino    : {m['sortino_ratio']:>11.4f}

  STATISTIQUES DES TRADES
  ─────────────────────────────────────────────────
  Nombre de trades    : {m['n_trades']:>11d}
  Taux de réussite    : {m['win_rate_pct']:>11.1f} %
  Gain moyen          : ${m['avg_win_usd']:>11.2f}
  Perte moyenne       : ${m['avg_loss_usd']:>11.2f}
  Profit Factor       : {m['profit_factor']:>11.3f}
  Espérance           : ${m['expectancy_usd']:>11.2f}
  Durée moy. (jours)  : {m['avg_trade_days']:>11.1f}

  COMPARAISON BENCHMARK
  ─────────────────────────────────────────────────
  Stratégie QTO       : {m['total_return_pct']:>+11.2f} %
  Buy & Hold          : {m['buy_hold_return_pct']:>+11.2f} %
  Surperformance      : {m['alpha_pct']:>+11.2f} %

{sep}
  ⚠️  Les performances passées ne garantissent pas les résultats futurs.
{sep}
"""
        return report

    def compare_strategies(
        self,
        results_list: List[Tuple[str, Dict]],
    ) -> pd.DataFrame:
        """
        Compare plusieurs stratégies côte à côte.

        Args:
            results_list: Liste de tuples (nom, résultats_backtest)

        Returns:
            DataFrame de comparaison
        """
        rows = []
        for name, results in results_list:
            m = results.get("metrics", {})
            rows.append({
                "Stratégie":      name,
                "Rendement %":    m.get("total_return_pct", 0),
                "CAGR %":         m.get("cagr_pct", 0),
                "Max DD %":       m.get("max_drawdown_pct", 0),
                "Sharpe":         m.get("sharpe_ratio", 0),
                "Sortino":        m.get("sortino_ratio", 0),
                "Win Rate %":     m.get("win_rate_pct", 0),
                "Profit Factor":  m.get("profit_factor", 0),
                "N Trades":       m.get("n_trades", 0),
            })

        df = pd.DataFrame(rows).set_index("Stratégie")
        df = df.round(3)
        log.info("Comparaison de %d stratégies générée", len(rows))
        return df
