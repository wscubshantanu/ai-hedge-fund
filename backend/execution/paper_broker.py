import json
from pathlib import Path
from typing import Dict, Any
from backend.core.config import settings

class PaperBroker:
    """
    Simulated Institutional Paper Trading Execution Engine:
    - Tracks live cash, equity holdings, realized & unrealized PnL
    - Models 5 basis points execution slippage
    - Persists portfolio state to disk across sessions
    """
    def __init__(self, initial_cash: float = 100_000.0):
        self.state_file = settings.DATA_DIR / "paper_portfolio.json"
        self.initial_cash = initial_cash
        self.load_state()

    def load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cash = data.get("cash", self.initial_cash)
                    self.positions = data.get("positions", {})
                    self.realized_pnl = data.get("realized_pnl", 0.0)
                    self.trades_history = data.get("trades_history", [])
                    return
            except Exception:
                pass

        self.cash = self.initial_cash - 10766.0
        self.positions = {
            "NVDA": {"shares": 22.0, "entry_price": 198.40, "current_price": 218.29, "action": "BUY", "regime": "LOW_VOL_BULL"},
            "AAPL": {"shares": 9.0, "entry_price": 310.00, "current_price": 332.27, "action": "BUY", "regime": "LOW_VOL_BULL"},
            "MSFT": {"shares": 6.0, "entry_price": 478.00, "current_price": 495.63, "action": "HOLD", "regime": "RANGEBOUND_CHOP"}
        }
        self.realized_pnl = 0.0
        self.trades_history = [
            {"ticker": "NVDA", "action": "BUY", "shares": 22.0, "fill_price": 198.40, "total_cost": 4364.80, "status": "FILLED"},
            {"ticker": "AAPL", "action": "BUY", "shares": 9.0, "fill_price": 310.00, "total_cost": 2790.00, "status": "FILLED"},
            {"ticker": "MSFT", "action": "BUY", "shares": 6.0, "fill_price": 478.00, "total_cost": 2868.00, "status": "FILLED"}
        ]
        self.save_state()

    def save_state(self):
        payload = {
            "cash": round(self.cash, 2),
            "positions": self.positions,
            "realized_pnl": round(self.realized_pnl, 2),
            "trades_history": self.trades_history[-50:]
        }
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def execute_order(
        self,
        ticker: str,
        action: str,
        target_allocation_pct: float,
        current_price: float,
        slippage_bps: float = 5.0
    ) -> Dict[str, Any]:
        ticker = ticker.upper().strip()
        slippage_factor = slippage_bps / 10000.0

        # Current total equity
        pos_value = sum(p["shares"] * current_price for t, p in self.positions.items() if t == ticker)
        total_nav = self.cash + sum(p["shares"] * p["current_price"] for p in self.positions.values())

        if action == "BUY":
            target_dollar = total_nav * target_allocation_pct
            diff_dollar = target_dollar - pos_value

            if diff_dollar > 0 and self.cash > 100:
                fill_price = current_price * (1.0 + slippage_factor)
                shares_to_buy = min(self.cash, diff_dollar) / fill_price
                cost = shares_to_buy * fill_price

                self.cash -= cost
                if ticker in self.positions:
                    existing = self.positions[ticker]
                    total_shares = existing["shares"] + shares_to_buy
                    avg_price = ((existing["shares"] * existing["entry_price"]) + cost) / total_shares
                    self.positions[ticker] = {
                        "shares": round(total_shares, 4),
                        "entry_price": round(avg_price, 2),
                        "current_price": round(current_price, 2)
                    }
                else:
                    self.positions[ticker] = {
                        "shares": round(shares_to_buy, 4),
                        "entry_price": round(fill_price, 2),
                        "current_price": round(current_price, 2)
                    }

                trade_record = {
                    "ticker": ticker,
                    "action": "BUY",
                    "shares": round(shares_to_buy, 4),
                    "fill_price": round(fill_price, 2),
                    "total_cost": round(cost, 2),
                    "status": "FILLED"
                }
                self.trades_history.append(trade_record)
                self.save_state()
                return {"status": "SUCCESS", "trade": trade_record, "portfolio": self.get_summary()}

        elif action == "SELL":
            if ticker in self.positions:
                pos = self.positions.pop(ticker)
                fill_price = current_price * (1.0 - slippage_factor)
                proceeds = pos["shares"] * fill_price
                pnl = (fill_price - pos["entry_price"]) * pos["shares"]

                self.cash += proceeds
                self.realized_pnl += pnl

                trade_record = {
                    "ticker": ticker,
                    "action": "SELL",
                    "shares": pos["shares"],
                    "fill_price": round(fill_price, 2),
                    "proceeds": round(proceeds, 2),
                    "realized_pnl": round(pnl, 2),
                    "status": "FILLED"
                }
                self.trades_history.append(trade_record)
                self.save_state()
                return {"status": "SUCCESS", "trade": trade_record, "portfolio": self.get_summary()}

        return {"status": "NO_ACTION_REQUIRED", "message": "Allocation already matches target."}

    def update_prices(self, price_map: Dict[str, float]):
        for ticker, px in price_map.items():
            if ticker in self.positions and px > 0:
                self.positions[ticker]["current_price"] = round(px, 2)
        self.save_state()

    def get_summary(self) -> Dict[str, Any]:
        equity_holdings_val = sum(p["shares"] * p["current_price"] for p in self.positions.values())
        total_portfolio_value = self.cash + equity_holdings_val
        total_pnl = total_portfolio_value - self.initial_cash
        pnl_pct = (total_pnl / self.initial_cash) * 100

        holdings_list = []
        for ticker, pos in self.positions.items():
            shares = pos.get("shares", 0.0)
            avg_cost = pos.get("entry_price", 0.0)
            current_px = pos.get("current_price", avg_cost)
            pos_val = shares * current_px
            cost = shares * avg_cost
            pnl = pos_val - cost
            pnl_pct_item = ((pos_val - cost) / cost * 100) if cost > 0 else 0.0
            weight = (pos_val / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0

            holdings_list.append({
                "ticker": ticker,
                "shares": round(shares, 4),
                "avgCost": round(avg_cost, 2),
                "currentPrice": round(current_px, 2),
                "positionValue": round(pos_val, 2),
                "unrealizedPnl": round(pnl, 2),
                "unrealizedPnlPct": round(pnl_pct_item, 2),
                "weight": round(weight, 1),
                "action": pos.get("action", "BUY"),
                "regime": pos.get("regime", "LOW_VOL_BULL")
            })

        return {
            "cash_balance": round(self.cash, 2),
            "equity_holdings_value": round(equity_holdings_val, 2),
            "total_portfolio_value": round(total_portfolio_value, 2),
            "total_pnl_dollars": round(total_pnl, 2),
            "total_pnl_pct": round(pnl_pct, 2),
            "open_positions": self.positions,
            "holdings": holdings_list,
            "recent_executions": self.trades_history[-10:]
        }

    def execute_batch_rebalance(self, target_weights: Dict[str, float], current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes systematic portfolio rebalancing towards target weights:
        1. Sells overweight positions to release liquidity
        2. Buys underweight positions with allocated cash
        """
        total_nav = self.cash + sum(p["shares"] * current_prices.get(t, p["current_price"]) for t, p in self.positions.items())
        executed_trades = []

        # 1. Update current prices
        self.update_prices(current_prices)

        # 2. Phase 1: SELL Overweight or Liquidate Excluded
        for ticker, pos in list(self.positions.items()):
            cur_price = current_prices.get(ticker, pos["current_price"])
            cur_val = pos["shares"] * cur_price
            target_alloc = target_weights.get(ticker, 0.0)
            target_val = total_nav * target_alloc

            if cur_val > target_val:
                diff = cur_val - target_val
                shares_to_sell = diff / cur_price
                if shares_to_sell >= 0.01:
                    if target_alloc <= 0.001:
                        # Full liquidation
                        res = self.execute_order(ticker, "SELL", 0.0, cur_price)
                        if "trade" in res:
                            executed_trades.append(res["trade"])
                    else:
                        # Partial reduction
                        self.positions[ticker]["shares"] = round(pos["shares"] - shares_to_sell, 4)
                        proceeds = shares_to_sell * cur_price * 0.9995  # 5 bps slippage
                        self.cash += proceeds
                        pnl = (cur_price * 0.9995 - pos["entry_price"]) * shares_to_sell
                        self.realized_pnl += pnl
                        trade_rec = {
                            "ticker": ticker,
                            "action": "SELL",
                            "shares": round(shares_to_sell, 4),
                            "fill_price": round(cur_price * 0.9995, 2),
                            "proceeds": round(proceeds, 2),
                            "realized_pnl": round(pnl, 2),
                            "status": "FILLED"
                        }
                        self.trades_history.append(trade_rec)
                        executed_trades.append(trade_rec)

        # 3. Phase 2: BUY Underweight
        for ticker, target_alloc in target_weights.items():
            if target_alloc > 0.01:
                cur_price = current_prices.get(ticker, 150.0)
                cur_shares = self.positions.get(ticker, {}).get("shares", 0.0)
                cur_val = cur_shares * cur_price
                target_val = total_nav * target_alloc
                if target_val > cur_val:
                    diff = min(self.cash * 0.98, target_val - cur_val)
                    if diff > 10.0:
                        fill_px = cur_price * 1.0005
                        buy_shares = diff / fill_px
                        cost = buy_shares * fill_px
                        self.cash -= cost

                        if ticker in self.positions:
                            old = self.positions[ticker]
                            new_tot = old["shares"] + buy_shares
                            new_entry = (old["shares"] * old["entry_price"] + cost) / new_tot
                            self.positions[ticker] = {
                                "shares": round(new_tot, 4),
                                "entry_price": round(new_entry, 2),
                                "current_price": round(cur_price, 2),
                                "action": "BUY",
                                "regime": "LOW_VOL_BULL"
                            }
                        else:
                            self.positions[ticker] = {
                                "shares": round(buy_shares, 4),
                                "entry_price": round(fill_px, 2),
                                "current_price": round(cur_price, 2),
                                "action": "BUY",
                                "regime": "LOW_VOL_BULL"
                            }

                        trade_rec = {
                            "ticker": ticker,
                            "action": "BUY",
                            "shares": round(buy_shares, 4),
                            "fill_price": round(fill_px, 2),
                            "total_cost": round(cost, 2),
                            "status": "FILLED"
                        }
                        self.trades_history.append(trade_rec)
                        executed_trades.append(trade_rec)

        self.save_state()
        return {
            "status": "SUCCESS",
            "executed_trades": executed_trades,
            "portfolio": self.get_summary()
        }

    def reset_portfolio(self):
        self.cash = self.initial_cash
        self.positions = {
            "NVDA": {"shares": 22.0, "entry_price": 198.40, "current_price": 218.29, "action": "BUY", "regime": "LOW_VOL_BULL"},
            "AAPL": {"shares": 9.0, "entry_price": 310.00, "current_price": 332.27, "action": "BUY", "regime": "LOW_VOL_BULL"},
            "MSFT": {"shares": 6.0, "entry_price": 478.00, "current_price": 495.63, "action": "HOLD", "regime": "RANGEBOUND_CHOP"}
        }
        self.realized_pnl = 0.0
        self.trades_history = []
        self.save_state()
        return self.get_summary()

# Global Broker Singleton
broker = PaperBroker()

