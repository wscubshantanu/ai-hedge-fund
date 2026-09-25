import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Any

def compute_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate core quantitative technical indicators on OHLCV dataframe."""
    if df is None or len(df) < 20:
        raise ValueError("Insufficient data points to compute indicators (min 20 required).")

    # Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=min(50, len(df))).mean()
    df['SMA_200'] = df['Close'].rolling(window=min(200, len(df))).mean()

    # Relative Strength Index (RSI 14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # Bollinger Bands (20-day, 2 std)
    df['BB_Mid'] = df['SMA_20']
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (2 * bb_std)
    df['BB_Lower'] = df['BB_Mid'] - (2 * bb_std)

    # Average True Range (ATR 14)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    # Volatility & Returns
    returns = df['Close'].pct_change().dropna()
    annualized_vol = returns.std() * np.sqrt(252)

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    trend = "UPTREND" if latest['Close'] > latest['SMA_50'] > latest['SMA_200'] else (
        "DOWNTREND" if latest['Close'] < latest['SMA_50'] < latest['SMA_200'] else "SIDEWAYS"
    )

    return {
        "current_price": round(float(latest['Close']), 2),
        "previous_close": round(float(prev['Close']), 2),
        "change_pct": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2),
        "sma_20": round(float(latest['SMA_20']), 2),
        "sma_50": round(float(latest['SMA_50']), 2),
        "sma_200": round(float(latest['SMA_200']), 2),
        "rsi_14": round(float(latest['RSI']), 2),
        "macd": round(float(latest['MACD']), 3),
        "macd_signal": round(float(latest['MACD_Signal']), 3),
        "macd_hist": round(float(latest['MACD_Hist']), 3),
        "bb_upper": round(float(latest['BB_Upper']), 2),
        "bb_mid": round(float(latest['BB_Mid']), 2),
        "bb_lower": round(float(latest['BB_Lower']), 2),
        "atr_14": round(float(latest['ATR']), 2),
        "annualized_volatility": round(float(annualized_vol), 4),
        "52w_high": round(float(df['High'].max()), 2),
        "52w_low": round(float(df['Low'].min()), 2),
        "trend": trend,
        "is_overbought": bool(latest['RSI'] > 70),
        "is_oversold": bool(latest['RSI'] < 30)
    }

def get_market_technicals(ticker: str, period: str = "1y") -> Dict[str, Any]:
    """Fetch live data and calculate indicators with resilient fallback."""
    try:
        data = yf.Ticker(ticker).history(period=period)
        if data.empty or len(data) < 20:
            raise ValueError(f"No price history available for {ticker}")
        return compute_technical_indicators(data)
    except Exception as e:
        # Fallback realistic mock data for offline/test environments
        mock_profiles = {
            'NVDA': {'price': 218.29, 'prev': 215.10, 'change': 1.48, 'vol': 0.385, 'trend': 'UPTREND', 'rsi': 64.2},
            'AAPL': {'price': 332.27, 'prev': 329.80, 'change': 0.75, 'vol': 0.224, 'trend': 'UPTREND', 'rsi': 70.6},
            'MSFT': {'price': 495.63, 'prev': 491.20, 'change': 0.90, 'vol': 0.218, 'trend': 'UPTREND', 'rsi': 62.1},
            'TSLA': {'price': 365.44, 'prev': 372.10, 'change': -1.79, 'vol': 0.521, 'trend': 'SIDEWAYS', 'rsi': 48.3},
            'GOOGL': {'price': 338.50, 'prev': 335.60, 'change': 0.86, 'vol': 0.264, 'trend': 'SIDEWAYS', 'rsi': 55.8},
        }
        p = mock_profiles.get(ticker, {'price': 185.0, 'prev': 183.0, 'change': 1.09, 'vol': 0.28, 'trend': 'UPTREND', 'rsi': 54.0})
        base_price = p['price']
        return {
            "current_price": base_price,
            "previous_close": p['prev'],
            "change_pct": p['change'],
            "sma_20": round(base_price * 0.98, 2),
            "sma_50": round(base_price * 0.95, 2),
            "sma_200": round(base_price * 0.88, 2),
            "rsi_14": p['rsi'],
            "macd": round(base_price * 0.008, 3),
            "macd_signal": round(base_price * 0.006, 3),
            "macd_hist": round(base_price * 0.002, 3),
            "bb_upper": round(base_price * 1.04, 2),
            "bb_mid": round(base_price, 2),
            "bb_lower": round(base_price * 0.96, 2),
            "atr_14": round(base_price * 0.025, 2),
            "annualized_volatility": p['vol'],
            "52w_high": round(base_price * 1.18, 2),
            "52w_low": round(base_price * 0.75, 2),
            "trend": p['trend'],
            "is_overbought": bool(p['rsi'] > 70),
            "is_oversold": bool(p['rsi'] < 30),
            "_warning": f"Used simulated data due to: {str(e)}"
        }
