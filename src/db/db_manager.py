import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """
    Persistence layer for compliance, audit trails, and performance tracking.
    Stores every investment committee trade order and backtest simulation run.
    """
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "hedge_fund_audit.sqlite3")
        else:
            self.db_path = db_path

        self._init_tables()

    def _init_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_allocation_pct REAL NOT NULL,
                    confidence REAL NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    executive_thesis TEXT NOT NULL,
                    bull_bear_consensus TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    period TEXT NOT NULL,
                    strategy_return_pct REAL NOT NULL,
                    benchmark_return_pct REAL NOT NULL,
                    excess_alpha_pct REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    sortino_ratio REAL NOT NULL,
                    max_drawdown_pct REAL NOT NULL,
                    total_trades INTEGER NOT NULL
                )
            """)
            conn.commit()

    def save_order(self, order: Dict[str, Any]) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trade_orders (
                    timestamp, ticker, action, target_allocation_pct,
                    confidence, stop_loss, take_profit, executive_thesis, bull_bear_consensus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                order.get("ticker", "UNKNOWN"),
                order.get("action", "HOLD"),
                order.get("target_allocation_pct", 0.0),
                order.get("confidence", 0.0),
                order.get("stop_loss_price"),
                order.get("take_profit_price"),
                order.get("executive_thesis", ""),
                order.get("bull_bear_consensus", "")
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_orders(self, limit: int = 15) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trade_orders ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def save_backtest(self, bt: Dict[str, Any]) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backtest_logs (
                    timestamp, ticker, period, strategy_return_pct,
                    benchmark_return_pct, excess_alpha_pct, sharpe_ratio,
                    sortino_ratio, max_drawdown_pct, total_trades
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                bt.get("ticker", "UNKNOWN"),
                bt.get("period", "1y"),
                bt.get("strategy_return_pct", 0.0),
                bt.get("benchmark_return_pct", 0.0),
                bt.get("excess_alpha_pct", 0.0),
                bt.get("sharpe_ratio", 0.0),
                bt.get("sortino_ratio", 0.0),
                bt.get("max_drawdown_pct", 0.0),
                bt.get("total_trades", 0)
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_backtests(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM backtest_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

# Global DB Singleton
db = DatabaseManager()
