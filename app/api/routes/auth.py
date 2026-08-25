from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.schemas.auth import SendOTPRequest, VerifyOTPRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter()

COOKIE_NAME = "access_token"


def _set_auth_cookie(response: Response, token: str) -> None:
    """Stores the JWT in an HttpOnly cookie so client-side JS cannot read it."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/send-otp")
def send_otp(request: SendOTPRequest):
    """Sends OTP to user's phone number via SMS (Logs dev OTP in local environment)."""
    return AuthService.send_otp(request)

@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, response: Response, db: Session = Depends(get_db)):
    """Verifies OTP and sets the auth cookie or indicates registration needed."""
    result = AuthService.verify_otp(request, db)
    if result.get("status") == "success":
        _set_auth_cookie(response, result.pop("access_token"))
    return result

@router.post("/register")
def register(request: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Registers a new user (customer or worker) and sets the auth cookie."""
    result = AuthService.register(request, db)
    if result.get("status") == "success":
        _set_auth_cookie(response, result.pop("access_token"))
    return result

@router.post("/logout")
def logout(response: Response):
    """Clears the auth cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Logged out successfully"}
