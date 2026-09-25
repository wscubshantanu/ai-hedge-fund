"""
AETHER Capital — Audit Log Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.audit import AuditLog

router = APIRouter(tags=["Audit & Compliance"])


@router.get("/audit")
def get_audit_log(
    limit: int = Query(50, ge=1, le=200),
    event_type: str = Query(None),
    ticker: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get audit trail with optional filtering."""
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())

    if event_type:
        query = query.filter(AuditLog.event_type == event_type.upper())
    if ticker:
        query = query.filter(AuditLog.ticker == ticker.upper())

    entries = query.limit(limit).all()
    return {
        "total": len(entries),
        "entries": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "ticker": e.ticker,
                "action": e.action,
                "details": e.details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
    }
