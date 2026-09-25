import pytest
from src.quant.technical_indicators import get_market_technicals, compute_technical_indicators
from src.quant.risk_metrics import evaluate_portfolio_risk, calculate_parametric_var
from src.quant.valuation_models import calculate_dcf_valuation, calculate_graham_number, get_fundamental_metrics
from src.quant.portfolio_optimizer import optimize_portfolio_markowitz, black_litterman_allocation
from src.quant.monte_carlo import run_monte_carlo_simulation
from src.quant.regime_detector import detect_market_regime
from src.data.cache_manager import CacheManager
from src.db.db_manager import DatabaseManager
from src.graph.workflow import create_hedge_fund_graph

def test_technical_indicators_calculation():
    tech = get_market_technicals("AAPL", period="3mo")
    assert "current_price" in tech
    assert "rsi_14" in tech
    assert "trend" in tech
    assert tech["annualized_volatility"] > 0
    assert 0 <= tech["rsi_14"] <= 100

def test_parametric_var_bounds():
    # 25% annual volatility should yield approx 2.6% 1-day 95% VaR
    var_95 = calculate_parametric_var(0.25, confidence_level=0.95)
    assert 2.0 <= var_95 <= 3.5

def test_risk_manager_veto():
    # Extreme volatility of 85% must trigger CRO veto
    risk = evaluate_portfolio_risk("TEST", annual_volatility=0.85, current_price=100.0, max_vol_limit=0.65)
    assert risk["is_vetoed"] is True
    assert risk["max_position_size_pct"] == 0.0
    assert risk["risk_rating"] == "EXTREME"

def test_dcf_valuation_model():
    dcf = calculate_dcf_valuation(
        free_cash_flow=10_000_000_000,
        growth_rate_5y=0.12,
        terminal_growth_rate=0.03,
        discount_rate=0.09,
        shares_outstanding=2_000_000_000,
        net_debt=0
    )
    assert dcf["intrinsic_value_per_share"] > 0
    assert dcf["terminal_value_weight_pct"] > 50

def test_graham_number_calculation():
    # EPS=4, BVPS=25 -> sqrt(22.5 * 4 * 25) = sqrt(2250) = 47.43
    gn = calculate_graham_number(eps=4.0, book_value_per_share=25.0)
    assert gn is not None
    assert 47.0 < gn < 48.0

def test_monte_carlo_simulation():
    mc = run_monte_carlo_simulation(
        current_price=150.0,
        annual_volatility=0.25,
        forecast_days=30,
        num_simulations=500
    )
    assert mc["worst_case_p5"] < mc["median_terminal_price"] < mc["best_case_p95"]
    assert 0.0 <= mc["probability_of_profit_pct"] <= 100.0
    assert len(mc["fan_chart"]["days"]) == 31

def test_portfolio_optimizer_markowitz():
    res = optimize_portfolio_markowitz(["NVDA", "AAPL", "MSFT"])
    assert "max_sharpe_weights" in res
    assert "expected_annual_return" in res
    assert len(res["max_sharpe_weights"]) == 3
    # Check that weights sum to approximately 100%
    total_weight = sum(res["max_sharpe_weights"].values())
    assert 0.98 <= total_weight <= 1.02

def test_cache_manager(tmp_path):
    test_db = str(tmp_path / "test_cache.sqlite3")
    cm = CacheManager(db_path=test_db, default_ttl_seconds=10)
    cm.set("test_key", {"status": "ok", "value": 42})
    
    cached = cm.get("test_key")
    assert cached is not None
    assert cached["value"] == 42
    
    # Missing key returns None
    assert cm.get("non_existent_key") is None

def test_database_manager(tmp_path):
    test_db = str(tmp_path / "test_audit.sqlite3")
    dm = DatabaseManager(db_path=test_db)
    order_id = dm.save_order({
        "ticker": "NVDA",
        "action": "BUY",
        "target_allocation_pct": 0.25,
        "confidence": 0.85,
        "executive_thesis": "Test thesis for audit trail."
    })
    assert order_id is not None
    assert order_id > 0
    
    orders = dm.get_recent_orders(limit=5)
    assert len(orders) == 1
    assert orders[0]["ticker"] == "NVDA"
    assert orders[0]["action"] == "BUY"

def test_end_to_end_langgraph():
    app = create_hedge_fund_graph()
    initial_state = {
        "ticker": "AAPL",
        "debate_round": 0,
        "debate_history": [],
        "bull_arguments": [],
        "bear_arguments": [],
        "logs": []
    }
    final_state = app.invoke(initial_state)
    assert "final_order" in final_state
    assert final_state["final_order"]["action"] in ["BUY", "SELL", "HOLD"]
    assert len(final_state["bull_arguments"]) >= 1
    assert final_state["risk_assessment"] is not None

def test_paper_broker_summary_and_rebalance(tmp_path):
    from backend.execution.paper_broker import PaperBroker
    broker = PaperBroker()
    summary = broker.get_summary()
    assert "cash_balance" in summary
    assert "total_portfolio_value" in summary
    assert "holdings" in summary
    assert len(summary["holdings"]) >= 1

    # Test batch rebalance execution
    target_weights = {"NVDA": 0.50, "AAPL": 0.50}
    prices = {"NVDA": 220.0, "AAPL": 330.0}
    rebal_res = broker.execute_batch_rebalance(target_weights, prices)
    assert rebal_res["status"] == "SUCCESS"
    assert "portfolio" in rebal_res
    new_summary = rebal_res["portfolio"]
    assert new_summary["total_portfolio_value"] > 0

