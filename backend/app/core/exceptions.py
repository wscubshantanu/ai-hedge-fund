"""
AETHER Capital — Custom Exceptions & Error Handlers
"""
from fastapi import HTTPException, status


class AetherException(Exception):
    """Base exception for AETHER Capital."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class TickerNotFoundError(AetherException):
    def __init__(self, ticker: str):
        super().__init__(f"Ticker '{ticker}' not found or invalid", status_code=404)


class InsufficientCashError(AetherException):
    def __init__(self, required: float, available: float):
        super().__init__(
            f"Insufficient cash. Required: ${required:,.2f}, Available: ${available:,.2f}",
            status_code=400
        )


class GuardrailVetoError(AetherException):
    def __init__(self, reason: str):
        super().__init__(f"Trade vetoed by guardrails: {reason}", status_code=403)


class AnalysisError(AetherException):
    def __init__(self, ticker: str, detail: str):
        super().__init__(f"Analysis failed for {ticker}: {detail}", status_code=500)


class DataProviderError(AetherException):
    def __init__(self, provider: str, detail: str):
        super().__init__(f"Data provider '{provider}' error: {detail}", status_code=502)
