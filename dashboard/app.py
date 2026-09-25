import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
from src.graph.workflow import create_hedge_fund_graph
from src.quant.valuation_models import get_fundamental_metrics
from src.quant.technical_indicators import get_market_technicals
from src.quant.portfolio_optimizer import optimize_portfolio_markowitz, black_litterman_allocation
from src.quant.monte_carlo import run_monte_carlo_simulation
from src.quant.regime_detector import detect_market_regime
from src.agents.personas import warren_buffett_analysis, cathie_wood_analysis, benjamin_graham_analysis, jim_simons_quant_analysis
from src.backtester.event_engine import run_backtest

st.set_page_config(
    page_title="Institutional AI Hedge Fund Terminal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional Theme Styling
st.markdown("""
<style>
    .kpi-box {
        background-color: #1a1f2c;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #2e384d;
        text-align: center;
    }
    .buy-signal { color: #00ff88; font-weight: bold; font-size: 24px; }
    .sell-signal { color: #ff4757; font-weight: bold; font-size: 24px; }
    .hold-signal { color: #ffa502; font-weight: bold; font-size: 24px; }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Institutional Multi-Agent AI Hedge Fund")
st.caption("Quantitative MPT & Black-Litterman • Iconic Investor Personas • 2,000-Path Monte Carlo • Macro Regime Detection")

with st.sidebar:
    st.header("⚙️ Fund Universe & Controls")
    lead_ticker = st.text_input("Lead Asset Ticker", value="NVDA").upper().strip()
    portfolio_universe = st.text_area("Asset Universe (Comma Separated)", value="NVDA, AAPL, MSFT, GOOGL, TSLA").upper()
    universe_tickers = [t.strip() for t in portfolio_universe.split(",") if t.strip()]
    st.divider()
    run_btn = st.button("🚀 Convene Institutional Committee", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown("**Committee Personas:**\n- 👴 Warren Buffett (Moat & Quality)\n- 🚀 Cathie Wood (Exponential Innovation)\n- ⚖️ Benjamin Graham (Deep Value)\n- 🧮 Jim Simons (Quantitative Quant)\n- 🛡️ Chief Risk Officer (Parametric VaR)\n- 🎯 Chief Investment Officer (Allocation)")

if run_btn and lead_ticker:
    with st.spinner("Executing multi-agent quantitative models, Monte Carlo simulations & MPT optimization..."):
        try:
            # 1. Single Asset StateGraph Execution
            app = create_hedge_fund_graph()
            initial_state = {
                "ticker": lead_ticker,
                "debate_round": 0,
                "debate_history": [],
                "bull_arguments": [],
                "bear_arguments": [],
                "logs": []
            }
            final_state = app.invoke(initial_state)
            
            tech = final_state["technical_analysis"]
            risk = final_state["risk_assessment"]
            order = final_state["final_order"]
            fundamentals = get_fundamental_metrics(lead_ticker)
            
            # 2. Macro Regime Detection
            spy_df = yf.Ticker("SPY").history(period="6mo")
            regime = detect_market_regime(spy_df)

            # 3. Portfolio Optimization (MPT & Black-Litterman)
            mpt = optimize_portfolio_markowitz(universe_tickers)
            agent_views = {t: 0.18 if t in ["NVDA", "MSFT"] else 0.10 for t in universe_tickers}
            agent_conf = {t: 0.85 if t in ["NVDA", "MSFT"] else 0.60 for t in universe_tickers}
            bl = black_litterman_allocation(universe_tickers, agent_views, agent_conf)

            # 4. Monte Carlo Simulation
            mc = run_monte_carlo_simulation(
                current_price=tech["current_price"],
                annual_volatility=tech["annualized_volatility"],
                forecast_days=60,
                num_simulations=2000
            )

            st.success("Institutional Analysis & Portfolio Optimization Complete!")

            # --- TOP KPI METRICS ---
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                action_class = "buy-signal" if order["action"] == "BUY" else ("sell-signal" if order["action"] == "SELL" else "hold-signal")
                st.markdown(f"<div class='kpi-box'><div>CIO Directive</div><div class='{action_class}'>{order['action']}</div><div>Conviction: {order['confidence']*100:.0f}%</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='kpi-box'><div>Macro Market Regime</div><div style='font-size:22px; font-weight:bold; color:#00d2d3;'>{regime['regime']}</div><div>S&P Vol: {regime['annualized_volatility']}%</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='kpi-box'><div>Portfolio Max Sharpe</div><div style='font-size:24px; font-weight:bold;'>{mpt['max_sharpe_ratio']}</div><div>Exp. Return: {mpt['expected_annual_return']}%</div></div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div class='kpi-box'><div>Daily 95% VaR</div><div style='font-size:24px; font-weight:bold;'>{risk['var_95']}%</div><div>Rating: {risk['risk_rating']}</div></div>", unsafe_allow_html=True)

            st.write("")

            # --- ADVANCED TABS ---
            t_port, t_personas, t_mc, t_debate, t_dcf, t_bt = st.tabs([
                "📊 MPT & Black-Litterman Portfolio",
                "🧠 Iconic Investor Personas",
                "🎲 Monte Carlo Fan Chart",
                "⚔️ Committee Debate",
                "💎 Fundamental DCF",
                "🧪 Event Backtest"
            ])

            with t_port:
                st.subheader("Multi-Asset Modern Portfolio Theory & Black-Litterman Allocation")
                p1, p2 = st.columns([1, 1])
                with p1:
                    fig_w = go.Figure()
                    fig_w.add_trace(go.Bar(
                        x=list(bl['black_litterman_weights'].keys()),
                        y=[w * 100 for w in bl['black_litterman_weights'].values()],
                        name="Black-Litterman Blended %",
                        marker_color="#00ff88"
                    ))
                    fig_w.add_trace(go.Bar(
                        x=list(mpt['max_sharpe_weights'].keys()),
                        y=[w * 100 for w in mpt['max_sharpe_weights'].values()],
                        name="Markowitz Max Sharpe %",
                        marker_color="#3867d6"
                    ))
                    fig_w.update_layout(template="plotly_dark", barmode='group', height=400, yaxis_title="Target Weight (%)")
                    st.plotly_chart(fig_w, use_container_width=True)

                with p2:
                    st.markdown(f"**Expected Portfolio Annual Return:** `{mpt['expected_annual_return']}%`")
                    st.markdown(f"**Expected Portfolio Volatility:** `{mpt['expected_annual_volatility']}%`")
                    st.markdown(f"**Macro Capital Guidance:** {regime['action_guidance']}")
                    st.dataframe([
                        {"Ticker": t, "Markowitz %": f"{mpt['max_sharpe_weights'].get(t, 0)*100:.1f}%", "Black-Litterman %": f"{bl['black_litterman_weights'].get(t, 0)*100:.1f}%"}
                        for t in universe_tickers
                    ], use_container_width=True)

            with t_personas:
                st.subheader(f"Iconic Investor Persona Committee: {lead_ticker}")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.info(f"**👴 Warren Buffett (Moat & Cash Flow):**\n\n{warren_buffett_analysis(lead_ticker, fundamentals, tech)}")
                    st.success(f"**🚀 Cathie Wood (Exponential Growth):**\n\n{cathie_wood_analysis(lead_ticker, tech)}")
                with col_p2:
                    st.warning(f"**⚖️ Benjamin Graham (Deep Value & Safety):**\n\n{benjamin_graham_analysis(lead_ticker, fundamentals)}")
                    st.error(f"**🧮 Jim Simons (Quant Signal):**\n\n{jim_simons_quant_analysis(lead_ticker, tech)}")

            with t_mc:
                st.subheader(f"2,000-Path Monte Carlo Stochastic Risk Simulation ({lead_ticker} - 60 Days)")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("60-Day Median Price", f"${mc['median_terminal_price']}", f"{mc['expected_return_pct']:+0.1f}%")
                m2.metric("95% Worst-Case (P5)", f"${mc['worst_case_p5']}")
                m3.metric("95% Best-Case (P95)", f"${mc['best_case_p95']}")
                m4.metric("Probability of Profit", f"{mc['probability_of_profit_pct']}%")

                fc = mc['fan_chart']
                fig_mc = go.Figure()
                fig_mc.add_trace(go.Scatter(x=fc['days'], y=fc['upper_95'], mode='lines', line=dict(width=0), showlegend=False))
                fig_mc.add_trace(go.Scatter(x=fc['days'], y=fc['lower_5'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(0, 255, 136, 0.15)', name='90% Confidence Interval (P5-P95)'))
                fig_mc.add_trace(go.Scatter(x=fc['days'], y=fc['median'], mode='lines', line=dict(color='#00ff88', width=3), name='Median Expected Path'))
                fig_mc.update_layout(template="plotly_dark", height=420, xaxis_title="Trading Days Forward", yaxis_title="Projected Price ($)")
                st.plotly_chart(fig_mc, use_container_width=True)

            with t_debate:
                st.subheader("Multi-Turn Adversarial Committee Transcript")
                bulls = final_state["bull_arguments"]
                bears = final_state["bear_arguments"]
                for r in range(len(bulls)):
                    st.markdown(f"#### 🥊 Round {r+1}")
                    col_b, col_s = st.columns(2)
                    with col_b:
                        st.success(f"**🟢 Bull Strategist:**\n\n{bulls[r]}")
                    with col_s:
                        if r < len(bears):
                            st.error(f"**🔴 Bear Skeptic:**\n\n{bears[r]}")

            with t_dcf:
                st.subheader(f"Fundamental Analysis & Intrinsic Valuation: {lead_ticker}")
                f1, f2, f3, f4 = st.columns(4)
                f1.metric("DCF Intrinsic Value", f"${fundamentals['dcf_intrinsic_value']}")
                f2.metric("Margin of Safety", f"{fundamentals['margin_of_safety_pct']:+0.1f}%")
                f3.metric("Trailing P/E", f"{fundamentals['trailing_pe'] or 'N/A'}")
                f4.metric("Debt-to-Equity", f"{fundamentals['debt_to_equity']}")

            with t_bt:
                st.subheader(f"Quantitative Backtest Simulation (1-Year Horizon)")
                bt = run_backtest(lead_ticker, period="1y")
                b1, b2, b3, b4 = st.columns(4)
                b1.metric("Strategy Return", f"{bt['strategy_return_pct']:+0.2f}%")
                b2.metric("Buy & Hold Benchmark", f"{bt['benchmark_return_pct']:+0.2f}%")
                b3.metric("Sharpe Ratio", f"{bt['sharpe_ratio']}")
                b4.metric("Max Drawdown", f"{bt['max_drawdown_pct']}%")

                fig_bt = go.Figure()
                fig_bt.add_trace(go.Scatter(y=bt['portfolio_history'], mode='lines', name='AI Strategy Equity', line=dict(color='#00ff88', width=2)))
                fig_bt.update_layout(template="plotly_dark", height=400, yaxis_title="Portfolio Value ($)")
                st.plotly_chart(fig_bt, use_container_width=True)

        except Exception as e:
            st.error(f"Execution Error: {str(e)}")
else:
    st.info("👈 Enter the asset universe in the sidebar and click **Convene Institutional Committee** to initiate the advanced analysis.")
