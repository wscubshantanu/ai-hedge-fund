"""
AETHER Capital — Unit Tests: Quant Risk Engine
Tests for CVaR, regime-aware sizing, VaR edge cases, and position limit logic.
Matches the actual API of src/quant/risk_metrics.py.
"""
import pytest
import numpy as np
from src.quant.risk_metrics import (
    evaluate_portfolio_risk,
    calculate_parametric_var,
    calculate_historical_cvar,
    regime_position_multiplier,
)


# ── CVaR Historical Simulation ──────────────────────────────────────────────

class TestCVaRHistorical:
    def test_cvar_positive(self):
        """CVaR (Expected Shortfall) must always be a positive loss percentage."""
        rng = np.random.default_rng(42)
        returns = rng.normal(0.001, 0.02, 252)
        cvar = calculate_historical_cvar(returns, confidence_level=0.95)
        assert cvar >= 0, "CVaR should be positive (loss expressed as positive %)"

    def test_cvar_increases_with_volatility(self):
        """Higher volatility returns should produce higher CVaR."""
        rng = np.random.default_rng(0)
        low_vol  = rng.normal(0, 0.005, 252)
        high_vol = rng.normal(0, 0.04,  252)
        cvar_low  = calculate_historical_cvar(low_vol,  confidence_level=0.95)
        cvar_high = calculate_historical_cvar(high_vol, confidence_level=0.95)
        assert cvar_high > cvar_low

    def test_cvar_99_gte_95(self):
        """CVaR at 99% confidence should be >= CVaR at 95%."""
        rng = np.random.default_rng(7)
        returns = rng.normal(0, 0.02, 500)
        cvar_95 = calculate_historical_cvar(returns, confidence_level=0.95)
        cvar_99 = calculate_historical_cvar(returns, confidence_level=0.99)
        assert cvar_99 >= cvar_95

    def test_fallback_with_no_history(self):
        """Should return a parametric estimate when returns=None."""
        result = calculate_historical_cvar(None, confidence_level=0.95, volatility_annual=0.25)
        assert isinstance(result, float)
        assert result > 0

    def test_fallback_with_too_few_history(self):
        """Should fall back to parametric when fewer than 60 returns provided."""
        sparse = np.array([0.01, -0.02, 0.005])
        result = calculate_historical_cvar(sparse, confidence_level=0.95, volatility_annual=0.25)
        assert isinstance(result, float)
        assert result > 0


# ── Regime Position Multiplier ───────────────────────────────────────────────

class TestRegimePositionMultiplier:
    def test_low_vol_bull_allows_full_sizing(self):
        mult = regime_position_multiplier("LOW_VOL_BULL")
        assert mult >= 0.9, "Low-vol bull should allow near-full position size"

    def test_high_vol_bull_reduces_sizing(self):
        mult = regime_position_multiplier("HIGH_VOL_BULL")
        assert mult <= 0.75, "High-vol bull must reduce position size"

    def test_bear_panic_near_zero(self):
        mult = regime_position_multiplier("BEAR_PANIC")
        assert mult <= 0.20, "Bear panic must force near-zero exposure"

    def test_unknown_regime_defaults_safe(self):
        mult = regime_position_multiplier("SOME_FUTURE_REGIME")
        assert 0.0 < mult <= 1.0, "Unknown regimes must produce a valid multiplier"

    def test_multiplier_bounded_all_known(self):
        for regime in ["LOW_VOL_BULL", "HIGH_VOL_BULL", "RANGEBOUND_CHOP", "BEAR_PANIC"]:
            mult = regime_position_multiplier(regime)
            assert 0.0 <= mult <= 1.0, f"Multiplier out of bounds for {regime}: {mult}"


# ── Parametric VaR ───────────────────────────────────────────────────────────

class TestParametricVaR:
    def test_zero_volatility_zero_var(self):
        """Zero vol position should yield near-zero VaR."""
        var = calculate_parametric_var(0.0, confidence_level=0.95)
        assert var == pytest.approx(0.0, abs=0.01)

    def test_var_scales_with_vol(self):
        """Doubling annualized vol should approximately double VaR."""
        var_25 = calculate_parametric_var(0.25, confidence_level=0.95)
        var_50 = calculate_parametric_var(0.50, confidence_level=0.95)
        ratio = var_50 / var_25
        assert 1.8 <= ratio <= 2.2, f"VaR scaling ratio {ratio:.2f} should be ~2.0"

    def test_higher_confidence_higher_var(self):
        """99% VaR should exceed 95% VaR."""
        var_95 = calculate_parametric_var(0.25, confidence_level=0.95)
        var_99 = calculate_parametric_var(0.25, confidence_level=0.99)
        assert var_99 > var_95

    def test_25pct_vol_95_confidence_approx(self):
        """25% annual vol should yield ~2.6% 1-day 95% VaR."""
        var = calculate_parametric_var(0.25, confidence_level=0.95)
        assert 2.0 <= var <= 3.5


# ── Full Risk Evaluation ─────────────────────────────────────────────────────

class TestEvaluatePortfolioRisk:
    def test_veto_at_extreme_vol(self):
        risk = evaluate_portfolio_risk("XXX", annual_volatility=0.90, current_price=50.0)
        assert risk["is_vetoed"] is True
        assert risk["max_position_size_pct"] == 0.0

    def test_no_veto_at_normal_vol(self):
        risk = evaluate_portfolio_risk("AAPL", annual_volatility=0.25, current_price=180.0)
        assert risk["is_vetoed"] is False
        assert risk["max_position_size_pct"] > 0.0

    def test_stop_loss_below_entry(self):
        risk = evaluate_portfolio_risk("MSFT", annual_volatility=0.22, current_price=400.0)
        if not risk["is_vetoed"]:
            assert risk["suggested_stop_loss"] < 400.0

    def test_risk_rating_labels(self):
        low_risk  = evaluate_portfolio_risk("T",  annual_volatility=0.10, current_price=20.0)
        high_risk = evaluate_portfolio_risk("T2", annual_volatility=0.80, current_price=20.0)
        valid_ratings = {"LOW", "MODERATE", "HIGH", "EXTREME"}
        assert low_risk["risk_rating"]  in valid_ratings
        assert high_risk["risk_rating"] in valid_ratings

    def test_regime_aware_sizing_reduces_in_bear(self):
        """Position in BEAR_PANIC should be <= LOW_VOL_BULL."""
        bull = evaluate_portfolio_risk("NVDA", annual_volatility=0.30, current_price=150.0,
                                       market_regime="LOW_VOL_BULL")
        bear = evaluate_portfolio_risk("NVDA", annual_volatility=0.30, current_price=150.0,
                                       market_regime="BEAR_PANIC")
        if not bull["is_vetoed"] and not bear["is_vetoed"]:
            assert bear["max_position_size_pct"] <= bull["max_position_size_pct"]

    def test_output_schema_completeness(self):
        """Risk output must have all fields the API serializes."""
        risk = evaluate_portfolio_risk("GOOGL", annual_volatility=0.28, current_price=170.0)
        required_fields = [
            "ticker", "is_vetoed", "max_position_size_pct",
            "var_95", "var_99", "cvar_95", "risk_rating",
            "suggested_stop_loss", "suggested_take_profit"
        ]
        for field in required_fields:
            assert field in risk, f"Missing required field: {field}"

    def test_position_size_capped_at_30pct(self):
        """No single position should exceed 30% allocation."""
        risk = evaluate_portfolio_risk("BOND", annual_volatility=0.02, current_price=100.0)
        assert risk["max_position_size_pct"] <= 0.30
