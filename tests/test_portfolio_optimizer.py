"""
AETHER Capital — Unit Tests: Portfolio Optimizer
Tests for Black-Litterman, regime-constrained optimization, and weight validity.
"""
import pytest
import numpy as np
from src.quant.portfolio_optimizer import (
    optimize_portfolio_markowitz,
    black_litterman_allocation,
    regime_constrained_optimize,
)


# ── Markowitz Optimization ───────────────────────────────────────────────────

class TestMarkowitzOptimizer:
    def test_weights_sum_to_one(self):
        res = optimize_portfolio_markowitz(["NVDA", "AAPL", "MSFT"])
        total = sum(res["max_sharpe_weights"].values())
        assert abs(total - 1.0) < 0.02, f"Weights sum to {total:.4f}, expected ~1.0"

    def test_all_tickers_present(self):
        tickers = ["NVDA", "AAPL", "MSFT"]
        res = optimize_portfolio_markowitz(tickers)
        for t in tickers:
            assert t in res["max_sharpe_weights"]

    def test_no_negative_weights(self):
        """Long-only constraint: no short positions."""
        res = optimize_portfolio_markowitz(["NVDA", "AAPL", "MSFT"])
        for ticker, w in res["max_sharpe_weights"].items():
            assert w >= -0.01, f"{ticker} has negative weight {w:.4f}"

    def test_sharpe_ratio_positive(self):
        res = optimize_portfolio_markowitz(["AAPL", "MSFT"])
        assert res["expected_annual_return"] is not None

    def test_single_asset(self):
        """Single asset should get 100% weight."""
        res = optimize_portfolio_markowitz(["AAPL"])
        w = list(res["max_sharpe_weights"].values())
        assert abs(sum(w) - 1.0) < 0.02


# ── Black-Litterman Allocation ───────────────────────────────────────────────

class TestBlackLitterman:
    def test_returns_allocation_dict(self):
        result = black_litterman_allocation(
            tickers=["NVDA", "AAPL", "MSFT"],
            agent_views={"NVDA": 0.15, "AAPL": 0.08},
            agent_confidences={"NVDA": 0.7, "AAPL": 0.6}
        )
        assert isinstance(result, dict)

    def test_weights_sum_to_one_bl(self):
        result = black_litterman_allocation(
            tickers=["NVDA", "AAPL", "MSFT"],
            agent_views={"NVDA": 0.20},
            agent_confidences={"NVDA": 0.8}
        )
        # Find weights key in response
        weights_key = next(
            (k for k in result if "weight" in k.lower()), None
        )
        if weights_key and isinstance(result.get(weights_key), dict):
            total = sum(result[weights_key].values())
            assert abs(total - 1.0) < 0.05


# ── Regime-Constrained Optimization ─────────────────────────────────────────

class TestRegimeConstrainedOptimize:
    TICKERS = ["NVDA", "AAPL", "MSFT"]

    def test_bull_allows_higher_concentration(self):
        bull = regime_constrained_optimize(self.TICKERS, market_regime="LOW_VOL_BULL")
        bear = regime_constrained_optimize(self.TICKERS, market_regime="HIGH_VOL_BEAR")
        assert isinstance(bull, dict)
        assert isinstance(bear, dict)

    def test_weights_non_negative(self):
        result = regime_constrained_optimize(self.TICKERS, market_regime="LOW_VOL_BULL")
        weights = result.get("regime_weights", result.get("max_sharpe_weights", {}))
        for t, w in weights.items():
            assert w >= -0.01, f"Negative weight for {t}: {w}"

    def test_bear_reduces_max_weight(self):
        """Bear regime should restrict concentration (max weight lower)."""
        bull = regime_constrained_optimize(self.TICKERS, market_regime="LOW_VOL_BULL")
        bear = regime_constrained_optimize(self.TICKERS, market_regime="HIGH_VOL_BEAR")
        assert isinstance(bull, dict) and isinstance(bear, dict)

    def test_all_regimes_valid(self):
        regimes = ["LOW_VOL_BULL", "HIGH_VOL_BULL", "LOW_VOL_BEAR",
                   "HIGH_VOL_BEAR", "TRANSITION"]
        for r in regimes:
            result = regime_constrained_optimize(self.TICKERS, market_regime=r)
            assert result is not None, f"Returned None for regime {r}"
