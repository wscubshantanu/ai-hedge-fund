"""
AETHER Capital — Authentication Endpoints
Register, Login (JWT), Refresh, Logout, Profile
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User, RefreshToken, UserRole
from backend.app.models.audit import AuditLog
from backend.app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user,
)
from backend.app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserResponse,
)
from backend.app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new institutional analyst account."""
    # Check unique constraints
    if db.query(User).filter(User.email == req.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.query(User).filter(User.username == req.username.lower()).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        email=req.email.lower().strip(),
        username=req.username.lower().strip(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name or req.username.capitalize(),
        role=UserRole.ANALYST.value,
    )
    db.add(user)

    # Create tokens
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    refresh_token_str = create_refresh_token()
    refresh_obj = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_obj)

    # Audit
    db.add(AuditLog(user_id=user.id, event_type="REGISTER", action="USER_CREATED",
                     details={"email": user.email, "role": user.role}))
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive JWT tokens."""
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    refresh_token_str = create_refresh_token()
    refresh_obj = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_obj)
    db.add(AuditLog(user_id=user.id, event_type="LOGIN", action="SESSION_START"))
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    token_obj = db.query(RefreshToken).filter(
        RefreshToken.token == req.refresh_token,
        RefreshToken.revoked == False,
    ).first()

    if not token_obj or token_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    # Rotate: revoke old, issue new
    token_obj.revoked = True
    new_access = create_access_token(data={"sub": user.id, "role": user.role})
    new_refresh = create_refresh_token()
    db.add(RefreshToken(
        token=new_refresh,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke all refresh tokens for the current user."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.add(AuditLog(user_id=user.id, event_type="LOGOUT", action="SESSION_END"))
    db.commit()
    return {"status": "success", "message": "All sessions revoked"}


@router.get("/me", response_model=UserResponse)
def get_profile(user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserResponse.model_validate(user)


@router.get("/policy")
def security_policy():
    """Public security and compliance policy."""
    return {
        "encryption": "AES-256 GCM at rest, TLS 1.3 in transit",
        "authentication": "JWT RS256 with bcrypt password hashing, refresh token rotation",
        "authorization": "Role-Based Access Control (RBAC): admin, analyst, trader, viewer",
        "compliance": "Simulated FINRA Rule 3110 & SEC Rule 15c3-5",
        "guardrails": "Deterministic pre-trade volatility ceiling & position sizing",
        "data_isolation": "Air-gapped local execution, zero proprietary telemetry",
        "custody": "Non-custodial paper trading vault",
    }
